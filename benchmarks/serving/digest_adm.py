#!/usr/bin/env python3
"""One line per run of a replay family (2026-11-10 admission study): the numbers the report's prose quotes, with changes against the stock
run (listed first; classes fixed by it). usage: digest_adm.py <dir> <stock tag> <tag> [<tag> ...]"""
import csv, glob, sys
d, tags = sys.argv[1], [t for t in sys.argv[2:] if glob.glob(f"{sys.argv[1]}/{t}-adm-requests.csv")]
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else float("nan")
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else float("nan")
def load(t):
    return {r["rid"][len(t) + 1:]: dict(cat=r["cat"], ttft=fl(r["ttft"]), total=fl(r["total"]), prompt=fl(r["prompt"]), wait=fl(r["wait_total"]) or 0.0) for r in csv.DictReader(open(f"{d}/{t}-adm-requests.csv"))}
D = {t: load(t) for t in tags}; S = D[tags[0]]
cls = {n: [k for k, r in S.items() if r["cat"] == c] for n, c in (("host", "host≥50%"), ("gpu", "GPU≥50%"), ("miss", "miss<10%"))}
longs = [k for k, r in S.items() if r["prompt"] >= 8192]
base = {}
for t in tags:
    R = D[t]; v = list(R.values()); tt = [r["ttft"] for r in v]
    cur = dict(all=mean(tt), rt=mean([r["total"] for r in v]), **{n: mean([R[k]["ttft"] for k in ks if k in R]) for n, ks in cls.items()})
    if t == tags[0]: base = cur
    pc = lambda k: "" if t == tags[0] else f"({100 * (cur[k] - base[k]) / base[k]:+.0f}%)"
    print(f"{t:28s} n={len(v)} TTFT p50/p95/p99/max {q(tt, .5):.2f}/{q(tt, .95):.1f}/{q(tt, .99):.1f}/{max(tt):.1f} mean {cur['all']:.2f}{pc('all')} rt {cur['rt']:.1f}{pc('rt')} "
          f"host[{len(cls['host'])}] {cur['host']:.2f}{pc('host')} gpu[{len(cls['gpu'])}] {cur['gpu']:.2f}{pc('gpu')} miss[{len(cls['miss'])}] {cur['miss']:.2f}{pc('miss')} "
          f">30/>60 {sum(1 for x in tt if x > 30)}/{sum(1 for x in tt if x > 60)} long p50/p95 {q([R[k]['ttft'] for k in longs if k in R], .5):.1f}/{q([R[k]['ttft'] for k in longs if k in R], .95):.1f} rt-p95 {q([r['total'] for r in v], .95):.1f}")
