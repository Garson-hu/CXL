#!/usr/bin/env python3
"""Figures for the group-meeting deck of 2026-10-07, drawn with matplotlib from the raw results in the repository.
Every label is written in plain English (no internal names). Output: <script dir>/deck_2026-10-07_figs/*.png
or the directory given as the first argument."""
import collections, csv, os, re, statistics as st, sys
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

R = "/home/ghu4/CXL/experimental_results"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "deck_2026-10-07_figs")
os.makedirs(OUT, exist_ok=True)
# matplotlib's default colour cycle: C0 blue, C1 orange, C2 green, C3 red, C4 purple, C7 gray; default white background
DRAM, CXL, GRAY, OURS, INK, INK2 = "C1", "C0", "C7", "C2", "k", "0.35"
plt.rcParams.update({"font.size": 12, "axes.titlesize": 12})
def despine(ax, grid="y"):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    if grid: ax.grid(axis=grid, alpha=0.3); ax.set_axisbelow(True)
def save(fig, name): fig.tight_layout(pad=0.6); fig.savefig(f"{OUT}/{name}.png", dpi=200); plt.close(fig); print("wrote", name)
def label_bars(ax, bars, fmt, dy, size=11, bold=False):
    for b in bars: ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy, fmt(b.get_height()), ha="center", fontsize=size, fontweight="bold" if bold else "normal")

# ---------------- 1. the problem: a DRAM reader next to programs that write DRAM (2026-09-08, healthy socket) ----------------
nt = [(0, 96.4), (54.1, 87.6), (79.3, 75.9), (138, 78.8), (273, 8.0), (294, 8.9)]
fig, ax = plt.subplots(figsize=(8.6, 4.4))
ax.plot([x for x, _ in nt], [y for _, y in nt], "-o", color=DRAM, lw=2.4, ms=7)
ax.annotate("12 times slower:\n96 GiB/s drops to 8 GiB/s", (273, 8), (150, 30), fontsize=11, arrowprops=dict(arrowstyle="->", color=INK))
ax.set_xlabel("how fast other programs write into DRAM, GiB/s"); ax.set_ylabel("how fast a program can read DRAM, GiB/s")
ax.set_ylim(0, 105); ax.set_xlim(-5, 310); despine(ax)
save(fig, "01-cliff")

# ---------------- 2. the idea: the same copy into DRAM vs into CXL, a DRAM reader next to it (2026-10-07, measured) -------------
rc = open(f"{R}/2026-10-07-read-cost/readcost.txt").read()
def burst(read_from, copy_into, field):
    xs = re.findall(rf"read_from={read_from} copy_into={copy_into} reader4_GiBs=([\d.]+) chain_ns=([\d.]+) writers_GiBs=([\d.]+)", rc)
    return st.median(float(x[{"bw": 0, "lat": 1, "wr": 2}[field]]) for x in xs)
fig, ax = plt.subplots(figsize=(8.6, 4.4))
vals = [burst("dram", "none", "bw"), burst("dram", "dram", "bw"), burst("dram", "cxl", "bw")]
labs = ["alone", "while a checkpoint copy\nwrites into DRAM", "while the same copy\nwrites into CXL instead"]
bars = ax.bar(range(3), vals, color=[GRAY, DRAM, CXL], width=0.6)
label_bars(ax, bars, lambda v: f"{v:.0f} GiB/s", 3, 12, True)
ax.set_xticks(range(3)); ax.set_xticklabels(labs); ax.set_ylabel("how fast a program reads DRAM, GiB/s"); ax.set_ylim(0, 190); despine(ax)
save(fig, "02-redirect")

# ---------------- 3. most of the saved attention state is never used again (2026-09-09 trace analysis) ----------------------
tr = ["chat service", "agent service", "synthetic workload"]; never = [76, 78, 58]
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.bar(range(3), never, color=CXL, width=0.55, label="never used again"); ax.bar(range(3), [100 - n for n in never], bottom=never, color=DRAM, width=0.55, label="used again later")
for i, n in enumerate(never):
    ax.text(i, n / 2, f"{n}%\nnever used\nagain", ha="center", va="center", fontsize=12, color="white", fontweight="bold")
    ax.text(i, n + (100 - n) / 2, f"{100 - n}%", ha="center", va="center", fontsize=11, color="white")
