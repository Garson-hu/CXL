#!/usr/bin/env python3
"""Figures of Experiment A (single-request KV retrieval cost) from the timeline CSVs written by analyze_a.py.
  figA1  prefix length vs TTFT (client, median; whiskers = min / max over repetitions) per path and model
  figA2  prefix length vs the retrieval stages of a host hit (lookup, L2->L1 prefetch for the SSD tier, GPU transfer)
         and the effective transfer bandwidth
  figA3  stage breakdown of one request (medians) for the cold / GPU-hit / DRAM-hit / SSD-hit paths at three lengths
usage: figs_a.py <A dir> <fig dir>"""
import csv, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

A, FIG = sys.argv[1], sys.argv[2]; os.makedirs(FIG, exist_ok=True)
def load(tag):
    p = f"{A}/{tag}-timeline.csv"
    if not os.path.exists(p): return []
    rows = []
    for r in csv.DictReader(open(p)):
        for k, v in r.items():
            if k in ("rid", "case", "grp", "status", "error", "irid"): continue
            r[k] = float(v) if v not in ("", None) else None
        if r["status"] == "200": rows.append(r)
    return rows
def med(v): v = sorted(v); return v[len(v) // 2] if v else None
def series(rows, case, key):
    out = {}
    for r in rows:
        if r["case"] == case and r.get(key) is not None: out.setdefault(int(r["L"]), []).append(r[key])
    Ls = sorted(out); return Ls, [med(out[L]) for L in Ls], [med(out[L]) - min(out[L]) for L in Ls], [max(out[L]) - med(out[L]) for L in Ls]
R = {t: load(t) for t in ("a-3b-dram", "a-3b-ssd", "a-3b-ssd-odirect", "a-3b-none", "a-15b-dram", "a-3b-dram-nohooks")}
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]

# ---- figA1 ----
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
for ax, (title, items) in zip(axes, [("Qwen2.5-3B-Instruct-AWQ", [("a-3b-dram", "cold", "recompute (cold, LMCache DRAM tier)", C[0], "-"), ("a-3b-none", "cold", "recompute, vLLM alone", C[0], ":"),
                                                                   ("a-3b-dram", "host", "host hit: DRAM L1", C[1], "-"), ("a-3b-ssd-odirect", "host", "host hit: SSD (fs L2 on NVMe, O_DIRECT)", C[3], "-"), ("a-3b-ssd", "host", "host hit: SSD files in the page cache", C[3], ":"),
                                                                   ("a-3b-dram", "gpu", "GPU prefix-cache hit (LMCache in the loop)", C[2], "-"), ("a-3b-none", "gpu", "GPU prefix-cache hit, vLLM alone", C[2], ":")]),
                                   ("Qwen2.5-1.5B-Instruct (fp16)", [("a-15b-dram", "cold", "recompute (cold)", C[0], "-"), ("a-15b-dram", "host", "host hit: DRAM L1", C[1], "-"), ("a-15b-dram", "gpu", "GPU prefix-cache hit", C[2], "-")])]):
    for tag, case, label, col, ls in items:
        Ls, m, lo, hi = series(R[tag], case, "ttft_client_ms")
        if Ls: ax.errorbar(Ls, m, yerr=[lo, hi], label=label, color=col, ls=ls, marker="o", ms=4, capsize=2, lw=1.4)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("prefix length L (tokens)"); ax.set_title(title, fontsize=10); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=7.5, loc="upper left")
    ax.set_xticks([256, 512, 1024, 2048, 4096, 8192, 16384]); ax.set_xticklabels(["256", "512", "1k", "2k", "4k", "8k", "16k"])
axes[0].set_ylabel("TTFT at the client (ms, log)")
fig.suptitle("Figure A1 — TTFT of one request vs prefix length and where the prefix comes from\n(MEASURED, c28 RTX 4060 Ti, 8 output tokens, median with min/max whiskers over 8 repetitions; the link is kept at PCIe Gen 4 by the sampler)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figA1-ttft-vs-length.png", dpi=300); fig.savefig(f"{FIG}/figA1-ttft-vs-length.pdf"); plt.close(fig)

