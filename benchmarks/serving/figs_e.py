#!/usr/bin/env python3
"""Figures of Experiment E (concurrent KV retrieval) from analyze_b.py's outputs and the GPU sampler.
  figE1  concurrent host hits k vs aggregate host→GPU bandwidth (PCIe RX over the burst) and per-request transfer time
  figE2  k vs per-request retrieval latency (lookup end → load finished) and TTFT, 1 vs 4 transfer threads, DRAM vs SSD
  figE3  transfer bandwidth utilization vs TTFT (every burst), and the e2 mix (loads while the GPU prefills cold prompts)
usage: figs_e.py <E dir> <fig dir> [tags=e-workers1,e-workers4,e-ssd]"""
import csv, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_b import load_gpu, q

E, FIG = sys.argv[1], sys.argv[2]; os.makedirs(FIG, exist_ok=True)
TAGS = (sys.argv[3].split("=", 1)[1] if len(sys.argv) > 3 else "e-workers1,e-workers4,e-ssd").split(",")
LABEL = {"e-workers1": "DRAM L1, 1 transfer thread (default)", "e-workers4": "DRAM L1, 4 transfer threads", "e-ssd": "SSD L2 (O_DIRECT), 1 thread", "e-workers1-nosamp": "DRAM L1, 1 thread, no GPU sampler"}
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def load(tag):
    p = f"{E}/{tag}-requests.csv"
    if not os.path.exists(p): return []
    return [{k: (v if k in ("rid", "case", "grp", "status", "error", "irid", "tier") else fl(v)) for k, v in r.items()} for r in csv.DictReader(open(p))]
D = {t: load(t) for t in TAGS}; D = {t: d for t, d in D.items() if d}
GPU = {t: load_gpu(E, t) for t in D}

def bursts(tag, prefix):
    """group requests of scenario `prefix` by (k, L, rep) -> list of requests"""
    out = {}
    for r in D[tag]:
        if r["grp"] and r["grp"].startswith(prefix) and r["status"] == "200" and r["case"] in ("host", "cold"):
            out.setdefault((r["grp"], int(r["rep"])), []).append(r)
    return out
def burst_stats(tag, reqs):
    t0 = min(r["send_mono"] for r in reqs); t1 = max(r["end_mono"] for r in reqs)
    rs = [r for r in reqs if r.get("retrieve_start_ms") is not None and r.get("retrieve_end_ms") is not None]
    if rs:
        a = min(r["send_mono"] + r["retrieve_start_ms"] / 1000 for r in rs); b = max(r["send_mono"] + r["retrieve_end_ms"] / 1000 for r in rs)
        by = sum(r["retrieve_bytes"] or 0 for r in rs); agg = by / (b - a) / 1e9 if b > a else None
    else: a = b = agg = None; by = 0
    _, Cc = GPU[tag]; rx = sum(c[2] for c in Cc if t0 <= c[0] <= t1); rxbw = rx / (t1 - t0) / 1e9 if t1 > t0 else None
    return dict(k=len(reqs), agg_GBps=agg, span_ms=(b - a) * 1000 if (a and b) else None, bytes_GB=by / 1e9, pcie_rx_GB=rx / 1e9, pcie_rx_GBps=rxbw,
                ttft_p50=q([r["ttft_client_ms"] for r in reqs], .5), ttft_max=max(r["ttft_client_ms"] for r in reqs),
                retr_p50=q([r["retrieve_ms"] for r in rs], .5) if rs else None, retr_max=max(r["retrieve_ms"] for r in rs) if rs else None,
                wait_p50=q([r["kv_load_wait_ms"] for r in reqs if r.get("kv_load_wait_ms") is not None], .5) if any(r.get("kv_load_wait_ms") is not None for r in reqs) else None,
                wait_max=max([r["kv_load_wait_ms"] for r in reqs if r.get("kv_load_wait_ms") is not None] or [0]))

def per_k(tag, L):
    out = {}
    for (grp, rep), reqs in bursts(tag, "e1-").items():
        if int(grp.split("-L")[1]) != L: continue
        k = int(grp.split("-k")[1].split("-")[0]); out.setdefault(k, []).append(burst_stats(tag, reqs))
    return out
def medk(stats, key): v = [s[key] for s in stats if s.get(key) is not None]; return q(v, .5) if v else None

