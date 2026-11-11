#!/usr/bin/env python3
"""Tails, fairness and side effects of one trace replay across server configurations (2026-11-10 admission study, Experiment D): one row
per configuration, the companion of table_adm_primary.py. The same requests are compared in every run (the stock run, listed first, is
the reference). Columns: TTFT p99 and longest TTFT; requests with a TTFT above 30 s / above 60 s; requests whose TTFT is more than 10 %
(and 0.1 s) lower / higher than in the stock run; TTFT p50 / p95 of the prompts shorter than 2,048 tokens and of those of 8,192 tokens or
more; preemptions; prompt tokens computed per second; share of prompt tokens served from a cache (host tier / GPU prefix); GB stored in the
host tier. Reads <dir>/<tag>-adm-requests.csv and the admission streams.
usage: table_adm_tails.py <dir> <stock tag> <tag> [<tag> ...] [labels=<a>|<b>|...]"""
import csv, glob, sys
args = [a for a in sys.argv[1:] if not a.startswith("labels=")]; d, tags = args[0], args[1:]
labs = dict(zip(tags, next((a.split("=", 1)[1].split("|") for a in sys.argv[1:] if a.startswith("labels=")), tags)))
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def load(tag):
    R = {r["rid"][len(tag) + 1:]: dict(ttft=fl(r["ttft"]), total=fl(r["total"]), send=fl(r["send"]), prompt=fl(r["prompt"]), cached=fl(r["cached"]) or 0, host=fl(r["host"]) or 0, sb=fl(r["store_bytes"]) or 0)
         for r in csv.DictReader(open(f"{d}/{tag}-adm-requests.csv"))}
    pre = 0
    for fn in glob.glob(f"{d}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(fn): pre += '"ev":"preempt"' in l
    v = list(R.values()); span = max(r["send"] + r["total"] for r in v) - min(r["send"] for r in v)
    return dict(R=R, pre=pre, span=span)
D = {t: load(t) for t in tags if glob.glob(f"{d}/{t}-adm-requests.csv")}; tags = [t for t in tags if t in D]; S = D[tags[0]]["R"]
short = [k for k, r in S.items() if r["prompt"] < 2048]; long_ = [k for k, r in S.items() if r["prompt"] >= 8192]
print(f"| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = {len(short)}): TTFT p50 / p95 (s) | "
      f"prompts ≥ 8,192 tokens (n = {len(long_)}): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |")
print("|---|---|---|---|---|---|---|---|---|---|")
for t in tags:
    R = D[t]["R"]; v = list(R.values()); tt = [r["ttft"] for r in v]; ks = [k for k in S if k in R]
    lo = sum(1 for k in ks if R[k]["ttft"] < 0.9 * S[k]["ttft"] and S[k]["ttft"] - R[k]["ttft"] > 0.1); hi = sum(1 for k in ks if R[k]["ttft"] > 1.1 * S[k]["ttft"] and R[k]["ttft"] - S[k]["ttft"] > 0.1)
    g = lambda K: f"{q([R[k]['ttft'] for k in K if k in R], .5):.2f} / {q([R[k]['ttft'] for k in K if k in R], .95):.1f}"
    P = sum(r["prompt"] for r in v)
    print(f"| {labs[t]} | {q(tt, .99):.1f} / {max(tt):.1f} | {sum(1 for x in tt if x > 30)} / {sum(1 for x in tt if x > 60)} | " + ("–" if t == tags[0] else f"{100 * lo / len(ks):.0f} % / {100 * hi / len(ks):.0f} %")
          + f" | {g(short)} | {g(long_)} | {D[t]['pre']} | {sum(r['prompt'] - r['cached'] for r in v) / D[t]['span']:.0f} | {sum(r['host'] for r in v) / P:.3f} / {sum(r['cached'] - r['host'] for r in v) / P:.3f} | {sum(r['sb'] for r in v) / 1e9:.1f} |")
