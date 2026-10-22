#!/usr/bin/env python3
"""Figures of the 2026-10-21 hardware validation (kvreplay + Adam on c28). usage: kv_hwval_figs.py <results dir>
fig-hwval-timeline: one co-run per stream at 70B 4x (conversation): DRAM write rate issued by the replayer (100 ms bins) and
the Adam step time, quiet window shaded (rates from the per-store records). fig-hwval-slowdown: measured Adam p99 slowdown per configuration and stream (every
repetition, mean), the Phase 3 prediction, the Adam-alone null runs and the 7% SLO. fig-hwval-bursts: measured 10 ms DRAM
write-rate distribution (complementary CDF) of admit-all vs filtered vs filtered + budget at 70B 4x and 8B 8x."""
import gzip
import csv, glob, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
def rd(p):   # raw text files may be gzip-compressed in place after the campaign
    if os.path.exists(p): return open(p).read()
    if os.path.exists(p + ".gz"): return gzip.open(p + ".gz", "rt").read()
    return ""
def ex(p): return os.path.exists(p) or os.path.exists(p + ".gz")
D = sys.argv[1]
plt.rcParams.update({"font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
STREAMS = [("admitall", "admit-all (split + LRU)", C[7]), ("filtered", "RQ1-filtered (value_split)", C[0]), ("budget", "filtered + live budget (independent)", C[1])]
CFGS = [("conversation-8b-8x", "conv 8B 8×"), ("conversation-70b-4x", "conv 70B 4×"), ("toolagent-8b-8x", "tool 8B 8×"), ("toolagent-70b-4x", "tool 70B 4×"), ("conversation-70b-8x", "conv 70B 8×")]
POL = {"admitall": "split_lru", "filtered": "value_split", "budget": "indep"}
def binrates(ev, dt, T):
    n = int(T / dt) + 1; v = [0.0] * n
    for s_, e, b in ev:
        if e <= s_: e = s_ + 1e-6
        i0, i1 = int(s_ / dt), min(int(e / dt), n - 1)
        for i in range(i0, i1 + 1):
            x0, x1 = max(s_, i * dt), min(e, (i + 1) * dt)
            if x1 > x0: v[i] += b * (x1 - x0) / (e - s_)
    return [x / dt / 1e9 for x in v]
def load_summary(group):
    p = f"{D}/{group}/summary.csv"
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []
def meta(tag, group):
    M = {}
    for l in open(f"{D}/{group}/{tag}-meta.txt"): f = l.split(); M[f[1]] = int(f[2])
    return M
def pred(cfg, stream):
    p = f"{D}/sim/sim-{cfg}-adam-joint.csv"
    if not os.path.exists(p): return None
    for r in csv.DictReader(open(p)):
        if r["policy"] == POL[stream]: return float(r["neighbour_p99_pct"])
# ---- 1. timeline ----
fig, axs = plt.subplots(3, 1, figsize=(13, 8.5), sharex=True); drawn = False
for ax, (s, lab, col) in zip(axs, STREAMS):
    tag = f"corun-conversation-70b-4x-{s}-r1"; rf = f"{D}/corun/{tag}-replay.txt"; nf = f"{D}/corun/{tag}-neighbor.txt"
    if not (ex(rf) and ex(nf) and os.path.exists(f"{D}/corun/{tag}-meta.txt")): continue
    M = meta(tag, "corun"); txt = rd(rf); m = re.search(r"^START (\d+)", txt, re.M)
    if not m or "done" not in M: continue
    t0 = M["before_start"]; st_ = int(m[1]); off = (st_ - t0) / 1e9
    Rr = [l.split() for l in txt.splitlines() if l.startswith("R ")]; evD = [(float(x[3]) / 1e3, float(x[4]) / 1e3, float(x[5])) for x in Rr if x[6] == "D" and x[7] == "1"]
    T = max(e for _, e, _ in evD) if evD else 1.0; d100 = binrates(evD, 0.1, T); t100 = [off + (i + 1) * 0.1 for i in range(len(d100))]
    ax.plot(t100, d100, color=col, lw=0.6, label=f"DRAM writes issued, 100 ms bins — {lab}")
    ax.axhline(8, color=C[3], ls=":", lw=0.8, label="safe DRAM budget beside Adam ≈ 6–8 GB/s (2026-09-21/10-12)")
    ax.set_ylabel("GB/s"); ax.set_ylim(0, max(10, max(d100) * 1.1) if d100 else 10)
    steps = [(int(t), float(v)) for v, t in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", rd(nf))]
    ax2 = ax.twinx(); ax2.plot([(t - t0) / 1e9 for t, v in steps], [1e3 * v for t, v in steps], color="k", lw=0.4, alpha=0.6, label="Adam step time (ms)")
    ax2.set_ylabel("Adam step, ms"); ax2.set_ylim(120, 220); ax2.grid(False)
    ax.axvspan(0, (M["before_end"] - t0) / 1e9, color="#dddddd", alpha=0.5, label="quiet window (Adam alone)")
    ax.legend(fontsize=8, loc="upper left"); ax2.legend(fontsize=8, loc="upper right"); drawn = True
axs[-1].set_xlabel("seconds from the start of the quiet window (70B 4×, conversation, repetition 1)")
if drawn: fig.tight_layout(); fig.savefig(f"{D}/fig-hwval-timeline.png", dpi=200); fig.savefig(f"{D}/fig-hwval-timeline.svg"); print("wrote fig-hwval-timeline")
# ---- 2. slowdown ----
rows = load_summary("corun") + load_summary("x8"); alone = load_summary("alone")
if rows:
    fig, ax = plt.subplots(figsize=(12, 5.2)); xs = {c: i for i, (c, _) in enumerate(CFGS)}
    for si, (s, lab, col) in enumerate(STREAMS):
        dx = (si - 1) * 0.22; first = True
        for c, _ in CFGS:
            v = [float(r["slow_p99"]) for r in rows if r.get("slow_p99") not in (None, "") and r["writelog"].startswith(c + "-") and (f"-{s}-r" in r["tag"])]
            if not v: continue
            ax.scatter([xs[c] + dx] * len(v), v, color=col, s=18, alpha=0.7, label=f"measured p99 slowdown, {lab} (each repetition)" if first else None)
            ax.scatter([xs[c] + dx], [sum(v) / len(v)], color=col, s=70, marker="_", linewidths=2.5, label=f"mean" if first and si == 0 else None)
            p = pred(c, s)
            if p is not None: ax.scatter([xs[c] + dx], [p], facecolors="none", edgecolors=col, s=55, marker="D", label="Phase 3 prediction (interference curve)" if first and si == 0 else None)
            first = False
    nv = [float(x) for r in alone for x in r.get("per_min_p99", "").split()] + [float(r["slow_p99"]) for r in alone if r.get("slow_p99") not in (None, "")]
    if nv: ax.axhspan(min(nv), max(nv), color="#bbbbbb", alpha=0.5, label=f"Adam alone: p99 of each later minute / quiet p99 − 1 (null, {len(alone)} runs, spread {min(nv):+.1f}…{max(nv):+.1f}%)")
    ax.axhline(7, color="k", ls="--", lw=0.9, label="SLO: p99 +7%"); ax.axhline(0, color="k", lw=0.5)
    ax.set_xticks(range(len(CFGS))); ax.set_xticklabels([l for _, l in CFGS]); ax.set_ylabel("Adam p99 step-time slowdown vs quiet window, %"); ax.set_yscale("symlog", linthresh=2); ax.set_ylim(-0.8, 40)
    ax.set_title("HW (CPU replay of the Phase 3 DRAM-targeted writes beside the real 80-thread Adam step, c28; CXL-targeted stores not issued)", fontsize=10)
    ax.legend(fontsize=7.5, ncol=2, loc="upper right", bbox_to_anchor=(1.0, 0.93)); fig.tight_layout(); fig.savefig(f"{D}/fig-hwval-slowdown.png", dpi=200); fig.savefig(f"{D}/fig-hwval-slowdown.svg"); print("wrote fig-hwval-slowdown")
# ---- 3. bursts ----
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6)); drawn = False
for ax, (c, lab) in zip(axs, [("conversation-70b-4x", "conv 70B 4×"), ("conversation-8b-8x", "conv 8B 8×")]):
    for s, slab, col in STREAMS:
        rf = f"{D}/corun/corun-{c}-{s}-r1-replay.txt"
        if not ex(rf): continue
        txt = rd(rf); nums = dict(re.findall(r"([a-z_0-9]+) ([\d.]+)", " ".join(l for l in txt.splitlines() if l.startswith("S "))))
        m = re.search(r"^START (\d+)", txt, re.M)
        if not m: continue
        d1 = int(m[1]) + int(float(nums.get("active_s", 0)) * 1e9)
        Rr = [l.split() for l in txt.splitlines() if l.startswith("R ")]; evD = [(float(x[3]) / 1e3, float(x[4]) / 1e3, float(x[5])) for x in Rr if x[6] == "D" and x[7] == "1"]
        dr = sorted(binrates(evD, 0.01, max(e for _, e, _ in evD)), reverse=True) if evD else []
        if not dr: continue
        ax.plot(dr, [(i + 1) / len(dr) for i in range(len(dr))], color=col, lw=1.2, label=slab); drawn = True
    ax.set_xscale("symlog", linthresh=1); ax.set_yscale("log"); ax.set_xlabel("DRAM write rate in a 10 ms bin, GB/s"); ax.set_ylabel("share of 10 ms bins at or above"); ax.set_title(f"{lab}, measured by the replayer (repetition 1)", fontsize=10.5)
    ax.axvline(8, color=C[3], ls=":", lw=0.8); ax.legend(fontsize=8)
if drawn: fig.tight_layout(); fig.savefig(f"{D}/fig-hwval-bursts.png", dpi=200); fig.savefig(f"{D}/fig-hwval-bursts.svg"); print("wrote fig-hwval-bursts")
