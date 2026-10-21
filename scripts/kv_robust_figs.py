#!/usr/bin/env python3
"""Figures of the robust-admission study (2026-10-21, second round). usage: kv_robust_figs.py <dir>
fig-robust-grid: usable-prefix hit share and TB written vs capacity for the focused baseline set (three traces).
fig-robust-regime: the regime rule's inputs over time (predicted admit-all residence vs the gap quantile) and the
regime, at 210 and 839 GiB, both real traces. fig-robust-est: residence estimators vs the realized residence over
time under the CONSTRUCTED load steps (210 GiB), and the estimator error summary. fig-robust-dyn: admissions and
usable hits per 5-s window under the load steps for 2nd, 2nd_int and LRU."""
import csv, glob, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = sys.argv[1]
plt.rcParams.update({"font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
def load(pattern):
    G = {}
    for f in sorted(glob.glob(f"{D}/{pattern}")):
        for r in csv.DictReader(open(f)): G[(int(r["cap"]), r["policy"], os.path.basename(f).replace("-replay.csv", ""))] = r
    return G
LAB = {"lru": "LRU (first touch)", "slru": "SLRU 1/3", "2nd": "second touch", "2nd64": "second touch, 64k ghost", "2nd_int": "2nd_int (gap ≤ residence)", "2nd_int64": "2nd_int, 64k ghost", "auto": "2nd_int + regime switch (res_ft, LRU)", "autoslru": "2nd_int + regime switch (res_ft, SLRU)", "tinylfu": "TinyLFU (adapted)", "oracle": "oracle"}
STY = {"lru": (C[7], "-"), "slru": (C[7], "--"), "2nd": (C[8], "-"), "2nd64": (C[8], ":"), "2nd_int": (C[2], "-"), "2nd_int64": (C[2], ":"), "auto": (C[3], "-"), "autoslru": (C[3], "--"), "tinylfu": (C[1], "-"), "oracle": ("k", "-")}
# ---- 1. grid ----
fig, axs = plt.subplots(2, 3, figsize=(16.5, 8.4))
for col, tr in enumerate(("conversation", "toolagent", "synthetic")):
    G = load(f"g-{tr}-c*-replay.csv"); caps = sorted({c for c, _, _ in G})
    F = load(f"fin-{tr}-c*-replay.csv")
    for key in ("lru", "slru", "2nd", "2nd64", "2nd_int", "2nd_int64", "auto", "autoslru", "tinylfu", "oracle"):
        if key in ("auto", "autoslru"):
            rows = [next((r for (c, pp, f), r in F.items() if c == cap and f.endswith("slru") == (key == "autoslru")), None) for cap in caps]
        else:
            p = key.replace("64", ""); b = key.endswith("64")
            rows = [next((r for (c, pp, f), r in G.items() if c == cap and pp == p and f.endswith("g64k") == b), None) for cap in caps]
        if any(r is None for r in rows): continue
        c_, ls = STY[key]; xs = [c * 67.1 / 1024 for c in caps]
        axs[0][col].plot(xs, [float(r["usable_hit_share"]) for r in rows], color=c_, ls=ls, marker="o", ms=3.5, label=LAB[key], lw=1.6 if key in ("auto", "autoslru") else 1.1)
        axs[1][col].plot(xs, [float(r["written_TB"]) for r in rows], color=c_, ls=ls, marker="o", ms=3.5, label=LAB[key], lw=1.6 if key in ("auto", "autoslru") else 1.1)
    for row, yl in ((0, "usable-prefix hit share (scored half)"), (1, "TB written to the host cache (scored half)")):
        ax = axs[row][col]; ax.set_xscale("log"); ax.set_xticks([c * 67.1 / 1024 for c in caps]); ax.set_xticklabels([f"{c * 67.1 / 1024:.0f}" for c in caps]); ax.set_xticks([], minor=True); ax.set_xlabel("host cache capacity, GiB (8B blocks)"); ax.set_ylabel(yl)
    axs[0][col].set_title(f"Mooncake {tr}" + (" (SYNTHETIC)" if tr == "synthetic" else ""), fontsize=11); axs[0][col].set_ylim(0, 1.02)
h, l = axs[0][0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=5, fontsize=9, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(f"{D}/fig-robust-grid.png", dpi=200, bbox_inches="tight"); fig.savefig(f"{D}/fig-robust-grid.svg", bbox_inches="tight"); print("wrote fig-robust-grid")
# ---- 2. regime rule inputs over time ----
fig, axs = plt.subplots(2, 2, figsize=(14, 7.5))
for row, tr in enumerate(("conversation", "toolagent")):
    for col, cap in enumerate((3200, 12800)):
        ax = axs[row][col]; f = f"{D}/dump/fin-{tr}-2nd_int_auto-{cap}-regime.json"; f0 = f"{D}/dump/g-{tr}-2nd_int_auto-{cap}-regime.json"
        if not os.path.exists(f): continue
        L = json.load(open(f))["log"]; t = [x[0] / 60 for x in L]
        ax.plot(t, [x[3] for x in L], color=C[0], label="predicted admit-all residence C / (λ_first + λ_reseen), s")
        ax.plot(t, [x[4] if x[4] is not None else float("nan") for x in L], color=C[1], label="median re-lookup gap of FIRST-touch blocks (online; the selected rule), s")
        if os.path.exists(f0):
            L0 = json.load(open(f0))["log"]; ax.plot([x[0] / 60 for x in L0], [x[4] if x[4] is not None else float("nan") for x in L0], color=C[7], ls="--", lw=0.9, label="median re-lookup gap of re-seen blocks (the first grid's rule), s")
        ax.set_yscale("log"); ax.set_xlabel("minutes since trace start (scored half from ~30)"); ax.set_ylabel("seconds"); ax.set_title(f"{tr}, {cap * 67.1 / 1024:.0f} GiB: regime rule inputs", fontsize=11)
        reg = [1 if x[1] == "normal" else 0 for x in L]; ax2 = ax.twinx(); ax2.fill_between(t, 0, reg, color=C[3], alpha=0.15, step="post", label="regime = normal admission (selected rule)"); ax2.set_ylim(0, 1); ax2.set_yticks([]); ax2.grid(False)
        if row == 0 and col == 0:
            h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig(f"{D}/fig-robust-regime.png", dpi=200); fig.savefig(f"{D}/fig-robust-regime.svg"); print("wrote fig-robust-regime")
# ---- 3. estimators under load steps (210 GiB, 2nd_int) ----
fig, axs = plt.subplots(2, 3, figsize=(16.5, 7.5))
for row, tr in enumerate(("conversation", "toolagent")):
    for col, scen in enumerate(("stepup", "stepdown", "burst")):
        ax = axs[row][col]; f = f"{D}/dump/dyn-{tr}-{scen}-2nd_int-3200-res.json"
        if not os.path.exists(f): continue
        S = json.load(open(f))["series"]; t = [x["t"] / 60 for x in S]
        for m, c_, ls in (("evict", C[0], "-"), ("evict50", C[0], ":"), ("dead", C[2], "-"), ("rate", C[1], "-"), ("tail", C[4], "-"), ("median", C[5], "--")):
            ax.plot(t, [x[m] if x[m] is not None else float("nan") for x in S], color=c_, ls=ls, lw=1.0, label=m)
        ax2 = ax.twinx(); ax2.plot(t, [x["adm"] for x in S], color=C[7], alpha=0.25, lw=0.6, label="admissions per 5 s"); ax2.set_ylabel("admissions / 5 s"); ax2.grid(False)
        ax.set_ylim(0, 700); ax.set_xlabel("minutes since trace start"); ax.set_ylabel("residence estimate, s"); ax.set_title(f"{tr}, 210 GiB, 2nd_int, CONSTRUCTED {scen}", fontsize=10.5)
        if row == 0 and col == 0:
            h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=7.5, ncol=2)
fig.tight_layout(); fig.savefig(f"{D}/fig-robust-est.png", dpi=200); fig.savefig(f"{D}/fig-robust-est.svg"); print("wrote fig-robust-est")
# ---- 4. admissions and hits per window under the load steps ----
fig, axs = plt.subplots(2, 3, figsize=(16.5, 7.5))
for row, tr in enumerate(("conversation", "toolagent")):
    for col, scen in enumerate(("stepup", "stepdown", "burst")):
        ax = axs[row][col]
        for p, c_ in (("lru", C[7]), ("2nd", C[8]), ("2nd_int", C[2])):
            f = f"{D}/dump/dyn-{tr}-{scen}-{p}-3200-res.json"
            if not os.path.exists(f): continue
            S = json.load(open(f))["series"]; t = [x["t"] / 60 for x in S]
            ax.plot(t, [x["adm"] for x in S], color=c_, lw=0.9, label=f"{LAB[p]}: admissions / 5 s")
        ax.set_xlabel("minutes since trace start"); ax.set_ylabel("admissions per 5 s"); ax.set_title(f"{tr}, 210 GiB, CONSTRUCTED {scen}", fontsize=10.5)
        if row == 0 and col == 0: ax.legend(fontsize=7.5)
fig.tight_layout(); fig.savefig(f"{D}/fig-robust-dyn.png", dpi=200); fig.savefig(f"{D}/fig-robust-dyn.svg"); print("wrote fig-robust-dyn")
