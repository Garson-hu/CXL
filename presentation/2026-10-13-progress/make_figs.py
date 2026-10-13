#!/usr/bin/env python3
"""Figures of the research-progress deck of 2026-10-13 (every data figure is drawn from the raw result files in
experimental_results/; nothing is typed in by hand). Writes figs/<name>.png and .svg and figs/SOURCES.md (figure -> files).
Colours: the matplotlib default cycle, one fixed colour per category (DRAM blue, CXL orange, static split purple,
budget-gated green, existing controller gray), white background (user rule of 2026-10-07).
usage: make_figs.py [repo_root]   (run from anywhere; ~1 min)"""
import csv, glob, gzip, os, re, statistics as st, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
E = os.path.join(ROOT, "experimental_results"); OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs"); os.makedirs(OUT, exist_ok=True)
C = dict(dram="#1f77b4", cxl="#ff7f0e", split="#9467bd", budget="#2ca02c", ctrl="#7f7f7f", pm="#d62728", ink="#222222", muted="#666666")
plt.rcParams.update({"font.size": 13, "axes.titlesize": 14, "axes.labelsize": 13, "legend.fontsize": 11.5, "xtick.labelsize": 12, "ytick.labelsize": 12,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
                     "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.8, "axes.axisbelow": True, "legend.frameon": False, "svg.fonttype": "none"})
SOURCES = {}
def rd(p): return gzip.open(p, "rt", errors="replace").read() if p.endswith(".gz") else open(p, errors="replace").read()
def rdx(p): return rd(p) if os.path.exists(p) else rd(p + ".gz")
def med(xs): return st.median(xs)
def save(fig, name, sources, note=None):
    fig.tight_layout(rect=(0, getattr(fig, "_note_rect", 0.05 if note else 0), 1, 1))
    if note: fig.text(0.005, 0.006, note, fontsize=9, color=C["muted"], ha="left", va="bottom")
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200, bbox_inches="tight"); fig.savefig(os.path.join(OUT, name + ".svg"), bbox_inches="tight"); plt.close(fig)
    SOURCES[name] = sources; print("wrote", name)
def bars(ax, labels, series, colors, hatches=None, width=None, fmt="{:.1f}", label_fs=10.5, ylabel=None, legend=None, rot=0, yerr=None, vlabels=False):
    """grouped bars: series = {name: [values per label]}"""
    n = len(series); width = width or 0.8 / n; xs = range(len(labels))
    for i, (nm, vals) in enumerate(series.items()):
        off = (i - (n - 1) / 2) * width
        err = yerr.get(nm) if yerr else None
        b = ax.bar([x + off for x in xs], vals, width * 0.92, color=colors[i], hatch=(hatches or [None] * n)[i], edgecolor="white", linewidth=0.8, label=nm,
                   yerr=err, capsize=3, error_kw=dict(lw=1, color=C["ink"]))
        for k, (r, v) in enumerate(zip(b, vals)):
            if v is None or v != v: continue
            e = err[k] if (err and vlabels and err[k] == err[k]) else 0
            ax.annotate(fmt.format(v), (r.get_x() + r.get_width() / 2, r.get_height() + e), xytext=(0, 2 if v >= 0 else -2), textcoords="offset points",
                        ha="center", va="bottom" if v >= 0 else "top", fontsize=label_fs, color=C["ink"], rotation=90 if vlabels else 0)
    ax.set_xticks(list(xs)); ax.set_xticklabels(labels, rotation=rot, ha="right" if rot else "center")
    if ylabel: ax.set_ylabel(ylabel)
    if legend or (legend is None and n > 1): ax.legend(loc=legend if isinstance(legend, str) else "best")

# ---------------------------------------------------------------- helpers for the membench CSVs
def membench(path):
    rows = list(csv.DictReader(open(path))); out = {}
    for tag in {r["tag"] for r in rows}:
        rs = [r for r in rows if r["tag"] == tag]
        out[tag] = dict(bw=med([float(r["bandwidth_gib_s"]) for r in rs]), aggr=med([float(r["aggressor_bandwidth_gib_s"]) for r in rs]), n=len(rs))
    return out
def topo_cells(path):
    cells = {}
    for m in re.finditer(r"CELL rep=(\d+) fg=(\w+) kind=(\w+) place=(\S+) threads=(\d+) reader_GiBs=([\d.]+) chain_ns=([\d.]+) bg_GiBs=([\d.]+)", rd(path)):
        cells.setdefault((m[2], m[3], m[4], int(m[5])), []).append((float(m[6]), float(m[7]), float(m[8])))
    return {k: tuple(med([v[i] for v in vs]) for i in range(3)) for k, vs in cells.items()}

# ---------------------------------------------------------------- F1 drain cliff
def f_drain_cliff():
    d1 = os.path.join(E, "2026-09-08-dram-write-drain"); m1 = membench(f"{d1}/1b-matrix.csv"); m2 = membench(f"{d1}/1b2-matrix.csv"); ag = membench(f"{d1}/1b-aggressor.csv")
    topo = topo_cells(os.path.join(E, "2026-10-09-cxl-topology-interference", "topo.txt"))
    idle = m2["1b2-ro-idle"]["bw"]; cxl_idle = topo[("dram", "none", "-", 0)][0]; cxl8 = topo[("dram", "cxl_nt", "far", 8)]
    items = [("none", 100.0, C["dram"]),
             (f"8 → CXL\nother CCD\n{cxl8[2]:.0f} GiB/s", 100 * cxl8[0] / cxl_idle, C["cxl"]),
             (f"8 → DRAM\n1 CCD\n{ag['1b-wo-nt-w8']['bw']:.0f} GiB/s", 100 * m1["1b-rw-nt-w8"]["bw"] / m1["1b-ro-idle"]["bw"], C["dram"]),
             (f"32 → DRAM\n2 CCDs\n{ag['1b-wo-nt-w32']['bw']:.0f} GiB/s", 100 * m2["1b2-rw-nt-w32"]["bw"] / idle, C["dram"]),
             (f"64 → DRAM\n4 CCDs\n{ag['1b-wo-nt-w64']['bw']:.0f} GiB/s", 100 * m2["1b2-rw-nt-w64"]["bw"] / idle, C["dram"]),
             (f"96 → DRAM\n6 CCDs\n{ag['1b-wo-nt-w96']['bw']:.0f} GiB/s", 100 * m2["1b2-rw-nt-w96"]["bw"] / idle, C["dram"])]
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    b = ax.bar(range(len(items)), [i[1] for i in items], color=[i[2] for i in items], width=0.62)
    for r, it in zip(b, items): ax.annotate(f"{it[1]:.0f}%", (r.get_x() + r.get_width() / 2, r.get_height()), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=12, color=C["ink"])
    ax.set_xticks(range(len(items))); ax.set_xticklabels([i[0] for i in items], fontsize=10.5); ax.set_ylim(0, 112)
    ax.set_xlabel("non-temporal writer threads → target, core groups used, writers' own rate"); ax.set_ylabel("DRAM reader bandwidth, % of idle")
    ax.set_title("A 4-thread DRAM reader beside bulk writers")
    save(fig, "f01_drain_cliff", [f"{d1}/1b-matrix.csv", f"{d1}/1b2-matrix.csv", f"{d1}/1b-aggressor.csv", "2026-10-09-cxl-topology-interference/topo.txt"],
         "Hardware measurement, c28 (EPYC 9745, NPS1): reader on CCD 0 (CXL case: CCD 4), writers on other CCDs; medians of 3–5 runs. 2026-09-14 / 2026-10-10")
# ---------------------------------------------------------------- F2 original system core result
def f_original_core():
    d = os.path.join(E, "2026-09-22-three-policies-realdata"); rows = list(csv.DictReader(open(f"{d}/summary.csv")))
    def g(prefix):
        rs = [r for r in rows if re.sub(r"-rep\d+$", "", r["tag"]) == prefix]
        return med([float(r["slowdown_pct"]) for r in rs]), med([float(r["completion_s"]) for r in rs])
    victims = [("DRAM reader, 8 threads", "reader", "", "1.09"), ("PageRank, 32 threads", "pr32", "-s192", "1.09"), ("Adam step, 80 threads", "opt", "", "1.04")]
    pols = [("all DRAM (today)", "dram", C["dram"], "o", (8, 4)), ("all CXL", "cxl", C["cxl"], "s", (8, -12)), ("DRAM throttled to 20 GiB/s", "dram-limited-r20", C["dram"], "v", (-10, 8)), ("cxlpath: CXL + DRAM loan", "cxlpath-b{b}", C["ctrl"], "D", (8, 6))]
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.3))
    for ax, (title, v, suf, bound) in zip(axs, victims):
        pts = []
        for nm, p, col, mk, off in pols:
            tag = f"{v}-{p.format(b=bound)}{suf}"
            try: sl, t = g(tag)
            except st.StatisticsError: continue
            pts.append((t, sl)); ax.scatter([t], [sl], s=90, color=col, marker=mk, label=nm, zorder=3)
            ax.annotate(f"{sl:.0f}%", (t, sl), xytext=off, textcoords="offset points", fontsize=10.5, ha="center")
        ax.set_title(title, fontsize=12.5); ax.set_xlabel("checkpoint copy time, s"); ax.set_xlim(0, max(x for x, _ in pts) * 1.25); ax.set_ylim(-3, max(y for _, y in pts) * 1.25)
    axs[0].set_ylabel("victim slowdown during the copy, %")
    h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=4, fontsize=10.5, bbox_to_anchor=(0.5, 0.05))
    fig._note_rect = 0.13
    save(fig, "f02_original_core", [f"{d}/summary.csv"], "Real applications on c28, 64 GiB checkpoint every 25 s (PageRank: 192 GiB / 30 s); medians of 3 runs. 2026-09-22/23")