# ---- figA2 ----
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
ax = axes[0]
for tag, label, col in (("a-3b-dram", "DRAM L1", C[1]), ("a-3b-ssd-odirect", "SSD L2 (O_DIRECT)", C[3])):
    rows = R[tag]
    for key, name, ls in (("lookup_ms", "lookup (hash + index)", ":"), ("retrieve_ms", "GPU transfer (retrieve start→end on the stream)", "-"), ("ttft_client_ms", "TTFT", "--")):
        Ls, m, lo, hi = series(rows, "host", key)
        if Ls: ax.errorbar(Ls, m, yerr=[lo, hi], label=f"{label}: {name}", color=col, ls=ls, marker="o", ms=3, capsize=2, lw=1.3)
    # L2 -> L1 prefetch + queueing between lookup end and retrieve start
    rows_h = [r for r in rows if r["case"] == "host" and r.get("lookup_end_ms") is not None and r.get("retrieve_start_ms") is not None]
    out = {}
    for r in rows_h: out.setdefault(int(r["L"]), []).append(r["retrieve_start_ms"] - r["lookup_end_ms"])
    if out:
        Ls = sorted(out); ax.plot(Ls, [med(out[L]) for L in Ls], label=f"{label}: lookup end → transfer start" + (" (= disk read into L1)" if tag == "a-3b-ssd" else ""), color=col, ls="-.", marker="s", ms=3, lw=1.3)
ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("prefix length L (tokens)"); ax.set_ylabel("ms (log)"); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=7, loc="upper left")
ax.set_xticks([256, 512, 1024, 2048, 4096, 8192, 16384]); ax.set_xticklabels(["256", "512", "1k", "2k", "4k", "8k", "16k"]); ax.set_title("(a) stages of a host hit, 3B-AWQ (median; whiskers min/max)", fontsize=10)
ax = axes[1]
for tag, label, col in (("a-3b-dram", "DRAM L1 → GPU", C[1]), ("a-3b-ssd-odirect", "SSD L2 → L1 → GPU (transfer part)", C[3]), ("a-15b-dram", "DRAM L1 → GPU, 1.5B", C[4])):
    Ls, m, lo, hi = series(R[tag], "host", "retrieve_GBps")
    if Ls: ax.errorbar(Ls, m, yerr=[lo, hi], label=label, color=col, marker="o", ms=4, capsize=2, lw=1.4)
ax.axhline(12.5 * 1.0737, color="gray", ls="--", lw=1); ax.text(300, 12.5 * 1.0737 + 0.3, "cudaMemcpy pinned DRAM → GPU, 12.5 GiB/s (2026-10-07; CXL devdax identical)", fontsize=7, color="gray")
ax.set_xscale("log", base=2); ax.set_xlabel("prefix length L (tokens)"); ax.set_ylabel("effective transfer bandwidth (GB/s = bytes / transfer time)"); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=8, loc="lower right"); ax.set_ylim(0, 15)
ax.set_xticks([256, 512, 1024, 2048, 4096, 8192, 16384]); ax.set_xticklabels(["256", "512", "1k", "2k", "4k", "8k", "16k"]); ax.set_title("(b) effective host → GPU bandwidth of one retrieve", fontsize=10)
fig.suptitle("Figure A2 — KV retrieval latency and bandwidth vs prefix length\n(MEASURED; LMCache 0.5.5 server-driven CUDA-IPC transfer kernel, PCIe 4.0 ×8; 3B-AWQ unless stated)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figA2-retrieval-vs-length.png", dpi=300); fig.savefig(f"{FIG}/figA2-retrieval-vs-length.pdf"); plt.close(fig)

