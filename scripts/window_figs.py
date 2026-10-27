#!/usr/bin/env python3
"""Figures of the 2026-10-27 exploratory study. usage: window_figs.py <results dir>
fig-infer-window: usable-prefix hit share vs historical window W per capacity, for the three window families, with LRU / SLRU / the RQ1
adaptive policy / oracle as horizontal references (both traces). fig-infer-capacity: hit share vs capacity (30-720 GiB) for the baselines
and the best window of each family; the DRAM-only (60) and DRAM+CXL (180) points marked. fig-infer-writes: host writes (TB) vs window.
fig-train-window: training hit rate vs future window W per capacity (one panel per storage bandwidth / availability), from
train/sim/*.csv; fig-train-capacity: hit rate and storage traffic vs capacity for selected windows; fig-train-fit: measured vs fitted
H(W, C) if train/sim/fit.json exists."""
import csv, glob, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = sys.argv[1]
plt.rcParams.update({"font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
def fl(r, k, d=0.0):
    try: return float(r.get(k) or d)
    except (ValueError, TypeError): return d
# ---------------- inference ----------------
rows = []
for f in sorted(glob.glob(f"{D}/infer/*-replay.csv")):
    tr = os.path.basename(f).split("-cap")[0]
    for r in csv.DictReader(open(f)): r["trace"] = tr; rows.append(r)
if rows:
    traces = sorted({r["trace"] for r in rows}); caps = sorted({int(r["cap"]) for r in rows if int(r["cap"]) < 10000})
    FAM = [("wslru", "window-protected LRU", "-"), ("wlfu", "window-LFU eviction", "--"), ("wslru2nd", "window second-touch + protection", ":")]
    fig, axs = plt.subplots(2, len(caps), figsize=(3.3 * len(caps), 7.2), sharey="row")
    for ti, tr in enumerate(traces):
        for ci, cap in enumerate(caps):
            ax = axs[ti][ci]; G = {r["policy"]: r for r in rows if r["trace"] == tr and int(r["cap"]) == cap}
            for fi, (fam, lab, ls) in enumerate(FAM):
                pts = sorted((float(p.split(":")[1]), fl(r, "usable_hit_share")) for p, r in G.items() if p.startswith(fam + ":"))
                if pts: ax.plot([x for x, _ in pts], [y for _, y in pts], color=C[fi], ls=ls, marker="o", ms=3.5, label=lab if ci == 0 and ti == 0 else None)
            for pi, (p, lab, col, ls) in enumerate([("lru", "LRU", C[7], "-"), ("slru", "SLRU", C[7], "--"), ("2nd_int_auto", "RQ1 adaptive (gap rule + regime switch)", C[3], "-"), ("oracle", "ORACLE", "k", "-")]):
                if p in G: ax.axhline(fl(G[p], "usable_hit_share"), color=col, ls=ls, lw=0.9, label=lab if ci == 0 and ti == 0 else None)
            ax.set_xscale("log"); ax.set_title(f"{tr}, {G['lru']['cap_GiB']} GiB", fontsize=10)
            if ti == 1: ax.set_xlabel("historical window W (s)")
            if ci == 0: ax.set_ylabel("usable-prefix hit share (scored half)")
    axs[0][0].legend(fontsize=7, loc="upper left"); fig.tight_layout(); fig.savefig(f"{D}/fig-infer-window.png", dpi=200); fig.savefig(f"{D}/fig-infer-window.svg"); print("wrote fig-infer-window")
    # capacity
    fig, axs = plt.subplots(1, len(traces), figsize=(6.2 * len(traces), 4.8))
    allcaps = sorted({int(r["cap"]) for r in rows})
    for ti, tr in enumerate(traces):
        ax = axs[ti] if len(traces) > 1 else axs
        for p, lab, col, ls in [("lru", "LRU", C[7], "-"), ("slru", "SLRU", C[7], "--"), ("2nd", "second touch", C[8], "-"), ("2nd_int_auto", "RQ1 adaptive", C[3], "-"), ("oracle", "ORACLE", "k", "-")]:
            pts = [(fl(r, "cap_GiB"), fl(r, "usable_hit_share")) for r in rows if r["trace"] == tr and r["policy"] == p]
            if pts: pts.sort(); ax.plot([x for x, _ in pts], [y for _, y in pts], color=col, ls=ls, marker="o", ms=3.5, label=lab)
        for fi, (fam, lab, ls) in enumerate(FAM):
            pts = []
            for cap in allcaps:
                cand = [r for r in rows if r["trace"] == tr and int(r["cap"]) == cap and r["policy"].startswith(fam + ":")]
                if cand: b = max(cand, key=lambda r: fl(r, "usable_hit_share")); pts.append((fl(b, "cap_GiB"), fl(b, "usable_hit_share"), b["policy"].split(":")[1]))
            if pts: ax.plot([x for x, _, _ in pts], [y for _, y, _ in pts], color=C[fi], ls=ls, marker="s", ms=3.5, label=f"best {lab}")
            for x, y, w in pts: ax.annotate(f"{w}s", (x, y), fontsize=6.5, textcoords="offset points", xytext=(3, 3), color=C[fi])
        ax.axvline(60, color=C[1], ls=":", lw=0.8); ax.axvline(180, color=C[1], ls=":", lw=0.8); ax.text(60, 0.02, "DRAM-only 60 GiB", fontsize=7.5, rotation=90, va="bottom", ha="right"); ax.text(180, 0.02, "DRAM + CXL 180 GiB", fontsize=7.5, rotation=90, va="bottom", ha="right")
        ax.set_xscale("log", base=2); ax.set_xlabel("cache capacity (GiB, 8B blocks of 67.1 MB)"); ax.set_ylabel("usable-prefix hit share"); ax.set_title(f"Mooncake {tr}", fontsize=10.5); ax.legend(fontsize=7.5)
    fig.tight_layout(); fig.savefig(f"{D}/fig-infer-capacity.png", dpi=200); fig.savefig(f"{D}/fig-infer-capacity.svg"); print("wrote fig-infer-capacity")
    # writes
    fig, axs = plt.subplots(1, len(traces), figsize=(6.6 * len(traces), 4.4))
    for ti, tr in enumerate(traces):
        ax = axs[ti] if len(traces) > 1 else axs
        for ci, cap in enumerate(caps):
            G = {r["policy"]: r for r in rows if r["trace"] == tr and int(r["cap"]) == cap}
            pts = sorted((float(p.split(":")[1]), fl(r, "written_TB")) for p, r in G.items() if p.startswith("wslru2nd:"))
            if pts: ax.plot([x for x, _ in pts], [y for _, y in pts], color=C[ci % 10], marker="o", ms=3.5, label=f"window admission, {G['lru']['cap_GiB']} GiB")
            if "lru" in G: ax.scatter([1000], [fl(G["lru"], "written_TB")], color=C[ci % 10], marker="x")
            if "2nd_int_auto" in G: ax.scatter([700], [fl(G["2nd_int_auto"], "written_TB")], color=C[ci % 10], marker="^")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("admission window W (s); × at 1000 = LRU (admit all), ▲ at 700 = RQ1 adaptive"); ax.set_ylabel("host writes in the scored half (TB)"); ax.set_title(f"{tr}", fontsize=10.5); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f"{D}/fig-infer-writes.png", dpi=200); fig.savefig(f"{D}/fig-infer-writes.svg"); print("wrote fig-infer-writes")
# ---------------- training ----------------
T = []
for f in sorted(glob.glob(f"{D}/train/sim/*.csv")):
    if "pilot" in f or "fit" in f: continue
    for r in csv.DictReader(open(f)): r["_f"] = os.path.basename(f); T.append(r)
if T:
    SEL = [("all-bw0.064.csv", "B = 0.064 GB/s (one BeeGFS stream, 0.3× demand)"), ("all-bw0.15.csv", "B = 0.15 GB/s (0.7×)"), ("all-bw0.2.csv", "B = 0.20 GB/s (0.92×)"), ("all-bw0.82-x4.csv", "B = 0.82 GB/s, trainer ×4 (0.94×)"),
           ("all-bw0.25.csv", "B = 0.25 GB/s (1.15×)"), ("all-bw0.33.csv", "B = 0.33 GB/s (1.5×)"), ("fine-bw0.33.csv", "fine windows, B = 0.33 GB/s"), ("all-bw0.82-noprotect.csv", "naive prefetcher (no protection), B = 0.82 GB/s")]
    fig, axs = plt.subplots(2, 4, figsize=(17, 8), sharey=True)
    for k, (fn, title) in enumerate(SEL):
        ax = axs[k // 4][k % 4]; G = [r for r in T if r["_f"] == fn]; capsT = sorted({fl(r, "cap_gib") for r in G})
        for ci, cap in enumerate(capsT):
            pts = sorted((fl(r, "window_s"), fl(r, "hit_rate")) for r in G if fl(r, "cap_gib") == cap)
            ax.plot([max(x, 0.05) for x, _ in pts], [y for _, y in pts], color=C[ci % 10], marker="o", ms=3.5, label=f"C = {cap:g} GiB" if cap < 1e9 else "C = ∞")
        ax.set_xscale("log"); ax.set_title(title, fontsize=9.5); ax.set_ylim(-0.03, 1.05)
        if k // 4 == 1: ax.set_xlabel("future window W (s; W = 0 drawn at 0.05)")
        if k % 4 == 0: ax.set_ylabel("cache hit rate (epochs 1–2)")
        if k == 0: ax.legend(fontsize=7.5, loc="center right")
    fig.suptitle("training (real CosmoFlow trace, 166 GiB dataset, 0.21 GB/s demand): hit rate vs future window per capacity and storage bandwidth", fontsize=10.5)
    fig.tight_layout(); fig.savefig(f"{D}/fig-train-window.png", dpi=200); fig.savefig(f"{D}/fig-train-window.svg"); print("wrote fig-train-window")
    # capacity: retention (W = 0) with the analytic curve, prefetch plateau per regime, and storage traffic
    import math
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.8))
    none = [r for r in T if r["_f"] == "none.csv"]; pts = sorted((fl(r, "cap_gib"), fl(r, "hit_rate"), fl(r, "storage_GB")) for r in none if fl(r, "cap_gib") < 1e9)
    axs[0].plot([x for x, _, _ in pts], [y for _, y, _ in pts], color="k", marker="o", ms=4, label="no prefetch, LRU retention (measured)")
    xs = [15 * 1.05 ** k for k in range(80) if 15 * 1.05 ** k <= 400]; D_GIB = 165.8
    axs[0].plot(xs, [(x / D_GIB + (1 - x / D_GIB) * math.log(1 - x / D_GIB)) if x < D_GIB else 1.0 for x in xs], color="k", ls=":", lw=1, label="analytic c + (1 − c) ln(1 − c), c = C / 166 GiB")
    for fn, lab, col, W in [("all-bw0.33.csv", "prefetch, B = 0.33 GB/s (1.5× demand), W = 5 s", C[2], 5.0), ("all-bw0.2.csv", "prefetch, B = 0.20 GB/s (0.92×), W = 50 s", C[1], 50.0), ("all-bw0.15.csv", "prefetch, B = 0.15 GB/s (0.7×), W = 50 s", C[3], 50.0)]:
        q = sorted((fl(r, "cap_gib"), fl(r, "hit_rate")) for r in T if r["_f"] == fn and fl(r, "window_s") == W and fl(r, "cap_gib") < 1e9)
        axs[0].plot([x for x, _ in q], [y for _, y in q], color=col, marker="s", ms=3.5, label=lab)
    axs[1].plot([x for x, _, _ in pts], [z for _, _, z in pts], color="k", marker="o", ms=4, label="bytes fetched from storage per two epochs (any window)")
    for ax, yl in ((axs[0], "cache hit rate (epochs 1–2)"), (axs[1], "storage traffic = cache writes, GB")):
        ax.set_xscale("log", base=2); ax.set_xlabel("cache capacity (GiB); dataset 166 GiB"); ax.set_ylabel(yl); ax.axvline(60, color=C[1], ls=":", lw=0.8); ax.axvline(180, color=C[1], ls=":", lw=0.8); ax.legend(fontsize=7.5)
    axs[0].text(60, 0.9, "DRAM-only 60", fontsize=7.5, rotation=90, va="top", ha="right"); axs[0].text(180, 0.9, "DRAM + CXL 180", fontsize=7.5, rotation=90, va="top", ha="right")
    fig.tight_layout(); fig.savefig(f"{D}/fig-train-capacity.png", dpi=200); fig.savefig(f"{D}/fig-train-capacity.svg"); print("wrote fig-train-capacity")
    fit = f"{D}/train/sim/fit.json"
    if os.path.exists(fit):
        F = json.load(open(fit)); fig, ax = plt.subplots(figsize=(6, 5))
        xs = [p["measured"] for p in F["points"]]; ys = [p["fitted"] for p in F["points"]]; held = [p.get("held_out", False) for p in F["points"]]
        ax.scatter([x for x, h in zip(xs, held) if not h], [y for y, h in zip(ys, held) if not h], s=14, color=C[0], label="fitted points")
        ax.scatter([x for x, h in zip(xs, held) if h], [y for y, h in zip(ys, held) if h], s=18, color=C[3], marker="^", label="held-out points")
        ax.plot([0, 1], [0, 1], color="k", lw=0.8); ax.set_xlabel("measured hit rate"); ax.set_ylabel("fitted H(W, C)"); ax.set_title(F.get("form", "fit"), fontsize=9); ax.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(f"{D}/fig-train-fit.png", dpi=200); fig.savefig(f"{D}/fig-train-fit.svg"); print("wrote fig-train-fit")
