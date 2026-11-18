#!/usr/bin/env python3
"""Figures of the RQ1 progress deck of 2026-10-20 (docs/slides/SLIDES_2026-10-20-rq1-progress.pptx).
Every data figure is drawn from the raw result files in experimental_results/ (nothing typed in by hand); the two
schematic figures (f01 overview, f02 left panel) carry no measured numbers except what f02's right panel reads.
Writes docs/slides/2026-10-20-rq1-progress/figs/<name>.png|.svg and figs/SOURCES.md (figure -> raw files).
Colours: matplotlib's default cycle, fixed per meaning (conversation trace C0, tool-agent trace C2, synthetic C4;
LRU C7, SLRU C1, learned / signal policies C2, cost C3, oracle black; DRAM C1, CXL C0), white background.
usage: scripts/figs_deck_2026-10-20.py [repo_root]   (runs in ~10 s)"""
import csv, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
E = os.path.join(ROOT, "experimental_results")
OUT = os.path.join(ROOT, "docs", "slides", "2026-10-20-rq1-progress", "figs"); os.makedirs(OUT, exist_ok=True)   # docs/slides is local-only (gitignored)
TR = {"conversation": ("conversation (chat)", "C0"), "toolagent": ("tool agent", "C2"), "synthetic": ("synthetic", "C4")}
PC = {"lru": "C7", "slru": "C1", "learn": "C2", "cost": "C3", "oracle": "black", "dram": "C1", "cxl": "C0"}
plt.rcParams.update({"font.size": 12, "axes.titlesize": 12.5, "axes.labelsize": 12, "legend.fontsize": 10.5, "xtick.labelsize": 11, "ytick.labelsize": 11,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
                     "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.8, "axes.axisbelow": True, "legend.frameon": False, "svg.fonttype": "none"})
SOURCES = {}
D_OR = os.path.join(E, "2026-10-17-kv-reuse-oracle-study"); D_SH = os.path.join(E, "2026-10-17-kv-session-hint-study")
D_RH = os.path.join(E, "2026-10-17-rq1b-reuse-horizon"); D_AV = os.path.join(E, "2026-10-17-rq1b-agent-runtime-validation")
D_MC = os.path.join(E, "2026-10-18-rq1-misscost"); D_HL = os.path.join(E, "2026-10-18-rq1b-history-learning")
GB_PER_CHUNK = 0.0671   # 512-token block of Llama-3.1-8B = 67.1 MB (the replays' --chunk-mb)

def rows(p): return list(csv.DictReader(open(p)))
def get(rs, key="reuse_hit_share", **sel):
    for r in rs:
        if all(r[k] == str(v) for k, v in sel.items()): return float(r[key])
    raise KeyError((sel, key))
def save(fig, name, sources, note=None):
    fig.tight_layout(rect=(0, 0.05 if note else 0, 1, 1))
    if note: fig.text(0.005, 0.006, note, fontsize=9, color="#666666", ha="left", va="bottom")
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200, bbox_inches="tight"); fig.savefig(os.path.join(OUT, name + ".svg"), bbox_inches="tight"); plt.close(fig)
    SOURCES[name] = sources; print("wrote", name)
def label_bars(ax, bars, fmt="{:.2f}", fs=9, rot=0):
    for r in bars:
        v = r.get_height()
        ax.annotate(fmt.format(v), (r.get_x() + r.get_width() / 2, v if v >= 0 else 0), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=fs, rotation=rot)
def box(ax, x, y, w, h, text, fc="#f3f3f3", ec="#999999", fs=11, bold=False, color="#222222", r=0.08):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=color, linespacing=1.3)
def arrow(ax, x0, y0, x1, y1, color="#555555"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14, color=color, lw=1.2))

