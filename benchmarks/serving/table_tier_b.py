#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12), Experiments B and E: tables and figures of the trace replays.
Reads <B>/<tag>-tier.json, <tag>-tier-requests.csv, <tag>-traffic.csv (analyze_tier_replay.py) of the runs b-<group>-<config> and writes
  <B>/tables-b.md   per group (trace x load): hit shares by source, recomputed tokens, TTFT p50 / p95 / p99 / mean, request time,
                    throughput, GPU busy share, backlog, tier occupancy and evictions; host memory and CPU; TTFT by hit class
  <B>/tables-e.md   KV read / write traffic per medium: bytes, busy seconds, peak second, read-write overlap
  <figs>/figB1-capacity-share.png  cached prompt-token share against the KV capacity of the configuration (with the offline LRU model
                                   of the window, <results>/trace-model/trace-capacity.csv); figB1b-hit-sources.png: the share by source
  <figs>/figB2-ttft.png            TTFT p50 / mean / p95 / p99 per configuration; figB2b-ttft-cdf.png: the distributions
  <figs>/figB3-throughput.png      completed requests/s, output tokens/s, computed prompt tokens/s
  <figs>/figB4-recomputed.png      recomputed prompt tokens against the KV capacity
  <figs>/figB5-occupancy.png       L1 and L2 occupancy over the replay, evicted KV per tier
  <figs>/figE1-traffic.png         per-second KV bytes read from / written to the extension tier
KV capacity of a configuration = GPU pool (3.52 GiB) + what the host tiers hold at their 0.8 eviction trigger: 64 GiB (80 GiB DRAM),
473.6 GiB (592 GiB hybrid L1 or DRAM), 409.6 GiB (512 GiB L2; write-through, so the L2 holds a superset of L1).
usage: table_tier_b.py <B dir> <figs dir> [group ...]      (default groups: conv08 tool08 conv04 tool04 conv08L)"""
import csv, json, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

B, FIGS = sys.argv[1:3]; os.makedirs(FIGS, exist_ok=True)
GROUPS = {"conv08": "conversation, trace 0–400 s at 0.08× (overload)", "tool08": "tool-agent, trace 0–400 s at 0.08× (overload)",
          "conv04": "conversation, trace 0–200 s at 0.04× (sustainable)", "tool04": "tool-agent, trace 0–200 s at 0.04× (sustainable)",
          "conv08L": "conversation, LONG window: trace 0–900 s at 0.08× (overload; 1,043 GiB of KV produced, the extension tiers fill and evict)"}
CONFIGS = [("none", "recompute only\n(vLLM alone)"), ("dram80", "DRAM only\n80 GiB"), ("hyb", "DRAM + CXL\nhybrid L1"), ("daxl2", "DRAM + CXL\nL2 adapter"), ("ssdn", "DRAM + NVMe\nL2 adapter"),
           ("dram592", "DRAM only\n592 GiB (ref.)"), ("dram20", "DRAM only\n20 GiB"), ("hyb20", "20 GiB DRAM + CXL\nhybrid L1"), ("ssdn20", "20 GiB DRAM + NVMe\nL2 adapter")]
COL = {c: f"C{i}" for i, (c, _) in enumerate(CONFIGS)}        # one colour per configuration in every panel and figure
GPU_GIB = 3.52
CAP = {"none": GPU_GIB, "dram20": GPU_GIB + 16, "dram80": GPU_GIB + 64, "dram592": GPU_GIB + 473.6, "hyb": GPU_GIB + 473.6, "hyb20": GPU_GIB + 0.8 * 532, "daxl2": GPU_GIB + 409.6, "ssdn": GPU_GIB + 409.6, "ssdn20": GPU_GIB + 409.6}
WINDOW = {"conv08": ("conv", 400), "tool08": ("tool", 400), "conv04": ("conv", 200), "tool04": ("tool", 200), "conv08L": ("conv", 900)}
def model(g):
    """offline LRU model of the group's trace window: [(capacity GiB, share)], and the prompt tokens of the window"""
    p = os.path.join(os.path.dirname(os.path.abspath(B.rstrip("/"))), "trace-model", "trace-capacity.csv")
    if g not in WINDOW or not os.path.exists(p): return [], None
    tr, w = WINDOW[g]; rows = [r for r in csv.DictReader(open(p)) if r["trace"] == tr and int(r["window_s"]) == w and r["cap_GiB"] != "inf"]
    return [(float(r["cap_GiB"]), float(r["share"])) for r in rows], (float(rows[0]["prompt_Mtok"]) if rows else None)
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
def joined(g, c):
    """per request index: the tier split (tier-requests.csv) joined with the time line (requests.csv of analyze_b.py)"""
    R = {r["rid"].rsplit("-", 1)[1]: r for r in reqs(g, c)}; p = f"{B}/b-{g}-{c}-requests.csv"
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            i = r["rid"].rsplit("-", 1)[1]
            if i in R:
                for k in ("queue_to_sched_ms", "kv_load_wait_ms", "ready_to_sched_ms", "retrieve_ms", "prefill_ms", "kv_end_to_sched_ms"):
                    try: R[i][k] = float(r[k])
                    except Exception: R[i][k] = None
    for r in R.values():
        n = r["prompt_tokens"] or 1; r["ext"] = (r["tok_cxl_l1"] or 0) + (r["tok_l2"] or 0); r["host"] = r["ext"] + (r["tok_dram"] or 0) + (r["tok_unknown"] or 0)
        r["cls"] = "ext" if r["ext"] >= 0.5 * n else "dram" if (r["tok_dram"] or 0) >= 0.5 * n else "gpu" if max(0, (r["cached_tokens"] or 0) - r["host"]) >= 0.5 * n else "miss" if (r["cached_tokens"] or 0) < 0.1 * n else "part"
    return R
