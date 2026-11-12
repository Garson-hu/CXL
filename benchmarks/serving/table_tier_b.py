#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12), Experiments B and E: tables and figures of the trace replays.
Reads <B>/<tag>-tier.json, <tag>-tier-requests.csv, <tag>-traffic.csv (analyze_tier_replay.py) of the runs b-<group>-<config> and writes
  <B>/tables-b.md   per group (trace x load): hit shares by source, recomputed tokens, TTFT p50 / p95 / p99 / mean, request time,
                    throughput, GPU busy share, backlog, tier occupancy and evictions; host memory and CPU; TTFT by hit class
  <B>/tables-e.md   KV read / write traffic per medium: bytes, busy seconds, peak second, read-write overlap
  <figs>/figB1-hit-sources.png     share of prompt tokens by source, per configuration (capacity -> hit rate)
  <figs>/figB2-ttft.png            TTFT p50 / p95 / p99 / mean per configuration
  <figs>/figB3-ttft-cdf.png        TTFT CDFs
  <figs>/figB4-throughput.png      completed requests/s, output tokens/s, computed prompt tokens/s
  <figs>/figB5-occupancy.png       L1 and L2 occupancy over the replay
  <figs>/figE1-traffic.png         per-second KV bytes read from / written to the extension tier
usage: table_tier_b.py <B dir> <figs dir> [group ...]      (default groups: conv08 tool08 conv04 tool04)"""
import csv, json, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

B, FIGS = sys.argv[1:3]; os.makedirs(FIGS, exist_ok=True)
GROUPS = {"conv08": "conversation, trace 0–400 s at 0.08× (overload)", "tool08": "tool-agent, trace 0–400 s at 0.08× (overload)",
          "conv04": "conversation, trace 0–200 s at 0.04× (sustainable)", "tool04": "tool-agent, trace 0–200 s at 0.04× (sustainable)"}
CONFIGS = [("none", "recompute only\n(vLLM alone)"), ("dram80", "DRAM only\n80 GiB"), ("hyb", "DRAM + CXL\nhybrid L1"), ("daxl2", "DRAM + CXL\nL2 adapter"), ("ssdn", "DRAM + NVMe\nL2 adapter"),
           ("dram592", "DRAM only\n592 GiB (ref.)"), ("ssdn-retain", "DRAM + NVMe\nL2, promotion"), ("daxl2-retain", "DRAM + CXL\nL2, promotion")]
groups = sys.argv[3:] or list(GROUPS)
def load(g, c):
    p = f"{B}/b-{g}-{c}-tier.json"
    return json.load(open(p)) if os.path.exists(p) else None
def reqs(g, c):
    p = f"{B}/b-{g}-{c}-tier-requests.csv"; out = []
    if os.path.exists(p):
        for r in csv.DictReader(open(p)): out.append({k: (float(v) if v not in ("", None) and k != "rid" else v) for k, v in r.items()})
    return out
def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else None
def f(v, d=1, s=1.0): return "-" if v is None or v == "" else f"{v * s:.{d}f}"
D = {g: {c: load(g, c) for c, _ in CONFIGS} for g in groups}; D = {g: {c: s for c, s in d.items() if s} for g, d in D.items()}; D = {g: d for g, d in D.items() if d}
lab = dict(CONFIGS); flat = lambda c: lab[c].replace("\n", " ")

T = ["# Experiment B — end-to-end cache expansion (trace replays; one run per cell)", ""]
E = ["# Experiment E — KV read / write traffic per medium during the replays of Experiment B", ""]
for g, d in D.items():
    T += [f"## {GROUPS.get(g, g)}", "",
          "| configuration | requests ok / all | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed tok/s | GPU busy | backlog max |", "|" + "---|" * 19]
    for c, _ in CONFIGS:
        s = d.get(c)
        if not s: continue
        T.append(f"| {flat(c)} | {s['n_ok']} / {s['n']} | {s['cached_share']:.3f} | {s['share_gpu_prefix']:.3f} | {s['share_dram']:.3f} | {s['share_cxl_l1']:.3f} | {s['share_l2']:.3f} | {s['tok_recomputed'] / 1e6:.2f} | "
                 f"{s['ttft_p50'] / 1000:.2f} | {s['ttft_p95'] / 1000:.2f} | {s['ttft_p99'] / 1000:.2f} | {s['ttft_mean'] / 1000:.2f} | {s['total_ms_p50'] / 1000:.2f} | {s['total_ms_p95'] / 1000:.2f} | {s['req_per_s']:.3f} | {s['out_tok_per_s']:.0f} | "
                 f"{s['computed_tok_per_s']:.0f} | {f(s.get('gpu_busy_steps'), 2)} | {s['backlog_max']} |")
    T += ["", "| configuration | L1 max GiB (of) | L2 max GiB (of) | L1 evicted GiB DRAM / CXL | L2 evicted keys | L1 written GiB DRAM / CXL | L2 stored / loaded GiB | LMCache RSS max GiB (anon + shmem) | vLLM RSS max GiB | MemAvailable min GiB | page cache growth GiB | LMCache CPU s (cores) | NVMe device read / written GiB |", "|" + "---|" * 13]
    for c, _ in CONFIGS:
        s = d.get(c)
        if not s or c == "none": continue
        T.append(f"| {flat(c)} | {f(s.get('l1_used_GiB_max'))} ({f(s.get('l1_total_GiB'), 0)}) | {f(s.get('l2_used_GiB_max'))} ({f(s.get('l2_capacity_GiB'), 0)}) | {s['l1_evict_dram_GiB']:.1f} / {s['l1_evict_cxl_GiB']:.1f} | {s['l2_evicted_keys']} | "
                 f"{s['l1_write_dram_GiB']:.1f} / {s['l1_write_cxl_GiB']:.1f} | {s['l2_store_GiB']:.1f} / {s['l2_load_GiB']:.1f} | {f(s.get('lm_rss_GiB_max'))} ({f(s.get('lm_rss_anon_GiB_max'))} + {f(s.get('lm_rss_shmem_GiB_max'))}) | {f(s.get('rss_GiB_max_vllm'))} | "
                 f"{f(s.get('mem_available_GiB_min'), 0)} | {f(s.get('page_cache_growth_GiB'), 2)} | {f(s.get('lm_cpu_s'), 0)} ({f(s.get('lm_cpu_cores'), 2)}) | {f(s.get('nvme_dev_read_GiB'))} / {f(s.get('nvme_dev_write_GiB'))} |")
    # TTFT by hit class: where at least half of the prompt came from
    T += ["", "TTFT by the dominant source of the prompt (a request is in a class when at least half of its prompt tokens came from that source; p50 s, n):", "",
          "| configuration | extension tier (CXL L1 or L2) | DRAM tier | GPU prefix | miss (< 10 % cached) | lookup time of extension-tier hits p50 / p95 ms |", "|---|---|---|---|---|---|"]
    for c, _ in CONFIGS:
        if c not in d or c == "none": continue
        R = reqs(g, c)
        if not R: continue
        cls = {"ext": [], "dram": [], "gpu": [], "miss": []}; lk = []
        for r in R:
            n = r["prompt_tokens"] or 1; ext = (r["tok_cxl_l1"] or 0) + (r["tok_l2"] or 0); host = ext + (r["tok_dram"] or 0) + (r["tok_unknown"] or 0); gpu = max(0, (r["cached_tokens"] or 0) - host)
            if ext >= 0.5 * n:
                cls["ext"].append(r["ttft_ms"])
                if r.get("lookup_ms") not in ("", None): lk.append(r["lookup_ms"])
            elif (r["tok_dram"] or 0) >= 0.5 * n: cls["dram"].append(r["ttft_ms"])
            elif gpu >= 0.5 * n: cls["gpu"].append(r["ttft_ms"])
            elif (r["cached_tokens"] or 0) < 0.1 * n: cls["miss"].append(r["ttft_ms"])
        cell = lambda v: f"{q(v, .5) / 1000:.2f} ({len(v)})" if v else "- (0)"
        T.append(f"| {flat(c)} | {cell(cls['ext'])} | {cell(cls['dram'])} | {cell(cls['gpu'])} | {cell(cls['miss'])} | {f(q(lk, .5))} / {f(q(lk, .95))} |")
    T.append("")
    E += [f"## {GROUPS.get(g, g)}", "",
          "| configuration | medium | read GiB | write GiB | read busy s | write busy s | read GiB/s while busy | write GiB/s while busy | peak read GiB in 1 s | peak write GiB in 1 s | seconds with both | read-write overlap s | H2D GiB | D2H GiB | H2D-D2H overlap s | replay s |", "|" + "---|" * 16]
    for c, _ in CONFIGS:
        s = d.get(c)
        if not s or c == "none": continue
        for m, name in (("cxl", "CXL"), ("nvme", "NVMe")):
            if not (s.get(f"{m}_r_GiB") or s.get(f"{m}_w_GiB")): continue
            E.append(f"| {flat(c)} | {name} | {s[f'{m}_r_GiB']:.1f} | {s[f'{m}_w_GiB']:.1f} | {s[f'{m}_r_busy_s']:.1f} | {s[f'{m}_w_busy_s']:.1f} | {f(s.get(f'{m}_r_busy_GiBps'), 2)} | {f(s.get(f'{m}_w_busy_GiBps'), 2)} | {s[f'{m}_r_peak_GiB_s']:.2f} | {s[f'{m}_w_peak_GiB_s']:.2f} | "
                     f"{s[f'{m}_rw_same_second']} | {s[f'{m}_rw_overlap_s']:.2f} | {s['h2d_GiB']:.1f} | {s['d2h_GiB']:.1f} | {s['h2d_d2h_overlap_s']:.2f} | {s['wall_s']:.0f} |")
    E.append("")
open(f"{B}/tables-b.md", "w").write("\n".join(T) + "\n"); open(f"{B}/tables-e.md", "w").write("\n".join(E) + "\n")

ng = len(D)
if ng:
    def panels(h=4.0, w=5.6): 
        fig, axes = plt.subplots(1, ng, figsize=(w * ng, h), squeeze=False); return fig, axes[0]
    # B1 hit sources
    fig, axes = panels(4.4)
    src = [("share_gpu_prefix", "GPU prefix cache"), ("share_dram", "DRAM tier"), ("share_cxl_l1", "CXL (L1 objects)"), ("share_l2", "L2 adapter (CXL or NVMe)"), ("share_recomputed", "recomputed")]
    for ax, (g, d) in zip(axes, D.items()):
        cs = [c for c, _ in CONFIGS if c in d]; bottom = [0.0] * len(cs)
        for k, name in src:
            v = [d[c][k] + (d[c].get("share_unknown", 0) if k == "share_dram" else 0) for c in cs]
            ax.bar(range(len(cs)), v, bottom=bottom, label=name, width=0.7, color="lightgray" if k == "share_recomputed" else None); bottom = [b + x for b, x in zip(bottom, v)]
        ax.set_xticks(range(len(cs))); ax.set_xticklabels([lab[c] for c in cs], fontsize=7); ax.set_ylim(0, 1); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel("share of prompt tokens"); h, l = axes[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.05))
    fig.suptitle("B1  Where the prompt tokens came from"); fig.tight_layout(rect=(0, 0.02, 1, 0.96)); fig.savefig(f"{FIGS}/figB1-hit-sources.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B2 TTFT quantiles
    fig, axes = panels(4.2)
    for ax, (g, d) in zip(axes, D.items()):
        cs = [c for c, _ in CONFIGS if c in d]; W = 0.2
        for i, (k, name) in enumerate((("ttft_p50", "p50"), ("ttft_mean", "mean"), ("ttft_p95", "p95"), ("ttft_p99", "p99"))):
            ax.bar([x + (i - 1.5) * W for x in range(len(cs))], [d[c][k] / 1000 for c in cs], width=W, label=name)
        ax.set_xticks(range(len(cs))); ax.set_xticklabels([lab[c] for c in cs], fontsize=7); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel("TTFT (s)"); axes[0].legend(frameon=False, fontsize=8, ncol=4); fig.suptitle("B2  TTFT by configuration"); fig.tight_layout(); fig.savefig(f"{FIGS}/figB2-ttft.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B3 CDFs
    fig, axes = panels(4.2)
    for ax, (g, d) in zip(axes, D.items()):
        for c, _ in CONFIGS:
            if c not in d: continue
            v = sorted(r["ttft_ms"] / 1000 for r in reqs(g, c))
            if v: ax.plot(v, [(i + 1) / len(v) for i in range(len(v))], label=flat(c))
        ax.set_xscale("log"); ax.set_xlabel("TTFT (s)"); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("share of requests"); axes[-1].legend(frameon=False, fontsize=7, loc="lower right"); fig.suptitle("B3  TTFT distributions"); fig.tight_layout(); fig.savefig(f"{FIGS}/figB3-ttft-cdf.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B4 throughput
    fig, axs = plt.subplots(3, ng, figsize=(5.6 * ng, 7.6), squeeze=False)
    for j, (g, d) in enumerate(D.items()):
        cs = [c for c, _ in CONFIGS if c in d]
        for i, (k, name) in enumerate((("req_per_s", "completed requests/s"), ("out_tok_per_s", "output tokens/s"), ("computed_tok_per_s", "computed prompt tokens/s"))):
            ax = axs[i][j]; ax.bar(range(len(cs)), [d[c][k] for c in cs], width=0.6); ax.set_xticks(range(len(cs))); ax.set_xticklabels([lab[c] for c in cs] if i == 2 else [], fontsize=7); ax.grid(True, axis="y", alpha=0.3)
            if j == 0: ax.set_ylabel(name)
            if i == 0: ax.set_title(GROUPS.get(g, g), fontsize=9)
    fig.suptitle("B4  Throughput by configuration (same offered load in every configuration of a panel)"); fig.tight_layout(); fig.savefig(f"{FIGS}/figB4-throughput.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B5 occupancy and E1 traffic over time
    fig, axes = panels(4.0)
    for ax, (g, d) in zip(axes, D.items()):
        for c, _ in CONFIGS:
            if c not in d or c == "none": continue
            p = f"{B}/b-{g}-{c}-traffic.csv"
            if not os.path.exists(p): continue
            rows = list(csv.DictReader(open(p))); t = [int(r["second"]) for r in rows if r["l1_used_bytes"] != ""]
            l1 = [float(r["l1_used_bytes"]) / 2**30 for r in rows if r["l1_used_bytes"] != ""]; line, = ax.plot(t, l1, label=f"{flat(c)}: L1")
            l2 = [(int(r["second"]), float(r["l2_used_bytes"]) / 2**30) for r in rows if r["l2_used_bytes"] != ""]
            if l2: ax.plot([x for x, _ in l2], [y for _, y in l2], linestyle="--", color=line.get_color(), label=f"{flat(c)}: L2")
        ax.set_xlabel("replay time (s)"); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("KV held (GiB)"); axes[-1].legend(frameon=False, fontsize=7); fig.suptitle("B5  Cache occupancy over the replay"); fig.tight_layout(); fig.savefig(f"{FIGS}/figB5-occupancy.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    ext = [c for c in ("hyb", "daxl2", "ssdn") if any(c in d for d in D.values())]
    if ext:
        fig, axs = plt.subplots(len(ext), ng, figsize=(5.6 * ng, 2.6 * len(ext)), squeeze=False)
        for i, c in enumerate(ext):
            for j, (g, d) in enumerate(D.items()):
                ax = axs[i][j]; p = f"{B}/b-{g}-{c}-traffic.csv"
                if c in d and os.path.exists(p):
                    rows = list(csv.DictReader(open(p))); m = "nvme" if c.startswith("ssd") else "cxl"; bw = 10
                    t = list(range(0, len(rows), bw)); agg = lambda k: [sum(float(r[k]) for r in rows[a:a + bw]) / bw / 2**20 for a in t]
                    ax.plot(t, agg(f"{m}_write_bytes"), label="written", linewidth=0.9); ax.plot(t, agg(f"{m}_read_bytes"), label="read", linewidth=0.9)
                ax.grid(True, alpha=0.3)
                if j == 0: ax.set_ylabel(f"{flat(c)}\nMiB/s (10 s mean)", fontsize=8)
                if i == 0: ax.set_title(GROUPS.get(g, g), fontsize=9)
                if i == len(ext) - 1: ax.set_xlabel("replay time (s)")
        axs[0][-1].legend(frameon=False, fontsize=8); fig.suptitle("E1  KV traffic of the extension tier over the replay"); fig.tight_layout(); fig.savefig(f"{FIGS}/figE1-traffic.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print("\n".join(T)[:5000])
