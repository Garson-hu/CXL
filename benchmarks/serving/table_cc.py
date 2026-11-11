#!/usr/bin/env python3
"""Mixed workloads (run_b.py s1-s3; 2026-11-10 admission study, Experiment C): chosen scenarios across server configurations of one pool.
Per scenario and configuration: TTFT p50 / p95 of the external hits and of the misses (by request type), completed requests per second,
mean request time of all requests, time-weighted share of the GPU KV pool in use during the scenario, and refused admission attempts /
preemptions of the whole run. Reads <out>/<tag>-adm-requests.csv, <tag>-adm-kv.csv (analyze_adm.py case=host,cold) and the admission stream.
usage: table_cc.py <out> <scenario,scenario,...> <tag> [<tag> ...] [labels=<a>|<b>|...]"""
import bisect, csv, glob, sys
args = [a for a in sys.argv[1:] if not a.startswith("labels=")]; out, scen, tags = args[0], args[1].split(","), args[2:]
labs = dict(zip(tags, next((a.split("=", 1)[1].split("|") for a in sys.argv[1:] if a.startswith("labels=")), tags)))
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
NAME = {"s1-c": "closed loop, {} in the system", "s2-r": "open loop, {} requests/s", "s3-k": "bursts of {}"}
print("| scenario | configuration | pool in use | hits: TTFT p50 / p95 (s) | misses: TTFT p50 / p95 (s) | requests / s | request time, mean (s) |"); print("|---|---|---|---|---|---|---|")
tot = {}
for g in scen:
    for t in tags:
        R = [r for r in csv.DictReader(open(f"{out}/{t}-adm-requests.csv")) if r["grp"] == g]
        if not R: continue
        T = []; F = []; N = 1
        for r in csv.DictReader(open(f"{out}/{t}-adm-kv.csv")): T.append(float(r["t"])); F.append(int(r["free"])); N = int(r["tot"])
        t0 = min(fl(r["send"]) for r in R); t1 = max(fl(r["send"]) + fl(r["total"]) for r in R); i = max(0, bisect.bisect_right(T, t0) - 1); s = w = 0.0
        while i < len(T) - 1 and T[i] < t1:
            lo = max(t0, T[i]); hi = min(t1, T[i + 1])
            if hi > lo: s += (1 - F[i] / N) * (hi - lo); w += hi - lo
            i += 1
        h = [fl(r["ttft"]) for r in R if r["case"] == "host"]; c = [fl(r["ttft"]) for r in R if r["case"] == "cold"]
        print(f"| {NAME[g[:4]].format(g[4:])} | {labs[t]} | {s / w:.2f} | {q(h, .5):.2f} / {q(h, .95):.2f} | {q(c, .5):.2f} / {q(c, .95):.2f} | {len(R) / (t1 - t0):.2f} | {sum(fl(r['total']) for r in R) / len(R):.2f} |")
for t in tags:
    ref = pre = 0
    for f in glob.glob(f"{out}/{t}-vllmevt.adm.*.jsonl"):
        for l in open(f):
            if '"ev":"adm"' in l and '"ok":false' in l: ref += 1
            elif '"ev":"preempt"' in l: pre += 1
    tot[t] = (ref, pre)
print("\nWhole run: refused admission attempts / preemptions — " + "; ".join(f"{labs[t]} {tot[t][0]} / {tot[t][1]}" for t in tags))
