#!/usr/bin/env python3
"""Pick the safe settings from the CALIBRATION runs of the budget-gated admission experiment (2026-10-12), before any
evaluation run, by a fixed rule: per neighbour, configuration and family (split share, budget GB/s), the largest swept
value such that it and every smaller value meet the SLO (Adam / reader p99 during <= 1.07 x its quiet p99; slow_p99 in
analyze_bga.py); none -> 0 (no DRAM). The oracle's budget for phases without a neighbour is, per configuration, the
calibration budget with the highest hit share (any neighbour). Writes <calib_dir>/chosen.txt lines
"<neighbor> <model>-<speed>x split <share>" / "... budget <GBps>" / "any <model>-<speed>x offbudget <GBps>".
usage: select_settings.py <calib_dir> [slo_pct=7]"""
import csv, os, re, sys
from collections import defaultdict

D = sys.argv[1]; SLO = float(sys.argv[2]) if len(sys.argv) > 2 else 7.0
rows = list(csv.DictReader(open(os.path.join(D, "summary.csv"))))
fam = defaultdict(list); hits = defaultdict(list)
for r in rows:
    m = re.match(r"(\w+)-(\w+)-(\d+x)-(split|budget)([\d.]+)$", r["tag"])
    if not m: continue
    nb, model, sp, kind, val = m.groups(); v = float(val) / (100 if kind == "split" else 1)
    fam[(nb, f"{model}-{sp}", kind)].append((v, float(r["slow_p99"]), float(r["hit_share"])))
    if kind == "budget": hits[f"{model}-{sp}"].append((float(r["hit_share"]), v))
out = open(os.path.join(D, "chosen.txt"), "w")
for (nb, cfg, kind), xs in sorted(fam.items()):
    xs.sort(); best = 0.0
    for v, p99, _ in xs:
        if p99 == p99 and p99 <= SLO: best = v
        else: break
    out.write(f"{nb} {cfg} {kind} {best:g}\n")
    print(f"{nb:6s} {cfg:7s} {kind:6s} -> {best:g}   (" + ", ".join(f"{v:g}: p99 {p99:+.1f}% hit {h:.3f}" for v, p99, h in xs) + ")")
for cfg, xs in sorted(hits.items()):
    h, v = max(xs); out.write(f"any {cfg} offbudget {v:g}\n"); print(f"any    {cfg:7s} offbudget -> {v:g} (hit {h:.3f})")
out.close()
