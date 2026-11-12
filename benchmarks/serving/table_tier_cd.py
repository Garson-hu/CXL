#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12): tables and figures of Experiment C (equal-hit comparison, run_eqhit.py) and Experiment D (concurrent
retrieval, run_e.py scenario e1). Reads <dir>/<tag>-tier-timeline.csv (analyze_tier.py) and <dir>/<tag>-client.jsonl.

mode c:  per tier and arrival rate (both passes pooled): requests, the equality checks (sum of cached tokens, sum of retrieved bytes,
         chunks by medium, requests with a GPU-prefix hit), TTFT p50 / p95 / mean, waiting (queued -> scheduled) p50 / p95, lookup +
         media p50 / p95, GPU transfer p50, request time p50, completed requests/s and output tokens/s of the pass
         -> <dir>/tables-c.md, <dir>/c-summary.csv, figs figC1-ttft-vs-rate.png, figC2-throughput-vs-rate.png, figC3-parts-vs-rate.png
mode d:  per tier, prefix length and concurrency k (the bursts pooled): TTFT p50 / max, per-request retrieval latency (lookup start ->
         retrieve end) p50 / max, lookup + media p50 / max, GPU transfer p50, aggregate retrieval throughput of a burst (retrieved
         bytes / time from the first lookup start to the last retrieve end), media throughput (L2 bytes / union of the L2 load
         intervals), host-to-GPU throughput (staging bytes / staging time), LMCache CPU cores during the burst, the wait between
         the end of a request's own lookup and the start of its GPU transfer
         -> <dir>/tables-d.md, <dir>/d-summary.csv, figs figD1-throughput-vs-k.png, figD2-latency-vs-k.png, figD3-ttft-vs-k.png
