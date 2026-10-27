#!/usr/bin/env python3
"""Future-window evaluation of the inference policies (C4 of the 2026-10-27 exploratory study): hit rates of each policy over evaluation
horizons after the scoring boundary (the first H seconds of the scored half, H = 60 / 300 / 900 / 1800 s, and the whole half), from the
per-access hit bitmaps written by kv_admission_sim.py --dump-hits (<hits>/<trace>-cap<N>-<policy>-<cap>.bin: one byte per scored
access in trace order: 1 hit, 0 miss (new), 2 miss after bypass, 3 miss after eviction) and the trace's timestamps. Hits here are plain
hits (served), not prefix-usable hits. usage: kv_horizon_eval.py <trace.jsonl> <hits dir> <trace name> <cap> [--mooncake] [--policies a,b,c]"""
import argparse, glob, json, os
ap = argparse.ArgumentParser(); ap.add_argument("trace"); ap.add_argument("hits"); ap.add_argument("name"); ap.add_argument("cap", type=int); ap.add_argument("--mooncake", action="store_true")
ap.add_argument("--policies", default=""); ap.add_argument("--horizons", default="60,300,900,1800"); ap.add_argument("--score-range", default="0.5,1.0")
A = ap.parse_args(); HS = [float(x) for x in A.horizons.split(",")]
R = []
for l in open(A.trace):
    r = json.loads(l)
    if A.mooncake: R.append((r["timestamp"] / 1000.0, len(r["hash_ids"]), 0))
    else: R.append((r["t_lookup"], len(r["hashes"]), r.get("task", 0)))
R.sort(key=lambda x: x[0]); NR = len(R); s0, s1 = (float(x) for x in A.score_range.split(",")); LO, HI = int(s0 * NR), int(s1 * NR)
ts = [t for ri in range(LO, HI) if R[ri][2] >= 0 for t in [R[ri][0]] * R[ri][1]]      # one timestamp per scored block access
T0 = ts[0]
files = sorted(glob.glob(f"{A.hits}/{A.name}-cap{A.cap}-*-{A.cap}.bin"))
pols = A.policies.split(",") if A.policies else None
print(f"| policy | " + " | ".join(f"first {int(H)} s: hits / accesses (rate)" for H in HS) + " | whole half (rate) | misses after eviction (whole) |"); print("|---|" + "---|" * (len(HS) + 2))
for f in files:
    pol = os.path.basename(f)[len(f"{A.name}-cap{A.cap}-"):-len(f"-{A.cap}.bin")]
    if pols and pol not in pols: continue
    b = open(f, "rb").read()
    if len(b) != len(ts): print(f"| {pol} | length mismatch {len(b)} vs {len(ts)} |"); continue
    cells = []
    for H in HS:
        n = sum(1 for t in ts if t - T0 <= H); h = sum(1 for i in range(n) if b[i] == 1); cells.append(f"{h} / {n} ({h / max(1, n):.3f})")
    h = b.count(1); print(f"| {pol} | " + " | ".join(cells) + f" | {h / len(b):.3f} | {b.count(3)} |")
