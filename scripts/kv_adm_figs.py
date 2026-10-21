#!/usr/bin/env python3
"""Figures of the adaptive admission study (2026-10-21). usage: kv_adm_figs.py <dir>
fig-adm-grid: usable-prefix hit share and TB written vs capacity, replacement policies (write everything) and admission
filters, three traces. fig-adm-ghost: hit share / writes / forgotten re-lookups vs ghost entries, TTL and Bloom size.
fig-adm-plan: the adaptive threshold, residence estimate and admitted candidate share over time (210 GiB), and the
phase-change trace. fig-adm-walkforward: usable hits per fifth incl. cold start and frozen. fig-adm-gaps: the
first-to-second-touch gap CDF in seconds and in ghost entries (trace statistics)."""
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
LAB = {"lru": "LRU (first touch)", "slru": "SLRU 1/3", "2q": "2Q", "arc": "ARC", "wtinylfu": "W-TinyLFU", "tinylfu": "TinyLFU (adapted)", "2nd": "second touch", "2nd_int": "second touch + gap ≤ residence", "adapt2": "adapt2", "adaptive": "adaptive (class tables)", "lhd": "learned class (2026-10-20)", "oracle": "oracle"}
STY = {"lru": (C[7], "-"), "slru": (C[7], "--"), "2q": (C[0], ":"), "arc": (C[0], "-"), "wtinylfu": (C[9], "-"), "tinylfu": (C[1], "-"), "2nd": (C[8], "-"), "2nd_int": (C[8], "--"), "adapt2": (C[2], ":"), "adaptive": (C[2], "-"), "lhd": (C[4], "-"), "oracle": ("k", "-")}
# ---- 1. grid ----
fig, axs = plt.subplots(2, 3, figsize=(16.5, 8.6))
for col, tr in enumerate(("conversation", "toolagent", "synthetic")):
    G = load(f"g-{tr}-c*-replay.csv"); caps = sorted({c for c, _, _ in G})
    for p in ("lru", "slru", "2q", "arc", "wtinylfu", "tinylfu", "2nd", "2nd_int", "adapt2", "adaptive", "lhd", "oracle"):
        rows = [next((r for (c, pp, f), r in G.items() if c == cap and pp == p), None) for cap in caps]
        if any(r is None for r in rows): continue
        c_, ls = STY[p]; xs = [c * 67.1 / 1024 for c in caps]
        axs[0][col].plot(xs, [float(r["usable_hit_share"]) for r in rows], color=c_, ls=ls, marker="o", ms=3.5, label=LAB[p], lw=1.4 if p in ("2nd_int", "adaptive", "tinylfu") else 1.1)
        axs[1][col].plot(xs, [float(r["written_TB"]) for r in rows], color=c_, ls=ls, marker="o", ms=3.5, label=LAB[p], lw=1.4 if p in ("2nd_int", "adaptive", "tinylfu") else 1.1)
    for row, yl in ((0, "usable-prefix hit share (scored half)"), (1, "TB written to the host cache (scored half)")):
        ax = axs[row][col]; ax.set_xscale("log"); ax.set_xticks([c * 67.1 / 1024 for c in caps]); ax.set_xticklabels([f"{c * 67.1 / 1024:.0f}" for c in caps]); ax.set_xticks([], minor=True); ax.set_xlabel("host cache capacity, GiB (8B blocks)"); ax.set_ylabel(yl)
    axs[0][col].set_title(f"Mooncake {tr}" + (" (SYNTHETIC)" if tr == "synthetic" else ""), fontsize=11); axs[0][col].set_ylim(0, 1.02)