ax.set_xticks(range(3)); ax.set_xticklabels(tr); ax.set_ylabel("share of saved blocks, %"); ax.set_ylim(0, 100); despine(ax)
save(fig, "03-never-used")

# ---------------- 4. main result next to a neighbour that leaves DRAM bandwidth free (real-data re-run, 3 repetitions) ----------
rows = collections.defaultdict(list)
for r in csv.DictReader(open(f"{R}/2026-09-22-three-policies-realdata/summary.csv")): rows[r["tag"].rsplit("-rep", 1)[0]].append(r)
def med(base, k): return st.median(float(r[k]) for r in rows[base])
SER = [("copy into DRAM (today)", DRAM, "o"), ("copy into CXL only", CXL, "o"), ("copy into DRAM, slowed down", GRAY, "^"), ("our system", OURS, "*")]
panels = [("Neighbour: a program streaming through DRAM\n(8 threads); the copy is 64 GiB", ["reader-dram", "reader-cxl", "reader-dram-limited-r20", "reader-cxlpath-b1.09"]),
          ("Neighbour: PageRank on a large graph\n(32 threads); the copy is 192 GiB", ["pr32-dram-s192", "pr32-cxl-s192", "pr32-dram-limited-r20-s192", "pr32-cxlpath-b1.05-s192"])]
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
for ax, (title, bases) in zip(axes, panels):
    for (label, color, marker), b in zip(SER, bases):
        x, y = med(b, "completion_s"), med(b, "slowdown_pct")
        ax.scatter([x], [y], s=(380 if marker == "*" else 170), color=color, marker=marker, edgecolor="k", linewidth=0.6, label=label, zorder=3)
        ax.annotate(f"{x:.1f} s, " + ("not slower" if y < 0.5 else f"{y:.0f}% slower"), (x, y), textcoords="offset points", xytext=(10, 6), fontsize=10, color=color)
    ax.axhline(7, ls=":", color=INK2, lw=1); ax.text(0.15, 8.2, "7% limit", fontsize=10, color=INK2)
    ax.set_xlim(left=0); ax.set_title(title, fontsize=11); ax.set_xlabel("time to finish the copy, seconds"); despine(ax, "both")
axes[0].set_ylabel("how much slower the neighbour runs\nduring the copy, %"); axes[0].legend(fontsize=10, loc="upper right")
axes[0].set_xlim(0, 3.8); axes[1].set_xlim(0, 11)
save(fig, "04-main-free")

# ---------------- 5. next to a neighbour that already uses all of DRAM's bandwidth ---------------------------------------------
groups = [("training step\n(1.5 billion parameters)", "opt-dram", "opt-cxl", "opt-cxlpath-b1.04"),
          ("llama.cpp generating text", "llama-dram", "llama-cxl", "llama-cxlpath-b1.06"),
          ("PageRank\n(80 threads)", "pr-dram-s192", "pr-cxl-s192", "pr-cxlpath-b1.055-s192")]
fig, ax = plt.subplots(figsize=(10, 4.6)); w = 0.26
for j, (label, color) in enumerate([("copy into DRAM (today)", DRAM), ("copy into CXL only", CXL), ("our system", OURS)]):
    xs = [i + (j - 1) * w for i in range(3)]; ys = [med(g[1 + j], "slowdown_pct") for g in groups]; ts = [med(g[1 + j], "completion_s") for g in groups]
    bars = ax.bar(xs, ys, w, color=color, label=label)
    for b, y, t in zip(bars, ys, ts): ax.text(b.get_x() + w / 2, y + 0.8, f"{y:.0f}%\n{t:.1f} s", ha="center", fontsize=9.5)
ax.set_xticks(range(3)); ax.set_xticklabels([g[0] for g in groups]); ax.set_ylabel("how much slower the neighbour runs, %"); ax.set_ylim(0, 40)
ax.legend(fontsize=10, loc="upper left"); despine(ax)
save(fig, "05-main-busy")

# ---------------- 6. a fixed split between DRAM and CXL vs our system (2026-10-06) -------------------------------------------------
sp = collections.defaultdict(list)
for r in csv.DictReader(open(f"{R}/2026-10-06-fixed-split-baseline/summary.csv")): sp[r["tag"].rsplit("-rep", 1)[0]].append(r)
def smed(base, k): return st.median(float(r[k]) for r in sp[base])
G = [("streaming reader", "reader-split-d4", "reader-split-d8", "reader-cxlpath-b1.09"), ("PageRank, 32 threads", "pr32-split-d4-s192", "pr32-split-d8-s192", "pr32-cxlpath-b1.05-s192"),
     ("training step", "opt-split-d4", "opt-split-d8", "opt-cxlpath-b1.04"), ("llama.cpp", "llama-split-d4", "llama-split-d8", "llama-cxlpath-b1.06")]
