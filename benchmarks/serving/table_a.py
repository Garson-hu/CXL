#!/usr/bin/env python3
"""Result tables of Experiment A from the timeline CSVs (analyze_a.py): (1) TTFT per path and prefix length (median, min,
max, n) across the runs; (2) the stages of a host hit per tier; (3) instrumentation overhead (hooked vs hook-less run).
usage: table_a.py <A dir>  -> prints markdown and writes <A dir>/tables-a.md"""
import csv, os, sys
A = sys.argv[1]
def load(tag):
    p = f"{A}/{tag}-timeline.csv"
    if not os.path.exists(p): return []
    out = []
    for r in csv.DictReader(open(p)):
        if r["status"] != "200": continue
        out.append({k: (float(v) if v not in ("", None) and k not in ("rid", "case", "grp", "status", "error", "irid") else v) for k, v in r.items()})
    return out
def med(v): v = sorted(v); return v[len(v) // 2]
def cell(rows, case, L, key="ttft_client_ms"):
    v = [r[key] for r in rows if r["case"] == case and int(r["L"]) == L and r.get(key) is not None]
    return f"{med(v):.1f} ({min(v):.1f}–{max(v):.1f}, n={len(v)})" if v else "–"
R = {t: load(t) for t in ("a-3b-dram", "a-3b-ssd-odirect", "a-3b-ssd", "a-3b-none", "a-3b-dram-nohooks", "a-15b-dram")}
Ls = [256, 512, 1024, 2048, 4096, 8192, 16384]; out = []
out.append("### Table A-1 — TTFT at the client per path and prefix length (ms; median (min–max, n); MEASURED, 8 output tokens, CUDA graphs)\n")
paths = [("recompute (cold), LMCache DRAM tier", "a-3b-dram", "cold"), ("recompute (cold), vLLM alone", "a-3b-none", "cold"), ("GPU prefix hit, LMCache in the loop", "a-3b-dram", "gpu"), ("GPU prefix hit, vLLM alone", "a-3b-none", "gpu"),
         ("host hit, DRAM L1", "a-3b-dram", "host"), ("host hit, SSD L2 (O_DIRECT)", "a-3b-ssd-odirect", "host"), ("host hit, SSD L2 (page cache)", "a-3b-ssd", "host"),
         ("1.5B: recompute (cold)", "a-15b-dram", "cold"), ("1.5B: host hit, DRAM L1", "a-15b-dram", "host"), ("1.5B: GPU prefix hit", "a-15b-dram", "gpu")]
out.append("| path | " + " | ".join(f"L = {L}" for L in Ls) + " |"); out.append("|---|" + "---|" * len(Ls))
for name, tag, case in paths:
    if R[tag]: out.append(f"| {name} | " + " | ".join(cell(R[tag], case, L) for L in Ls) + " |")
out.append("\n### Table A-2 — stages of a host hit (ms, medians; MEASURED)\n")
out.append("| tier | L | lookup (incl. L2→L1 prefetch) | host→GPU transfer | transfer GB/s | transfer end → scheduled | scheduled → first token | queued → scheduled | TTFT |"); out.append("|---|---|---|---|---|---|---|---|---|")
for name, tag in (("DRAM L1", "a-3b-dram"), ("SSD L2 O_DIRECT", "a-3b-ssd-odirect"), ("SSD L2 page cache", "a-3b-ssd"), ("1.5B DRAM L1", "a-15b-dram")):
    for L in Ls:
        rows = [r for r in R[tag] if r["case"] == "host" and int(r["L"]) == L]
        if not rows: continue
        m = lambda k: (f"{med([r[k] for r in rows if r.get(k) is not None]):.1f}" if any(r.get(k) is not None for r in rows) else "–")
        out.append(f"| {name} | {L} | {m('lookup_ms')} | {m('retrieve_ms')} | {m('retrieve_GBps')} | {m('kv_end_to_sched_ms')} | {m('prefill_ms')} | {m('queue_to_sched_ms')} | {m('ttft_client_ms')} |")
out.append("\n### Table A-3 — instrumentation overhead: hooked run vs hook-less run (TTFT medians, ms)\n")
out.append("| case | " + " | ".join(f"L = {L}" for L in Ls) + " |"); out.append("|---|" + "---|" * len(Ls))
for case in ("cold", "gpu", "host"):
    for name, tag in (("with hooks + samplers", "a-3b-dram"), ("without", "a-3b-dram-nohooks")):
        if R[tag]: out.append(f"| {case}, {name} | " + " | ".join(cell(R[tag], case, L) for L in Ls) + " |")
s = "\n".join(out); open(f"{A}/tables-a.md", "w").write(s + "\n"); print(s)
