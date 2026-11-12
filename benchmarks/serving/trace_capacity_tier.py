#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12): TRACE-DRIVEN capacity analysis (a cache model, not a measurement) for the capacities of the study.
For a Mooncake trace window it replays the prompts through an LRU over 512-token hash blocks with prefix semantics (trace_reuse.py)
at a list of KV capacities and reports the share of prompt tokens a cache of that size could serve. Because an LRU hierarchy is
inclusive, the share a tier adds is the difference between two capacities:
    GPU prefix cache (6,400 blocks = 3.52 GiB)  ->  + DRAM tier (80 GiB nominal, 64 GiB at the 0.8 watermark)
    ->  + extension tier (512 GiB nominal: 409.6 GiB effective as an L2, 473.6 GiB effective for the 592 GiB hybrid L1)  ->  unbounded
Windows: the replayed ones (0-400 s, 0-200 s) and longer ones that were NOT replayed (0-900 s ... 0-3,600 s), to show what longer
replays would exercise. 36 KiB of KV per token (Qwen2.5-3B, fp16).
usage: trace_capacity_tier.py <out.csv> <fig.png>"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trace_reuse.py")).read().split('if __name__ == "__main__":')[0]
ns = {}; exec(src, ns)
BPT, ML, GIB = 36864, 31736, 2**30
CAPS = [3.52, 8, 16, 32, 51.2, 64, 80, 128, 160, 240, 320, 409.6, 473.6, 512, 592, 768, 1024, 0]      # GiB; 0 = unbounded
WINDOWS = [200, 400, 900, 1800, 3600]
rows = []
for name, tr in ns["TRACES"]:
    for t1 in WINDOWS:
        reqs = ns["load"](tr, 0, t1, ML); tot = sum(n for _, _, n in reqs)
        for g in CAPS:
            s, nr, _ = ns["run"](reqs, int(g * GIB / (512 * BPT)) if g else 0)
            rows.append(dict(trace=name, window_s=t1, requests=len(reqs), prompt_Mtok=round(tot / 1e6, 2), kv_produced_GiB=round(tot * BPT / GIB), cap_GiB=(g if g else "inf"), share=round(s, 4), req_half_hit=nr))
        print(name, t1, "done", flush=True)
with open(sys.argv[1], "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), sharey=True)
for ax, name, title in ((axes[0], "conv", "conversation"), (axes[1], "tool", "tool-agent")):
    for t1 in WINDOWS:
        g = [r for r in rows if r["trace"] == name and r["window_s"] == t1 and r["cap_GiB"] != "inf"]
        ax.plot([r["cap_GiB"] for r in g], [r["share"] for r in g], marker=".", label=f"0–{t1} s ({g[0]['requests']} requests, {g[0]['kv_produced_GiB']} GiB of KV)" + ("" if t1 <= 400 else ", not replayed"), linestyle="-" if t1 <= 400 else "--")
    for x, lab, ha in ((3.52, "GPU pool 3.5 GiB", "left"), (64, "DRAM tier: 80 GiB, 64 effective", "right"), (409.6, "+ 512 GiB L2: 409.6 effective", "right"), (473.6, "hybrid L1 592 GiB: 473.6 effective", "left")):
        ax.axvline(x, color="gray", linewidth=0.8, linestyle=":"); ax.text(x * (0.96 if ha == "right" else 1.04), 0.022, lab, rotation=90, fontsize=6.5, va="bottom", ha=ha, color="dimgray")
    ax.set_xscale("log", base=2); ax.set_xlabel("KV cache capacity (GiB, LRU)"); ax.set_title(f"{title} trace", fontsize=10); ax.grid(True, which="both", alpha=0.3); ax.legend(frameon=False, fontsize=7, loc="upper left", bbox_to_anchor=(0.08, 1.0))
axes[0].set_ylabel("share of prompt tokens a cache of that size can serve"); fig.suptitle("Trace-driven capacity model (offline LRU, prefix semantics; not a measurement)")
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=150, bbox_inches="tight")
