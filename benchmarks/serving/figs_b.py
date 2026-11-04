#!/usr/bin/env python3
"""Figures of Experiment B (controlled concurrent serving) from analyze_b.py's outputs (<tag>-requests.csv,
<tag>-scenarios.csv, <tag>-steps.csv) of the configurations in TAGS.
  figB1  arrival rate vs TTFT p50 / p95 / p99 (open-loop scenario s2), per configuration, and per request type (default)
  figB2  arrival rate vs completed throughput (s2) and concurrency vs throughput (closed loop s1), per configuration
  figB3  concurrency vs GPU busy share (engine steps with tokens) and NVML utilization (s1), per configuration
  figB4  request time lines of the four-request scenario s0 (one repetition per order), default configuration vs one
         alternative: waiting / KV load / ready-but-waiting / prefill per request, with the engine steps underneath
  figB5  queue state over time in the highest-rate open-loop run (default): running, waiting, waiting for KV, with the
         scheduled tokens per step
usage: figs_b.py <B dir> <fig dir> [tags=b-default,b-eager,b-workers4,b-prio-hits,b-prio-cold,b-none]"""
import csv, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

B, FIG = sys.argv[1], sys.argv[2]; os.makedirs(FIG, exist_ok=True)
TAGS = (sys.argv[3].split("=", 1)[1] if len(sys.argv) > 3 else "b-default,b-eager,b-workers4,b-prio-hits,b-prio-cold,b-none").split(",")
LABEL = {"b-default": "default (async load, eager prefetch off, 1 transfer thread)", "b-eager": "eager prefetch (lookup at arrival)", "b-workers4": "4 server transfer threads",
         "b-prio-hits": "priority: hits before cold", "b-prio-cold": "priority: cold before hits", "b-none": "vLLM alone (no host cache)"}
C = plt.rcParams["axes.prop_cycle"].by_key()["color"]
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def load(tag):
    d = {}
    for kind in ("requests", "scenarios", "steps"):
        p = f"{B}/{tag}-{kind}.csv"; d[kind] = [{k: (v if k in ("rid", "case", "grp", "status", "error", "irid", "tier", "tag") else fl(v)) for k, v in r.items()} for r in csv.DictReader(open(p))] if os.path.exists(p) else []
    return d
D = {t: load(t) for t in TAGS}; D = {t: d for t, d in D.items() if d["requests"]}
def scen(tag, prefix):
    out = {}
    for g in D[tag]["scenarios"]:
        if g["grp"].startswith(prefix): out[g["grp"]] = g
    return out
def xval(grp, prefix): return float(grp[len(prefix):])
def q(v, p): v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))]

# ---- figB1 ----
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))
ax = axes[0]
for i, tag in enumerate(D):
    S = scen(tag, "s2-r")
    if not S: continue
    xs = sorted(S, key=lambda g: xval(g, "s2-r")); x = [xval(g, "s2-r") for g in xs]
    for key, ls in (("all_ttft_p50", "-"), ("all_ttft_p95", "--"), ("all_ttft_p99", ":")):
        y = [S[g].get(key) for g in xs]
        if any(v is not None for v in y): ax.plot(x, y, ls=ls, color=C[i % 10], marker="o", ms=3, label=f"{LABEL.get(tag, tag)}" if ls == "-" else None)
ax.set_xlabel("offered arrival rate (requests/s, Poisson)"); ax.set_ylabel("TTFT (ms, log)"); ax.set_yscale("log"); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=7, loc="upper left")
ax.set_title("(a) all requests: p50 (solid), p95 (dashed), p99 (dotted)", fontsize=10)
ax = axes[1]
if "b-default" in D:
    S = scen("b-default", "s2-r"); xs = sorted(S, key=lambda g: xval(g, "s2-r")); x = [xval(g, "s2-r") for g in xs]
    for j, (ty, name) in enumerate((("host", "host (DRAM) hit"), ("gpu", "GPU prefix hit"), ("cold", "cold (recompute)"), ("part", "partial hit"))):
        for key, ls in ((f"{ty}_ttft_p50", "-"), (f"{ty}_ttft_p95", "--")):
            y = [S[g].get(key) for g in xs]
            if any(v is not None for v in y): ax.plot(x, [v if v is not None else float("nan") for v in y], ls=ls, color=C[j], marker="o", ms=3, label=name if ls == "-" else None)
ax.set_xlabel("offered arrival rate (requests/s)"); ax.set_yscale("log"); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=8); ax.set_title("(b) default configuration, by the tier that served the request (p50 solid, p95 dashed)", fontsize=10)
fig.suptitle("Figure B1 — arrival rate vs TTFT (MEASURED, open-loop mixed sequence of 96 requests: 50 % pool hits / 50 % cold, L ∈ {1k, 2k, 4k, 8k}, 32 output tokens, 3B-AWQ)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figB1-rate-vs-ttft.png", dpi=300); fig.savefig(f"{FIG}/figB1-rate-vs-ttft.pdf"); plt.close(fig)

