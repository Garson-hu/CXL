#!/usr/bin/env python3
"""Report figures of the 2026-10-27 exploratory study (figure revision, branch explore/reuse-window-prefetch).
usage: window_report_figs.py <results dir>   ->  <results dir>/figs/fig*.{png,pdf} + the data table of every figure (csv) + table-infer-admission.{csv,md}

Training (train/sim/*.csv = trace-driven prefetch SIMULATION on the REAL CosmoFlow demand timeline; B = storage channel bandwidth, the
measured cold BeeGFS read bandwidths from c33 are 0.064 / 0.33 / 0.52 / 0.82 GB/s at 1 / 4 / 8 / 32 streams):
  fig1  hit rate vs future window W, one curve per capacity (30-360 GiB), at B = 0.52 GB/s and at B = 0.20 GB/s
  fig2  hit rate vs future window W, one curve per storage bandwidth, at C = 60 GiB (the DRAM-only cache)
  fig3  hit rate vs capacity, one curve per window (0 / 0.25 / 10 / 50 / 100 / 300 s), at B = 0.52 and 0.20 GB/s
  fig4  storage read traffic vs capacity (60 GiB DRAM-only vs 60 + 120 GiB CXL) and vs window
Inference (infer/*-replay.csv = KV admission replay of the Mooncake traces, kv_admission_sim.py):
  fig5  window-protected LRU / window-LFU eviction vs plain LRU per historical window (10-300 s) and capacity (30-720 GiB)
  fig6  window-based admission vs the RQ1 adaptive admission per window and capacity
  table-infer-admission: window admission / second touch / 2nd_int / RQ1 adaptive / LRU / oracle per trace and capacity
Every point is a simulator output; no fitted curve is drawn. The coarse and the fine-window sweeps of ONE configuration (same
simulator, bandwidth, availability, trainer speed) are merged into one curve; their overlapping points are checked to be identical."""
import collections, csv, math, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
D = sys.argv[1]; O = f"{D}/figs"; SIM = f"{D}/train/sim"; os.makedirs(O, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
                     "axes.grid": True, "grid.color": "#e4e4e4", "grid.linewidth": 0.6, "legend.frameon": False, "pdf.fonttype": 42})
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
def fl(r, k, d=0.0):
    try: return float(r.get(k) or d)
    except (ValueError, TypeError): return d
def save(fig, name):
    fig.savefig(f"{O}/{name}.png", dpi=300); fig.savefig(f"{O}/{name}.pdf"); plt.close(fig); print("wrote", name)
