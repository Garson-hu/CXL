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
  event_end+defer / event_both+defer   as above, plus the store of a task's final call is never issued (LMCache's lazy
                 offload would hold it until the request ends; the end decision drops it) — the write-avoidance case
  oracle         Belady MIN with bypass of never-reused chunks                                     (upper bound E)
Metrics on the second half of the trace (by request order): reuse-hit share (hits / accesses to chunks seen before),
overall hit rate, recomputed tokens (misses × 256), chunks written, dead-occupancy share; share of the oracle's gain
over global LRU (the better of the two LRU baselines at small capacities). Output: <out>/<tag>-replay.csv and fig-agent-replay-<tag>.
usage: kv_agent_replay.py <trace.jsonl> <out_dir> <tag> [--caps 48,64,96,128,192,256,384] [--bound 30] [--chunk-mb 9.44]"""
import argparse, collections, csv, heapq, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser(); ap.add_argument("trace"); ap.add_argument("out"); ap.add_argument("tag")
ap.add_argument("--caps", default="48,64,96,128,192,256,384"); ap.add_argument("--bound", type=float, default=30.0); ap.add_argument("--chunk-mb", type=float, default=9.44)
ap.add_argument("--ttl", default="10,30"); ap.add_argument("--share", type=float, default=0.32)
A = ap.parse_args(); INF = float("inf"); TOK = 256
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})

R = sorted((json.loads(l) for l in open(A.trace)), key=lambda r: r["t_lookup"])
# accesses: (t, hash, request index); next-use index per access (for the oracle); task structure
acc = []; task_of = []; t_end_of = {}; next_call_t = {}
for i, r in enumerate(R):
    for h in r["hashes"]: acc.append((r["t_lookup"], h, i))
    task_of.append(r["task"]); t_end_of[r["task"]] = r.get("t_task_end") or INF
by_task = collections.defaultdict(list)
for i, r in enumerate(R): by_task[r["task"]].append(i)
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
    ev_end = policy.startswith("event"); ev_cont = policy.startswith("event_both"); oracle = policy == "oracle"; defer = "defer" in policy
    final_call = {i for i, r in enumerate(R) if r.get("decision") == "end"}                   # requests after which the runtime said "end"
    nslot = [int(cap * A.share), cap - int(cap * A.share)]; n = [0, 0]; where = {}
    lru = collections.OrderedDict(); tier = [collections.OrderedDict(), collections.OrderedDict()]
    prob = collections.OrderedDict(); prot = collections.OrderedDict()
    dead = collections.OrderedDict(); protected = {}                                # hash -> protect-until time (continue)
    refs = collections.defaultdict(set); ended = set(); task_last = {}                # hash -> tasks that referenced it; ended tasks; task -> last request time
    heap = []; nuv = {}; ei = 0
    st = dict(acc=0, reuse=0, hit=0, miss=0, written=0, bypass=0, occ_dead=0.0, occ_all=0.0); seen = set(); last_t = None; last_idx = {}
    def remove(h):
        t_ = where.pop(h); n[t_] -= 1; lru.pop(h, None); tier[t_].pop(h, None); dead.pop(h, None); prob.pop(h, None); prot.pop(h, None); nuv.pop(h, None); protected.pop(h, None)
    def place(h, t_, i):
        where[h] = t_; n[t_] += 1; lru[h] = True; tier[t_][h] = True; st["written"] += 1
        if use_slru: prob[h] = True
        if oracle: nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
    def victim(now):
        srcs = ((dead,) if dead else ()) + ((prob, prot) if use_slru else (lru,))
        for src in srcs:
            k = 0
            for b in src:
                if protected.get(b, -INF) > now: k += 1; continue
                if ttl is not None and src is lru:
                    pass
                return b
            if k > 512: break
        if ttl is not None:
            for b in lru:
                tk_ = max((tk for tk in refs[b] if tk not in ended), key=lambda tk: task_last.get(tk, -INF), default=None)
                if tk_ is None or now - task_last.get(tk_, now) > ttl: return b
                break
        return next(iter(lru))
    for i, (t, h, ri) in enumerate(acc):
        tk = task_of[ri]; task_last[tk] = t
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
        reuse = h in seen; seen.add(h); last_idx[h] = i; test = ri >= half
        if test:
            st["acc"] += 1; st["reuse"] += reuse
            if last_t is not None and where:
                dt = t - last_t; st["occ_all"] += dt * len(where); st["occ_dead"] += dt * sum(1 for b in where if nu[last_idx[b]] == INF)
        last_t = t
        if h in where:
            if test: st["hit"] += 1
            lru.move_to_end(h); tier[where[h]].move_to_end(h); dead.pop(h, None)
            if use_slru:
                if h in prot: prot.move_to_end(h)
                else:
                    prob.pop(h, None); prot[h] = True
                    while len(prot) > cap // 3: d_, _ = prot.popitem(last=False); prob[d_] = True
            if oracle: nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
            continue
        if test: st["miss"] += 1
        if oracle:
            if nu[i] == INF: st["bypass"] += 1; continue
            if n[0] + n[1] >= cap:
                while heap:
                    negn, b = heap[0]
                    if b in where and nuv[b] == -negn: break
                    heapq.heappop(heap)
                if -heap[0][0] <= nu[i]: st["bypass"] += 1; continue
                heapq.heappop(heap); remove(b); tgt = 0 if n[0] < nslot[0] else 1
            else: tgt = 0 if n[0] < nslot[0] else 1
            place(h, tgt, i); continue
        if use_split:
            tgt = 0 if (int(h[:12], 16) % 1000) < A.share * 1000 else 1                           # deterministic tier assignment
            if n[tgt] >= nslot[tgt]: remove(next(iter(tier[tgt])))
            place(h, tgt, i); continue
        if defer and ri in final_call: st["bypass"] += 1; continue                            # store deferred past the request end, dropped on the end decision
        if n[0] + n[1] >= cap: remove(victim(t))
        place(h, 0 if n[0] < nslot[0] else 1, i)
    return dict(policy=policy, cap=cap, cap_GB=cap * A.chunk_mb / 1000, acc=st["acc"], reuse=st["reuse"], hits=st["hit"], reuse_hit_share=st["hit"] / max(1, st["reuse"]), overall_hit=st["hit"] / max(1, st["acc"]),
                recomputed_tokens=st["miss"] * TOK, written_chunks=st["written"], bypassed=st["bypass"], dead_occupancy_share=st["occ_dead"] / max(1e-9, st["occ_all"]))

POLS = ["split", "lru", "slru"] + [f"ttl{t}" for t in A.ttl.split(",")] + ["event_end", "event_both", "event_both+slru", "event_end+defer", "event_both+defer", "oracle"]
caps = [int(c) for c in A.caps.split(",")]; rows = []
print(f"trace: {len(R)} requests, {len(by_task)} tasks, {len(acc)} chunk accesses, {len(set(h for _, h, _ in acc))} unique chunks, test half from request {half}")
for cap in caps:
    for p in POLS:
        r = run(p, cap); rows.append(r)
        print(f"cap {cap:4d} ({r['cap_GB']:.2f} GB) {p:16s} reuse-hit {r['reuse_hit_share']:.3f} overall {r['overall_hit']:.3f} recompute {r['recomputed_tokens'] / 1e3:7.1f} ktok written {r['written_chunks']:6d} dead-occ {r['dead_occupancy_share']:.2f}", flush=True)
os.makedirs(A.out, exist_ok=True)
with open(f"{A.out}/{A.tag}-replay.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
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
