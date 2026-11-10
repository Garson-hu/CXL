#!/usr/bin/env python3
"""Tables of the controlled admission experiment (run_adm.py plan=a3): reads <out>/<tag>-adm-requests.csv (analyze_adm.py
case=host,cold) and the trial / release marks of <out>/<tag>-meta.txt; writes <out>/tables-a3-<tag>.md and prints it.
Per probe: the free blocks, the blocks needed and the gate at its first admission attempt (the scheduler's own numbers),
whether that attempt was admitted, when it was admitted relative to the controlled release of a holder, and its TTFT.
usage: table_a3.py <out> <tag>"""
import csv, json, re, sys
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def f(v, d=0, s=1.0): return "–" if v is None else f"{v * s:.{d}f}"
out, tag = sys.argv[1:3]
trials, rel = {}, {}
for l in open(f"{out}/{tag}-meta.txt"):
    p = l.split(" ", 4)
    if len(p) >= 5 and p[1] == "trial": d = json.loads(p[4]); trials[d["name"]] = d
    elif len(p) >= 5 and p[1] == "release": d = json.loads(p[4]); rel[d["name"]] = int(p[2]) / 1e9
R = []
for r in csv.DictReader(open(f"{out}/{tag}-adm-requests.csv")):
    m = re.match(rf"{re.escape(tag)}-(p\d-.+)-r(\d+)-p(\d+)-(host|cold)-L(\d+)$", r["rid"])
    if not m: continue
    tr, rep, pos, ty, L = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4), int(m.group(5)); name = f"{tr}-r{rep}"
    d = dict(tr=tr, rep=rep, pos=pos, ty=ty, L=L, name=name, ttft=fl(r["ttft"]), free=fl(r["first_free"]), ok=r["first_ok"] == "True", gate=r["first_gate"], now=fl(r["first_now"]), full=fl(r["first_full"]),
             resv=fl(r["first_resv"]), nref=int(r["n_refused"] or 0), t_adm=fl(r["t_adm"]), t_res=fl(r["t_res"]), t_q=fl(r["t_q"]), t_run=fl(r["t_run"]),
             pre=fl(r["ph_pre"]), lookup=fl(r["ph_lookup"]), admit=fl(r["ph_admit"]), load=fl(r.get("ph_load")), promote=fl(r.get("ph_promote")), compute=fl(r["ph_compute"]),
             t_rel=rel.get(name), P_h=trials.get(name, {}).get("P_h"), K=trials.get(name, {}).get("K"), free_target=trials.get(name, {}).get("free_target"))
    d["adm_after_rel"] = (d["t_adm"] - d["t_rel"]) if (d["t_adm"] is not None and d["t_rel"] is not None) else None
    d["wait_adm"] = (d["t_adm"] - d["t_res"]) if (d["t_adm"] is not None and d["t_res"] is not None) else None
    R.append(d)
L_ = []
def gates(v): return "/".join(f"{g}:{sum(1 for d in v if d['gate'] == g)}" for g in ("ok", "full", "free", "resv") if any(d["gate"] == g for d in v))
def row(key, v):
    return (f"| {key} | {len(v)} | {f(q([d['full'] for d in v], .5))} / {f(q([d['now'] for d in v], .5))} | {f(q([d['free'] for d in v], .5))} ({f(min(d['free'] for d in v))}–{f(max(d['free'] for d in v))}) | {f(q([d['resv'] for d in v], .5))} | "
            f"{gates(v)} | {f(q([d['wait_adm'] for d in v], .5), 2)} | {f(q([d['adm_after_rel'] for d in v], .5), 2)} | {f(q([d['ttft'] for d in v], .5), 2)} ({f(min(d['ttft'] for d in v), 2)}–{f(max(d['ttft'] for d in v), 2)}) |")