# ---------------------------------------------------------------- f01 overview (schematic; the two shares are read from the characterization files)
def f01_overview():
    ch = {t: json.load(open(os.path.join(D_OR, f"characterization-{t}.json"))) for t in ("conversation", "toolagent")}
    never = [100 * ch[t]["never_share"] for t in ("conversation", "toolagent")]
    fig, ax = plt.subplots(figsize=(10.5, 4.6)); ax.set_xlim(0, 10.5); ax.set_ylim(0, 4.6); ax.axis("off")
    box(ax, 0.2, 2.55, 2.3, 1.5, "LLM serving\n(vLLM + LMCache)\nmakes KV blocks\nfor every request", fc="#eef2f7", fs=10.5)
    arrow(ax, 2.5, 3.3, 3.25, 3.3); ax.text(2.87, 3.42, "new\nblock", ha="center", va="bottom", fontsize=9.5, color="#555555")
    box(ax, 3.3, 2.1, 4.2, 2.4, "", fc="#ffffff", ec="#444444", r=0.06)
    ax.text(5.4, 4.25, "host KV cache (one pool, exclusive placement)", ha="center", va="center", fontsize=11, fontweight="bold")
    box(ax, 3.5, 2.3, 1.75, 1.6, "DRAM\n64 GiB\nfast, scarce,\nshared with others", fc="#fde7d2", ec="C1", fs=9.5)
    box(ax, 5.55, 2.3, 1.75, 1.6, "CXL\n136 GiB\nmore capacity,\nown write path", fc="#d8e6f3", ec="C0", fs=9.5)
    box(ax, 3.3, 0.25, 4.2, 1.35, "decisions for each block\nadmit or skip  ·  DRAM or CXL  ·  keep or evict  ·  move or not", fc="#f3f3f3", fs=10.5)
    arrow(ax, 5.4, 2.1, 5.4, 1.62)
    arrow(ax, 7.5, 3.6, 8.25, 3.95); arrow(ax, 7.5, 3.0, 8.25, 2.45)
    box(ax, 8.3, 3.55, 2.0, 0.85, "read again later\nhit: no recompute", fc="#e3f1e1", ec="C2", fs=10)
    box(ax, 8.3, 1.95, 2.0, 0.95, f"never read again\n{never[0]:.0f}% / {never[1]:.0f}% of blocks\n(chat / tool agent)", fc="#fbe3e3", ec="C3", fs=10)
    ax.text(5.4, 0.02, "RQ1 asks: can the cache know, early enough, which of the two a new block will be?", ha="center", va="bottom", fontsize=11, style="italic", color="#1B2A41")
    save(fig, "f01_overview", ["2026-10-17-kv-reuse-oracle-study/characterization-{conversation,toolagent}.json (never-reused shares)"])

