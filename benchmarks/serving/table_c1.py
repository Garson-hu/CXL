#!/usr/bin/env python3
"""Comparison table of the compute-contention scenario (run_adm.py plan=c1) over several server configurations: TTFT (median
of the repetitions, seconds) of the blocker miss, of the three external hits that arrive 0.5 / 2.5 / 4.5 s after it and of
the 4k miss that arrives 1.5 s after it, per blocker length; plus the blocker's completion time and the phases of the hits.
Reads <out>/<tag>-adm-requests.csv (analyze_adm.py case=host,cold). usage: table_c1.py <out> <tag> [<tag> ...]"""
import csv, re, sys
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def med(v):
    v = sorted(x for x in v if x is not None); return v[len(v) // 2] if v else None
out = sys.argv[1]; tags = sys.argv[2:]; D = {}
for tag in tags:
    for r in csv.DictReader(open(f"{out}/{tag}-adm-requests.csv")):
        m = re.match(rf"{re.escape(tag)}-c1-B(\d+)-r(\d+)-p(\d+)-(host|cold)-L(\d+)$", r["rid"])
        if m: D.setdefault((int(m.group(1)), int(m.group(3))), {}).setdefault(tag, []).append(r)
POS = {0: "blocker miss", 1: "hit +0.5 s", 2: "4k miss +1.5 s", 3: "hit +2.5 s", 4: "hit +4.5 s"}
L = ["| blocker (tokens) | probe | " + " | ".join(tags) + " |", "|---|---|" + "---|" * len(tags)]
for (Lb, pos) in sorted(D):
    L.append(f"| {Lb} | {POS.get(pos, pos)} | " + " | ".join(("–" if not D[(Lb, pos)].get(t) else f"{med([fl(r['ttft']) for r in D[(Lb, pos)][t]]):.2f}") for t in tags) + " |")
L.append(""); L.append("| blocker (tokens) | quantity | " + " | ".join(tags) + " |"); L.append("|---|---|" + "---|" * len(tags))
for Lb in sorted({k[0] for k in D}):
    L.append(f"| {Lb} | blocker request time (s) | " + " | ".join(("–" if not D[(Lb, 0)].get(t) else f"{med([fl(r['total']) for r in D[(Lb, 0)][t]]):.2f}") for t in tags) + " |")
    for ph in ("pre", "lookup", "admit", "load", "promote", "compute"):
        L.append(f"| {Lb} | hits: {ph} (s) | " + " | ".join(("–" if not any(D.get((Lb, p), {}).get(t) for p in (1, 3, 4)) else f"{med([fl(r.get('ph_' + ph)) for p in (1, 3, 4) for r in D.get((Lb, p), {}).get(t, [])]) or 0:.2f}") for t in tags) + " |")
print("\n".join(L))
