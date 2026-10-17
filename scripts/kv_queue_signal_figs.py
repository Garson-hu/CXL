#!/usr/bin/env python3
"""Figures of the RQ1-B application-signal study (2026-10-17): the scheduler-queue lookahead policies
(session-hints-8b-200GiB-queue.csv from kv_session_hint_study.py) and the lead times measured on the real c28 runs
(vLLM 0.31 + LMCache 0.5.5 multi-process: arrival -> lookup done, lookup -> first token).
usage: kv_queue_signal_figs.py"""
import bisect, csv, datetime, gzip, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); E = os.path.join(REPO, "experimental_results")
D = os.path.join(E, "2026-10-17-kv-session-hint-study"); OUT = os.path.join(E, "2026-10-17-rq1b-application-reuse-signals"); os.makedirs(OUT, exist_ok=True)
TRACES = ["conversation", "toolagent", "synthetic"]; COL = {"conversation": "#1f77b4", "toolagent": "#2ca02c", "synthetic": "#9467bd"}
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
rows = list(csv.DictReader(open(os.path.join(D, "session-hints-8b-200GiB-queue.csv"))))
def get(tr, pol, key="reuse_hit_share"): return next(float(r[key]) for r in rows if r["trace"] == tr and r["policy"] == pol)
def gain(tr, pol): b, t = get(tr, "split"), get(tr, "oracle_min"); return 100 * (get(tr, pol) - b) / (t - b)
def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(OUT, name + ".png"), dpi=200); fig.savefig(os.path.join(OUT, name + ".svg")); plt.close(fig); print("wrote", name)

# 1. queue lookahead: share of the oracle gain vs W
Ws = [1, 5, 10, 30, 60, 300]
fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
for tr in TRACES:
    axs[0].plot(Ws, [gain(tr, f"queue{w}") for w in Ws], marker="o", color=COL[tr], label=f"{tr}: queue only")
    axs[0].plot([5, 10, 30, 60], [gain(tr, f"queue{w}+slru") for w in (5, 10, 30, 60)], marker="s", ls="--", color=COL[tr], label=f"{tr}: queue + SLRU")
axs[0].axhline(50, color="#d62728", ls=":", lw=1.2); axs[0].text(1.1, 52, "Gate 2: 50%", color="#d62728", fontsize=9.5)
axs[0].axvspan(0.19, 6.0, color="#f3f3f3", zorder=0); axs[0].text(0.21, 101, "shaded: queue wait measured on c28\n(0.08× load): p50 0.2 s, p90 2.6–6 s", ha="left", va="top", fontsize=8.5, color="#555555")
axs[0].set_xscale("log"); axs[0].set_xticks(Ws); axs[0].set_xticklabels([f"{w} s" for w in Ws]); axs[0].set_xticks([], minor=True); axs[0].set_xlim(0.15, 400)
axs[0].set_xlabel("queueing delay W (arrival → service): the scheduler's lookahead"); axs[0].set_ylabel("share of the block oracle's gain, %"); axs[0].set_ylim(-5, 110); axs[0].legend(fontsize=8.5, loc="upper right")
axs[0].set_title("Protecting the blocks of queued requests", fontsize=11.5)
pols = [("static split", "split"), ("SLRU 1/3\n(online)", "queue0+slru"), ("task-end event\n(agent loop)", "hint:delay=0"), ("queue 10 s\n+ task end", "queue10+end0"), ("queue 60 s\n+ task end", "queue60+end0"), ("block\noracle", "oracle_min")]
w = 0.27
for j, tr in enumerate(TRACES):
    vals = [get(tr, p) for _, p in pols]; b = axs[1].bar([x + (j - 1) * w for x in range(len(pols))], vals, w * 0.92, color=COL[tr], label=tr)
    for r, v in zip(b, vals): axs[1].annotate(f"{v:.2f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7.5, rotation=90)
axs[1].set_xticks(range(len(pols))); axs[1].set_xticklabels([p[0] for p in pols], fontsize=9); axs[1].set_ylabel("reuse-hit share (test half)"); axs[1].set_ylim(0, 1.12); axs[1].legend(fontsize=9, loc="upper left")
axs[1].set_title("Combining the two realistic signals", fontsize=11.5)
save(fig, "fig-queue-lookahead")

# 2. measured lead times on c28 (real runs)
def lead(d, tag):
    meta = {l.split()[1]: l for l in open(f"{d}/{tag}-meta.txt")}; m = meta["clock"].split(); off = float(m[3].split("=")[1]) - int(m[2]) / 1e9
    p = f"{d}/{tag}-lmcache.log"; lm = gzip.open(p + ".gz", "rt", errors="replace").read() if os.path.exists(p + ".gz") else open(p, errors="replace").read()
    lm = re.sub(r"\x1b\[[0-9;]*m", "", lm)
    pf = [datetime.datetime.strptime(a, "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=datetime.timezone(datetime.timedelta(hours=-4))).timestamp() for a in re.findall(r"\[(\S+ \S+)\] LMCache INFO: Prefetch request completed", lm)]
    R = sorted((int(f[3]) / 1e9 + off, int(f[4]) / 1e9 + off if int(f[4]) else None) for f in (l.split() for l in open(f"{d}/{tag}-client.txt") if l.startswith("REQ ")))
    ss = [s for s, _ in R]; a, b = [], []
    for t in pf:
        k = bisect.bisect_right(ss, t) - 1
        if k >= 0:
            a.append(t - ss[k]); ft = R[k][1]
            if ft: b.append(ft - t)
    return sorted(a), sorted(b)
runs = [("2026-10-11-capacity-matched-kv/real", "dram", "conversation 0.08×, DRAM L1"), ("2026-10-11-capacity-matched-kv/real", "dax", "conversation 0.08×, CXL L1"), ("2026-10-12-checkpoint-kv-mixed/real", "none", "tool agent 0.08×, CXL L1")]
fig, axs = plt.subplots(1, 2, figsize=(11, 4.5))
for (d, tag, lab), col in zip(runs, ["#1f77b4", "#ff7f0e", "#2ca02c"]):
    a, b = lead(os.path.join(E, d), tag)
    axs[0].plot(a, [i / len(a) for i in range(1, len(a) + 1)], color=col, label=lab, lw=1.8); axs[1].plot(b, [i / len(b) for i in range(1, len(b) + 1)], color=col, label=lab, lw=1.8)
    print(f"{lab}: n={len(a)} arrival→lookup p50 {a[len(a)//2]:.2f} s p90 {a[int(0.9*len(a))]:.2f} s | lookup→first token p50 {b[len(b)//2]:.2f} s p90 {b[int(0.9*len(b))]:.2f} s")
axs[0].set_xscale("log"); axs[0].set_xlabel("request arrival → LMCache lookup done, s\n(= queue wait; eager prefetch off)"); axs[0].set_ylabel("CDF"); axs[0].legend(fontsize=8.5, loc="lower right"); axs[0].set_title("How long a request waits before its KV lookup", fontsize=11.5)
axs[1].set_xscale("log"); axs[1].set_xlabel("lookup done → first token, s\n(chunked prefill)"); axs[1].set_ylabel("CDF"); axs[1].set_title("From lookup to first token", fontsize=11.5)
for ax in axs: ax.set_ylim(0, 1)
save(fig, "fig-real-leadtime")
