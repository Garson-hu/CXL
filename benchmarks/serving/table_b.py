#!/usr/bin/env python3
"""Result tables of Experiment B across configurations from <tag>-requests.csv (analyze_b.py): per scenario group, TTFT
p50 / p95 of the host hits and of the cold requests, the host hits' median queued -> load start and load wait, the
completed-request throughput and the GPU busy share. Writes <B dir>/tables-b.md and prints it.
usage: table_b.py <B dir> [tags=b-default,b-eager,b-workers4,b-prio-hits,b-prio-cold,b-chunk512,b-noasync,b-none,b-default-nosamp]"""
import csv, os, sys
B = sys.argv[1]; TAGS = (sys.argv[2].split("=", 1)[1] if len(sys.argv) > 2 else "b-default,b-eager,b-workers4,b-prio-hits,b-prio-cold,b-chunk512,b-noasync,b-none,b-default-nosamp").split(",")
LABEL = {"b-default": "default", "b-eager": "eager prefetch", "b-workers4": "4 transfer threads", "b-prio-hits": "priority: hits first", "b-prio-cold": "priority: cold first",
         "b-chunk512": "prefill chunk 512", "b-noasync": "synchronous scheduling", "b-none": "vLLM alone", "b-default-nosamp": "default, no sampler (GPU may idle)"}
def q(v, p): v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else None
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def fmt(v): return "–" if v is None else f"{v:.0f}"
R = {}; S = {}
for t in TAGS:
    p = f"{B}/{t}-requests.csv"
    if os.path.exists(p): R[t] = [r for r in csv.DictReader(open(p)) if r["status"] == "200" and r["case"] in ("host", "gpu", "cold")]
    p = f"{B}/{t}-scenarios.csv"
    if os.path.exists(p): S[t] = {r["grp"]: r for r in csv.DictReader(open(p))}
groups = sorted({r["grp"] for t in R for r in R[t]}, key=lambda g: (g[:2], len(g), g))
out = ["### Table B-1 — TTFT (ms) per scenario and configuration: host hits p50 / p95 | cold p50 / p95 | GPU-prefix hits p50 (n host / cold / gpu)\n"]
out.append("| scenario | " + " | ".join(LABEL.get(t, t) for t in R) + " |"); out.append("|---|" + "---|" * len(R))
for g in groups:
    cells = []
    for t in R:
        rs = [r for r in R[t] if r["grp"] == g]
        if not rs: cells.append("–"); continue
        h = [fl(r["ttft_client_ms"]) for r in rs if r["tier"] == "host"]; c = [fl(r["ttft_client_ms"]) for r in rs if r["tier"] == "cold"]; gp = [fl(r["ttft_client_ms"]) for r in rs if r["tier"] == "gpu"]
        cells.append(f"{fmt(q(h, .5))} / {fmt(q(h, .95))} \\| {fmt(q(c, .5))} / {fmt(q(c, .95))} \\| {fmt(q(gp, .5))} ({len(h)}/{len(c)}/{len(gp)})")
    out.append(f"| {g} | " + " | ".join(cells) + " |")
out.append("\n### Table B-2 — where a host hit waits (ms, medians): queued → load start | load wait (allocated → load noticed) | transfer | scheduled → first token\n")
out.append("| scenario | " + " | ".join(LABEL.get(t, t) for t in R) + " |"); out.append("|---|" + "---|" * len(R))
for g in groups:
    cells = []
    for t in R:
        rs = [r for r in R[t] if r["grp"] == g and r["tier"] == "host"]
        if not rs: cells.append("–"); continue
        q2l = [fl(r["kv_wait_ms"]) - fl(r["queued_ms"]) for r in rs if fl(r["kv_wait_ms"]) is not None and fl(r["queued_ms"]) is not None]
        cells.append(f"{fmt(q(q2l, .5))} \\| {fmt(q([fl(r['kv_load_wait_ms']) for r in rs if fl(r['kv_load_wait_ms']) is not None], .5))} \\| {fmt(q([fl(r['retrieve_ms']) for r in rs if fl(r['retrieve_ms']) is not None], .5))} \\| {fmt(q([fl(r['prefill_ms']) for r in rs if fl(r['prefill_ms']) is not None], .5))}")
    out.append(f"| {g} | " + " | ".join(cells) + " |")
out.append("\n### Table B-3 — throughput and GPU busy share per scenario: completed requests / s | prompt tokens / s | GPU busy (union of engine steps with tokens) | NVML utilization\n")
out.append("| scenario | " + " | ".join(LABEL.get(t, t) for t in S) + " |"); out.append("|---|" + "---|" * len(S))
for g in groups:
    cells = []
    for t in S:
        s = S[t].get(g)
        cells.append(f"{fl(s['req_per_s']):.2f} \\| {fl(s['prompt_tok_per_s']):.0f} \\| {fl(s['gpu_busy_steps']):.2f} \\| {fl(s['gpu_util_nvml']) if s.get('gpu_util_nvml') else 0:.2f}" if s else "–")
    out.append(f"| {g} | " + " | ".join(cells) + " |")
txt = "\n".join(out); open(f"{B}/tables-b.md", "w").write(txt + "\n"); print(txt)
