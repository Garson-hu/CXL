#!/usr/bin/env python3
"""Figures of the session-level hint study (2026-10-17) from session-hints-<tag>.csv and session-structure-<tag>.json.
usage: kv_session_hint_figs.py [dir] [tag=8b-200GiB]"""
import csv, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "experimental_results", "2026-10-17-kv-session-hint-study"); TAG = sys.argv[2] if len(sys.argv) > 2 else "8b-200GiB"
TRACES = ["conversation", "toolagent", "synthetic"]; COL = {"conversation": "#1f77b4", "toolagent": "#2ca02c", "synthetic": "#9467bd"}
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
rows = list(csv.DictReader(open(os.path.join(D, f"session-hints-{TAG}.csv")))); S = json.load(open(os.path.join(D, f"session-structure-{TAG}.json")))
def get(tr, pol, key="reuse_hit_share"): return next(float(r[key]) for r in rows if r["trace"] == tr and r["policy"] == pol)
def gain(tr, pol): base, top = get(tr, "split"), get(tr, "oracle_min"); return 100 * (get(tr, pol) - base) / (top - base)
def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(D, name + ".png"), dpi=200); fig.savefig(os.path.join(D, name + ".svg")); plt.close(fig); print("wrote", name)
w = 0.27
# 1. session structure
fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.3), gridspec_kw=dict(width_ratios=[1.4, 1, 1]))
keys = [("single_turn_share", "single-turn\nsessions"), ("requests_continued", "requests with\na next turn"), ("reuse_within_session", "reuses within\nthe session"), ("prefix_reuse_ratio_all_mean", "blocks re-read by\nthe next turn"), ("prefix_reuse_ratio_new_mean", "NEW blocks re-read\nby the next turn")]
for j, tr in enumerate(TRACES):
    vals = [100 * S[tr][k] for k, _ in keys]; b = axs[0].bar([x + (j - 1) * w for x in range(len(keys))], vals, w * 0.92, color=COL[tr], label=tr)
    for r, v in zip(b, vals): axs[0].annotate(f"{v:.0f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8)
axs[0].set_xticks(range(len(keys))); axs[0].set_xticklabels([k[1] for k in keys], fontsize=8, rotation=20, ha="right"); axs[0].set_ylabel("%"); axs[0].legend(fontsize=9); axs[0].set_ylim(0, 110); axs[0].set_title("Session structure (reconstructed from prefix chains)", fontsize=11, loc="left")
for j, tr in enumerate(TRACES):
    vals = [100 * S[tr][k] for k in ("next_turn_within_60", "next_turn_within_300", "next_turn_within_900")]
    axs[1].plot([60, 300, 900], vals, marker="o", color=COL[tr], label=f"{tr} (p50 gap {S[tr]['next_turn_gap_p50']:.0f} s)")
axs[1].set_xscale("log"); axs[1].set_xticks([60, 300, 900]); axs[1].set_xticklabels(["60 s", "300 s", "900 s"]); axs[1].set_xticks([], minor=True); axs[1].set_ylabel("next turn arrives within, %"); axs[1].set_ylim(0, 105); axs[1].legend(fontsize=8.5, loc="lower right"); axs[1].set_xlabel("time after the turn")
pol = [("split", "static split"), ("hint:mode=both", "perfect session\nhint"), ("oracle_min", "block oracle")]
for j, tr in enumerate(TRACES):
    vals = [100 * get(tr, p, "dead_occupancy_share") for p, _ in pol]; b = axs[2].bar([x + (j - 1) * w for x in range(len(pol))], vals, w * 0.92, color=COL[tr])
    for r, v in zip(b, vals): axs[2].annotate(f"{v:.0f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8.5)
axs[2].set_xticks(range(len(pol))); axs[2].set_xticklabels([p[1] for p in pol], fontsize=9.5); axs[2].set_ylabel("occupancy-time spent on dead blocks, %"); axs[2].set_ylim(0, 100); axs[2].set_title("What the cache holds", fontsize=11, loc="left")
save(fig, "fig-session-structure")
# 2. policies
pols = [("static split (B)", "split"), ("global LRU (C)", "global_lru"), ("session TTL 300 s\n(online)", "session_ttl300"), ("session TTL 60 s\n(online)", "session_ttl60"),
        ("termination event,\ndelay 300 s", "hint:delay=300"), ("termination event,\ndelay 60 s", "hint:delay=60"), ("termination event,\ndelay 10 s", "hint:delay=10"), ("termination event,\nno delay", "hint:delay=0"),
        ("perfect hint,\nadmission only", "hint:mode=admit"), ("perfect hint,\neviction only", "hint:mode=evict"), ("perfect hint,\nboth", "hint:mode=both"), ("perfect hint,\ncontinues ≤ 300 s", "hint:mode=both,bound=300"), ("block-level\noracle (E)", "oracle_min")]
fig, ax = plt.subplots(figsize=(14, 5.6))
for j, tr in enumerate(TRACES):
    vals = [get(tr, p) for _, p in pols]; b = ax.bar([x + (j - 1) * w for x in range(len(pols))], vals, w * 0.92, color=COL[tr], label=tr)
    for r, v in zip(b, vals): ax.annotate(f"{v:.2f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7.5, rotation=90)
ax.set_xticks(range(len(pols))); ax.set_xticklabels([p[0] for p in pols], fontsize=8.5, rotation=25, ha="right"); ax.set_ylabel("reuse-hit share (test half)"); ax.set_ylim(0, 1.12); ax.legend(loc="upper left")
ax.axvspan(1.5, 7.5, color="#f3f3f3", zorder=0); ax.text(4.5, 1.06, "online or delayed signals (no future information)", ha="center", fontsize=9.5, color="#555555"); ax.text(10, 1.06, "oracle session hints", ha="center", fontsize=9.5, color="#555555")
save(fig, "fig-session-hint-policies")
# 3. share of the block oracle's gain recovered, and sensitivity
fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
sp = [("admission only", "hint:mode=admit"), ("eviction only", "hint:mode=evict"), ("both", "hint:mode=both"), ("both, ≤ 900 s", "hint:mode=both,bound=900"), ("both, ≤ 300 s", "hint:mode=both,bound=300"), ("both, ≤ 60 s", "hint:mode=both,bound=60")]
for j, tr in enumerate(TRACES):
    vals = [gain(tr, p) for _, p in sp]; b = axs[0].bar([x + (j - 1) * w for x in range(len(sp))], vals, w * 0.92, color=COL[tr], label=tr)
    for r, v in zip(b, vals): axs[0].annotate(f"{v:.0f}", (r.get_x() + r.get_width() / 2, max(v, 0)), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8)
axs[0].set_xticks(range(len(sp))); axs[0].set_xticklabels([p[0] for p in sp], fontsize=9, rotation=20, ha="right"); axs[0].set_ylabel("share of the block oracle's gain, %"); axs[0].axhline(50, color="#d62728", ls=":", lw=1.2); axs[0].set_ylim(-10, 110); axs[0].legend(fontsize=9); axs[0].set_title("Perfect session hints (oracle)", fontsize=11)
for tr in TRACES:
    axs[1].plot([0, 10, 30], [gain(tr, "hint:mode=both")] + [gain(tr, f"hint:mode=both,fp={p}") for p in ("0.1", "0.3")], marker="o", color=COL[tr], label=f"{tr}: false positives")
    axs[1].plot([0, 10, 30], [gain(tr, "hint:mode=both")] + [gain(tr, f"hint:mode=both,fn={p}") for p in ("0.1", "0.3")], marker="s", ls="--", color=COL[tr], label=f"{tr}: false negatives")
    axs[1].plot([0, 30, 60], [gain(tr, "hint:mode=both")] + [gain(tr, f"hint:mode=both,miss={p}") for p in ("0.3", "0.6")], marker="^", ls=":", color=COL[tr], label=f"{tr}: missing")
axs[1].set_xlabel("hint error / missing rate, %"); axs[1].set_ylabel("share of the block oracle's gain, %"); axs[1].axhline(50, color="#d62728", ls=":", lw=1.2); axs[1].set_ylim(-10, 110); axs[1].legend(fontsize=7.5, ncol=1); axs[1].set_title("Hint accuracy", fontsize=11)
for tr in TRACES:
    axs[2].plot([0, 10, 60, 300], [gain(tr, f"hint:delay={d}") for d in (0, 10, 60, 300)], marker="o", color=COL[tr], label=tr)
axs[2].set_xlabel("termination event delay after the last turn, s"); axs[2].set_ylabel("share of the block oracle's gain, %"); axs[2].axhline(50, color="#d62728", ls=":", lw=1.2); axs[2].set_ylim(-10, 110); axs[2].legend(fontsize=9); axs[2].set_title("Events only (no positive hint)", fontsize=11)
save(fig, "fig-session-hint-sensitivity")
# 4. writes and occupancy
fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
wp = [("split", "static split"), ("hint:mode=evict", "hint,\neviction only"), ("hint:mode=admit", "hint,\nadmission only"), ("hint:mode=both", "hint, both"), ("oracle_min", "block oracle")]
for j, tr in enumerate(TRACES):
    vals = [(get(tr, p, "dram_GB") + get(tr, p, "cxl_GB")) / 1000 for p, _ in wp]; b = axs[0].bar([x + (j - 1) * w for x in range(len(wp))], vals, w * 0.92, color=COL[tr], label=tr)
    for r, v in zip(b, vals): axs[0].annotate(f"{v:.1f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8)
    vals = [get(tr, p, "useful_occupancy") for p, _ in wp]; axs[1].bar([x + (j - 1) * w for x in range(len(wp))], vals, w * 0.92, color=COL[tr], label=tr)
axs[0].set_xticks(range(len(wp))); axs[0].set_xticklabels([p[1] for p in wp], fontsize=9.5, rotation=15, ha="right"); axs[0].set_ylabel("bytes written to host memory, TB"); axs[0].legend(fontsize=9)
axs[1].set_xticks(range(len(wp))); axs[1].set_xticklabels([p[1] for p in wp], fontsize=9.5, rotation=15, ha="right"); axs[1].set_ylabel("useful occupancy"); axs[1].set_ylim(0, 1)
save(fig, "fig-session-hint-writes-occupancy")
