#!/usr/bin/env python3
"""Figures of the exploratory-study deck of 2026-10-27 (docs/slides/SLIDES_2026-10-27-reuse-window-prefetch.pptx).
Every data figure is drawn from the figure data tables of the experiment report (experimental_results/2026-10-27-reuse-window-prefetch/figs/*.csv,
written by scripts/window_report_figs.py from the simulators' raw outputs) and from the raw files of the real CosmoFlow run (train/run-61440/reads.txt,
train/beegfs-bw-c33.txt); nothing is typed in by hand. f01 is a schematic without measured numbers.
Writes docs/slides/2026-10-27-reuse-window-prefetch/figs/<name>.png|.svg and figs/SOURCES.md.
Colours: matplotlib's default cycle, white background; capacities 30 / 60 / 120 / 180 / 360 / 720 GiB = C0 … C5 (as in the report figures);
policies: LRU C7, second touch C8, 2nd_int C1, RQ1 adaptive C3, window admission C2, oracle black.
usage: scripts/figs_deck_2026-10-27.py [repo_root]"""
import collections, csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
E = os.path.join(ROOT, "experimental_results", "2026-10-27-reuse-window-prefetch"); F = os.path.join(E, "figs")
OUT = os.path.join(ROOT, "docs", "slides", "2026-10-27-reuse-window-prefetch", "figs"); os.makedirs(OUT, exist_ok=True)   # docs/slides is local-only (gitignored)
plt.rcParams.update({"font.size": 12, "axes.titlesize": 12.5, "axes.labelsize": 12, "legend.fontsize": 10.5, "xtick.labelsize": 11, "ytick.labelsize": 11,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
                     "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.8, "axes.axisbelow": True, "legend.frameon": False, "svg.fonttype": "none"})
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
SOURCES = {}
def rows(p): return list(csv.DictReader(open(p)))
def fl(r, k):
    try: return float(r[k])
    except (ValueError, KeyError): return None
def save(fig, name, sources, note=None):
    fig.tight_layout(rect=(0, 0.06 if note else 0, 1, 1))
    if note: fig.text(0.005, 0.008, note, fontsize=9.5, color="#555555", ha="left", va="bottom")
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200, bbox_inches="tight"); fig.savefig(os.path.join(OUT, name + ".svg"), bbox_inches="tight"); plt.close(fig)
    SOURCES[name] = sources; print("wrote", name)
def box(ax, x, y, w, h, text, fc="#f3f6fa", ec="#9aa5b1", fs=11, bold=False, color="#1F2D3D", r=0.08):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=color, linespacing=1.3)
def arrow(ax, x0, y0, x1, y1, color="#555555", style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=14, color=color, lw=1.2))
def wax(ax):
    ax.set_xscale("symlog", linthresh=0.1, linscale=0.45); ax.set_xlim(-0.012, 2600); ax.set_xticks([0, 0.1, 1, 10, 100, 1000]); ax.set_xticklabels(["0", "0.1", "1", "10", "100", "1000"]); ax.minorticks_off()

# ---------------------------------------------------------------- f01: the two settings and the three questions (schematic)
fig, ax = plt.subplots(figsize=(12.3, 3.3)); ax.set_xlim(0, 12.3); ax.set_ylim(0, 3.3); ax.axis("off")
for x0, head, src, cons, win, col in [(0.2, "Training: data loader with a known schedule", "Storage\n(BeeGFS)", "Trainer\n(GPU)", "FUTURE window W: the loader knows which samples are\ndue within the next W seconds (epoch order drawn at epoch start)", C[0]),
                                      (6.35, "Inference: KV cache of an LLM serving engine", "Serving engine\n(new KV blocks)", "Serving engine\n(lookups)", "HISTORICAL window W: the cache knows only the\nlookups of the last W seconds", C[1])]:
    ax.text(x0 + 2.85, 3.12, head, ha="center", va="center", fontsize=12.5, fontweight="bold", color="#1B2A41")
    box(ax, x0, 1.35, 1.5, 0.9, src, fs=10.5); box(ax, x0 + 1.95, 1.2, 1.85, 1.2, "Cache\nDRAM 60 GiB\n+ CXL 120 GiB ?", fc="#e8f0fb", ec=col, fs=10.5, bold=True); box(ax, x0 + 4.25, 1.35, 1.5, 0.9, cons, fs=10.5)
    arrow(ax, x0 + 1.5, 1.8, x0 + 1.95, 1.8); arrow(ax, x0 + 3.8, 1.8, x0 + 4.25, 1.8)
    ax.text(x0 + 2.85, 0.55, win, ha="center", va="center", fontsize=10, color="#333333", bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=col, lw=1.0))
