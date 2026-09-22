#!/usr/bin/env python3
"""Scatter figure of a policy campaign: one panel per victim, x = completion time of the copy, y = victim
slowdown during the copy; small = one repetition, large = median of the repetitions; labels give the copy
rate and, for cxlpath, the DRAM share. Panels and series are given in a small spec so the same script draws
every campaign figure (kept next to the data so that a figure can be regenerated from summary.csv).
usage: plot_policy.py <summary.csv> <out.png> <spec: 32threads|pacing|dcp>"""
import csv, statistics as st, sys, collections
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
summary, out, spec = sys.argv[1:4]
rows = collections.defaultdict(list)
for r in csv.DictReader(open(summary)): rows[r["tag"].rsplit("-rep", 1)[0]].append(r)
S = dict(dram=("all-DRAM, NT stores (today)", "#c8511b", "o", 1), cxl=("all-CXL", "#1f6f78", "o", 1), lim=("DRAM, throttled 20 GiB/s", "#8a9bb0", "^", 1),
         cx09=("cxlpath, bound 1.09", "#1a2a44", "*", 1), cx05=("cxlpath, bound 1.05", "#4a5d7a", "P", 1), cxtight=("cxlpath, tight bound + pacing", "#1a2a44", "*", 1),
         cxloose=("cxlpath, bound 1.10 (unpaced)", "#4a5d7a", "P", 1), dcpdram=("DCP stock: DRAM stager + FileSystemWriter (today)", "#c8511b", "o", 1), dcpcxl=("DCP with CxlpathWriter", "#1a2a44", "*", 1))
SPECS = {
 "32threads": dict(title="A periodic checkpoint copy beside a REAL application on 32 of 128 cores (moderate regime): simple policies vs cxlpath (small = one repetition, large = median of 3; dotted = 7% bound) — c28, 2026-09-22",
   panels=[("llama.cpp decode, Qwen2.5-7B Q8, 32 threads; 64 GiB copies", [("llama32-dram", "dram"), ("llama32-cxl", "cxl"), ("llama32-dram-limited-r20", "lim"), ("llama32-cxlpath-b1.09-g1.3", "cx09"), ("llama32-cxlpath-b1.05-g1.3", "cx05")]),
           ("GAPBS PageRank, 2^25 Kronecker, 32 threads; 192 GiB copies", [("pr32-dram-s192", "dram"), ("pr32-cxl-s192", "cxl"), ("pr32-dram-limited-r20-s192", "lim"), ("pr32-cxlpath-b1.09-g1.3-s192", "cx09"), ("pr32-cxlpath-b1.05-g1.3-s192", "cx05")]),
           ("CPU Adam step, 24 GB state, 32 threads; 64 GiB copies (guard: no loan; pacing)", [("opt32-dram", "dram"), ("opt32-cxl", "cxl"), ("opt32-dram-limited-r20", "lim"), ("opt32-cxlpath-b1.09-g1.3", "cx09"), ("opt32-cxlpath-b1.05-g1.3", "cx05")])]),
 "pacing": dict(title="Producer pacing as the last resort beside the SATURATED (80-thread) victims: cxlpath with a bound at the ~7% probe level vs the unpaced runs (small = one repetition, large = median of 3; dotted = 7%) — c28, 2026-09-22",
   panels=[("CPU Adam step, 80 threads; 64 GiB copies", [("opt-dram", "dram"), ("opt-cxl", "cxl"), ("opt-cxlpath-b1.10", "cxloose"), ("opt-cxlpath-b1.04-g1.3", "cxtight")]),
           ("llama.cpp decode, 80 threads; 64 GiB copies", [("llama-dram", "dram"), ("llama-cxl", "cxl"), ("llama-dram-limited-r20", "lim"), ("llama-cxlpath-b1.10-g1.3", "cxloose"), ("llama-cxlpath-b1.06-g1.3", "cxtight")]),
           ("GAPBS PageRank 2^26, 80 threads; 192 GiB copies", [("pr-dram-s192", "dram"), ("pr-cxl-s192", "cxl"), ("pr-cxlpath-b1.10-g1.3-s192", "cxloose"), ("pr-cxlpath-b1.055-g1.3-s192", "cxtight")])]),
 "dcp": dict(title="The real producer: torch.distributed.checkpoint.async_save of a 16 GiB CPU state dict every 30 s, stock DRAM staging vs CxlpathWriter (x = time the training thread is blocked in async_save) — c28, 2026-09-22",
   panels=[("CPU Adam step, 80 threads (saturated)", [("opt-dcp-dram-s16", "dcpdram"), ("opt-dcp-cxlpath-s16", "dcpcxl")]),
           ("llama.cpp decode, 32 threads (moderate)", [("llama32-dcp-dram-s16", "dcpdram"), ("llama32-dcp-cxlpath-s16", "dcpcxl")])]),
}
sp = SPECS[spec]; n = len(sp["panels"])
fig, axes = plt.subplots(1, n, figsize=(6.2 * n, 5.2)); axes = list(axes) if n > 1 else [axes]
for ax, (title, series) in zip(axes, sp["panels"]):
    for base, kind in series:
        rs = rows.get(base)
        if not rs: print("missing", base); continue
        label, color, marker, _ = S[kind]
        xs = [float(r["completion_s"]) for r in rs]; ys = [float(r["slowdown_pct"]) for r in rs]
        ax.scatter(xs, ys, s=30, color=color, marker=marker, alpha=0.35)
        x, y = st.median(xs), st.median(ys); ax.scatter([x], [y], s=(260 if marker == "*" else 160), color=color, marker=marker, edgecolor="k", linewidth=0.6, label=label, zorder=3)
        rate = st.median(float(r["copy_GiBs"]) for r in rs); share = st.median(float(r["dram_share"]) for r in rs)
        ax.annotate(f"{rate:.0f} GiB/s" + (f", {100 * share:.0f}% DRAM" if kind.startswith("cx") and share > 0.005 else ""), (x, y), textcoords="offset points", xytext=(8, 5), fontsize=8, color=color)
    ax.axhline(7, ls=":", color="gray", lw=1); ax.set_xlim(left=0); ax.grid(alpha=0.3)
    ax.set_xlabel("completion time of the copy, s"); ax.set_ylabel("victim slowdown during the copy, %"); ax.set_title(title, fontsize=10); ax.legend(fontsize=8, loc="best")
fig.suptitle(sp["title"], fontsize=10); fig.tight_layout(); fig.savefig(out, dpi=130); print("wrote", out)
