#!/usr/bin/env python3
"""One replay, many server configurations (2026-11-10 admission study, Experiment D): one row per configuration. Request classes are
fixed by the STOCK run (listed first): its host-dominant hits, its GPU-prefix hits and its misses are followed through every other run.
Columns: all requests TTFT p50 / p95 / p99 / mean and request time mean; TTFT p50 and mean of the stock run's host-dominant hits, GPU-prefix
hits and misses; requests whose TTFT is > 10 % (and 0.1 s) lower / higher than in the stock run; longest TTFT; prompt tokens computed per
second; share of prompt tokens served from a cache; GB stored in the host tier; preemptions; time-weighted share of the pool in use.
Reads <dir>/<tag>-adm-requests.csv, <dir>/<tag>-adm-kv.csv (analyze_adm.py) and the admission streams.
usage: table_adm_variants.py <dir> <stock tag> <tag> [<tag> ...] [labels=<a>|<b>|...]"""
import csv, glob, sys
args = [a for a in sys.argv[1:] if not a.startswith("labels=")]; d, tags = args[0], args[1:]
labs = dict(zip(tags, next((a.split("=", 1)[1].split("|") for a in sys.argv[1:] if a.startswith("labels=")), tags)))
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else None
def load(tag):
    R = {r["rid"][len(tag) + 1:]: dict(cat=r["cat"], ttft=fl(r["ttft"]), total=fl(r["total"]), send=fl(r["send"]), prompt=fl(r["prompt"]), cached=fl(r["cached"]) or 0, sb=fl(r["store_bytes"]) or 0)
         for r in csv.DictReader(open(f"{d}/{tag}-adm-requests.csv"))}
    pre = 0
    for f in glob.glob(f"{d}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(f): pre += '"ev":"preempt"' in l
    T = [(float(r["t"]), int(r["free"]), int(r["tot"])) for r in csv.DictReader(open(f"{d}/{tag}-adm-kv.csv"))]
    used = sum((1 - T[i][1] / T[i][2]) * (T[i + 1][0] - T[i][0]) for i in range(len(T) - 1)) / max(1e-9, T[-1][0] - T[0][0])
    v = list(R.values()); span = max(r["send"] + r["total"] for r in v) - min(r["send"] for r in v)
    return dict(R=R, pre=pre, span=span, used=used)
D = {t: load(t) for t in tags if glob.glob(f"{d}/{t}-adm-requests.csv")}; tags = [t for t in tags if t in D]; S = D[tags[0]]["R"]
cls = {c: [k for k, r in S.items() if r["cat"] == c] for c in ("host≥50%", "GPU≥50%", "miss<10%")}
f = lambda v, n=2: "–" if v is None else f"{v:.{n}f}"
print(f"| configuration | all requests: TTFT p50 / p95 / p99 / mean (s) | request time mean (s) | host-dominant hits of the stock run (n = {len(cls['host≥50%'])}): TTFT p50 / mean | GPU-prefix hits (n = {len(cls['GPU≥50%'])}): TTFT p50 / mean | misses (n = {len(cls['miss<10%'])}): TTFT p50 / mean | requests faster / slower by > 10 % | longest TTFT (s) | prompt tok computed / s | cached share | GB stored | preemptions | pool in use |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for t in tags:
    R = D[t]["R"]; v = list(R.values()); tt = [r["ttft"] for r in v]
    def pc(c): ks = [k for k in cls[c] if k in R]; return f"{f(q([R[k]['ttft'] for k in ks], .5))} / {f(mean([R[k]['ttft'] for k in ks]))}"
    ks = [k for k in S if k in R]
    lo = sum(1 for k in ks if R[k]["ttft"] < 0.9 * S[k]["ttft"] and S[k]["ttft"] - R[k]["ttft"] > 0.1); hi = sum(1 for k in ks if R[k]["ttft"] > 1.1 * S[k]["ttft"] and R[k]["ttft"] - S[k]["ttft"] > 0.1)
    print(f"| {labs[t]} | {f(q(tt, .5))} / {f(q(tt, .95), 1)} / {f(q(tt, .99), 1)} / {f(mean(tt))} | {f(mean([r['total'] for r in v]), 1)} | {pc('host≥50%')} | {pc('GPU≥50%')} | {pc('miss<10%')} | "
          + ("–" if t == tags[0] else f"{100 * lo / len(ks):.0f} % / {100 * hi / len(ks):.0f} %") + f" | {max(tt):.1f} | {sum(r['prompt'] - r['cached'] for r in v) / D[t]['span']:.0f} | {sum(r['cached'] for r in v) / sum(r['prompt'] for r in v):.3f} | {sum(r['sb'] for r in v) / 1e9:.1f} | {D[t]['pre']} | {D[t]['used']:.2f} |")