fig, ax = plt.subplots(figsize=(11, 4.6))
for j, (label, color) in enumerate([("always send a quarter to DRAM", "C4"), ("always send half to DRAM", "C3"), ("our system decides", OURS)]):
    xs = [i + (j - 1) * w for i in range(4)]
    ys = [(smed(g[1 + j], "slowdown_pct") if j < 2 else med(g[3], "slowdown_pct")) for g in G]; ts = [(smed(g[1 + j], "completion_s") if j < 2 else med(g[3], "completion_s")) for g in G]
    bars = ax.bar(xs, ys, w, color=color, label=label)
    for b, y, t in zip(bars, ys, ts): ax.text(b.get_x() + w / 2, y + 0.6, f"{y:.0f}%\n{t:.1f} s", ha="center", fontsize=9)
ax.set_xticks(range(4)); ax.set_xticklabels([g[0] for g in G]); ax.set_ylabel("how much slower the neighbour runs, %"); ax.set_ylim(0, 28)
ax.legend(fontsize=10, loc="upper left"); despine(ax)
save(fig, "06-fixed-split")

# ---------------- 7. real PyTorch checkpoint next to a training step (2026-09-22) ---------------------------------------------------
d = f"{R}/2026-09-22-moderate-pacing-dcp"; fig, ax = plt.subplots(figsize=(12.5, 4.2))
for tag, label, color in [("opt-dcp-dram-s16-rep2", "PyTorch today: the checkpoint is copied into DRAM", DRAM), ("opt-dcp-cxlpath-s16-rep2", "PyTorch with our system: the checkpoint is copied into CXL", CXL)]:
    pt = open(f"{d}/{tag}-producer.txt").read(); wins = [(int(m[1]), int(m[2])) for m in re.findall(r"COPY (\d+) START (\d+) END (\d+)", pt)]; s0, s1 = wins[3]
    pers = [(int(m[1]), int(m[2])) for m in re.findall(r"PERSIST (\d+) START (\d+) END (\d+)", pt)]
    steps = [(int(m[1]), float(m[0])) for m in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", open(f"{d}/{tag}-victim.txt").read())]
    base = st.median(v for t, v in steps if wins[0][0] - 15e9 <= t < wins[0][0] - 0.5e9)
    xs = [(t - s0) / 1e9 for t, v in steps if s0 - 3e9 <= t <= s0 + 10e9]; ys = [100 * (v / base - 1) for t, v in steps if s0 - 3e9 <= t <= s0 + 10e9]
    ax.plot(xs, ys, color=color, lw=2, label=f"{label}\n      training is paused {(s1 - s0) / 1e9:.1f} s; the checkpoint is safe on disk after {(pers[3][1] - s0) / 1e9:.0f} s")
    ax.axvspan(0, (s1 - s0) / 1e9, color=color, alpha=0.09)
ax.axhline(0, color="k", lw=0.8); ax.set_xlabel("seconds since the checkpoint started"); ax.set_ylabel("how much slower the neighbouring\ntraining step runs, %")
ax.set_ylim(-1, 15); despine(ax); ax.legend(loc="upper right", fontsize=10)
save(fig, "07-pytorch")

# ---------------- 8. a language model next to the copy: time per token (real-data re-run) --------------------------------------------
d = f"{R}/2026-09-22-three-policies-realdata"; fig, ax = plt.subplots(figsize=(12, 4.0))
for tag, label, color in [("llama-dram-rep1", "checkpoint copied into DRAM (today)", DRAM), ("llama-cxlpath-b1.06-rep1", "checkpoint copied into CXL (our system)", CXL)]:
    pt = open(f"{d}/{tag}-producer.txt").read(); wins = [(int(m[1]), int(m[2])) for m in re.findall(r"COPY (\d+) START (\d+) END (\d+)", pt)]; s0, s1 = wins[3]
    toks = [int(m) for m in re.findall(r"^TOK (\d+)", open(f"{d}/{tag}-victim.txt").read(), flags=re.M)]
    pts = [((toks[i] - s0) / 1e9, (toks[i] - toks[i - 1]) / 1e6) for i in range(1, len(toks)) if s0 - 2e9 <= toks[i] <= s0 + 4e9]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=1.8, label=f"{label}: the copy takes {(s1 - s0) / 1e9:.1f} s"); ax.axvspan(0, (s1 - s0) / 1e9, color=color, alpha=0.08)
