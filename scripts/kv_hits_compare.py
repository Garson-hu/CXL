#!/usr/bin/env python3
"""Per-access comparison of replay policies against global LRU from the hit bitmaps written by kv_agent_replay.py
--dump-hits (one byte per scored access, same access order for every policy): misses avoided (hit under the policy,
miss under LRU) and misses introduced (miss under the policy, hit under LRU).
usage: kv_hits_compare.py <prefix> <cap> <policy> [...]   (files <prefix>-<policy>-<cap>.bin)"""
import os, sys
prefix, cap = sys.argv[1], sys.argv[2]; pols = sys.argv[3:]
base = open(f"{prefix}-lru-{cap}.bin", "rb").read()
print(f"{'policy':16s} {'hits':>8s} {'LRU hits':>8s} {'avoided':>8s} {'introduced':>10s} {'net':>8s}  (scored accesses {len(base)}; bitmap codes 1 hit, 0 miss-new, 2 miss-after-bypass, 3 miss-after-eviction)")
for p in pols:
    f = f"{prefix}-{p}-{cap}.bin"
    if not os.path.exists(f): continue
    b = open(f, "rb").read(); n = min(len(b), len(base))
    hb = [x == 1 for x in b[:n]]; hbase = [x == 1 for x in base[:n]]
    av = sum(1 for i in range(n) if hb[i] and not hbase[i]); intro = sum(1 for i in range(n) if hbase[i] and not hb[i])
    reasons = {c: sum(1 for i in range(n) if hbase[i] and b[i] == c) for c in (0, 2, 3)}
    print(f"{p:16s} {sum(hb):8d} {sum(hbase):8d} {av:8d} {intro:10d} {av - intro:+8d}   introduced: after bypass {reasons[2]}, after eviction {reasons[3]}, other {reasons[0]}")
