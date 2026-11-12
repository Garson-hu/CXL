#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12), Experiment A: tables and figures of the single-request retrieval runs.
Reads <A>/<tag>-tier-timeline.csv (analyze_tier.py) of the given runs and writes
  <A>/tables-a.md          per tier and prefix length: TTFT (median, min-max), its parts, bytes, bandwidths, LMCache CPU time
  <A>/a-summary.csv        the same numbers, one row per (tier, case, L)
  <figs>/figA1-ttft-vs-prefix.png          prefix length vs TTFT, one line per source of the prefix
  <figs>/figA2-retrieval-vs-prefix.png     prefix length vs retrieval latency (lookup + media read + GPU transfer)
  <figs>/figA3-breakdown.png               TTFT breakdown per tier at each prefix length
  <figs>/figA4-bandwidth.png               effective bandwidth: media read (L2 load) and host-to-GPU copy
The parts of a host hit (ms after the client's send; medians over the repetitions):
  lookup + media   LMCache's lookup, including the L2 load (media read + copy into the L1 object) when the chunks are not in L1
  GPU transfer     mp.retrieve.start -> end: host-to-GPU staging copies + the GPU kernels that install the KV in vLLM's blocks
  prefill          scheduled -> first token: what is left to compute (the last token of the prompt)
  other            everything else: HTTP, tokenizer, queue hand-overs, scheduler steps
usage: table_tier_a.py <A dir> <figs dir> tag=label [tag=label ...]     (label = legend name of the run's "host" case)"""
import csv, os, statistics as st, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

A, FIGS = sys.argv[1:3]; RUNS = [a.split("=", 1) for a in sys.argv[3:]]
os.makedirs(FIGS, exist_ok=True)
def num(x):
    try: return float(x)
    except Exception: return None
def load(tag):
    rows = []
    for r in csv.DictReader(open(f"{A}/{tag}-tier-timeline.csv")):
        if r["status"] != "200" or r["case"] not in ("cold", "gpu", "host"): continue
        rows.append({k: (num(v) if k not in ("rid", "case", "grp", "error", "irid") else v) for k, v in r.items()})
    return rows
def med(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]; return st.median(v) if v else None
def f(v, d=1): return "-" if v is None else f"{v:.{d}f}"

DATA = {}; summary = []
for tag, label in RUNS:
    rows = load(tag)
    for case in ("cold", "gpu", "host"):
        for L in sorted({int(r["L"]) for r in rows}):
            g = [r for r in rows if r["case"] == case and int(r["L"]) == L]
            if not g: continue
            tt = [r["ttft_client_ms"] for r in g]
            d = dict(tag=tag, label=label, case=case, L=L, n=len(g), ttft_p50=st.median(tt), ttft_min=min(tt), ttft_max=max(tt), cached=med(g, "cached_tokens"),
                     l1_dram=med(g, "l1_dram"), l1_dax=med(g, "l1_dax"), l2_chunks=med(g, "l2_chunks"), lookup_ms=med(g, "lookup_ms"), l2_load_ms=med(g, "l2_load_ms"), l2_GiBps=med(g, "l2_GiBps"),
                     media_copy_ms=med(g, "media_copy_ms"), retrieve_ms=med(g, "retrieve_ms"), staging_ms=med(g, "staging_ms"), h2d_GiBps=med(g, "h2d_GiBps"), kernel_ms=med(g, "kernel_ms"),
                     kv_end_to_sched_ms=med(g, "kv_end_to_sched_ms"), prefill_ms=med(g, "prefill_ms"), lm_cpu_ms=med(g, "lm_cpu_ms"), retrieve_MiB=(med(g, "retrieve_bytes") or 0) / 2**20, l2_MiB=(med(g, "l2_bytes") or 0) / 2**20)
            d["other_ms"] = d["ttft_p50"] - sum(d[k] or 0 for k in ("lookup_ms", "retrieve_ms", "prefill_ms")) if case != "cold" else None
            DATA[(tag, case, L)] = d; summary.append(d)
with open(f"{A}/a-summary.csv", "w", newline="") as fo:
    w = csv.DictWriter(fo, fieldnames=list(summary[0])); w.writeheader()
    for d in summary: w.writerow({k: ("" if v is None else (round(v, 3) if isinstance(v, float) else v)) for k, v in d.items()})

Ls = sorted({d["L"] for d in summary})
COL = {tag: f"C{i % 10}" for i, (tag, _) in enumerate(RUNS)}       # one colour per run in every figure (matplotlib's default cycle)
lines = ["# Experiment A — single-request retrieval (medians over the repetitions; times in ms after the client's send)", ""]
for case, title in (("host", "Host-tier hit (after the GPU prefix cache was flushed)"), ("gpu", "Same prompt repeated at once (vLLM's GPU prefix cache holds it)"), ("cold", "First occurrence (recompute; LMCache stores the KV)")):
    lines += [f"## {title}", "", "| tier | L | n | cached tok | chunks DRAM / DAX / L2 | TTFT p50 (min–max) | lookup + media | L2 load | L2 GiB/s | per-chunk copy sum | GPU transfer | staging (H2D) | H2D GiB/s | KV install | prefill | other | LMCache CPU | MiB to GPU |", "|" + "---|" * 18]
    for tag, label in RUNS:
        for L in Ls:
            d = DATA.get((tag, case, L))
            if not d: continue
            lines.append(f"| {label} | {L} | {d['n']} | {f(d['cached'], 0)} | {f(d['l1_dram'], 0)} / {f(d['l1_dax'], 0)} / {f(d['l2_chunks'], 0)} | {d['ttft_p50']:.1f} ({d['ttft_min']:.1f}–{d['ttft_max']:.1f}) | {f(d['lookup_ms'])} | {f(d['l2_load_ms'])} | {f(d['l2_GiBps'])} | "
                         f"{f(d['media_copy_ms'])} | {f(d['retrieve_ms'])} | {f(d['staging_ms'])} | {f(d['h2d_GiBps'])} | {f(d['kernel_ms'])} | {f(d['prefill_ms'])} | {f(d['other_ms'])} | {f(d['lm_cpu_ms'])} | {f(d['retrieve_MiB'], 0)} |")
    lines.append("")
open(f"{A}/tables-a.md", "w").write("\n".join(lines) + "\n")

def xt(ax):
    ax.set_xscale("log", base=2); ax.set_xticks(Ls); ax.set_xticklabels([f"{L // 1024}K" if L >= 1024 else str(L) for L in Ls]); ax.set_xlabel("prefix length (tokens)")
# A1: TTFT vs prefix length
fig, ax = plt.subplots(figsize=(7.2, 4.4))
ref = RUNS[0][0]
ax.plot(Ls, [DATA[(ref, "cold", L)]["ttft_p50"] for L in Ls if (ref, "cold", L) in DATA], "k--", marker="x", label="recompute (first occurrence)")
ax.plot(Ls, [DATA[(ref, "gpu", L)]["ttft_p50"] for L in Ls if (ref, "gpu", L) in DATA], "k:", marker=".", label="GPU prefix-cache hit")
for tag, label in RUNS:
    y = [DATA[(tag, "host", L)]["ttft_p50"] for L in Ls if (tag, "host", L) in DATA and DATA[(tag, "host", L)]["retrieve_ms"] is not None]
    if y: ax.plot([L for L in Ls if (tag, "host", L) in DATA and DATA[(tag, "host", L)]["retrieve_ms"] is not None], y, marker="o", label=label, color=COL[tag])
xt(ax); ax.set_yscale("log"); ax.set_ylabel("TTFT (ms), median"); ax.set_title("A1  TTFT by source of the prefix (single request, idle server)"); ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False); fig.savefig(f"{FIGS}/figA1-ttft-vs-prefix.png", dpi=150, bbox_inches="tight"); plt.close(fig)
# A2: retrieval latency
fig, ax = plt.subplots(figsize=(7.2, 4.4))
for tag, label in RUNS:
    xs = [L for L in Ls if (tag, "host", L) in DATA and DATA[(tag, "host", L)]["retrieve_ms"] is not None]
    if xs: ax.plot(xs, [(DATA[(tag, "host", L)]["lookup_ms"] or 0) + DATA[(tag, "host", L)]["retrieve_ms"] for L in xs], marker="o", label=label, color=COL[tag])
xt(ax); ax.set_yscale("log"); ax.set_ylabel("lookup + media read + GPU transfer (ms), median"); ax.set_title("A2  KV retrieval latency of a host-tier hit"); ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False); fig.savefig(f"{FIGS}/figA2-retrieval-vs-prefix.png", dpi=150, bbox_inches="tight"); plt.close(fig)
# A3: breakdown, one panel per prefix length
parts = [("lookup_ms", "lookup + media read"), ("retrieve_ms", "GPU transfer (staging + KV install)"), ("prefill_ms", "prefill of the remaining token"), ("other_ms", "other (HTTP, queue, scheduler)")]
fig, axes = plt.subplots(1, len(Ls), figsize=(2.6 * len(Ls), 4.2), sharey=False)
for ax, L in zip(axes, Ls):
    ok = [(tag, label) for tag, label in RUNS if (tag, "host", L) in DATA and DATA[(tag, "host", L)]["retrieve_ms"] is not None]
    labs = [label for tag, label in ok]; bottom = [0.0] * len(labs)
    for k, name in parts:
        v = [max(0.0, DATA[(tag, "host", L)][k] or 0.0) for tag, label in ok]
        ax.bar(range(len(labs)), v, bottom=bottom, label=name, width=0.7); bottom = [b + x for b, x in zip(bottom, v)]
    ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs, rotation=60, ha="right", fontsize=7); ax.set_title(f"{L // 1024}K" if L >= 1024 else str(L), fontsize=10); ax.grid(True, axis="y", alpha=0.3)