# ---------------------------------------------------------------- f02 toy example (schematic) + real-trace reuse facts
def f02_lru_vs_oracle():
    ch = {t: json.load(open(os.path.join(D_OR, f"characterization-{t}.json"))) for t in TR}
    cap = rows(os.path.join(D_OR, "oracle-8b-capacity.csv"))
    fig = plt.figure(figsize=(14.5, 4.6)); gs = fig.add_gridspec(1, 4, width_ratios=[1.15, 1.15, 0.78, 0.78], wspace=0.42)
    seq = ["A", "B", "C", "A", "B"]
    def panel(ax, title, states, outcomes):
        ax.set_xlim(-0.6, 4.9); ax.set_ylim(-1.6, 3.4); ax.axis("off"); ax.set_title(title, fontsize=12, loc="left")
        for t, a in enumerate(seq):
            ax.text(t, 3.05, a, ha="center", va="center", fontsize=14, fontweight="bold")
            for s_ in range(2):
                v = states[t][s_]; fc = "#ffffff" if v is None else ("#e3f1e1" if outcomes[t] == "hit" and v == a else "#eef2f7")
                ax.add_patch(Rectangle((t - 0.42, 1.0 + s_ * 0.95), 0.84, 0.85, fc=fc, ec="#777777", lw=1))
                if v: ax.text(t, 1.42 + s_ * 0.95, v, ha="center", va="center", fontsize=12.5)
            col = {"hit": "C2", "miss": "C3", "skip": "#555555"}[outcomes[t]]
            ax.text(t, 0.55, {"hit": "hit", "miss": "miss", "skip": "not\nstored"}[outcomes[t]], ha="center", va="center", fontsize=10.5, color=col, fontweight="bold", linespacing=1.0)
        ax.text(-0.55, 3.05, "access", ha="right", va="center", fontsize=10, color="#555555"); ax.text(-0.55, 1.9, "cache\n(2 slots)", ha="right", va="center", fontsize=10, color="#555555")
    ax1 = fig.add_subplot(gs[0]); panel(ax1, "LRU: stores all, evicts the oldest", [("A", None), ("A", "B"), ("C", "B"), ("C", "A"), ("B", "A")], ["miss", "miss", "miss", "miss", "miss"])
    ax1.text(2, -0.25, "C pushes A out; A pushes B out.\n0 hits of 2 reuses.", ha="center", va="top", fontsize=11)
    ax2 = fig.add_subplot(gs[1]); panel(ax2, "Oracle: knows C is never read again", [("A", None), ("A", "B"), ("A", "B"), ("A", "B"), ("A", "B")], ["miss", "miss", "skip", "hit", "hit"])
    ax2.text(2, -0.25, "C is not stored (bypass); A and B stay.\n2 hits of 2 reuses, 1 write less.", ha="center", va="top", fontsize=11)
    gaps = {t: ch[t]["gap_p"][1] for t in TR}
    ax1.text(-0.55, -1.0, f"Real traces: median gap between two uses {gaps['conversation']:.0f} s (chat), {gaps['toolagent']:.0f} s (tool agent), {gaps['synthetic']:.0f} s (synthetic).\nA 200 GiB cache turns over in ~60 s: most reused blocks leave before their second use.", ha="left", va="top", fontsize=9.5, color="#555555", clip_on=False)
    # real traces: how many blocks are like C, and what that does to LRU
    short = {"conversation": "chat", "toolagent": "tool\nagent", "synthetic": "synthetic"}
    ax3 = fig.add_subplot(gs[2]); ax3.set_title("Blocks like C:\nnever read again in the trace", fontsize=11.5, loc="left")
    b = ax3.bar(range(3), [100 * ch[t]["never_share"] for t in TR], 0.62, color=[TR[t][1] for t in TR]); label_bars(ax3, b, "{:.0f}%", fs=10.5)
    ax3.set_xticks(range(3)); ax3.set_xticklabels([short[t] for t in TR]); ax3.set_ylim(0, 100); ax3.set_ylabel("% of all distinct blocks in the trace")
    ax4 = fig.add_subplot(gs[3]); ax4.set_title("Re-reads a 200 GiB LRU\nwould serve", fontsize=11.5, loc="left")
    b = ax4.bar(range(3), [100 * ch[t]["stack_within_200"] for t in TR], 0.62, color=[TR[t][1] for t in TR]); label_bars(ax4, b, "{:.0f}%", fs=10.5)
    ax4.set_xticks(range(3)); ax4.set_xticklabels([short[t] for t in TR]); ax4.set_ylim(0, 100); ax4.set_ylabel("% of all re-reads (reuse distance ≤ 200 GiB)")
    lru = [get(cap, trace=t, policy="global_lru") for t in TR]
    ax4.text(0.97, 0.97, "= LRU's reuse-hit share\n(measured " + " / ".join(f"{v:.2f}" for v in lru) + ")", ha="right", va="top", fontsize=9, color="#555555", transform=ax4.transAxes)
    save(fig, "f02_lru_vs_oracle", ["2026-10-17-kv-reuse-oracle-study/characterization-{conversation,toolagent,synthetic}.json (never_share, stack_within_200, gap_p)", "oracle-8b-capacity.csv (global_lru)"])

