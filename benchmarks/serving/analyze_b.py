#!/usr/bin/env python3
"""Per-run analysis of the concurrent-serving experiments (B, E, and the trace replays): joins the records with
analyze_a.timeline, classifies the tier that actually served each request, and summarizes every scenario group (the
`grp` field of the client record, or the whole run) with TTFT percentiles per type, throughput, the KV-load waits and
the GPU busy share from the engine-step log and from NVML.
Tier served:  gpu   vLLM's cached_tokens >= 90 % of the prompt and at most one 256-token chunk retrieved from LMCache
              host  more than one chunk retrieved from LMCache (DRAM L1 or the fs L2 in the ssd tier)
              cold  cached_tokens < 10 % of the prompt and nothing retrieved
              part  anything else (a partial hit)
Outputs <out>/<tag>-requests.csv, <out>/<tag>-scenarios.csv, <out>/<tag>-steps.csv (per step) and prints the summary.
usage: analyze_b.py <out> <tag> [more tags ...]"""
import csv, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_a import load_run, timeline, q, COLS

def tier(r):
    L = r["prompt_tokens"] or 1; c = r.get("vllm_cached") if r.get("vllm_cached") is not None else (r.get("cached_tokens") or 0)
    rt = r.get("retrieve_tokens") or 0
    if rt > 256: return "host"
    if c >= 0.9 * L: return "gpu"
    if c < 0.1 * L and rt == 0: return "cold"
    return "part"

def load_steps(out, tag):
    steps = []; ends = {}
    for f in glob.glob(f"{out}/{tag}-vllmevt.step.*.jsonl"):
        for l in open(f):
            d = json.loads(l)
            if d.get("ev") == "step": steps.append(d)
            elif d.get("ev") == "end": ends[d["i"]] = d["t"]
    for s in steps: s["t_end"] = ends.get(s["i"])
    return sorted(steps, key=lambda s: s["i"])

def load_gpu(out, tag):
    U = []; C = []
    p = f"{out}/{tag}-gpu.txt"
    if os.path.exists(p):
        for l in open(p):
            if l.startswith("U "): _, t, g, m, mem = l.split(); U.append((int(t) / 1e9, int(g), int(mem)))
            elif l.startswith("C "): _, t, tx, rx = l.split(); C.append((int(t) / 1e9, int(tx), int(rx)))
    return U, C

def gpu_busy(steps, t_lo, t_hi):
    """share of [t_lo, t_hi] (monotonic s) covered by engine steps that scheduled tokens (schedule end -> model output)"""
    busy = 0.0
    for s in steps:
        if s["tok"] > 0 and s["t_end"] is not None:
            a, b = max(s["t1"], t_lo), min(s["t_end"], t_hi)
            if b > a: busy += b - a
    return busy / (t_hi - t_lo) if t_hi > t_lo else None

def summarize_group(rows, steps, U, C):
    ok = [r for r in rows if r["status"] == 200 and r["case"] not in ("flush", "warm", "populate", "gpuwarm")]
    if not ok: return None
    t_lo = min(r["send_mono"] for r in ok); t_hi = max(r["end_mono"] for r in ok)
    g = {"n": len(ok), "n_err": sum(1 for r in rows if r["status"] != 200), "window_s": t_hi - t_lo, "req_per_s": len(ok) / (t_hi - t_lo) if t_hi > t_lo else None,
         "prompt_tok_per_s": sum(r["prompt_tokens"] for r in ok) / (t_hi - t_lo) if t_hi > t_lo else None, "gpu_busy_steps": gpu_busy(steps, t_lo, t_hi)}
    u = [x[1] for x in U if t_lo <= x[0] <= t_hi]; g["gpu_util_nvml"] = sum(u) / len(u) / 100 if u else None
    rx = sum(x[2] for x in C if t_lo <= x[0] <= t_hi); g["pcie_rx_GB"] = rx / 1e9; g["pcie_rx_GBps"] = rx / 1e9 / (t_hi - t_lo) if t_hi > t_lo else None
    for ty in ("all", "host", "gpu", "cold", "part"):
        sel = ok if ty == "all" else [r for r in ok if r["tier"] == ty]
        if not sel: continue
        tt = [r["ttft_client_ms"] for r in sel]
        g[f"{ty}_n"] = len(sel); g[f"{ty}_ttft_p50"] = q(tt, .5); g[f"{ty}_ttft_p95"] = q(tt, .95); g[f"{ty}_ttft_p99"] = q(tt, .99); g[f"{ty}_ttft_mean"] = sum(tt) / len(tt)
        for k in ("queue_to_sched_ms", "retrieve_ms", "kv_load_wait_ms", "ready_to_sched_ms", "prefill_ms", "lookup_ms"):
            v = [r[k] for r in sel if r.get(k) is not None]
            if v: g[f"{ty}_{k}_p50"] = q(v, .5); g[f"{ty}_{k}_p95"] = q(v, .95)
    return g