axes[0].set_ylabel("TTFT of a host-tier hit (ms), median parts")
h, l = axes[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.04)); fig.suptitle("A3  Where the time of a host-tier hit goes, by prefix length")
fig.tight_layout(rect=(0, 0.03, 1, 0.96)); fig.savefig(f"{FIGS}/figA3-breakdown.png", dpi=150, bbox_inches="tight"); plt.close(fig)
# A4: effective bandwidths
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
for tag, label in RUNS:
    xs = [L for L in Ls if (tag, "host", L) in DATA and DATA[(tag, "host", L)]["l2_GiBps"] is not None]
    if xs: a1.plot(xs, [DATA[(tag, "host", L)]["l2_GiBps"] for L in xs], marker="o", label=label, color=COL[tag])
    xs = [L for L in Ls if (tag, "host", L) in DATA and DATA[(tag, "host", L)]["h2d_GiBps"] is not None]
    if xs: a2.plot(xs, [DATA[(tag, "host", L)]["h2d_GiBps"] for L in xs], marker="o", label=label, color=COL[tag])
for ax, t in ((a1, "media read into the L1 object (L2 load: bytes / task time)"), (a2, "host-to-GPU staging copy (bytes / copy time)")):
    xt(ax); ax.set_ylabel("GiB/s"); ax.set_title(t, fontsize=10); ax.grid(True, alpha=0.3); ax.set_ylim(bottom=0)
a1.legend(frameon=False, fontsize=8); a2.legend(frameon=False, fontsize=8, loc="lower right"); fig.suptitle("A4  Effective bandwidth of the two copies of a host-tier hit")
fig.tight_layout(); fig.savefig(f"{FIGS}/figA4-bandwidth.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print(open(f"{A}/tables-a.md").read()[:6000])