# ---------------------------------------------------------------- F3 / F4 / F15 diagrams
def box(ax, x, y, w, h, text, fc="#f3f3f3", ec="#444444", fs=11.5, bold=False, tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=tc or C["ink"])
def arrow(ax, p, q, text=None, col="#444444", ls="-", fs=10.5, tpos=0.5, toff=(0, 0.12)):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, color=col, lw=1.6, linestyle=ls, shrinkA=2, shrinkB=2))
    if text: ax.text(p[0] + (q[0] - p[0]) * tpos + toff[0], p[1] + (q[1] - p[1]) * tpos + toff[1], text, fontsize=fs, ha="center", va="center", color=col)
def canvas(w=11, h=4.6):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off"); ax.grid(False); return fig, ax
def f_arch_original():
    fig, ax = canvas(11.5, 5.0)
    box(ax, 0.3, 3.5, 2.4, 1.0, "Applications\ncheckpoint staging\nKV-cache stores", fc="#eaeaea", fs=11)
    box(ax, 3.6, 3.5, 3.2, 1.0, "Placement decision\nCXL by default; DRAM loan while\nCXL is full and DRAM readers\nstay inside the bound", fc="#efe9f5", fs=10)
    box(ax, 8.0, 4.0, 3.2, 0.75, "CXL segment store (raw dax)", fc="#fdebd9", fs=11)
    box(ax, 8.0, 2.85, 3.2, 0.75, "DRAM spill pool (on loan)", fc="#dde9f5", fs=11)
    box(ax, 8.0, 1.5, 3.2, 0.7, "NVMe (drain, no DRAM copy)", fc="#eaeaea", fs=11)
    box(ax, 3.6, 1.5, 3.2, 1.0, "Interference monitor\nDRAM latency probe every ~30 ms\n+ CXL write ledger", fc="#efe9f5", fs=10.5)
    box(ax, 0.3, 1.5, 2.4, 1.0, "Readers\nread in place;\ncopy to DRAM if reuse pays", fc="#eaeaea", fs=10.5)
    arrow(ax, (2.7, 4.0), (3.6, 4.0), "write", toff=(0, 0.15)); arrow(ax, (6.8, 4.2), (8.0, 4.37), "default", toff=(0, 0.17)); arrow(ax, (6.8, 3.8), (8.0, 3.22), "loan", col=C["dram"], toff=(0.25, 0.0))
    arrow(ax, (9.6, 4.0), (9.6, 3.6)); arrow(ax, (9.6, 2.85), (9.6, 2.2)); arrow(ax, (5.2, 2.5), (5.2, 3.5), "headroom?", col=C["ctrl"], toff=(0.75, 0))
    arrow(ax, (1.5, 2.5), (1.5, 3.5), "lookup", ls="--", toff=(0.5, 0)); arrow(ax, (9.0, 4.0), (2.7, 2.3), "read in place", ls="--", col=C["cxl"], tpos=0.8, toff=(0, 0.17))
    ax.text(0.3, 0.6, "Built 2026-09-19 (cxlpath, user space). DRAM holds copies of CXL data (inclusive): DRAM adds speed, not capacity.", fontsize=10.5, color=C["muted"])
    save(fig, "f03_arch_original", ["docs/DESIGN.md §10 (as built)"])
def f_unified_pool():
    fig, ax = canvas(12.5, 4.3)
    for x0, title, left, right, note in [(0.3, "Inclusive (original cxlpath read path)", "CXL\nevery block", "DRAM\ncopies of hot blocks", "capacity = CXL\nhits get faster"),
                                         (6.6, "Exclusive (advisor's unified pool)", "CXL\ncold and write-only blocks", "DRAM\nhot blocks, one place each", "capacity = CXL + DRAM\nneeds promotion, demotion,\neviction, reclamation")]:
        ax.text(x0 + 2.8, 3.95, title, ha="center", fontsize=12.5, fontweight="bold")
        box(ax, x0, 2.3, 2.4, 1.2, left, fc="#fdebd9", fs=10.5); box(ax, x0 + 3.2, 2.3, 2.4, 1.2, right, fc="#dde9f5", fs=10.5)
        ax.text(x0 + 2.8, 1.15, note, ha="center", va="center", fontsize=10.5, color=C["ink"])
    arrow(ax, (2.7, 2.9), (3.5, 2.9), "copy", toff=(0, 0.22)); arrow(ax, (9.0, 3.15), (9.8, 3.15), "promote", toff=(0, 0.22)); arrow(ax, (9.8, 2.65), (9.0, 2.65), "demote", toff=(0, -0.22))
    ax.text(6.25, 0.25, "In both, new writes, promotions and copies spend DRAM write bandwidth, which other programs' reads are sensitive to.", ha="center", fontsize=10.5, color=C["muted"])
    save(fig, "f04_unified_pool", ["WORKLOG.md session 29 (2026-10-09 discussion)"])
def f_budget_design():
    fig, ax = canvas(11.5, 4.6)
    box(ax, 0.3, 3.1, 2.6, 1.1, "New KV block\n(store starts)", fc="#eaeaea")
    box(ax, 3.8, 2.6, 3.4, 1.9, "Token bucket\nrefill: budget B GB/s\ndepth: d blocks\n(unused credit is lost)", fc="#e3f1e1", fs=11)
    box(ax, 8.9, 3.6, 2.4, 0.85, "DRAM tier (64 GiB)\nper-tier LRU", fc="#dde9f5"); box(ax, 8.9, 2.2, 2.4, 0.85, "CXL tier (136 GiB)\nper-tier LRU", fc="#fdebd9")
    arrow(ax, (2.9, 3.65), (3.8, 3.65)); arrow(ax, (7.2, 3.9), (8.9, 4.0), "credit ≥ 1 block", col=C["dram"], tpos=0.5, toff=(0, 0.22)); arrow(ax, (7.2, 3.2), (8.9, 2.65), "no credit", col=C["cxl"], tpos=0.5, toff=(0, -0.24))
    box(ax, 0.3, 0.9, 7.6, 1.3, "B comes from a calibration against the neighbour's SLO (p99 slowdown ≤ 7%).\nVarying-load test: an ORACLE switches B with the neighbour — an upper bound, not a mechanism.\nSame capacity, eviction and warm-up as the static split.", fc="#f7f7f7", fs=10.5)
    ax.text(8.3, 1.55, "Not built: online estimation of B;\none B shared by KV admission,\npromotion and checkpoint writers.", fontsize=10.5, color=C["muted"], va="center")
    save(fig, "f15_budget_design", ["benchmarks/memory/kvemu2.c (policy budget)"])
