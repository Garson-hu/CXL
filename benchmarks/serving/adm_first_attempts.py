#!/usr/bin/env python3
"""First admission attempt of every request against the GPU KV occupancy at that instant (2026-11-10 admission study, analysis
questions 1-3 of Experiment A): refusals / attempts per band of the used share of the pool, separately for external loads and for
compute requests (misses and GPU-prefix hits), with the blocks needed and the blocks free at refused and admitted attempts; and the
requests whose GPU-cached prefix shrank between their first visit and their admission (evicted while they waited).
A second table (if <out>/<tag>-adm-requests.csv of analyze_adm.py exists) gives, for the requests admitted as external loads, the wait
from queueing to the admission of the load by length of the loaded prefix, split by whether a prefill was in flight at arrival.
Reads the admission stream <out>/<tag>-vllmevt.adm.*.jsonl. Writes <out>/tables-first-<tag>.md and prints it.
usage: adm_first_attempts.py <out> <tag> [<tag> ...]"""
import glob, json, sys
def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))] if v else None
BANDS = [(0, 0.5), (0.5, 0.75), (0.75, 0.9), (0.9, 0.95), (0.95, 0.98), (0.98, 1.01)]
out = sys.argv[1]
for tag in sys.argv[2:]:
    first = {}; fpoll = {}; fok = {}; tot = None
    for f in glob.glob(f"{out}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(f):
            if '"ev":"adm"' in l:
                d = json.loads(l)
                if d["comp"] == 0 and d["rid"] not in first: first[d["rid"]] = d
                if d["ok"] and d["rid"] not in fok: fok[d["rid"]] = d
            elif '"ev":"poll"' in l:
                d = json.loads(l); fpoll.setdefault(d["rid"], d)
            elif tot is None and '"ev":"kv"' in l: tot = json.loads(l)["tot"]
    L = [f"## First admission attempts of `{tag}` (pool {tot} blocks)\n",
         "| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |", "|---|---|---|---|---|---|---|---|---|"]
    det = []
    for kind, sel in (("external load", lambda d: d["as"]), ("compute request (miss or GPU-prefix hit)", lambda d: not d["as"])):
        v = [d for d in first.values() if sel(d)]; cells = []
        for lo, hi in BANDS:
            w = [d for d in v if lo <= 1 - d["free"] / tot < hi]; cells.append(f"{sum(1 for d in w if not d['ok'])} / {len(w)}")
        L.append(f"| {kind} | {len(v)} | {sum(1 for d in v if not d['ok'])} | " + " | ".join(cells) + " |")
        ref = [d for d in v if not d["ok"]]; okv = [d for d in v if d["ok"]]
        if ref:
            gates = {g: sum(1 for d in ref if d["gate"] == g) for g in sorted({d["gate"] for d in ref})}
            det.append(f"- {kind}, refused at the first attempt ({len(ref)}): blocks of the full sequence p10 / p50 / p90 = {q([d['full'] for d in ref], .1)} / {q([d['full'] for d in ref], .5)} / {q([d['full'] for d in ref], .9)}; "
                       f"free blocks {q([d['free'] for d in ref], .1)} / {q([d['free'] for d in ref], .5)} / {q([d['free'] for d in ref], .9)}; needed / free p50 {q([d['full'] / max(1, d['free']) for d in ref], .5):.2f}; "
                       f"used share of the pool p10 / p50 {q([1 - d['free'] / tot for d in ref], .1):.3f} / {q([1 - d['free'] / tot for d in ref], .5):.3f}; gate {gates}")
        if okv:
            det.append(f"- {kind}, admitted at the first attempt ({len(okv)}): blocks of the full sequence p50 / p90 = {q([d['full'] for d in okv], .5)} / {q([d['full'] for d in okv], .9)}; free blocks p10 / p50 {q([d['free'] for d in okv], .1)} / {q([d['free'] for d in okv], .5)}; "
                       f"smallest free / needed ratio {min(d['free'] / max(1, d['full']) for d in okv):.2f}")
    n = lost = seen = 0; as_load = 0
    for rid, d in fpoll.items():
        a = fok.get(rid)
        if a is None: continue
        seen += d["loc"]
        if a["loc"] < d["loc"]: n += 1; lost += d["loc"] - a["loc"]; as_load += bool(a["as"])
    det.append(f"- GPU-cached prefix at the first visit: {seen} tokens over {len(fpoll)} requests; {n} requests had lost part of it by the time they were admitted "
               f"({lost} tokens, {100 * lost / max(1, seen):.1f} %); {as_load} of them were then admitted as external loads")
    L2 = []; ap = f"{out}/{tag}-adm-requests.csv"
    import csv, os
    if os.path.exists(ap):
        fl = lambda x: float(x) if x not in ("", None) else None
        R = [r for r in csv.DictReader(open(ap)) if (fl(r["ext"]) or 0) > 0 and fl(r["t_adm"]) is not None and fl(r["t_q"]) is not None]
        L2 = ["", f"### External loads of `{tag}` by length of the loaded prefix: wait from queueing to the admission of the load (s)", "",
              "| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |", "|---|---|---|---|---|---|---|---|"]
        for lo, hi, lab in ((0, 2048, "< 2k"), (2048, 4096, "2k–4k"), (4096, 8192, "4k–8k"), (8192, 10 ** 9, "≥ 8k")):
            v = [r for r in R if lo <= fl(r["ext"]) < hi]
            if not v: continue
            w = [fl(r["t_adm"]) - fl(r["t_q"]) for r in v]; a = [fl(r["t_adm"]) - fl(r["t_q"]) for r in v if (fl(r["arr_infl"]) or 0) == 0]; b = [fl(r["t_adm"]) - fl(r["t_q"]) for r in v if (fl(r["arr_infl"]) or 0) > 0]
            pq = lambda x: "–" if not x else f"{len(x)}, {q(x, .5):.2f}"
            L2.append(f"| {lab} | {len(v)} | {q([fl(r['need_full']) for r in v], .5):.0f} | {sum(1 for r in v if (fl(r['n_refused']) or 0) > 0)} | {q(w, .5):.2f} / {sum(w) / len(w):.2f} | {pq(a)} | {pq(b)} | {q([fl(r['ttft']) for r in v], .5):.2f} |")
    T = "\n".join(L) + "\n\n" + "\n".join(det) + "\n" + "\n".join(L2) + ("\n" if L2 else ""); open(f"{out}/tables-first-{tag}.md", "w").write(T); print(T)