# ---------------------------------------------------------------- f03 oracle study
def f03_oracle():
    cap = rows(os.path.join(D_OR, "oracle-8b-capacity.csv")); onl = rows(os.path.join(D_OR, "oracle-8b-capacity-online.csv"))
    pols = [("CXL-first\n+ LRU", "cxlfirst", cap), ("static split\n+ LRU per tier", "split", cap), ("global LRU\n(one pool)", "global_lru", cap), ("SLRU 1/3\n(best online)", "slru0.33", onl),
            ("oracle, sees\n300 s ahead", "oracle_h300", cap), ("oracle, sees\nall the future", "oracle_min", cap)]
    traces = ["conversation", "toolagent"]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.7), gridspec_kw=dict(width_ratios=[1.75, 1]))
    w = 0.38
    for j, t in enumerate(traces):
        vals = [get(rs, trace=t, policy=p) for _, p, rs in pols]
        b = axs[0].bar([x + (j - 0.5) * w for x in range(len(pols))], vals, w * 0.92, color=TR[t][1], label=TR[t][0]); label_bars(axs[0], b, "{:.2f}", fs=9.5)
    axs[0].set_xticks(range(len(pols))); axs[0].set_xticklabels([p[0] for p in pols], fontsize=10); axs[0].set_ylabel("reuse-hit share (test half)"); axs[0].set_ylim(0, 1.08); axs[0].legend(loc="upper left")
    axs[0].axvspan(3.5, 5.5, color="#f3f3f3", zorder=0); axs[0].text(4.5, 1.03, "ORACLE (future known)", ha="center", fontsize=10, color="#555555"); axs[0].text(2.5, 1.03, "online policies (no future information)", ha="center", fontsize=10, color="#555555")
    axs[0].set_title("Share of re-reads served from the 200 GiB host cache (DRAM 64 + CXL 136 GiB)", fontsize=11.5, loc="left")
    wp = [("static split\n+ LRU", "split", cap), ("SLRU 1/3", "slru0.33", onl), ("oracle", "oracle_min", cap)]
    for j, t in enumerate(traces):
        vals = [(get(rs, "dram_GB", trace=t, policy=p) + get(rs, "cxl_GB", trace=t, policy=p)) / 1000 for _, p, rs in wp]
        b = axs[1].bar([x + (j - 0.5) * w for x in range(len(wp))], vals, w * 0.92, color=TR[t][1]); label_bars(axs[1], b, "{:.1f}", fs=10)
    axs[1].set_xticks(range(len(wp))); axs[1].set_xticklabels([p[0] for p in wp], fontsize=10); axs[1].set_ylabel("TB written into host memory (test half)"); axs[1].set_ylim(0, 21)
    axs[1].set_title("The oracle stores only blocks with a future read", fontsize=11.5, loc="left")
    save(fig, "f03_oracle", ["2026-10-17-kv-reuse-oracle-study/oracle-8b-capacity.csv", "oracle-8b-capacity-online.csv"])

# ---------------------------------------------------------------- f04 block-level prediction
def f04_prediction():
    ch = {t: json.load(open(os.path.join(D_OR, f"characterization-{t}.json"))) for t in ("conversation", "toolagent")}
    cap = rows(os.path.join(D_OR, "oracle-8b-capacity.csv")); onl = rows(os.path.join(D_OR, "oracle-8b-capacity-online.csv"))
    feats = [("creation", "position in request", "position\nin request"), ("creation", "continuation depth (leading old blocks)", "continuation\ndepth"),
             ("chain", "turns so far", "turns so far\nin the chat"), ("chain", "time since previous turn", "time since\nprevious turn"), ("chain", "prompt length (tokens)", "prompt length")]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.7), gridspec_kw=dict(width_ratios=[1.9, 1]))
    ax = axs[0]; x = 0; ticks = []; seps = []
    for grp, key, lab in feats:
        buckets = [bk for bk, v in ch["conversation"][grp][key].items() if v.get("n2", 0) >= 200 and bk != "0"]
        for bk in buckets:
            for t in ("conversation", "toolagent"):
                v = ch[t][grp][key].get(bk)
                if v and v.get("p2") is not None and v.get("n2", 0) >= 200: ax.plot(x, 100 * v["p2"], marker="o" if t == "conversation" else "s", color=TR[t][1], ms=7, ls="none", label=TR[t][0] if x == 0 else None)
            ticks.append((x, bk.replace(" (fresh)", "").replace(" (leading old blocks)", ""))); x += 1
        ax.text(x - 1 - (len(buckets) - 1) / 2, 48, lab, ha="center", va="top", fontsize=9.5, color="#333333"); seps.append(x - 0.5); x += 0.6
    for s in seps[:-1]: ax.axvline(s + 0.3, color="#dddddd", lw=1)
    for t in ("conversation", "toolagent"):
        base = 100 * ch[t]["again_k"]["0"]["p"]; ax.axhline(base, color=TR[t][1], ls=":", lw=1.3); ax.text(x - 0.4, base + 0.8, f"base rate {base:.0f}%", ha="right", va="bottom", fontsize=9, color=TR[t][1])
    ax.set_xticks([p for p, _ in ticks]); ax.set_xticklabels([l for _, l in ticks], fontsize=9, rotation=35, ha="right"); ax.set_ylim(0, 50); ax.set_ylabel("% of new blocks read again later"); ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.86))
    ax.set_title("Reuse probability by what is known when the block is created (test half)", fontsize=11.5, loc="left")
    ax = axs[1]
    onp = [("SLRU 1/3", "slru0.33", onl), ("reactive\npromotion", "reactive_mig", cap), ("admission filter\n(θ = 0.12)", "pred_admit", onl), ("evict by\npast-use count", "pred_evict", cap)]
    w = 0.38
    for j, t in enumerate(("conversation", "toolagent")):
        base = get(cap, trace=t, policy="split"); top = get(cap, trace=t, policy="oracle_min")
        vals = [100 * (get(rs, trace=t, policy=p) - base) / (top - base) for _, p, rs in onp]
        b = ax.bar([k + (j - 0.5) * w for k in range(len(onp))], vals, w * 0.92, color=TR[t][1], label=TR[t][0]); label_bars(ax, b, "{:.0f}%", fs=10)
    ax.axhline(50, color="C3", ls="--", lw=1.2); ax.text(len(onp) - 0.55, 52, "Gate 2: 50% of the oracle's gain", ha="right", va="bottom", fontsize=9.5, color="C3")
    ax.set_xticks(range(len(onp))); ax.set_xticklabels([p[0] for p in onp], fontsize=9.5); ax.set_ylim(-12, 62); ax.set_ylabel("share of the oracle's gain over LRU, %")
    ax.set_title("What simple online rules recover", fontsize=11.5, loc="left")
    save(fig, "f04_prediction", ["2026-10-17-kv-reuse-oracle-study/characterization-{conversation,toolagent}.json (creation / chain features, again_k)", "oracle-8b-capacity.csv", "oracle-8b-capacity-online.csv"])