# ---------------------------------------------------------------- F5 topology, F6 CXL reader
def f_topology():
    p = os.path.join(E, "2026-10-09-cxl-topology-interference", "topo.txt"); t = topo_cells(p); base = t[("dram", "none", "-", 0)][0]
    places = [("same CCD", "same"), ("paired CCD", "near"), ("other CCD", "far")]
    kinds = [("CXL writes (NT)", "cxl_nt", C["cxl"], None), ("DRAM → CXL copy", "copy_cxl", C["cxl"], "//"), ("DRAM writes (NT)", "dram_nt", C["dram"], None), ("DRAM → DRAM copy", "copy_dram", C["dram"], "//")]
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    series = {nm: [100 * (1 - t[("dram", k, pl, 8)][0] / base) for _, pl in places] for nm, k, _, _ in kinds}
    bars(ax, [f"{n}\n(CCD {'4' if p_ == 'same' else '5' if p_ == 'near' else '0'})" for n, p_ in places], series, [k[2] for k in kinds], [k[3] for k in kinds], fmt="{:.0f}%", ylabel="DRAM reader bandwidth loss, %", legend="upper right")
    ax.set_title("8 background threads vs a 4-thread DRAM reader on CCD 4"); ax.set_ylim(0, 92)
    rates = {k: t[("dram", k, "far", 8)][2] for _, k, _, _ in kinds}
    ax.text(0.99, 0.62, "background rates from CCD 0:\n" + "\n".join(f"{nm}: {rates[k]:.0f} GiB/s" for nm, k, _, _ in kinds), transform=ax.transAxes, ha="right", va="top", fontsize=9.5, color=C["muted"])
    save(fig, "f05_topology", [p], "Hardware measurement, c28, 5 runs × 3 s, medians; reader alone 98.0 GiB/s. 2026-10-10")
def f_cxl_reader():
    p = os.path.join(E, "2026-10-09-cxl-topology-interference", "topo.txt"); t = topo_cells(p); base = t[("cxl", "none", "-", 0)]
    rc = os.path.join(E, "2026-10-07-read-cost", "readcost.txt"); B = {}
    for m in re.finditer(r"BURST rep=\d+ read_from=(\w+) copy_into=(\w+) reader4_GiBs=([\d.]+) chain_ns=([\d.]+) writers_GiBs=([\d.]+)", rd(rc)): B.setdefault((m[1], m[2]), []).append((float(m[3]), float(m[4]), float(m[5])))
    B = {k: tuple(med([v[i] for v in vs]) for i in range(3)) for k, vs in B.items()}
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[1.25, 1]))
    kinds = [("CXL writes (NT)", "cxl_nt", C["cxl"], None), ("DRAM → CXL copy", "copy_cxl", C["cxl"], "//"), ("DRAM writes (NT)", "dram_nt", C["dram"], None)]
    places = [("same CCD", "same"), ("paired CCD", "near"), ("other CCD", "far")]
    bars(axs[0], [n for n, _ in places], {nm: [100 * (1 - t[("cxl", k, pl, 8)][0] / base[0]) for _, pl in places] for nm, k, _, _ in kinds}, [k[2] for k in kinds], [k[3] for k in kinds], fmt="{:.0f}%", ylabel="CXL reader bandwidth loss, %", legend="upper right")
    axs[0].set_title(f"4-thread CXL reader ({base[0]:.0f} GiB/s alone) vs 8 background threads", fontsize=12); axs[0].set_ylim(0, 100)
    labels = ["none", "→ DRAM", "→ CXL", "none", "→ DRAM", "→ CXL"]
    keys = [("dram", "none"), ("dram", "dram"), ("dram", "cxl"), ("cxl", "none"), ("cxl", "dram"), ("cxl", "cxl")]
    cols = [C["dram"]] * 3 + [C["cxl"]] * 3; vals = [B[k][1] for k in keys]
    b = axs[1].bar(range(6), vals, color=cols, width=0.65)
    for r, v in zip(b, vals): axs[1].annotate(f"{v:.0f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=10.5)
    axs[1].set_xticks(range(6)); axs[1].set_xticklabels(labels, fontsize=10); axs[1].set_ylabel("one dependent read, ns"); axs[1].set_title("Read latency while an 8-thread copy runs", fontsize=12); axs[1].set_ylim(0, 680)
    axs[1].set_xlabel("copy target"); axs[1].text(1, 630, "reader reads DRAM", ha="center", fontsize=10.5, color=C["dram"]); axs[1].text(4, 630, "reader reads CXL", ha="center", fontsize=10.5, color=C["cxl"])
    save(fig, "f06_cxl_reader", [p, rc], "Hardware measurement, c28; left: 2026-10-10 (medians of 5); right: 2026-10-06 (medians of 3), copy threads on CCDs 0–1")

# ---------------------------------------------------------------- F7 throttled DRAM + Optane
def f_throttle_optane():
    l2 = {r["tag"]: r for r in csv.DictReader(open(os.path.join(E, "2026-10-10-lmcache-kv-traffic", "layer2", "summary.csv")))}
    th = {r["tag"]: r for r in csv.DictReader(open(os.path.join(E, "2026-10-11-throttled-dram-baseline", "summary.csv")))}
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[1.3, 1]))
    cfgs = [("Adam step\n8B 8×", "opt", "8b-8x"), ("PageRank\n8B 8×", "pr", "8b-8x"), ("Adam step\n70B 4×", "opt", "70b-4x"), ("PageRank\n70B 4×", "pr", "70b-4x")]
    series = {"KV tier in DRAM": [float(l2[f"{n}-{c}-dram"]["slowdown_pct"]) for _, n, c in cfgs],
              "DRAM, writes capped at 48 GB/s": [float(th[f"{n}-{c}-dramcap48"]["slowdown_pct"]) for _, n, c in cfgs],
              "KV tier in CXL": [float(l2[f"{n}-{c}-cxl"]["slowdown_pct"]) for _, n, c in cfgs]}
    bars(axs[0], [c[0] for c in cfgs], series, [C["dram"], C["dram"], C["cxl"]], [None, "//", None], fmt="{:.1f}", label_fs=9, ylabel="neighbour slowdown, %", legend="upper left")
    axs[0].set_title("Emulated KV writes: capping DRAM does not protect", fontsize=12); axs[0].set_ylim(-2, 30)
    om = membench(os.path.join(E, "2026-10-06-optane-control", "matrix.csv")); idle = om["ro-idle"]["bw"]; oa = membench(os.path.join(E, "2026-10-06-optane-control", "aggressor.csv"))
    items = [("DRAM\nNT", "rw-stream-write-nt-node1-w4", "wo-nt-node1-w4", C["dram"], None), ("Optane\nNT", "rw-stream-write-nt-node3-w4", "wo-nt-node3-w4", C["pm"], None),
             ("DRAM\nplain", "rw-stream-write-node1-w4", "wo-plain-node1-w4", C["dram"], "//"), ("Optane\nplain", "rw-stream-write-node3-w4", "wo-plain-node3-w4", C["pm"], "//")]
    vals = [om[t]["bw"] for _, t, _, _, _ in items]
    b = axs[1].bar(range(4), vals, color=[i[3] for i in items], hatch=[i[4] for i in items], edgecolor="white", width=0.65)
    for r, (nm, t, ta, _, _) in zip(b, items): axs[1].annotate(f"{om[t]['bw']:.1f}\nwriters {oa[ta]['bw']:.1f}", (r.get_x() + r.get_width() / 2, om[t]["bw"]), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=9.5)
    axs[1].axhline(idle, color=C["muted"], ls="--", lw=1); axs[1].text(3.45, idle + 0.6, f"reader alone {idle:.1f}", ha="right", fontsize=9.5, color=C["muted"])
    axs[1].set_xticks(range(4)); axs[1].set_xticklabels([i[0] for i in items], fontsize=10.5); axs[1].set_ylabel("DRAM reader, GiB/s"); axs[1].set_ylim(0, 50); axs[1].set_xlabel("4 writer threads, same socket (rates in GiB/s)")
    axs[1].set_title("c35 Optane: writes to PM hurt DRAM readers", fontsize=12)
    save(fig, "f07_throttle_optane", ["2026-10-10-lmcache-kv-traffic/layer2/summary.csv", "2026-10-11-throttled-dram-baseline/summary.csv", "2026-10-06-optane-control/matrix.csv", "2026-10-06-optane-control/aggressor.csv"],
         "Left: host memory traffic emulation on c28, one run per cell (2026-10-10/11). Right: hardware measurement on c35, socket 1, medians of 3 (2026-10-11)")