HDR = ["| {} | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |", "|---|---|---|---|---|---|---|---|---|"]
P1 = [d for d in R if d["tr"].startswith("p1-")]
if P1:
    L_.append("### Table A3-1 — one probe under K = 6 decoding holders: external hit vs miss of the same length at three levels of free blocks\n")
    L_.append(HDR[0].format("probe (L + tail), target free / need, type")); L_.append(HDR[1])
    for Lp in sorted({d["L"] for d in P1}):
        for rho in ("3", "1.5", "0.6"):
            for ty in ("host", "cold"):
                v = [d for d in P1 if d["L"] == Lp and d["ty"] == ty and d["tr"].split("-")[2] == f"f{rho}"]
                if v: L_.append(row(f"{Lp} tok, {rho}×, {ty}", v))
P2 = [d for d in R if d["tr"].startswith("p2-")]
if P2:
    L_.append("\n### Table A3-2 — the same probe (4,096 + tail tokens) with 4 and 12 holders: the number of running requests at equal free blocks\n")
    L_.append(HDR[0].format("holders K, target free / need, type")); L_.append(HDR[1])
    for K in sorted({d["K"] for d in P2 if d["K"]}):
        for rho in ("1.5", "0.6"):
            for ty in ("host", "cold"):
                v = [d for d in P2 if d["K"] == K and d["ty"] == ty and d["tr"].split("-")[2] == f"f{rho}"]
                if v: L_.append(row(f"K = {K}, {rho}×, {ty}", v))
for part, title in (("p3-", "two probes 5 ms apart, 700 free blocks targeted (not enough for both); a holder is released 3 s later"),
                    ("p5-", "two probes 5 ms apart, no memory pressure (more than 5,000 free blocks)")):
    V = [d for d in R if d["tr"].startswith(part)]
    if not V: continue
    L_.append(f"\n### Table A3-{part[1]} — {title}\n")
    L_.append(HDR[0].format("order, position: probe")); L_.append(HDR[1])
    for tr in sorted({d["tr"] for d in V}):
        for pos in sorted({d["pos"] for d in V if d["tr"] == tr}):
            v = [d for d in V if d["tr"] == tr and d["pos"] == pos]
            L_.append(row(f"{tr[3:]}, #{pos + 1}: {v[0]['ty']} {v[0]['L']}", v))
P4 = [d for d in R if d["tr"].startswith("p4-")]
if P4:
    L_.append("\n### Table A3-4 — bursts of 4 and 8 probes of 2,048 + tail tokens, alternating external hit / miss, free blocks for half of the burst\n")
    L_.append("| burst | type | n | admitted at the first attempt | admitted before the release | refused first: gate full / free / resv | TTFT p50 (s) | admitted after the release p50 (s) |"); L_.append("|---|---|---|---|---|---|---|---|")
    for tr in sorted({d["tr"] for d in P4}):
        for ty in ("host", "cold"):
            v = [d for d in P4 if d["tr"] == tr and d["ty"] == ty]
            if not v: continue
            before = sum(1 for d in v if d["adm_after_rel"] is not None and d["adm_after_rel"] < 0)
            L_.append(f"| {tr[3:]} | {ty} | {len(v)} | {sum(1 for d in v if d['ok'])} | {before} | {sum(1 for d in v if d['gate'] == 'full')} / {sum(1 for d in v if d['gate'] == 'free')} / {sum(1 for d in v if d['gate'] == 'resv')} | {f(q([d['ttft'] for d in v], .5), 2)} | {f(q([d['adm_after_rel'] for d in v if d['adm_after_rel'] is not None and d['adm_after_rel'] >= 0], .5), 2)} |")
L_.append("\n### Table A3-6 — phases of the probes (seconds, median): lookup result → admitted, load, promotion, compute\n")
L_.append("| group | type | n | queued → first visit | lookup | admit | load | promote | compute | TTFT |"); L_.append("|---|---|---|---|---|---|---|---|---|---|")
for part in ("p1-", "p2-", "p3-", "p4-", "p5-"):
    for ty in ("host", "cold"):
        v = [d for d in R if d["tr"].startswith(part) and d["ty"] == ty]
        if v: L_.append(f"| part {part[1]} | {ty} | {len(v)} | " + " | ".join(f(q([d[k] for d in v], .5), 3) for k in ("pre", "lookup", "admit", "load", "promote", "compute", "ttft")) + " |")
T = "\n".join(L_) + "\n"; open(f"{out}/tables-a3-{tag}.md", "w").write(T); print(T)
