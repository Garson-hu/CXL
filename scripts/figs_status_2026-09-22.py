#!/usr/bin/env python3
"""Figures for the 2026-09-22 status deck, all from raw results in the repo (matplotlib)."""
import csv, re, statistics as st, collections, os
# Reads: hardware/results, experimental_results/{2026-09-21-dram-write-budget, 2026-09-22-moderate-pacing-dcp, 2026-09-22-three-policies-realdata}
# and a snapshot of the real-data summary (realdata-summary.csv beside this script, or regenerate it with benchmarks/policy/analyze_policy.py).
# Output: ./figs/*.png next to the script. Numbers typed into the script (cliff, duplex, o3, kv, guard) are copied from the experiment files named in each block.
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = "/home/ghu4/CXL/experimental_results"; OUT = os.path.dirname(os.path.abspath(__file__)) + "/figs"; os.makedirs(OUT, exist_ok=True)
DRAM, CXL, GRAY, INK, INK2, MIX, LIGHT = "#c8511b", "#1f6f78", "#8a9bb0", "#15202b", "#4a5568", "#5b8c5a", "#f7f6f2"
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans", "text.color": INK, "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": LIGHT, "axes.facecolor": LIGHT, "savefig.facecolor": LIGHT, "axes.titlesize": 12, "axes.titleweight": "bold", "legend.frameon": False})
def despine(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e3e2de", lw=0.8); ax.set_axisbelow(True)
def save(fig, name): fig.tight_layout(pad=0.6); fig.savefig(f"{OUT}/{name}.png", dpi=200); plt.close(fig); print("wrote", name)

# ---------- 1. the DRAM write-drain cliff (2026-09-08, healthy NPS1 socket) ----------
nt = [(0, 96.4), (54.1, 87.6), (79.3, 75.9), (138, 78.8), (273, 8.0), (294, 8.9)]
pl = [(0, 96.4), (37.0, 91.6), (62.6, 81.3), (65.4, 80.3), (110, 61.5), (137, 12.4), (138, 7.8)]
fig, ax = plt.subplots(figsize=(8.4, 4.4))
ax.plot([x for x, _ in nt], [y for _, y in nt], "-o", color=DRAM, lw=2.2, ms=7, label="aggressor: non-temporal (streaming) stores")
ax.plot([x for x, _ in pl], [y for _, y in pl], "--s", color=GRAY, lw=2, ms=6, label="aggressor: plain stores (read-for-ownership)")
ax.axvline(290, color=INK2, ls=":", lw=1.2); ax.text(292, 60, "socket write ceiling\n~290 GiB/s", fontsize=10, color=INK2)
ax.annotate("12× (96 → 8 GiB/s)\nload latency 130 → 610 ns", (273, 8), (150, 25), fontsize=10, arrowprops=dict(arrowstyle="->", color=INK))
ax.set_xlabel("DRAM write rate of the co-running writers, GiB/s (writers on other CCDs)"); ax.set_ylabel("bandwidth of a 4-thread DRAM reader, GiB/s")
ax.set_ylim(0, 105); ax.set_xlim(-5, 320); despine(ax); ax.legend(loc="lower left", fontsize=10)
save(fig, "cliff")

# ---------- 2. CXL: reads + writes together exceed either alone (2026-09-08 card scaling, 32 threads) ----------
cards = ["1 card", "2 cards (the dax0.0 pair)", "4 cards"]; rd = [24.2, 45.6, 90.2]; wr = [22.0, 43.7, 85.4]; mx = [37.2, 62.4, 128.3]; gain = ["+53%", "+36%", "+42%"]
fig, ax = plt.subplots(figsize=(8.4, 4.4)); x = range(3); w = 0.26
ax.bar([i - w for i in x], rd, w, color=CXL, label="reads only"); ax.bar(list(x), wr, w, color=DRAM, label="NT writes only"); ax.bar([i + w for i in x], mx, w, color=MIX, label="reads + writes at the same time")
for i in x:
    ax.text(i - w, rd[i] + 2, f"{rd[i]:.0f}", ha="center", fontsize=10); ax.text(i, wr[i] + 2, f"{wr[i]:.0f}", ha="center", fontsize=10)
    ax.text(i + w, mx[i] + 2, f"{mx[i]:.0f} ({gain[i]})", ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(list(x)); ax.set_xticklabels(cards); ax.set_ylabel("aggregate GiB/s"); ax.set_ylim(0, 150); despine(ax); ax.legend(loc="upper left", fontsize=10)
ax.text(0.99, 0.97, "DRAM in the same mix: the sum never exceeds one direction\n(one pipe, ~290 GiB/s; reads collapse past the cliff)", transform=ax.transAxes, ha="right", va="top", fontsize=10, color=INK2)
save(fig, "duplex")

# ---------- 3. O3: the write stream moved to CXL costs the DRAM reader nothing (gate 2b, 2026-08-25) + stencil (2026-09-14) ----------
fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 4.2), gridspec_kw=dict(width_ratios=[1.15, 1]))
vals = [68.6, 10.9, 68.6]; cols = [GRAY, DRAM, CXL]; labs = ["reader alone", "+ 8 NT writers\ninto DRAM", "+ the same writers\nredirected to CXL"]
a.bar(range(3), vals, color=cols, width=0.6)
for i, v in enumerate(vals): a.text(i, v + 1.5, f"{v:.1f}", ha="center", fontsize=11, fontweight="bold")
a.set_xticks(range(3)); a.set_xticklabels(labs, fontsize=10); a.set_ylabel("DRAM reader, GiB/s"); a.set_ylim(0, 80); a.set_title("A DRAM reader beside a 55 GiB/s write stream"); despine(a)
idle = [0.261, 0.60]; press = [2.59, 0.60]; xx = [0, 1]
b.bar([i - 0.18 for i in xx], idle, 0.36, color=GRAY, label="no DRAM write pressure"); b.bar([i + 0.18 for i in xx], press, 0.36, color=DRAM, label="280 GiB/s of DRAM NT writes beside it")
for i in xx: b.text(i - 0.18, idle[i] + 0.05, f"{idle[i]:.2f}", ha="center", fontsize=10); b.text(i + 0.18, press[i] + 0.05, f"{press[i]:.2f}", ha="center", fontsize=10, fontweight="bold")
b.set_xticks(xx); b.set_xticklabels(["stencil, all data in DRAM", "stencil, all data on CXL"], fontsize=10); b.set_ylabel("seconds per step"); b.set_ylim(0, 3.1); b.set_title("An application that lives on CXL is immune"); despine(b); b.legend(fontsize=9, loc="upper right")
save(fig, "o3")