def wcsv(name, rows):
    cols = list(rows[0].keys())
    with open(f"{O}/{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
def footnote(fig, text, y=0.012): fig.text(0.01, y, text, fontsize=7.2, color="#333333", va="bottom", ha="left", wrap=True)

# ============================================================ training ============================================================
DEMAND = 0.217            # GB/s consumed by the trainer in epochs 1-2 (74.9 samples/s x 2.9 MB): the rate the storage must match without retention
SRC = {0.064: ["all-bw0.064.csv", "fine-bw0.064.csv"], 0.15: ["all-bw0.15.csv", "fine-bw0.15.csv"], 0.2: ["grid-bw0.2.csv", "all-bw0.2.csv"],
       0.25: ["all-bw0.25.csv", "fine-bw0.25.csv"], 0.33: ["all-bw0.33.csv", "fine-bw0.33.csv"], 0.52: ["grid-bw0.52.csv"], 0.82: ["all-bw0.82.csv", "fine-bw0.82.csv"]}
MEASURED = {0.064: "1 stream", 0.33: "4 streams", 0.52: "8 streams", 0.82: "32 streams"}      # measured cold BeeGFS reads from c33
def bwlabel(bw): return f"B = {bw:g} GB/s ({bw / DEMAND:.1f}× demand; " + (f"measured BeeGFS, {MEASURED[bw]})" if bw in MEASURED else "simulated)")
def merged(bw):
    """all (W, C) points of one configuration; overlapping points of the coarse and the fine sweep must be identical"""
    g = {}; dup = 0
    for fn in SRC[bw]:
        p = f"{SIM}/{fn}"
        if not os.path.exists(p): print("MISSING", fn); continue
        for r in csv.DictReader(open(p)):
            assert r["avail"] == "all" and float(r["speed"]) == 1.0 and abs(float(r["bw_gbps"]) - bw) < 1e-9 and r["pin"] == "1" and r["protect"] == "1", (fn, r["label"])
            r["_f"] = fn; k = (fl(r, "window_s"), fl(r, "cap_gib"))
            if k in g:
                dup += 1
                for col in ("hit_rate", "hits", "hit_retained", "hit_prefetched", "storage_GB", "prefetch_GB", "miss_late", "stall_s", "wasted_prefetches"):
                    assert abs(fl(g[k], col) - fl(r, col)) < 1e-9, ("MISMATCH", bw, k, col, g[k][col], r[col], g[k]["_f"], fn)
            else: g[k] = r
    return g, dup
T = {}
for bw in SRC:
    T[bw], dup = merged(bw); print(f"B = {bw}: {len(T[bw])} points, {dup} overlapping points verified identical")
none = {fl(r, "cap_gib"): r for r in csv.DictReader(open(f"{SIM}/none.csv"))}
for cap, r in none.items():                                                                     # W = 0 of the grids == the no-prefetch sweep
    for bw in (0.52, 0.2):
        if (0.0, cap) in T[bw]: assert abs(fl(T[bw][(0.0, cap)], "hit_rate") - fl(r, "hit_rate")) < 1e-9 and abs(fl(T[bw][(0.0, cap)], "storage_GB") - fl(r, "storage_GB")) < 1e-9
def series(G, cap): return sorted((W, r) for (W, c), r in G.items() if abs(c - cap) < 1e-9)
def sat_point(pts, tol=0.01):
    """saturation = the first window within tol of the curve's maximum; None when the curve never rises by more than tol"""
    hmax = max(h for _, h in pts)
    if hmax - pts[0][1] <= tol: return None
    return next(W for W, h in pts if h >= hmax - tol)
def wax(ax):
    ax.set_xscale("symlog", linthresh=0.1, linscale=0.45); ax.set_xlim(-0.012, 2600); ax.set_xticks([0, 0.1, 1, 10, 100, 1000]); ax.set_xticklabels(["0", "0.1", "1", "10", "100", "1000"]); ax.minorticks_off()
def capname(cap): return f"{cap:g} GiB" + (" (DRAM-only)" if cap == 60 else " (DRAM + CXL)" if cap == 180 else "")
def trow(fig, bw, r):
    acc = fl(r, "acc")
    return dict(figure=fig, bw_gbps=bw, avail=r["avail"], trainer_speed=r["speed"], cap_gib=r["cap_gib"], window_s=r["window_s"], hit_rate=r["hit_rate"],
                retention_hit_rate=round(fl(r, "hit_retained") / acc, 4), prefetch_hit_rate=round(fl(r, "hit_prefetched") / acc, 4), miss_cold=r["miss_cold"], miss_late=r["miss_late"],
                storage_GB=r["storage_GB"], prefetch_GB=r["prefetch_GB"], wasted_prefetches=r["wasted_prefetches"], stall_s=r["stall_s"], lead_p50_s=r["lead_p50_s"], source_csv=r["_f"])
def plateau_labels(ax, curves, x=1200):
    """one label per distinct plateau value: '60–360 GiB: 1.00'"""
    groups = collections.OrderedDict()
    for lab, col, pts in curves: groups.setdefault(round(pts[-1][1], 2), []).append((lab, col))
    for v, items in groups.items():
        txt = (items[0][0] if len(items) == 1 else f"{items[0][0]}–{items[-1][0]}") + f": {v:.2f}"
        ax.annotate(txt, (x, v), xytext=(5, 0), textcoords="offset points", fontsize=7.5, va="center", color=items[0][1] if len(items) == 1 else "#222222")
TRAIN_NOTE = ("Demand timeline = the REAL CosmoFlow run (A100 node c33, 3 epochs × 61,440 TFRecord files = 178 GB; epochs 1–2 at 74.9 samples/s = 0.217 GB/s). Cache and storage = trace-driven SIMULATION "
              "(train_prefetch_sim.py: one FIFO storage channel of bandwidth B, LRU cache with window protection, every epoch's order known at job start; the prefetcher fetches the samples due within the next W seconds). Hit rate = share of the 122,880 sample "
              "demands of epochs 1–2 (epoch 0 = cold start) served from the cache: RETAINED from the previous epoch, or PREFETCHED and complete before the consuming training step (a prefetch still "
              "in flight counts as a miss). Measured BeeGFS cold-read bandwidths from c33: 0.064 / 0.33 / 0.52 / 0.82 GB/s at 1 / 4 / 8 / 32 streams; 0.15 / 0.20 / 0.25 GB/s are simulated values.")

# ---------- fig1: hit rate vs window per capacity, two bandwidths ----------
CAPS1 = [30.0, 60.0, 120.0, 180.0, 360.0]; rows = []
fig, axs = plt.subplots(1, 2, figsize=(12.6, 6.3), sharey=True)
for ax, bw, sub in zip(axs, [0.52, 0.2], ["(a) B = 0.52 GB/s: measured BeeGFS, 8 streams = 2.4× the trainer's demand", "(b) B = 0.20 GB/s: simulated, 0.92× the trainer's demand"]):
    G = T[bw]; sats = []; curves = []
    for i, cap in enumerate(CAPS1):
        pts = [(W, fl(r, "hit_rate")) for W, r in series(G, cap)]; curves.append((f"{cap:g}", C[i], pts))
        ax.plot([W for W, _ in pts], [h for _, h in pts], color=C[i], marker="o", ms=3.2, lw=1.6, label=f"C = {capname(cap)}")
        ax.plot([0], [pts[0][1]], marker="o", ms=7.5, mfc="white", mec=C[i], ls="none", zorder=4)
        ws = sat_point(pts)
        if ws is not None: sats.append(ws); ax.plot([ws], [dict(pts)[ws]], marker="*", ms=12, color=C[i], mec="k", mew=0.4, ls="none", zorder=5)
        rows += [trow("fig1", bw, r) for _, r in series(G, cap)]
    if sats:
        wsat = max(sats); ax.axvspan(wsat, 2600, color="#f1f1f1", zorder=0)
        ax.text(wsat * 1.25, 0.40, f"saturated: every capacity within\n0.01 of its plateau for W ≥ {wsat:g} s", fontsize=8, va="center", color="#333333")
    plateau_labels(ax, curves); wax(ax); ax.set_ylim(-0.03, 1.06); ax.set_title(sub, fontsize=9.6)
    ax.set_xlabel("future window W (s); W = 0 = no prefetch")
axs[0].set_ylabel("cache hit rate, epochs 1–2 (retained + prefetched)")
h, l = axs[0].get_legend_handles_labels()
h += [Line2D([], [], marker="o", mfc="white", mec="k", ls="none", ms=7), Line2D([], [], marker="*", color="k", ls="none", ms=11), Patch(color="#f1f1f1")]
l += ["W = 0: retention hits only (no prefetch)", "saturation point: first W within 0.01 of the curve's maximum", "all capacities saturated"]
fig.legend(h, l, loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, 0.085))
fig.suptitle("Training: cache hit rate vs future window, per cache capacity (CosmoFlow, 178 GB dataset, 0.217 GB/s demand)", fontsize=11)
footnote(fig, TRAIN_NOTE); fig.tight_layout(rect=(0, 0.16, 1, 0.97)); save(fig, "fig1-train-window-by-capacity"); wcsv("fig1-train-window-by-capacity", rows)

