#!/usr/bin/env python3
"""Summary of experimental_results/2026-10-06-optane-control/: PM and DRAM write capacity vs threads, PM read capacity, and the
DRAM reader beside writers into DRAM vs into PM (medians over repetitions)."""
import csv, statistics as st, collections, sys
d = sys.argv[1] if len(sys.argv) > 1 else "/home/ghu4/CXL/experimental_results/2026-10-06-optane-control"
def load(f):
    g = collections.defaultdict(list)
    for r in csv.DictReader(open(f)): g[r["tag"]].append(float(r["bandwidth_gib_s"]))
    return {k: st.median(v) for k, v in g.items()}
agg = load(f"{d}/aggressor.csv"); mat = load(f"{d}/matrix.csv")
pm = sorted({k.split("node")[1].split("-")[0] for k in agg if k.startswith("wo-") and "node0" not in k})
print("write-only capacity, GiB/s (threads 1/2/4/8/16):")
for node in ["0"] + pm:
    for kind in ("nt", "plain"):
        print(f"  node {node} {kind:5s} " + "  ".join(f"{agg.get(f'wo-{kind}-node{node}-w{w}', float('nan')):5.1f}" for w in (1, 2, 4, 8, 16)))
print("read-only 8 threads: " + "  ".join(f"node {n}: {mat.get(f'ro-node{n}-t8', float('nan')):.1f}" for n in ["0"] + pm) + f"   4-thread reader idle: {mat.get('ro-idle', float('nan')):.1f}")
print("4-thread DRAM reader beside writers (GiB/s; writers' own rate in parentheses):")
for node in ["0"] + pm:
    for mode, kind in (("stream-write-nt", "NT"), ("stream-write", "plain")):
        print(f"  writers into node {node} {kind:5s} " + "  ".join(f"w{w}: {mat.get(f'rw-{mode}-node{node}-w{w}', float('nan')):5.1f} ({agg.get(f'rw-{mode}-node{node}-w{w}', float('nan')):5.1f})" for w in (4, 8, 16)))
