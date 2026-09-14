#!/usr/bin/env python3
"""Summarize 3c stencil runs: steady-state median step time (steps >= 4) per config, median over reps."""
import csv, glob, os, statistics as st, collections, re
D='experimental_results/2026-09-14-stencil-3c/'
per=collections.defaultdict(list)   # (world,name,store) -> list of per-rep medians
for f in sorted(glob.glob(D+'*.csv')):
    b=os.path.basename(f)[:-4]
    if b=='aggressor': continue
    m=re.match(r'(idle|press|press2)-(.+)-(normal|nt)-r(\d+)$',b)
    if not m: continue
    rows=[r for r in csv.DictReader(open(f)) if int(r['step'])>=4]
    if not rows: continue
    per[(m[1],m[2],m[3])].append((st.median(float(r['step_s']) for r in rows),
                                  min(float(r['step_s']) for r in rows), max(float(r['step_s']) for r in rows)))
names=['A-alldram-rotate','B-rotate','B-copyback','B-migrate','B-pingpong','C-allcxl-rotate']
for world in ['idle','press2','press']:
    note={"idle":"no aggressor","press2":"80 NT writers on CCD3-7, ~280 GiB/s, VERIFIED live","press":"INVALID first attempt: aggressor still pre-touching (see doc)"}[world]
    print(f"\n## {world} — {note}  (seconds per step, steady-state median of steps 4..19, then median over reps; min–max in parens)")
    print("| policy | normal stores | NT stores |"); print("|---|---:|---:|")
    for n in names:
        cells=[]
        for stt in ['normal','nt']:
            v=per.get((world,n,stt))
            if not v: cells.append('—'); continue
            med=st.median(x[0] for x in v); lo=min(x[1] for x in v); hi=max(x[2] for x in v)
            cells.append(f"{med:.3f} ({lo:.2f}–{hi:.2f}) n={len(v)}")
        print(f"| {n} | {cells[0]} | {cells[1]} |")
