#!/usr/bin/env python3
"""Mixed workloads across GPU KV pool sizes (run_b.py s1-s3; 2026-11-10 admission study, Experiment C): the condensed matrix of the report.
One column per pool size; per scenario four rows (TTFT p50 of the external hits, TTFT p50 of the misses, completed requests per second, mean
request time), each cell "stock → P1 / P2"; then the measured share of the pool in use in the stock run and the refused admission attempts and
preemptions of each whole run. Reads <dir>/<tag>-adm-requests.csv, <tag>-adm-kv.csv (analyze_adm.py case=host,cold) and the admission streams.
usage: table_cc_matrix.py <dir> <scenario,scenario,...> <pool>=<stock tag>,<P1 tag>,<P2 tag> [<pool>=... ...]"""
import bisect, csv, glob, sys
d, scen = sys.argv[1], sys.argv[2].split(","); pools = [(a.split("=")[0], a.split("=")[1].split(",")) for a in sys.argv[3:]]
NAME = {"s1-c": "closed loop, {} in the system", "s2-r": "open loop, {} requests/s", "s3-k": "bursts of {}"}
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def load(tag):
    R = list(csv.DictReader(open(f"{d}/{tag}-adm-requests.csv"))); T = []; F = []; N = 1
    for r in csv.DictReader(open(f"{d}/{tag}-adm-kv.csv")): T.append(float(r["t"])); F.append(int(r["free"])); N = int(r["tot"])
    ref = pre = 0
    for fn in glob.glob(f"{d}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(fn):
            if '"ev":"adm"' in l and '"ok":false' in l: ref += 1
            elif '"ev":"preempt"' in l: pre += 1
    return dict(R=R, T=T, F=F, N=N, ref=ref, pre=pre)
def scen_stats(D, g):
    R = [r for r in D["R"] if r["grp"] == g]; T, F, N = D["T"], D["F"], D["N"]
    t0 = min(fl(r["send"]) for r in R); t1 = max(fl(r["send"]) + fl(r["total"]) for r in R); i = max(0, bisect.bisect_right(T, t0) - 1); s = w = 0.0
    while i < len(T) - 1 and T[i] < t1:
        a, b = max(T[i], t0), min(T[i + 1], t1)
        if b > a: s += (1 - F[i] / N) * (b - a); w += b - a
        i += 1
    h = [fl(r["ttft"]) for r in R if r["case"] == "host"]; c = [fl(r["ttft"]) for r in R if r["case"] == "cold"]
    return dict(hit=q(h, .5), miss=q(c, .5), rps=len(R) / (t1 - t0), rt=sum(fl(r["total"]) for r in R) / len(R), used=s / max(w, 1e-9))
D = {p: [load(t) for t in tags] for p, tags in pools}
print("| scenario | quantity (stock → P1 / P2) | " + " | ".join(f"pool {int(p):,} blocks" for p, _ in pools) + " |"); print("|---|---|" + "---|" * len(pools))
for g in scen:
    S = {p: [scen_stats(x, g) for x in D[p]] for p, _ in pools}; nm = NAME[g[:4]].format(g[4:])
    for lab, k, n in (("external hits: TTFT p50 (s)", "hit", 2), ("misses: TTFT p50 (s)", "miss", 2), ("completed requests / s", "rps", 2), ("request time, mean (s)", "rt", 2)):
        print(f"| {nm} | {lab} | " + " | ".join(f"{S[p][0][k]:.{n}f} → {S[p][1][k]:.{n}f} / {S[p][2][k]:.{n}f}" for p, _ in pools) + " |")
    print(f"| {nm} | pool in use, measured: stock / P1 / P2 | " + " | ".join(" / ".join(f"{x['used']:.2f}" for x in S[p]) for p, _ in pools) + " |")
print("| whole run | refused admission attempts: stock / P1 / P2 | " + " | ".join(" / ".join(str(x["ref"]) for x in D[p]) for p, _ in pools) + " |")
print("| whole run | preemptions: stock / P1 / P2 | " + " | ".join(" / ".join(str(x["pre"]) for x in D[p]) for p, _ in pools) + " |")