# ---------- fig2: hit rate vs window per storage bandwidth at C = 60 GiB ----------
BWS = [0.064, 0.15, 0.2, 0.25, 0.33, 0.52, 0.82]; rows = []
fig, ax = plt.subplots(figsize=(9.2, 7.4)); curves = []; sats = {}
for i, bw in enumerate(BWS):
    pts = [(W, fl(r, "hit_rate")) for W, r in series(T[bw], 60.0)]; curves.append((f"{bw:g}", C[i], pts))
    ax.plot([W for W, _ in pts], [h for _, h in pts], color=C[i], marker="o", ms=3.2, lw=1.6, ls="-" if bw in MEASURED else "--", label=bwlabel(bw))
    ax.plot([0], [pts[0][1]], marker="o", ms=7.5, mfc="white", mec=C[i], ls="none", zorder=4)
    ws = sat_point(pts); sats[bw] = ws
    if ws is not None: ax.plot([ws], [dict(pts)[ws]], marker="*", ms=12, color=C[i], mec="k", mew=0.4, ls="none", zorder=5)
    rows += [trow("fig2", bw, r) for _, r in series(T[bw], 60.0)]
wax(ax); ax.set_ylim(-0.03, 1.06); ax.set_ylabel("cache hit rate, epochs 1–2 (retained + prefetched)"); ax.set_xlabel("future window W (s); W = 0 = no prefetch")
fast = [bw for bw in BWS if sats[bw] is not None and sats[bw] <= 0.25]; marg = [bw for bw in BWS if sats[bw] is not None and sats[bw] > 0.25]; flat = [bw for bw in BWS if sats[bw] is None]
ax.text(0.3, 0.80, f"B = {', '.join(f'{b:g}' for b in fast)} GB/s (the four curves coincide):\nsaturated from W = {max(sats[b] for b in fast):g} s, one file's fetch time", fontsize=8.2, color="#333333")
if marg: ax.text(50, 0.50, f"B = {', '.join(f'{b:g}' for b in marg)} GB/s: rises over 5–100 s,\nsaturated from W = {max(sats[b] for b in marg):g} s", fontsize=8.2, color="#333333", ha="left")
ax.text(3.0, 0.14, f"B = {', '.join(f'{b:g}' for b in flat)} GB/s (coincide): no window helps\n(storage slower than the demand; every prefetch is late)", fontsize=8.2, color="#333333")
ax.set_title("Training: hit rate vs future window at C = 60 GiB (DRAM-only), per storage bandwidth\n(solid = measured BeeGFS bandwidths, dashed = simulated values near the demand)", fontsize=10)
fig.legend(*ax.get_legend_handles_labels(), fontsize=7.8, loc="lower center", ncol=2, title="storage channel bandwidth B (demand ratio = B / 0.217 GB/s)", title_fontsize=8, bbox_to_anchor=(0.5, 0.11))
footnote(fig, TRAIN_NOTE + " After the 7.5% retention of a 60 GiB cache the storage must supply 0.20 GB/s."); fig.tight_layout(rect=(0, 0.25, 1, 1)); save(fig, "fig2-train-window-by-bandwidth"); wcsv("fig2-train-window-by-bandwidth", rows)