ax.text(6.15, 2.95, "", ha="center")
ax.plot([6.15, 6.15], [0.1, 3.25], color="#cccccc", lw=0.8)
save(fig, "f01_overview", ["schematic (no measured numbers); setting of docs/experiments/2026-10-27-reuse-window-prefetch.md"])

# ---------------------------------------------------------------- f02: the real run and the measured storage bandwidth
bw = [(int(l.split()[1]), float(l.split()[-1])) for l in open(os.path.join(E, "train", "beegfs-bw-c33.txt")) if l.startswith("streams")]
R = [(float(a[1]), int(a[2]), int(a[5])) for a in (l.split() for l in open(os.path.join(E, "train", "run-61440", "reads.txt"))) if a[0] == "R"]
DEMAND = 0.217
fig, axs = plt.subplots(1, 2, figsize=(12.3, 3.3), gridspec_kw=dict(width_ratios=[1, 1.45]))
ax = axs[0]; xs = range(len(bw)); bars = ax.bar(xs, [b for _, b in bw], color=[C[2] if s == 8 else C[7] for s, _ in bw], width=0.62)
for r_, (s, b) in zip(bars, bw): ax.annotate(f"{b:.2f}", (r_.get_x() + r_.get_width() / 2, b), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=10)
ax.axhline(DEMAND, color=C[3], ls="--", lw=1.4, label="trainer demand, epochs 1–2: 0.217 GB/s"); ax.legend(loc="upper left", fontsize=9.5)
ax.set_xticks(list(xs)); ax.set_xticklabels([str(s) for s, _ in bw]); ax.set_xlabel("concurrent read streams"); ax.set_ylabel("cold read bandwidth (GB/s)"); ax.set_ylim(0, 1.0)
ax.set_title("(a) BeeGFS cold reads, c33 (green: the run's 8 streams)", fontsize=11.5)
ax = axs[1]; t0 = min(t for t, _, _ in R); BIN = 10.0; acc = collections.Counter()
for t, e, b in R: acc[int((t - t0) // BIN)] += b
ks = sorted(acc); ax.plot([k * BIN / 60 for k in ks], [acc[k] / BIN / 1e9 for k in ks], color=C[0], lw=1.2)
ep = {}
for t, e, b in R: ep.setdefault(e, [t, t]); ep[e][1] = max(ep[e][1], t)
for e, (a, b) in sorted(ep.items()):
    ax.axvline((b - t0) / 60, color="#bbbbbb", lw=0.8, ls=":"); ax.text(((a + b) / 2 - t0) / 60, 0.265, f"epoch {e}", ha="center", fontsize=10, color="#333333")
ax.axhline(DEMAND, color=C[3], ls="--", lw=1.2); ax.set_ylim(0, 0.29); ax.set_xlabel("time since the first read (min)"); ax.set_ylabel("GB/s pulled (10-s bins)")
ax.set_title("(b) the real CosmoFlow run on the A100 node: 3 epochs × 61,440 files (178 GB)", fontsize=11.5)
save(fig, "f02_setup", ["train/beegfs-bw-c33.txt (cold reads of the test split, 2026-10-27)", "train/run-61440/reads.txt (per-file pull stamps of the real run, job 322135)"],
     note="Real measurements. Epoch 0 pays cold BeeGFS reads (63.5 samples/s); epochs 1–2 run at 74.9 samples/s = 0.217 GB/s of files (partly served by the node's page cache); the input pipeline pulls each file 0.4–0.85 s before its training step.")

# ---------------------------------------------------------------- f03: hit rate vs future window (per bandwidth at 60 GiB; per capacity at 0.20 GB/s)
f1 = rows(os.path.join(F, "fig1-train-window-by-capacity.csv")); f2 = rows(os.path.join(F, "fig2-train-window-by-bandwidth.csv"))
fig, axs = plt.subplots(1, 2, figsize=(12.3, 3.3), sharey=True)
ax = axs[0]
for i, (b, lab, ls) in enumerate([("0.064", "0.064 GB/s (1 stream, 0.3× demand)", "-"), ("0.2", "0.20 GB/s (simulated, 0.92×)", "--"), ("0.33", "0.33 GB/s (4 streams, 1.5×)", "-"), ("0.52", "0.52 GB/s (8 streams, 2.4×)", "-"), ("0.82", "0.82 GB/s (32 streams, 3.8×)", "-")]):
    pts = sorted((fl(r, "window_s"), fl(r, "hit_rate")) for r in f2 if r["bw_gbps"] == b)
    ax.plot([w for w, _ in pts], [h for _, h in pts], color=C[i], ls=ls, marker="o", ms=3.5, lw=1.6, label=lab)
wax(ax); ax.set_ylim(-0.03, 1.06); ax.set_xlabel("future window W (s); W = 0 = no prefetch"); ax.set_ylabel("hit rate, epochs 1–2")
ax.set_title("(a) C = 60 GiB (DRAM-only), one curve per storage bandwidth B"); ax.legend(loc="center left", bbox_to_anchor=(0.1, 0.56), fontsize=9.5)
ax.text(60, 0.84, "0.33 / 0.52 / 0.82 GB/s coincide:\n≥ 0.999 from W = 0.1 s", fontsize=10, color="#333333"); ax.text(30, 0.12, "0.064 GB/s: 0.075 at every W", fontsize=10, color="#333333")
ax = axs[1]
for i, cap in enumerate(["30.0", "60.0", "120.0", "180.0"]):
    pts = sorted((fl(r, "window_s"), fl(r, "hit_rate")) for r in f1 if r["bw_gbps"] == "0.2" and r["cap_gib"] == cap)
    ax.plot([w for w, _ in pts], [h for _, h in pts], color=C[i], marker="o", ms=3.5, lw=1.6, label=f"C = {cap[:-2]} GiB" + (" (DRAM-only)" if cap == "60.0" else " (DRAM + CXL)" if cap == "180.0" else ""))
wax(ax); ax.set_xlabel("future window W (s); W = 0 = no prefetch"); ax.set_title("(b) B = 0.20 GB/s (0.92× demand), one curve per capacity C")
ax.legend(loc="lower right", fontsize=9.5, title="saturation: 120 GiB at 25 s, 60 GiB at 100 s,\n30 GiB plateau 0.78 (the cache cannot hold the queue)", title_fontsize=9.5)
save(fig, "f03_window", ["figs/fig2-train-window-by-bandwidth.csv", "figs/fig1-train-window-by-capacity.csv (train/sim/*.csv, third pass + the 16:40 grid)"],
     note="Trace-driven simulation on the real demand timeline. Hit = the sample is resident (retained since the previous epoch) or its prefetch completed before its training step; a prefetch still in flight is a miss. 122,880 demands of epochs 1–2.")

# ---------------------------------------------------------------- f04: capacity: retention and storage traffic
f3 = rows(os.path.join(F, "fig3-train-capacity-by-window.csv")); f4 = rows(os.path.join(F, "fig4-train-storage-traffic.csv"))
fig, axs = plt.subplots(1, 2, figsize=(12.3, 3.3))
ax = axs[0]
for col, b, W, lab, mk in [(C[7], "0.52", "0.0", "no prefetch (W = 0): LRU retention", "o"), (C[2], "0.52", "0.25", "W = 0.25 s, B = 0.52 GB/s", "s"), (C[1], "0.2", "50.0", "W = 50 s, B = 0.20 GB/s", "^")]:
    pts = sorted((fl(r, "cap_gib"), fl(r, "hit_rate")) for r in f3 if r["bw_gbps"] == b and r["window_s"] == W)
    ax.plot([c for c, _ in pts], [h for _, h in pts], color=col, marker=mk, ms=5, lw=1.8, label=lab)
for x, lab in ((60, "60 GiB DRAM-only"), (180, "60 + 120 GiB CXL")): ax.axvline(x, color="#888888", ls=":", lw=0.9); ax.text(x + 3, 0.03, lab, fontsize=9, rotation=90, va="bottom", color="#444444")
ax.set_xlim(0, 375); ax.set_xticks([0, 60, 120, 180, 240, 300, 360]); ax.set_ylim(-0.03, 1.06); ax.set_xlabel("cache capacity C (GiB); dataset = 166 GiB"); ax.set_ylabel("hit rate, epochs 1–2")
ax.set_title("(a) hit rate vs capacity"); ax.legend(loc="center right", fontsize=9.5)
ax = axs[1]
for col, b, W, lab, mk, ms in [(C[7], "0.52", "0.0", "no prefetch (W = 0)", "o", 7), (C[2], "0.52", "50.0", "W = 50 s, B = 0.52 GB/s", "s", 5), (C[1], "0.2", "50.0", "W = 50 s, B = 0.20 GB/s", "^", 4)]:
    pts = sorted((fl(r, "cap_gib"), fl(r, "storage_GB")) for r in f4 if r["figure"] == "fig4a" and r["bw_gbps"] == b and r["window_s"] == W)
    ax.plot([c for c, _ in pts], [g for _, g in pts], color=col, marker=mk, ms=ms, lw=1.8, label=lab)
s60 = next(fl(r, "storage_GB") for r in f4 if r["figure"] == "fig4a" and r["window_s"] == "0.0" and r["cap_gib"] == "60.0"); tot = next(fl(r, "read_GB") for r in rows(os.path.join(E, "train", "sim", "none.csv")) if r["cap_gib"] == "60.0")
ax.annotate(f"60 GiB: {s60:.0f} GB ({s60 / tot:.0%} of all reads)", (60, s60), xytext=(110, 330), fontsize=10, arrowprops=dict(arrowstyle="->", color="#333333", lw=0.8))
ax.annotate("180 GiB: 0 GB", (180, 0), xytext=(200, 60), fontsize=10, arrowprops=dict(arrowstyle="->", color="#333333", lw=0.8))
ax.set_xlim(0, 375); ax.set_xticks([0, 60, 120, 180, 240, 300, 360]); ax.set_ylim(-10, 390); ax.set_xlabel("cache capacity C (GiB); dataset = 166 GiB"); ax.set_ylabel("GB read from storage, epochs 1–2")
ax.set_title("(b) storage reads: the same at every window and bandwidth"); ax.legend(loc="center right", fontsize=9.5)
save(fig, "f04_capacity", ["figs/fig3-train-capacity-by-window.csv", "figs/fig4-train-storage-traffic.csv", "train/sim/none.csv"],
     note="Trace-driven simulation on the real demand timeline (epochs 1–2 read 356 GB of files). The retention curve (W = 0) does not depend on the storage bandwidth.")

# ---------------------------------------------------------------- f05: inference: window-based eviction vs LRU (difference)
f5 = rows(os.path.join(F, "fig5-infer-window-retention-vs-lru.csv")); TR = {"conversation": "Mooncake conversation", "toolagent": "Mooncake tool agent"}
caps = ["30.0", "60.0", "120.0", "180.0", "359.9", "719.9"]
fig, axs = plt.subplots(1, 2, figsize=(12.3, 3.3), sharey=True)
for ax, tr in zip(axs, TR):
    for i, cap in enumerate(caps):
        for fam, ls, lw in (("wslru", "-", 1.6), ("wlfu", "--", 1.1)):
            pts = sorted((fl(r, "window_s"), fl(r, "delta_vs_lru")) for r in f5 if r["trace"] == tr and r["family"] == fam and r["cap_GiB"] == cap)
            if pts: ax.plot([w for w, _ in pts], [d for _, d in pts], color=C[i], ls=ls, lw=lw, marker="o", ms=4 if len(pts) > 1 else 7, label=f"{round(float(cap))} GiB" if fam == "wslru" else None)
    ax.axhline(0, color="k", lw=1.0); ax.set_xscale("log"); ax.set_xlim(8, 400); ax.set_xticks([10, 30, 50, 100, 200, 300]); ax.set_xticklabels(["10", "30", "50", "100", "200", "300"]); ax.minorticks_off()
    ax.set_ylim(-0.08, 0.06); ax.set_xlabel("historical window W (s)"); ax.set_title(TR[tr])
axs[0].set_ylabel("usable-prefix hit share − LRU")
h, l = axs[0].get_legend_handles_labels(); h += [Line2D([], [], color="k", ls="-"), Line2D([], [], color="k", ls="--")]; l += ["window-protected LRU (wslru:W)", "window-LFU eviction (wlfu:W)"]
axs[1].legend(h, l, loc="lower left", ncol=2, fontsize=9, title="capacity (720 GiB: W = 100 s only)", title_fontsize=9)
save(fig, "f05_retention", ["figs/fig5-infer-window-retention-vs-lru.csv (infer/*-replay.csv)"],
     note="Trace-driven replay of the Mooncake traces (kv_admission_sim.py); 8B blocks of 67.1 MB; second half scored. Both policies admit every block like LRU and differ only in the eviction order.")

# ---------------------------------------------------------------- f06: inference: admission policies vs capacity
T = rows(os.path.join(F, "table-infer-admission.csv"))
fig, axs = plt.subplots(1, 2, figsize=(12.3, 3.5))
for ax, tr in zip(axs, TR):
    G = sorted((fl(r, "cap_GiB"), r) for r in T if r["trace"] == tr)
    for key, lab, col, ls, mk in [("oracle", "oracle (Belady with bypass; uses the future, not implementable)", "black", "--", "x"), ("lru", "LRU (admit all)", C[7], "-", "o"), ("second_touch", "second touch", C[8], "-", "v"),
                                  ("second_touch_int", "2nd_int (second touch, gap ≤ residence)", C[1], "-", "^"), ("rq1_adaptive", "RQ1 adaptive (gap rule + regime switch)", C[3], "-", "D"), ("best_window_admission", "best fixed window admission (wslru2nd:W)", C[2], "-", "*")]:
        pts = [(c, fl(r, key)) for c, r in G if fl(r, key) is not None]
        ax.plot([c for c, _ in pts], [v for _, v in pts], color=col, ls=ls, marker=mk, ms=9 if mk == "*" else 5, lw=1.6, label=lab)
    for c, r in G: ax.annotate(f"{fl(r, 'best_window_s'):g} s", (c, fl(r, "best_window_admission")), xytext=(6, -12), textcoords="offset points", fontsize=8.5, color=C[2])
    ax.set_xscale("log", base=2); ax.set_xticks([30, 60, 120, 180, 360, 720]); ax.set_xticklabels(["30", "60", "120", "180", "360", "720"]); ax.minorticks_off()
    ax.set_xlabel("cache capacity (GiB of 8B blocks)"); ax.set_title(TR[tr])
axs[0].set_ylabel("usable-prefix hit share (scored half)"); axs[0].set_ylim(0.05, 1.03); axs[1].set_ylim(0.55, 1.03)
fig.legend(*axs[0].get_legend_handles_labels(), loc="upper center", ncol=3, fontsize=9.5, bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(rect=(0, 0.06, 1, 0.88)); fig.text(0.005, 0.008, "Trace-driven replay of the Mooncake traces; the oracle is an upper bound that uses the future. At 720 GiB only the 100-s window was run; second touch and 2nd_int were not run there.", fontsize=9.5, color="#555555", ha="left", va="bottom")
fig.savefig(os.path.join(OUT, "f06_admission.png"), dpi=200, bbox_inches="tight"); fig.savefig(os.path.join(OUT, "f06_admission.svg"), bbox_inches="tight"); plt.close(fig)
SOURCES["f06_admission"] = ["figs/table-infer-admission.csv (infer/*-replay.csv); best window per capacity annotated"]; print("wrote f06_admission")

with open(os.path.join(OUT, "SOURCES.md"), "w") as f:
    f.write("# Deck figures 2026-10-27 — sources (paths under experimental_results/2026-10-27-reuse-window-prefetch/)\n\n")
    for k, v in SOURCES.items(): f.write(f"- `{k}`: " + "; ".join(v) + "\n")
print("wrote SOURCES.md")