# ---------- 4. KV traces: written-never-read shares and read-back gaps (2026-09-09) ----------
tr = ["conversation", "toolagent", "synthetic"]; never = [76, 78, 58]; p50 = [114, 0, 59]; p90 = [519, 243, 282]; wr8 = [3.23, 3.24, 2.69]
fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 4.2), gridspec_kw=dict(width_ratios=[1, 1.1]))
a.bar(range(3), never, color=CXL, width=0.55); a.bar(range(3), [100 - n for n in never], bottom=never, color=DRAM, width=0.55)
for i, n in enumerate(never): a.text(i, n / 2, f"{n}%\nnever read\nagain", ha="center", va="center", fontsize=10, color="white", fontweight="bold"); a.text(i, n + (100 - n) / 2, f"{100 - n}%\nread back", ha="center", va="center", fontsize=9, color="white")
a.set_xticks(range(3)); a.set_xticklabels([f"{t}\n{w:.1f} GiB/s of KV\nwrites (Llama-3.1-8B)" for t, w in zip(tr, wr8)], fontsize=9); a.set_ylabel("share of KV blocks written to the prefix pool, %"); a.set_ylim(0, 100); a.set_title("Mooncake production traces, 512-token blocks"); despine(a)
b.bar([i - 0.18 for i in range(3)], p50, 0.36, color=GRAY, label="reuse gap p50"); b.bar([i + 0.18 for i in range(3)], p90, 0.36, color=INK2, label="reuse gap p90")
for i in range(3): b.text(i - 0.18, p50[i] + 8, f"{p50[i]} s", ha="center", fontsize=9); b.text(i + 0.18, p90[i] + 8, f"{p90[i]} s", ha="center", fontsize=9)
b.set_xticks(range(3)); b.set_xticklabels(tr, fontsize=10); b.set_ylabel("seconds from write to next read"); b.set_ylim(0, 600); b.set_title("The reads that do happen come seconds to minutes later"); despine(b); b.legend(fontsize=9)
save(fig, "kv")