# ---------- fig3: hit rate vs capacity per window ----------
WINS3 = [0.0, 0.25, 10.0, 50.0, 100.0, 300.0]; MK = ["o", "s", "^", "v", "D", "P"]; rows = []
fig, axs = plt.subplots(1, 2, figsize=(12.6, 5.9), sharey=True)
for ax, bw, sub in zip(axs, [0.52, 0.2], ["(a) B = 0.52 GB/s: measured BeeGFS, 8 streams (2.4× demand)", "(b) B = 0.20 GB/s: simulated, 0.92× demand"]):
    G = T[bw]; caps = sorted({c for (_, c) in G if c < 1e9})
    for i, W in enumerate(WINS3):
        pts = [(c, fl(G[(W, c)], "hit_rate")) for c in caps if (W, c) in G]
        ax.plot([c for c, _ in pts], [h for _, h in pts], color=C[i], marker=MK[i], ms=4.5 if i else 5.5, lw=1.5 if i else 2.0, label=f"W = {W:g} s" + (" (no prefetch: retention only)" if W == 0 else ""), zorder=3 + (6 - i))
        rows += [trow("fig3", bw, G[(W, c)]) for c in caps if (W, c) in G]
    for x, lab in ((60, "60 GiB DRAM-only"), (180, "60 GiB DRAM + 120 GiB CXL")): ax.axvline(x, color="#888888", ls=":", lw=0.9); ax.text(x + 3, 0.02, lab, fontsize=7.5, rotation=90, va="bottom", ha="left", color="#444444")
    if bw == 0.52: ax.text(100, 0.93, "W ≥ 0.25 s: the five curves coincide at 1.00\nat every capacity from 15 GiB", fontsize=8.2, color="#333333", ha="left", va="top")
    else: ax.text(200, 0.52, "over retention (W = 0):\nW = 0.25 s: +0.03 … +0.12 at 15–60 GiB,\nup to +0.34 at 90–120 GiB\nW = 10 s: +0.10 … +0.49\nW = 100 s and 300 s coincide:\n1.00 from 45 GiB, 0.78 at 30 GiB", fontsize=8.2, color="#333333")
    ax.set_xlim(0, 375); ax.set_xticks([0, 30, 60, 90, 120, 150, 180, 240, 300, 360]); ax.set_ylim(-0.03, 1.06); ax.set_title(sub, fontsize=9.6)
    ax.set_xlabel("cache capacity C (GiB); dataset = 166 GiB (178 GB)")
