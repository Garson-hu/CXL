#!/usr/bin/env python3
"""Figures of Experiment C (scheduling gap) from run_c.py's c-summary.csv and c-decomposition.csv.
  figC1  measured TTFT vs the calibrated model of the existing scheduler (validation) and vs the references
         (ZERO-DELAY loads, CLAIRVOYANT shortest-remaining-prefill-first), per open-loop rate and per closed-loop concurrency
  figC2  sources of the measured TTFT per tier (queue wait before the load, KV load, ready-but-waiting, compute, client legs)
  figC3  scheduling improvement (measured - reference) vs concurrency / rate
usage: figs_c.py <C dir> <fig dir> [tag=b-default]"""
import csv, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

Cd, FIG = sys.argv[1], sys.argv[2]; TAG = sys.argv[3].split("=", 1)[1] if len(sys.argv) > 3 else "b-default"; os.makedirs(FIG, exist_ok=True)
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
S = [{k: (v if k in ("tag", "grp", "policy") else fl(v)) for k, v in r.items()} for r in csv.DictReader(open(f"{Cd}/c-summary.csv"))]
Dd = [{k: (v if k in ("tag", "grp", "tier") else fl(v)) for k, v in r.items()} for r in csv.DictReader(open(f"{Cd}/c-decomposition.csv"))]
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
POL = [("measured", "measured (real vLLM + LMCache)", "k", "-"), ("vllm", "model of the existing scheduler (SIMULATED)", C[0], "--"), ("zero", "zero-delay loads (REFERENCE, not implementable)", C[1], ":"),
       ("srpt", "clairvoyant shortest-prefill-first (REFERENCE)", C[3], "-."), ("hits", "hits before cold (model)", C[2], ":")]
def series(tag, prefix, policy, key):
    pts = [(float(s["grp"][len(prefix):]), s[key]) for s in S if s["tag"] == tag and s["grp"].startswith(prefix) and s["policy"] == policy and s.get(key) is not None]
    pts.sort(); return [p[0] for p in pts], [p[1] for p in pts]

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for row, (prefix, xl) in enumerate((("s2-r", "offered arrival rate (requests/s)"), ("s1-c", "closed-loop concurrency"))):
    for col, (key, name) in enumerate((("mean_ms", "mean TTFT"), ("p95_ms", "p95 TTFT"))):
        ax = axes[row][col]
        for pol, label, color, ls in POL:
            x, y = series(TAG, prefix, pol, key)
            if x: ax.plot(x, y, color=color, ls=ls, marker="o", ms=3, label=label)
        ax.set_xlabel(xl); ax.set_ylabel(f"{name} (ms, log)"); ax.set_yscale("log"); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=6.5)
        if prefix == "s1-c": ax.set_xscale("log", base=2)
fig.suptitle(f"Figure C1 — measured TTFT vs the calibrated model and the scheduling references ({TAG}; references use the SAME arrivals, lengths and tiers)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figC1-measured-vs-reference.png", dpi=300); fig.savefig(f"{FIG}/figC1-measured-vs-reference.pdf"); plt.close(fig)

# figC2: decomposition per tier for the open-loop rates
LEGS = [("client_to_queued", "client → engine queue"), ("queued_to_load_start", "queued → load start (lookup / first scheduling attempt)"), ("alloc_to_transfer", "blocks allocated → transfer start"), ("transfer", "transfer host → GPU"),
        ("done_to_noticed", "load done → noticed at a step boundary"), ("ready_to_sched", "KV ready → scheduled (waiting for the GPU)"),
        ("queued_to_sched_no_load", "queued → scheduled (no host load)"), ("compute", "scheduled → first token (prefill)"), ("engine_to_client", "engine → client")]
grps = sorted({d["grp"] for d in Dd if d["tag"] == TAG and d["grp"].startswith("s2-r")}, key=lambda g: float(g[4:]))
fig, axes = plt.subplots(1, len(grps) or 1, figsize=(3.2 * max(1, len(grps)), 4.6), sharey=False)
if len(grps) == 1: axes = [axes]
for ax, g in zip(axes, grps):
    xs = []
    for tier in ("host", "gpu", "cold"):
        d = next((d for d in Dd if d["tag"] == TAG and d["grp"] == g and d["tier"] == tier), None)
        if not d: continue
        xs.append(f"{tier}\n(n={int(d['n'])})"); b = 0.0
        for i, (k, name) in enumerate(LEGS):
            v = d.get(k + "_mean")
            if v is None: continue
            ax.bar(len(xs) - 1, v, bottom=b, color=C[i], width=0.6, label=name if (g == grps[0] and tier == "host") or (g == grps[0] and tier == "cold" and k == "queued_to_sched_no_load") else None); b += v
        ax.text(len(xs) - 1, b, f"{d['ttft_mean']:.0f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(len(xs))); ax.set_xticklabels(xs, fontsize=8); ax.set_title(f"{float(g[4:]):g} req/s", fontsize=10); ax.grid(alpha=.3, axis="y")
axes[0].set_ylabel("mean ms per request (legs are means, so they add up to the mean TTFT)")
h, l = axes[0].get_legend_handles_labels(); fig.legend(h, l, fontsize=7, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 0.98))
fig.suptitle(f"Figure C2 — where the measured TTFT goes, per tier served and offered rate ({TAG}, open loop)", fontsize=9, y=1.0)
fig.tight_layout(rect=(0, 0, 1, 0.88)); fig.savefig(f"{FIG}/figC2-sources-of-delay.png", dpi=300); fig.savefig(f"{FIG}/figC2-sources-of-delay.pdf"); plt.close(fig)

# figC3: improvement opportunity vs concurrency / rate
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, (prefix, xl) in zip(axes, (("s1-c", "closed-loop concurrency"), ("s2-r", "offered arrival rate (requests/s)"))):
    for key, name, ls in (("mean_ms", "mean", "-"), ("p95_ms", "p95", "--")):
        xm, ym = series(TAG, prefix, "measured", key)
        for pol, label, color in (("zero", "vs zero-delay loads", C[1]), ("srpt", "vs clairvoyant shortest-prefill-first", C[3]), ("vllm", "vs the model of the existing scheduler (validation)", C[0])):
            xr, yr = series(TAG, prefix, pol, key)
            pts = [(x, (m - r) / m * 100) for x, m, xx, r in zip(xm, ym, xr, yr) if x == xx and m]
            if pts: ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, ls=ls, marker="o", ms=3, label=f"{name} TTFT {label}")
    ax.axhline(0, color="gray", lw=0.8); ax.set_xlabel(xl); ax.set_ylabel("measured TTFT minus reference, % of measured"); ax.grid(alpha=.3); ax.legend(fontsize=6.5)
    if prefix == "s1-c": ax.set_xscale("log", base=2)
fig.suptitle(f"Figure C3 — remaining scheduling opportunity vs load ({TAG}); positive = the reference is better", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figC3-opportunity-vs-load.png", dpi=300); fig.savefig(f"{FIG}/figC3-opportunity-vs-load.pdf"); plt.close(fig)
print("figures written to", FIG)
