#!/usr/bin/env python3
"""Figures of the admission study (2026-10-20). usage: kv_admission_figs.py <dir>"""
import csv, glob, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = sys.argv[1]
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
def load(pattern):
    G = {}
    for f in sorted(glob.glob(f"{D}/{pattern}")):
        for r in csv.DictReader(open(f)): G[(int(r["cap"]), r["policy"])] = r
    return G
LAB = {"lru": "LRU", "slru": "SLRU 1/3", "static_d8": "static: position ≥ 8", "static_n8": "static: 8th+ new block", "static_2nd1": "static: second touch", "lhd": "learned class (online)", "cond": "learned root (online)", "oracle": "oracle"}
STY = {"lru": ("#7f7f7f", "-"), "slru": ("#7f7f7f", "--"), "static_d8": ("#ff7f0e", ":"), "static_n8": ("#ff7f0e", "-"), "static_2nd1": ("#bcbd22", "-"), "lhd": ("#2ca02c", "-"), "cond": ("#2ca02c", "--"), "oracle": ("k", "-")}
# 1. hit share and writes vs capacity, two traces
fig, axs = plt.subplots(2, 3, figsize=(16, 8.5))
for col, tr in enumerate(("conversation", "toolagent", "synthetic")):
    G = load(f"g-{tr}-c*-replay.csv"); G.update(load(f"s2-{tr}-c*-replay.csv")); caps = sorted({c for c, _ in G})
    for p in ("lru", "slru", "static_d8", "static_n8", "static_2nd1", "lhd", "cond", "oracle"):
        if (caps[0], p) not in G: continue
        c_, ls = STY[p]; xs = [c * 67.1 / 1024 for c in caps]
        axs[0][col].plot(xs, [float(G[(c, p)]["usable_hit_share"]) for c in caps], color=c_, ls=ls, marker="o", ms=4, label=LAB[p])
        axs[1][col].plot(xs, [float(G[(c, p)]["written_chunks"]) * 67.1 / 1e6 for c in caps], color=c_, ls=ls, marker="o", ms=4, label=LAB[p])
    for row, yl in ((0, "usable-prefix hit share (second half)"), (1, "TB written to the host cache (second half)")):
        ax = axs[row][col]; ax.set_xscale("log"); ax.set_xticks([c * 67.1 / 1024 for c in caps]); ax.set_xticklabels([f"{c * 67.1 / 1024:.0f}" for c in caps]); ax.set_xticks([], minor=True); ax.set_xlabel("host cache capacity, GiB (8B blocks)"); ax.set_ylabel(yl)
    axs[0][col].set_title(f"Mooncake {tr}" + (" (SYNTHETIC)" if tr == "synthetic" else ""), fontsize=11); axs[0][col].set_ylim(0, 1.02)
h, l = axs[0][0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=8, fontsize=9, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(f"{D}/fig-admission-grid.png", dpi=200, bbox_inches="tight"); fig.savefig(f"{D}/fig-admission-grid.svg", bbox_inches="tight"); print("wrote fig-admission-grid")
# 2. walk-forward per fifth at 200 GiB and the mixed traces
fig, axs = plt.subplots(1, 3, figsize=(16, 4.4))
for ax, tr in zip(axs[:2], ("conversation", "toolagent")):
    G = load(f"g-{tr}-c3200-replay.csv"); F = load(f"v-{tr}-frozen-replay.csv"); S = load(f"s2-{tr}-c3200-replay.csv")
    for p, src, lab, c_, ls in (("lru", G, "LRU", "#7f7f7f", "-"), ("static_n8", G, "static: 8th+ new block", "#ff7f0e", "-"), ("static_2nd1", S, "static: second touch", "#bcbd22", "-"), ("lhd", G, "learned class, online", "#2ca02c", "-"), ("lhd", F, "learned class, frozen after 20%", "#2ca02c", ":"), ("oracle", G, "oracle", "k", "-")):
        r = src.get((3200, p))
        if not r: continue
        hs = [int(x) for x in r["hits_by_fifth"].split("/")]; ac = [int(x) for x in r["acc_by_fifth"].split("/")]
        ax.plot(range(1, 6), [h / a for h, a in zip(hs, ac)], marker="o", color=c_, ls=ls, label=lab)
    ax.set_xlabel("chronological fifth of the scored half"); ax.set_ylabel("hit share of accesses"); ax.set_title(f"{tr}, 200 GiB: walk-forward", fontsize=10.5); ax.legend(fontsize=8)
ax = axs[2]; M = load("m-mix-phase-replay.csv"); MF = load("m-mix-phase-frozen-replay.csv"); MS = load("s2-m-mix-phase-replay.csv")
for p, src, lab, c_, ls in (("lru", M, "LRU", "#7f7f7f", "-"), ("static_n8", M, "static: 8th+ new block", "#ff7f0e", "-"), ("static_2nd1", MS, "static: second touch", "#bcbd22", "-"), ("lhd", M, "learned class, online", "#2ca02c", "-"), ("lhd", MF, "learned class, frozen after 20%", "#2ca02c", ":"), ("oracle", M, "oracle", "k", "-")):
    r = src.get((3200, p))
    if not r: continue
    hs = [int(x) for x in r["hits_by_fifth"].split("/")]; ac = [int(x) for x in r["acc_by_fifth"].split("/")]
    ax.plot(range(1, 6), [h / a for h, a in zip(hs, ac)], marker="o", color=c_, ls=ls, label=lab)
ax.set_xlabel("chronological fifth of the scored half (tool-agent phase)"); ax.set_ylabel("hit share of accesses"); ax.set_title("CONSTRUCTED phase change (conversation → tool agent), 200 GiB", fontsize=10); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(f"{D}/fig-admission-walkforward.png", dpi=200); fig.savefig(f"{D}/fig-admission-walkforward.svg"); print("wrote fig-admission-walkforward")