axs[0].set_ylabel("cache hit rate, epochs 1–2 (retained + prefetched)"); axs[1].legend(fontsize=8, loc="lower right")
fig.suptitle("Training: cache hit rate vs capacity, per future window (CosmoFlow, 178 GB dataset, 0.217 GB/s demand)", fontsize=11)
footnote(fig, TRAIN_NOTE); fig.tight_layout(rect=(0, 0.12, 1, 0.97)); save(fig, "fig3-train-capacity-by-window"); wcsv("fig3-train-capacity-by-window", rows)

# ---------- fig4: storage read traffic vs capacity and vs window ----------
rows = []
fig, axs = plt.subplots(1, 2, figsize=(12.6, 5.6))
ax = axs[0]; G = T[0.52]; caps = sorted({c for (_, c) in G if c < 1e9}); TOTAL = fl(G[(0.0, 60.0)], "read_GB")
for i, (bw, W, lab, mk) in enumerate([(0.52, 0.0, "no prefetch (W = 0), any B", "o"), (0.52, 50.0, "prefetch W = 50 s, B = 0.52 GB/s", "s"), (0.2, 50.0, "prefetch W = 50 s, B = 0.20 GB/s", "^"), (0.52, 300.0, "prefetch W = 300 s, B = 0.52 GB/s", "v")]):
    pts = [(c, fl(T[bw][(W, c)], "storage_GB")) for c in caps if (W, c) in T[bw]]
    ax.plot([c for c, _ in pts], [g for _, g in pts], color=C[i], marker=mk, ms=5.5 - i * 0.6, lw=1.4, label=lab, zorder=6 - i)
    rows += [trow("fig4a", bw, T[bw][(W, c)]) for c in caps if (W, c) in T[bw]]
ax.axhline(TOTAL, color="#888888", ls="--", lw=0.9); ax.text(190, TOTAL + 6, f"all sample reads of epochs 1–2 = {TOTAL:.0f} GB (no cache)", fontsize=7.8, color="#444444")
s60 = fl(G[(0.0, 60.0)], "storage_GB"); s180 = fl(G[(0.0, 180.0)], "storage_GB")
ax.annotate(f"60 GiB DRAM-only: {s60:.0f} GB from storage\n= {s60 / 2:.0f} GB per epoch ({s60 / TOTAL:.0%} of the reads)", (60, s60), xytext=(120, 300), fontsize=8.2, arrowprops=dict(arrowstyle="->", color="#333333", lw=0.8), color="#111111")
ax.annotate(f"60 GiB DRAM + 120 GiB CXL: {s180:.0f} GB\n(the dataset stays resident after epoch 0)", (180, s180), xytext=(190, 110), fontsize=8.2, arrowprops=dict(arrowstyle="->", color="#333333", lw=0.8), color="#111111")
for x in (60, 180): ax.axvline(x, color="#888888", ls=":", lw=0.9)
ax.set_xlim(0, 375); ax.set_xticks([0, 30, 60, 90, 120, 150, 180, 240, 300, 360]); ax.set_ylim(-10, 395); ax.set_xlabel("cache capacity C (GiB); dataset = 166 GiB (178 GB)"); ax.set_ylabel("bytes read from storage in epochs 1–2 (GB)")
ax.set_title("(a) storage read traffic vs capacity (independent of B and W)", fontsize=9.6); ax.legend(fontsize=8, loc="center right")
ax = axs[1]
for i, (cap, bw, ls) in enumerate([(60.0, 0.52, "-"), (60.0, 0.2, "--"), (180.0, 0.52, "-"), (180.0, 0.2, "--")]):
    pts = [(W, fl(r, "storage_GB")) for W, r in series(T[bw], cap)]
    ax.plot([W for W, _ in pts], [g for _, g in pts], color=C[0 if cap == 60 else 2], ls=ls, marker="o", ms=3.2, lw=1.5, label=f"C = {capname(cap)}, B = {bw:g} GB/s")
    rows += [trow("fig4b", bw, r) for _, r in series(T[bw], cap)]