ax.set_xlabel("seconds since the 64 GiB copy started"); ax.set_ylabel("time to generate one token,\nmilliseconds"); ax.set_ylim(25, 55); despine(ax); ax.legend(loc="upper right", fontsize=10)
save(fig, "08-tokens")

# ---------------- 9. how often a job can save a checkpoint for a given cost ---------------------------------------------------------
cfg = {"PyTorch today": (dict(stall=1.60, persist=31.0, tail=[(7.0, 0.015), (24.0, 0.004)]), DRAM), "PyTorch with our system": (dict(stall=0.81, persist=19.0, tail=[]), CXL)}
def overhead(c, T):
    if T < c["stall"] + c["persist"]: return None
    return 100 * (c["stall"] + sum(min(dd, T) * s for dd, s in c["tail"])) / T
fig, ax = plt.subplots(figsize=(8.6, 4.4)); Ts = list(range(10, 361, 1))
for name, (c, color) in cfg.items():
    ys = [overhead(c, t) for t in Ts]; ax.plot([t for t, y in zip(Ts, ys) if y is not None], [y for y in ys if y is not None], color=color, lw=2.4, label=name)
ax.axhline(3, color=INK2, ls=":", lw=1.2); ax.text(355, 3.25, "3% of training time", ha="right", fontsize=10, color=INK2)
ax.annotate("today: at most once\nevery 60 seconds", (60, 3.0), (110, 6), fontsize=10, color=DRAM, arrowprops=dict(arrowstyle="->", color=DRAM))
ax.annotate("our system: once\nevery 27 seconds", (27, 3.0), (40, 7.3), fontsize=10, color=CXL, arrowprops=dict(arrowstyle="->", color=CXL))
ax.set_xlabel("seconds between two checkpoints (16 GiB state)"); ax.set_ylabel("training time lost to checkpoints, %"); ax.set_ylim(0, 9); despine(ax); ax.legend(fontsize=10, loc="upper right")
save(fig, "09-frequency")

# ---------------- 10. the lending control loop in action (real-data re-run, streaming reader) ------------------------------------
f = f"{R}/2026-09-22-three-policies-realdata/reader-cxlpath-b1.09-rep1-daemon.csv"; hdr = open(f).readline(); idle = float(hdr.split("idle_ns=")[1].split()[0]); bound = float(hdr.split("bound=")[1].split()[0])
log = [r for r in csv.DictReader(l for l in open(f) if not l.startswith("#"))]
t = [float(r["t_ms"]) / 1000 for r in log]; m5 = [float(r["mean5_ns"]) for r in log]; sp16 = [int(r["spill16"]) / 16 * 100 for r in log]; cg = [float(r["cxl_GiBs"]) for r in log]; dg = [float(r["dram_GiBs"]) for r in log]
sel = [i for i, x in enumerate(t) if 29 <= x <= 59]
fig, (a, b, c) = plt.subplots(3, 1, figsize=(12.5, 6.0), sharex=True)
a.plot([t[i] for i in sel], [m5[i] for i in sel], color=INK, lw=1.3, label="time of one DRAM read, measured every 10 ms")
a.axhline(idle, color=GRAY, ls="--", lw=1, label=f"normal: {idle:.0f} ns"); a.axhline(bound * idle, color=DRAM, ls=":", lw=1.5, label=f"limit: {bound * idle:.0f} ns")
a.set_ylabel("nanoseconds"); a.set_ylim(120, 175); a.legend(fontsize=9.5, loc="upper right", ncol=3); despine(a)
b.step([t[i] for i in sel], [sp16[i] for i in sel], color=INK, lw=1.5, where="post"); b.set_ylabel("share of new data\nsent to DRAM, %"); b.set_ylim(0, 60); despine(b)
c.stackplot([t[i] for i in sel], [cg[i] for i in sel], [dg[i] for i in sel], colors=[CXL, DRAM], labels=["written into CXL", "written into DRAM (lent)"])
c.set_ylabel("GiB/s"); c.set_xlabel("seconds (two 64 GiB copies, 25 seconds apart, next to the streaming reader)"); c.legend(fontsize=9.5, loc="upper right", ncol=2); c.set_ylim(0, 75); despine(c)
save(fig, "10-lending")

