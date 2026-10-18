#!/usr/bin/env python3
"""Miss-cost microbenchmark analysis (RQ1 miss-cost feasibility, 2026-10-18): fits the TTFT model to misscost_bench.py
CSVs and draws the figures. Model: TTFT(L, h) = t0 + r0·(L − h) + r1·((L² − h²)/2) + l·h, with h = usable cached prefix
(tokens), r0/r1 = recompute seconds per token and its growth with position (prefill superlinearity), l = load seconds
per token from the host tier (DRAM or CXL). Fit: cold cases give t0, r0, r1 (least squares on L); l1 cases give l.
usage: kv_misscost_figs.py <out_dir> <label=ttft.csv> [...]"""
import csv, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
def med(xs): xs = sorted(xs); return xs[len(xs) // 2] if xs else float("nan")
def lsq(X, y):
    """ordinary least squares for small systems without numpy: X list of rows, y list."""
    import itertools
    n = len(X[0]); A = [[sum(X[k][i] * X[k][j] for k in range(len(X))) for j in range(n)] for i in range(n)]; b = [sum(X[k][i] * y[k] for k in range(len(X))) for i in range(n)]
    # gaussian elimination
    M = [row[:] + [bi] for row, bi in zip(A, b)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(M[r][i])); M[i], M[p] = M[p], M[i]
        for r in range(n):
            if r != i and M[i][i] != 0:
                f = M[r][i] / M[i][i]; M[r] = [a - f * c for a, c in zip(M[r], M[i])]
    return [M[i][n] / M[i][i] if M[i][i] else 0.0 for i in range(n)]
summary = {}; data = {}
for arg in sys.argv[2:]:
    label, path = arg.split("=", 1); rows = list(csv.DictReader(open(path))); data[label] = rows
    def sel(case, L=None, f=None, conc=1): return [float(r["ttft_ms"]) for r in rows if r["case"] == case and (L is None or int(r["L"]) == L) and (f is None or abs(float(r["f"]) - f) < 1e-6) and int(r["conc"]) == conc]
    Ls = sorted({int(r["L"]) for r in rows})
    # cold fit: ttft = t0 + r0 L + r1 L^2/2
    X = [[1.0, L, L * L / 2] for L in Ls for _ in sel("cold", L)]; y = [v / 1000 for L in Ls for v in sel("cold", L)]
    t0, r0, r1 = lsq(X, y)
    # l1 fit: ttft = t0' + l L  (all tokens loaded; the last token recomputed)
    Xl = [[1.0, L] for L in Ls for _ in sel("l1", L)]; yl = [v / 1000 for L in Ls for v in sel("l1", L)]; tl, l = lsq(Xl, yl)
    Xg = [[1.0, L] for L in Ls for _ in sel("gpu", L)]; yg = [v / 1000 for L in Ls for v in sel("gpu", L)]; tg, g = lsq(Xg, yg)
    s = dict(Ls=Ls, t0_ms=1000 * t0, r0_ms_per_tok=1000 * r0, r1_us_per_tok_per_ktok=1e9 * r1 / 1000, l_ms_per_tok=1000 * l, gpu_ms_per_tok=1000 * g,
             cold_ms={L: med(sel("cold", L)) for L in Ls}, gpu_ms={L: med(sel("gpu", L)) for L in Ls}, l1_ms={L: med(sel("l1", L)) for L in Ls},
             prefix_ms={f"{L}@{f}": med(sel("prefix", L, f)) for L in Ls for f in (0.25, 0.5, 0.75)}, hole_ms={f"{L}@{f}": med(sel("hole", L, f)) for L in Ls for f in (0.25, 0.5, 0.75)},
             conc4_ms={L: med(sel("conc4", L, conc=4)) for L in Ls}, cached_tokens_l1={L: med([float(r["cached_tokens"]) for r in rows if r["case"] == "l1" and int(r["L"]) == L]) for L in Ls},
             cached_tokens_hole={f"{L}@{f}": med([float(r["cached_tokens"]) for r in rows if r["case"] == "hole" and int(r["L"]) == L and abs(float(r["f"]) - f) < 1e-6]) for L in Ls for f in (0.25, 0.5, 0.75)})
    s["recompute_over_load"] = (r0 + r1 * max(Ls) / 2) / l if l > 0 else float("inf")
    summary[label] = s
json.dump(summary, open(f"{out}/misscost-summary.json", "w"), indent=1); print(json.dumps({k: {kk: vv for kk, vv in v.items() if not isinstance(vv, dict)} for k, v in summary.items()}, indent=1))
for k, v in summary.items():
    print(k, "cold ms by L:", {L: round(x) for L, x in v["cold_ms"].items()}, "| gpu:", {L: round(x) for L, x in v["gpu_ms"].items()}, "| l1:", {L: round(x) for L, x in v["l1_ms"].items()})
    print(k, "prefix f vs hole f (ms):", {kk: (round(v["prefix_ms"][kk]), round(v["hole_ms"][kk]), round(v["cached_tokens_hole"][kk])) for kk in v["prefix_ms"]})
    print(k, "conc4 (4 cold prompts at once) ms:", {L: round(x) for L, x in v["conc4_ms"].items()})
# figure
fig, axs = plt.subplots(1, 3, figsize=(16, 4.5))
cyc = plt.rcParams["axes.prop_cycle"].by_key()["color"]
for i, (label, v) in enumerate(summary.items()):
    Ls = v["Ls"]; col = cyc[i]
    axs[0].plot(Ls, [v["cold_ms"][L] for L in Ls], marker="o", color=col, label=f"{label}: cold (recompute all)")
    axs[0].plot(Ls, [v["l1_ms"][L] for L in Ls], marker="s", ls="--", color=col, label=f"{label}: all from LMCache L1")
    axs[0].plot(Ls, [v["gpu_ms"][L] for L in Ls], marker="^", ls=":", color=col, label=f"{label}: all in vLLM's GPU cache")
    axs[0].plot(Ls, [v["conc4_ms"][L] for L in Ls], marker="x", ls="-.", color=col, label=f"{label}: cold, 4 at once")
    for L in Ls[-2:]:
        fs = [0, 0.25, 0.5, 0.75, 1.0]
        axs[1].plot(fs, [v["cold_ms"][L]] + [v["hole_ms"][f"{L}@{f}"] for f in (0.25, 0.5, 0.75)] + [v["l1_ms"][L]], marker="o", color=col, alpha=0.9 if L == Ls[-1] else 0.5, label=f"{label}, L={L}: usable prefix f·L (hole test)")
        axs[1].plot(fs[1:-1], [v["prefix_ms"][f"{L}@{f}"] for f in (0.25, 0.5, 0.75)], marker="x", ls="", ms=8, color=col, alpha=0.5, label="× clean-prefix case (base partly evicted from L1 between cases, see text)" if L == Ls[-1] and i == 0 else None)
        axs[1].plot(fs, [v["cold_ms"][L] * (1 - f) + v["gpu_ms"][L] * f for f in fs], ls=":", lw=1, color="#7f7f7f", label="linear model: (1−f)·cold + f·floor" if L == Ls[-1] and i == 0 else None)
    L = Ls[-1]; xs = [i * 4 + (0 if i == 0 else 0)]; bars = [("recompute\n1 request", (v["cold_ms"][L] - v["gpu_ms"][L]) / L), ("recompute\n4 at once", (v["conc4_ms"][L] - v["gpu_ms"][L]) / L), ("load from L1\n(upper bound)", max(0.0, (v["l1_ms"][L] - v["gpu_ms"][L]) / L))]
    for j, (nm, val) in enumerate(bars):
        x = j * (len(summary) + 1) + i; b_ = axs[2].bar(x, max(val, 1e-3), 0.9, color=col, label=label if j == 0 else None)
        axs[2].annotate(f"{val:.3f}" if val >= 0.001 else "< 0.001", (x, max(val, 1e-3)), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8)
    axs[2].set_xticks([j * (len(summary) + 1) + (len(summary) - 1) / 2 for j in range(3)]); axs[2].set_xticklabels([nm for nm, _ in bars], fontsize=9)
axs[0].set_xlabel("prompt length L, tokens"); axs[0].set_ylabel("TTFT, ms"); axs[0].set_title("TTFT by where the KV comes from (DIRECTLY MEASURED)", fontsize=10.5); axs[0].legend(fontsize=7, ncol=2)
ymax = max(v["cold_ms"][v["Ls"][-1]] for v in summary.values()) * 1.15; axs[1].set_ylim(0, ymax)
for label, v in summary.items():
    for kk, val in v["hole_ms"].items():
        if val > ymax: L_, f_ = kk.split("@"); axs[1].annotate(f"off scale: {label}, L={L_}, f={f_}: {val:.0f} ms (store/evict stall, see text)", (0.02, ymax * 0.06), ha="left", va="bottom", fontsize=7, color="#555555")
axs[1].set_xlabel("f: fraction of the prompt that is a usable cached prefix"); axs[1].set_ylabel("TTFT, ms"); axs[1].set_title("Prefix-dependence: the cost is set by the usable prefix, not by what is cached", fontsize=10.5); axs[1].legend(fontsize=7, loc="upper right")
axs[2].set_ylabel("ms per token above the GPU-hit floor"); axs[2].set_yscale("log"); axs[2].set_ylim(1e-3, 1); axs[2].set_title(f"Per-token cost at L = {max(summary[next(iter(summary))]['Ls'])} tokens", fontsize=10.5); axs[2].legend(fontsize=8)
fig.tight_layout(); fig.savefig(f"{out}/fig-misscost-ttft.png", dpi=200); fig.savefig(f"{out}/fig-misscost-ttft.svg"); print("wrote", f"{out}/fig-misscost-ttft.png")