wax(ax); ax.set_ylim(-10, 395); ax.set_xlabel("future window W (s)"); ax.set_ylabel("bytes read from storage in epochs 1–2 (GB)")
ax.set_title("(b) storage read traffic vs window: W moves the reads earlier, it adds none", fontsize=9.6); ax.legend(fontsize=8, loc="center right")
ax.text(0.3, 300, f"60 GiB: {s60:.0f} GB at every W (0 wasted prefetches)", fontsize=8.2, color="#333333"); ax.text(0.3, 25, "180 GiB: 0 GB at every W", fontsize=8.2, color="#333333")
fig.suptitle("Training: storage read traffic vs cache capacity and future window (CosmoFlow, 178 GB dataset)", fontsize=11)
footnote(fig, "Storage read traffic = bytes fetched from storage (demand fetches + prefetches) during epochs 1–2 of the REAL CosmoFlow demand timeline in the trace-driven SIMULATION; epoch 0 (cold start) is not counted. "
              "The cache is LRU with window protection; prefetched data is pinned until its use. 1 GB = 10⁹ bytes; the 61,440-file dataset is 178 GB (166 GiB); epochs 1–2 read every file once = 356 GB.")
fig.tight_layout(rect=(0, 0.09, 1, 0.96)); save(fig, "fig4-train-storage-traffic"); wcsv("fig4-train-storage-traffic", rows)

# ============================================================ inference ============================================================
import glob
I = []
for f in sorted(glob.glob(f"{D}/infer/*-replay.csv")):
    tr = os.path.basename(f).split("-cap")[0]
    for r in csv.DictReader(open(f)): r["trace"] = tr; I.append(r)
TR = {"conversation": "Mooncake conversation", "toolagent": "Mooncake tool agent"}; traces = [t for t in TR if any(r["trace"] == t for r in I)]
capsI = sorted({fl(r, "cap_GiB") for r in I}); G = {(r["trace"], fl(r, "cap_GiB"), r["policy"]): r for r in I}
def nom(cap): return f"{round(cap):g} GiB"
def ush(tr, cap, p): return fl(G[(tr, cap, p)], "usable_hit_share") if (tr, cap, p) in G else None
def fam_pts(tr, cap, fam): return sorted((float(p.split(":")[1]), fl(r, "usable_hit_share")) for (t, c, p), r in G.items() if t == tr and c == cap and p.startswith(fam + ":"))
INF_NOTE = ("KV-cache admission replay (kv_admission_sim.py) of the Mooncake conversation and tool-agent traces; one host cache of 8B blocks (67.1 MB); the first half of each trace warms the cache, the second half "
            "is scored. Usable-prefix hit share = share of the scored block lookups with a reuse that hit AND whose whole preceding prefix in the request also hit (a hit the engine can use). "
            "wslru:W = LRU with a protected segment for blocks with ≥ 2 accesses inside the last W s (protection expires after W s idle); wlfu:W = among the K least recently used blocks evict the one with the fewest accesses in "
            "the last W s; both admit every block (like LRU). Historical windows only; no future information is used online.")
