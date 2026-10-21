#!/usr/bin/env python3
"""RQ1-B agent runtime validation (2026-10-17): offline replay of the REAL agent request trace (<tag>-trace.jsonl from
kv_agent_events.py: one line per LLM call with its LMCache chunk hashes, lookup time, the runtime's continue / end
decision and its time) through a capacity-only host-cache simulator, with the policies of the earlier studies and one
policy that uses the real agent events. TRACE SIMULATION on a REAL trace; capacity is swept because the 4060 Ti run is
far smaller than the 200 GiB setting of the Mooncake studies (reported separately, never mixed).

Policies (all decide with information available at the decision time):
  split          static DRAM/CXL split (share 0.32 of capacity hashed to tier 0), LRU per tier   (baseline B)
  lru            one global LRU                                                                   (baseline C)
  slru           segmented LRU, protected segment = 1/3, protect on first hit                     (Phase 1's best online)
  ttl<T>         session-aware LRU: blocks of a task idle for more than T s are evicted first      (needs the task id)
  event_end      REAL end events: at the task's end (agent_end) its blocks become evict-first unless another task that
                 has not ended referenced them (shared prefixes stay)                             (needs task id + end event)
  event_both     event_end + at a REAL continue decision the current context is protected until the task's next call
                 arrives or <bound> s pass                                                        (needs continue event)
  event_both+slru  event_both with the SLRU order for the rest
  event_cont     REAL continue decisions only (protect the context until the task's next call or <bound> s)
  cost / event_cont+cost   COST-AWARE: among the next --scan LRU candidates evict the cheapest-to-lose chunk under the
                 miss-cost model: the recompute of the contiguous cached chain behind the chunk (prefix semantics) at
                 the measured position-dependent per-token cost, minus the load cost; needs --r0/--r1/--l
  static_2nd<k>  STATIC second-touch admission on LRU: a block never requested before is admitted only at positions < k
                 (k = 1 by default); any block requested before is admitted (a ghost set of hashes, no data kept)
  static_d<k> / static_p<m> / static_n<k> / static_dp<k>_<m>   STATIC admission rules on LRU: bypass a new block at
                 position >= k / of a request with >= m existing-prefix blocks / that is the k-th or later NEW block of
                 its request / position >= k and existing prefix >= m (never the first block). No learning.
  pop / lhd / olr / cond   LEARNED ONLINE (history only, the cache's own feedback as labels): retention priority used as
                 the tie-break among the least-recent window — pop = decayed popularity of the block, lhd = hit
                 probability of the block's class (root, position, depth) learned from admissions that did / did not hit
                 before eviction, olr = online logistic regression on creation-time features, cond = per-root hit rate;
                 with --admit-th > 0 lhd / olr / cond also bypass admission of blocks whose learned probability is below it.
  --order tail   LMCache 0.5.5 / vLLM eviction order (a request's tail chunks are evicted before its head); 'head' is
                 the position-blind order used by the earlier rounds. Scoring is prefix-aware in both cases: a chunk
                 counts as USABLE only if every earlier chunk of the request also hit (TTFT model: --r0 --r1 --l).
  event_end+defer / event_both+defer   as above, plus the store of a task's final call is never issued (LMCache's lazy
                 offload would hold it until the request ends; the end decision drops it) — the write-avoidance case
  oracle         Belady MIN with bypass of never-reused chunks                                     (upper bound E)
Metrics on the second half of the trace (by request order): reuse-hit share (hits / accesses to chunks seen before),
overall hit rate, recomputed tokens (misses × 256), chunks written, dead-occupancy share; share of the oracle's gain
over global LRU (the better of the two LRU baselines at small capacities). Output: <out>/<tag>-replay.csv and fig-agent-replay-<tag>.
Extra metrics per policy: evictions before reuse, live / dead occupancy, hits under continue-protection, dead-marked
blocks that were read again, LRU residence (write -> eviction, p50), and the trace's live working set, production rate
and reuse horizon (regime variables); --churn adds SYNTHETIC never-reused chunks of other tenants at a fixed rate.
usage: kv_agent_replay.py <trace.jsonl> <out_dir> <tag> [--caps 48,64,96,128,192,256,384] [--bound 30] [--chunk-mb 9.44] [--churn 0] [--policies ...] [--no-fig]"""
import argparse, collections, csv, heapq, json, math, os, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser(); ap.add_argument("trace"); ap.add_argument("out"); ap.add_argument("tag")
ap.add_argument("--caps", default="48,64,96,128,192,256,384"); ap.add_argument("--bound", type=float, default=30.0); ap.add_argument("--chunk-mb", type=float, default=9.44)
ap.add_argument("--ttl", default="10,30"); ap.add_argument("--share", type=float, default=0.32)
ap.add_argument("--churn", type=float, default=0.0, help="SYNTHETIC background churn: never-reused chunks from other tenants injected at this rate (chunks/s), uniformly over the trace span")
ap.add_argument("--policies", default="split,lru,slru,ttl10,ttl30,event_end,event_cont,event_both,event_both+slru,event_end+defer,event_both+defer,oracle")
ap.add_argument("--no-fig", action="store_true")
ap.add_argument("--order", default="head", choices=["head", "tail"], help="LRU order inside a request: head = position-blind (chunk 0 least recent), tail = LMCache 0.5.5 / vLLM order (tail evicted first)")
ap.add_argument("--mooncake", action="store_true", help="the trace is a Mooncake jsonl (timestamp ms, hash_ids, input_length); no tasks, no events")
ap.add_argument("--tok", type=int, default=256, help="tokens per chunk (256 for LMCache chunks, 512 for Mooncake hash blocks)")
ap.add_argument("--r0", type=float, default=0.0, help="MISS-COST MODEL: recompute seconds per token at position 0 (measured)"); ap.add_argument("--r1", type=float, default=0.0, help="recompute seconds per token per token of position (superlinearity, measured)")
ap.add_argument("--l", type=float, default=0.0, help="MISS-COST MODEL: load seconds per token from the host tier (measured)"); ap.add_argument("--cost-noise", type=float, default=0.0, help="relative noise applied to the cost estimate used by cost-aware policies (sensitivity)")
ap.add_argument("--tau", type=float, default=300.0, help="learned policies: popularity / rate decay time constant (s)"); ap.add_argument("--admit-th", type=float, default=0.0, help="learned policies: bypass admission when the learned reuse probability is below this (0 = no bypass)")
ap.add_argument("--dump-hits", default="", help="write one byte per scored access per policy and capacity to <path>-<policy>-<cap>.bin: 1 hit, 0 miss on a never-seen block, 2 miss on a block that was bypassed at its last admission opportunity, 3 miss on a block that had been admitted and evicted")
ap.add_argument("--dump-admit", default="", help="write one byte per NEW block in the scored half (1 admitted, 0 bypassed) to <path>-<policy>-<cap>.adm, for the oracle-gap decomposition")
ap.add_argument("--explore", type=float, default=0.0, help="learned admission: admit a would-be-bypassed block with this probability so that its class keeps receiving feedback")
ap.add_argument("--bypass-feedback", action="store_true", help="learned admission: a bypassed block also labels its class — 1 if the same hash is requested again within the online residence estimate, 0 otherwise (both observable at runtime)")
ap.add_argument("--freeze-at", type=float, default=0.0, help="learned policies: stop updating the class statistics after this fraction of the trace span (0 = keep learning): 'historical' vs 'online' variants")
ap.add_argument("--min-samples", type=float, default=50.0, help="learned admission: a class may bypass only after this many (decayed) feedback samples")
ap.add_argument("--scan", type=int, default=64, help="cost-aware policies: upper bound of LRU candidates scanned per eviction (the window is min(scan, cap/16), at least 4)")
A = ap.parse_args(); INF = float("inf"); TOK = A.tok
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})

