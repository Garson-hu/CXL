#!/usr/bin/env python3
"""Write-pressure statistics after RQ1 filtering (Task A of the joint benefit analysis, 2026-10-21), from the per-wall-second
series written by kv_joint_sim.py --series (test-<cfg>-<policy>.json): mean / p50 / p90 / p99 / max of the total write rate
per second (DRAM + CXL), DRAM-only rates, the share of seconds above the CXL capacity (46 GB/s) and above the safe DRAM budget
(8 GB/s), burst statistics (runs of consecutive seconds above 46 GB/s: count, max length), CXL backlog max, and the
inter-write idle share. usage: kv_joint_pressure.py <dir> [policies] (default split_lru,value_split,indep,joint)"""
import glob, gzip, json, os, sys
def jload(p):   # the series files were gzip-compressed after the campaign (2026-10-21); either form is accepted
    if os.path.exists(p): return json.load(open(p))
    if os.path.exists(p + ".gz"): return json.load(gzip.open(p + ".gz", "rt"))
    return None
D = sys.argv[1]; pols = (sys.argv[2] if len(sys.argv) > 2 else "split_lru,value_split,indep,joint").split(",")
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else 0.0
print("| configuration | policy | total GB/s: mean / p50 / p90 / p99 / max | DRAM GB/s: mean / p99 / max | seconds > 46 GB/s total | seconds > 8 GB/s DRAM | bursts > 46 GB/s (count / longest s) | idle seconds (no write) | CXL backlog max GB |")
print("|---|---|---|---|---|---|---|---|---|")
for f in sorted(glob.glob(f"{D}/series/test-*-{pols[0]}.json") + glob.glob(f"{D}/series/test-*-{pols[0]}.json.gz")):
    f = f[:-3] if f.endswith(".gz") else f
    cfg = os.path.basename(f)[len("test-"):-len(f"-{pols[0]}.json")]
    for p in pols:
        S = jload(f"{D}/series/test-{cfg}-{p}.json")
        if not S: continue
        smin, smax = S[0]["s"], S[-1]["s"]; by = {x["s"]: x for x in S}
        # the series covers the whole trace; the scored half is its second half in wall time
        lo = smin + (smax - smin) // 2; secs = list(range(lo, smax + 1))
        tot = [by[s]["dram_gb"] + by[s]["cxl_gb"] if s in by else 0.0 for s in secs]; dr = [by[s]["dram_gb"] if s in by else 0.0 for s in secs]
        over = [x > 46 for x in tot]; bursts = []; run = 0
        for o in over:
            if o: run += 1
            elif run: bursts.append(run); run = 0
        if run: bursts.append(run)
        print(f"| {cfg} | {p} | {sum(tot) / len(tot):.2f} / {q(tot, .5):.2f} / {q(tot, .9):.2f} / {q(tot, .99):.2f} / {max(tot):.2f} | {sum(dr) / len(dr):.2f} / {q(dr, .99):.2f} / {max(dr):.2f} | {sum(over)} of {len(secs)} | {sum(1 for x in dr if x > 8)} | {len(bursts)} / {max(bursts) if bursts else 0} | {sum(1 for x in tot if x == 0)} | {max((by[s]['backlog_gb'] for s in secs if s in by), default=0):.0f} |")