# ---------- fig5: window-based retention vs LRU ----------
FAM5 = [("wslru", "window-protected LRU (wslru:W)"), ("wlfu", "window-LFU eviction (wlfu:W)")]; rows = []
fig, axs = plt.subplots(2, 4, figsize=(16, 8.0))
k = 0
for tr in traces:
    for fam, flab in FAM5:
        ax, axd = axs[0][k], axs[1][k]
        for i, cap in enumerate(capsI):
            pts = fam_pts(tr, cap, fam); lru = ush(tr, cap, "lru")
            if not pts or lru is None: continue
            ax.plot([W for W, _ in pts], [h for _, h in pts], color=C[i], marker="o", ms=4 if len(pts) > 1 else 7, lw=1.5, label=nom(cap))
            ax.axhline(lru, color=C[i], ls="--", lw=0.9)
            axd.plot([W for W, _ in pts], [h - lru for _, h in pts], color=C[i], marker="o", ms=4 if len(pts) > 1 else 7, lw=1.5)
            rows += [dict(figure="fig5", trace=tr, family=fam, cap_GiB=cap, window_s=W, usable_hit_share=h, lru_usable_hit_share=lru, delta_vs_lru=round(h - lru, 4),
                          slru_usable_hit_share=ush(tr, cap, "slru"), written_TB=fl(G[(tr, cap, f"{fam}:{W:g}")], "written_TB"), lru_written_TB=fl(G[(tr, cap, "lru")], "written_TB")) for W, h in pts]
        axd.axhline(0, color="k", lw=0.9); axd.set_ylim(-0.06, 0.06)
        for a in (ax, axd): a.set_xscale("log"); a.set_xlim(8, 400); a.set_xticks([10, 30, 50, 100, 200, 300]); a.set_xticklabels(["10", "30", "50", "100", "200", "300"]); a.minorticks_off()
        vals = [fl(r, "usable_hit_share") for r in I if r["trace"] == tr and (r["policy"] == "lru" or r["policy"].startswith(fam + ":"))]
        ax.set_title(f"{TR[tr]}: {flab}", fontsize=9.3); ax.set_ylim(min(vals) - 0.03, max(vals) + 0.04); axd.set_xlabel("historical window W (s)")
        if k == 0: ax.set_ylabel("usable-prefix hit share (scored half)"); axd.set_ylabel("difference to LRU at the same capacity")
        k += 1
fig.legend(*axs[0][0].get_legend_handles_labels(), loc="upper center", ncol=6, fontsize=8.5, title="cache capacity — solid = window policy (admit all, window-based eviction), dashed = plain LRU at the same capacity; 720 GiB: one window (100 s) only", title_fontsize=8.5, bbox_to_anchor=(0.5, 0.955))
fig.suptitle("Inference: a historical window used for RETENTION (eviction order) vs plain LRU, per window and capacity — both traces", fontsize=11)
footnote(fig, INF_NOTE); fig.tight_layout(rect=(0, 0.075, 1, 0.9)); save(fig, "fig5-infer-window-retention-vs-lru"); wcsv("fig5-infer-window-retention-vs-lru", rows)

# ---------- fig6: window admission vs the RQ1 adaptive admission ----------
rows = []
fig, axs = plt.subplots(2, 2, figsize=(12.6, 8.0))
for k, tr in enumerate(traces):
    ax, axd = axs[0][k], axs[1][k]
    for i, cap in enumerate(capsI):
        pts = fam_pts(tr, cap, "wslru2nd"); ad = ush(tr, cap, "2nd_int_auto")
        if not pts or ad is None: continue
        ax.plot([W for W, _ in pts], [h for _, h in pts], color=C[i], marker="o", ms=4 if len(pts) > 1 else 7, lw=1.5, label=nom(cap))
        ax.axhline(ad, color=C[i], ls="--", lw=0.9)
        axd.plot([W for W, _ in pts], [h - ad for _, h in pts], color=C[i], marker="o", ms=4 if len(pts) > 1 else 7, lw=1.5)
        best = max(pts, key=lambda x: x[1]); ax.plot([best[0]], [best[1]], marker="*", ms=12, color=C[i], mec="k", mew=0.4, ls="none", zorder=5)
        rows += [dict(figure="fig6", trace=tr, cap_GiB=cap, window_s=W, window_admission_usable=h, rq1_adaptive_usable=ad, delta_vs_rq1=round(h - ad, 4), lru_usable=ush(tr, cap, "lru"),
                      second_touch_usable=ush(tr, cap, "2nd"), second_touch_int_usable=ush(tr, cap, "2nd_int"), oracle_usable=ush(tr, cap, "oracle"),
                      window_admission_written_TB=fl(G[(tr, cap, f"wslru2nd:{W:g}")], "written_TB"), rq1_adaptive_written_TB=fl(G[(tr, cap, "2nd_int_auto")], "written_TB"), lru_written_TB=fl(G[(tr, cap, "lru")], "written_TB")) for W, h in pts]
    axd.axhline(0, color="k", lw=0.9); axd.set_ylim(-0.38, 0.04)
    for a in (ax, axd): a.set_xscale("log"); a.set_xlim(8, 400); a.set_xticks([10, 30, 50, 100, 200, 300]); a.set_xticklabels(["10", "30", "50", "100", "200", "300"]); a.minorticks_off()
    ax.set_title(f"{TR[tr]}", fontsize=10); ax.set_ylim(0.05, 0.9); axd.set_xlabel("admission window W (s)")
    if k == 0: ax.set_ylabel("usable-prefix hit share (scored half)"); axd.set_ylabel("window admission − RQ1 adaptive")