# ---------------------------------------------------------------- F8 real KV traffic
def f_real_kv():
    d = os.path.join(E, "2026-10-10-lmcache-kv-traffic", "layer1"); txt = rd(f"{d}/summary.txt")
    blocks = re.split(r"^## ", txt, flags=re.M)[1:]; R = {}
    for b in blocks:
        name = b.split()[0]; m = re.search(r"GPU->host \(KV stores\): ([\d.]+) GB payload, mean ([\d.]+) GB/s", b); bu = re.search(r"bursts: (\d+); duration p50 (\d+) ms.*?bytes p50 ([\d.]+) GB.*?peak bin p50 ([\d.]+) GB/s.*?gap p50 ([\d.]+) s", b)
        ld = re.search(r"host->GPU \(KV loads\): ([\d.]+) GB payload, mean ([\d.]+) GB/s", b); ac = re.search(r"achieved: ([\d.]+) requests/s, (\d+) prompt tokens/s", b); tt = re.search(r"TTFT p50 ([\d.]+) s p90 ([\d.]+) p99 ([\d.]+)", b)
        if m and bu and ac: R[name] = dict(store=float(m[2]), load=float(ld[2]) if ld else 0, nb=int(bu[1]), dur=int(bu[2]), bytes=float(bu[3]), peak=float(bu[4]), gap=float(bu[5]), req=float(ac[1]), tok=int(ac[2]), ttft=(float(tt[1]), float(tt[3])) if tt else None)
    runs = [("conversation\n0.08×, normal", "normal-conv-v2"), ("tool agent\n0.08×, normal", "normal-tool-v2"), ("conversation\n0.2×, saturated", "sat-alone")]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[1, 1.4]))
    bars(axs[0], [f"{n}\n{R[k]['tok']:,} tok/s" for n, k in runs], {"KV stores (GPU → host)": [R[k]["store"] for _, k in runs], "KV loads (host → GPU)": [R[k]["load"] for _, k in runs]}, [C["dram"], C["cxl"]], fmt="{:.3f}", ylabel="mean rate on the GPU link, GB/s", legend="upper left")
    axs[0].set_title("Real serving: mean KV traffic", fontsize=12); axs[0].set_ylim(0, 0.2); axs[0].tick_params(axis="x", labelsize=10)
    # a 3 s excerpt of the 5 ms bins of the saturated run
    p = glob.glob(f"{d}/sat-alone-pcie.txt*")[0]; M = {}
    for l in open(f"{d}/sat-alone-meta.txt"): f = l.split(); M[f[1]] = int(f[2])
    t0 = M["serve_start"] + 120_000_000_000; Cl = [(int(a), int(b) / 1.12 / 1e9 / 0.005) for a, b, c in re.findall(r"^C (\d+) (\d+) (\d+)$", rdx(p), re.M) if t0 <= int(a) < t0 + 3_000_000_000]
    axs[1].plot([(t - t0) / 1e9 for t, _ in Cl], [v for _, v in Cl], color=C["dram"], lw=1.2)
    axs[1].set_xlabel("time, s (3 s of the saturated run)"); axs[1].set_ylabel("GPU → host, GB/s per 5 ms bin"); axs[1].set_title(f"Store bursts: {R['sat-alone']['bytes']:.3f} GB each, ~{R['sat-alone']['dur']} ms, every ~{R['sat-alone']['gap']:.2f} s", fontsize=12)
    axs[1].set_ylim(0, 13)
    save(fig, "f08_real_kv", [f"{d}/summary.txt", p, f"{d}/sat-alone-meta.txt"], "Real application: vLLM 0.31 + LMCache 0.5.5, Qwen2.5-1.5B on the RTX 4060 Ti (PCIe 4.0 ×8), c28, 2026-10-10/11; NVML cumulative counters, payload = counter / 1.12")
    return R

# ---------------------------------------------------------------- F9 emulation offered/achieved/backlog, F10 neighbours
def f_emulation():
    l2 = {r["tag"]: r for r in csv.DictReader(open(os.path.join(E, "2026-10-10-lmcache-kv-traffic", "layer2", "summary.csv")))}
    cfgs = ["8b-1x", "8b-4x", "8b-8x", "70b-1x", "70b-4x", "70b-8x"]; lab = [c.replace("b-", "B\n").replace("x", "×") for c in cfgs]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[1.3, 1]))
    series = {"offered": [float(l2[f"none-{c}-dram"]["target_GBps"]) for c in cfgs], "achieved, tier in DRAM": [float(l2[f"none-{c}-dram"]["store_GBps"]) for c in cfgs], "achieved, tier in CXL": [float(l2[f"none-{c}-cxl"]["store_GBps"]) for c in cfgs]}
    bars(axs[0], lab, series, [C["ctrl"], C["dram"], C["cxl"]], fmt="{:.0f}", ylabel="KV store rate, GB/s (mean)", legend="upper left"); axs[0].set_title("Offered vs achieved store rate", fontsize=12)
    axs[0].axhline(46.5, color=C["cxl"], ls="--", lw=1); axs[0].text(2.0, 48.5, "CXL write ceiling ~46 GB/s", ha="center", fontsize=9.5, color=C["cxl"])
    bl = {"tier in DRAM": [max(0.1, float(l2[f"none-{c}-dram"]["backlog_max_GB"])) for c in cfgs], "tier in CXL": [max(0.1, float(l2[f"none-{c}-cxl"]["backlog_max_GB"])) for c in cfgs]}
    bars(axs[1], lab, bl, [C["dram"], C["cxl"]], fmt="{:.0f}", ylabel="largest backlog, GB (log)", legend="upper left"); axs[1].set_yscale("log"); axs[1].set_ylim(0.1, 5e4); axs[1].set_title("Backlog of unwritten KV", fontsize=12)
    for i, c in enumerate(cfgs):
        lt = float(l2[f"none-{c}-cxl"]["late_max_ms"]) / 1000
        if lt >= 1: axs[1].text(i + 0.2, float(l2[f"none-{c}-cxl"]["backlog_max_GB"]) * 3.2, f"{lt:.0f} s late", ha="center", fontsize=9, color=C["cxl"])
    save(fig, "f09_emulation_rate", ["2026-10-10-lmcache-kv-traffic/layer2/summary.csv"], "Host memory traffic emulation (CPU non-temporal stores, not GPU DMA), c28, conversation trace, 200 GiB tier, one run per cell, 2026-10-10/11")
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.0), sharey=True); lab = [c.replace("b-", "B ").replace("x", "×") for c in cfgs]
    for ax, (nm, key) in zip(axs, [("DRAM reader, 8 threads", "reader"), ("PageRank, 80 threads", "pr"), ("Adam step, 80 threads", "opt")]):
        bars(ax, lab, {"KV tier in DRAM": [float(l2[f"{key}-{c}-dram"]["slowdown_pct"]) for c in cfgs], "KV tier in CXL": [float(l2[f"{key}-{c}-cxl"]["slowdown_pct"]) for c in cfgs]}, [C["dram"], C["cxl"]], fmt="{:.0f}", label_fs=9, legend="upper left" if ax is axs[0] else False, rot=30)
        ax.set_title(nm, fontsize=12)
    axs[0].set_ylabel("neighbour slowdown, %"); axs[0].set_ylim(-3, 70)
    save(fig, "f10_emulation_neighbors", ["2026-10-10-lmcache-kv-traffic/layer2/summary.csv"], "Host memory traffic emulation, c28; neighbour on cpus 0–79, its own 60 s window before the traffic as baseline; one run per cell, 2026-10-10/11")

