#!/usr/bin/env python3
"""Figures for docs/experiments/2026-10-06-why-evidence.md: (a) per-token latency of the llama.cpp tenant during a copy
burst, (b) checkpoint overhead vs period for the stock PyTorch path and cxlpath. Output: experimental_results/2026-10-06-why-evidence/."""
import re, statistics as st
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = "/home/ghu4/CXL/experimental_results"; OUT = f"{R}/2026-10-06-why-evidence"
DRAM, CXL, GRAY, INK, INK2, LIGHT = "#c8511b", "#1f6f78", "#8a9bb0", "#15202b", "#4a5568", "#f7f6f2"
plt.rcParams.update({"font.size": 11, "text.color": INK, "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": LIGHT, "axes.facecolor": LIGHT, "savefig.facecolor": LIGHT, "legend.frameon": False})
def despine(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e3e2de", lw=0.8); ax.set_axisbelow(True)
# (a) token latency timeline around the 4th copy window, llama.cpp-80, repetition 1
d = f"{R}/2026-09-22-three-policies-realdata"; fig, ax = plt.subplots(figsize=(10, 3.8))
for tag, label, color in [("llama-dram-rep1", "checkpoint staged in DRAM (today)", DRAM), ("llama-cxlpath-b1.06-rep1", "checkpoint staged in CXL (cxlpath)", CXL)]:
    pt = open(f"{d}/{tag}-producer.txt").read(); wins = [(int(m[1]), int(m[2])) for m in re.findall(r"COPY (\d+) START (\d+) END (\d+)", pt)]; s0, s1 = wins[3]
    toks = [int(m) for m in re.findall(r"^TOK (\d+)", open(f"{d}/{tag}-victim.txt").read(), flags=re.M)]
    xs = [(toks[i] - s0) / 1e9 for i in range(1, len(toks)) if s0 - 2e9 <= toks[i] <= s0 + 4e9]; ys = [(toks[i] - toks[i - 1]) / 1e6 for i in range(1, len(toks)) if s0 - 2e9 <= toks[i] <= s0 + 4e9]
    ax.plot(xs, ys, color=color, lw=1.5, label=f"{label}: copy takes {(s1 - s0) / 1e9:.2f} s"); ax.axvspan(0, (s1 - s0) / 1e9, color=color, alpha=0.08)
ax.set_xlabel("time relative to the start of the 64 GiB checkpoint copy, s"); ax.set_ylabel("time per generated token, ms"); ax.set_ylim(25, 55); despine(ax); ax.legend(loc="upper right", fontsize=9)
ax.set_title("llama.cpp decoding (Qwen2.5-7B Q8, 80 threads) beside a checkpoint copy: every token slows while DRAM is the staging buffer", fontsize=10)
fig.tight_layout(); fig.savefig(f"{OUT}/token-latency-timeline.png", dpi=200); plt.close(fig)
# (b) checkpoint overhead vs period
cfg = {"stock DRAM staging (PyTorch DCP)": (dict(stall=1.60, persist=31.0, tail=[(7.0, 0.015), (24.0, 0.004)]), DRAM), "cxlpath": (dict(stall=0.81, persist=19.0, tail=[]), CXL)}
def overhead(c, T, scale):
    stall = c["stall"] * scale; persist = c["persist"] * scale
    if T < stall + persist: return None
    return 100 * (stall + sum(min(dd * scale, T) * s for dd, s in c["tail"])) / T
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for ax, scale, title in zip(axes, (1, 4), ("16 GiB state (measured)", "64 GiB state (stall and persist scaled 4x)")):
    Ts = [t for t in range(10, 601, 2)]
    for name, (c, color) in cfg.items():
        ys = [overhead(c, t, scale) for t in Ts]; ax.plot([t for t, y in zip(Ts, ys) if y is not None], [y for y in ys if y is not None], color=color, lw=2, label=name)
    ax.axhline(3, color=INK2, ls=":", lw=1); ax.text(560, 3.3, "3% budget", fontsize=9, color=INK2, ha="right")
    ax.set_xlabel("checkpoint period, s"); ax.set_title(title, fontsize=10); ax.set_ylim(0, 8); despine(ax)
axes[0].set_ylabel("training time lost to checkpointing, %"); axes[0].legend(fontsize=9)
fig.suptitle("How often can a job checkpoint for a given overhead? (training thread blocked + own compute slowed while the checkpoint is written)", fontsize=10)
fig.tight_layout(); fig.savefig(f"{OUT}/checkpoint-overhead-vs-period.png", dpi=200); plt.close(fig); print("wrote 2 figures")