# ---------- 5. phase 1: DRAM write budget under a bound (2026-09-21/22) ----------
def budget(victim, f):
    rows = [r for r in csv.DictReader(open(f"{R}/2026-09-21-dram-write-budget/{f}")) if r["target"] == "dram" and r["overlap_ok"] == "1"]
    v0 = st.median(float(r["value"]) for r in rows if r["asked_GiBs"] == "0")
    out = {}
    for mode in ("pure", "copy"):
        g = collections.defaultdict(list)
        for r in rows:
            if r["mode"] == mode and r["asked_GiBs"] != "0": g[r["asked_GiBs"]].append(r)
        pts = []
        for k, rs in g.items():
            wr_ = st.median(float(r["write_GiBs"]) for r in rs); v = st.median(float(r["value"]) for r in rs)
            slow = 100 * (1 - v / v0) if victim in ("synth", "llama") else 100 * (v / v0 - 1)
            pts.append((wr_, slow))
        out[mode] = sorted(pts)
    return out
data = {"synthetic reader (8 threads, ~100 GiB/s)": budget("synth", "synth.csv"), "CPU Adam step (24 GB state, 80 threads)": budget("opt", "opt.csv"), "llama.cpp decode (Qwen2.5-7B Q8, 80 threads)": budget("llama", "llama.csv"), "GAPBS PageRank (2^26, 80 threads)": budget("pr", "pr.csv")}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True); cols = [CXL, DRAM, MIX, "#7a4fb0"]
for ax, mode, title in zip(axes, ("pure", "copy"), ("pure NT writes into DRAM", "copies into DRAM (source read + NT write)")):
    for (name, d), c in zip(data.items(), cols):
        pts = d[mode]; ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", color=c, ms=4, lw=1.8, label=name)
    ax.axhline(7, color=INK2, ls=":", lw=1.2); ax.text(1, 7.6, "7% bound", fontsize=9, color=INK2)
    ax.axvline(43.9, color=CXL, ls="--", lw=1); ax.text(45, 38, "CXL pair\n43.9 GiB/s", fontsize=9, color=CXL)
    ax.set_xlabel("achieved DRAM write rate of the co-runner, GiB/s"); ax.set_title(title); ax.set_ylim(-2, 45); ax.set_xlim(0, 130); despine(ax)
axes[0].set_ylabel("victim slowdown, %"); axes[0].legend(fontsize=9, loc="upper left")
save(fig, "budget")

# ---------- 6. the core figure, real-data re-run (reps 1-2 of 3) ----------
rows = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.dirname(os.path.abspath(__file__)) + "/realdata-summary-2026-09-22.csv")): rows[r["tag"].rsplit("-rep", 1)[0]].append(r)
S = dict(dram=("all-DRAM staging (today)", DRAM, "o"), plain=("all-DRAM, plain stores", DRAM, "s"), cxl=("all-CXL", CXL, "o"), lim=("DRAM, throttled", GRAY, "^"), cx=("cxlpath", INK, "*"), cx2=("cxlpath, looser bound", "#4a5d7a", "P"))
panels = [("Synthetic reader, 8 threads (moderate)", [("reader-dram", "dram"), ("reader-dram-plain", "plain"), ("reader-cxl", "cxl"), ("reader-dram-limited-r20", "lim"), ("reader-cxlpath-b1.09", "cx"), ("reader-cxlpath-b1.15", "cx2")]),
          ("GAPBS PageRank, 32 threads (moderate); 192 GiB", [("pr32-dram-s192", "dram"), ("pr32-cxl-s192", "cxl"), ("pr32-dram-limited-r20-s192", "lim"), ("pr32-cxlpath-b1.05-s192", "cx"), ("pr32-cxlpath-b1.09-s192", "cx2")]),
          ("llama.cpp decode, 32 threads (moderate)", [("llama32-dram", "dram"), ("llama32-cxl", "cxl"), ("llama32-dram-limited-r20", "lim"), ("llama32-cxlpath-b1.05", "cx")]),
          ("CPU Adam step, 80 threads (saturated)", [("opt-dram", "dram"), ("opt-dram-plain", "plain"), ("opt-cxl", "cxl"), ("opt-dram-limited-r10", "lim"), ("opt-cxlpath-b1.04", "cx")])]
