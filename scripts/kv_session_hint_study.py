#!/usr/bin/env python3
"""Session-level hint study (2026-10-17, the last exploratory experiment on reuse predictability per the user's brief):
can application-level session information give data-lifetime signals that block-level prediction cannot? TRACE SIMULATION
on the Mooncake traces with the Phase 1 protocol (two halves by request count; every policy warmed on the first half and
scored on the second; 200 GiB = DRAM 64 + CXL 136 GiB, 8B blocks of 64 MiB; stores complete at once; a hit needs a resident
block). Sessions are reconstructed from prefix chains: the previous turn of a request is the request that created the
last old block of its prefix after the shared system block(s); the trace has no session ids.

Session reuse structure (reported first): share of reuses that are within-session vs cross-session; blocks shared by
several sessions; what fraction of a continued turn's blocks the next turn actually re-reads (prefix reuse ratio); gap to
the next turn; turns per session.

Policies (all over one global LRU on 200 GiB unless noted; a new block takes the slot its victim frees, DRAM-first fill):
  split            Baseline B (Phase 1): 32% of new blocks to DRAM by hash, LRU per tier
  global_lru       Baseline C
  session_ttl<T>   ONLINE session state only: blocks of sessions idle for more than T seconds are evicted first (LRU within)
  oracle_min       full block-level oracle (Belady MIN with bypass) — the ceiling
  hint:<spec>      SESSION HINT policies. spec fields (comma-separated key=value):
      mode=both|admit|evict   both: new blocks of a session that will not continue are not stored AND its resident blocks
                              become evict-first; admit: only the first; evict: only the second (everything is stored)
      bound=<s>               "continues" means "has a next turn within <s> seconds" (default: ever)
      fp=<p> fn=<p>           per-request hint errors: a dead session reported live with prob. fp, a live one dead with fn
      miss=<p>                the hint is absent with prob. miss (fallback: store, LRU — the baseline behaviour)
      delay=<s>               EVENTS-ONLY mode: no positive hints; every session is assumed live; a termination event
                              arrives <s> seconds after a session's last request and marks its blocks evict-first
      shared blocks (referenced by >= 2 sessions so far) are never marked dead by a hint
  queue<W>         SCHEDULER QUEUE signal (2026-10-17, RQ1-B): blocks referenced by requests that have ARRIVED but are not yet
                   served are protected from eviction (evicted last). The trace records arrival times and our replay serves
                   at arrival, so the queueing delay W is a scenario parameter: at time t the requests with arrival in
                   (t, t+W] are the ones a server with queueing delay W would hold in its waiting queue. W = 0 is what the
                   trace guarantees; the real c28 runs give W = lookup-to-first-token times (measured separately). Positive
                   signal only (it cannot mark a block dead); no bypass. Variants: queue<W>+slru (protected first, then
                   the segmented LRU order), queue<W>+end0 (plus the termination event at delay 0: the agent-loop signal).
  Oracle hints use the future of the trace and are labelled as such; session_ttl uses only the past.
Metrics on the test half: reuse-hit share, overall hit rate, recomputed tokens, host writes (GB, DRAM / CXL), bypassed
blocks, useful occupancy (resident blocks with a future use, sampled), occupancy-seconds spent on dead blocks (share),
mean residence time of blocks that were hit vs never hit, hits from within-session vs cross-session reuse.
usage: kv_session_hint_study.py [--traces ...] [--policies spec;spec;...] [--out dir] [--tag name] [--seed 1]"""
import argparse, collections, csv, heapq, json, os, random

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); INF = float("inf"); TOK = 512; BLOCK = 64 * 2**20
NSLOT = {0: int(64 * 2**30 // BLOCK), 1: int(136 * 2**30 // BLOCK)}; NTOT = NSLOT[0] + NSLOT[1]; SHARE = NSLOT[0] / NTOT
DEFAULT = ("split;global_lru;session_ttl300;session_ttl60;oracle_min;"
           "hint:mode=both;hint:mode=admit;hint:mode=evict;hint:mode=both,bound=300;hint:mode=both,bound=900;hint:mode=both,bound=60;"
           "hint:mode=both,fp=0.1;hint:mode=both,fp=0.3;hint:mode=both,fn=0.1;hint:mode=both,fn=0.3;hint:mode=both,fp=0.3,fn=0.3;hint:mode=both,miss=0.3;hint:mode=both,miss=0.6;"
           "hint:delay=0;hint:delay=10;hint:delay=60;hint:delay=300")
ap = argparse.ArgumentParser(); ap.add_argument("--traces", default="conversation,toolagent,synthetic"); ap.add_argument("--policies", default=DEFAULT)
ap.add_argument("--out", default=os.path.join(REPO, "experimental_results", "2026-10-17-kv-session-hint-study")); ap.add_argument("--tag", default="8b-200GiB"); ap.add_argument("--seed", type=int, default=1)
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)

# ---------------------------------------------------------------- trace + sessions
def load(trace):
    reqs = [json.loads(l) for l in open(os.path.join(REPO, "workloads", f"mooncake_{trace}_trace.jsonl"))]
    reqs = [(r["timestamp"] / 1000.0, r["hash_ids"], r["input_length"], r["output_length"]) for r in reqs]
    shared_first = {h for h, n in collections.Counter(r[1][0] for r in reqs if r[1]).items() if n >= 100}
    creator, seen = {}, set(); sess, turn, prev = [], [], []
    for ri, (t, hs, il, ol) in enumerate(reqs):
        d = 0
        for h in hs:
            if h in seen: d += 1
            else: break
        k = d
        while k > 0 and hs[k - 1] in shared_first: k -= 1
        if k == 0: sess.append(ri); turn.append(0); prev.append(None)
        else: pr = creator[hs[k - 1]]; sess.append(sess[pr]); turn.append(turn[pr] + 1); prev.append(pr)
        for h in hs:
            if h not in creator: creator[h] = ri
            seen.add(h)
    nxt_turn = [INF] * len(reqs); last_of = {}
    for ri in range(len(reqs) - 1, -1, -1):
        s = sess[ri]; nxt_turn[ri] = reqs[last_of[s]][0] if s in last_of else INF; last_of[s] = ri
    acc = []; sess_of_block = {}
    for ri, (t, hs, il, ol) in enumerate(reqs):
        for pos, h in enumerate(hs): acc.append((t, h, ri)); sess_of_block.setdefault(h, set()).add(sess[ri])
    last = {}; next_use = [INF] * len(acc)
    for i in range(len(acc) - 1, -1, -1):
        h = acc[i][1]; next_use[i] = last.get(h, INF); last[h] = i
    return dict(reqs=reqs, acc=acc, next_use=next_use, sess=sess, turn=turn, prev=prev, nxt_turn=nxt_turn, creator=creator, shared_first=shared_first, sess_of_block=sess_of_block, half=len(reqs) // 2)

def session_structure(D):
    reqs, acc, sess, turn, prev, nxt_turn, creator = D["reqs"], D["acc"], D["sess"], D["turn"], D["prev"], D["nxt_turn"], D["creator"]
    nsess = len(set(sess)); turns = collections.Counter(sess); ts = list(turns.values())
    within = cross = 0; seen = set()
    for t, h, ri in acc:
        if h in seen:
            if sess[creator[h]] == sess[ri]: within += 1
            else: cross += 1
        seen.add(h)
    shared_blocks = sum(1 for h, s in D["sess_of_block"].items() if len(s) >= 2)
    ratio_all, ratio_new, gaps = [], [], []
    seen2 = set()
    for ri, (t, hs, il, ol) in enumerate(reqs):
        new = [h for h in hs if h not in seen2]; seen2.update(hs)
        if nxt_turn[ri] < INF:
            nr = next((rj for rj in range(ri + 1, len(reqs)) if sess[rj] == sess[ri]), None)
            if nr is None: continue
            nh = set(reqs[nr][1]); ratio_all.append(sum(1 for h in hs if h in nh) / len(hs))
            if new: ratio_new.append(sum(1 for h in new if h in nh) / len(new))
            gaps.append(nxt_turn[ri] - t)
    q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
    cont = sum(1 for ri in range(len(reqs)) if nxt_turn[ri] < INF) / len(reqs)
    return dict(sessions=nsess, turns_p50=q(ts, .5), turns_p90=q(ts, .9), turns_mean=sum(ts) / len(ts), single_turn_share=sum(1 for x in ts if x == 1) / nsess,
                requests_continued=cont, reuse_within_session=within / max(1, within + cross), reuse_cross_session=cross / max(1, within + cross),
                shared_blocks_share=shared_blocks / len(creator), prefix_reuse_ratio_all_p50=q(ratio_all, .5), prefix_reuse_ratio_all_mean=sum(ratio_all) / max(1, len(ratio_all)),
                prefix_reuse_ratio_new_mean=sum(ratio_new) / max(1, len(ratio_new)), next_turn_gap_p50=q(gaps, .5), next_turn_gap_p90=q(gaps, .9),
                next_turn_within_60=sum(1 for g in gaps if g <= 60) / max(1, len(gaps)), next_turn_within_300=sum(1 for g in gaps if g <= 300) / max(1, len(gaps)), next_turn_within_900=sum(1 for g in gaps if g <= 900) / max(1, len(gaps)))

# ---------------------------------------------------------------- simulator
def parse_spec(spec):
    p = dict(mode="both", bound=INF, fp=0.0, fn=0.0, miss=0.0, delay=None)
    for kv in spec.split(","):
        if not kv: continue
        k, v = kv.split("="); p[k] = v if k == "mode" else float(v)
    return p

def run(policy, D, rng):
    reqs, acc, nu, sess, nxt_turn, creator, half = D["reqs"], D["acc"], D["next_use"], D["sess"], D["nxt_turn"], D["creator"], D["half"]
    is_hint = policy.startswith("hint:"); P = parse_spec(policy[5:]) if is_hint else {}
    qW = None; q_slru = False; q_end = False
    if policy.startswith("queue"):
        parts = policy[5:].split("+"); qW = float(parts[0]); q_slru = "slru" in parts[1:]; q_end = "end0" in parts[1:]
        if q_end: is_hint = True; P = parse_spec("delay=0")
    req_times = [r[0] for r in reqs]; pend = collections.defaultdict(int); q_hi = 0; q_lo = 0
    prob = collections.OrderedDict(); prot = collections.OrderedDict()                   # slru segments for the queue+slru variant
    ttl = float(policy[len("session_ttl"):]) if policy.startswith("session_ttl") else None
    where = {}; n = {0: 0, 1: 0}; lru = collections.OrderedDict(); tier_lru = {0: collections.OrderedDict(), 1: collections.OrderedDict()}
    dead = set(); dead_lru = collections.OrderedDict()                                 # evict-first set, LRU inside
    heap = []; nuv = {}                                                                # oracle
    sess_last = {}; sess_shared_cnt = collections.defaultdict(int); last_idx = {}
    events = []                                                                        # (t_mark, session) termination events (delay mode)
    sess_hint = {}                                                                     # per request: reported "continues"
    st = dict(acc=0, reuse=0, hits=[0, 0], hit_within=0, hit_cross=0, miss=0, comp=0, bypass=0, st_bytes=[0, 0], evict=0, premature=0, occ_samples=0, occ_useful=0, dead_occ=0.0, occ_all=0.0,
              res_hit=[0.0, 0], res_nohit=[0.0, 0])
    stored_at = {}; hit_since_store = set()
    seen = set(); test = False; last_t = None
    def place(h, t_tier, i):
        where[h] = t_tier; n[t_tier] += 1; lru[h] = True; tier_lru[t_tier][h] = True; st["st_bytes"][t_tier] += BLOCK; stored_at[h] = acc[i][0]
        if q_slru: prob[h] = True
        if policy == "oracle_min": nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
    def remove(h, now, i_next):
        t_tier = where.pop(h); n[t_tier] -= 1; lru.pop(h, None); tier_lru[t_tier].pop(h, None); dead.discard(h); dead_lru.pop(h, None); nuv.pop(h, None); prob.pop(h, None); prot.pop(h, None)
        st["evict"] += 1; st["premature"] += (i_next < INF)
        r = now - stored_at.pop(h, now)
        if h in hit_since_store: st["res_hit"][0] += r; st["res_hit"][1] += 1; hit_since_store.discard(h)
        else: st["res_nohit"][0] += r; st["res_nohit"][1] += 1
        return t_tier
    def victim(now):
        if policy == "oracle_min": return None
        if qW is not None:
            for cand_src in ((dead_lru,) if dead_lru else ()) + ((prob, prot) if q_slru else (lru,)):
                scanned = 0
                for b in cand_src:
                    if pend.get(b, 0) == 0: return b
                    scanned += 1
                    if scanned > 256: break
            return next(iter(lru))                                                          # everything pending: plain LRU
        if dead_lru: return next(iter(dead_lru))
        if ttl is not None:
            for h in lru:                                                              # scan a bounded number of LRU candidates for an idle session
                if now - sess_last.get(sess[creator[h]], now) > ttl: return h
                break
        if policy == "split": return None
        return next(iter(lru))
    def mark_dead(h):
        if h in where and h not in dead and sess_shared_cnt[h] < 2: dead.add(h); dead_lru[h] = True
    def mark_live(h):
        if h in dead: dead.discard(h); dead_lru.pop(h, None)
    cur_req = -1; req_blocks = []
    for i, (t, h, ri) in enumerate(acc):
        if ri != cur_req:
            # a new request: finish the previous one (hints at request completion), process due termination events
            if is_hint and cur_req >= 0 and P["delay"] is None and P["mode"] in ("both", "evict"):
                if not sess_hint.get(cur_req, True):
                    for b in req_blocks: mark_dead(b)
                else:
                    for b in req_blocks: mark_live(b)
            if is_hint and P["delay"] is not None:
                if cur_req >= 0 and nxt_turn[cur_req] == INF: heapq.heappush(events, (reqs[cur_req][0] + P["delay"], cur_req))
                while events and events[0][0] <= t:
                    _, rq = heapq.heappop(events)
                    for b in reqs[rq][1]: mark_dead(b)
            cur_req = ri; req_blocks = list(reqs[ri][1])
            if ri >= half: test = True
            sess_last[sess[ri]] = t
            if is_hint and P["delay"] is None:
                cont = nxt_turn[ri] < INF and (nxt_turn[ri] - t <= P["bound"])
                if rng.random() < P["miss"]: rep = None
                else:
                    rep = cont
                    if cont and rng.random() < P["fn"]: rep = False
                    if (not cont) and rng.random() < P["fp"]: rep = True
                sess_hint[ri] = rep if rep is not None else True
        if qW is not None:
            while q_hi < len(reqs) and req_times[q_hi] <= t + qW:
                for b in reqs[q_hi][1]: pend[b] += 1
                q_hi += 1
            while q_lo < len(reqs) and req_times[q_lo] <= t:
                for b in reqs[q_lo][1]: pend[b] -= 1
                q_lo += 1
        last_idx[h] = i; s_here = sess[ri]
        if h in D["sess_of_block"] and s_here not in getattr(run, "_dummy", ()): pass
        # count sessions that reference the block so far (shared detection)
        if creator[h] != ri or True:
            key = (h, s_here)
            if key not in seen_pairs: seen_pairs.add(key); sess_shared_cnt[h] += 1
        reuse = h in seen; seen.add(h)
        if test:
            st["acc"] += 1; st["reuse"] += reuse
            if i % 1000 == 0 and where:
                st["occ_samples"] += 1; st["occ_useful"] += sum(1 for b in where if nu[last_idx[b]] < INF) / len(where)
            if last_t is not None and where:
                dt = t - last_t; st["occ_all"] += dt * len(where); st["dead_occ"] += dt * sum(1 for b in where if nu[last_idx[b]] == INF)
        last_t = t
        if h in where:                                                                 # hit
            if test:
                st["hits"][where[h]] += 1
                if sess[creator[h]] == s_here: st["hit_within"] += 1
                else: st["hit_cross"] += 1
            hit_since_store.add(h); lru.move_to_end(h); tier_lru[where[h]].move_to_end(h)
            if q_slru:
                if h in prot: prot.move_to_end(h)
                else:
                    prob.pop(h, None); prot[h] = True
                    while len(prot) > NTOT // 3: d_, _ = prot.popitem(last=False); prob[d_] = True
            if policy == "oracle_min": nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
            if h in dead_lru: dead_lru.move_to_end(h)
            if is_hint and P["delay"] is None and P["mode"] in ("both", "evict") and sess_hint.get(ri, True): mark_live(h)
            continue
        if test: st["miss"] += 1; st["comp"] += (not reuse)
        # admission
        if policy == "oracle_min":
            if nu[i] == INF: st["bypass"] += test; continue
            if n[0] + n[1] >= NTOT:
                while heap:
                    negn, b = heap[0]
                    if b in where and nuv[b] == -negn: break
                    heapq.heappop(heap)
                if -heap[0][0] <= nu[i]: st["bypass"] += test; continue
                heapq.heappop(heap); tgt = remove(b, t, -negn)
            else: tgt = 0 if n[0] < NSLOT[0] else 1
            place(h, tgt, i); continue
        if is_hint and P["delay"] is None and P["mode"] in ("both", "admit") and not sess_hint.get(ri, True) and sess_shared_cnt[h] < 2:
            st["bypass"] += test; continue
        if policy == "split":
            tgt = 0 if ((h * 0xD6E8FEB86659FD93) >> 40) % 1000 < SHARE * 1000 else 1
            if n[tgt] >= NSLOT[tgt]: v = next(iter(tier_lru[tgt])); remove(v, t, nu[last_idx[v]])
            place(h, tgt, i); continue
        if n[0] + n[1] >= NTOT:
            v = victim(t); tgt = remove(v, t, nu[last_idx[v]])
        else: tgt = 0 if n[0] < NSLOT[0] else 1
        place(h, tgt, i)
        if is_hint and P["delay"] is None and P["mode"] in ("both", "evict") and not sess_hint.get(ri, True): mark_dead(h)
    hits = st["hits"][0] + st["hits"][1]
    return dict(policy=policy, acc=st["acc"], reuse=st["reuse"], hits=hits, reuse_hit_share=hits / max(1, st["reuse"]), overall_hit_rate=hits / max(1, st["acc"]), hit_within_share=st["hit_within"] / max(1, hits),
                recomputed_tokens=st["miss"] * TOK, dram_GB=st["st_bytes"][0] / 1e9, cxl_GB=st["st_bytes"][1] / 1e9, bypassed=st["bypass"], premature_share=st["premature"] / max(1, st["evict"]),
                useful_occupancy=st["occ_useful"] / max(1, st["occ_samples"]), dead_occupancy_share=st["dead_occ"] / max(1e-9, st["occ_all"]),
                residence_hit_s=st["res_hit"][0] / max(1, st["res_hit"][1]), residence_nohit_s=st["res_nohit"][0] / max(1, st["res_nohit"][1]))

seen_pairs = set()
rows = []; structure = {}
for trace in A.traces.split(","):
    D = load(trace); structure[trace] = session_structure(D)
    S = structure[trace]
    print(f"## {trace}: {S['sessions']} sessions; turns/session mean {S['turns_mean']:.2f} p50 {S['turns_p50']} p90 {S['turns_p90']}; single-turn sessions {100 * S['single_turn_share']:.0f}%; requests with a next turn {100 * S['requests_continued']:.0f}%")
    print(f"   reuses within-session {100 * S['reuse_within_session']:.0f}% / cross-session {100 * S['reuse_cross_session']:.0f}%; blocks shared by >= 2 sessions {100 * S['shared_blocks_share']:.1f}%")
    print(f"   next turn re-reads {100 * S['prefix_reuse_ratio_all_mean']:.0f}% of the turn's blocks on average (p50 {100 * S['prefix_reuse_ratio_all_p50']:.0f}%), {100 * S['prefix_reuse_ratio_new_mean']:.0f}% of its NEW blocks; gap to the next turn p50 {S['next_turn_gap_p50']:.0f} s p90 {S['next_turn_gap_p90']:.0f} s; within 60 / 300 / 900 s: {100 * S['next_turn_within_60']:.0f} / {100 * S['next_turn_within_300']:.0f} / {100 * S['next_turn_within_900']:.0f}%")
    for pol in A.policies.split(";"):
        seen_pairs = set(); rng = random.Random(A.seed)
        r = run(pol, D, rng); r["trace"] = trace; rows.append(r)
        print(f"   {pol:34s} reuse-hit {r['reuse_hit_share']:.3f} overall {r['overall_hit_rate']:.3f} within-session hits {100 * r['hit_within_share']:.0f}% recompute {r['recomputed_tokens'] / 1e6:5.1f} Mtok writes {r['dram_GB'] + r['cxl_GB']:6.0f} GB bypass {r['bypassed']:6d} useful-occ {r['useful_occupancy']:.2f} dead-occ {r['dead_occupancy_share']:.2f} residence hit/no-hit {r['residence_hit_s']:.0f}/{r['residence_nohit_s']:.0f} s", flush=True)
json.dump(structure, open(os.path.join(A.out, f"session-structure-{A.tag}.json"), "w"), indent=1)
with open(os.path.join(A.out, f"session-hints-{A.tag}.csv"), "w") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", os.path.join(A.out, f"session-hints-{A.tag}.csv"))