h, l = axs[0][0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=6, fontsize=9, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(f"{D}/fig-adm-grid.png", dpi=200, bbox_inches="tight"); fig.savefig(f"{D}/fig-adm-grid.svg", bbox_inches="tight"); print("wrote fig-adm-grid")
# ---- 2. ghost bounds ----
fig, axs = plt.subplots(2, 3, figsize=(16, 8))
for col, tr in enumerate(("conversation", "toolagent")):
    G = load(f"gh-{tr}-c*-g*-replay.csv"); U = load(f"g-{tr}-c*-replay.csv")
    for ci, cap in enumerate((800, 3200, 6400)):
        for p, ls in (("2nd", "-"), ("2nd_int", "--"), ("adaptive", ":")):
            pts = []
            for (c, pp, f), r in G.items():
                if c != cap or pp != p or "-g" not in f: continue
                spec = f.split("-g")[-1]; n = int(float(spec[:-1]) * cap) if spec.endswith("c") else int(spec); pts.append((n, float(r["usable_hit_share"]), float(r["written_TB"]), int(r["ghost_forgotten_relookups"])))
            u = next((r for (c, pp, f), r in U.items() if c == cap and pp == p), None)
            if u is not None: pts.append((400000, float(u["usable_hit_share"]), float(u["written_TB"]), 0))
            pts.sort()
            axs[0][col].plot([x[0] for x in pts], [x[1] for x in pts], color=C[ci], ls=ls, marker="o", ms=3.5, label=f"{LAB[p]}, {cap * 67.1 / 1024:.0f} GiB")
            axs[1][col].plot([x[0] for x in pts], [x[2] for x in pts], color=C[ci], ls=ls, marker="o", ms=3.5)
    for row in (0, 1):
        ax = axs[row][col]; ax.set_xscale("log"); ax.set_xticks([1000, 4000, 16000, 64000, 400000]); ax.set_xticklabels(["1k", "4k", "16k", "64k", "unbounded"]); ax.set_xticks([], minor=True); ax.set_xlabel("ghost history entries (exact LRU list)")
    axs[0][col].set_ylabel("usable-prefix hit share"); axs[1][col].set_ylabel("TB written (scored half)"); axs[0][col].set_title(f"Mooncake {tr}: bounded ghost", fontsize=11)
    if col == 0: axs[0][col].legend(fontsize=7.5, ncol=1)
# TTL and Bloom panel (conversation / toolagent at 210 GiB, 2nd)
ax = axs[0][2]; ax2 = axs[1][2]
for col, tr in enumerate(("conversation", "toolagent")):
    G = load(f"gh-{tr}-c3200-*-replay.csv"); U = load(f"g-{tr}-c3200-replay.csv")
    ttl = sorted((float(f.split("ttl")[-1]), float(r["usable_hit_share"]), float(r["written_TB"])) for (c, p, f), r in G.items() if p == "2nd" and "ttl" in f)
    u = next(r for (c, p, f), r in U.items() if p == "2nd"); ttl.append((3600, float(u["usable_hit_share"]), float(u["written_TB"])))
    ax.plot([x[0] for x in ttl], [x[1] for x in ttl], color=C[col], marker="o", ms=3.5, label=f"{tr}: TTL (s; 3600 = none)")
    ax2.plot([x[0] for x in ttl], [x[2] for x in ttl], color=C[col], marker="o", ms=3.5)
    bl = sorted((int(f.split("bloom")[-1].split("_")[0]) / 8 / 1024, float(r["usable_hit_share"]), float(r["written_TB"]), int(r["bloom_false_positives"])) for (c, p, f), r in G.items() if p == "2nd" and "bloom" in f)
    axb = ax.twiny() if col == 0 else axb
    axb.plot([x[0] for x in bl], [x[1] for x in bl], color=C[col], marker="s", ms=4, ls="--", label=f"{tr}: Bloom (KB per filter, 2 filters)")
    ax2.plot([x[0] * 10 for x in bl], [x[2] for x in bl], color=C[col], marker="s", ms=4, ls="--")
ax.set_xscale("log"); ax.set_xlabel("ghost TTL, s (circles)"); axb.set_xscale("log"); axb.set_xlabel("Bloom filter size, KB (squares; reset every 8k–128k inserts)"); ax.set_ylabel("usable-prefix hit share, 210 GiB"); ax.set_title("second touch: TTL and Bloom history", fontsize=11)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = axb.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=7.5, loc="lower right")
ax2.set_xscale("log"); ax2.set_xlabel("TTL s (circles) / Bloom KB × 10 (squares)"); ax2.set_ylabel("TB written, 210 GiB")
fig.tight_layout(); fig.savefig(f"{D}/fig-adm-ghost.png", dpi=200); fig.savefig(f"{D}/fig-adm-ghost.svg"); print("wrote fig-adm-ghost")
# ---- 3. plan time series ----
fig, axs = plt.subplots(1, 3, figsize=(16, 4.3))
for ax, (lab, f) in zip(axs, (("conversation, 210 GiB", "g-conversation-adaptive-3200.json"), ("tool agent, 210 GiB", "g-toolagent-adaptive-3200.json"), ("CONSTRUCTED phase change, 210 GiB", "m-mix-phase-adaptive-3200.json"))):
    p = f"{D}/dump/{f}"
    if not os.path.exists(p): continue
    L = json.load(open(p)); t = [x[0] / 60 for x in L if x[1] is not None]
    ax.plot(t, [x[2] for x in L if x[1] is not None], color=C[2], label="admission threshold on P(re-lookup within residence)")
    ax.plot(t, [x[4] for x in L if x[1] is not None], color=C[1], label="share of candidates admitted")
    ax.set_ylim(0, 1); ax.set_xlabel("minutes since trace start (scored half starts at ~30)"); ax.set_ylabel("threshold / admitted share"); ax.set_title(lab, fontsize=11)
    ax2 = ax.twinx(); ax2.plot(t, [x[1] for x in L if x[1] is not None], color=C[7], ls="--", label="online residence estimate (s)"); ax2.set_ylabel("residence estimate, s"); ax2.grid(False)
    if ax is axs[0]:
        h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=7.5, loc="upper right")
