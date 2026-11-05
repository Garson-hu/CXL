#!/usr/bin/env python3
"""Markdown table of trace-replay runs from replay-summary.csv (analyze_replay.py). usage: table_d.py <replay dir> tag [tag ...]"""
import csv, sys
R = sys.argv[1]; rows = {r["tag"]: r for r in csv.DictReader(open(f"{R}/replay-summary.csv"))}
def f(r, k, d=1, s=1.0):
    v = r.get(k, "")
    try: return f"{float(v) * s:.{d}f}"
    except ValueError: return "–"
print("| run | n ok/err | cached share (host / GPU) | TTFT p50 / p95 / p99 (s) | hit≥50 % TTFT p50 (s) [n] | miss TTFT p50 (s) [n] | request time p50 (s) | computed tok/s | KV host→GPU / GPU→host (GB) | evicted chunks | L1 max (GB) | GPU busy | backlog max |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for t in sys.argv[2:]:
    r = rows.get(t)
    if not r: print(f"| {t} | missing |"); continue
    print(f"| {t} | {f(r,'n_ok',0)}/{f(r,'n_err',0)} | {f(r,'cached_share',3)} ({f(r,'host_share',3)} / {f(r,'local_share',3)}) | {f(r,'ttft_p50',1,1e-3)} / {f(r,'ttft_p95',1,1e-3)} / {f(r,'ttft_p99',1,1e-3)} | {f(r,'ttft_hit50_p50',1,1e-3)} [{f(r,'n_hit50',0)}] | {f(r,'ttft_miss_p50',1,1e-3)} [{f(r,'n_miss',0)}] | {f(r,'total_ms_p50',1,1e-3)} | {f(r,'computed_tok_per_s',0)} | {f(r,'retrieve_GB',1)} / {f(r,'store_GB',1)} | {f(r,'evicted_chunks',0)} | {f(r,'l1_used_GB_max',1)} | {f(r,'gpu_busy_steps',2)} | {f(r,'backlog_max',0)} |")
