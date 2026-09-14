#!/usr/bin/env python3
"""Summarize 1b DRAM write-drain matrix: medians over reps."""
import csv, statistics as st, sys, collections
D='experimental_results/2026-09-08-dram-write-drain/'
def med(rows,key): 
    v=[float(r[key]) for r in rows]; return st.median(v) if v else float('nan')
mat=collections.defaultdict(list); agg=collections.defaultdict(list); ch=collections.defaultdict(list)
for r in csv.DictReader(open(D+'1b-matrix.csv')): mat[r['tag']].append(r)
for r in csv.DictReader(open(D+'1b-aggressor.csv')): agg[r['tag']].append(r)
for r in csv.DictReader(open(D+'1b-chase.csv')): ch[r['tag']].append(r)
ceil=med(mat['1b-ro-idle'],'bandwidth_gib_s')
print(f"reader idle (4T stream-read node0 CCD0): {ceil:.1f} GiB/s  n={len(mat['1b-ro-idle'])}")
c=ch['1b-chase-idle']; print(f"chase idle: mean {med(c,'mean_ns'):.0f} p50 {med(c,'p50'):.0f} p99 {med(c,'p99'):.0f} p99.9 {med(c,'p99.9'):.0f} ns")
print()
print("| store | W (CCDs) | write-only GiB/s | reader w/ writers | writers w/ reader | sum | reader drop | chase mean/p50/p99/p99.9 ns |")
print("|---|---:|---:|---:|---:|---:|---:|---|")
for kind in ['nt','plain']:
    for W in [1,2,4,8,16,32,64,96]:
        wo=med(agg[f'1b-wo-{kind}-w{W}'],'bandwidth_gib_s')
        rd=med(mat[f'1b-rw-{kind}-w{W}'],'bandwidth_gib_s')
        wr=med(agg[f'1b-rw-{kind}-w{W}'],'bandwidth_gib_s')
        c=ch[f'1b-chase-{kind}-w{W}']
        lab=f"{W} (CCD1)" if W<=16 else f"{W} (CCD2-{1+W//16})"
        print(f"| {kind} | {lab} | {wo:.1f} | {rd:.1f} | {wr:.1f} | {rd+wr:.1f} | {ceil/rd:.2f}x (−{100*(1-rd/ceil):.0f}%) | {med(c,'mean_ns'):.0f} / {med(c,'p50'):.0f} / {med(c,'p99'):.0f} / {med(c,'p99.9'):.0f} |")

print("\n### Writer victim (4T on CCD0, node 0) under NT writers on CCD2-7")
print("| victim | idle GiB/s | under 64 NT | under 96 NT |"); print("|---|---:|---:|---:|")
for vk in ['plain','nt']:
    idle=med(mat[f'1b-wv-{vk}-idle'],'bandwidth_gib_s')
    cells=[]
    for W in [64,96]:
        v=med(mat[f'1b-wv-{vk}-w{W}'],'bandwidth_gib_s'); a=med(agg[f'1b-wv-{vk}-w{W}'],'bandwidth_gib_s')
        cells.append(f"{v:.1f} ({idle/v:.1f}x, −{100*(1-v/idle):.0f}%; aggr {a:.0f})")
    print(f"| {vk}-store | {idle:.1f} | {cells[0]} | {cells[1]} |")
