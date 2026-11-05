#!/usr/bin/env python3
"""Figures of Experiment D (host-cache capacity) and the real-trace part of B from replay-summary.csv (analyze_replay.py).
  figD1  capacity vs cached-token share (total, from the host tier, from the GPU prefix cache) per trace
  figD2  capacity vs TTFT p50 / p95 / p99, with the vLLM-alone and SSD-backed references
  figD3  capacity vs computed prompt tokens per second and completed requests per second
  figD4  capacity vs KV traffic on the GPU link (retrieved bytes, PCIe RX; stored bytes, PCIe TX) and host-cache evictions
  figBR  the real-trace scheduler configurations (default 40 GB vs eager prefetch vs 4 transfer threads): TTFT and waits
usage: figs_d.py <replay dir> <fig dir>"""
import csv, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

R, FIG = sys.argv[1], sys.argv[2]; os.makedirs(FIG, exist_ok=True)
rows = {}
for r in csv.DictReader(open(f"{R}/replay-summary.csv")):
    rows[r["tag"]] = {k: (v if k == "tag" else (float(v) if v not in ("", None) else None)) for k, v in r.items()}
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
TR = {"conv": "Mooncake conversation", "tool": "Mooncake tool-agent"}
def cap_series(tr):
    out = []
    for t, r in rows.items():
        if t.startswith(f"d-{tr}-dram"): out.append((float(t.split("dram")[1]), r))
    return sorted(out)
def ref(tr, kind): return rows.get(f"d-{tr}-{kind}")

def panel(ax, key_list, ylabel, title, logy=False, refs=("none", "ssd"), legend_loc="best"):
    for i, tr in enumerate(TR):
        S = cap_series(tr)
        if not S: continue
        x = [c for c, _ in S]
        for key, ls, name in key_list:
            y = [r.get(key) for _, r in S]
            if any(v is not None for v in y): ax.plot(x, [v if v is not None else float("nan") for v in y], ls=ls, marker="o", ms=4, color=C[i], label=f"{TR[tr]}: {name}")
        for kind, mk in zip(refs, ("x", "^")):
            r = ref(tr, kind)
            if r and r.get(key_list[0][0]) is not None: ax.plot([x[-1] * 1.6], [r[key_list[0][0]]], marker=mk, ms=8, ls="none", color=C[i], label=f"{TR[tr]}: {'vLLM alone' if kind == 'none' else 'SSD-backed (fs L2, O_DIRECT)'}")
    ax.set_xscale("log", base=2); ax.set_xlabel("host-cache (L1) capacity, GB of pinned DRAM (references drawn right of the axis)"); ax.set_ylabel(ylabel); ax.set_title(title, fontsize=10); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=6.5, loc=legend_loc)
    if logy: ax.set_yscale("log")

fig, ax = plt.subplots(figsize=(7.5, 4.4))
panel(ax, [("cached_share", "-", "cached share of prompt tokens (vLLM)"), ("host_share", "--", "served from the host tier"), ("local_share", ":", "served from the GPU prefix cache")], "share of prompt tokens", "cached prompt tokens vs host-cache capacity", refs=("none",))
fig.suptitle("Figure D1 — capacity vs KV-cache hit share\n(MEASURED replay: trace seconds 0–100 at 0.08×, 3B-AWQ, LMCache LRU, watermark 0.8)", fontsize=9); fig.tight_layout(); fig.savefig(f"{FIG}/figD1-capacity-vs-hit.png", dpi=300); fig.savefig(f"{FIG}/figD1-capacity-vs-hit.pdf"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.5, 4.4))
panel(ax, [("ttft_p50", "-", "TTFT p50"), ("ttft_p95", "--", "TTFT p95"), ("ttft_p99", ":", "TTFT p99")], "ms (log)", "TTFT vs host-cache capacity", logy=True, legend_loc="center left")
fig.suptitle("Figure D2 — capacity vs TTFT (MEASURED replay, offered load unchanged across runs)", fontsize=9); fig.tight_layout(); fig.savefig(f"{FIG}/figD2-capacity-vs-ttft.png", dpi=300); fig.savefig(f"{FIG}/figD2-capacity-vs-ttft.pdf"); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
panel(axes[0], [("computed_tok_per_s", "-", "prompt tokens computed / s")], "tokens / s", "(a) prefill work the GPU actually did")
panel(axes[1], [("gpu_busy_steps", "-", "GPU busy (engine steps with tokens)")], "share of wall time", "(b) GPU busy share")
fig.suptitle("Figure D3 — capacity vs computed prefill work and GPU busy share\n(MEASURED replay; the request rate is the trace's, so throughput = offered load unless the server falls behind)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figD3-capacity-vs-throughput.png", dpi=300); fig.savefig(f"{FIG}/figD3-capacity-vs-throughput.pdf"); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
panel(axes[0], [("retrieve_GB", "-", "KV retrieved host → GPU (LMCache retrieve events)"), ("store_GB", "--", "KV stored GPU → host (LMCache store events)")], "GB over the window", "(a) KV traffic between host cache and GPU", refs=("ssd",))
panel(axes[1], [("evicted_chunks", "-", "evicted 256-token chunks")], "chunks", "(b) host-cache evictions", refs=())
fig.suptitle("Figure D4 — capacity vs KV retrieval traffic and evictions (MEASURED replay)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figD4-capacity-vs-traffic.png", dpi=300); fig.savefig(f"{FIG}/figD4-capacity-vs-traffic.pdf"); plt.close(fig)

