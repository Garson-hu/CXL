#!/usr/bin/env python3
"""Bounded-reservation scenario (run_adm.py plan=c5; 2026-11-10 admission study, Experiment B): a 16k external hit that does not fit
arrives first, a stream of 2k misses that fit follows (one every 0.15 s for 4.5 s), one of ten holders is released 1.0, 2.5 and 4.0 s
after the hit. Per server configuration (medians over the repetitions): when the hit's load is admitted and its TTFT; how many misses
are admitted before the hit and when the first one is; TTFT p50 / p95 / max of the misses; mean request time of all 31 probes; refused
admission attempts; preemptions; blocks kept free for the passed hit (time-weighted mean while it waits, from the policy's hres events).
Reads <out>/<tag>-adm-requests.csv (analyze_adm.py case=host,cold) and the admission stream.
usage: table_c5.py <out> <tag> [<tag> ...] [labels=<a>|<b>|...]"""
import csv, glob, json, sys
args = [a for a in sys.argv[1:] if not a.startswith("labels=")]; out, tags = args[0], args[1:]
labs = dict(zip(tags, next((a.split("=", 1)[1].split("|") for a in sys.argv[1:] if a.startswith("labels=")), tags)))
def fl(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
med = lambda v: q(v, .5)
print("| configuration | hit: load admitted at (s) | hit: TTFT (s) | misses admitted before the hit (of 30) | first miss admitted at (s) | misses: TTFT p50 / p95 / max (s) | all 31 probes: mean request time (s) | refused attempts of the hit | preemptions | blocks kept free for the hit while it waits |")
print("|---|---|---|---|---|---|---|---|---|---|")
for tag in tags:
    rows = list(csv.DictReader(open(f"{out}/{tag}-adm-requests.csv"))); reps = sorted({r["rid"].split("-c5-res-r")[1].split("-")[0] for r in rows if "-c5-res-r" in r["rid"]})
    pre = 0; hres = []
    for f in glob.glob(f"{out}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(f):
            if '"ev":"preempt"' in l: pre += 1
            elif '"ev":"hres"' in l: d = json.loads(l); hres.append((d["t"], d["r"]))
    hres.sort(); A = []; T = []; NB = []; F = []; M50 = []; M95 = []; MX = []; TOT = []; REF = []; HR = []
    for rep in reps:
        v = [r for r in rows if f"-c5-res-r{rep}-" in r["rid"]]; hit = [r for r in v if r["case"] == "host"]; miss = [r for r in v if r["case"] == "cold"]
        if not hit or fl(hit[0]["t_adm"]) is None: continue
        h = hit[0]; t0 = fl(h["send"]); ta = fl(h["t_adm"]); A.append(ta - t0); T.append(fl(h["ttft"])); REF.append(fl(h["n_refused"]) or 0)
        ma = [fl(r["t_adm"]) for r in miss if fl(r["t_adm"]) is not None]; NB.append(sum(1 for x in ma if x < ta)); F.append(min(ma) - t0 if ma else None)
        mt = [fl(r["ttft"]) for r in miss]; M50.append(q(mt, .5)); M95.append(q(mt, .95)); MX.append(max(mt)); TOT.append(sum(fl(r["total"]) for r in v) / len(v))
        s = w = 0.0
        for n, (t, r) in enumerate(hres):
            t2 = hres[n + 1][0] if n + 1 < len(hres) else ta
            lo = max(t, t0); hi = min(t2, ta)
            if hi > lo: s += r * (hi - lo); w += hi - lo
        HR.append(s / (ta - t0) if hres and ta > t0 else None)
    f = lambda v, n=2: "–" if v is None else f"{v:.{n}f}"
    print(f"| {labs[tag]} | {f(med(A))} | {f(med(T))} | {f(med(NB), 0)} | {f(med(F))} | {f(med(M50))} / {f(med(M95))} / {f(med(MX))} | {f(med(TOT))} | {f(med(REF), 0)} | {pre} | {f(med(HR), 0)} |")
