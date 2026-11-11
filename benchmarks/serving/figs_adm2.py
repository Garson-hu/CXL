#!/usr/bin/env python3
"""Figures of the 2026-11-10 GPU-KV admission study, evaluation part (matplotlib defaults, white background).
  fig3-concurrency-vs-ttft     (required figure 3) mixed workload (run_b.py: 50 % external hits / 50 % misses of 1k-8k tokens): TTFT p50 and
                               p95 of the external hits and of the misses against the closed-loop concurrency and the open-loop rate, per
                               GPU KV pool, stock against prototype
  fig4-request-timelines       (required figure 4) the compute-contention scenario (run_adm.py plan=c1), one repetition: what every request
                               does over time (waiting, lookup, load, prefill, decode), stock against prototype
  fig5-hit-vs-miss-ttft        (required figure 5) trace replays: TTFT p50 and p95 per request category, stock against prototype, paired by
                               the stock run's category
  fig6-throughput-vs-pressure  (required figure 6) mixed workload at saturation: throughput and TTFT against the MEASURED GPU KV occupancy
                               of the scenario (time-weighted used share of the pool between the scenario's first send and last completion)
  fig7-variants-tradeoff       one replay, every server configuration as a point: mean TTFT of the requests that are hits in the stock run
                               against mean TTFT of its misses (left), and median against 99th percentile of all requests (right)
usage: figs_adm2.py <fig_dir> [cc=<dir>:<pool>=<stock tag>,<prototype tag>[,<second prototype tag: table only>]+<pool>=...]
                    [c1=<dir>:<stock tag>,<prototype tag>[,<blocker tokens>]] [d=<label>=<dir>:<stock tag>,<prototype tag>+<label>=...]
                    [plab=<prototype label>] [plab2=<label of the second prototype configuration>]
                    [t=<dir>:<stock tag>,<tag>,<tag>... tlab=<label>|<label>|... ttitle=<title>]"""
import bisect, csv, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "font.size": 9, "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.5})
FIG = sys.argv[1]; KW = dict(a.split("=", 1) for a in sys.argv[2:]); os.makedirs(FIG, exist_ok=True); PLAB = KW.get("plab", "prototype")
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else None
def save(fig, name):
    fig.tight_layout(); fig.savefig(f"{FIG}/{name}.png", dpi=150); fig.savefig(f"{FIG}/{name}.pdf"); plt.close(fig); print("wrote", name)
def reqs(d, tag): return list(csv.DictReader(open(f"{d}/{tag}-adm-requests.csv")))
def kvs(d, tag):
    T = []; F = []; N = None
    for r in csv.DictReader(open(f"{d}/{tag}-adm-kv.csv")): T.append(float(r["t"])); F.append(int(r["free"])); N = int(r["tot"])
    return T, F, N
def used_share(T, F, N, a, b):
    """time-weighted used share of the pool in [a, b) from the decimated per-step occupancy"""
    i = max(0, bisect.bisect_right(T, a) - 1); s = 0.0; w = 0.0
    while i < len(T) - 1 and T[i] < b:
        lo = max(a, T[i]); hi = min(b, T[i + 1])
        if hi > lo: s += (1 - F[i] / N) * (hi - lo); w += hi - lo
        i += 1
    return s / w if w else None