def analyze(out, tag):
    cl, req, steps_req, ev, off = load_run(out, tag); steps = load_steps(out, tag); U, C = load_gpu(out, tag)
    rows = []
    for c in cl:
        r = timeline(c, req, steps_req, ev, off); r["send_mono"] = c["send_mono_ns"] / 1e9; r["end_mono"] = c["end_mono_ns"] / 1e9; r["tier"] = tier(r)
        if r.get("kv_wait_ms") is not None and r.get("kv_arrived_ms") is not None: r["kv_load_wait_ms"] = r["kv_arrived_ms"] - r["kv_wait_ms"]
        if r.get("kv_arrived_ms") is not None and r.get("scheduled_ms") is not None: r["ready_to_sched_ms"] = r["scheduled_ms"] - r["kv_arrived_ms"]
        rows.append(r)
    cols = COLS + ["tier", "send_mono", "end_mono", "kv_load_wait_ms", "ready_to_sched_ms", "trace_s", "blocks"]
    with open(f"{out}/{tag}-requests.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.4f}" if isinstance(r.get(k), float) else r.get(k))) for k in cols})
    with open(f"{out}/{tag}-steps.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["i", "t0", "t1", "t_end", "tok", "new", "cached", "run", "wait", "hold", "wfr", "fin"])
        for s in steps: w.writerow([s["i"], f"{s['t0']:.6f}", f"{s['t1']:.6f}", "" if s["t_end"] is None else f"{s['t_end']:.6f}", s["tok"], s["new"], s["cached"], s["run"], s["wait"], s["hold"], s["wfr"], s["fin"]])
    groups = {}
    for r in rows: groups.setdefault(r.get("grp") or "(all)", []).append(r)
    summ = []
    for gname, rs in groups.items():
        g = summarize_group(rs, steps, U, C)
        if g: g = dict(tag=tag, grp=gname, **g); summ.append(g)
    allg = summarize_group(rows, steps, U, C)
    if allg: summ.append(dict(tag=tag, grp="(all)", **allg))
    keys = sorted({k for g in summ for k in g}, key=lambda k: (k not in ("tag", "grp", "n"), k))
    with open(f"{out}/{tag}-scenarios.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for g in summ: w.writerow({k: ("" if g.get(k) is None else (f"{g[k]:.4f}" if isinstance(g.get(k), float) else g.get(k))) for k in keys})
    return rows, summ, steps

def fmt(v): return "-" if v is None else (f"{v:.1f}" if isinstance(v, float) else str(v))

if __name__ == "__main__":
    out = sys.argv[1]
    for tag in sys.argv[2:]:
        rows, summ, steps = analyze(out, tag)
        print(f"## {tag}\n")
        print("| group | n (err) | req/s | prompt tok/s | GPU busy (steps) | NVML util | PCIe RX GB | TTFT all p50/p95/p99 | host n: p50/p95 | gpu n: p50/p95 | cold n: p50/p95 | host load wait p50 | ready→sched p50 |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for g in summ:
            c = lambda ty: f"{g.get(ty + '_n', 0)}: {fmt(g.get(ty + '_ttft_p50'))}/{fmt(g.get(ty + '_ttft_p95'))}" if g.get(ty + "_n") else "-"
            print(f"| {g['grp']} | {g['n']} ({g['n_err']}) | {fmt(g['req_per_s'])} | {fmt(g['prompt_tok_per_s'])} | {fmt(g['gpu_busy_steps'])} | {fmt(g['gpu_util_nvml'])} | {fmt(g['pcie_rx_GB'])} | "
                  f"{fmt(g.get('all_ttft_p50'))}/{fmt(g.get('all_ttft_p95'))}/{fmt(g.get('all_ttft_p99'))} | {c('host')} | {c('gpu')} | {c('cold')} | {fmt(g.get('host_kv_load_wait_ms_p50'))} | {fmt(g.get('host_ready_to_sched_ms_p50'))} |")
        print()