fig.legend(*axs[0][0].get_legend_handles_labels(), loc="upper center", ncol=6, fontsize=8.5, title="cache capacity — solid = window admission wslru2nd:W (★ = its best window), dashed = the RQ1 adaptive admission at the same capacity; 720 GiB: one window (100 s) only", title_fontsize=8.5, bbox_to_anchor=(0.5, 0.955))
fig.suptitle("Inference: a historical window used for ADMISSION vs the RQ1 adaptive admission rule, per window and capacity", fontsize=11)
footnote(fig, INF_NOTE.split(" wslru:W")[0] + " wslru2nd:W = admit a block only if it was looked up within the last W s (the first block of a request is always admitted), with the wslru:W protection; "
              "RQ1 adaptive = 2nd_int_auto: admit on a second touch whose re-lookup gap ≤ the online residence estimate, SLRU structure, automatic switch to first-touch admission when the admit-all residence ≥ the median first-touch re-lookup gap.")
fig.tight_layout(rect=(0, 0.075, 1, 0.9)); save(fig, "fig6-infer-window-admission-vs-rq1"); wcsv("fig6-infer-window-admission-vs-rq1", rows)

# ---------- table: admission policies ----------
trs = []; md = ["| trace | capacity (GiB) | LRU (admit all) | second touch (2nd) | 2nd_int (gap ≤ residence) | RQ1 adaptive (2nd_int_auto) | best window admission wslru2nd:W (W) | oracle | writes TB: LRU / RQ1 adaptive / best window |", "|---|---|---|---|---|---|---|---|---|"]
for tr in traces:
    for cap in capsI:
        pts = fam_pts(tr, cap, "wslru2nd")
        if not pts: continue
        bw_, bh = max(pts, key=lambda x: x[1]); f3 = lambda v: "–" if v is None else f"{v:.3f}"
        row = dict(trace=tr, cap_GiB=cap, lru=ush(tr, cap, "lru"), slru=ush(tr, cap, "slru"), second_touch=ush(tr, cap, "2nd"), second_touch_int=ush(tr, cap, "2nd_int"), rq1_adaptive=ush(tr, cap, "2nd_int_auto"),
                   best_window_admission=bh, best_window_s=bw_, window_admission_minus_rq1=round(bh - ush(tr, cap, "2nd_int_auto"), 4), oracle=ush(tr, cap, "oracle"),
                   lru_written_TB=fl(G[(tr, cap, "lru")], "written_TB"), rq1_written_TB=fl(G[(tr, cap, "2nd_int_auto")], "written_TB"), best_window_written_TB=fl(G[(tr, cap, f"wslru2nd:{bw_:g}")], "written_TB"))
        trs.append(row)
        md.append(f"| {TR[tr]} | {round(cap):g} | {f3(row['lru'])} | {f3(row['second_touch'])} | {f3(row['second_touch_int'])} | {f3(row['rq1_adaptive'])} | {bh:.3f} ({bw_:g} s) | {f3(row['oracle'])} | {row['lru_written_TB']:.2f} / {row['rq1_written_TB']:.2f} / {row['best_window_written_TB']:.2f} |")
wcsv("table-infer-admission", trs); open(f"{O}/table-infer-admission.md", "w").write("\n".join(md) + "\n"); print("wrote table-infer-admission")