# ---------------- 11. how much slower is a read from CXL (2026-10-07) --------------------------------------------------------------
lat_d = st.median(float(x) for x in re.findall(r"LAT rep=\d+ dram_ns=([\d.]+)", rc)); lat_c = st.median(float(x) for x in re.findall(r"LAT rep=\d+ dram_ns=[\d.]+ cxl_ns=([\d.]+)", rc))
th = [1, 2, 4, 8, 16]
bwd = [st.median(float(x) for x in re.findall(rf"BW rep=\d+ threads={T} dram_GiBs=([\d.]+)", rc)) for T in th]
bwc = [st.median(float(x) for x in re.findall(rf"BW rep=\d+ threads={T} dram_GiBs=[\d.]+ cxl_GiBs=([\d.]+)", rc)) for T in th]
gr = open(f"{R}/2026-10-07-read-cost/gpuread.txt").read(); gd = st.median(float(x) for x in re.findall(r"from_dram_GiBs=([\d.]+)", gr)); gc = st.median(float(x) for x in re.findall(r"from_cxl_GiBs=([\d.]+)", gr))
fig, (a, b, c) = plt.subplots(1, 3, figsize=(13.5, 4.4), gridspec_kw=dict(width_ratios=[0.8, 1.4, 0.8]))
bars = a.bar([0, 1], [lat_d, lat_c], color=[DRAM, CXL], width=0.6); label_bars(a, bars, lambda v: f"{v:.0f} ns", 4, 12, True)
a.set_xticks([0, 1]); a.set_xticklabels(["DRAM", "CXL"]); a.set_ylabel("nanoseconds"); a.set_ylim(0, 270); a.set_title("One read that waits\nfor the previous one", fontsize=11); despine(a)
b.plot(th, bwd, "-o", color=DRAM, lw=2.2, label="from DRAM"); b.plot(th, bwc, "-o", color=CXL, lw=2.2, label="from CXL")
for T, y in zip(th, bwd): b.text(T, y + 9, f"{y:.0f}", ha="center", fontsize=10, color=DRAM)
for T, y in zip(th, bwc): b.text(T, y - 22, f"{y:.0f}", ha="center", fontsize=10, color=CXL)
b.set_xscale("log", base=2); b.set_xticks(th); b.set_xticklabels([str(x) for x in th]); b.set_xlabel("processor threads reading at once"); b.set_ylabel("GiB/s"); b.set_ylim(0, 310)
b.set_title("Processor reading large blocks", fontsize=11); b.legend(fontsize=10, loc="upper left"); despine(b)
bars = c.bar([0, 1], [gd, gc], color=[DRAM, CXL], width=0.6); label_bars(c, bars, lambda v: f"{v:.1f}", 0.3, 12, True)
c.set_xticks([0, 1]); c.set_xticklabels(["DRAM", "CXL"]); c.set_ylabel("GiB/s"); c.set_ylim(0, 16); c.set_title("GPU reading 1 GiB", fontsize=11); despine(c)
save(fig, "11-read-cost")

# ---------------- 12. reading while a checkpoint copy runs (2026-10-07) --------------------------------------------------------------
fig, (a, b) = plt.subplots(1, 2, figsize=(13, 4.6))
cases = [("dram", "none", "reads DRAM,\nno copy", GRAY), ("dram", "dram", "reads DRAM,\ncopy into DRAM", DRAM), ("dram", "cxl", "reads DRAM,\ncopy into CXL", CXL),
         ("cxl", "none", "reads CXL,\nno copy", GRAY), ("cxl", "cxl", "reads CXL,\ncopy into CXL", CXL)]
xs = [0, 1, 2, 3.5, 4.5]
bars = a.bar(xs, [burst(r, w, "bw") for r, w, _, _ in cases], color=[c4 for *_, c4 in cases], width=0.7); label_bars(a, bars, lambda v: f"{v:.0f}", 3, 11, True)
a.set_xticks(xs); a.set_xticklabels([l for _, _, l, _ in cases], fontsize=9.5); a.set_ylabel("GiB/s (4 reading threads)"); a.set_ylim(0, 190); a.set_title("How much can be read per second", fontsize=11); despine(a)
bars = b.bar(xs, [burst(r, w, "lat") for r, w, _, _ in cases], color=[c4 for *_, c4 in cases], width=0.7); label_bars(b, bars, lambda v: f"{v:.0f} ns", 8, 11, True)
b.set_xticks(xs); b.set_xticklabels([l for _, _, l, _ in cases], fontsize=9.5); b.set_ylabel("nanoseconds"); b.set_ylim(0, 620); b.set_title("How long one read that waits for the previous one takes", fontsize=11); despine(b)
save(fig, "12-read-during-copy")