# ---- figB2 ----
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))
for i, tag in enumerate(D):
    S = scen(tag, "s2-r")
    if S:
        xs = sorted(S, key=lambda g: xval(g, "s2-r")); axes[0].plot([xval(g, "s2-r") for g in xs], [S[g]["prompt_tok_per_s"] for g in xs], color=C[i % 10], marker="o", ms=3, label=LABEL.get(tag, tag))
    S = scen(tag, "s1-c")
    if S:
        xs = sorted(S, key=lambda g: xval(g, "s1-c")); axes[1].plot([xval(g, "s1-c") for g in xs], [S[g]["req_per_s"] for g in xs], color=C[i % 10], marker="o", ms=3, label=LABEL.get(tag, tag))
axes[0].set_xlabel("offered arrival rate (requests/s)"); axes[0].set_ylabel("completed prompt tokens / s"); axes[0].set_title("(a) open loop: prompt-token throughput over the run", fontsize=10)
axes[1].set_xlabel("closed-loop concurrency"); axes[1].set_ylabel("completed requests / s"); axes[1].set_title("(b) closed loop: request throughput (64 requests)", fontsize=10); axes[1].set_xscale("log", base=2)
for ax in axes: ax.grid(alpha=.3); ax.legend(fontsize=7)
fig.suptitle("Figure B2 — serving throughput per configuration (MEASURED; the same request sequences in every run)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figB2-throughput.png", dpi=300); fig.savefig(f"{FIG}/figB2-throughput.pdf"); plt.close(fig)

# ---- figB3 ----
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))
for i, tag in enumerate(D):
    S = scen(tag, "s1-c")
    if not S: continue
    xs = sorted(S, key=lambda g: xval(g, "s1-c")); x = [xval(g, "s1-c") for g in xs]
    axes[0].plot(x, [S[g]["gpu_busy_steps"] for g in xs], color=C[i % 10], marker="o", ms=3, label=LABEL.get(tag, tag))
    axes[0].plot(x, [S[g]["gpu_util_nvml"] for g in xs], color=C[i % 10], marker="x", ms=3, ls=":")
    axes[1].plot(x, [S[g].get("all_ttft_p50") for g in xs], color=C[i % 10], marker="o", ms=3, label=LABEL.get(tag, tag)); axes[1].plot(x, [S[g].get("all_ttft_p95") for g in xs], color=C[i % 10], marker="o", ms=3, ls="--")
