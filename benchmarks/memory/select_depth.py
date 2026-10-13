#!/usr/bin/env python3
"""Bucket-depth sweep (2026-10-13): table and selection. Depth 1 rows come from the calibration (opt-<cfg>-budget<B>),
depths 2/4/8 from the sweep directory (opt-<cfg>-d<D>-budget<B>), same trace segment and neighbour (Adam). Per
configuration: for each depth the feasible budgets (the budget and every smaller swept budget meet the SLO, p99 <= slo),
then the (depth, budget) pair with the highest hit share among all feasible pairs = the budget family's best safe setting
when the depth is free (rule 2 extended to the pair). Writes <depth_dir>/chosen-depth.txt lines "opt <cfg> depth D budget B".
usage: select_depth.py <calib_dir> <depth_dir> [slo_pct=7]"""
import csv, os, re, sys
from collections import defaultdict

C, D = sys.argv[1], sys.argv[2]; SLO = float(sys.argv[3]) if len(sys.argv) > 3 else 7.0
rows = defaultdict(dict)    # (cfg, depth) -> budget -> row
for d, pat in ((C, r"opt-(\w+-\d+x)-budget([\d.]+)$"), (D, r"opt-(\w+-\d+x)-d(\d+)-budget([\d.]+)$")):
    for r in csv.DictReader(open(os.path.join(d, "summary.csv"))):
        m = re.match(pat, r["tag"])
        if not m: continue
        cfg = m.group(1); depth = 1 if d == C else int(m.group(2)); b = float(m.group(len(m.groups())))
        rows[(cfg, depth)][b] = r
out = open(os.path.join(D, "chosen-depth.txt"), "w")
for cfg in sorted({c for c, _ in rows}):
    print(f"## {cfg} next to Adam (calibration segment); hit / p99 / DRAM GB/s (20 ms peak) / budget utilization")
    feas = []
    for depth in sorted(d for c, d in rows if c == cfg):
        cells = []; ok = True
        for b, r in sorted(rows[(cfg, depth)].items()):
            p99 = float(r["slow_p99"]); ok = ok and p99 == p99 and p99 <= SLO
            if ok: feas.append((float(r["hit_share"]), depth, b))
            cells.append(f"B{b:g}: {float(r['hit_share']):.3f} / {p99:+.1f}% / {float(r['store_dram']):.1f} ({float(r['dram_peak20']):.0f}) / {float(r['budget_util']):.2f}{'' if ok else ' X'}")
        print(f"  depth {depth}: " + " | ".join(cells))
    if feas:
        h, depth, b = max(feas); out.write(f"opt {cfg} depth {depth} budget {b:g}\n"); print(f"  -> chosen depth {depth}, budget {b:g} GB/s (hit {h:.3f})")
out.close()