if "cc" in KW:
    cdir, spec = KW["cc"].split(":", 1); pools = []; third = {}; PLAB2 = KW.get("plab2", "prototype 2")
    for item in spec.split("+"):
        pool, tg = item.split("="); tl = tg.split(","); pools.append((int(pool), tl[0], tl[1]))
        if len(tl) > 2 and os.path.exists(f"{cdir}/{tl[2]}-adm-requests.csv"): third[int(pool)] = tl[2]      # a second prototype configuration: table only
    pools = [(p, a, b) for p, a, b in pools if os.path.exists(f"{cdir}/{a}-adm-requests.csv") and os.path.exists(f"{cdir}/{b}-adm-requests.csv")]
    G = {}                                  # (pool, config, group) -> dict of stats
    for pool, a, b in pools:
        for cfg, tag in (("stock", a), (PLAB, b)) + (((PLAB2, third[pool]),) if pool in third else ()):
            R = reqs(cdir, tag); T, F, N = kvs(cdir, tag)
            for g in sorted({r["grp"] for r in R if r["grp"]}):
                v = [r for r in R if r["grp"] == g]; t0 = min(fl(r["send"]) for r in v); t1 = max(fl(r["send"]) + fl(r["total"]) for r in v)
                h = [fl(r["ttft"]) for r in v if r["case"] == "host"]; c = [fl(r["ttft"]) for r in v if r["case"] == "cold"]
                G[(pool, cfg, g)] = dict(h50=q(h, .5), h95=q(h, .95), c50=q(c, .5), c95=q(c, .95), n=len(v), rps=len(v) / (t1 - t0), tps=sum(fl(r["prompt"]) for r in v) / (t1 - t0),
                                         used=used_share(T, F, N, t0, t1), tot50=q([fl(r["total"]) for r in v], .5), totm=mean([fl(r["total"]) for r in v]))
    # figure 3 (closed-loop concurrency) and 3b (open-loop rate): rows = external hits / misses; columns = pools; colour = configuration
    for name, pre, xl, xs in (("fig3-concurrency-vs-ttft", "s1-c", "closed-loop concurrency", [1, 2, 4, 8, 16]),
                              ("fig3b-rate-vs-ttft", "s2-r", "open-loop arrival rate (requests / s)", [0.5, 1, 2, 4])):
        fig, axes = plt.subplots(2, len(pools), figsize=(3.3 * len(pools) + 0.4, 5.6), squeeze=False, sharex=True)
        for j, (pool, a, b) in enumerate(pools):
            for i, (ty, tl) in enumerate((("h", "external hits"), ("c", "misses"))):
                ax = axes[i][j]
                for cfg, col in (("stock", "C0"), (PLAB, "C1")):
                    for pc, ls, mk, lw in (("50", "-", "o", 1.5), ("95", ":", "^", 1.1)):
                        ys = [G.get((pool, cfg, f"{pre}{x:g}"), {}).get(ty + pc) for x in xs]
                        ax.plot(range(len(xs)), ys, linestyle=ls, marker=mk, markersize=4, linewidth=lw, color=col, label=f"{cfg}, p{pc}")
                ax.set_xticks(range(len(xs))); ax.set_xticklabels([f"{x:g}" for x in xs]); ax.set_yscale("log")
                if j == 0: ax.set_ylabel(f"{tl}: TTFT (s)")
                if i == 1: ax.set_xlabel(xl)
                if i == 0: ax.set_title(f"GPU KV pool {pool:,} blocks ({pool * 16 // 1000}k tokens)", fontsize=8.5)
        lo = min(a_.get_ylim()[0] for a_ in axes.flat); hi = max(a_.get_ylim()[1] for a_ in axes.flat)
        for a_ in axes.flat: a_.set_ylim(lo, hi)
        axes[0][0].legend(fontsize=6.8, frameon=False, loc="lower right")
        save(fig, name)
    # figure 6: saturation scenarios against the measured occupancy
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.5))
    for g, mk in (("s1-c16", "o"), ("s2-r4", "s"), ("s3-k16", "^")):
        for cfg, col in (("stock", "C0"), (PLAB, "C1")):
            pts = sorted((G[(p, cfg, g)]["used"], G[(p, cfg, g)]) for p, _, _ in pools if (p, cfg, g) in G and G[(p, cfg, g)]["used"] is not None)
            if not pts: continue
            lab = f"{ {'s1-c16': 'closed loop, 16', 's2-r4': 'open loop, 4 req/s', 's3-k16': 'bursts of 16'}[g] }, {cfg}"
            axes[0].plot([x for x, _ in pts], [s["tps"] for _, s in pts], marker=mk, color=col, linewidth=1.1, markersize=5, linestyle="-" if cfg == "stock" else "--", label=lab)
            axes[1].plot([x for x, _ in pts], [s["h50"] for _, s in pts], marker=mk, color=col, linewidth=1.1, markersize=5, linestyle="-" if cfg == "stock" else "--", label=lab)
            axes[2].plot([x for x, _ in pts], [s["c50"] for _, s in pts], marker=mk, color=col, linewidth=1.1, markersize=5, linestyle="-" if cfg == "stock" else "--", label=lab)
    for ax, yl in zip(axes, ("prompt tokens served / s", "external hits: TTFT p50 (s)", "misses: TTFT p50 (s)")):
        ax.set_xlabel("GPU KV blocks in use, time-weighted share of the pool\n(measured during the scenario; one point per pool size)"); ax.set_ylabel(yl); ax.set_ylim(bottom=0)
    axes[0].legend(fontsize=6.5, frameon=False, loc="lower left")
    save(fig, "fig6-throughput-vs-pressure")
    # table behind figures 3 and 6
    L = ["| pool (blocks) | scenario | config | used share of the pool | requests / s | prompt tok / s | hit TTFT p50 / p95 (s) | miss TTFT p50 / p95 (s) | request time p50 / mean (s) |", "|---|---|---|---|---|---|---|---|---|"]
    order = lambda g: (g[:2], float(re.sub(r"[^0-9.]", "", g[3:]) or 0))
    for pool, a, b in pools:
        for g in sorted({k[2] for k in G if k[0] == pool}, key=order):
            for cfg in ("stock", PLAB, PLAB2):
                s = G.get((pool, cfg, g))
                if s: L.append(f"| {pool} | {g} | {cfg} | {s['used']:.3f} | {s['rps']:.2f} | {s['tps']:.0f} | {s['h50']:.2f} / {s['h95']:.2f} | {s['c50']:.2f} / {s['c95']:.2f} | {s['tot50']:.2f} / {s['totm']:.2f} |")
    open(f"{FIG}/table-fig3-fig6.md", "w").write("\n".join(L) + "\n"); print("wrote table-fig3-fig6.md")