axes[0].set_xlabel("closed-loop concurrency"); axes[0].set_ylabel("share of wall time"); axes[0].set_title("(a) GPU busy: engine steps with tokens (solid) and NVML utilization (dotted)", fontsize=10); axes[0].set_ylim(0, 1.05)
axes[1].set_xlabel("closed-loop concurrency"); axes[1].set_ylabel("TTFT (ms, log)"); axes[1].set_yscale("log"); axes[1].set_title("(b) TTFT p50 (solid) / p95 (dashed)", fontsize=10)
for ax in axes: ax.grid(alpha=.3, which="both"); ax.legend(fontsize=7); ax.set_xscale("log", base=2)
fig.suptitle("Figure B3 — GPU utilization and TTFT vs concurrency (MEASURED, closed loop, mixed sequence)", fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/figB3-gpu-vs-concurrency.png", dpi=300); fig.savefig(f"{FIG}/figB3-gpu-vs-concurrency.pdf"); plt.close(fig)

# ---- figB4 ----
def timeline_panel(ax, tag, grp, rep):
    R = [r for r in D[tag]["requests"] if r["grp"] == grp and r["rep"] == rep and r["case"] in ("host", "gpu", "cold")]
    if not R: ax.text(0.5, 0.5, "no data", ha="center"); return
    R.sort(key=lambda r: r["send_mono"]); t0 = min(r["send_mono"] for r in R)
    rows = []
    for k, r in enumerate(R):
        base = (r["send_mono"] - t0) * 1000; y = len(R) - k
        segs = []
        if r.get("queued_ms") is not None:
            segs.append((base, base + r["queued_ms"], C[7], "client → engine queue"))
            if r.get("kv_wait_ms") is not None:
                segs.append((base + r["queued_ms"], base + r["kv_wait_ms"], C[0], "waiting (lookup pending / not yet scheduled)"))
                if r.get("kv_arrived_ms") is not None:
                    segs.append((base + r["kv_wait_ms"], base + r["kv_arrived_ms"], C[1], "KV load in flight (host → GPU)"))
                    if r.get("scheduled_ms") is not None: segs.append((base + r["kv_arrived_ms"], base + r["scheduled_ms"], C[3], "KV ready, waiting for the GPU"))
            elif r.get("scheduled_ms") is not None: segs.append((base + r["queued_ms"], base + r["scheduled_ms"], C[0], "waiting (lookup pending / not yet scheduled)"))
            if r.get("scheduled_ms") is not None and r.get("first_token_engine_ms") is not None: segs.append((base + r["scheduled_ms"], base + r["first_token_engine_ms"], C[2], "scheduled → first token (prefill)"))
        for a, b, col, lab in segs: ax.barh(y, b - a, left=a, color=col, height=0.6, label=lab)
        ax.text(base + r["ttft_client_ms"] + 3, y, f"{r['rid'].split('-')[-1]} {r['tier']} L={int(r['L'])}  TTFT {r['ttft_client_ms']:.0f} ms", va="center", fontsize=7)
    steps = [s for s in D[tag]["steps"] if s["t_end"] is not None and s["tok"] > 0 and s["t1"] >= t0 - 0.05 and s["t1"] <= t0 + max(r["ttft_client_ms"] for r in R) / 1000 + 0.3]
    for s in steps: ax.barh(0, (s["t_end"] - s["t1"]) * 1000, left=(s["t1"] - t0) * 1000, color="k", alpha=0.5, height=0.4)
    ax.text(0, -0.55, "GPU steps with tokens (engine)", fontsize=7)
    ax.set_yticks([]); ax.set_xlabel("ms after the first request of the burst was sent"); ax.grid(alpha=.3, axis="x")
tags4 = [t for t in ("b-default", "b-prio-hits", "b-eager") if t in D][:2]
if tags4:
    orders = ["s0-ABCD", "s0-DCBA", "s0-CADB"]
    fig, axes = plt.subplots(len(orders), len(tags4), figsize=(6.2 * len(tags4), 2.6 * len(orders)), squeeze=False)
    for j, tag in enumerate(tags4):
        for i, o in enumerate(orders):
            timeline_panel(axes[i][j], tag, o, 0); axes[i][j].set_title(f"{LABEL.get(tag, tag)} — order {o[3:]}", fontsize=9)
    h, l = axes[0][0].get_legend_handles_labels(); seen = {}; [seen.setdefault(lab, hh) for hh, lab in zip(h, l)]
    fig.legend(seen.values(), seen.keys(), fontsize=7, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 0.995))
    fig.suptitle("Figure B4 — the four-request burst (A = 8k host hit, B = 1k GPU hit, C = 4k cold, D = 4k host hit, sent 5 ms apart; MEASURED time lines, repetition 0)", fontsize=9, y=0.955)
    fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(f"{FIG}/figB4-timelines.png", dpi=300); fig.savefig(f"{FIG}/figB4-timelines.pdf"); plt.close(fig)

# ---- figB5 ----
if "b-default" in D:
    S = scen("b-default", "s2-r")
    if S:
        gmax = max(S, key=lambda g: xval(g, "s2-r")); R = [r for r in D["b-default"]["requests"] if r["grp"] == gmax]
        t0 = min(r["send_mono"] for r in R); t1 = max(r["end_mono"] for r in R)
        steps = [s for s in D["b-default"]["steps"] if t0 <= s["t1"] <= t1]
        fig, axes = plt.subplots(2, 1, figsize=(12, 5.5), sharex=True)
        x = [(s["t1"] - t0) for s in steps]
        axes[0].plot(x, [s["run"] for s in steps], label="running (in the batch)", color=C[2], lw=1)
        axes[0].plot(x, [s["wait"] + s["hold"] for s in steps], label="waiting (fresh + holding KV blocks)", color=C[0], lw=1)
        axes[0].plot(x, [s["wfr"] for s in steps], label="waiting for a KV load (WAITING_FOR_REMOTE_KVS)", color=C[1], lw=1)
        for r in R: axes[0].axvline(r["send_mono"] - t0, color="gray", alpha=0.25, lw=0.5)
        axes[0].set_ylabel("requests"); axes[0].legend(fontsize=8, loc="upper right"); axes[0].grid(alpha=.3); axes[0].set_title(f"{LABEL['b-default']} — open loop at {xval(gmax, 's2-r'):g} req/s (grey ticks = arrivals)", fontsize=10)
        axes[1].bar(x, [s["tok"] for s in steps], width=[(s["t_end"] - s["t1"]) if s["t_end"] else 0.01 for s in steps], align="edge", color=C[7]); axes[1].set_ylabel("tokens scheduled per engine step"); axes[1].set_xlabel("s after the first arrival"); axes[1].grid(alpha=.3)
        fig.suptitle("Figure B5 — queue state over time (MEASURED from the engine-step log)", fontsize=9)
        fig.tight_layout(); fig.savefig(f"{FIG}/figB5-queue-state.png", dpi=300); fig.savefig(f"{FIG}/figB5-queue-state.pdf"); plt.close(fig)
print("figures written to", FIG)