# ---------------------------------------------------------------- F11 KV capacity
def f_kv_capacity():
    p = os.path.join(E, "2026-10-09-kv-capacity-characterization", "kv-capacity.csv"); rows = list(csv.DictReader(open(p)))
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2), sharey=True)
    marks = [(242.5, "dax0.0\n242.5", 1.02), (512, "CXL pair\n512", 1.16), (768, "+256 DRAM\n768", 1.02), (1024, "1 TiB", 1.16)]
    for ax, model in zip(axs, ["Llama-3.1-8B", "Llama-3.1-70B"]):
        for tr, col, mk in [("conversation", C["dram"], "o"), ("toolagent", C["budget"], "s"), ("synthetic", C["split"], "^")]:
            pts = sorted((float(r["capacity_gib"]), float(r["lru_hit_share"])) for r in rows if r["trace"] == tr and r["model"] == model)
            ax.plot([x for x, _ in pts], [y for _, y in pts], marker=mk, ms=5, color=col, label=tr, lw=1.8)
        for x, t, yy in marks: ax.axvline(x, color="#bbbbbb", lw=0.8, ls=":"); ax.text(x, yy, t, ha="center", va="bottom", fontsize=8.5, color=C["muted"])
        ax.set_xscale("log"); ax.set_xlabel("host KV cache capacity, GiB (LRU)"); ax.set_title(model, fontsize=12, pad=42); ax.set_xlim(14, 4500)
    axs[0].set_ylabel("share of reuses served from host memory"); axs[0].legend(loc="upper left"); axs[0].set_ylim(0, 1.0)
    save(fig, "f11_kv_capacity", [p], "Trace simulation (exact LRU stack distances on Mooncake traces, 512-token blocks; KV bytes/token from the model configs, bf16; no GPU prefix cache in front), 2026-10-09")