# ---------------- 13. how many reuses are served from DRAM, by size of the DRAM copy area (simulation) ---------------------------------
sim = open(f"{R}/2026-09-23-kv-first-hit-promotion/first-hit-8B-delay0.txt").read() + open(f"{R}/2026-09-23-kv-first-hit-promotion/variants-8B.txt").read()
pat = re.compile(r"trace=(?:mooncake_)?([a-z]+)(?:_trace\.jsonl)? dram=(\w+)GiB delay=(\d+)s(?: k=(\d) evict=(\w+))? \|[^\n]*?\(DRAM ([\d.]+)%")
ours, best, unl = collections.defaultdict(dict), collections.defaultdict(dict), {}
for name, cap, delay, k, ev, share in pat.findall(sim):
    if delay != "0": continue
    if cap == "inf" and (k in ("", "1")) and ev in ("", "lru"): unl[name] = float(share); continue
    if cap == "inf": continue
    if k in ("", "1") and ev in ("", "lru"): ours[name][int(cap)] = float(share)
    if ev == "oracle": best[name][int(cap)] = float(share)
NAMES = {"conversation": ("chat service", "C0"), "toolagent": ("agent service", "C1"), "synthetic": ("synthetic workload", "C2")}
fig, ax = plt.subplots(figsize=(10.5, 4.8))
for name, (lab, color) in NAMES.items():
    cs = sorted(ours[name]); ax.plot(cs, [ours[name][c] for c in cs], "-o", color=color, lw=2.2, label=f"{lab}: copy after the first reuse")
    cb = sorted(best[name]); ax.plot(cb, [best[name][c] for c in cb], "--", color=color, lw=1.4, alpha=0.8, label=f"{lab}: perfect knowledge of the future")
    ax.scatter([300], [unl[name]], color=color, marker="D", s=60, zorder=3); ax.text(310, unl[name], f"{unl[name]:.0f}%", va="center", fontsize=10, color=color)
ax.set_xscale("log", base=2); ax.set_xticks([10, 20, 40, 80, 160, 300]); ax.set_xticklabels(["10", "20", "40", "80", "160", "no limit"])
ax.set_xlabel("size of the DRAM area that holds copies, GiB"); ax.set_ylabel("share of reuses served from DRAM, %"); ax.set_ylim(0, 100)
ax.legend(fontsize=9, loc="upper left", ncol=1); despine(ax, "both")
save(fig, "13-share-from-dram")

# ---------------- 14. when does the second reuse come, and how long does a copy stay (Mooncake traces) ---------------------------------
txt = open(f"{R}/2026-10-07-read-cost/reuse-gaps.txt").read()
fig, ax = plt.subplots(figsize=(10.5, 4.6))
for name, (lab, color) in NAMES.items():
    pts = [(float(a), float(b)) for a, b in re.findall(r"(\d+):([\d.]+)", re.search(rf"CDF {name}: (.*)", txt).group(1))]
    ax.plot([p[0] for p in pts], [100 * p[1] for p in pts], "-", color=color, lw=2.2, label=lab)
for S, xs in ((80, 106), (320, 424)):
    ax.axvline(xs, color=INK2, ls=":", lw=1.2); ax.text(xs * 1.04, 8, f"an {S} GiB area keeps\na copy about {xs} s" if S == 80 else f"a {S} GiB area: about {xs} s", fontsize=10, color=INK2)
ax.set_xscale("log"); ax.set_xticks([10, 30, 60, 120, 300, 600, 1200]); ax.set_xticklabels(["10 s", "30 s", "1 min", "2 min", "5 min", "10 min", "20 min"])
ax.set_xlabel("time between the first and the second reuse of a block"); ax.set_ylabel("share of second reuses that\nhave arrived by then, %"); ax.set_ylim(0, 102); ax.set_xlim(8, 1900)
ax.legend(fontsize=10, loc="upper left"); despine(ax, "both")
save(fig, "14-reuse-gap")
