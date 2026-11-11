#!/usr/bin/env python3
"""Cross-load matrix of the 2026-11-10 admission study (report section C2.6): rows = server configurations, columns = replay families (each with
its own stock run on its node). Cell: change of the mean TTFT of all requests / of the mean request time / of the mean TTFT of the stock run's
misses, against that family's stock run, and the longest TTFT (s). A dash where the configuration was not run in the family.
usage: table_adm_cross.py <column label>=<dir>:<stock tag> [...] -- <row label>=<col index>:<tag>,<col index>:<tag>,... [...]
       (column indices start at 1; one row per configuration)"""
import csv, os, sys
a = sys.argv[1:]; k = a.index("--"); cols = []; 
for c in a[:k]:
    lab, rest = c.split("=", 1); d, st = rest.rsplit(":", 1); cols.append((lab, d, st))
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else None
def load(d, t): return {r["rid"][len(t) + 1:]: dict(cat=r["cat"], ttft=fl(r["ttft"]), total=fl(r["total"])) for r in csv.DictReader(open(f"{d}/{t}-adm-requests.csv"))}
S = [load(d, st) if os.path.exists(f"{d}/{st}-adm-requests.csv") else None for _, d, st in cols]
def stats(R, ref):
    miss = [k_ for k_, r in ref.items() if r["cat"] == "miss<10%"]
    return dict(a=mean([r["ttft"] for r in R.values()]), rt=mean([r["total"] for r in R.values()]), m=mean([R[k_]["ttft"] for k_ in miss if k_ in R]), mx=max(r["ttft"] for r in R.values()))
B = [stats(s, s) if s else None for s in S]
print("| configuration | " + " | ".join(lab for lab, _, _ in cols) + " |"); print("|---|" + "---|" * len(cols))
print("| stock: mean TTFT / mean request time / misses' mean TTFT / longest TTFT (s) | " + " | ".join("–" if b is None else f"{b['a']:.2f} / {b['rt']:.1f} / {b['m']:.2f} / {b['mx']:.0f}" for b in B) + " |")
for row in a[k + 1:]:
    lab, rest = row.split("=", 1); cells = ["–"] * len(cols)
    for it in rest.split(","):
        i, t = it.split(":"); i = int(i) - 1; d = cols[i][1]
        if S[i] is None or not os.path.exists(f"{d}/{t}-adm-requests.csv"): continue
        x = stats(load(d, t), S[i]); b = B[i]; p = lambda key: f"{100 * (x[key] - b[key]) / b[key]:+.0f} %"
        cells[i] = f"{p('a')} / {p('rt')} / {p('m')} / {x['mx']:.0f}"
    print(f"| {lab} | " + " | ".join(cells) + " |")