# ---- figE1 / E2 ----
for L in (4096, 8192):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for i, tag in enumerate(D):
        P = per_k(tag, L)
        if not P: continue
        ks = sorted(P)
        axes[0].plot(ks, [medk(P[k], "agg_GBps") for k in ks], marker="o", color=C[i], label=f"{LABEL.get(tag, tag)}: bytes / (first start → last end)")
        axes[0].plot(ks, [medk(P[k], "pcie_rx_GBps") for k in ks], marker="x", ls=":", color=C[i], label=f"{LABEL.get(tag, tag)}: PCIe RX over the whole burst")
        axes[1].plot(ks, [medk(P[k], "retr_p50") for k in ks], marker="o", color=C[i], label=f"{LABEL.get(tag, tag)}: per-request transfer p50")
        axes[1].plot(ks, [medk(P[k], "wait_max") for k in ks], marker="s", ls="--", color=C[i], label=f"{LABEL.get(tag, tag)}: longest KV wait in the burst")
        axes[2].plot(ks, [medk(P[k], "ttft_p50") for k in ks], marker="o", color=C[i], label=f"{LABEL.get(tag, tag)}: TTFT p50"); axes[2].plot(ks, [medk(P[k], "ttft_max") for k in ks], marker="s", ls="--", color=C[i], label=f"{LABEL.get(tag, tag)}: TTFT max")
    axes[0].axhline(12.5 * 1.0737, color="gray", ls="--", lw=1); axes[0].text(1, 12.5 * 1.0737 + 0.2, "cudaMemcpy pinned DRAM → GPU 12.5 GiB/s (2026-10-07)", fontsize=7, color="gray")
    axes[0].set_ylabel("GB/s"); axes[0].set_title("(a) aggregate host → GPU retrieval bandwidth", fontsize=10); axes[0].set_ylim(0, 15)
    axes[1].set_ylabel("ms"); axes[1].set_title("(b) per-request transfer time and KV wait", fontsize=10); axes[1].set_yscale("log")
    axes[2].set_ylabel("ms"); axes[2].set_title("(c) TTFT of the burst's requests", fontsize=10); axes[2].set_yscale("log")
    for ax in axes: ax.set_xlabel("k simultaneous host hits"); ax.set_xscale("log", base=2); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=6.5)
    fig.suptitle(f"Figure E1/E2 — k simultaneous host hits of L = {L} tokens ({L * 36864 / 1e6:.0f} MB each; MEASURED, medians over 4 bursts, 3B-AWQ, 4 output tokens)", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{FIG}/figE1-concurrent-loads-L{L}.png", dpi=300); fig.savefig(f"{FIG}/figE1-concurrent-loads-L{L}.pdf"); plt.close(fig)

# ---- figE3: utilization vs TTFT (all e1 bursts) + e2 mix ----
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))
for i, tag in enumerate(D):
    xs = []; ys = []
    for (grp, rep), reqs in bursts(tag, "e1-").items():
        s = burst_stats(tag, reqs)
        if s["pcie_rx_GBps"] is not None: xs.append(s["pcie_rx_GBps"] / (12.5 * 1.0737)); ys.append(s["ttft_p50"])
    axes[0].scatter(xs, ys, s=14, color=C[i], label=LABEL.get(tag, tag), alpha=.8)
axes[0].set_xlabel("link utilization over the burst (PCIe RX / 13.4 GB/s)"); axes[0].set_ylabel("TTFT p50 of the burst (ms, log)"); axes[0].set_yscale("log"); axes[0].grid(alpha=.3, which="both"); axes[0].legend(fontsize=7); axes[0].set_title("(a) bandwidth utilization vs TTFT, every e1 burst", fontsize=10)
for i, tag in enumerate(D):
    P = {}
    for (grp, rep), reqs in bursts(tag, "e2-").items():
        k = int(grp.split("-k")[1]); hosts = [r for r in reqs if r["case"] == "host"]; colds = [r for r in reqs if r["case"] == "cold"]
        P.setdefault(k, []).append((q([r["ttft_client_ms"] for r in hosts], .5), q([r["ttft_client_ms"] for r in colds], .5), max(r["ttft_client_ms"] for r in hosts)))
    if P:
        ks = sorted(P); axes[1].plot(ks, [q([x[0] for x in P[k]], .5) for k in ks], marker="o", color=C[i], label=f"{LABEL.get(tag, tag)}: host hits p50")
        axes[1].plot(ks, [q([x[2] for x in P[k]], .5) for k in ks], marker="s", ls="--", color=C[i], label=f"{LABEL.get(tag, tag)}: host hits max"); axes[1].plot(ks, [q([x[1] for x in P[k]], .5) for k in ks], marker="^", ls=":", color=C[i], label=f"{LABEL.get(tag, tag)}: cold p50")
axes[1].set_xlabel("k host hits (8k) + k cold prompts (4k) at once"); axes[1].set_ylabel("TTFT (ms, log)"); axes[1].set_yscale("log"); axes[1].set_xscale("log", base=2); axes[1].grid(alpha=.3, which="both"); axes[1].legend(fontsize=6.5); axes[1].set_title("(b) loads beside prefill compute (scenario e2)", fontsize=10)
fig.suptitle("Figure E3 — retrieval bandwidth utilization vs TTFT, and loads competing with prefill (MEASURED)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figE3-utilization-vs-ttft.png", dpi=300); fig.savefig(f"{FIG}/figE3-utilization-vs-ttft.pdf"); plt.close(fig)
print("figures written to", FIG)