# ---------------------------------------------------------------- F12 real LMCache 2a
def f_real_lmcache():
    p = os.path.join(E, "2026-10-11-capacity-matched-kv", "real", "summary.txt"); txt = rd(p); R = {}
    for b in re.split(r"^## ", txt, flags=re.M)[1:]:
        name = b.split()[0]; hit = re.search(r"chunks found (\d+) of (\d+) = ([\d.]+)", b); tt = re.search(r"TTFT p50 ([\d.]+) p90 ([\d.]+) p99 ([\d.]+)", b); l1 = re.search(r"L1 used: mean ([\d.]+) GiB, max ([\d.]+) of (\d+)", b)
        R[name] = dict(hit=float(hit[3]), ttft=(float(tt[1]), float(tt[2]), float(tt[3])), l1=(float(l1[1]), float(l1[2])))
    pools = re.search(r"hybrid pools.*DRAM mean ([\d.]+) max ([\d.]+) GiB, DAX mean ([\d.]+) max ([\d.]+)", txt)
    cfgs = [("DRAM\n40 GiB", "dram", C["dram"], None), ("hybrid\n20 + 20 GiB", "hybrid", C["dram"], "//"), ("CXL\n40 GiB", "dax", C["cxl"], None)]
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.0))
    for ax, (title, key, fmt, lim) in zip(axs, [("LMCache chunk hit share", "hit", "{:.3f}", 0.12), ("TTFT p50 / p99, s", "ttft", "{:.1f}", 45), ("L1 occupancy mean / max, GiB", "l1", "{:.1f}", 48)]):
        if key == "hit":
            b = ax.bar(range(3), [R[c[1]]["hit"] for c in cfgs], color=[c[2] for c in cfgs], hatch=[c[3] for c in cfgs], edgecolor="white", width=0.6)
            for r, c in zip(b, cfgs): ax.annotate(fmt.format(R[c[1]]["hit"]), (r.get_x() + r.get_width() / 2, R[c[1]]["hit"]), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=11)
        else:
            idx = (0, 2) if key == "ttft" else (0, 1); w = 0.36
            for j, (ii, nm) in enumerate(zip(idx, ["p50", "p99"] if key == "ttft" else ["mean", "max"])):
                vals = [R[c[1]][key][ii] for c in cfgs]
                b = ax.bar([x + (j - 0.5) * w for x in range(3)], vals, w * 0.92, color=[c[2] for c in cfgs], hatch=[c[3] for c in cfgs], edgecolor="white", alpha=1 if j == 0 else 0.55)
                for r, v in zip(b, vals): ax.annotate(f"{nm} {fmt.format(v)}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=9)
        ax.set_xticks(range(3)); ax.set_xticklabels([c[0] for c in cfgs], fontsize=9.5); ax.set_title(title, fontsize=12); ax.set_ylim(0, lim)
    axs[2].axhline(32, color=C["muted"], ls="--", lw=1); axs[2].text(1, 37.5, "80% eviction watermark = 32 GiB", ha="center", fontsize=9, color=C["muted"])
    if pools: axs[2].text(1, 44, f"hybrid pools: DRAM {float(pools[1]):.1f} / CXL {float(pools[3]):.1f} GiB", ha="center", fontsize=9, color=C["ink"])
    save(fig, "f12_real_lmcache", [p], "Real application: vLLM 0.31 + LMCache 0.5.5 multi-process, Qwen2.5-1.5B, RTX 4060 Ti, c28; conversation trace 0–180 s at 0.08× (556 requests), one run per configuration, 2026-10-12")

# ---------------------------------------------------------------- F13 admission vs migration (2b), F14 controller limit
def load_2b():
    return list(csv.DictReader(open(os.path.join(E, "2026-10-11-capacity-matched-kv", "emulation", "summary.csv"))))
def f_admission_migration():
    rows = load_2b(); get = lambda nb, cfg, pol: next(r for r in rows if r["neighbor"] == nb and r["policy"] == pol and f"{r['model']}-{r['speed']}" == cfg)
    pols = [("all DRAM", "dram", C["dram"], None), ("LMCache-like\n(DRAM-first)", "lmcache", C["dram"], "//"), ("static split 32%", "split", C["split"], None), ("CXL-first", "cxlfirst", C["cxl"], None),
            ("CXL-first + loan\n(controller)", "borrowtier", C["ctrl"], None), ("+ global LRU", "borrowglob", C["ctrl"], ".."), ("+ migration", "borrowmig", C["ctrl"], "//"), ("all CXL", "cxl", C["cxl"], "//")]
    fig, axs = plt.subplots(2, 2, figsize=(11.5, 6.4), sharex="col")
    for j, cfg in enumerate(["8b-4x", "8b-8x"]):
        ax = axs[0][j]; vals = [float(get("none", cfg, p)["hit_share"]) for _, p, _, _ in pols]
        b = ax.bar(range(len(pols)), vals, color=[p[2] for p in pols], hatch=[p[3] for p in pols], edgecolor="white", width=0.65)
        for r, v in zip(b, vals): ax.annotate(f"{v:.3f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=9.5)
        ax.set_title(f"{cfg.replace('b-', 'B ').replace('x', '×')} — hit share (no neighbour)", fontsize=12); ax.set_ylim(0, 0.235)
        if j == 0: ax.set_ylabel("hit share of reuses")
        ax = axs[1][j]; v50 = [float(get("opt", cfg, p)["slow"]) for _, p, _, _ in pols]; v99 = [float(get("opt", cfg, p)["tail"]) for _, p, _, _ in pols]
        w = 0.38
        b1 = ax.bar([x - w / 2 for x in range(len(pols))], v50, w * 0.92, color=[p[2] for p in pols], hatch=[p[3] for p in pols], edgecolor="white")
        b2 = ax.bar([x + w / 2 for x in range(len(pols))], v99, w * 0.92, color=[p[2] for p in pols], hatch=[p[3] for p in pols], edgecolor="white", alpha=0.5)
        for r, v in zip(b1, v50): ax.annotate(f"{v:.1f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8.5)
        for r, v in zip(b2, v99): ax.annotate(f"{v:.0f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8.5, color=C["muted"])
        ax.set_xticks(range(len(pols))); ax.set_xticklabels([p[0] for p in pols], fontsize=8.5, rotation=30, ha="right"); ax.set_title("Adam step slowdown: median (solid), p99 (pale)", fontsize=11); ax.set_ylim(0, 36)
        if j == 0: ax.set_ylabel("slowdown, %")
    save(fig, "f13_admission_migration", ["2026-10-11-capacity-matched-kv/emulation/summary.csv"], "Host memory traffic emulation (kvemu2), c28, 200 GiB effective capacity for every policy, conversation trace, one run per cell, 2026-10-11/12")
def f_controller_limit():
    rows = load_2b(); R = {r["tag"]: r for r in rows}
    pts = [("CXL-first\n(controller lends 0)", "opt-70b-4x-cxlfirst"), ("split: 6 GB/s\nto DRAM", "opt-70b-4x-split24"), ("split: 10 GB/s", "opt-70b-4x-split40"), ("split: 16 GB/s", "opt-70b-4x-split")]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2))
    x = [float(R[t]["store_dram"]) for _, t in pts]
    axs[0].plot(x, [float(R[t]["slow"]) for _, t in pts], marker="o", color=C["split"], label="Adam median"); axs[0].plot(x, [float(R[t]["tail"]) for _, t in pts], marker="s", color=C["split"], ls="--", label="Adam p99")
    axs[0].axhline(7, color=C["pm"], lw=1.2, ls=":"); axs[0].text(0.2, 7.4, "7% target", color=C["pm"], fontsize=10)
    for xi, (_, t) in zip(x, pts): axs[0].annotate(f"{float(R[t]['tail']):.1f}", (xi, float(R[t]["tail"])), xytext=(4, 4), textcoords="offset points", fontsize=9.5)
    axs[0].set_xlabel("DRAM write rate, GB/s (static split, 70B 4×)"); axs[0].set_ylabel("Adam step slowdown, %"); axs[0].legend(loc="upper left"); axs[0].set_ylim(0, 15); axs[0].set_title("What Adam tolerates", fontsize=12)
    b = axs[1].bar(range(4), [float(R[t]["backlog_max"]) for _, t in pts], color=[C["cxl"], C["split"], C["split"], C["split"]], width=0.6)
    for r, (_, t) in zip(b, pts): axs[1].annotate(f"{float(R[t]['backlog_max']):.0f} GB\n{float(R[t]['late_max']) / 1000:.1f} s late", (r.get_x() + r.get_width() / 2, float(R[t]["backlog_max"])), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=9.5)
    axs[1].set_xticks(range(4)); axs[1].set_xticklabels([p[0] for p in pts], fontsize=9.5); axs[1].set_ylabel("largest backlog, GB"); axs[1].set_ylim(0, 950); axs[1].set_title("Offered 52 GB/s, CXL takes ~46: the deficit is 6 GB/s", fontsize=12)
    save(fig, "f14_controller_limit", ["2026-10-11-capacity-matched-kv/emulation/summary.csv (opt-70b-4x-*)"], "Host memory traffic emulation, c28, 70B 4× next to the 80-thread Adam step, one run per point, 2026-10-12. The controller's probe reads Adam's own DRAM load as 'busy' (275 ns vs 127 ns idle) and lends nothing")

# ---------------------------------------------------------------- F16 calibration sweeps, F17 evaluation (bga)
def f_bga_calibration():
    p = os.path.join(E, "2026-10-12-budget-gated-admission", "calibration", "summary.csv"); rows = list(csv.DictReader(open(p)))
    fig, axs = plt.subplots(2, 3, figsize=(11.5, 6.6))
    for j, cfg in enumerate(["8b-4x", "8b-8x", "70b-4x"]):
        for fam, col, mk in [("split", C["split"], "o"), ("budget", C["budget"], "s")]:
            rs = sorted([r for r in rows if re.match(rf"opt-{cfg}-{fam}[\d.]+$", r["tag"])], key=lambda r: float(r["store_dram"]))
            x = [float(r["store_dram"]) for r in rs]
            axs[0][j].plot(x, [float(r["slow_p99"]) for r in rs], marker=mk, color=col, label=f"{'static split' if fam == 'split' else 'budget-gated'}")
            for r in rs: axs[0][j].annotate(r["tag"].split("-")[-1].replace("split", "").replace("budget", "") + ("%" if fam == "split" else ""), (float(r["store_dram"]), float(r["slow_p99"])), xytext=(3, -11 if fam == "split" else 4), textcoords="offset points", fontsize=8, color=col)
            y2 = [float(r["hit_share"]) for r in rs] if cfg != "70b-4x" else [float(r["backlog_max"]) for r in rs]
            axs[1][j].plot(x, y2, marker=mk, color=col, label=f"{'static split' if fam == 'split' else 'budget-gated'}")
        axs[0][j].axhline(7, color=C["pm"], ls=":", lw=1.2); axs[0][j].text(0.3, 7.4, "7% SLO", color=C["pm"], fontsize=9.5)
        axs[0][j].set_title(cfg.replace("b-", "B ").replace("x", "×") + " next to Adam", fontsize=12); axs[0][j].set_ylim(0, 23)
        axs[1][j].set_xlabel("mean DRAM write rate, GB/s")
        if cfg == "70b-4x": axs[1][j].set_yscale("log"); axs[1][j].set_ylim(8, 600)
    axs[0][0].set_ylabel("Adam p99 slowdown, %"); axs[1][0].set_ylabel("hit share of reuses"); axs[1][2].set_ylabel("largest backlog, GB (log)"); axs[0][0].legend(loc="upper left")
    for j in range(2): axs[1][j].set_ylim(0.14, 0.215)
    save(fig, "f16_bga_calibration", [p], "Host memory traffic emulation, c28, calibration segment (trace 2040 s on), 60 s quiet window, one run per point, 2026-10-12. Labels: split share / budget GB/s")
def f_bga_evaluation():
    p = os.path.join(E, "2026-10-12-budget-gated-admission", "evaluation", "summary.csv"); rows = list(csv.DictReader(open(p)))
    pols = [("static split", "split", C["split"], None), ("budget-gated", "budget", C["budget"], None), ("controller", "borrowtier", C["ctrl"], None), ("+ migration", "borrowmig", C["ctrl"], "//"), ("CXL-first", "cxlfirst", C["cxl"], None)]
    cfgs = ["8b-4x", "8b-8x", "70b-4x"]; nreps = {}
    def agg(nb, cfg, pol, key):
        v = [float(r[key]) for r in rows if re.match(rf"{nb}-{cfg}-{pol}-r\d+$", r["tag"])]
        nreps[(nb, cfg, pol)] = len(v); return (st.mean(v), (max(v) - min(v)) / 2 if len(v) > 1 else 0) if v else (float("nan"), 0)
    fig, axs = plt.subplots(2, 2, figsize=(11.5, 6.6), sharex="col")
    for i, nb in enumerate(["opt", "reader"]):
        for j, (key, yl) in enumerate([("hit_share", "hit share of reuses"), ("slow_p99", "neighbour p99 slowdown, %")]):
            ax = axs[j][i]; lab = [c.replace("b-", "B ").replace("x", "×") for c in cfgs]
            series = {nm: [agg(nb, c, pol, key)[0] for c in cfgs] for nm, pol, _, _ in pols}; errs = {nm: [agg(nb, c, pol, key)[1] for c in cfgs] for nm, pol, _, _ in pols}
            bars(ax, lab, series, [p_[2] for p_ in pols], [p_[3] for p_ in pols], fmt="{:.3f}" if key == "hit_share" else "{:.1f}", label_fs=8.5, legend="upper right" if (i, j) == (0, 0) else False, yerr=errs, vlabels=(key == "hit_share"))
            if key == "slow_p99": ax.axhline(7, color=C["pm"], ls=":", lw=1.2); ax.set_ylim(0, 11)
            else: ax.set_ylim(0.1, 0.26)
            if i == 0: ax.set_ylabel(yl)
            if j == 0: ax.set_title(("next to the Adam step (80 threads)" if nb == "opt" else "next to the DRAM reader (8 threads)"), fontsize=12)
    n = sorted(x for x in set(nreps.values()) if x)
    save(fig, "f17_bga_evaluation", [p], f"Host memory traffic emulation, c28, evaluation segment (trace 600 s on), settings from the independent calibration, 2026-10-12/13. Bars = mean of {'–'.join(str(x) for x in n)} independent runs per cell, error bars = half the range; 70B 4× hit shares not comparable (overload)")
    return nreps

# ---------------------------------------------------------------- F18 depth sweep, F19 varying + long run (when present)
def f_bga_depth():
    d = os.path.join(E, "2026-10-12-budget-gated-admission"); pd = f"{d}/depth/summary.csv"
    if not os.path.exists(pd): print("depth sweep not available yet"); return False
    cal = list(csv.DictReader(open(f"{d}/calibration/summary.csv"))); dep = list(csv.DictReader(open(pd)))
    rows = {}
    for r in cal:
        m = re.match(r"opt-(8b-\dx)-budget(\d+)$", r["tag"])
        if m: rows[(m[1], 1, int(m[2]))] = r
    for r in dep:
        m = re.match(r"opt-(8b-\dx)-d(\d+)-budget(\d+)$", r["tag"])
        if m: rows[(m[1], int(m[2]), int(m[3]))] = r
    fig, axs = plt.subplots(2, 4, figsize=(11.5, 6.4))
    cols = {1: C["budget"], 2: "#7fbf7b", 4: "#2b6e2b", 8: "#163c16"}
    for i, cfg in enumerate(["8b-4x", "8b-8x"]):
        for depth in (1, 2, 4, 8):
            bs = sorted(b for (c, dd, b) in rows if c == cfg and dd == depth and b in (8, 16, 32))
            if not bs: continue
            rs = [rows[(cfg, depth, b)] for b in bs]
            for j, (key, yl) in enumerate([("hit_share", "hit share"), ("budget_util_active", "budget utilization"), ("dram_peak20", "DRAM 20 ms peak, GB/s"), ("slow_p99", "Adam p99 slowdown, %")]):
                ax = axs[i][j]; ax.plot(bs, [float(r[key]) for r in rs], marker="o", color=cols[depth], label=f"depth {depth}")
                ax.set_xticks([8, 16, 32]); ax.set_xlabel("budget, GB/s" if i == 1 else ""); ax.set_title(f"{cfg.replace('b-', 'B ').replace('x', '×')}: {yl}", fontsize=11)
                if key == "slow_p99": ax.axhline(7, color=C["pm"], ls=":", lw=1.2)
    axs[0][0].legend(loc="lower right", fontsize=9)
    save(fig, "f18_bga_depth", [f"{d}/calibration/summary.csv", pd], "Host memory traffic emulation, c28, calibration segment next to the Adam step, one run per point (depth 1 = calibration runs), 2026-10-12/13")
    return True
def f_bga_varying():
    d = os.path.join(E, "2026-10-12-budget-gated-admission"); pv, pl = f"{d}/varying/summary.csv", f"{d}/longrun/summary.csv"
    if not (os.path.exists(pv) and os.path.exists(pl)): print("varying / long run not available yet"); return False
    V = list(csv.DictReader(open(pv))); L = {r["tag"]: r for r in csv.DictReader(open(pl))}
    pols = [("static split", "split", C["split"], None), ("budget, fixed", "budget", C["budget"], None), ("budget, oracle", "oracle", C["budget"], "//"), ("controller", "borrowtier", C["ctrl"], None), ("+ migration", "borrowmig", C["ctrl"], "//"), ("CXL-first", "cxlfirst", C["cxl"], None)]
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.2))
    def agg(cfg, pol, key):
        v = [float(r[key]) for r in V if re.match(rf"{cfg}-{pol}-r\d+$", r["tag"])]; return (st.mean(v), (max(v) - min(v)) / 2 if len(v) > 1 else 0) if v else (float("nan"), 0)
    for ax, (key, yl, fmt) in zip(axs[:2], [("hit_share", "hit share of reuses", "{:.3f}"), ("slow_p99", "Adam p99 slowdown (on phases), %", "{:.1f}")]):
        series = {nm: [agg(c, pol, key)[0] for c in ["8b-8x", "70b-4x"]] for nm, pol, _, _ in pols}; errs = {nm: [agg(c, pol, key)[1] for c in ["8b-8x", "70b-4x"]] for nm, pol, _, _ in pols}
        bars(ax, ["8B 8×", "70B 4×"], series, [p[2] for p in pols], [p[3] for p in pols], fmt=fmt, label_fs=8, legend="upper right" if key == "hit_share" else False, yerr=errs); ax.set_ylabel(yl)
        if key == "slow_p99": ax.axhline(7, color=C["pm"], ls=":", lw=1.2)
    ax = axs[2]
    for nm, tag, col in [("budget 12 GB/s", "70b-4x-budget", C["budget"]), ("split 16%", "70b-4x-split", C["split"]), ("CXL-first", "70b-4x-cxlfirst", C["cxl"])]:
        if tag in L:
            y = [float(x) for x in L[tag]["per_min_backlog"].split()]; ax.plot(range(1, len(y) + 1), y, marker="o", ms=4, color=col, label=nm)
    ax.set_xlabel("minute of the 12-minute run"); ax.set_ylabel("largest backlog in the minute, GB"); ax.set_yscale("log"); ax.legend(loc="upper left", fontsize=9); ax.set_title("70B 4× long run next to Adam", fontsize=12)
    save(fig, "f19_bga_varying", [pv, pl], "Host memory traffic emulation, c28; left/middle: Adam 30 s on / 30 s off, 2 runs per cell (error bars = half range); right: 720 s of traffic, one run each; 2026-10-13")
    return True