usage: table_tier_cd.py c|d <dir> <figs dir> tag=label [tag=label ...]"""
import csv, json, os, statistics as st, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

MODE, DIR, FIGS = sys.argv[1:4]; RUNS = [a.split("=", 1) for a in sys.argv[4:]]; os.makedirs(FIGS, exist_ok=True)
TXT = ("rid", "case", "grp", "error", "irid")
def num(x):
    try: return float(x)
    except Exception: return None
def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else None
def f(v, d=1): return "-" if v is None else f"{v:.{d}f}"
def load(tag):
    cl = {}
    for l in open(f"{DIR}/{tag}-client.jsonl"):
        c = json.loads(l); cl[c["rid"]] = c
    rows = []
    for r in csv.DictReader(open(f"{DIR}/{tag}-tier-timeline.csv")):
        d = {k: (num(v) if k not in TXT else v) for k, v in r.items()}; c = cl.get(r["rid"], {})
        d.update(send=c.get("send_mono_ns", 0) / 1e9, end=c.get("end_mono_ns", 0) / 1e9, out_tokens=c.get("out_tokens") or 0, rate=(c.get("rate")), pool=c.get("pool")); rows.append(d)
    return rows
def union_len(iv):
    iv = sorted(iv); tot = 0.0; cur = None
    for a, b in iv:
        if cur is None or a > cur[1]:
            if cur: tot += cur[1] - cur[0]
            cur = [a, b]
        else: cur[1] = max(cur[1], b)
    return tot + (cur[1] - cur[0] if cur else 0.0)

S = []
COL = {tag: f"C{i % 10}" for i, (tag, _) in enumerate(RUNS)}       # one colour per run in every panel (matplotlib's default cycle)
if MODE == "c":
    for tag, label in RUNS:
        rows = [r for r in load(tag) if r["case"] == "hit" and r["status"] == 200]
        for rate in sorted({r["rate"] for r in rows}):
            g = [r for r in rows if r["rate"] == rate]; passes = sorted({r["grp"] for r in g}); thr = []; otk = []
            for p in passes:
                gp = [r for r in g if r["grp"] == p]; w = max(r["end"] for r in gp) - min(r["send"] for r in gp); thr.append(len(gp) / w); otk.append(sum(r["out_tokens"] for r in gp) / w)
            tt = [r["ttft_client_ms"] for r in g]; v = lambda k: [r[k] for r in g if r.get(k) is not None]
            S.append(dict(tag=tag, label=label, rate=rate, n=len(g), passes=len(passes), cached_tokens=sum(r["cached_tokens"] or 0 for r in g), retrieve_MiB=sum(r["retrieve_bytes"] or 0 for r in g) / 2**20,
                          retrieve_tokens=sum(r["retrieve_tokens"] or 0 for r in g), ch_dram=sum(r["l1_dram"] or 0 for r in g), ch_dax=sum(r["l1_dax"] or 0 for r in g), ch_l2=sum(r["l2_chunks"] or 0 for r in g),
                          gpu_prefix_hits=sum(1 for r in g if (r["cached_tokens"] or 0) - (r["retrieve_tokens"] or 0) > 256),
                          ttft_p50=q(tt, .5), ttft_p95=q(tt, .95), ttft_mean=sum(tt) / len(tt), wait_p50=q(v("queue_to_sched_ms"), .5), wait_p95=q(v("queue_to_sched_ms"), .95),
                          lookup_p50=q(v("lookup_ms"), .5), lookup_p95=q(v("lookup_ms"), .95), l2_load_p50=q(v("l2_load_ms"), .5), retrieve_p50=q(v("retrieve_ms"), .5), retrieve_p95=q(v("retrieve_ms"), .95),
                          total_p50=q(v("total_ms"), .5), total_p95=q(v("total_ms"), .95), req_per_s=sum(thr) / len(thr), out_tok_per_s=sum(otk) / len(otk)))
    L = ["# Experiment C — equal-hit comparison (same pre-populated prefixes, same request sequence and arrival instants in every tier)", "",
         "| tier | rate req/s | n | cached tokens | MiB retrieved | chunks DRAM / DAX / L2 | GPU-prefix hits | TTFT p50 | p95 | mean | wait p50 | wait p95 | lookup + media p50 | p95 | L2 load p50 | GPU transfer p50 | request p50 | p95 | done req/s | out tok/s |", "|" + "---|" * 20]
    for d in S:
        L.append(f"| {d['label']} | {d['rate']:g} | {d['n']} | {d['cached_tokens']:.0f} | {d['retrieve_MiB']:.0f} | {d['ch_dram']:.0f} / {d['ch_dax']:.0f} / {d['ch_l2']:.0f} | {d['gpu_prefix_hits']} | {f(d['ttft_p50'])} | {f(d['ttft_p95'])} | {f(d['ttft_mean'])} | "
                 f"{f(d['wait_p50'])} | {f(d['wait_p95'])} | {f(d['lookup_p50'])} | {f(d['lookup_p95'])} | {f(d['l2_load_p50'])} | {f(d['retrieve_p50'])} | {f(d['total_p50'], 0)} | {f(d['total_p95'], 0)} | {d['req_per_s']:.2f} | {d['out_tok_per_s']:.0f} |")
    open(f"{DIR}/tables-c.md", "w").write("\n".join(L) + "\n")
    rates = sorted({d["rate"] for d in S})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, k, t in ((axes[0], "ttft_p50", "TTFT p50 (ms)"), (axes[1], "ttft_p95", "TTFT p95 (ms)")):
        for tag, label in RUNS:
            g = [d for d in S if d["tag"] == tag]
            if g: ax.plot([d["rate"] for d in g], [d[k] for d in g], marker="o", label=label, color=COL[tag])
        ax.set_xscale("log", base=2); ax.set_xticks(rates); ax.set_xticklabels([f"{r:g}" for r in rates]); ax.set_yscale("log"); ax.set_xlabel("offered rate (requests/s, Poisson)"); ax.set_ylabel(t); ax.grid(True, which="both", alpha=0.3)
    axes[1].legend(frameon=False, fontsize=8); fig.suptitle("C1  Equal hits: TTFT by tier and load (every request hits a 2K–16K prefix in the tier)"); fig.tight_layout(); fig.savefig(f"{FIGS}/figC1-ttft-vs-rate.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for tag, label in RUNS:
        g = [d for d in S if d["tag"] == tag]
        if g: ax.plot([d["rate"] for d in g], [d["req_per_s"] for d in g], marker="o", label=label, color=COL[tag])
    ax.plot(rates, rates, "k:", label="offered"); ax.set_xscale("log", base=2); ax.set_yscale("log", base=2); ax.set_xticks(rates); ax.set_xticklabels([f"{r:g}" for r in rates]); ax.set_xlabel("offered rate (requests/s)"); ax.set_ylabel("completed requests/s over the pass")
    ax.grid(True, which="both", alpha=0.3); ax.legend(frameon=False, fontsize=8); ax.set_title("C2  Equal hits: completed throughput"); fig.savefig(f"{FIGS}/figC2-throughput-vs-rate.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.0))
    for ax, k, t in ((axes[0], "lookup_p50", "lookup + media read p50 (ms)"), (axes[1], "retrieve_p50", "GPU transfer p50 (ms)"), (axes[2], "wait_p50", "queued → scheduled p50 (ms)")):
        for tag, label in RUNS:
            g = [d for d in S if d["tag"] == tag and d[k] is not None]
            if g: ax.plot([d["rate"] for d in g], [max(d[k], 0.1) for d in g], marker="o", label=label, color=COL[tag])
        ax.set_xscale("log", base=2); ax.set_xticks(rates); ax.set_xticklabels([f"{r:g}" for r in rates]); ax.set_yscale("log"); ax.set_xlabel("offered rate (requests/s)"); ax.set_title(t, fontsize=10); ax.grid(True, which="both", alpha=0.3)
    axes[0].legend(frameon=False, fontsize=8); fig.suptitle("C3  Equal hits: where the time goes as the load rises"); fig.tight_layout(); fig.savefig(f"{FIGS}/figC3-parts-vs-rate.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    out = f"{DIR}/c-summary.csv"
else:
    for tag, label in RUNS:
        rows = [r for r in load(tag) if r["case"] == "host" and r["status"] == 200 and r["grp"].startswith("e1-")]
        for grp in sorted({r["grp"] for r in rows}, key=lambda g: (int(g.split("-L")[1]), int(g.split("-k")[1].split("-")[0]))):
            g = [r for r in rows if r["grp"] == grp]; k = int(grp.split("-k")[1].split("-")[0]); Lp = int(grp.split("-L")[1]); agg = []; media = []; h2d = []; cpu = []
            for rep in sorted({r["rep"] for r in g}):
                b = [r for r in g if r["rep"] == rep and r.get("lookup_start_ms") is not None and r.get("retrieve_end_ms") is not None]
                if not b: continue
                t0 = min(r["send"] + r["lookup_start_ms"] / 1000 for r in b); t1 = max(r["send"] + r["retrieve_end_ms"] / 1000 for r in b)
                agg.append(sum(r["retrieve_bytes"] or 0 for r in b) / 2**30 / (t1 - t0))
                iv = [(r["send"] + r["l2_start_ms"] / 1000, r["send"] + r["l2_end_ms"] / 1000) for r in b if r.get("l2_start_ms") is not None]
                if iv: media.append(sum(r["l2_bytes"] or 0 for r in b) / 2**30 / union_len(iv))
                sb = sum(r["staging_bytes"] or 0 for r in b); sm = sum(r["staging_ms"] or 0 for r in b)
                if sm: h2d.append(sb / 2**30 / (sm / 1000))
                c = [r["lm_cpu_ms"] for r in b if r.get("lm_cpu_ms") is not None]
            tt = [r["ttft_client_ms"] for r in g]; v = lambda key: [r[key] for r in g if r.get(key) is not None]
            rl = [r["retrieve_end_ms"] - r["lookup_start_ms"] for r in g if r.get("retrieve_end_ms") is not None and r.get("lookup_start_ms") is not None]
            gap = [r["retrieve_start_ms"] - r["lookup_end_ms"] for r in g if r.get("retrieve_start_ms") is not None and r.get("lookup_end_ms") is not None]
            S.append(dict(tag=tag, label=label, L=Lp, k=k, n=len(g), cached_tokens=sum(r["cached_tokens"] or 0 for r in g), retrieve_MiB=sum(r["retrieve_bytes"] or 0 for r in g) / 2**20,
                          ch_dram=sum(r["l1_dram"] or 0 for r in g), ch_dax=sum(r["l1_dax"] or 0 for r in g), ch_l2=sum(r["l2_chunks"] or 0 for r in g),
                          ttft_p50=q(tt, .5), ttft_max=max(tt), retr_lat_p50=q(rl, .5), retr_lat_max=max(rl) if rl else None, lookup_p50=q(v("lookup_ms"), .5), lookup_max=max(v("lookup_ms")) if v("lookup_ms") else None,
                          l2_load_p50=q(v("l2_load_ms"), .5), retrieve_p50=q(v("retrieve_ms"), .5), gap_p50=q(gap, .5), gap_max=max(gap) if gap else None, wait_p50=q(v("queue_to_sched_ms"), .5), wait_max=max(v("queue_to_sched_ms")) if v("queue_to_sched_ms") else None,
                          agg_GiBps=st.median(agg) if agg else None, media_GiBps=st.median(media) if media else None, h2d_GiBps=st.median(h2d) if h2d else None, total_p50=q(v("total_ms"), .5)))
    L = ["# Experiment D — concurrent retrieval: k simultaneous host-tier hits of distinct prefixes (4 bursts per point; GPU prefix cache flushed before each)", "",
         "| tier | L | k | n | chunks DRAM / DAX / L2 | TTFT p50 | max | retrieval latency p50 (lookup start → KV on GPU) | max | lookup + media p50 | max | L2 load p50 | lookup end → transfer start p50 | max | GPU transfer p50 | aggregate GiB/s | media GiB/s | H2D GiB/s | queued → scheduled p50 | max |", "|" + "---|" * 20]
    for d in S:
        L.append(f"| {d['label']} | {d['L']} | {d['k']} | {d['n']} | {d['ch_dram']:.0f} / {d['ch_dax']:.0f} / {d['ch_l2']:.0f} | {f(d['ttft_p50'])} | {f(d['ttft_max'])} | {f(d['retr_lat_p50'])} | {f(d['retr_lat_max'])} | {f(d['lookup_p50'])} | {f(d['lookup_max'])} | {f(d['l2_load_p50'])} | "
                 f"{f(d['gap_p50'])} | {f(d['gap_max'])} | {f(d['retrieve_p50'])} | {f(d['agg_GiBps'], 2)} | {f(d['media_GiBps'], 2)} | {f(d['h2d_GiBps'], 2)} | {f(d['wait_p50'])} | {f(d['wait_max'])} |")
    open(f"{DIR}/tables-d.md", "w").write("\n".join(L) + "\n")
    ks = sorted({d["k"] for d in S}); Ls = sorted({d["L"] for d in S})
    for name, key, yl, title, logy in (("figD1-throughput-vs-k", "agg_GiBps", "retrieved GiB/s over the burst", "D1  Aggregate KV retrieval throughput (first lookup → last KV on GPU)", False),
                                       ("figD2-latency-vs-k", "retr_lat_p50", "ms, median over the burst's requests", "D2  Per-request retrieval latency (lookup start → KV on GPU)", True),
                                       ("figD3-ttft-vs-k", "ttft_p50", "TTFT (ms), median", "D3  TTFT of k simultaneous host-tier hits", True)):
        fig, axes = plt.subplots(1, len(Ls), figsize=(5.4 * len(Ls), 4.0), squeeze=False)
        for ax, Lp in zip(axes[0], Ls):
            for tag, label in RUNS:
                g = [d for d in S if d["tag"] == tag and d["L"] == Lp and d[key] is not None]
                if g: ax.plot([d["k"] for d in g], [d[key] for d in g], marker="o", label=label, color=COL[tag])
            ax.set_xscale("log", base=2); ax.set_xticks(ks); ax.set_xticklabels([str(k) for k in ks]); ax.set_xlabel("simultaneous requests k"); ax.set_ylabel(yl); ax.set_title(f"{Lp // 1024}K-token prefixes", fontsize=10); ax.grid(True, which="both", alpha=0.3)
            if logy: ax.set_yscale("log")
            else: ax.set_ylim(bottom=0)
        axes[0][-1].legend(frameon=False, fontsize=8); fig.suptitle(title); fig.tight_layout(); fig.savefig(f"{FIGS}/{name}.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    out = f"{DIR}/d-summary.csv"
with open(out, "w", newline="") as fo:
    w = csv.DictWriter(fo, fieldnames=list(S[0])); w.writeheader()
    for d in S: w.writerow({k: ("" if v is None else (round(v, 3) if isinstance(v, float) else v)) for k, v in d.items()})
print("\n".join(L)[:7000])
