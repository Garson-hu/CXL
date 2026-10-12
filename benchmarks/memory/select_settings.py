#!/usr/bin/env python3
"""Pick the safe settings from the CALIBRATION runs of the budget-gated admission experiment (2026-10-12), before any
evaluation run, by a fixed rule. Per neighbour, configuration and family (split share, budget GB/s):
  feasible = the swept values v such that v and every smaller value meet the SLO (p99 during <= (1 + slo) x quiet p99;
             slow_p99 of analyze_bga.py);
  chosen   = the feasible value with the highest hit share — the family's best safe setting (rule 2, 2026-10-12 17:15;
             rule 1 took the largest feasible value, which for the split next to the reader picked 48%, a share with a
             LOWER hit share than 32%); when the family is overloaded (any run with a backlog above 100 GB: the hit share
             is then inflated by the backlog, 2026-10-11 finding) the largest feasible value instead (least backlog);
  none feasible -> 0 (no DRAM).
The oracle's budget for phases without a neighbour is the largest swept budget (no neighbour, no SLO; rule 2 — rule 1
took the best-hit budget, which in the overloaded 70B 4x picked 2 GB/s through the backlog artifact).
Writes <calib_dir>/chosen.txt: "<neighbor> <model>-<speed>x split <share>" / "... budget <GBps>" / "any <cfg> offbudget <GBps>".
usage: select_settings.py <calib_dir> [slo_pct=7]"""
import csv, os, re, sys
from collections import defaultdict

D = sys.argv[1]; SLO = float(sys.argv[2]) if len(sys.argv) > 2 else 7.0; OVER_GB = 100.0
rows = list(csv.DictReader(open(os.path.join(D, "summary.csv"))))
fam = defaultdict(list); budgets = defaultdict(set)
for r in rows:
    m = re.match(r"(\w+)-(\w+)-(\d+x)-(split|budget)([\d.]+)$", r["tag"])
    if not m: continue
    nb, model, sp, kind, val = m.groups(); v = float(val) / (100 if kind == "split" else 1)
    fam[(nb, f"{model}-{sp}", kind)].append((v, float(r["slow_p99"]), float(r["hit_share"]), float(r["backlog_max"])))
    if kind == "budget": budgets[f"{model}-{sp}"].add(v)
out = open(os.path.join(D, "chosen.txt"), "w")
for (nb, cfg, kind), xs in sorted(fam.items()):
    xs.sort(); feas = []
    for v, p99, h, bl in xs:
        if p99 == p99 and p99 <= SLO: feas.append((v, h))
        else: break
    over = any(bl > OVER_GB for _, _, _, bl in xs)
    best = 0.0 if not feas else (feas[-1][0] if over else max(feas, key=lambda x: (x[1], x[0]))[0])
    out.write(f"{nb} {cfg} {kind} {best:g}\n")
    print(f"{nb:6s} {cfg:7s} {kind:6s} -> {best:g}{' (overloaded family: largest feasible)' if over else ''}   (" + ", ".join(f"{v:g}: p99 {p99:+.1f}% hit {h:.3f} backlog {bl:.0f}" for v, p99, h, bl in xs) + ")")
for cfg, vs in sorted(budgets.items()):
    out.write(f"any {cfg} offbudget {max(vs):g}\n"); print(f"any    {cfg:7s} offbudget -> {max(vs):g} (largest swept budget)")
out.close()