def _load():
    if not A.mooncake: return sorted((json.loads(l) for l in open(A.trace)), key=lambda r: r["t_lookup"])
    out = []
    for i, l in enumerate(open(A.trace)):
        r = json.loads(l); t = r["timestamp"] / 1000.0
        out.append(dict(task=i, call=1, rid=f"mc{i}", t_submit=t, t_lookup=t, t_resp=None, t_dec=None, decision=None, t_task_end=t, outcome="trace", hashes=[str(h) for h in r["hash_ids"]], found=None, input_length=r.get("input_length")))
    return sorted(out, key=lambda r: r["t_lookup"])
R = _load()
# accesses: (t, hash, request index); next-use index per access (for the oracle); task structure
acc = []; task_of = []; t_end_of = {}; next_call_t = {}
for i, r in enumerate(R):
    for h in r["hashes"]: acc.append((r["t_lookup"], h, i))
    task_of.append(r["task"]); t_end_of[r["task"]] = r.get("t_task_end") or INF
T0, T1 = R[0]["t_lookup"], R[-1]["t_lookup"]; SPAN = max(1e-9, T1 - T0)
n_churn = int(A.churn * SPAN)
if n_churn:                                                                            # SYNTHETIC churn: one access each, never reused, no task, no events
    for j in range(n_churn):
        hx = f"{0xc0ffee0000000000 + j:016x}"                                         # hex so that the hash-based split works; 16 chars never collide with 64-char real hashes
        R.append(dict(task=-1, call=0, t_lookup=T0 + (j + 0.5) * SPAN / n_churn, hashes=[hx], decision=None, t_dec=None, t_task_end=None)); task_of.append(-1)
        acc.append((T0 + (j + 0.5) * SPAN / n_churn, hx, len(R) - 1))
    acc.sort(key=lambda x: (x[0], x[2]))
    order = sorted(range(len(R)), key=lambda i: R[i]["t_lookup"]); remap = {old: new for new, old in enumerate(order)}
    R = [R[i] for i in order]; task_of = [r["task"] for r in R]; acc = [(t, h, remap[ri]) for t, h, ri in acc]
# live working set over time: chunks referenced by tasks that have started and not ended (sampled every second); agent production rate; horizon
live_samples = []; first_ref = {}; last_ref = {}; task_span = {}
for i, r in enumerate(R):
    if r["task"] < 0: continue
    tk = r["task"]; ts, te = task_span.get(tk, (r["t_lookup"], r.get("t_task_end") or r["t_lookup"])); task_span[tk] = (min(ts, r["t_lookup"]), max(te, r.get("t_task_end") or r["t_lookup"]))
    for h in r["hashes"]: first_ref.setdefault(h, (r["t_lookup"], tk)); last_ref[h] = (r["t_lookup"], tk)
