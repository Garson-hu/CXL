#!/usr/bin/env python3
"""Regime analysis for the RQ1-B reuse-horizon validation (2026-10-17): reads the replay CSVs of several real agent
traces (kv_agent_replay.py, possibly with SYNTHETIC churn) and relates the value of the real lifecycle events to the
regime variables: reuse horizon H (previous use -> next use of a task's own chunks), LRU residence T_res (write ->
eviction under global LRU at that capacity), live working set W_live and capacity C.
Output: <out>/regime.csv and fig-regime.
A second figure (fig-regime-2d) places every replay point in the (C / W_live, H / T_res) plane coloured by the share
of the oracle's gain the continue signal recovers, with the ESTIMATED operating points of the public agent workloads
(Exgentic/agent-llm-traces parameters, 8B model, 200 GiB host cache, 16 / 64 / 256 concurrent agents) overlaid.
usage: kv_agent_regime.py <out_dir> <label=replay.csv> [...] [--public public-agent-summary.json]"""
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

args = [a for a in sys.argv[1:] if not a.startswith("--public=")]; PUB = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--public=")), None)
out = args[0]; os.makedirs(out, exist_ok=True); sys.argv = [sys.argv[0]] + args
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
pts = []
for arg in sys.argv[2:]:
    label, path = arg.split("=", 1); R = list(csv.DictReader(open(path)))
    G = {}
    for r in R: G.setdefault((int(r["cap"]), float(r.get("churn", 0) or 0)), {})[r["policy"]] = r
    for (cap, churn), P in sorted(G.items()):
        if "lru" not in P or "oracle" not in P: continue
        lru, orc = P["lru"], P["oracle"]; gain = float(orc["reuse_hit_share"]) - float(lru["reuse_hit_share"])
        for pol in ("event_end", "event_cont", "event_both", "slru", "ttl30"):
            if pol not in P: continue
            e = P[pol]
            pts.append(dict(trace=label, cap=cap, churn=churn, cap_GB=float(e["cap_GB"]), policy=pol, W_live=float(lru["W_live_mean"]), cap_over_Wlive=cap / max(1e-9, float(lru["W_live_mean"])),
                            P_total=float(lru["P_total_chunks_s"]), T_res=float(lru["residence_p50_s"]), H_p50=float(lru["H_p50_s"]), H_p90=float(lru["H_p90_s"]),
                            H_over_Tres=float(lru["H_p50_s"]) / max(1e-9, float(lru["residence_p50_s"])), lru_evict_before_reuse=float(lru["evict_before_reuse_share"]),
                            lru_hit=float(lru["reuse_hit_share"]), oracle_hit=float(orc["reuse_hit_share"]), pol_hit=float(e["reuse_hit_share"]), oracle_gain_pts=100 * gain,
                            share_of_gain=100 * (float(e["reuse_hit_share"]) - float(lru["reuse_hit_share"])) / max(1e-9, gain), hits_vs_lru=int(float(e.get("hits_vs_lru", 0) or 0)),
                            recompute_avoided_ktok=float(e.get("recompute_tokens_avoided_vs_lru", 0) or 0) / 1e3, dead_occ_lru=float(lru["dead_occupancy_share"])))
with open(f"{out}/regime.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(pts[0].keys())); w.writeheader(); w.writerows(pts)
fig, axs = plt.subplots(1, 3, figsize=(16, 4.6)); COL = {}
cyc = plt.rcParams["axes.prop_cycle"].by_key()["color"]
for i, lab in enumerate(sorted({p["trace"] for p in pts})): COL[lab] = cyc[i % len(cyc)]
for lab in COL:
    P = [p for p in pts if p["trace"] == lab and p["policy"] == "event_both"]
    axs[0].scatter([p["cap_over_Wlive"] for p in P], [p["lru_evict_before_reuse"] * 100 for p in P], color=COL[lab], label=lab, s=28)
    axs[1].scatter([p["cap_over_Wlive"] for p in P], [max(-20, min(110, p["share_of_gain"])) for p in P], color=COL[lab], label=lab, s=28)
    axs[2].scatter([p["cap_over_Wlive"] for p in P], [p["oracle_gain_pts"] for p in P], color=COL[lab], label=lab, s=28, marker="s")
    axs[2].scatter([p["cap_over_Wlive"] for p in P], [100 * (p["pol_hit"] - p["lru_hit"]) for p in P], color=COL[lab], s=28, marker="^")
axs[0].set_xscale("log"); axs[0].set_xlabel("capacity / live working set"); axs[0].set_ylabel("LRU evictions that precede a reuse, %"); axs[0].set_title("When LRU starts losing live blocks", fontsize=10.5)
axs[1].set_xscale("log"); axs[1].axhline(50, color="#d62728", ls=":", lw=1.2); axs[1].axvline(1, color="#7f7f7f", ls=":", lw=1); axs[1].set_xlabel("capacity / live working set"); axs[1].set_ylabel("share of the oracle's gain recovered, % (end + continue)"); axs[1].set_title("Gate 2 criterion vs capacity pressure (clipped at −20)", fontsize=10.5)
axs[1].text(1.05, -17, "C = W_live", fontsize=8, color="#7f7f7f")
axs[2].set_xscale("log"); axs[2].axhline(0, color="#7f7f7f", lw=0.8); axs[2].set_xlabel("capacity / live working set"); axs[2].set_ylabel("reuse-hit share, points"); axs[2].set_title("Absolute gap: oracle − LRU (squares), events − LRU (triangles)", fontsize=10.5)
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=min(6, len(l)), fontsize=8, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.1 if len(l) > 6 else 0.07, 1, 1)); fig.savefig(f"{out}/fig-regime.png", dpi=200, bbox_inches="tight"); fig.savefig(f"{out}/fig-regime.svg", bbox_inches="tight"); print("wrote", f"{out}/fig-regime.png", len(pts), "points")