# real-trace scheduler configurations
cfgs = [("d-{tr}-dram40", "default (40 GB)"), ("br-{tr}-eager", "eager prefetch"), ("br-{tr}-workers4", "4 transfer threads")]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
for i, tr in enumerate(TR):
    names = []; vals = {k: [] for k in ("ttft_p50", "ttft_p95", "ttft_p99", "kv_load_wait_ms_p50", "ready_to_sched_ms_p50", "queue_to_sched_ms_p50")}
    for t, name in cfgs:
        r = rows.get(t.format(tr=tr))
        if not r: continue
        names.append(name); [vals[k].append(r.get(k)) for k in vals]
    if not names: continue
    x = [j + i * 0.35 for j in range(len(names))]
    for k, ls, mk in (("ttft_p50", "-", "o"), ("ttft_p95", "--", "s"), ("ttft_p99", ":", "^")):
        axes[0].plot(x, [v if v is not None else float("nan") for v in vals[k]], ls=ls, marker=mk, color=C[i], label=f"{TR[tr]}: {k[5:]}")
    for k, ls, mk in (("kv_load_wait_ms_p50", "-", "o"), ("ready_to_sched_ms_p50", "--", "s"), ("queue_to_sched_ms_p50", ":", "^")):
        axes[1].plot(x, [v if v is not None else float("nan") for v in vals[k]], ls=ls, marker=mk, color=C[i], label=f"{TR[tr]}: {k.replace('_ms_p50', '').replace('_', ' ')} (p50)")
    for ax in axes: ax.set_xticks([j + 0.17 for j in range(len(names))]); ax.set_xticklabels(names, fontsize=8)
axes[0].set_ylabel("ms (log)"); axes[0].set_yscale("log"); axes[0].set_title("(a) TTFT", fontsize=10); axes[1].set_ylabel("ms (log)"); axes[1].set_yscale("log"); axes[1].set_title("(b) KV load wait, ready → scheduled, queue → scheduled", fontsize=10)
for ax in axes: ax.grid(alpha=.3, which="both"); ax.legend(fontsize=6.5)
fig.suptitle("Figure BR — real-trace replay under the supported scheduler / connector configurations (MEASURED, 40 GB DRAM L1)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figBR-trace-configs.png", dpi=300); fig.savefig(f"{FIG}/figBR-trace-configs.pdf"); plt.close(fig)
print("figures written to", FIG)

# figD0: offline reuse potential of the traces vs cache capacity (TRACE ANALYSIS from trace_reuse.py --csv), for the replayed
# 0-100 s windows (Experiment D at 0.08x), the 0-200 s windows (lighter-load sweep) and the full hour
if os.path.exists(f"{R}/trace-reuse.csv"):
    T = [r for r in csv.DictReader(open(f"{R}/trace-reuse.csv"))]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=False)
    for i, tr in enumerate(TR):
        ax = axes[i]
        for w, ls in ((100, ":"), (200, "--"), (3600, "-")):
            rr = [r for r in T if r["trace"] == tr and int(r["window_s"]) == w and r["cap_gb"] != "inf"]
            inf = [float(r["share"]) for r in T if r["trace"] == tr and int(r["window_s"]) == w and r["cap_gb"] == "inf"]
            ax.plot([float(r["cap_gb"]) for r in rr], [float(r["share"]) for r in rr], ls=ls, marker="o", ms=3, color=C[i], label=f"window 0–{w} s ({rr[0]['n']} requests); unbounded cache {inf[0]:.3f}")
        ax.axvline(4.49, color="gray", ls="--", lw=1); ax.text(4.49 * 1.08, 0.56, "GPU KV cache of the 4060 Ti\n(121,792 tokens = 4.5 GB)", fontsize=7, color="gray")
        ax.axvline(80, color="gray", ls=":", lw=1); ax.text(80 * 1.08, 0.56, "largest DRAM L1\nreplayed (80 GB)", fontsize=7, color="gray")
        ax.axvline(1160, color="gray", ls="-.", lw=1); ax.text(1160 * 1.08, 0.56, "c28's 4× CZ120\n(1.06 TiB)", fontsize=7, color="gray")
        ax.set_xscale("log", base=2); ax.set_xlabel("LRU cache capacity, GB of KV at 36 KiB/token (3B-AWQ; ×8.9 for a 70B fp16 model)", fontsize=8); ax.set_ylabel("reusable share of prompt tokens"); ax.set_title(f"{TR[tr]}", fontsize=10); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(0, 0.88)); ax.set_ylim(0, 0.65)
    fig.suptitle("Figure D0 — prefix reuse the traces offer vs cache capacity (TRACE ANALYSIS: LRU over 512-token hash blocks, prefix semantics, prompts cut at 31,736 tokens; not a measurement)", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{FIG}/figD0-trace-reuse-vs-capacity.png", dpi=300); fig.savefig(f"{FIG}/figD0-trace-reuse-vs-capacity.pdf"); plt.close(fig)
    print("figD0 written")
