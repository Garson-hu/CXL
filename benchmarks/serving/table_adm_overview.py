#!/usr/bin/env python3
"""Overview of the trace replays of the 2026-11-10 admission study (Experiment D): one row per metric, one column per replay
configuration, each cell "stock -> prototype (change)". Request classes are fixed by the STOCK run's category (the same requests on
both sides); changes are relative to stock (seconds for the absolute columns in table_adm_d.py's per-configuration tables).
Reads <dir>/<tag>-adm-requests.csv (analyze_adm.py), <dir>/<tag>-client.jsonl and the admission streams.
usage: table_adm_overview.py <label>=<dir>:<stock tag>,<prototype tag> [<label>=...]"""
import csv, glob, json, sys
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else None
def load(d, tag):
    R = {r["rid"][len(tag) + 1:]: dict(cat=r["cat"], ttft=fl(r["ttft"]), total=fl(r["total"]), send=fl(r["send"]), prompt=fl(r["prompt"]), cached=fl(r["cached"]) or 0, host=fl(r["host"]) or 0, sb=fl(r["store_bytes"]) or 0)
         for r in csv.DictReader(open(f"{d}/{tag}-adm-requests.csv"))}
    pre = 0
    for f in glob.glob(f"{d}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(f): pre += '"ev":"preempt"' in l
    v = list(R.values()); span = max(r["send"] + r["total"] for r in v) - min(r["send"] for r in v)
    return dict(R=R, pre=pre, span=span)
cols = []
for a in sys.argv[1:]:
    lab, rest = a.split("=", 1); d, tg = rest.split(":"); s, p = tg.split(","); cols.append((lab, load(d, s), load(d, p)))
def cell(a, b, d=2, pct=True):
    if a is None or b is None: return "–"
    return f"{a:.{d}f} → {b:.{d}f}" + (f" ({100 * (b - a) / a:+.0f} %)" if pct and a else "")
CATS = (("host≥50%", "host-dominant hits"), ("GPU≥50%", "GPU-prefix hits"), ("10–50%", "partial hits"), ("miss<10%", "misses"))
rows = [("requests (host-dominant / GPU-prefix / partial / miss in the stock run)", lambda S, P: f"{len(S['R'])} ({' / '.join(str(sum(1 for r in S['R'].values() if r['cat'] == c)) for c, _ in CATS)})")]
def sel(S, P, cat): return [k for k, r in S["R"].items() if (cat is None or r["cat"] == cat) and k in P["R"]]
for cat, name in ((None, "all requests"),) + CATS:
    for lab, fn in (("TTFT p50 (s)", lambda v: q(v, .5)), ("TTFT p95 (s)", lambda v: q(v, .95)), ("TTFT mean (s)", mean)):
        rows.append((f"{name}: {lab}", (lambda cat, fn: lambda S, P: (lambda ks: cell(fn([S['R'][k]['ttft'] for k in ks]), fn([P['R'][k]['ttft'] for k in ks])) if ks else "–")(sel(S, P, cat)))(cat, fn)))
    rows.append((f"{name}: request time mean (s)", (lambda cat: lambda S, P: (lambda ks: cell(mean([S['R'][k]['total'] for k in ks]), mean([P['R'][k]['total'] for k in ks])) if ks else "–")(sel(S, P, cat)))(cat)))
rows += [("TTFT p99 / max, all requests (s)", lambda S, P: f"{q([r['ttft'] for r in S['R'].values()], .99):.1f} / {max(r['ttft'] for r in S['R'].values()):.1f} → {q([r['ttft'] for r in P['R'].values()], .99):.1f} / {max(r['ttft'] for r in P['R'].values()):.1f}"),
         ("completed requests / s", lambda S, P: cell(len(S["R"]) / S["span"], len(P["R"]) / P["span"], 3)),
         ("prompt tokens computed / s", lambda S, P: cell(sum(r["prompt"] - r["cached"] for r in S["R"].values()) / S["span"], sum(r["prompt"] - r["cached"] for r in P["R"].values()) / P["span"], 0)),
         ("share of prompt tokens served from a cache", lambda S, P: cell(sum(r["cached"] for r in S["R"].values()) / sum(r["prompt"] for r in S["R"].values()), sum(r["cached"] for r in P["R"].values()) / sum(r["prompt"] for r in P["R"].values()), 3, False)),
         ("KV stored in the host tier (GB)", lambda S, P: cell(sum(r["sb"] for r in S["R"].values()) / 1e9, sum(r["sb"] for r in P["R"].values()) / 1e9, 1)),
         ("preemptions", lambda S, P: f"{S['pre']} → {P['pre']}")]
print("| metric (stock → prototype; classes by the stock run's category) | " + " | ".join(c[0] for c in cols) + " |"); print("|---|" + "---|" * len(cols))
for lab, fn in rows: print(f"| {lab} | " + " | ".join(fn(S, P) for _, S, P in cols) + " |")
