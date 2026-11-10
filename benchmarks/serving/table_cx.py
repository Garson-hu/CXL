#!/usr/bin/env python3
"""Comparison table of controlled multi-probe scenarios (run_adm.py plans c2, c3, a3 parts) over server configurations:
per trial and probe position, TTFT p50 (s) with the gate of the first admission attempt ("ok" or the refusing gate; "skip" if the
policy set the request aside before any attempt) and, below, totals of refused attempts, preemptions and unfinished probes.
Reads <out>/<tag>-adm-requests.csv (analyze_adm.py case=host,cold), <out>/<tag>-client.jsonl and the admission stream.
usage: table_cx.py <out> <trial-regex> <tag> [<tag> ...]      e.g. table_cx.py . 'c3-hol' c3-base c3-skip2"""
import csv, glob, json, re, sys
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def med(v):
    v = sorted(x for x in v if x is not None); return v[len(v) // 2] if v else None
out, rx = sys.argv[1], sys.argv[2]; tags = sys.argv[3:]; D = {}; TOT = {}
for tag in tags:
    n_pre = 0; n_runfail = 0
    for f in glob.glob(f"{out}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(f):
            if '"preempt"' in l: n_pre += 1
            elif '"runfail"' in l: n_runfail += 1
    cl = [json.loads(l) for l in open(f"{out}/{tag}-client.jsonl")]
    probes = [c for c in cl if c["case"] in ("host", "cold")]
    TOT[tag] = dict(pre=n_pre, runfail=n_runfail, sent=len(probes), failed=sum(1 for c in probes if c["status"] != 200 or c.get("error")), refused=0)
    for r in csv.DictReader(open(f"{out}/{tag}-adm-requests.csv")):
        m = re.match(rf"{re.escape(tag)}-({rx})-r(\d+)-p(\d+)-(host|cold)-L(\d+)$", r["rid"])
        if not m: continue
        TOT[tag]["refused"] += int(r["n_refused"] or 0)
        D.setdefault((m.group(1), int(m.group(3)), m.group(4), int(m.group(5))), {}).setdefault(tag, []).append(r)
L = ["| trial | probe | " + " | ".join(tags) + " |", "|---|---|" + "---|" * len(tags)]
for key in sorted(D):
    tr, pos, ty, Lp = key; cells = []
    for t in tags:
        v = D[key].get(t)
        if not v: cells.append("–"); continue
        g = {}
        for r in v: g[r["first_gate"] or "none"] = g.get(r["first_gate"] or "none", 0) + 1
        cells.append(f"{med([fl(r['ttft']) for r in v]):.2f} ({', '.join(f'{k}:{n}' for k, n in sorted(g.items()))})")
    L.append(f"| {tr} | #{pos + 1} {'hit' if ty == 'host' else 'miss'} {Lp - 256 if Lp % 1024 else Lp} | " + " | ".join(cells) + " |")
L.append(""); L.append("| total | " + " | ".join(tags) + " |"); L.append("|---|" + "---|" * len(tags))
for k, lab in (("sent", "probes sent"), ("failed", "probes failed or timed out"), ("refused", "refused admission attempts of probes"), ("pre", "preemptions (all requests)"), ("runfail", "running requests that could not get their next chunk")):
    L.append(f"| {lab} | " + " | ".join(str(TOT[t][k]) for t in tags) + " |")
print("\n".join(L))
