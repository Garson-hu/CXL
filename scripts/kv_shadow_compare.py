#!/usr/bin/env python3
"""Selection-bias check for the adaptive admission study (2026-10-21): the class tables (P(re-lookup within w) per class)
written by kv_admission_sim.py --dump-tables under different policies must agree if the labels are policy-independent.
Compares the end-of-trace tables of several runs on the leaf classes they share, at the windows 60 / 120 / 480 s, and
prints the mean / max absolute difference and the per-class values of the largest classes.
usage: kv_shadow_compare.py <label>=<...-tables.json> [<label>=<json> ...]"""
import json, sys
runs = [a.split("=", 1) for a in sys.argv[1:]]
T = {lab: json.load(open(f))["4"] for lab, f in runs}
WG = [15, 30, 60, 120, 240, 480, 960]; idx = {60: 2, 120: 3, 480: 5}
labs = [lab for lab, _ in runs]; base = labs[0]
leaves = [k for k in T[base] if "-" not in k.split("/") and all(k in T[l] for l in labs) and min(T[l][k]["n"] for l in labs) >= 100]
print(f"{len(leaves)} leaf classes with >= 100 labelled touches in every run; windows 60 / 120 / 480 s")
for l in labs[1:]:
    for w, i in idx.items():
        d = [abs(T[base][k]["F"][i] - T[l][k]["F"][i]) for k in leaves]
        print(f"  {l} vs {base} at w={w}: mean |dF| {sum(d) / max(1, len(d)):.4f}, max {max(d) if d else 0:.4f}")
print("largest classes (c/int/pos/pre: touches-before, gap bucket, position bucket, prefix bucket): n, candidate rate /s, F(60 / 120 / 480 s) per run")
for k in sorted(leaves, key=lambda k: -T[base][k]["n"])[:12]:
    print(f"  {k}: " + " | ".join(f"{l}: n={T[l][k]['n']:.0f} rate={T[l][k]['rate']:.3f} F={T[l][k]['F'][2]:.2f}/{T[l][k]['F'][3]:.2f}/{T[l][k]['F'][5]:.2f}" for l in labs))
