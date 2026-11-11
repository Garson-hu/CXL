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
                               against mean TTFT of its misses (left), and mean TTFT of all requests against the longest TTFT (right)
usage: figs_adm2.py <fig_dir> [cc=<dir>:<pool>=<stock tag>,<prototype tag>[,<second prototype tag: table only>]+<pool>=...]
                    [c1=<dir>:<stock tag>,<prototype tag>[,<blocker tokens>]] [d=<panel title>=<dir>:<stock tag>,<tag>@<configuration label>,...||<panel title>=...]
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
                for cfg, col in (("stock", "C0"), (PLAB, "C1")) + (((PLAB2, "C2"),) if third else ()):
                    for pc, ls, mk, lw in (("50", "-", "o", 1.5), ("95", ":", "^", 1.1)):
                        ys = [G.get((pool, cfg, f"{pre}{x:g}"), {}).get(ty + pc) for x in xs]
                        if any(y is not None for y in ys): ax.plot(range(len(xs)), ys, linestyle=ls, marker=mk, markersize=4 if cfg != PLAB2 else 3, linewidth=lw, color=col, label=f"{cfg}, p{pc}")
                ax.set_xticks(range(len(xs))); ax.set_xticklabels([f"{x:g}" for x in xs]); ax.set_yscale("log")
                if j == 0: ax.set_ylabel(f"{tl}: TTFT (s)")
                if i == 1: ax.set_xlabel(xl)
                if i == 0: ax.set_title(f"GPU KV pool {pool:,} blocks ({round(pool * 16 / 1000)}k tokens)", fontsize=8.5)
        lo = min(a_.get_ylim()[0] for a_ in axes.flat); hi = max(a_.get_ylim()[1] for a_ in axes.flat)
        for a_ in axes.flat: a_.set_ylim(lo, hi)
        axes[0][0].legend(fontsize=6.8, frameon=False, loc="lower right")
        save(fig, name)
    # figure 6: saturation scenarios against the measured occupancy; columns = scenarios, rows = quantities, one line per configuration,
    # points joined in the order of the pool sizes (the largest pool has the lowest occupancy)
    SC = (("s1-c16", "closed loop, 16 in the system"), ("s2-r4", "open loop, 4 requests / s"), ("s3-k16", "bursts of 16"))
    QY = (("tps", "prompt tokens served / s"), ("h50", "external hits: TTFT p50 (s)"), ("c50", "misses: TTFT p50 (s)"))
    fig, axes = plt.subplots(3, 3, figsize=(10.5, 7.4), sharex=True, sharey="row")
    for j, (g, gl) in enumerate(SC):
        for cfg, col, mk in (("stock", "C0", "o"), (PLAB, "C1", "s")) + (((PLAB2, "C2", "^"),) if third else ()):
            pts = [(G[(p, cfg, g)]["used"], G[(p, cfg, g)]) for p, _, _ in sorted(pools, reverse=True) if (p, cfg, g) in G and G[(p, cfg, g)]["used"] is not None]
            if not pts: continue
            for i, (k, _) in enumerate(QY):
                axes[i][j].plot([x for x, _ in pts], [st[k] for _, st in pts], marker=mk, color=col, linewidth=1.2, markersize=5, label=cfg)
        axes[0][j].set_title(gl, fontsize=9); axes[2][j].set_xlabel("GPU KV pool in use during the scenario\n(measured, time-weighted share)", fontsize=8)
    for i, (_, yl) in enumerate(QY):
        axes[i][0].set_ylabel(yl)
        for j in range(3): axes[i][j].set_ylim(bottom=0)
    axes[0][0].legend(fontsize=7.5, frameon=False, loc="lower left")
    fig.suptitle("one point per GPU KV pool size (14,912 / 7,456 / 3,728 / 2,560 blocks, left to right)" if len(pools) == 4 else "one point per GPU KV pool size", fontsize=8.5)
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
    # by prompt length, saturated scenarios pooled (do the gains depend on the length of the cached prefix?)
    SAT = ("s1-c8", "s1-c16", "s2-r4", "s3-k8", "s3-k16")
    L = ["| pool (blocks) | request type | prompt (tokens) | n | stock: TTFT p50 / p95 (s) | " + PLAB + ": TTFT p50 / p95 (s) |", "|---|---|---|---|---|---|"]
    for pool, a, b in pools:
        A = reqs(cdir, a); B = reqs(cdir, b)
        for ty, tl in (("host", "external hit"), ("cold", "miss")):
            for Lp in (1024, 2048, 4096, 8192):
                va = [fl(r["ttft"]) for r in A if r["case"] == ty and r["grp"] in SAT and r["rid"].endswith(f"-L{Lp}")]; vb = [fl(r["ttft"]) for r in B if r["case"] == ty and r["grp"] in SAT and r["rid"].endswith(f"-L{Lp}")]
                if va and vb: L.append(f"| {pool} | {tl} | {Lp // 1024}k | {len(va)} | {q(va, .5):.2f} / {q(va, .95):.2f} | {q(vb, .5):.2f} / {q(vb, .95):.2f} |")
    open(f"{FIG}/table-cc-by-length.md", "w").write("\n".join(L) + "\n"); print("wrote table-cc-by-length.md")

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
    # d=<panel title>=<dir>:<stock tag>,<tag>@<configuration label>,<tag>@<label>...||<panel title>=...   (a configuration keeps its colour in every panel)
    panels = []; order = ["stock"]
    for item in KW["d"].split("||"):
        lab, rest = item.split("=", 1); ddir, tg = rest.split(":"); tl = tg.split(","); a = tl[0]
        cfgs = [(t.split("@")[0], t.split("@")[1]) for t in tl[1:] if os.path.exists(f"{ddir}/{t.split('@')[0]}-adm-requests.csv")]
        for _, c in cfgs:
            if c not in order: order.append(c)
        if os.path.exists(f"{ddir}/{a}-adm-requests.csv") and cfgs: panels.append((lab, ddir, a, cfgs))
    COL = {c: f"C{i}" for i, c in enumerate(order)}
    CATS = [("host≥50%", "host-dominant\nhit"), ("GPU≥50%", "GPU-prefix\nhit"), ("10–50%", "partial\nhit"), ("miss<10%", "miss"), (None, "all")]
    nc = len(panels) if len(panels) <= 2 else 2; nr = -(-len(panels) // nc)
    fig, axes = plt.subplots(nr, nc, figsize=(6.6 * nc, 3.7 * nr), squeeze=False)
    for ax in axes.flat[len(panels):]: ax.set_visible(False)
    for ax, (lab, ddir, a, cfgs) in zip(axes.flat, panels):
        A = {r["rid"][len(a) + 1:]: r for r in reqs(ddir, a)}; runs = [("stock", A)] + [(c, {r["rid"][len(t) + 1:]: r for r in reqs(ddir, t)}) for t, c in cfgs]; w = 0.84 / len(runs)
        for j, (cfg, D) in enumerate(runs):
            mn = []; p95 = []; ns = []
            for ck, _ in CATS:
                ks = [k for k, r in A.items() if (ck is None or r["cat"] == ck) and k in D]
                v = [fl(D[k]["ttft"]) for k in ks]; mn.append(mean(v) or 0); p95.append(q(v, .95) or 0); ns.append(len(ks))
            xs = [i + (j - (len(runs) - 1) / 2) * w for i in range(len(CATS))]
            ax.bar(xs, mn, w, label=cfg, color=COL[cfg], edgecolor="white", linewidth=0.6)
            ax.plot(xs, p95, linestyle="none", marker="_", markersize=max(5, 34 * w), markeredgewidth=1.6, color=COL[cfg])
        ax.set_xticks(range(len(CATS))); ax.set_xticklabels([f"{cl}\n(n = {n})" for (_, cl), n in zip(CATS, ns)], fontsize=7.5); ax.set_title(lab, fontsize=8.5); ax.grid(axis="x", visible=False)
    for r_ in range(nr): axes[r_][0].set_ylabel("TTFT (s): bar = mean, tick = p95")
    h = [plt.Rectangle((0, 0), 1, 1, color=COL[c]) for c in order]
    fig.legend(h, order, fontsize=7.5, frameon=False, loc="lower center", ncol=len(order), bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout(); fig.savefig(f"{FIG}/fig5-hit-vs-miss-ttft.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{FIG}/fig5-hit-vs-miss-ttft.pdf", bbox_inches="tight"); plt.close(fig); print("wrote fig5-hit-vs-miss-ttft")

if "t" in KW:
    tdir, tg = KW["t"].split(":"); tags = [t for t in tg.split(",") if os.path.exists(f"{tdir}/{t}-adm-requests.csv")]; labs = dict(zip(tg.split(","), KW.get("tlab", "|".join(tg.split(","))).split("|")))
    D = {t: {r["rid"][len(t) + 1:]: r for r in reqs(tdir, t)} for t in tags}; S = D[tags[0]]
    hits = [k for k, r in S.items() if r["cat"] in ("host≥50%", "GPU≥50%")]; miss = [k for k, r in S.items() if r["cat"] == "miss<10%"]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.0)); X0 = []; Y0 = []; X1 = []; Y1 = []
    for n, t in enumerate(tags):
        R = D[t]; col = "k" if n == 0 else f"C{(n - 1) % 10}"; mk = "*" if n == 0 else "os^Dv<>pPXhd8H"[(n - 1) % 14]
        hx = mean([fl(R[k]["ttft"]) for k in miss if k in R]); hy = mean([fl(R[k]["ttft"]) for k in hits if k in R]); allv = [fl(r["ttft"]) for r in R.values()]
        axes[0].scatter([hx], [hy], color=col, marker=mk, s=70 if n == 0 else 38, label=labs[t], zorder=3); X0.append(hx); Y0.append(hy)
        axes[1].scatter([max(allv)], [mean(allv)], color=col, marker=mk, s=70 if n == 0 else 38, label=labs[t], zorder=3); X1.append(max(allv)); Y1.append(mean(allv))
    axes[0].set_xlabel(f"misses of the stock run (n = {len(miss)}): mean TTFT (s)"); axes[0].set_ylabel(f"hits of the stock run (n = {len(hits)}): mean TTFT (s)")
    axes[1].set_xlabel("all requests: longest TTFT (s), log scale"); axes[1].set_ylabel("all requests: mean TTFT (s)")
    axes[0].set_xlim(0, max(X0) * 1.08); axes[0].set_ylim(0, max(Y0) * 1.08)
    axes[1].set_xscale("log"); axes[1].set_xlim(min(X1) * 0.85, max(X1) * 1.25); axes[1].set_ylim(0, max(Y1) * 1.08)
    ticks = [t_ for t_ in (40, 50, 60, 80, 100, 150, 200, 300) if min(X1) * 0.85 <= t_ <= max(X1) * 1.25]; axes[1].set_xticks(ticks); axes[1].set_xticklabels([str(t_) for t_ in ticks]); axes[1].minorticks_off()
    axes[1].legend(fontsize=6.8, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    if "ttitle" in KW: fig.suptitle(KW["ttitle"], fontsize=9)
    save(fig, "fig7-variants-tradeoff")
