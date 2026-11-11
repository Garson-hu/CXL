#!/usr/bin/env python3
"""Figure 8 of the 2026-11-10 GPU-KV admission study: the bound of the head-of-line bypass on one replay (matplotlib defaults, white
background). x: how long a request that does not fit may be passed (stock = never); left: mean TTFT of all requests and of the stock run's
classes; right: mean request time, TTFT p95 of all requests and TTFT p95 of the long prompts (>= 8,192 tokens). Solid lines: token rules plus
bypass (P2 family); hollow markers joined by dashed lines: the bypass alone (stock token rules).
usage: fig_bypass_bound.py <fig_dir> <dir> <stock tag> <tag>=<bound s> [...] [alone:<tag>=<bound s> ...] [title=<text>]"""
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "font.size": 9, "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.5})
FIG, d, stock = sys.argv[1:4]; title = next((a.split("=", 1)[1] for a in sys.argv[4:] if a.startswith("title=")), "")
fam = [(a.split("=")[0], float(a.split("=")[1])) for a in sys.argv[4:] if not a.startswith(("alone:", "title="))]
alone = [(a[6:].split("=")[0], float(a[6:].split("=")[1])) for a in sys.argv[4:] if a.startswith("alone:")]
fam = [(t, b) for t, b in fam if os.path.exists(f"{d}/{t}-adm-requests.csv")]; alone = [(t, b) for t, b in alone if os.path.exists(f"{d}/{t}-adm-requests.csv")]
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))]
def mean(v): return sum(v) / len(v)
def load(t): return {r["rid"][len(t) + 1:]: dict(cat=r["cat"], ttft=fl(r["ttft"]), total=fl(r["total"]), prompt=fl(r["prompt"])) for r in csv.DictReader(open(f"{d}/{t}-adm-requests.csv"))}
S = load(stock); cls = {c: [k for k, r in S.items() if r["cat"] == c] for c in ("host≥50%", "GPU≥50%", "miss<10%")}; longs = [k for k, r in S.items() if r["prompt"] >= 8192]
def stats(t):
    R = load(t); v = list(R.values())
    return dict(all=mean([r["ttft"] for r in v]), host=mean([R[k]["ttft"] for k in cls["host≥50%"] if k in R]), gpu=mean([R[k]["ttft"] for k in cls["GPU≥50%"] if k in R]),
                miss=mean([R[k]["ttft"] for k in cls["miss<10%"] if k in R]), rt=mean([r["total"] for r in v]), p95=q([r["ttft"] for r in v], .95), l95=q([R[k]["ttft"] for k in longs if k in R], .95))
bounds = sorted({b for _, b in fam} | {b for _, b in alone}); xs = {b: i + 1 for i, b in enumerate(bounds)}
F = [(0, stats(stock))] + [(xs[b], stats(t)) for t, b in sorted(fam, key=lambda x: x[1])]
A = [(0, stats(stock))] + [(xs[b], stats(t)) for t, b in sorted(alone, key=lambda x: x[1])]
fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.6))
SER = ((("all", "all requests"), ("host", f"host-dominant hits (n = {len(cls['host≥50%'])})"), ("gpu", f"GPU-prefix hits (n = {len(cls['GPU≥50%'])})"), ("miss", f"misses (n = {len(cls['miss<10%'])})")),
       (("rt", "request time, mean"), ("p95", "TTFT p95, all requests"), ("l95", f"TTFT p95, prompts ≥ 8,192 tokens (n = {len(longs)})")))
for ax, ser, yl in zip(axes, SER, ("TTFT, mean (s)", "seconds")):
    for i, (k, lab) in enumerate(ser):
        ax.plot([x for x, _ in F], [s[k] for _, s in F], marker="o", markersize=5, linewidth=1.4, color=f"C{i}", label=lab)
        if len(A) > 1: ax.plot([x for x, _ in A], [s[k] for _, s in A], marker="s", markersize=6, linewidth=1.0, linestyle="--", color=f"C{i}", markerfacecolor="white")
    ax.set_xticks(range(len(bounds) + 1)); ax.set_xticklabels(["stock\n(never)"] + [f"{b:g} s" for b in bounds]); ax.set_ylim(bottom=0)
    ax.set_xlabel("how long a request that does not fit may be passed"); ax.set_ylabel(yl)
    ax.legend(fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
axes[0].plot([], [], marker="o", color="0.3", linewidth=1.4, label="token rules + bypass"); axes[0].plot([], [], marker="s", color="0.3", linestyle="--", markerfacecolor="white", linewidth=1.0, label="bypass alone")
axes[0].legend(fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
if title: fig.suptitle(title, fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/fig8-bypass-bound.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{FIG}/fig8-bypass-bound.pdf", bbox_inches="tight"); print("wrote fig8-bypass-bound")