fig.tight_layout(); fig.savefig(f"{D}/fig-adm-plan.png", dpi=200); fig.savefig(f"{D}/fig-adm-plan.svg"); print("wrote fig-adm-plan")
# ---- 4. walk-forward ----
fig, axs = plt.subplots(1, 3, figsize=(16, 4.3))
for ax, tr in zip(axs[:2], ("conversation", "toolagent")):
    G = load(f"g-{tr}-c3200-replay.csv"); A = load(f"ab-{tr}-c3200-*-replay.csv")
    series = [("lru", G, "LRU", C[7], "-"), ("2nd_int", G, "second touch + gap ≤ residence", C[8], "--"), ("adaptive", G, "adaptive, online", C[2], "-"), ("oracle", G, "oracle", "k", "-")]
    for p, src, lab, c_, ls in series:
        r = next((r for (c, pp, f), r in src.items() if pp == p), None)
        if r: ax.plot(range(1, 6), [int(h) / int(a) for h, a in zip(r["hits_by_fifth"].split("/"), r["acc_by_fifth"].split("/"))], marker="o", color=c_, ls=ls, label=lab)
    for suffix, lab, ls in (("frozen", "adaptive, frozen after 20%", ":"), ("cold", "adaptive, cold start at the scored half", "-.")):
        r = next((r for (c, pp, f), r in A.items() if pp == "adaptive" and f.endswith(suffix)), None)
        if r: ax.plot(range(1, 6), [int(h) / int(a) for h, a in zip(r["hits_by_fifth"].split("/"), r["acc_by_fifth"].split("/"))], marker="o", color=C[2], ls=ls, label=lab)
    r = next((r for (c, pp, f), r in A.items() if pp == "2nd" and f.endswith("cold")), None)
    if r: ax.plot(range(1, 6), [int(h) / int(a) for h, a in zip(r["hits_by_fifth"].split("/"), r["acc_by_fifth"].split("/"))], marker="o", color=C[8], ls="-.", label="second touch, cold start (empty ghost)")
    ax.set_xlabel("chronological fifth of the scored half"); ax.set_ylabel("usable hits / accesses"); ax.set_title(f"{tr}, 210 GiB: walk-forward", fontsize=11); ax.legend(fontsize=7.5)
ax = axs[2]; M = load("m-mix-phase-replay.csv"); MC_ = load("m-mix-phase-cold-replay.csv"); MF = load("m-mix-phase-frozen-replay.csv")
for p, src, lab, c_, ls in (("lru", M, "LRU", C[7], "-"), ("tinylfu", M, "TinyLFU (adapted)", C[1], "-"), ("2nd_int", M, "second touch + gap ≤ residence", C[8], "--"), ("adaptive", M, "adaptive, online", C[2], "-"), ("adaptive", MC_, "adaptive, cold start", C[2], "-."), ("adaptive", MF, "adaptive, frozen after 20%", C[2], ":"), ("oracle", M, "oracle", "k", "-")):
    r = next((r for (c, pp, f), r in src.items() if pp == p), None)
    if r: ax.plot(range(1, 6), [int(h) / int(a) for h, a in zip(r["hits_by_fifth"].split("/"), r["acc_by_fifth"].split("/"))], marker="o", color=c_, ls=ls, label=lab)
ax.set_xlabel("chronological fifth of the scored half (tool-agent phase)"); ax.set_ylabel("usable hits / accesses"); ax.set_title("CONSTRUCTED phase change (conversation → tool agent), 210 GiB", fontsize=10.5); ax.legend(fontsize=7.5)
fig.tight_layout(); fig.savefig(f"{D}/fig-adm-walkforward.png", dpi=200); fig.savefig(f"{D}/fig-adm-walkforward.svg"); print("wrote fig-adm-walkforward")
# ---- 5. gap CDFs ----
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
for tr, c_ in (("conversation", C[0]), ("toolagent", C[1]), ("synthetic", C[2])):
    s = json.load(open(f"{D}/ghost-stats-{tr}.json")); f = s["first_to_second"]
    xs = sorted(float(k) for k in f["cdf_s"]); axs[0].plot(xs, [f["cdf_s"][str(int(x))] for x in xs], marker="o", ms=3.5, color=c_, label=f"{tr}{' (SYNTHETIC)' if tr == 'synthetic' else ''}: {f['n']} second touches")
    xe = sorted(float(k) for k in f["cdf_entries"]); axs[1].plot(xe, [f["cdf_entries"][str(int(x))] for x in xe], marker="o", ms=3.5, color=c_, label=f"{tr}: {s['new_rate_per_s']:.0f} new hashes/s")
axs[0].set_xscale("log"); axs[0].set_xlabel("gap from the first to the second touch, s"); axs[0].set_ylabel("CDF over blocks that are touched twice"); axs[0].legend(fontsize=8); axs[0].set_title("how long a ghost entry must live", fontsize=11)
axs[1].set_xscale("log"); axs[1].set_xlabel("new hashes first-touched in between (ghost entries needed)"); axs[1].set_ylabel("CDF"); axs[1].legend(fontsize=8); axs[1].set_title("how many ghost entries are needed", fontsize=11)
fig.tight_layout(); fig.savefig(f"{D}/fig-adm-gaps.png", dpi=200); fig.savefig(f"{D}/fig-adm-gaps.svg"); print("wrote fig-adm-gaps")