if "c1" in KW:
    cdir, spec = KW["c1"].split(":", 1); parts = spec.split(","); a, b = parts[0], parts[1]; LB = parts[2] if len(parts) > 2 else "28000"
    PH = [("unvisited", "queued, waiting queue not scanned", "0.75"), ("lookup", "LMCache lookup pending", "C4"), ("admit", "lookup done, waiting for admission\n(token budget or blocks)", "C3"),
          ("load", "KV load (transfer + step boundary)", "C1"), ("promote", "loaded, waiting for a step", "C5"), ("prefill", "prefill of the uncached tokens", "C0"), ("decode", "decode (16 output tokens)", "C2")]
    NAMES = {0: "miss, {L} tokens\n(the blocker)", 1: "external hit 4k\nsent at +0.5 s", 2: "miss 4k\nsent at +1.5 s", 3: "external hit 4k\nsent at +2.5 s", 4: "external hit 4k\nsent at +4.5 s"}
    fig, axes = plt.subplots(2, 1, figsize=(8.6, 6.0), sharex=True)
    for ax, tag, ttl in ((axes[0], a, "stock vLLM 0.31.0 + LMCache 0.5.5"), (axes[1], b, PLAB)):
        R = {}
        for r in reqs(cdir, tag):
            m = re.match(rf"{re.escape(tag)}-c1-B{LB}-r0-p(\d+)-(host|cold)-L(\d+)$", r["rid"])
            if m: R[int(m.group(1))] = r
        t0 = fl(R[0]["send"]); seen = set()
        for pos in sorted(R):
            r = R[pos]; g = lambda k: (fl(r[k]) - t0) if fl(r[k]) is not None else None
            send = g("send"); tq = g("t_q") or send; tv = g("t_visit"); tr = g("t_res"); ta = g("t_adm"); tar = g("t_arr"); trn = g("t_run"); tf = g("t_ft"); te = send + fl(r["total"])
            seg = [("unvisited", send, tv), ("lookup", tv, tr), ("admit", tr, ta)] + ([("load", ta, tar), ("promote", tar, trn)] if tar is not None else []) + [("prefill", trn, tf), ("decode", tf, te)]
            for name, x0, x1 in seg:
                if x0 is None or x1 is None or x1 - x0 <= 0: continue
                lab, col = next((l, c) for n, l, c in PH if n == name)
                ax.barh(pos, x1 - x0, left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.4, label=lab if name not in seen else None); seen.add(name)
            ax.plot([tf], [pos], marker="|", color="k", markersize=11, markeredgewidth=1.4)
            ax.text(te + 0.08, pos, f"first token {fl(r['ttft']):.2f} s, done {fl(r['total']):.2f} s", va="center", fontsize=7)
        ax.set_yticks(sorted(R)); ax.set_yticklabels([NAMES[p].format(L=f"{int(LB) // 1000}k") for p in sorted(R)], fontsize=7.5); ax.invert_yaxis(); ax.grid(axis="y", visible=False)
        ax.set_title(ttl, fontsize=9, loc="left")
    axes[1].set_xlabel("time since the blocker was sent (s); black tick = first token"); axes[0].set_xlim(0, max(a_.get_xlim()[1] for a_ in axes) * 1.22)
    h, l = [], []
    for ax in axes:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            if ll not in l: h.append(hh); l.append(ll)
    order = [n for _, n, _ in PH]; hl = sorted(zip(h, l), key=lambda x: order.index(x[1]))
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    fig.legend([x[0] for x in hl], [x[1] for x in hl], fontsize=7, frameon=False, loc="lower center", ncol=4)
    fig.savefig(f"{FIG}/fig4-request-timelines.png", dpi=150); fig.savefig(f"{FIG}/fig4-request-timelines.pdf"); plt.close(fig); print("wrote fig4-request-timelines")

