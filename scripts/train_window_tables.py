#!/usr/bin/env python3
"""Tables of the training part of the 2026-10-27 exploratory study from the sweep CSVs of train_prefetch_sim.py in <sim dir>.
Per sweep (label): hit rate per window W (rows) and capacity C (columns), with storage traffic, late prefetches and stall time at a
few windows; the smallest window reaching 95% of the curve's plateau per capacity (W95); the capacity table at W = 0 (LRU retention)
against the analytic LRU-under-reshuffle formula H0(c) = c + (1 - c) ln(1 - c), c = C / dataset.  usage: train_window_tables.py <sim dir> [dataset GiB]"""
import csv, glob, math, os, sys
D = sys.argv[1]; DS = float(sys.argv[2]) if len(sys.argv) > 2 else 165.8
def fl(r, k, d=0.0):
    try: return float(r.get(k) or d)
    except (ValueError, TypeError): return d
for f in sorted(glob.glob(f"{D}/*.csv")):
    if "pilot" in f or "fit" in f: continue
    rows = list(csv.DictReader(open(f)))
    if not rows: continue
    lab = rows[0]["label"]; caps = sorted({fl(r, "cap_gib") for r in rows}); wins = sorted({fl(r, "window_s") for r in rows})
    g = {(fl(r, "cap_gib"), fl(r, "window_s")): r for r in rows}
    print(f"\n### {os.path.basename(f)} — {lab}\n")
    print("| W (s) | " + " | ".join(f"C = {c:g} GiB" if c < 1e9 else "C = ∞" for c in caps) + " |"); print("|---|" + "---|" * len(caps))
    for W in wins:
        print(f"| {W:g} | " + " | ".join((f"{fl(g[(c, W)], 'hit_rate'):.3f}" if (c, W) in g else "–") for c in caps) + " |")
    if len(wins) > 1:
        print("\n| capacity | H(0) | plateau H(max W) | W95 (s): smallest W with H ≥ H0 + 0.95 (H1 − H0) | storage GB at W = 0 / W95 / max W | prefetch GB at W95 | late prefetches at W95 / max W | stall s at W = 0 / W95 | lead p50 s at W95 |"); print("|---|---|---|---|---|---|---|---|---|")
        for c in caps:
            cur = [(W, g[(c, W)]) for W in wins if (c, W) in g]
            if len(cur) < 2: continue
            H0 = fl(cur[0][1], "hit_rate"); H1 = max(fl(r, "hit_rate") for _, r in cur); thr = H0 + 0.95 * (H1 - H0)
            w95 = next(((W, r) for W, r in cur if fl(r, "hit_rate") >= thr - 1e-9), cur[-1])
            print(f"| {c:g} | {H0:.3f} | {H1:.3f} | {w95[0]:g} | {fl(cur[0][1], 'storage_GB'):.0f} / {fl(w95[1], 'storage_GB'):.0f} / {fl(cur[-1][1], 'storage_GB'):.0f} | {fl(w95[1], 'prefetch_GB'):.0f} | {int(fl(w95[1], 'miss_late'))} / {int(fl(cur[-1][1], 'miss_late'))} | {fl(cur[0][1], 'stall_s'):.0f} / {fl(w95[1], 'stall_s'):.0f} | {w95[1].get('lead_p50_s') or '–'} |")
    if len(caps) > 2 and len(wins) == 1:
        print("\n| capacity | c = C / D | measured LRU hit (W = 0) | analytic c + (1 − c) ln(1 − c) | naive c²/2 | 'cached fraction' c |"); print("|---|---|---|---|---|---|")
        for c in caps:
            if c >= 1e9: continue
            x = c / DS; H = x + (1 - x) * math.log(1 - x) if x < 1 else 1.0
            print(f"| {c:g} GiB | {x:.2f} | {fl(g[(c, wins[0])], 'hit_rate'):.3f} | {H:.3f} | {min(1, x * x / 2):.3f} | {min(1, x):.2f} |")
