#!/usr/bin/env python3
"""Figures of Experiment F (workload sensitivity, scenario s4 of run_b.py: open loop at 2 req/s, 48 requests per point, host-hit
share 0 / 0.25 / 0.5 / 0.75 / 1 x length class short (1k/2k) or long (8k); default DRAM tier vs vLLM alone) from analyze_b.py's
<tag>-scenarios.csv.  figF1: TTFT p50 / p95 of all, host-hit and cold requests vs hit share;  figF2: completed req/s, served
prompt tokens/s and GPU busy share vs hit share.   usage: figs_f.py <F dir> <fig dir> [tags=f-default,f-none]"""
import csv, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
F, FIG = sys.argv[1], sys.argv[2]; os.makedirs(FIG, exist_ok=True)
TAGS = (sys.argv[3].split("=", 1)[1] if len(sys.argv) > 3 else "f-default,f-none").split(",")
LABEL = {"f-default": "DRAM host tier (default)", "f-none": "vLLM alone (recompute)"}
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
S = {}
for t in TAGS:
    p = f"{F}/{t}-scenarios.csv"
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            if r["grp"].startswith("s4-"): S[(t, r["grp"].split("-")[1], float(r["grp"].split("-h")[1]))] = {k: fl(v) for k, v in r.items() if k not in ("grp", "tag")}
def series(t, cls, key):
    pts = sorted((sh, v[key]) for (tt, cc, sh), v in S.items() if tt == t and cc == cls and v.get(key) is not None)
    return [p[0] for p in pts], [p[1] for p in pts]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
for j, cls in enumerate(("short", "long")):
    ax = axes[j]
    for i, t in enumerate(TAGS):
        for key, ls, mk, name in (("all_ttft_p50", "-", "o", "all, p50"), ("all_ttft_p95", "--", "s", "all, p95"), ("host_ttft_p50", ":", "^", "host hits, p50"), ("cold_ttft_p50", "-.", "v", "cold, p50")):
            x, y = series(t, cls, key)
            if x: ax.plot(x, y, ls=ls, marker=mk, ms=4, color=C[i], label=f"{LABEL.get(t, t)}: {name}")
    ax.set_xlabel("share of requests whose prefix is in the host tier"); ax.set_ylabel("TTFT (ms, log)"); ax.set_yscale("log"); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=6.5)
    ax.set_title(f"({'ab'[j]}) {cls} prompts ({'1k / 2k' if cls == 'short' else '8k'} tokens), open loop 2 req/s, 48 requests per point", fontsize=9)
fig.suptitle("Figure F1 — TTFT vs host-hit share and prompt length (MEASURED, 3B-AWQ, 32 output tokens; vLLM alone recomputes every request)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figF1-ttft-vs-share.png", dpi=300); fig.savefig(f"{FIG}/figF1-ttft-vs-share.pdf"); plt.close(fig)
fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
for i, t in enumerate(TAGS):
    for j, cls in enumerate(("short", "long")):
        for ax, key in zip(axes, ("req_per_s", "prompt_tok_per_s", "gpu_busy_steps")):
            x, y = series(t, cls, key)
            if x: ax.plot(x, y, ls="-" if cls == "short" else "--", marker="o" if cls == "short" else "s", ms=4, color=C[i], label=f"{LABEL.get(t, t)}: {cls}")
for ax, yl, ti in zip(axes, ("completed requests / s", "served prompt tokens / s (cached included)", "GPU busy share"), ("(a) completed request rate (offered: 2 req/s)", "(b) prompt tokens served per second (completed requests, cached tokens included)", "(c) GPU busy share")):
    ax.set_xlabel("host-hit share"); ax.set_ylabel(yl); ax.set_title(ti, fontsize=9); ax.grid(alpha=.3); ax.legend(fontsize=6.5)
fig.suptitle("Figure F2 — throughput and GPU work vs host-hit share (MEASURED)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figF2-throughput-vs-share.png", dpi=300); fig.savefig(f"{FIG}/figF2-throughput-vs-share.pdf"); plt.close(fig)
print("figures written to", FIG, "points:", len(S))
