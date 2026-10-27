#!/usr/bin/env python3
"""Tables of the inference part of the 2026-10-27 exploratory study (window-based reuse policies vs the baselines over capacities).
Reads <dir>/<trace>-cap<N>-replay.csv (kv_admission_sim.py). Prints: (1) usable-prefix hit share per policy and capacity for each trace,
with the window-based families shown at every window; (2) the best window per family and capacity against the baselines and the online
residence; (3) writes (host writes in the scored half), evictions and residence per capacity for the baselines and the best windows;
(4) the DRAM-only 60 GiB vs DRAM + CXL 180 GiB comparison (and 30 / 120 / 360 / 720 GiB) for every family.
usage: kv_window_tables.py <dir>"""
import csv, glob, os, re, sys
D = sys.argv[1]
rows = []
for f in sorted(glob.glob(f"{D}/*-replay.csv")):
    tr = os.path.basename(f).split("-cap")[0]
    for r in csv.DictReader(open(f)): r["trace"] = tr; rows.append(r)
def fl(r, k, d=0.0):
    try: return float(r.get(k) or d)
    except (ValueError, TypeError): return d
traces = sorted({r["trace"] for r in rows}); caps = sorted({int(r["cap"]) for r in rows})
BASE = ["lru", "slru", "2nd", "2nd_int", "2nd_int_auto", "oracle"]; FAM = ["wslru", "wlfu", "wslru2nd"]
LAB = {"lru": "LRU", "slru": "SLRU", "2nd": "second touch (unbounded ghost)", "2nd_int": "second touch, gap <= residence (2nd_int)", "2nd_int_auto": "RQ1 adaptive (gap rule + regime switch, SLRU)", "oracle": "ORACLE (Belady + bypass)",
       "wslru": "window-protected LRU (wslru:W)", "wlfu": "window-LFU eviction (wlfu:W)", "wslru2nd": "window second-touch admission + window protection (wslru2nd:W)"}
def get(tr, cap, pol):
    for r in rows:
        if r["trace"] == tr and int(r["cap"]) == cap and r["policy"] == pol: return r
def fam_of(p): return p.split(":")[0]
for tr in traces:
    print(f"\n### {tr}: usable-prefix hit share (scored half) — rows: policies; columns: capacity (GiB)\n")
    cl = [c for c in caps if get(tr, c, "lru")]
    print("| policy | " + " | ".join(f"{get(tr, c, 'lru')['cap_GiB']} GiB" for c in cl) + " |"); print("|---|" + "---|" * len(cl))
    pols = BASE + sorted({r["policy"] for r in rows if r["trace"] == tr and fam_of(r["policy"]) in FAM}, key=lambda p: (FAM.index(fam_of(p)), float(p.split(":")[1])))
    for p in pols:
        vals = [get(tr, c, p) for c in cl]
        if not any(vals): continue
        print(f"| {LAB.get(p, p)} | " + " | ".join(f"{fl(v, 'usable_hit_share'):.3f}" if v else "–" for v in vals) + " |")
    print(f"\n### {tr}: best window per family and capacity (usable share; Δ vs LRU / vs SLRU / vs the RQ1 adaptive policy; online residence estimate of LRU at the end)\n")
    print("| capacity | LRU | SLRU | RQ1 adaptive | ORACLE | LRU residence p50 / est (s) | " + " | ".join(f"best {f}: W (share)" for f in FAM) + " |"); print("|---|---|---|---|---|---|" + "---|" * len(FAM))
    for c in cl:
        lru, slru, ad, orc = get(tr, c, "lru"), get(tr, c, "slru"), get(tr, c, "2nd_int_auto"), get(tr, c, "oracle")
        cells = []
        for f in FAM:
            cand = [r for r in rows if r["trace"] == tr and int(r["cap"]) == c and fam_of(r["policy"]) == f]
            if not cand: cells.append("–"); continue
            b = max(cand, key=lambda r: fl(r, "usable_hit_share")); x = fl(b, "usable_hit_share")
            cells.append(f"{b['policy'].split(':')[1]} s ({x:.3f}; {x - fl(lru, 'usable_hit_share'):+.3f} / {x - fl(slru, 'usable_hit_share'):+.3f} / {x - fl(ad, 'usable_hit_share'):+.3f})")
        print(f"| {lru['cap_GiB']} GiB | {fl(lru, 'usable_hit_share'):.3f} | {fl(slru, 'usable_hit_share'):.3f} | {fl(ad, 'usable_hit_share'):.3f} | {fl(orc, 'usable_hit_share'):.3f} | {lru['residence_p50_s']} / {lru['residence_est_end_s']} | " + " | ".join(cells) + " |")
    print(f"\n### {tr}: host writes (scored half, TB), evictions, residence p50 (s) and misses by kind\n")
    print("| capacity | policy | usable share | written TB | bypassed | evictions | residence p50 s | misses: new / after eviction / after bypass |"); print("|---|---|---|---|---|---|---|---|")
    for c in cl:
        for p in ["lru", "slru", "2nd_int_auto", "oracle"] + [max([r for r in rows if r["trace"] == tr and int(r["cap"]) == c and fam_of(r["policy"]) == f], key=lambda r: fl(r, "usable_hit_share"))["policy"] for f in FAM if any(r for r in rows if r["trace"] == tr and int(r["cap"]) == c and fam_of(r["policy"]) == f)]:
            r = get(tr, c, p)
            if r: print(f"| {r['cap_GiB']} GiB | {p} | {fl(r, 'usable_hit_share'):.3f} | {fl(r, 'written_TB'):.2f} | {int(fl(r, 'bypass_total'))} | {int(fl(r, 'evictions'))} | {r['residence_p50_s']} | {int(fl(r, 'miss_new'))} / {int(fl(r, 'miss_after_eviction'))} / {int(fl(r, 'miss_after_bypass'))} |")
print("\n### DRAM-only 60 GiB vs DRAM + CXL 180 GiB (usable share; both traces)\n")
print("| policy | conversation 60 GiB | conversation 180 GiB | gain | tool agent 60 GiB | tool agent 180 GiB | gain |"); print("|---|---|---|---|---|---|---|")
for p in ["lru", "slru", "2nd", "2nd_int", "2nd_int_auto", "wslru:100", "wlfu:100", "wslru2nd:100", "wslru2nd:300", "oracle"]:
    cells = []
    for tr in traces:
        a, b = get(tr, 915, p), get(tr, 2747, p)
        cells += [f"{fl(a, 'usable_hit_share'):.3f}" if a else "–", f"{fl(b, 'usable_hit_share'):.3f}" if b else "–", f"{fl(b, 'usable_hit_share') - fl(a, 'usable_hit_share'):+.3f}" if a and b else "–"]
    print(f"| {LAB.get(p, p)} | " + " | ".join(cells) + " |")
