#!/usr/bin/env python3
"""Per-run summary of a trace replay (Experiment D and the real-trace part of B): hit shares, TTFT, throughput, KV
traffic on the GPU link, host-cache occupancy and evictions. Reads the client records, the vLLM hook, the LMCache
events, the GPU sampler and the /status poll of one run; writes <out>/<tag>-replay.json and a per-request CSV
(through analyze_b), and prints one summary line. A combined table over several tags goes to <out>/replay-summary.csv.
Hit accounting (prefix semantics, as vLLM reports it): cached_tokens = prompt tokens served from the GPU prefix cache or
from LMCache; host_tokens = tokens actually retrieved from LMCache (retrieve events); local = cached - host.
usage: analyze_replay.py <out> <tag> [more tags ...]"""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_b import analyze, load_gpu, q

def summarize(out, tag):
    rows, summ, steps = analyze(out, tag)
    R = [r for r in rows if r["case"] == "trace"]; ok = [r for r in R if r["status"] == 200]
    if not ok: return None
    t0 = min(r["send_mono"] for r in ok); t1 = max(r["end_mono"] for r in ok); W = t1 - t0
    prompt = sum(r["prompt_tokens"] for r in ok); cached = sum(max(0, r["cached_tokens"] or 0) for r in ok); host = sum(r.get("retrieve_tokens") or 0 for r in ok)
    s = dict(tag=tag, n=len(R), n_ok=len(ok), n_err=len(R) - len(ok), window_s=W, prompt_tokens=prompt, cached_share=cached / prompt, host_share=host / prompt, local_share=(cached - host) / prompt,
             computed_tok_per_s=(prompt - cached) / W, offered_prompt_tok_per_s=prompt / W, req_per_s=len(ok) / W,
             ttft_p50=q([r["ttft_client_ms"] for r in ok], .5), ttft_p95=q([r["ttft_client_ms"] for r in ok], .95), ttft_p99=q([r["ttft_client_ms"] for r in ok], .99), ttft_mean=sum(r["ttft_client_ms"] for r in ok) / len(ok),
             retrieve_GB=sum(r.get("retrieve_bytes") or 0 for r in ok) / 1e9, store_GB=sum(r.get("store_bytes") or 0 for r in ok) / 1e9,
             total_ms_p50=q([r["total_ms"] for r in ok], .5))
    hi = [r for r in ok if (r["cached_tokens"] or 0) >= 0.5 * r["prompt_tokens"]]; lo = [r for r in ok if (r["cached_tokens"] or 0) < 0.1 * r["prompt_tokens"]]
    s["n_hit50"] = len(hi); s["ttft_hit50_p50"] = q([r["ttft_client_ms"] for r in hi], .5) if hi else None; s["n_miss"] = len(lo); s["ttft_miss_p50"] = q([r["ttft_client_ms"] for r in lo], .5) if lo else None
    for k in ("kv_load_wait_ms", "ready_to_sched_ms", "queue_to_sched_ms", "retrieve_ms"):
        v = [r[k] for r in ok if r.get(k) is not None]
        if v: s[k + "_p50"] = q(v, .5); s[k + "_p95"] = q(v, .95)
    U, C = load_gpu(out, tag); cw = [c for c in C if t0 <= c[0] <= t1]
    s["pcie_rx_GB"] = sum(c[2] for c in cw) / 1e9; s["pcie_tx_GB"] = sum(c[1] for c in cw) / 1e9
    u = [x[1] for x in U if t0 <= x[0] <= t1]; s["gpu_util_nvml"] = sum(u) / len(u) / 100 if u else None
    busy = sum((st["t_end"] - st["t1"]) for st in steps if st["tok"] > 0 and st["t_end"] and t0 <= st["t1"] <= t1); s["gpu_busy_steps"] = busy / W
    # host cache occupancy and evictions
    p = f"{out}/{tag}-status.txt"; used = []
    if os.path.exists(p):
        for l in open(p):
            if l.startswith("S "):
                try:
                    t, js = l[2:].split(" ", 1); d = json.loads(js); m = d["storage_manager"]["l1_manager"]
                    if t0 <= int(t) / 1e9 <= t1 + 5: used.append((m["memory_used_bytes"], m["total_object_count"]))
                except Exception: pass
    if used: s["l1_used_GB_max"] = max(u[0] for u in used) / 1e9; s["l1_used_GB_mean"] = sum(u[0] for u in used) / len(used) / 1e9; s["l1_objects_max"] = max(u[1] for u in used)
    p = f"{out}/{tag}-kvevents.jsonl"; ev = 0; evk = 0
    if os.path.exists(p):
        for l in open(p):
            if '"l1.keys.evicted"' in l:
                d = json.loads(l); ev += 1; evk += len(d.get("keys") or [])
    s["eviction_events"] = ev; s["evicted_chunks"] = evk
    # backlog (sent, unanswered) over time: max
    ev2 = sorted([(r["send_mono"], 1) for r in ok] + [(r["end_mono"], -1) for r in ok]); b = 0; bmax = 0
    for _, d in ev2: b += d; bmax = max(bmax, b)
    s["backlog_max"] = bmax
    json.dump(s, open(f"{out}/{tag}-replay.json", "w"), indent=1)
    return s

if __name__ == "__main__":
    out = sys.argv[1]; S = []
    for tag in sys.argv[2:]:
        s = summarize(out, tag)
        if s: S.append(s); print(f"{tag}: n={s['n_ok']}/{s['n']} cached {s['cached_share']:.3f} (host {s['host_share']:.3f}, local {s['local_share']:.3f}) TTFT p50/p95/p99 {s['ttft_p50']:.0f}/{s['ttft_p95']:.0f}/{s['ttft_p99']:.0f} ms, computed {s['computed_tok_per_s']:.0f} tok/s, PCIe RX {s['pcie_rx_GB']:.1f} GB TX {s['pcie_tx_GB']:.1f} GB, L1 max {s.get('l1_used_GB_max', 0):.1f} GB, evicted chunks {s['evicted_chunks']}, GPU busy {s['gpu_busy_steps']:.2f}, backlog max {s['backlog_max']}")
    if S:
        keys = sorted({k for s in S for k in s}, key=lambda k: (k != "tag", k)); p = f"{out}/replay-summary.csv"; old = {}
        if os.path.exists(p):
            for r in csv.DictReader(open(p)): old[r["tag"]] = r
        for s in S: old[s["tag"]] = {k: ("" if s.get(k) is None else s[k]) for k in keys}
        keys = sorted({k for r in old.values() for k in r}, key=lambda k: (k != "tag", k))
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
            for t in sorted(old): w.writerow({k: old[t].get(k, "") for k in keys})