BINS = [(0, 4096, "< 4K"), (4096, 8192, "4K–8K"), (8192, 16384, "8K–16K"), (16384, 10**9, "≥ 16K")]
PAIRS = [("hyb", "ssdn"), ("daxl2", "ssdn"), ("hyb", "daxl2"), ("hyb", "dram80"), ("ssdn", "dram80"), ("dram80", "none"), ("hyb", "dram592"), ("hyb20", "ssdn20"), ("hyb20", "dram20"), ("ssdn20", "dram20")]
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
          "| configuration | extension tier (CXL L1 or L2) | DRAM tier | GPU prefix | miss (< 10 % cached) | L2 prefetch inside the cache server, all requests that loaded from the L2: p50 / p95 / max ms (n) |", "|---|---|---|---|---|---|"]
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
        s_ = d[c]; T.append(f"| {flat(c)} | {cell(cls['ext'])} | {cell(cls['dram'])} | {cell(cls['gpu'])} | {cell(cls['miss'])} | " + (f"{f(s_.get('l2_ms_p50'))} / {f(s_.get('l2_ms_p95'))} / {f(s_.get('l2_ms_max'))} ({s_.get('l2_requests_loaded')})" if s_.get("l2_requests_loaded") else "–") + " |")
    J = {c: joined(g, c) for c, _ in CONFIGS if c in d and c != "none"}
    if "none" in d: J["none"] = joined(g, "none")
    T += ["", "Requests served mainly from the extension tier (at least half of the prompt from CXL L1 objects or from the L2): parts of the TTFT, p50 ms (n). "
          "The lookup interval ends at the poll of vLLM's scheduler that finds the prefetch complete, so it contains the wait for that poll; the L2 prefetch is the part inside the cache server.", "",
          "| configuration | n | TTFT | lookup interval | of which L2 prefetch | GPU transfer | queued → scheduled | KV ready → scheduled | scheduled → first token |", "|---|---|---|---|---|---|---|---|---|"]
    for c, _ in CONFIGS:
        if c not in J or c == "none": continue
        e = [r for r in J[c].values() if r["cls"] == "ext"]
        if not e: continue
        m = lambda k: f(q([r[k] for r in e if r.get(k) not in ("", None)], .5), 0)
        T.append(f"| {flat(c)} | {len(e)} | {m('ttft_ms')} | {m('lookup_ms')} | {m('l2_ms')} | {m('retrieve_ms')} | {m('queue_to_sched_ms')} | {m('ready_to_sched_ms')} | {m('prefill_ms')} |")
    T += ["", "The same requests by the length of the prefix that came from the extension tier — L2 prefetch p50 / lookup interval p50 / TTFT p50 in ms (n):", "", "| configuration | " + " | ".join(b[2] for b in BINS) + " |", "|---|" + "---|" * len(BINS)]
    for c, _ in CONFIGS:
        if c not in J or c == "none": continue
        cells = []
        for lo, hi, _ in BINS:
            e = [r for r in J[c].values() if r["cls"] == "ext" and lo <= r["ext"] < hi]
            cells.append(f"{f(q([r['l2_ms'] for r in e if r.get('l2_ms') not in ('', None)], .5), 0)} / {f(q([r['lookup_ms'] for r in e if r.get('lookup_ms') not in ('', None)], .5), 0)} / {f(q([r['ttft_ms'] for r in e], .5), 0)} ({len(e)})" if e else "–")
        if any(x != "–" for x in cells): T.append(f"| {flat(c)} | " + " | ".join(cells) + " |")
    T += ["", "Paired comparison, the same request of the trace in two configurations (first minus second; negative = the first is faster):", "",
          "| pair | requests | mean TTFT difference s | median difference s | share of requests faster in the first | requests that are extension-tier hits in both | their median TTFT difference ms | their median lookup-interval difference ms |", "|---|---|---|---|---|---|---|---|"]
    for a, b in PAIRS:
        if a not in J or b not in J: continue
        ks = [k for k in J[a] if k in J[b]]
        if not ks: continue
        dd = [J[a][k]["ttft_ms"] - J[b][k]["ttft_ms"] for k in ks]; both = [k for k in ks if J[a][k]["cls"] == "ext" and J[b][k]["cls"] == "ext"]
        de = [J[a][k]["ttft_ms"] - J[b][k]["ttft_ms"] for k in both]; dl = [J[a][k]["lookup_ms"] - J[b][k]["lookup_ms"] for k in both if J[a][k].get("lookup_ms") not in ("", None) and J[b][k].get("lookup_ms") not in ("", None)]
        T.append(f"| {flat(a)} − {flat(b)} | {len(ks)} | {sum(dd) / len(dd) / 1000:+.2f} | {q(dd, .5) / 1000:+.2f} | {sum(1 for x in dd if x < 0) / len(dd):.2f} | {len(both)} | {f(q(de, .5), 0)} | {f(q(dl, .5), 0)} |")
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
    # B1 capacity -> cached share (measured points, offline LRU model of the window as a line); B4 recomputed tokens -> capacity
    for name, title, ylab, val, mval in (("figB1-capacity-share", "B1  KV capacity and cached prompt-token share", "cached share of the prompt tokens", lambda s_: s_["cached_share"], lambda sh, mt: sh),
                                         ("figB4-recomputed", "B4  KV capacity and recomputed prompt tokens", "recomputed prompt tokens (millions)", lambda s_: s_["tok_recomputed"] / 1e6, lambda sh, mt: (1 - sh) * mt)):
        fig, axes = panels(4.3)
        for ax, (g, d) in zip(axes, D.items()):
            m, mt = model(g)
            if m: ax.plot([GPU_GIB + x if x > GPU_GIB else x for x, _ in m], [mval(sh, mt) for _, sh in m], color="gray", linestyle="--", linewidth=1, label="offline LRU model of the window (not a measurement)")
            for c, _ in CONFIGS:
                if c in d and c in CAP: ax.plot([CAP[c]], [val(d[c])], marker="o" if not c.startswith("ssd") else "s", markersize=8, linestyle="", color=COL[c], label=flat(c))
            ax.set_xscale("log", base=2); ax.set_xlabel("KV capacity: GPU pool + host tiers at their eviction trigger (GiB)"); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, which="both", alpha=0.3); ax.set_ylim(bottom=0)
        axes[0].set_ylabel(ylab); h, l = axes[0].get_legend_handles_labels()
        for ax in axes[1:]:
            for hh, ll in zip(*ax.get_legend_handles_labels()):
                if ll not in l: h.append(hh); l.append(ll)
        fig.legend(h, l, loc="lower center", ncol=min(5, len(l)), frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.09)); fig.suptitle(title); fig.tight_layout(rect=(0, 0.02, 1, 0.97)); fig.savefig(f"{FIGS}/{name}.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B1b hit sources
    fig, axes = panels(4.4)
    src = [("share_gpu_prefix", "GPU prefix cache"), ("share_dram", "DRAM tier"), ("share_cxl_l1", "CXL (L1 objects)"), ("share_l2", "L2 adapter (CXL or NVMe)"), ("share_recomputed", "recomputed")]
    for ax, (g, d) in zip(axes, D.items()):
        cs = [c for c, _ in CONFIGS if c in d]; bottom = [0.0] * len(cs)
        for k, name in src:
            v = [d[c][k] + (d[c].get("share_unknown", 0) if k == "share_dram" else 0) for c in cs]
            ax.bar(range(len(cs)), v, bottom=bottom, label=name, width=0.7, color="lightgray" if k == "share_recomputed" else None); bottom = [b + x for b, x in zip(bottom, v)]
        ax.set_xticks(range(len(cs))); ax.set_xticklabels([lab[c] for c in cs], fontsize=6.5); ax.set_ylim(0, 1); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel("share of prompt tokens"); h, l = axes[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.05))
    fig.suptitle("B1b  Where the prompt tokens came from"); fig.tight_layout(rect=(0, 0.02, 1, 0.96)); fig.savefig(f"{FIGS}/figB1b-hit-sources.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B2 TTFT quantiles
    fig, axes = panels(4.2)
    for ax, (g, d) in zip(axes, D.items()):
        cs = [c for c, _ in CONFIGS if c in d]; W = 0.2
        for i, (k, name) in enumerate((("ttft_p50", "p50"), ("ttft_mean", "mean"), ("ttft_p95", "p95"), ("ttft_p99", "p99"))):
            ax.bar([x + (i - 1.5) * W for x in range(len(cs))], [d[c][k] / 1000 for c in cs], width=W, label=name)
        ax.set_xticks(range(len(cs))); ax.set_xticklabels([lab[c] for c in cs], fontsize=6.5); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel("TTFT (s)"); axes[0].legend(frameon=False, fontsize=8, ncol=4); fig.suptitle("B2  TTFT by configuration"); fig.tight_layout(); fig.savefig(f"{FIGS}/figB2-ttft.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B2b CDFs
    fig, axes = panels(4.2)
    for ax, (g, d) in zip(axes, D.items()):
        for c, _ in CONFIGS:
            if c not in d: continue
            v = sorted(r["ttft_ms"] / 1000 for r in reqs(g, c))
            if v: ax.plot(v, [(i + 1) / len(v) for i in range(len(v))], label=flat(c), color=COL[c])
        ax.set_xscale("log"); ax.set_xlabel("TTFT (s)"); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, which="both", alpha=0.3); ax.legend(frameon=False, fontsize=7, loc="upper left")
    axes[0].set_ylabel("share of requests"); fig.suptitle("B2b  TTFT distributions"); fig.tight_layout(); fig.savefig(f"{FIGS}/figB2b-ttft-cdf.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B3 throughput
    fig, axs = plt.subplots(3, ng, figsize=(5.6 * ng, 7.6), squeeze=False)
    for j, (g, d) in enumerate(D.items()):
        cs = [c for c, _ in CONFIGS if c in d]
        for i, (k, name) in enumerate((("req_per_s", "completed requests/s"), ("out_tok_per_s", "output tokens/s"), ("computed_tok_per_s", "computed prompt tokens/s"))):
            ax = axs[i][j]; ax.bar(range(len(cs)), [d[c][k] for c in cs], width=0.6, color=[COL[c] for c in cs]); ax.set_xticks(range(len(cs))); ax.set_xticklabels([lab[c] for c in cs] if i == 2 else [], fontsize=6.5); ax.grid(True, axis="y", alpha=0.3)
            if j == 0: ax.set_ylabel(name)
            if i == 0: ax.set_title(GROUPS.get(g, g), fontsize=9)
    fig.suptitle("B3  Throughput by configuration (same offered load in every configuration of a panel)"); fig.tight_layout(); fig.savefig(f"{FIGS}/figB3-throughput.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # B5 occupancy over time (top) and evicted KV per tier (bottom)
    fig, axs = plt.subplots(2, ng, figsize=(5.6 * ng, 7.0), squeeze=False)
    for j, (g, d) in enumerate(D.items()):
        ax = axs[0][j]
        for c, _ in CONFIGS:
            if c not in d or c == "none": continue
            p = f"{B}/b-{g}-{c}-traffic.csv"
            if not os.path.exists(p): continue
            rows = list(csv.DictReader(open(p))); t = [int(r["second"]) for r in rows if r["l1_used_bytes"] != ""]
            l1 = [float(r["l1_used_bytes"]) / 2**30 for r in rows if r["l1_used_bytes"] != ""]; ax.plot(t, l1, label=f"{flat(c)}: L1", color=COL[c], linewidth=1)
            l2 = [(int(r["second"]), float(r["l2_used_bytes"]) / 2**30) for r in rows if r["l2_used_bytes"] != ""]
            if l2: ax.plot([x for x, _ in l2], [y for _, y in l2], linestyle="--", color=COL[c], linewidth=1, label=f"{flat(c)}: L2")
        ax.set_xlabel("replay time (s)"); ax.set_title(GROUPS.get(g, g), fontsize=9); ax.grid(True, alpha=0.3); ax.legend(frameon=False, fontsize=6.5, loc="upper left")
        if j == 0: ax.set_ylabel("KV held (GiB)")
        ax = axs[1][j]; cs = [c for c, _ in CONFIGS if c in d and c != "none"]; W = 0.27
        for i, (name, fn) in enumerate((("L1 objects on DRAM", lambda s_: s_["l1_evict_dram_GiB"]), ("L1 objects on CXL", lambda s_: s_["l1_evict_cxl_GiB"]), ("L2 (CXL slots or NVMe files)", lambda s_: s_["l2_evicted_keys"] * 9 / 1024))):
            ax.bar([x + (i - 1) * W for x in range(len(cs))], [fn(d[c]) for c in cs], width=W, label=name)
        ax.set_xticks(range(len(cs))); ax.set_xticklabels([lab[c] for c in cs], fontsize=6.5); ax.grid(True, axis="y", alpha=0.3)
        if j == 0: ax.set_ylabel("KV evicted over the replay (GiB)"); ax.legend(frameon=False, fontsize=7.5)
    fig.suptitle("B5  Cache occupancy and evictions"); fig.tight_layout(); fig.savefig(f"{FIGS}/figB5-occupancy.png", dpi=150, bbox_inches="tight"); plt.close(fig)
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
