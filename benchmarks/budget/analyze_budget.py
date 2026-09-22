#!/usr/bin/env python3
"""Phase-1 analysis: per victim, the median slowdown at every level and the DRAM write budget under a
5 / 7 / 10 % bound (linear interpolation between measured levels, on ACHIEVED write rates).
usage: analyze_budget.py <outdir> [victims...]"""
import csv, os, statistics as st, sys, collections
out = sys.argv[1]; victims = sys.argv[2:] or ["synth", "opt", "lulesh"]
def load(v):
    rows = [r for r in csv.DictReader(open(f"{out}/{v}.csv")) if r["overlap_ok"] == "1"]
    g = collections.defaultdict(list)
    for r in rows: g[(r["mode"], r["target"], int(r["asked_GiBs"]))].append((float(r["write_GiBs"]), float(r["value"]), float(r["probe_p50_ns"])))
    return g
def budget(pts, bound):
    """pts: sorted (rate, slowdown%) with (0,0) first; largest rate at which slowdown <= bound, interpolated"""
    for (r0, s0), (r1, s1) in zip(pts, pts[1:]):
        if s1 >= bound: return r0 + (r1 - r0) * (bound - s0) / (s1 - s0) if s1 > s0 else r1
    return float("nan")
summary = {}
for v in victims:
    if not os.path.exists(f"{out}/{v}.csv"): continue
    g = load(v); zero = g[("pure", "dram", 0)]; base = st.median(x[1] for x in zero); higher_is_better = v in ("synth", "llama")
    print(f"\n=== victim {v}: baseline {base:.4f} {'GiB/s read' if v == 'synth' else ('tok/s' if v == 'llama' else 's per step')} over {len(zero)} zero-level runs, spread {100*(max(x[1] for x in zero)/min(x[1] for x in zero)-1):.1f}%")
    curves = {}
    for (m, t, r), xs in sorted(g.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
        if r == 0: continue
        w = st.median(x[0] for x in xs); val = st.median(x[1] for x in xs); slow = 100 * (1 - val / base) if higher_is_better else 100 * (val / base - 1)
        curves.setdefault((m, t), [(0.0, 0.0)]).append((w, slow))
        print(f"  {m:4s} {t:12s} asked {r:4d}  achieved {w:6.2f} GiB/s  slowdown {slow:5.1f}%  probe {st.median(x[2] for x in xs):6.1f} ns  n={len(xs)}")
    for (m, t), pts in curves.items():
        pts.sort(); b = {bd: budget(pts, bd) for bd in (5, 7, 10)}; summary[(v, m, t)] = b
        print(f"  -> {m} to {t}: budget at 5% = {b[5]:5.1f}, 7% = {b[7]:5.1f}, 10% = {b[10]:5.1f} GiB/s")
print("\n=== DRAM write budget under the bound (GiB/s), achieved rates; CXL pair write capacity = 43.9")
print(f"{'victim':8s} {'stream':22s} {'5%':>7s} {'7%':>7s} {'10%':>7s}")
for (v, m, t), b in summary.items(): print(f"{v:8s} {m + ' -> ' + ('CXL' if 'dax' in t else 'DRAM'):22s} {b[5]:7.1f} {b[7]:7.1f} {b[10]:7.1f}")