# ---------------------------------------------------------------- F20 checkpoint + KV
def f_ckpt_kv():
    d = os.path.join(E, "2026-10-12-checkpoint-kv-mixed"); modes = [("no checkpoint", "none", C["ctrl"]), ("uncoordinated", "64_8_full", C["cxl"]), ("rate 20 GB/s", "64_8_rate_20", C["cxl"]), ("KV priority", "64_8_kvprio", C["budget"])]
    S = {}
    for cfg in ("8b-4x", "8b-8x"):
        for nm, tag, _ in modes:
            m = re.search(r"S3 loads \d+ wait_ms p50 ([\d.]+) p99 ([\d.]+).*?service_ms p50 ([\d.]+) p99 ([\d.]+).*?extra_delay_ms p50 ([\d.]+) p90 [\d.]+ p99 ([\d.]+)", rdx(f"{d}/emulation/{cfg}-{tag}.txt"))
            S[(cfg, tag)] = tuple(float(x) for x in m.groups())
    real = rd(f"{d}/real/summary.txt"); RB = {}
    for b in re.split(r"^## ", real, flags=re.M)[1:]:
        name = b.split()[0]; rr = re.search(r"CXL reader.*?inside bursts p50 (\d+) p99 (\d+) ns, outside p50 (\d+)", b); ck = re.search(r"duration p50 ([\d.]+) s.*?busy (\d+)%", b)
        if rr: RB[name] = (int(rr[1]), int(rr[3]), float(ck[1]), int(ck[2]))
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[1.2, 1.2, 1]))
    for ax, cfg in zip(axs[:2], ["8b-4x", "8b-8x"]):
        v50 = [S[(cfg, t)][4] for _, t, _ in modes]; v99 = [S[(cfg, t)][5] for _, t, _ in modes]; w = 0.38
        b1 = ax.bar([x - w / 2 for x in range(4)], v50, w * 0.92, color=[m[2] for m in modes], edgecolor="white"); b2 = ax.bar([x + w / 2 for x in range(4)], v99, w * 0.92, color=[m[2] for m in modes], alpha=0.5, edgecolor="white")
        for r, v in zip(b1, v50): ax.annotate(f"{v:.0f}" if v >= 10 else f"{v:.1f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=9)
        for r, v in zip(b2, v99): ax.annotate(f"{v:.0f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=9, color=C["muted"])
        ax.set_yscale("log"); ax.set_ylim(1, 5e4); ax.set_xticks(range(4)); ax.set_xticklabels([m[0] for m in modes], fontsize=9.5, rotation=20, ha="right"); ax.set_title(f"{cfg.replace('b-', 'B ').replace('x', '×')} emulated: delay of a request\nby its KV loads (median solid, p99 pale)", fontsize=10.5)
    axs[0].set_ylabel("extra delay of the request, ms")
    names = [("uncoordinated", "96_8_full"), ("rate 20 GB/s", "96_8_rate_20"), ("KV priority", "96_8_kvprio")]
    ins = [RB[t][0] for _, t in names]; out = [RB[t][1] for _, t in names]
    bars(axs[2], [n for n, _ in names], {"outside bursts": out, "inside checkpoint bursts": ins}, [C["ctrl"], C["cxl"]], fmt="{:.0f}", label_fs=9.5, legend="upper left", rot=20); axs[2].set_ylim(0, 860); axs[2].tick_params(axis="x", labelsize=10)
    axs[2].set_ylabel("dependent read from CXL, ns"); axs[2].set_title("Real run: CPU reader of CXL\nduring 96 GiB checkpoints", fontsize=10.5)
    save(fig, "f20_ckpt_kv", [f"{d}/emulation/*.txt.gz (S3 lines)", f"{d}/real/summary.txt"], "Left/middle: host memory traffic emulation (kvemu3, toolagent trace, KV tier 150 GiB in CXL, 64 GiB checkpoint every 8 s), one run per cell. Right: real vLLM + LMCache run on c28, 2026-10-12")
    return S, RB


# ---------------------------------------------------------------- extra diagrams (2026-10-13)
def f_two_resources():
    fig, ax = canvas(11.5, 4.4)
    box(ax, 0.3, 2.9, 2.6, 1.0, "New KV writes\n(admission)", fc="#eaeaea"); box(ax, 0.3, 1.6, 2.6, 1.0, "Promotions / copies\n(migration)", fc="#eaeaea"); box(ax, 0.3, 0.3, 2.6, 1.0, "Checkpoint staging\n(other writers)", fc="#eaeaea")
    box(ax, 4.6, 2.5, 3.0, 1.3, "DRAM write bandwidth\n(one shared budget)", fc="#dde9f5", bold=True); box(ax, 4.6, 0.6, 3.0, 1.3, "DRAM capacity\n(a second, separate budget)", fc="#dde9f5", bold=True)
    box(ax, 8.9, 2.5, 2.4, 1.3, "Neighbour SLO\np99 slowdown ≤ 7%", fc="#fbe3e3"); box(ax, 8.9, 0.6, 2.4, 1.3, "KV hit rate\nTTFT, recompute", fc="#e3f1e1")
    for y in (3.4, 2.1, 0.8): arrow(ax, (2.9, y), (4.6, 3.15), col="#444444")
    arrow(ax, (2.9, 3.3), (4.6, 1.3), col="#888888"); arrow(ax, (2.9, 2.0), (4.6, 1.2), col="#888888")
    arrow(ax, (7.6, 3.15), (8.9, 3.15), "bounded by"); arrow(ax, (7.6, 1.25), (8.9, 1.25), "raises")
    ax.text(5.75, 4.15, "Every DRAM write draws on the same interference budget; every admitted or promoted block uses capacity.", ha="center", fontsize=10.5, color=C["muted"])
    save(fig, "f21_two_resources", ["memory: user decisions 2026-10-09 (Direction 2)"])
def f_emulation_method():
    fig, ax = canvas(11.5, 4.4)
    box(ax, 0.3, 2.6, 2.5, 1.3, "Mooncake trace\nrequest arrivals, block hashes\n× 1 / 4 / 8 speed", fc="#eaeaea", fs=10.5)
    box(ax, 3.4, 2.6, 2.7, 1.3, "Dispatcher\nlookup at arrival; a block\nis a hit only after its\nstore completes", fc="#efe9f5", fs=9.5)
    box(ax, 6.7, 2.6, 2.3, 1.3, "64 copy workers\nCCDs 6–7\n9.5 GB/s per transfer\n2048-token pieces", fc="#efe9f5", fs=9.5)
    box(ax, 9.5, 3.3, 1.8, 0.7, "DRAM tier", fc="#dde9f5"); box(ax, 9.5, 2.4, 1.8, 0.7, "CXL tier (dax0.0)", fc="#fdebd9")
    box(ax, 0.3, 0.5, 4.2, 1.3, "Neighbour on cpus 0–79\n(Adam step, PageRank, reader, llama.cpp)\nits own 60 s quiet window = baseline", fc="#fbe3e3", fs=9.5)
    box(ax, 5.0, 0.5, 6.3, 1.3, "Recorded every 20 ms: offered vs achieved rate, 20 ms peaks,\nbacklog, lateness, hit share, occupancy;\nneighbour step times / bandwidth samples; cxlpathd probe log", fc="#f7f7f7", fs=9.5)
    arrow(ax, (2.8, 3.25), (3.4, 3.25)); arrow(ax, (6.1, 3.25), (6.7, 3.25)); arrow(ax, (9.0, 3.4), (9.5, 3.65)); arrow(ax, (9.0, 3.1), (9.5, 2.75))
    ax.text(5.75, 4.15, "Host memory traffic emulation: CPU non-temporal stores from a cache-resident source, calibrated on the real runs. Not GPU DMA.", ha="center", fontsize=10.5, color=C["muted"])
    save(fig, "f22_emulation_method", ["benchmarks/memory/kvemu2.c", "benchmarks/memory/run_exp2b.py"])
def f_direction():
    fig, ax = canvas(11.5, 4.6)
    items = [("Write admission\nbudget-gated,\nper tier", "emulated policy", "#e3f1e1"), ("Capacity\nmanagement\nexclusive tiers,\nper-tier LRU", "emulated;\nLMCache real", "#e3f1e1"),
             ("Safe bandwidth\nestimation\nonline budget B", "calibration only;\nonline = proposal", "#fbe3e3"), ("Migration\nwhen it pays\ncalm-time moves", "minimal policy,\nemulated", "#fdebd9"),
             ("Cross-writer\ncoordination\ncheckpoint + KV\non one budget", "proposal,\nnot built", "#fbe3e3")]
    for i, (t, st_, fc) in enumerate(items):
        x = 0.3 + i * 2.25; box(ax, x, 2.0, 2.05, 1.5, t, fc=fc, fs=10); ax.text(x + 1.025, 1.55, st_, ha="center", va="top", fontsize=9.5, color=C["muted"])
    box(ax, 2.0, 3.9, 7.5, 0.6, "Interference-aware capacity and bandwidth management for DRAM/CXL memory", fc="#efe9f5", fs=12.5, bold=True)
    for i in range(5): arrow(ax, (2.0 + 0.8 + i * 1.5, 3.9), (0.3 + i * 2.25 + 1.025, 3.5), col="#888888")
    ax.text(5.75, 0.45, "Two budgets: DRAM write bandwidth (one shared budget) and DRAM capacity. CXL stays the default home of bulk writes.", ha="center", fontsize=10.5, color=C["muted"])
    save(fig, "f23_direction", ["this deck (proposal)"])

if __name__ == "__main__":
    f_drain_cliff(); f_original_core(); f_arch_original(); f_unified_pool(); f_budget_design(); f_topology(); f_cxl_reader(); f_throttle_optane(); f_real_kv(); f_emulation()
    f_kv_capacity(); f_real_lmcache(); f_admission_migration(); f_controller_limit(); f_bga_calibration(); f_bga_evaluation(); f_bga_depth(); f_bga_varying(); f_ckpt_kv()
    f_two_resources(); f_emulation_method(); f_direction()
    with open(os.path.join(OUT, "SOURCES.md"), "w") as f:
        f.write("# Figure → data sources (all under experimental_results/ unless a path is given)\n\n| figure | source files |\n|---|---|\n")
        for k, v in SOURCES.items(): f.write(f"| {k} | " + "; ".join(x.replace(E + "/", "") for x in v) + " |\n")
    print("done")
