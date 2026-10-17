#!/usr/bin/env python3
"""Figures of the oracle placement study (Phase 1, Steps 2–4; 2026-10-17) from the CSVs that kv_oracle_study.py writes.
usage: kv_oracle_figs.py [dir=experimental_results/2026-10-17-kv-reuse-oracle-study]"""
import csv, glob, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.ticker

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "experimental_results", "2026-10-17-kv-reuse-oracle-study")
TRACES = ["conversation", "toolagent", "synthetic"]; COL = {"conversation": "#1f77b4", "toolagent": "#2ca02c", "synthetic": "#9467bd"}
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
def rows(tag): return list(csv.DictReader(open(os.path.join(D, f"oracle-{tag}.csv"))))
def get(rs, tr, pol, key="reuse_hit_share"): return next(float(r[key]) for r in rs if r["trace"] == tr and r["policy"] == pol)
def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(D, name + ".png"), dpi=200); fig.savefig(os.path.join(D, name + ".svg")); plt.close(fig); print("wrote", name)

cap = rows("8b-capacity"); onl = rows("8b-capacity-online")
# 1. policies: reuse-hit share and host writes, capacity-only
pols = [("CXL-first\n+ LRU (A)", "cxlfirst", cap), ("static split\n+ per-tier LRU (B)", "split", cap), ("global\nLRU (C)", "global_lru", cap), ("reactive\nmigration (D)", "reactive_mig", cap),
        ("SLRU 1/3\n(online)", "slru0.33", onl), ("admission\nfilter (online)", "pred_admit", onl), ("oracle\nhorizon 60 s", "oracle_h60", cap), ("oracle\nhorizon 300 s", "oracle_h300", cap), ("oracle\nMIN (E)", "oracle_min", cap)]
fig, axs = plt.subplots(1, 2, figsize=(13.5, 5.0), gridspec_kw=dict(width_ratios=[1.6, 1]))
w = 0.27
for j, tr in enumerate(TRACES):
    vals = [get(rs, tr, p) for _, p, rs in pols]
    b = axs[0].bar([x + (j - 1) * w for x in range(len(pols))], vals, w * 0.92, color=COL[tr], label=tr)
    for r, v in zip(b, vals): axs[0].annotate(f"{v:.2f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7.5, rotation=90)
axs[0].set_xticks(range(len(pols))); axs[0].set_xticklabels([p[0] for p in pols], fontsize=8.5, rotation=25, ha="right"); axs[0].set_ylabel("reuse-hit share (test half)"); axs[0].set_ylim(0, 1.12); axs[0].legend(loc="upper left")
axs[0].set_title("200 GiB (DRAM 64 + CXL 136), 8B blocks: baselines, online policies, oracles", fontsize=11.5)
wp = [("split (B)", "split", cap), ("SLRU 1/3", "slru0.33", onl), ("oracle MIN (E)", "oracle_min", cap)]
for j, tr in enumerate(TRACES):
    vals = [(get(rs, tr, p, "dram_GB") + get(rs, tr, p, "cxl_GB")) / 1000 for _, p, rs in wp]
    b = axs[1].bar([x + (j - 1) * w for x in range(len(wp))], vals, w * 0.92, color=COL[tr])
    for r, v in zip(b, vals): axs[1].annotate(f"{v:.1f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8.5)
axs[1].set_xticks(range(len(wp))); axs[1].set_xticklabels([p[0] for p in wp], fontsize=10); axs[1].set_ylabel("bytes written to host memory, TB (test half)"); axs[1].set_title("The oracle stores only blocks with a future use", fontsize=11.5)
save(fig, "fig-oracle-policies")
# 2. capacity sweep: LRU-type vs oracle
fig, ax = plt.subplots(figsize=(7.5, 4.3))
caps = [(200, cap), (512, rows("8b-capacity-512GiB")), (1024, rows("8b-capacity-1024GiB"))]
for tr in TRACES:
    ax.plot([c for c, _ in caps], [get(rs, tr, "split") for _, rs in caps], marker="o", color=COL[tr], label=f"{tr}: static split + LRU")
    ax.plot([c for c, _ in caps], [get(rs, tr, "oracle_min") for _, rs in caps], marker="s", ls="--", color=COL[tr], label=f"{tr}: oracle MIN")
ax.set_xscale("log"); ax.set_xticks([200, 512, 1024]); ax.set_xticklabels(["200 GiB", "512 GiB", "1 TiB"]); ax.set_xticks([], minor=True); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax.set_ylabel("reuse-hit share (test half)"); ax.set_ylim(0, 1.05); ax.legend(fontsize=9, ncol=1, loc="lower right"); ax.set_xlabel("host capacity (DRAM 32% + CXL 68%), 8B blocks")
ax.set_title("Future information is worth more than 5× the capacity", fontsize=11.5)
save(fig, "fig-oracle-capacity")
# 3. share of the oracle's gain captured by online policies
fig, ax = plt.subplots(figsize=(7.5, 4.3))
onp = [("SLRU 1/3", "slru0.33", onl), ("SLRU 1/2", "slru0.5", onl), ("reactive migration", "reactive_mig", cap), ("admission filter θ=0.12", "pred_admit", onl), ("oracle, horizon 60 s", "oracle_h60", cap), ("oracle, horizon 300 s", "oracle_h300", cap)]
for j, tr in enumerate(TRACES):
    base = get(cap, tr, "split"); top = get(cap, tr, "oracle_min")
    vals = [100 * (get(rs, tr, p) - base) / (top - base) for _, p, rs in onp]
    b = ax.bar([x + (j - 1) * w for x in range(len(onp))], vals, w * 0.92, color=COL[tr], label=tr)
    for r, v in zip(b, vals): ax.annotate(f"{v:.0f}", (r.get_x() + r.get_width() / 2, max(v, 0)), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8.5)
ax.axhline(50, color="#d62728", ls=":", lw=1.2); ax.text(0.02, 52, "Gate 2: 50% of the oracle gain", color="#d62728", fontsize=10, transform=ax.get_yaxis_transform())
ax.set_xticks(range(len(onp))); ax.set_xticklabels([p[0] for p in onp], fontsize=9, rotation=15, ha="right"); ax.set_ylabel("share of the oracle's gain over the static split, %"); ax.set_ylim(-25, 110); ax.legend(loc="upper left")
save(fig, "fig-oracle-gain-captured")