# ---------------------------------------------------------------- f05 session hints (trace simulation) + real agent runs (replay of the real trace with the real events)
def f05_hints():
    sh = rows(os.path.join(D_SH, "session-hints-8b-200GiB.csv")); rh = rows(os.path.join(D_RH, "lt-k16-l1g-bg2-churn0-replay.csv"))
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw=dict(width_ratios=[1.25, 1]))
    ax = axs[0]
    pols = [("session idle\n> 300 s → evict", "session_ttl300", False), ("end event\n60 s late", "hint:delay=60", False), ("end event\n10 s late", "hint:delay=10", False), ("end event\nno delay", "hint:delay=0", False),
            ("perfect\n'continues'", "hint:mode=both", True), ("perfect, only\n≤ 300 s", "hint:mode=both,bound=300", True)]
    w = 0.38
    for j, t in enumerate(("conversation", "toolagent")):
        base = get(sh, trace=t, policy="split"); top = get(sh, trace=t, policy="oracle_min")
        vals = [100 * (get(sh, trace=t, policy=p) - base) / (top - base) for _, p, _ in pols]
        b = ax.bar([k + (j - 0.5) * w for k in range(len(pols))], vals, w * 0.92, color=TR[t][1], label=TR[t][0]); label_bars(ax, b, "{:.0f}%", fs=10)
    ax.axvspan(3.5, 5.5, color="#f3f3f3", zorder=0); ax.text(4.5, 97, "ORACLE hints", ha="center", fontsize=10, color="#555555"); ax.text(1.5, 97, "signals a system could have", ha="center", fontsize=10, color="#555555")
    ax.axhline(50, color="C3", ls="--", lw=1.2); ax.text(-0.45, 52, "Gate 2", ha="left", va="bottom", fontsize=9.5, color="C3")
    ax.set_xticks(range(len(pols))); ax.set_xticklabels([p[0] for p in pols], fontsize=9.5); ax.set_ylim(0, 105); ax.set_ylabel("share of the block oracle's gain, %"); ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.68))
    ax.set_title("Session-level hints, Mooncake traces at 200 GiB (trace simulation)", fontsize=11.5, loc="left")
    ax = axs[1]
    caps = [24, 32, 48, 64, 96, 128]; wl = get(rh, "W_live_mean", cap=24, policy="lru")
    for lab, p, c, mk in [("LRU", "lru", PC["lru"], "o"), ("SLRU 1/3", "slru", PC["slru"], "s"), ("agent 'continue' event", "event_cont", PC["learn"], "^"), ("oracle", "oracle", PC["oracle"], "d")]:
        ax.plot(range(len(caps)), [get(rh, cap=c_, policy=p) for c_ in caps], marker=mk, color=c, label=lab, lw=1.6)
    ax.axvspan(-0.4, 1.4, color="#f3f3f3", zorder=0); ax.text(0.5, 0.883, "cache turns over\nin < 2 reuse horizons", ha="center", va="bottom", fontsize=9.5, color="#555555")
    ax.set_xticks(range(len(caps))); ax.set_xticklabels([f"{c}\n{c / wl:.1f}×" for c in caps], fontsize=9.5); ax.set_xlabel("host cache size in blocks (× the live working set)")
    ax.set_ylim(0.88, 1.005); ax.set_ylabel("reuse-hit share (test half)"); ax.legend(loc="lower right", fontsize=9.5)
    ax.set_title("Real agent runs: 16 agents, real tools, real churn (replay)", fontsize=11.5, loc="left")
    save(fig, "f05_hints", ["2026-10-17-kv-session-hint-study/session-hints-8b-200GiB.csv", "2026-10-17-rq1b-reuse-horizon/lt-k16-l1g-bg2-churn0-replay.csv"])

