#!/usr/bin/env python3
"""Hit-share sweep of the mixed workload (run_b.py scenario s4; 2026-11-10 admission study, Experiment C): open loop at 2 requests/s, 48
requests per point, share of external hits 0 / 0.25 / 0.5 / 0.75 / 1, short prompts (1k-2k) and long prompts (8k). Per point and server
configuration: TTFT p50 / p95 of the external hits and of the misses, mean request time of all requests, prompt tokens served per second
and the measured share of the GPU KV pool in use (time-weighted, between the point's first send and last completion).
Reads <out>/<tag>-adm-requests.csv and <out>/<tag>-adm-kv.csv (analyze_adm.py case=host,cold).
usage: table_s4.py <out> <tag> [<tag> ...] [labels=a,b,c]"""
import bisect, csv, sys
args = [a for a in sys.argv[1:] if "=" not in a]; kv = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
out, tags = args[0], args[1:]; LAB = dict(zip(tags, kv["labels"].split(","))) if "labels" in kv else {t: t for t in tags}
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def f(v): return "–" if v is None else f"{v:.2f}"
D = {}
for t in tags:
    R = [r for r in csv.DictReader(open(f"{out}/{t}-adm-requests.csv")) if (r["grp"] or "").startswith("s4-")]
    T = []; F = []; N = 1
    for r in csv.DictReader(open(f"{out}/{t}-adm-kv.csv")): T.append(float(r["t"])); F.append(int(r["free"])); N = int(r["tot"])
    for g in sorted({r["grp"] for r in R}):
        v = [r for r in R if r["grp"] == g]; t0 = min(fl(r["send"]) for r in v); t1 = max(fl(r["send"]) + fl(r["total"]) for r in v)
        i = max(0, bisect.bisect_right(T, t0) - 1); s = w = 0.0
        while i < len(T) - 1 and T[i] < t1:
            lo = max(t0, T[i]); hi = min(t1, T[i + 1])
            if hi > lo: s += (1 - F[i] / N) * (hi - lo); w += hi - lo
            i += 1
        h = [fl(r["ttft"]) for r in v if r["case"] == "host"]; c = [fl(r["ttft"]) for r in v if r["case"] == "cold"]
        D[(g, t)] = dict(nh=len(h), nc=len(c), h50=q(h, .5), h95=q(h, .95), c50=q(c, .5), c95=q(c, .95), tot=sum(fl(r["total"]) for r in v) / len(v), tps=sum(fl(r["prompt"]) for r in v) / (t1 - t0), used=s / w if w else None)
groups = sorted({g for g, _ in D}, key=lambda g: (g.split("-")[1], float(g.split("-h")[1])))
print("| prompts | share of external hits (hits / misses) | configuration | pool in use | prompt tok / s | hits: TTFT p50 / p95 (s) | misses: TTFT p50 / p95 (s) | request time, mean (s) |"); print("|---|---|---|---|---|---|---|---|")
for g in groups:
    for t in tags:
        d = D.get((g, t))
        if not d: continue
        cls = "1k–2k" if "short" in g else "8k"
        print(f"| {cls} | {g.split('-h')[1]} ({d['nh']} / {d['nc']}) | {LAB[t]} | {f(d['used'])} | {d['tps']:.0f} | {f(d['h50'])} / {f(d['h95'])} | {f(d['c50'])} / {f(d['c95'])} | {f(d['tot'])} |")