fig, axes = plt.subplots(1, 4, figsize=(15.5, 4.3))
for ax, (title, series) in zip(axes, panels):
    for base, kind in series:
        rs = rows.get(base)
        if not rs: print("missing", base); continue
        label, color, marker = S[kind]; xs = [float(r["completion_s"]) for r in rs]; ys = [float(r["slowdown_pct"]) for r in rs]
        ax.scatter(xs, ys, s=22, color=color, marker=marker, alpha=0.35)
        x, y = st.mean(xs), st.mean(ys); ax.scatter([x], [y], s=(230 if marker == "*" else 120), color=color, marker=marker, edgecolor="k", linewidth=0.5, label=label, zorder=3)
        rate = st.mean(float(r["copy_GiBs"]) for r in rs); share = st.mean(float(r["dram_share"]) for r in rs)
        ax.annotate(f"{rate:.0f} GiB/s" + (f", {100 * share:.0f}% DRAM" if kind.startswith("cx") and share > 0.005 else ""), (x, y), textcoords="offset points", xytext=(7, 4), fontsize=8, color=color)
    ax.axhline(7, ls=":", color=INK2, lw=1); ax.set_xlim(left=0); ax.set_title(title, fontsize=10); ax.set_xlabel("completion time of the 64 GiB copy, s"); despine(ax); ax.legend(fontsize=7.5, loc="best")
axes[0].set_ylabel("victim slowdown during the copy, %")
save(fig, "core")

