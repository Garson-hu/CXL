#!/usr/bin/env python3
"""Explain which accesses a policy hits that LRU misses (and vice versa), from the hit bitmaps of kv_agent_replay.py
--dump-hits and the trace: tabulate avoided / introduced by block position in the request, continuation depth of the
request, past uses of the block at that access and the block's age. Scored accesses = agent/trace accesses in the
second half of the request order (same convention as the replay).
usage: kv_hits_explain.py <trace> <prefix> <cap> <policy> [--mooncake]"""
import collections, json, sys
trace, prefix, cap, policy = sys.argv[1:5]; mc = "--mooncake" in sys.argv
R = []
for l in open(trace):
    r = json.loads(l)
    if mc: R.append((r["timestamp"] / 1000.0, [str(h) for h in r["hash_ids"]]))
    elif r.get("task", 0) >= 0: R.append((r["t_lookup"], list(r["hashes"])))
R.sort(key=lambda r: r[0]); half = len(R) // 2
base = open(f"{prefix}-lru-{cap}.bin", "rb").read(); pol = open(f"{prefix}-{policy}-{cap}.bin", "rb").read()
seen = collections.Counter(); first_t = {}; k = 0
T = collections.defaultdict(lambda: [0, 0, 0])            # key -> [scored accesses, avoided, introduced]
def pb(j): return "pos0-7" if j < 8 else "pos8-31" if j < 32 else "pos32+"
for ri, (t, hs) in enumerate(R):
    old = sum(1 for h in hs if h in seen); dep = "fresh" if old == 0 else "cont<8" if old < 8 else "cont8+"
    for j, h in enumerate(hs):
        if ri >= half:
            if k >= min(len(base), len(pol)): break
            b, p = base[k] == 1, pol[k] == 1; k += 1
            uses = seen[h]; ub = "new" if uses == 0 else "1" if uses == 1 else "2-4" if uses < 5 else "5+"
            age = t - first_t.get(h, t); ab = "age<60s" if age < 60 else "age<300s" if age < 300 else "age300s+"
            for key in (("position", pb(j)), ("request", dep), ("past uses", ub), ("block age", ab)):
                T[key][0] += 1; T[key][1] += (p and not b); T[key][2] += (b and not p)
        seen[h] += 1; first_t.setdefault(h, t)
print(f"{policy} vs lru at cap {cap}: scored accesses {k}, avoided {sum(v[1] for kk, v in T.items() if kk[0] == 'position')}, introduced {sum(v[2] for kk, v in T.items() if kk[0] == 'position')}")
for dim in ("position", "request", "past uses", "block age"):
    rows = [(kk[1], v) for kk, v in T.items() if kk[0] == dim]
    print(f"  by {dim}: " + "; ".join(f"{name}: n={v[0]} avoided {v[1]} ({100 * v[1] / max(1, v[0]):.1f}%) introduced {v[2]} ({100 * v[2] / max(1, v[0]):.1f}%)" for name, v in sorted(rows)))
