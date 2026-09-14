#!/usr/bin/env python3
"""Summarize 1b2 (redo with verified overlap). Checks every victim window lies inside its aggressor's
measurement window using measure_start/end_epoch lines from membench stderr."""
import csv, re, statistics as st, collections, sys
D='experimental_results/2026-09-08-dram-write-drain/'
def med(rows,key):
    v=[float(r[key]) for r in rows]; return st.median(v) if v else float('nan')
mat=collections.defaultdict(list); agg=collections.defaultdict(list); ch=collections.defaultdict(list)
for r in csv.DictReader(open(D+'1b2-matrix.csv')): mat[r['tag']].append(r)
for r in csv.DictReader(open(D+'1b2-aggressor.csv')): agg[r['tag']].append(r)
for r in csv.DictReader(open(D+'1b2-chase.csv')): ch[r['tag']].append(r)
# overlap check: aggressor windows (tag,rep)->(start,end); victim windows from 1b2-stderr.log
def windows(path, kind):
    w={}; cur=None
    for line in open(path):
        m=re.match(rf'(aggressor|victim|chase) (\S+) rep=(\d+) (launch|start)=',line)
        if m: cur=(m[2],int(m[3])); continue
        m=re.match(r'measure_start_epoch=([\d.]+)',line)
        if m and cur: w.setdefault(cur,[None,None])[0]=float(m[1]); continue
        m=re.match(r'measure_end_epoch=([\d.]+)',line)
        if m and cur: w.setdefault(cur,[None,None])[1]=float(m[1]); continue
        m=re.match(r'aggressor (\S+) rep=(\d+) alive_after_victim=(\S+)',line)
        if m: w.setdefault((m[1],int(m[2])),[None,None]).append(m[3])
    return w
aw=windows(D+'1b2-aggressor-stderr.log','agg')
vw={}
cur=None
for line in open(D+'1b2-stderr.log'):
    m=re.match(r'(victim|chase) (\S+) rep=(\d+) start=([\d.]+)',line)
    if m: cur=(m[2],int(m[3])); vw[cur]=[float(m[4]),None]; continue
    m=re.match(r'(victim|chase) (\S+) rep=(\d+) end=([\d.]+)',line)
    if m: vw[(m[2],int(m[3]))][1]=float(m[4])
bad=[]
for (vt,rep),(vs,ve) in vw.items():
    at=vt.replace('1b2-chase-','1b2-ch-')
    if (at,rep) not in aw: continue
    a=aw[(at,rep)]
    ok = a[0] is not None and a[1] is not None and a[0] <= vs and ve <= a[1] and (len(a)<3 or a[2]=='yes')
    if not ok: bad.append((vt,rep,vs,ve,a))
print(f"overlap check: {len(vw)} victim windows, {len(bad)} NOT inside a live aggressor window")
for b in bad: print("  BAD:",b)
ceil=med(mat['1b2-ro-idle'],'bandwidth_gib_s'); c=ch['1b2-chase-idle']
print(f"\nreader idle 4T {ceil:.1f} GiB/s (n={len(mat['1b2-ro-idle'])}); 32T {med(mat['1b2-ro32-idle'],'bandwidth_gib_s'):.1f}; chase idle mean {med(c,'mean_ns'):.0f} p50 {med(c,'p50'):.0f} p99 {med(c,'p99'):.0f} p99.9 {med(c,'p99.9'):.0f}")
print(f"idle victims: plain-write 4T {med(mat['1b2-wv-plain-idle'],'bandwidth_gib_s'):.1f}, NT-write 4T {med(mat['1b2-wv-nt-idle'],'bandwidth_gib_s'):.1f}, mixed 16T (67:33) {med(mat['1b2-mixed16-idle'],'bandwidth_gib_s'):.1f}")
print("\n| aggressor | write-only* | reader 4T | aggr w/ reader | sum | reader loss | chase mean/p50/p99/p99.9 ns |")
print("|---|---:|---:|---:|---:|---:|---|")
for kind in ['nt','plain']:
    for W in [32,64,96]:
        rd=med(mat[f'1b2-rw-{kind}-w{W}'],'bandwidth_gib_s'); wr=med(agg[f'1b2-rw-{kind}-w{W}'],'bandwidth_gib_s'); c=ch[f'1b2-chase-{kind}-w{W}']
        lab=f"{W}T {kind} (CCD2–{1+W//16})"
        print(f"| {lab} | {wr:.0f} | {rd:.1f} | {wr:.0f} | {rd+wr:.0f} | {ceil/rd:.1f}× (−{100*(1-rd/ceil):.0f}%) | {med(c,'mean_ns'):.0f} / {med(c,'p50'):.0f} / {med(c,'p99'):.0f} / {med(c,'p99.9'):.0f} |")
print("\n(*aggressor bandwidth over its own 30 s window, victim inside it)")
print("\n| aggressor | reader 32T | plain-write 4T | NT-write 4T | mixed 16T |")
print("|---|---:|---:|---:|---:|")
idle={'rw32':med(mat['1b2-ro32-idle'],'bandwidth_gib_s'),'wv-plain':med(mat['1b2-wv-plain-idle'],'bandwidth_gib_s'),'wv-nt':med(mat['1b2-wv-nt-idle'],'bandwidth_gib_s'),'mixed16':med(mat['1b2-mixed16-idle'],'bandwidth_gib_s')}
for kind in ['nt','plain']:
    for W in [64,96]:
        cells=[]
        for v in ['rw32','wv-plain','wv-nt','mixed16']:
            x=med(mat[f'1b2-{v}-{kind}-w{W}'],'bandwidth_gib_s'); cells.append(f"{x:.1f} ({idle[v]/x:.1f}×, −{100*(1-x/idle[v]):.0f}%)")
        print(f"| {W}T {kind} (CCD2–{1+W//16}) | "+" | ".join(cells)+" |")
