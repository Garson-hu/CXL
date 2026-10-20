#!/usr/bin/env python3
"""Figures of the historical-learning round (2026-10-18): cache-level utility of the learned online policies from the
kv_agent_replay.py CSVs (prefix-aware scoring, tail order), per trace and capacity, with and without learned admission
bypass. usage: kv_history_figs.py <dir> <label=replay.csv> [...]"""
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

out = sys.argv[1]; items = [a.split("=", 1) for a in sys.argv[2:]]
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
POLS = ["split", "lru", "slru", "pop", "lhd", "olr", "cond", "event_cont", "oracle"]
LAB = {"split": "static split + LRU", "lru": "global LRU", "slru": "SLRU 1/3", "pop": "decayed popularity", "lhd": "class hit-rate (LHD-like)", "olr": "online logistic", "cond": "per-root rate", "event_cont": "agent continue signal", "oracle": "oracle"}
fig, axs = plt.subplots(1, len(items), figsize=(5.2 * len(items), 4.6), squeeze=False); axs = axs[0]
for ax, (label, path) in zip(axs, items):
    R = list(csv.DictReader(open(path))); G = {(int(r["cap"]), r["policy"]): r for r in R}; caps = sorted({int(r["cap"]) for r in R})
    pols = [p for p in POLS if (caps[0], p) in G]; w = 0.8 / len(pols)
    for i, p in enumerate(pols):
        ys = [float(G[(c, p)]["usable_hit_share"]) for c in caps]
        b = ax.bar([k + (i - len(pols) / 2 + 0.5) * w for k in range(len(caps))], ys, w * 0.95, label=LAB.get(p, p), color="k" if p == "oracle" else None)
    lo = min(float(G[(c, p)]["usable_hit_share"]) for c in caps for p in pols)
    ax.set_xticks(range(len(caps))); ax.set_xticklabels([(f"{float(G[(c, 'lru')]['cap_GB']):.1f}" if float(G[(c, 'lru')]['cap_GB']) < 10 else f"{float(G[(c, 'lru')]['cap_GB']):.0f}") + " GB" for c in caps]); ax.set_ylabel("usable-prefix hit share (second half)"); ax.set_ylim(max(0, lo - 0.05), 1.02)
    ax.set_title(label, fontsize=10)
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=min(5, len(l)), fontsize=8, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(f"{out}/fig-history-policies.png", dpi=200, bbox_inches="tight"); fig.savefig(f"{out}/fig-history-policies.svg", bbox_inches="tight"); print("wrote", f"{out}/fig-history-policies.png")