# ---------------------------------------------------------------- f06 measured miss cost + retention policies
def f06_cost_retention():
    S = json.load(open(os.path.join(D_MC, "misscost-summary.json")))
    mc = {t: rows(os.path.join(D_MC, f"mc-{t}-tail-replay.csv")) for t in ("conversation", "toolagent")}
    hl = {"conversation": rows(os.path.join(D_HL, "mc-conversation-th0-replay.csv")), "toolagent": rows(os.path.join(D_HL, "mc-toolagent-th0-c3200-replay.csv"))}
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.7), gridspec_kw=dict(width_ratios=[1, 1.25]))
    ax = axs[0]; Ls = [str(l) for l in S["DRAM L1"]["Ls"]]; w = 0.21
    series = [("cold: recompute all", S["DRAM L1"]["cold_ms"], PC["cost"]), ("GPU prefix cache", S["DRAM L1"]["gpu_ms"], "C7"), ("LMCache L1 in DRAM", S["DRAM L1"]["l1_ms"], PC["dram"]), ("LMCache L1 on CXL devdax", S["CXL devdax L1"]["l1_ms"], PC["cxl"])]
    for i, (lab, d, c) in enumerate(series):
        b = ax.bar([k + (i - 1.5) * w for k in range(len(Ls))], [d[l] for l in Ls], w * 0.92, color=c, label=lab); label_bars(ax, b, "{:.0f}", fs=8.5, rot=90)
    ax.set_xticks(range(len(Ls))); ax.set_xticklabels([f"{int(l) // 1024 if int(l) % 1024 == 0 else round(int(l) / 1024, 1)}k" for l in Ls]); ax.set_xlabel("prompt length (tokens)"); ax.set_ylabel("time to first token, ms"); ax.set_ylim(0, 1700); ax.legend(loc="upper left", fontsize=9.5)
    ax.set_title("Measured: Qwen2.5-3B-AWQ on the RTX 4060 Ti (real system)", fontsize=11.5, loc="left")
    ax = axs[1]
    pols = [("SLRU 1/3", mc, "slru"), ("cost-aware\ntie-break", mc, "cost"), ("SLRU + cost", mc, "slru+cost"), ("decayed\npopularity", hl, "pop"), ("learned class\nhit rate", hl, "lhd"), ("learned\nper-root rate", hl, "cond")]
    w = 0.38
    for j, t in enumerate(("conversation", "toolagent")):
        vals = []
        for _, src, p in pols:
            base = get(src[t], "usable_hit_share", cap=3200, policy="lru"); top = get(src[t], "usable_hit_share", cap=3200, policy="oracle")
            vals.append(100 * (get(src[t], "usable_hit_share", cap=3200, policy=p) - base) / (top - base))
        b = ax.bar([k + (j - 0.5) * w for k in range(len(pols))], vals, w * 0.92, color=TR[t][1], label=TR[t][0]); label_bars(ax, b, "{:.0f}%", fs=10)
    ax.axhline(50, color="C3", ls="--", lw=1.2); ax.text(len(pols) - 0.55, 52, "Gate 2: 50% of the oracle's gain", ha="right", va="bottom", fontsize=9.5, color="C3")
    ax.axvspan(2.5, 5.5, color="#f3f3f3", zorder=0); ax.text(4, 30, "eviction ranked by learned history", ha="center", fontsize=10, color="#555555"); ax.text(1, 30, "eviction ranked by miss cost", ha="center", fontsize=10, color="#555555")
    ax.set_xticks(range(len(pols))); ax.set_xticklabels([p[0] for p in pols], fontsize=9.5); ax.set_ylim(-6, 64); ax.set_ylabel("share of the oracle's gain over LRU, %"); ax.legend(loc="upper left")
    ax.set_title("Eviction policies at 200 GiB, Mooncake traces (trace simulation)", fontsize=11.5, loc="left")
    save(fig, "f06_cost_retention", ["2026-10-18-rq1-misscost/misscost-summary.json (from real/dram3b-ttft.csv, real/dax3b-ttft.csv)", "mc-{conversation,toolagent}-tail-replay.csv",
                                     "2026-10-18-rq1b-history-learning/mc-conversation-th0-replay.csv", "mc-toolagent-th0-c3200-replay.csv"])