blocks_by_task = collections.defaultdict(set)
for i, r in enumerate(R):
    if r["task"] >= 0:
        for h in r["hashes"]: blocks_by_task[r["task"]].add(h)
import bisect as _b
ends = sorted((te, tk) for tk, (ts, te) in task_span.items()); starts = sorted((ts, tk) for tk, (ts, te) in task_span.items())
t = T0
while t <= T1:
    live = set()
    for ts, tk in starts:
        if ts > t: break
        if task_span[tk][1] >= t: live |= blocks_by_task[tk]
    live_samples.append(len(live)); t += max(1.0, SPAN / 400)
W_LIVE = dict(mean=sum(live_samples) / max(1, len(live_samples)), p90=sorted(live_samples)[int(0.9 * (len(live_samples) - 1))] if live_samples else 0, max=max(live_samples) if live_samples else 0)
uniq_agent = {h for t_, h, ri in acc if task_of[ri] >= 0}
P_AGENT = len(uniq_agent) / SPAN                                                        # chunks created per second by the agents (first writes)
uniq_bg = {h for t_, h, ri in acc if task_of[ri] < 0 and not h.startswith("c0ffee")}
P_BG = len(uniq_bg) / SPAN                                                              # REAL background requests recorded on the same server (task -1 in the trace)
tasks_of_h = collections.defaultdict(set)
for t_, h, ri in acc:
    if task_of[ri] >= 0: tasks_of_h[h].add(task_of[ri])
gaps = []                                                                               # reuse horizon of a task's OWN chunks: previous use -> next use (shared prefixes excluded)
seen_t = {}
for t_, h, ri in acc:
    if task_of[ri] < 0 or len(tasks_of_h[h]) > 1: continue
    if h in seen_t: gaps.append(t_ - seen_t[h])
    seen_t[h] = t_