# ---------- 7. DCP headline timeline (real producer; 2026-09-22) ----------
d = f"{R}/2026-09-22-moderate-pacing-dcp"; fig, ax = plt.subplots(figsize=(13, 4.2))
for tag, label, color in [("opt-dcp-dram-s16-rep2", "DCP stock: BlockingAsyncStager into pinned DRAM + FileSystemWriter (today)", DRAM), ("opt-dcp-cxlpath-s16-rep2", "DCP with CxlpathWriter: NT copy into CXL, daemon drains CXL → NVMe", CXL)]:
    pt = open(f"{d}/{tag}-producer.txt").read(); wins = [(int(m[1]), int(m[2])) for m in re.findall(r"COPY (\d+) START (\d+) END (\d+)", pt)]; s0, s1 = wins[3]
    pers = [(int(m[1]), int(m[2])) for m in re.findall(r"PERSIST (\d+) START (\d+) END (\d+)", pt)]
    steps = [(int(m[1]), float(m[0])) for m in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", open(f"{d}/{tag}-victim.txt").read())]
    base = st.median(v for t, v in steps if wins[0][0] - 15e9 <= t < wins[0][0] - 0.5e9)
    xs = [(t - s0) / 1e9 for t, v in steps if s0 - 4e9 <= t <= s0 + 12e9]; ys = [100 * (v / base - 1) for t, v in steps if s0 - 4e9 <= t <= s0 + 12e9]
    ax.plot(xs, ys, color=color, lw=1.8, label=f"{label}\n   training thread blocked {(s1 - s0) / 1e9:.2f} s, durable after {(pers[3][1] - s0) / 1e9:.0f} s"); ax.axvspan(0, (s1 - s0) / 1e9, color=color, alpha=0.10)
ax.axhline(0, color="k", lw=0.8); ax.set_xlabel("time relative to the start of dcp.async_save, s"); ax.set_ylabel("Adam step time vs no checkpoint, %"); ax.set_ylim(-1, 14); despine(ax); ax.legend(loc="upper right", fontsize=9.5)
save(fig, "dcp")

# ---------- 8. the controller in action (reader-cxlpath-b1.09-rep1, real-data re-run) ----------
f = f"{R}/2026-09-22-three-policies-realdata/reader-cxlpath-b1.09-rep1-daemon.csv"; hdr = open(f).readline(); idle = float(hdr.split("idle_ns=")[1].split()[0]); bound = float(hdr.split("bound=")[1].split()[0])
log = [r for r in csv.DictReader(l for l in open(f) if not l.startswith("#"))]
t = [float(r["t_ms"]) / 1000 for r in log]; m5 = [float(r["mean5_ns"]) for r in log]; sp = [int(r["spill16"]) / 16 * 100 for r in log]; cg = [float(r["cxl_GiBs"]) for r in log]; dg = [float(r["dram_GiBs"]) for r in log]
lo, hi = 28, 84; sel = [i for i, x in enumerate(t) if lo <= x <= hi]
fig, (a, b, c) = plt.subplots(3, 1, figsize=(13, 5.6), sharex=True)
a.plot([t[i] for i in sel], [m5[i] for i in sel], color=INK, lw=1.2, label="DRAM latency probe, 50 ms mean"); a.axhline(idle, color=GRAY, ls="--", lw=1, label=f"calibrated idle level {idle:.0f} ns"); a.axhline(bound * idle, color=DRAM, ls=":", lw=1.4, label=f"bound {bound:.2f} × idle = {bound * idle:.0f} ns")
a.set_ylabel("ns"); a.legend(fontsize=9, loc="upper right", ncol=3); despine(a); a.set_ylim(120, 175)
b.step([t[i] for i in sel], [sp[i] for i in sel], color=INK, lw=1.4, where="post"); b.set_ylabel("DRAM share of\nnew chunks, %"); b.set_ylim(0, 60); despine(b)
c.stackplot([t[i] for i in sel], [cg[i] for i in sel], [dg[i] for i in sel], colors=[CXL, DRAM], labels=["written to CXL", "written to DRAM (the loan)"]); c.set_ylabel("GiB/s"); c.set_xlabel("time since daemon start, s (two 64 GiB copies, 25 s apart, beside the 8-thread reader)"); c.legend(fontsize=9, loc="upper right", ncol=2); despine(c); c.set_ylim(0, 75)
save(fig, "controller")

# ---------- 9. zero-line writes (2026-09-22) ----------
fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.2), sharey=False)
for ax, title, z, r in [(a, "copy into CXL (8 threads)", [43.8, 43.7], [43.9, 28.8]), (b, "copy into DRAM (8 threads)", [94.5, 82.3], [94.3, 18.7])]:
    xx = [0, 1]; ax.bar([i - 0.18 for i in xx], z, 0.36, color=GRAY, label="source = all-zero cache lines"); ax.bar([i + 0.18 for i in xx], r, 0.36, color=DRAM if ax is b else CXL, label="source = random data")
    for i in xx: ax.text(i - 0.18, z[i] + 1.5, f"{z[i]:.0f}", ha="center", fontsize=10); ax.text(i + 0.18, r[i] + 1.5, f"{r[i]:.0f}", ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(xx); ax.set_xticklabels(["alone", "beside llama.cpp (32 threads)"]); ax.set_ylabel("copy rate, GiB/s"); ax.set_title(title); despine(ax); ax.legend(fontsize=9, loc="upper right"); ax.set_ylim(0, (55 if ax is a else 110))
save(fig, "zeroline")

# ---------- 10. the regime signal: probe level per victim vs the guard ----------
names = ["idle machine", "reader 8T", "llama.cpp 32T", "PageRank 32T", "Adam 32T", "PageRank 80T", "llama.cpp 80T", "Adam 80T"]; lvl = [1.0, 1.03, 1.14, 1.13, 1.42, 1.41, 1.5, 1.95]
fig, ax = plt.subplots(figsize=(8.4, 4.0)); cols = [CXL if v < 1.3 else DRAM for v in lvl]
ax.bar(range(len(names)), lvl, color=cols, width=0.6); ax.axhline(1.3, color=INK, ls=":", lw=1.4); ax.text(7.4, 1.32, "guard 1.3×: no loan above", ha="right", fontsize=10)
for i, v in enumerate(lvl): ax.text(i, v + 0.03, f"{v:.2f}×", ha="center", fontsize=10)
ax.set_xticks(range(len(names))); ax.set_xticklabels(names, fontsize=9, rotation=15); ax.set_ylabel("DRAM probe latency beside the victim,\nrelative to the idle level (135 ns)"); ax.set_ylim(0.8, 2.15); despine(ax)
ax.text(0.01, 0.97, "teal = DRAM has headroom, the loan is allowed;  orange = saturated, cxlpath = all-CXL (+ pacing)", transform=ax.transAxes, fontsize=9.5, va="top", color=INK2)
save(fig, "guard")