# ---------------------------------------------------------------- f07 learned admission
def f07_admission():
    hl = {t: rows(os.path.join(D_HL, f"mc-{t}-th0.15-replay.csv")) for t in ("conversation", "toolagent")}
    pols = [("LRU", "lru", PC["lru"]), ("SLRU 1/3", "slru", PC["slru"]), ("learned admission\n(class hit rate)", "lhd", PC["learn"]), ("learned admission\n(per-root rate)", "cond", "C8"), ("oracle", "oracle", PC["oracle"])]
    caps = [(1600, "100 GiB"), (3200, "200 GiB"), (6400, "400 GiB")]
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.7), gridspec_kw=dict(width_ratios=[1, 1, 0.8]))
    w = 0.8 / len(pols)
    for ax, t in zip(axs[:2], ("conversation", "toolagent")):
        for i, (lab, p, c) in enumerate(pols):
            vals = [get(hl[t], "usable_hit_share", cap=cp, policy=p) for cp, _ in caps]
            b = ax.bar([k + (i - 2) * w for k in range(len(caps))], vals, w * 0.92, color=c, label=lab); label_bars(ax, b, "{:.2f}", fs=8.5, rot=90)
        ax.set_xticks(range(len(caps))); ax.set_xticklabels([c for _, c in caps]); ax.set_ylim(0, 1.1); ax.set_ylabel("usable-prefix hit share (test half)")
        ax.set_title(f"{TR[t][0]} trace", fontsize=11.5, loc="left", color=TR[t][1])
    h, l = axs[0].get_legend_handles_labels(); fig.legend(h, [x.replace("\n", " ") for x in l], loc="lower center", ncol=5, fontsize=10, bbox_to_anchor=(0.5, -0.02))
    ax = axs[2]; w = 0.38
    for j, t in enumerate(("conversation", "toolagent")):
        vals = [get(hl[t], "written_chunks", cap=3200, policy=p) * GB_PER_CHUNK / 1000 for _, p, _ in pols]
        b = ax.bar([k + (j - 0.5) * w for k in range(len(pols))], vals, w * 0.92, color=TR[t][1], label=TR[t][0]); label_bars(ax, b, "{:.1f}", fs=9.5)
    ax.set_xticks(range(len(pols))); ax.set_xticklabels(["LRU", "SLRU", "learned\n(class)", "learned\n(root)", "oracle"], fontsize=9.5); ax.set_ylabel("TB written into host memory (test half)"); ax.set_ylim(0, 21); ax.legend(loc="upper right", fontsize=9)
    ax.set_title("Writes at 200 GiB", fontsize=11.5, loc="left")
    fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(os.path.join(OUT, "f07_admission.png"), dpi=200, bbox_inches="tight"); fig.savefig(os.path.join(OUT, "f07_admission.svg"), bbox_inches="tight"); plt.close(fig)
    SOURCES["f07_admission"] = ["2026-10-18-rq1b-history-learning/mc-{conversation,toolagent}-th0.15-replay.csv"]; print("wrote f07_admission")

if __name__ == "__main__":
    f01_overview(); f02_lru_vs_oracle(); f03_oracle(); f04_prediction(); f05_hints(); f06_cost_retention(); f07_admission()
    with open(os.path.join(OUT, "SOURCES.md"), "w") as f:
        f.write("# Figure sources (RQ1 progress deck 2026-10-20)\n\nAll paths relative to `experimental_results/`. Figures drawn by `scripts/figs_deck_2026-10-20.py`.\n\n| figure | raw files |\n|---|---|\n")
        for k, v in SOURCES.items(): f.write(f"| {k} | {'; '.join(v)} |\n")
    print("wrote SOURCES.md")
