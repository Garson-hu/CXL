#!/usr/bin/env python3
"""Figures of the joint benefit analysis (2026-10-21). usage: kv_joint_figs.py <dir>
fig-joint-pressure: per-second write rates (DRAM + CXL) of the admitted stream for split_lru vs indep at the stressed
configurations (test half), with the CXL capacity and the measured safe DRAM budget. fig-joint-grid: usable hit share
and estimated neighbour p99 per policy across the model × speed configurations (both traces, Adam). fig-joint-regimes:
usable share per policy in the regime runs (capacity pressure, checkpoints, phases, mixes)."""
import csv, glob, gzip, json, os, sys
def jload(p):   # series files as .json or .json.gz (compressed after the campaign, 2026-10-21)
    if os.path.exists(p): return json.load(open(p))
    if os.path.exists(p + ".gz"): return json.load(gzip.open(p + ".gz", "rt"))
    return None
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = sys.argv[1]
plt.rcParams.update({"font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
LAB = {"split_lru": "static split + LRU", "split_slru": "static split + SLRU", "value_split": "reuse-aware only", "cost_budget": "cost-aware only", "indep": "independent combination", "joint": "joint", "joint_hash": "joint, hash placement", "joint_2nd": "joint w/ plain second touch", "oracle_cost": "ORACLE value, same costs", "oracle_joint": "ORACLE value+placement", "oracle_free": "ORACLE, no bandwidth limit"}
STY = {"split_lru": (C[7], "-"), "split_slru": (C[7], "--"), "value_split": (C[8], "-"), "cost_budget": (C[1], "-"), "indep": (C[0], "-"), "joint": (C[3], "-"), "joint_hash": (C[3], ":"), "joint_2nd": (C[3], "--"), "oracle_cost": ("k", "--"), "oracle_joint": ("k", ":"), "oracle_free": ("k", "-")}
def load(pattern):
    G = {}
    for f in sorted(glob.glob(f"{D}/{pattern}")):
        for r in csv.DictReader(open(f)): G.setdefault(os.path.basename(f).replace("-joint.csv", ""), {})[r["policy"]] = r
    return G
# ---- 1. pressure ----
cfgs = [("conversation-8b-1x-adam", "8B 1×"), ("conversation-8b-8x-adam", "8B 8×"), ("conversation-70b-4x-adam", "70B 4×"), ("conversation-70b-8x-adam", "70B 8×")]
fig, axs = plt.subplots(2, 4, figsize=(18, 7.2))
for col, (cfg, lab) in enumerate(cfgs):
    for row, p in enumerate(("split_lru", "indep")):
        ax = axs[row][col]; S = jload(f"{D}/series/test-{cfg}-{p}.json")
        if not S: continue
        t = [x["s"] / 60 for x in S]
        ax.plot(t, [x["cxl_gb"] for x in S], color=C[1], lw=0.6, label="CXL writes, GB/s (per second)")
        ax.plot(t, [x["dram_gb"] for x in S], color=C[0], lw=0.6, label="DRAM writes, GB/s")
        ax.axhline(46, color="k", ls="--", lw=0.8, label="CXL capacity 46 GB/s (measured)"); ax.axhline(8, color=C[3], ls=":", lw=0.8, label="safe DRAM budget beside Adam ≈ 6–8 GB/s (measured)")
        ax.set_title(f"{lab}, {LAB[p]}", fontsize=10.5); ax.set_xlabel("wall minutes (scored half from ~half)"); ax.set_ylabel("GB/s"); ax.set_ylim(0, max(60, max((x["cxl_gb"] + x["dram_gb"]) for x in S) * 1.05))
        if row == 0 and col == 0: ax.legend(fontsize=7.5)
fig.tight_layout(); fig.savefig(f"{D}/fig-joint-pressure.png", dpi=200); fig.savefig(f"{D}/fig-joint-pressure.svg"); print("wrote fig-joint-pressure")
# ---- 2. grid ----
G = load("test-*-joint.csv"); order = ["8b-1x", "8b-4x", "8b-8x", "70b-1x", "70b-4x", "70b-8x"]
fig, axs = plt.subplots(2, 2, figsize=(14, 8))
for col, tr in enumerate(("conversation", "toolagent")):
    for p in ("split_lru", "split_slru", "value_split", "cost_budget", "indep", "joint", "joint_hash", "oracle_cost", "oracle_free"):
        xs, ys, zs = [], [], []
        for i, o in enumerate(order):
            r = G.get(f"test-{tr}-{o}-adam", {}).get(p)
            if r: xs.append(i); ys.append(float(r["usable_hit_share"])); zs.append(float(r["neighbour_p99_pct"]))
        if xs:
            c_, ls = STY[p]; axs[0][col].plot(xs, ys, color=c_, ls=ls, marker="o", ms=3.5, label=LAB[p]); axs[1][col].plot(xs, zs, color=c_, ls=ls, marker="o", ms=3.5, label=LAB[p])
    for row, yl in ((0, "usable-prefix hit share (test half)"), (1, "estimated neighbour p99 slowdown, % (Adam)")):
        ax = axs[row][col]; ax.set_xticks(range(len(order))); ax.set_xticklabels(order); ax.set_ylabel(yl); ax.set_xlabel("model × trace speed (200 GiB = 64 DRAM + 136 CXL)")
    axs[1][col].axhline(7, color="k", ls="--", lw=0.8); axs[1][col].set_yscale("symlog"); axs[0][col].set_title(f"Mooncake {tr}, beside Adam", fontsize=11)
axs[0][0].legend(fontsize=7.5, ncol=2)
fig.tight_layout(); fig.savefig(f"{D}/fig-joint-grid.png", dpi=200); fig.savefig(f"{D}/fig-joint-grid.svg"); print("wrote fig-joint-grid")
# ---- 3. regimes ----
G = load("reg-*-joint.csv"); keys = sorted(G)
if keys:
    fig, ax = plt.subplots(figsize=(max(10, 0.55 * len(keys)), 5.5)); pols = ["split_slru", "value_split", "cost_budget", "indep", "joint", "oracle_cost"]; wdt = 0.13
    for pi, p in enumerate(pols):
        ax.bar([i + (pi - 2.5) * wdt for i in range(len(keys))], [float(G[k][p]["usable_hit_share"]) if p in G[k] else 0 for k in keys], width=wdt, color=STY[p][0], label=LAB[p], alpha=0.9 if p != "oracle_cost" else 0.5)
    ax.set_xticks(range(len(keys))); ax.set_xticklabels([k.replace("reg-", "") for k in keys], rotation=60, ha="right", fontsize=8); ax.set_ylabel("usable-prefix hit share (test half)"); ax.legend(fontsize=8, ncol=3); ax.set_title("regime runs (CONSTRUCTED load conditions where marked: capacity, checkpoint co-writer, neighbour phases, mixes)", fontsize=10)
    fig.tight_layout(); fig.savefig(f"{D}/fig-joint-regimes.png", dpi=200); fig.savefig(f"{D}/fig-joint-regimes.svg"); print("wrote fig-joint-regimes")
