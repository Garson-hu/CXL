#!/usr/bin/env python3
"""Hit-category breakdown of a trace replay (Experiment D): TTFT, queue wait and the KV-load timeline of requests grouped by
where their prefix came from — host-tier hits (>= 50 % of the prompt retrieved from LMCache), GPU-prefix hits (>= 50 % served
by vLLM's prefix cache), partial hits (10-50 % cached) and misses (< 10 %); the same groups at equal backlog at arrival; and
how many later-arriving requests were first scheduled while a host hit waited between its lookup result and its load.
Reads <out>/<tag>-requests.csv (analyze_b.py / analyze_replay.py); writes <out>/tables-d-hitcat.md and prints it.
usage: hitcat_d.py <out> <tag> [more tags ...]"""
import csv, sys
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def s(v, d=1): return "–" if v is None else f"{v / 1000:.{d}f}"
CATS = ("host≥50%", "GPU≥50%", "10–50%", "miss<10%")
def cat_of(r):
    P = fl(r["prompt_tokens"]); c = fl(r["cached_tokens"]) or 0; h = fl(r["retrieve_tokens"]) or 0
    return "miss<10%" if c < 0.1 * P else "10–50%" if c < 0.5 * P else "host≥50%" if h >= 0.5 * P else "GPU≥50%" if c - h >= 0.5 * P else "mixed"

out = sys.argv[1]; L = []
L.append("| run | category | n | prompt tok p50 | uncached tok p50 | TTFT p50 (s) | queue→sched p50 (s) | lookup p50 (s) | lookup end→load start p50 (s) | KV load wait p50 (s) | transfer p50 (s) | prefill p50 (s) |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
B = ["| run | backlog at arrival | host≥50 % TTFT p50 (s) [n] | GPU≥50 % TTFT p50 (s) [n] | miss TTFT p50 (s) [n] |", "|---|---|---|---|---|"]
G = ["| run | host hits with lookup→load gap > 2 s | gap p50 / p90 (s) | requests first scheduled inside such a gap (GPU / miss / partial / host) | of those, arrived after the host hit |", "|---|---|---|---|---|"]
for tag in sys.argv[2:]:
    R = [r for r in csv.DictReader(open(f"{out}/{tag}-requests.csv")) if r["case"] == "trace" and r["status"] == "200"]
    if not R: continue
    for r in R:
        r["cat"] = cat_of(r); sm = fl(r["send_mono"])
        for k in ("scheduled_ms", "lookup_end_ms", "retrieve_start_ms"): r["abs_" + k] = sm + fl(r[k]) / 1000 if fl(r[k]) is not None else None
    ev = sorted([(fl(r["send_mono"]), 1) for r in R] + [(fl(r["end_mono"]), -1) for r in R]); b = 0; bl = {}
    for t, d in ev:
        b += d
        if d == 1: bl[t] = b
    for r in R: r["backlog"] = bl[fl(r["send_mono"])]
    for k in CATS:
        v = [r for r in R if r["cat"] == k]
        if not v: continue
        g = lambda key: q([fl(r[key]) for r in v], .5)
        gap = q([fl(r["retrieve_start_ms"]) - fl(r["lookup_end_ms"]) for r in v if fl(r["retrieve_start_ms"]) is not None and fl(r["lookup_end_ms"]) is not None], .5)
        L.append(f"| {tag} | {k} | {len(v)} | {g('prompt_tokens'):.0f} | {q([fl(r['prompt_tokens']) - (fl(r['cached_tokens']) or 0) for r in v], .5):.0f} | {s(g('ttft_client_ms'))} | {s(g('queue_to_sched_ms'))} | {s(g('lookup_ms'), 2)} | {s(gap)} | {s(g('kv_load_wait_ms'), 2)} | {s(g('retrieve_ms'), 2)} | {s(g('prefill_ms'), 2)} |")
    for lo, hi in ((0, 20), (20, 35), (35, 1000)):
        row = []
        for k in ("host≥50%", "GPU≥50%", "miss<10%"):
            v = [fl(r["ttft_client_ms"]) for r in R if r["cat"] == k and lo <= r["backlog"] < hi]
            row.append(f"{s(q(v, .5))} [{len(v)}]")
        B.append(f"| {tag} | {lo}–{hi if hi < 1000 else 'max'} | " + " | ".join(row) + " |")
    hosts = [r for r in R if r["cat"] == "host≥50%"]
    gapped = [r for r in hosts if r["abs_lookup_end_ms"] and r["abs_retrieve_start_ms"] and r["abs_retrieve_start_ms"] - r["abs_lookup_end_ms"] > 2]
    tot = {"GPU≥50%": 0, "miss<10%": 0, "10–50%": 0, "host≥50%": 0}; later = dict(tot)
    for H in gapped:
        a, bb = H["abs_lookup_end_ms"], H["abs_retrieve_start_ms"]
        for r in R:
            if r is H or r["abs_scheduled_ms"] is None or r["cat"] not in tot: continue
            if a <= r["abs_scheduled_ms"] <= bb:
                tot[r["cat"]] += 1
                if fl(r["send_mono"]) > fl(H["send_mono"]): later[r["cat"]] += 1
    gaps = [r["abs_retrieve_start_ms"] - r["abs_lookup_end_ms"] for r in gapped]
    if hosts: G.append(f"| {tag} | {len(gapped)} of {len(hosts)} | {q(gaps, .5) or 0:.1f} / {q(gaps, .9) or 0:.1f} | {tot['GPU≥50%']} / {tot['miss<10%']} / {tot['10–50%']} / {tot['host≥50%']} | {sum(later.values())} ({later['GPU≥50%']} GPU, {later['miss<10%']} miss, {later['10–50%']} partial) |")
T = "\n".join(L) + "\n\n" + "\n".join(B) + "\n\n" + "\n".join(G) + "\n"
open(f"{out}/tables-d-hitcat.md", "w").write(T); print(T)