# 2-D regime map: x = C / W_live, y = H / T_res, colour = share of the oracle's gain recovered by the continue signal
import json, math
fig, axs = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw=dict(width_ratios=[1.25, 1]))
P2 = [p for p in pts if p["policy"] == "event_cont" and p["oracle_gain_pts"] >= 0.5]        # points where there is a gain to recover (≥ 0.5 points)
sc = axs[0].scatter([p["cap_over_Wlive"] for p in P2], [min(30.0, p["H_over_Tres"]) for p in P2], c=[max(-20, min(100, p["share_of_gain"])) for p in P2], cmap="RdYlGn", vmin=-20, vmax=100, s=34, edgecolors="k", linewidths=0.3)
if any(p["H_over_Tres"] > 30 for p in P2): axs[0].text(1.1, 18, "top row: bursty background runs\n(LRU residence ≈ 0, each burst flushes the cache; shown at 30)", fontsize=7.5, color="#555555")
axs[0].set_xscale("log"); axs[0].set_yscale("log"); axs[0].axvline(1, color="#7f7f7f", ls=":", lw=1); axs[0].axhline(1, color="#7f7f7f", ls=":", lw=1)
axs[0].set_xlabel("capacity / live working set  (C / W_live)"); axs[0].set_ylabel("reuse horizon / LRU residence  (H / T_res)")
axs[0].set_title("Replays of the real agent traces (points with an oracle gap ≥ 0.5 pt)", fontsize=10.5); cb = fig.colorbar(sc, ax=axs[0]); cb.set_label("share of the oracle's gain recovered by the continue signal, %")
axs[0].text(1.05, axs[0].get_ylim()[0] * 1.3, "C = W_live", fontsize=8, color="#7f7f7f", rotation=90); axs[0].text(axs[0].get_xlim()[0] * 1.2, 1.1, "H = T_res", fontsize=8, color="#7f7f7f")
if PUB:
    J = json.load(open(PUB)); CH = 256; Cc = 200 * 2**30 / (32 * 2**20)
    marks = {16: "o", 64: "s", 256: "^"}; first = True
    for b, v in J["per_benchmark"].items():
        ctx = v["in_tok_p50"] / CH; H = v["horizon_p50"]; calls = v["calls_per_session_p50"]; growth = max(1.0, v["context_growth_per_step_p50"] / CH)
        for K, m in marks.items():
            W = K * ctx; Pr = K * (growth / H + ctx / (calls * H)); T = Cc / Pr
            axs[1].scatter(Cc / W, H / T, marker=m, s=46, facecolors="none", edgecolors="k", label=f"{K} concurrent agents" if first else None)
            if K == 64: axs[1].annotate(b, (Cc / W, H / T), xytext=(4, 3), textcoords="offset points", fontsize=7.5)
        first = False
    axs[1].set_xscale("log"); axs[1].set_yscale("log"); axs[1].axvline(1, color="#7f7f7f", ls=":", lw=1); axs[1].axhline(1, color="#7f7f7f", ls=":", lw=1)
    axs[1].set_xlabel("capacity / live working set  (C / W_live)"); axs[1].set_ylabel("reuse horizon / LRU residence  (H / T_res)")
    axs[1].set_title("ESTIMATE: public agent workloads at a 200 GiB host cache, 8B model\n(Exgentic/agent-llm-traces medians; labels at 64 agents)", fontsize=9.5); axs[1].legend(fontsize=8, loc="lower right")
    lo = min(axs[0].get_xlim()[0], axs[1].get_xlim()[0]); hi = max(axs[0].get_xlim()[1], axs[1].get_xlim()[1]); axs[1].set_xlim(lo, hi); axs[0].set_xlim(lo, hi)
    ylo = min(axs[0].get_ylim()[0], axs[1].get_ylim()[0]); yhi = max(axs[0].get_ylim()[1], axs[1].get_ylim()[1]); axs[0].set_ylim(ylo, yhi); axs[1].set_ylim(ylo, yhi)
fig.tight_layout(); fig.savefig(f"{out}/fig-regime-2d.png", dpi=200); fig.savefig(f"{out}/fig-regime-2d.svg"); print("wrote", f"{out}/fig-regime-2d.png")