if "d" in KW:
    panels = []
    for item in KW["d"].split("+"):
        lab, rest = item.split("=", 1); ddir, tg = rest.split(":"); a, b = tg.split(",")
        if os.path.exists(f"{ddir}/{a}-adm-requests.csv") and os.path.exists(f"{ddir}/{b}-adm-requests.csv"): panels.append((lab, ddir, a, b))
    CATS = [("host≥50%", "host-dominant\nhit"), ("GPU≥50%", "GPU-prefix\nhit"), ("10–50%", "partial\nhit"), ("miss<10%", "miss"), (None, "all")]
    nc = len(panels) if len(panels) <= 2 else 2; nr = -(-len(panels) // nc)
    fig, axes = plt.subplots(nr, nc, figsize=(5.4 * nc, 3.8 * nr), squeeze=False)
    for ax in axes.flat[len(panels):]: ax.set_visible(False)
    for ax, (lab, ddir, a, b) in zip(axes.flat, panels):
        A = {r["rid"][len(a) + 1:]: r for r in reqs(ddir, a)}; B = {r["rid"][len(b) + 1:]: r for r in reqs(ddir, b)}; w = 0.38
        for j, (cfg, D) in enumerate((("stock", A), (PLAB, B))):
            p50 = []; p95 = []; ns = []
            for ck, _ in CATS:
                ks = [k for k, r in A.items() if (ck is None or r["cat"] == ck) and k in B]
                v = [fl(D[k]["ttft"]) for k in ks]; p50.append(q(v, .5) or 0); p95.append(q(v, .95) or 0); ns.append(len(ks))
            xs = [i + (j - 0.5) * w for i in range(len(CATS))]
            bars = ax.bar(xs, p50, w, label=f"{cfg}, p50 (bar) and p95 (marker)", edgecolor="white", linewidth=0.8)
            ax.plot(xs, p95, linestyle="none", marker="_", markersize=11, markeredgewidth=1.8, color=bars[0].get_facecolor())
            for x, v in zip(xs, p50): ax.text(x, v, f"{v:.1f}" if v >= 10 else f"{v:.2f}", ha="center", va="bottom", fontsize=6.3)
        ax.set_xticks(range(len(CATS))); ax.set_xticklabels([f"{cl}\n(n = {n})" for (_, cl), n in zip(CATS, ns)], fontsize=7.5); ax.set_ylabel("TTFT (s)"); ax.set_title(lab, fontsize=8.5); ax.grid(axis="x", visible=False)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.22)
    axes[0][0].legend(fontsize=6.8, frameon=False, loc="upper left")
    save(fig, "fig5-hit-vs-miss-ttft")

if "t" in KW:
    tdir, tg = KW["t"].split(":"); tags = [t for t in tg.split(",") if os.path.exists(f"{tdir}/{t}-adm-requests.csv")]; labs = dict(zip(tg.split(","), KW.get("tlab", "|".join(tg.split(","))).split("|")))
    D = {t: {r["rid"][len(t) + 1:]: r for r in reqs(tdir, t)} for t in tags}; S = D[tags[0]]
    hits = [k for k, r in S.items() if r["cat"] in ("host≥50%", "GPU≥50%")]; miss = [k for k, r in S.items() if r["cat"] == "miss<10%"]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.0))
    for n, t in enumerate(tags):
        R = D[t]; col = "k" if n == 0 else f"C{(n - 1) % 10}"; mk = "*" if n == 0 else "os^Dv<>pPX"[(n - 1) % 10]
        hx = mean([fl(R[k]["ttft"]) for k in miss if k in R]); hy = mean([fl(R[k]["ttft"]) for k in hits if k in R]); allv = [fl(r["ttft"]) for r in R.values()]
        axes[0].scatter([hx], [hy], color=col, marker=mk, s=70 if n == 0 else 38, label=labs[t], zorder=3)
        axes[1].scatter([q(allv, .99)], [q(allv, .5)], color=col, marker=mk, s=70 if n == 0 else 38, label=labs[t], zorder=3)
    axes[0].set_xlabel(f"misses of the stock run (n = {len(miss)}): mean TTFT (s)"); axes[0].set_ylabel(f"hits of the stock run (n = {len(hits)}): mean TTFT (s)")
    axes[1].set_xlabel("all requests: TTFT p99 (s)"); axes[1].set_ylabel("all requests: TTFT p50 (s)")
    for ax in axes: ax.set_ylim(bottom=0); ax.set_xlim(left=0)
    axes[1].legend(fontsize=6.8, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    if "ttitle" in KW: fig.suptitle(KW["ttitle"], fontsize=9)
    save(fig, "fig7-variants-tradeoff")