gaps.sort(); H = dict(p50=gaps[len(gaps) // 2] if gaps else 0, p90=gaps[int(0.9 * (len(gaps) - 1))] if gaps else 0, n=len(gaps))
by_task = collections.defaultdict(list)
for i, r in enumerate(R):
    if r["task"] >= 0: by_task[r["task"]].append(i)                                   # synthetic churn requests (task -1) have no task structure
for tk, idxs in by_task.items():
    for a, b in zip(idxs, idxs[1:]): next_call_t[a] = R[b]["t_lookup"]
nu = [INF] * len(acc); last = {}
for i in range(len(acc) - 1, -1, -1):
    h = acc[i][1]; nu[i] = last.get(h, INF); last[h] = i
half = len(R) // 2
# events, in time order: ("end", t, task) ; ("cont", t, request index) with protection until next call or bound
events = []
for tk, idxs in by_task.items():
    te = t_end_of[tk]
    if te < INF: events.append((te, 0, "end", tk))
for i, r in enumerate(R):
    if r.get("decision") == "continue" and r.get("t_dec") is not None: events.append((r["t_dec"], 1, "cont", i))
events.sort()

def run(policy, cap):
    use_split = policy == "split"; use_slru = "slru" in policy; ttl = float(policy[3:]) if policy.startswith("ttl") else None
    ev_end = policy.startswith("event") and not policy.startswith("event_cont"); ev_cont = policy.startswith("event_both") or policy.startswith("event_cont"); oracle = policy == "oracle"; defer = "defer" in policy
    final_call = {i for i, r in enumerate(R) if r.get("decision") == "end"}                   # requests after which the runtime said "end"
    nslot = [int(cap * A.share), cap - int(cap * A.share)]; n = [0, 0]; where = {}
    lru = collections.OrderedDict(); tier = [collections.OrderedDict(), collections.OrderedDict()]
    prob = collections.OrderedDict(); prot = collections.OrderedDict()
    dead = collections.OrderedDict(); protected = {}                                # hash -> protect-until time (continue)
    refs = collections.defaultdict(set); ended = set(); task_last = {}                # hash -> tasks that referenced it; ended tasks; task -> last request time
    heap = []; nuv = {}; ei = 0
    st = dict(acc=0, reuse=0, hit=0, miss=0, written=0, bypass=0, occ_dead=0.0, occ_all=0.0, evict=0, evict_live=0, cov_prot=0, dead_fp=0, res=[], usable=0, usable_tok=0, req=0, req_tok=0, ttft_cold=0.0, ttft=0.0, evict_cost=0.0); seen = set(); last_t = None; last_idx = {}
    stored_at = {}; pos = {}                                                               # pos[h]: chunk index inside the request that first stored it (online: the manager knows it)
    cost_aware = "cost" in policy; rng_c = random.Random(7); req_of = {}
    learned = policy.split("+")[0] in ("pop", "lhd", "olr", "cond"); L_kind = policy.split("+")[0] if learned else None
    static_rule = None                                                                   # ("d", k): bypass new blocks at position >= k; ("p", m): requests with >= m old blocks; ("n", k): the k-th+ NEW block of a request; ("dp", k, m): position >= k and old >= m
    import re as _re
    m_ = _re.match(r"static_(dp)(\d+)_(\d+)$|static_([dpn])(\d+)$|static_(2nd)(\d*)$", policy.split("+")[0])
    if m_: static_rule = ("dp", int(m_.group(2)), int(m_.group(3))) if m_.group(1) else (("2nd", int(m_.group(7) or 1)) if m_.group(6) else (m_.group(4), int(m_.group(5))))
    FREEZE_T = (T0 + A.freeze_at * SPAN) if A.freeze_at > 0 else INF
    last_state = {}                                                                      # hash -> "bypassed" | "evicted" | None (resident)
    pend_fb = []; pend_open = {}; pend_cls = {}; req_old = 0                             # bypass feedback: heap of (deadline, h, cls, root); open deadlines per hash
    adm_rate = [0.0, None]                                                               # online residence estimate: decayed admissions per second
    st.update(bypass_total=0, bypass_reused=0, bypass_reused_60=0, bypass_reused_300=0, admit_never=0, miss_bypassed=0, miss_evicted=0, miss_new=0, explored=0, fb_delay=[], hits_f=[0] * 5, acc_f=[0] * 5)
    admlog = bytearray() if A.dump_admit else None
    TAU = A.tau; cls_stat = collections.defaultdict(lambda: [0.0, 0.0, None])            # class -> [hits (decayed), admitted (decayed), last t]: P(a block of this class gets a hit before eviction)
    root_stat = collections.defaultdict(lambda: [0.0, 0.0, None]); blk_pop = {}; blk_pop_t = {}; blk_cls = {}; blk_hit = {}; blk_z = {}; blk_root = {}
    olr_w = [0.0] * 7; olr_m = [0.0] * 6; olr_v = [1.0] * 6; olr_n = [0]
    def dec(st, t):
        if st[2] is not None and t > st[2]: f = math.exp(-(t - st[2]) / (4 * TAU)); st[0] *= f; st[1] *= f
        st[2] = t if st[2] is None else max(st[2], t)
    def rate(st, t, prior, k=20.0): dec(st, t); return (st[0] + k * prior) / (st[1] + k)
    def bpop(h, t): return blk_pop[h] * math.exp(-(t - blk_pop_t[h]) / TAU) if h in blk_pop else 0.0
    def cls_of(h, j, dep, root): return (root, min(3, j // 8), min(2, dep // 8))
    def olr_feats(h, t, j, dep, root, Lr): rs = root_stat[root]; return [math.log1p(j), math.log1p(dep), math.log1p(Lr / TOK), rate(rs, t, 0.25) if rs[1] > 0 else 0.25, math.log1p(rs[1]), math.log1p(bpop(root, t))]
    def olr_z(x):
        olr_n[0] += 1
        if olr_n[0] <= 2000:
            for i_, xi in enumerate(x): olr_m[i_] += (xi - olr_m[i_]) / olr_n[0]; olr_v[i_] += ((xi - olr_m[i_]) ** 2 - olr_v[i_]) / olr_n[0]
        return [(xi - olr_m[i_]) / math.sqrt(olr_v[i_] + 1e-6) for i_, xi in enumerate(x)]
    def olr_p(z): s_ = olr_w[0] + sum(w * zi for w, zi in zip(olr_w[1:], z)); return 1 / (1 + math.exp(-max(-30, min(30, s_))))
    def olr_upd(z, y):
        p_ = olr_p(z); g = p_ - y; olr_w[0] -= 0.05 * g
        for i_, zi in enumerate(z): olr_w[i_ + 1] -= 0.05 * (g * zi + 1e-4 * olr_w[i_ + 1])
    def feedback(h, t, hit, cls=None, root=None):
        """the cache's own label when a block is evicted (0) or first hit after admission (1): used by lhd / olr / cond.
        With --bypass-feedback also called for bypassed blocks (cls/root given): 1 if re-requested within the residence estimate."""
        if t > FREEZE_T: return
        cls = cls if cls is not None else blk_cls.get(h); root = root if root is not None else blk_root.get(h)
        if cls is not None: st_ = cls_stat[cls]; dec(st_, t); st_[0] += hit; st_[1] += 1
        if root is not None: st_ = root_stat[root]; dec(st_, t); st_[0] += hit; st_[1] += 1
        if h in blk_z: olr_upd(blk_z[h], hit)
        if h in stored_at and len(st["fb_delay"]) < 100000: st["fb_delay"].append(t - stored_at[h])
    def residence_est(t):
        """online estimate of the LRU residence: capacity / admission rate (decayed over 4 tau)."""
        return cap / max(1e-6, adm_rate[0] / (4 * TAU)) if adm_rate[1] is not None else INF
    def note_admission(t):
        if adm_rate[1] is not None: adm_rate[0] *= math.exp(-(t - adm_rate[1]) / (4 * TAU))
        adm_rate[0] += 1.0; adm_rate[1] = t
    def prio(h, t):
        """learned retention priority (higher = keep): pop = decayed popularity; lhd = class hit rate; olr = model score; cond = root rate."""
        if L_kind == "pop": return bpop(h, t)
        if L_kind == "lhd": st = cls_stat.get(blk_cls.get(h)); return rate(st, t, 0.3) if st and st[1] >= 20 else 0.3
        if L_kind == "olr": return olr_p(blk_z[h]) if h in blk_z else 0.3
        if L_kind == "cond": st = root_stat.get(blk_root.get(h)); return rate(st, t, 0.3) if st and st[1] >= 50 else 0.3
        return 0.0
    def ev_cost(h):
        """Estimated cost of losing this chunk (seconds), online information only: the recompute of the contiguous cached
        chain from this chunk to the first gap of the request that stored it (prefix semantics: everything behind a hole
        is recomputed anyway), at the measured per-token cost r(p) = r0 + r1·p, minus what loading it would have cost."""
        q = req_of.get(h); k = pos.get(h, 0); hs = R[q]["hashes"] if q is not None else [h]; c = 0.0; n_ = 0
        while k < len(hs) and hs[k] in where and n_ < 64:
            c += (A.r0 + A.r1 * k * TOK - A.l) * TOK; k += 1; n_ += 1
        return c * (1 + A.cost_noise * rng_c.uniform(-1, 1)) if A.cost_noise else c
    cur = -1; req_hs = []; usable = True; hitlog = bytearray() if A.dump_hits else None
    def remove(h, now=None):
        t_ = where.pop(h); n[t_] -= 1; lru.pop(h, None); tier[t_].pop(h, None); dead.pop(h, None); prob.pop(h, None); prot.pop(h, None); nuv.pop(h, None); protected.pop(h, None)
        if learned and now is not None and not blk_hit.get(h, False): feedback(h, now, 0)
        blk_hit.pop(h, None); last_state[h] = "evicted"
        st["evict"] += 1; st["evict_live"] += (nu[last_idx[h]] < INF)
        if now is not None and h in stored_at and len(st["res"]) < 200000: st["res"].append(now - stored_at.pop(h))
    def place(h, t_, i):
        where[h] = t_; n[t_] += 1; lru[h] = True; tier[t_][h] = True; st["written"] += 1; stored_at[h] = acc[i][0]; pos.setdefault(h, len(req_hs) - 1); req_of.setdefault(h, cur); last_state[h] = None
        if nu[i] == INF: st["admit_never"] += 1
        note_admission(acc[i][0])
        if use_slru: prob[h] = True
        if oracle: nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
    def victim(now):
        srcs = ((dead,) if dead else ()) + ((prob, prot) if use_slru else (lru,))
        for src in srcs:
            k = 0; best = None; bc = INF; scanned = 0
            win = min(A.scan, max(4, cap // 16))                                          # cost breaks ties only among the least-recent few (recency = reuse likelihood stays primary)
            for b in src:
                if protected.get(b, -INF) > now: k += 1; continue
                if not cost_aware and not learned: return b
                c = ev_cost(b) if cost_aware else prio(b, now)                             # cost-aware: cheapest-to-lose; learned: lowest retention priority among the next `win` LRU candidates
                if c < bc: best, bc = b, c
                scanned += 1
                if scanned >= win: break
            if best is not None: return best
            if k > 512: break
        if ttl is not None:
            for b in lru:
                tk_ = max((tk for tk in refs[b] if tk not in ended), key=lambda tk: task_last.get(tk, -INF), default=None)
                if tk_ is None or now - task_last.get(tk_, now) > ttl: return b
                break
        return next(iter(lru))
    def end_request():
        if cur < 0: return
        if A.order == "tail":                                                              # LMCache / vLLM order: touch the request's chunks in reverse so the tail is evicted first
            for b in reversed(req_hs):
                if b in where:
                    lru.move_to_end(b); tier[where[b]].move_to_end(b)
                    if use_slru:
                        if b in prot: prot.move_to_end(b)
                        elif b in prob: prob.move_to_end(b)
    for i, (t, h, ri) in enumerate(acc):
        tk = task_of[ri]; task_last[tk] = t
        if ri != cur:
            end_request(); cur = ri; req_hs = []; usable = True; req_old = sum(1 for x in R[ri]["hashes"] if x in seen)   # existing-prefix length: blocks that existed before this request
            if ri >= half and task_of[ri] >= 0:
                Ltok = R[ri].get("input_length") or len(R[ri]["hashes"]) * TOK; st["req"] += 1; st["req_tok"] += Ltok
                st["ttft_cold"] += A.r0 * Ltok + A.r1 * Ltok * Ltok / 2
        req_hs.append(h)
        while ei < len(events) and events[ei][0] <= t:
            _, _, kind, x = events[ei]; ei += 1
            if kind == "end" and ev_end:
                ended.add(x)
                for b in list(where):
                    if x in refs[b] and not any(tk2 not in ended for tk2 in refs[b]): dead[b] = True
            elif kind == "cont" and ev_cont:
                until = min(next_call_t.get(x, INF), events[ei - 1][0] + A.bound)
                for b in R[x]["hashes"]:
                    if b in where: protected[b] = until
        refs[h].add(tk)
        reuse = h in seen; seen.add(h); last_idx[h] = i; test = ri >= half and task_of[ri] >= 0            # scored: agent accesses in the second half; churn / background only adds pressure
        if learned and A.bypass_feedback:
            while pend_fb and pend_fb[0][0] <= t:                                        # deadline passed: the bypassed block was not requested again within the residence estimate
                dl, hb, cb, rb = heapq.heappop(pend_fb)
                if pend_open.get(hb) == dl: pend_open.pop(hb, None); feedback(hb, dl, 0, cb, rb)
            if h in pend_open:                                                           # requested again before the deadline: a useful block was bypassed
                dl = pend_open.pop(h); cb_rb = pend_cls.pop(h, None)
                if cb_rb: feedback(h, t, 1, cb_rb[0], cb_rb[1])
        if test:
            f_ = min(4, int(5 * (ri - half) / max(1, len(R) - half))); st["acc_f"][f_] += 1
            st["acc"] += 1; st["reuse"] += reuse
            if last_t is not None and where:
                dt = t - last_t; st["occ_all"] += dt * len(where); st["occ_dead"] += dt * sum(1 for b in where if nu[last_idx[b]] == INF)
        last_t = t
        if learned: blk_pop[h] = bpop(h, t) + 1.0; blk_pop_t[h] = t; blk_pop[R[ri]["hashes"][0]] = bpop(R[ri]["hashes"][0], t) + 1.0; blk_pop_t[R[ri]["hashes"][0]] = t
        if test and hitlog is not None: hitlog.append(1 if h in where else (2 if last_state.get(h) == "bypassed" else 3 if last_state.get(h) == "evicted" else 0))
        if h in where:
            if learned and not blk_hit.get(h, False): blk_hit[h] = True; feedback(h, t, 1)
            if test:
                st["hit"] += 1; st["hits_f"][f_] += 1
                if protected.get(h, -INF) > t: st["cov_prot"] += 1
                if usable: st["usable"] += 1; st["usable_tok"] += TOK; st["ttft"] += A.l * TOK          # prefix-aware: counts only while every earlier chunk of the request hit
            if h in dead and test: st["dead_fp"] += 1
            lru.move_to_end(h); tier[where[h]].move_to_end(h); dead.pop(h, None)
            if use_slru:
                if h in prot: prot.move_to_end(h)
                else:
                    prob.pop(h, None); prot[h] = True
                    while len(prot) > cap // 3: d_, _ = prot.popitem(last=False); prob[d_] = True
            if oracle: nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
            continue
        if test:
            st["miss"] += 1; ls_ = last_state.get(h)
            if ls_ == "bypassed": st["miss_bypassed"] += 1
            elif ls_ == "evicted": st["miss_evicted"] += 1
            else: st["miss_new"] += 1
            if usable: usable = False; k_ = len(req_hs) - 1; rem = (R[ri].get("input_length") or len(R[ri]["hashes"]) * TOK) - k_ * TOK; st["ttft"] += A.r0 * rem + A.r1 * (rem * rem / 2 + k_ * TOK * rem)
        def _adm(x):
            if admlog is not None and test and not reuse: admlog.append(x)
        if oracle:
            if nu[i] == INF: st["bypass"] += 1; st["bypass_total"] += 1; last_state[h] = "bypassed"; _adm(0); continue
            if n[0] + n[1] >= cap:
                while heap:
                    negn, b = heap[0]
                    if b in where and nuv[b] == -negn: break
                    heapq.heappop(heap)
                if -heap[0][0] <= nu[i]: st["bypass"] += 1; st["bypass_total"] += 1; last_state[h] = "bypassed"; _adm(0); continue
                heapq.heappop(heap); remove(b, t); tgt = 0 if n[0] < nslot[0] else 1
            else: tgt = 0 if n[0] < nslot[0] else 1
            _adm(1); place(h, tgt, i); continue
        if use_split:
            tgt = 0 if (int(h[:12], 16) % 1000) < A.share * 1000 else 1                           # deterministic tier assignment
            if n[tgt] >= nslot[tgt]: remove(next(iter(tier[tgt])), t)
            place(h, tgt, i); continue
        if defer and ri in final_call: st["bypass"] += 1; continue                            # store deferred past the request end, dropped on the end decision
        j_ = len(req_hs) - 1
        def _bypass():
            st["bypass"] += 1; st["bypass_total"] += 1; last_state[h] = "bypassed"; _adm(0)
            if nu[i] < INF:
                st["bypass_reused"] += 1; dt_ = acc[nu[i]][0] - t; st["bypass_reused_60"] += (dt_ <= 60); st["bypass_reused_300"] += (dt_ <= 300)
        if static_rule is not None and j_ > 0:
            kind_ = static_rule[0]; by = False
            if kind_ == "d": by = j_ >= static_rule[1]
            elif kind_ == "p": by = req_old >= static_rule[1]
            elif kind_ == "n": by = (j_ - req_old) >= static_rule[1]
            elif kind_ == "dp": by = j_ >= static_rule[1] and req_old >= static_rule[2]
            elif kind_ == "2nd": by = (not reuse) and j_ >= static_rule[1]                 # second-touch admission: a never-seen block is admitted only in the first k positions
            if by: _bypass(); continue
        if learned:
            root_ = R[ri]["hashes"][0]; dep_ = req_old                                       # continuation depth = existing-prefix length of the request (fixed 2026-10-20; the 2026-10-18 runs used the position here)
            cls_ = cls_of(h, j_, dep_, root_); blk_cls[h] = cls_; blk_root[h] = root_; blk_hit[h] = False
            if L_kind == "olr": blk_z[h] = olr_z(olr_feats(h, t, j_, dep_, root_, R[ri].get("input_length") or len(R[ri]["hashes"]) * TOK))
            if A.admit_th > 0 and L_kind in ("lhd", "olr", "cond"):
                st_ = cls_stat.get(cls_) if L_kind == "lhd" else root_stat.get(root_)
                p_ = (olr_p(blk_z[h]) if olr_n[0] > 2000 else 1.0) if L_kind == "olr" else (rate(st_, t, 0.3) if st_ and st_[1] >= A.min_samples else 1.0)
                if p_ < A.admit_th and j_ > 0:
                    if A.explore > 0 and rng_c.random() < A.explore: st["explored"] += 1        # sampled admission keeps the class observable
                    else:
                        blk_cls.pop(h, None); blk_z.pop(h, None); blk_root.pop(h, None); _bypass()
                        if A.bypass_feedback:
                            dl = t + min(residence_est(t), 4 * TAU); heapq.heappush(pend_fb, (dl, h, cls_, root_)); pend_open[h] = dl; pend_cls[h] = (cls_, root_)
                        continue
        _adm(1)
        if n[0] + n[1] >= cap: remove(victim(t), t)
        place(h, 0 if n[0] < nslot[0] else 1, i)
    end_request()
    if hitlog is not None: open(f"{A.dump_hits}-{policy}-{cap}.bin", "wb").write(bytes(hitlog))
    if admlog is not None: open(f"{A.dump_admit}-{policy}-{cap}.adm", "wb").write(bytes(admlog))
    fbd = sorted(st["fb_delay"])
    res = sorted(st["res"]); t_res = res[len(res) // 2] if res else INF
    return dict(policy=policy, order=A.order, cap=cap, cap_GB=cap * A.chunk_mb / 1000, churn=A.churn, acc=st["acc"], reuse=st["reuse"], hits=st["hit"], reuse_hit_share=st["hit"] / max(1, st["reuse"]), overall_hit=st["hit"] / max(1, st["acc"]),
                usable_hits=st["usable"], usable_hit_share=st["usable"] / max(1, st["reuse"]), usable_tokens=st["usable_tok"], prompt_tokens=st["req_tok"], usable_token_share=st["usable_tok"] / max(1, st["req_tok"]),
                requests=st["req"], ttft_cold_s=st["ttft_cold"], ttft_s=st["ttft"], ttft_saved_s=st["ttft_cold"] - st["ttft"], ttft_mean_ms=1000 * st["ttft"] / max(1, st["req"]),
                ttft_saved_per_written_GB=(st["ttft_cold"] - st["ttft"]) / max(1e-9, st["written"] * A.chunk_mb / 1000),
                recomputed_tokens=st["miss"] * TOK, written_chunks=st["written"], bypassed=st["bypass"], dead_occupancy_share=st["occ_dead"] / max(1e-9, st["occ_all"]), live_occupancy_share=1 - st["occ_dead"] / max(1e-9, st["occ_all"]),
                evictions=st["evict"], evictions_before_reuse=st["evict_live"], evict_before_reuse_share=st["evict_live"] / max(1, st["evict"]), hits_under_protection=st["cov_prot"], dead_marked_but_reused=st["dead_fp"],
                bypass_total=st["bypass_total"], bypass_reused_later=st["bypass_reused"], bypass_reused_60s=st["bypass_reused_60"], bypass_reused_300s=st["bypass_reused_300"], admitted_never_reused=st["admit_never"],
                miss_after_bypass=st["miss_bypassed"], miss_after_eviction=st["miss_evicted"], miss_new=st["miss_new"], explored=st["explored"], feedback_delay_p50_s=(fbd[len(fbd) // 2] if fbd else None), feedback_delay_p90_s=(fbd[int(0.9 * (len(fbd) - 1))] if fbd else None),
                residence_est_end_s=residence_est(acc[-1][0]) if learned else None, hits_by_fifth="/".join(str(x) for x in st["hits_f"]), acc_by_fifth="/".join(str(x) for x in st["acc_f"]), freeze_at=A.freeze_at, explore=A.explore, bypass_feedback=int(A.bypass_feedback), admit_th=A.admit_th,
                residence_p50_s=t_res, W_live_mean=W_LIVE["mean"], W_live_p90=W_LIVE["p90"], P_agent_chunks_s=P_AGENT, P_bg_chunks_s=P_BG, P_total_chunks_s=P_AGENT + P_BG + A.churn, H_p50_s=H["p50"], H_p90_s=H["p90"])

POLS = A.policies.split(",")
caps = [int(c) for c in A.caps.split(",")]; rows = []
print(f"trace: {len(R)} requests ({n_churn} synthetic churn), {len(by_task)} tasks, {len(acc)} chunk accesses, {len(set(h for _, h, _ in acc))} unique chunks, test half from request {half}")
print(f"live working set (agent chunks of unfinished tasks): mean {W_LIVE['mean']:.0f} p90 {W_LIVE['p90']:.0f} max {W_LIVE['max']}; agent production {P_AGENT:.2f} chunks/s + real background {P_BG:.2f} + synthetic churn {A.churn:.2f}; reuse horizon p50 {H['p50']:.1f} s p90 {H['p90']:.1f} s (n={H['n']})")
for cap in caps:
    base = None
    for p in POLS:
        r = run(p, cap); rows.append(r)
        if p == "lru": base = r
        if base is not None and p != "lru":
            r["hits_vs_lru"] = r["hits"] - base["hits"]; r["recompute_tokens_avoided_vs_lru"] = base["recomputed_tokens"] - r["recomputed_tokens"]; r["written_vs_lru"] = r["written_chunks"] - base["written_chunks"]
        print(f"cap {cap:4d} ({r['cap_GB']:.2f} GB) churn {A.churn:4.1f} {A.order} {p:16s} reuse-hit {r['reuse_hit_share']:.3f} usable {r['usable_hit_share']:.3f} tok-share {r['usable_token_share']:.3f} ttft {r['ttft_mean_ms']:7.0f} ms written {r['written_chunks']:6d} dead-occ {r['dead_occupancy_share']:.2f} evict-live {r['evict_before_reuse_share']:.2f} res {r['residence_p50_s']:6.1f} s" + (f" hits+{r['hits_vs_lru']}" if "hits_vs_lru" in r else ""), flush=True)
os.makedirs(A.out, exist_ok=True)
keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in rows[-1], k))
with open(f"{A.out}/{A.tag}-replay.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
if A.no_fig: raise SystemExit
# figure: reuse-hit share vs capacity, and share of the oracle's gain
fig, axs = plt.subplots(1, 3, figsize=(16, 4.4)); G = {r["policy"]: {} for r in rows}
for r in rows: G[r["policy"]][r["cap"]] = r
style = {"split": ("#7f7f7f", "-"), "lru": ("#7f7f7f", "--"), "slru": ("#1f77b4", "-"), f"ttl{A.ttl.split(',')[0]}": ("#17becf", ":"), f"ttl{A.ttl.split(',')[-1]}": ("#17becf", "-."), "event_end": ("#d62728", "-"), "event_both": ("#2ca02c", "-"), "event_both+slru": ("#2ca02c", "--"), "event_end+defer": ("#d62728", ":"), "event_both+defer": ("#2ca02c", ":"), "oracle": ("k", "-")}
lab = {"split": "static split + LRU (B)", "lru": "global LRU (C)", "slru": "SLRU 1/3 (online)", "event_end": "real end events", "event_both": "real end + continue events", "event_both+slru": "real events + SLRU", "event_end+defer": "end events + deferred store", "event_both+defer": "both events + deferred store", "oracle": "block oracle (E)"}
for p in POLS:
    col, ls = style.get(p, ("#9467bd", "-")); xs = [c * A.chunk_mb / 1000 for c in caps]
    axs[0].plot(xs, [G[p][c]["reuse_hit_share"] for c in caps], color=col, ls=ls, marker="o", ms=4, label=lab.get(p, f"session TTL {p[3:]} s"))
    if p not in ("split", "lru", "oracle"):
        axs[1].plot(xs, [100 * (G[p][c]["reuse_hit_share"] - G["lru"][c]["reuse_hit_share"]) / max(1e-9, G["oracle"][c]["reuse_hit_share"] - G["lru"][c]["reuse_hit_share"]) for c in caps], color=col, ls=ls, marker="o", ms=4, label=lab.get(p, f"session TTL {p[3:]} s"))
axs[0].set_xlabel(f"host cache capacity, GB ({A.chunk_mb:.2f} MB per 256-token chunk)"); axs[0].set_ylabel("reuse-hit share (second half)"); lo = min(r["reuse_hit_share"] for r in rows); axs[0].set_ylim(max(0, lo - 0.05), 1.005); axs[0].legend(fontsize=7, loc="lower right", ncol=2); axs[0].set_xscale("log"); axs[0].set_xticks([c * A.chunk_mb / 1000 for c in caps]); axs[0].set_xticklabels([f"{c * A.chunk_mb / 1000:.1f}" for c in caps]); axs[0].set_xticks([], minor=True)
axs[0].set_title(f"Replay of the real agent trace ({len(by_task)} tasks, {len(R)} LLM calls)", fontsize=10.5)
axs[1].axhline(50, color="#d62728", ls=":", lw=1.2); axs[1].text(caps[0] * A.chunk_mb / 1000, 52, "Gate 2: 50%", color="#d62728", fontsize=9)
axs[1].set_xlabel("host cache capacity, GB"); axs[1].set_ylabel("share of the block oracle's gain over global LRU, %"); axs[1].set_ylim(-20, 145); axs[1].legend(fontsize=7, loc="upper right", ncol=2); axs[1].set_xscale("log"); axs[1].set_xticks([c * A.chunk_mb / 1000 for c in caps]); axs[1].set_xticklabels([f"{c * A.chunk_mb / 1000:.1f}" for c in caps]); axs[1].set_xticks([], minor=True)
axs[1].set_title("What the real events recover (hits)", fontsize=10.5)
for p in ("split", "slru", "event_end", "event_end+defer", "oracle"):
    col, ls = style.get(p, ("#9467bd", "-")); xs = [c * A.chunk_mb / 1000 for c in caps]
    axs[2].plot(xs, [G[p][c]["written_chunks"] * A.chunk_mb / 1000 for c in caps], color=col, ls=ls, marker="o", ms=4, label=lab.get(p, p))
axs[2].set_xlabel("host cache capacity, GB"); axs[2].set_ylabel("bytes written to the host cache, GB"); axs[2].set_ylim(0); axs[2].set_xscale("log"); axs[2].set_xticks([c * A.chunk_mb / 1000 for c in caps]); axs[2].set_xticklabels([f"{c * A.chunk_mb / 1000:.1f}" for c in caps]); axs[2].set_xticks([], minor=True)
axs[2].set_title("Writes (second half of the trace)", fontsize=10.5); axs[2].legend(fontsize=7.5, loc="center right")
fig.tight_layout(); fig.savefig(f"{A.out}/fig-agent-replay-{A.tag}.png", dpi=200); fig.savefig(f"{A.out}/fig-agent-replay-{A.tag}.svg"); plt.close(fig); print("wrote", f"{A.out}/fig-agent-replay-{A.tag}.png")