# ---- figA3 ----
STAGES = [("client → vLLM arrival", lambda r: r.get("arrival_ms")), ("arrival → queued (engine)", lambda r: r["queued_ms"] - r["arrival_ms"] if r.get("queued_ms") is not None and r.get("arrival_ms") is not None else None),
          ("queued → lookup end", lambda r: r["lookup_end_ms"] - r["queued_ms"] if r.get("lookup_end_ms") is not None and r.get("queued_ms") is not None else None),
          ("lookup end → transfer start", lambda r: r["retrieve_start_ms"] - r["lookup_end_ms"] if r.get("retrieve_start_ms") is not None and r.get("lookup_end_ms") is not None else None),
          ("host → GPU transfer", lambda r: r.get("retrieve_ms")), ("transfer end → scheduled", lambda r: r.get("kv_end_to_sched_ms")),
          ("queued → scheduled (no host load)", lambda r: r["scheduled_ms"] - r["queued_ms"] if r.get("retrieve_ms") is None and r.get("scheduled_ms") is not None and r.get("queued_ms") is not None else None),
          ("scheduled → first token (prefill / 1-token step)", lambda r: r.get("prefill_ms")), ("engine → client", lambda r: r.get("engine_to_client_ms"))]
paths = [("GPU prefix hit\n(vLLM alone)", "a-3b-none", "gpu"), ("GPU prefix hit\n(LMCache in the loop)", "a-3b-dram", "gpu"), ("DRAM L1 hit", "a-3b-dram", "host"), ("SSD L2 hit\n(O_DIRECT)", "a-3b-ssd-odirect", "host"), ("SSD L2 hit\n(page cache)", "a-3b-ssd", "host")]
Lsel = [1024, 4096, 16384]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.4), sharey=False)
for ax, L in zip(axes, Lsel):
    xs = []; bottoms = []
    for pi, (pname, tag, case) in enumerate(paths):
        rows = [r for r in R[tag] if r["case"] == case and int(r["L"]) == L]
        if not rows: continue
        xs.append(pname); b = 0.0
        for si, (sname, f) in enumerate(STAGES):
            v = [f(r) for r in rows]; v = [x for x in v if x is not None]
            if not v: continue
            m = med(v); ax.bar(len(xs) - 1, m, bottom=b, color=C[si % 10], label=sname if pi == 0 or (pi == 2 and si in (2, 3, 4, 5)) else None, width=0.6); b += m
        tt = med([r["ttft_client_ms"] for r in rows]); ax.text(len(xs) - 1, b, f"TTFT {tt:.0f} ms", ha="center", va="bottom", fontsize=7)
    cold = [r["ttft_client_ms"] for r in R["a-3b-dram"] if r["case"] == "cold" and int(r["L"]) == L]
    ax.set_xticks(range(len(xs))); ax.set_xticklabels(xs, fontsize=7); ax.set_title(f"L = {L} tokens  (recompute from scratch: TTFT {med(cold):.0f} ms)" if cold else f"L = {L} tokens", fontsize=9); ax.grid(alpha=.3, axis="y")
    if L == Lsel[0]: ax.set_ylabel("ms after the client's send (medians of each stage)")
h, l = axes[0].get_legend_handles_labels(); h2, l2 = axes[1].get_legend_handles_labels()
seen = {}; [seen.setdefault(lab, hh) for hh, lab in list(zip(h, l)) + list(zip(h2, l2))]
fig.legend(seen.values(), seen.keys(), fontsize=7, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 0.97))
fig.suptitle("Figure A3 — where one request's TTFT goes on the hit paths (MEASURED, 3B-AWQ; each stage is the median of its instants, so the stack adds up to ~ the median TTFT)", fontsize=9, y=1.0)
fig.tight_layout(rect=(0, 0, 1, 0.88)); fig.savefig(f"{FIG}/figA3-stage-breakdown.png", dpi=300); fig.savefig(f"{FIG}/figA3-stage-breakdown.pdf"); plt.close(fig)
print("figures written to", FIG)
