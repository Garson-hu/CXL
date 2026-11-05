#!/usr/bin/env python3
"""Offline prefix-reuse potential of a Mooncake trace window (TRACE ANALYSIS, not a measurement): for the requests with
t0 <= timestamp < t1, the share of prompt tokens whose 512-token hash blocks already occurred in an earlier request of
the window (prefix semantics: a request's hit = its longest all-seen prefix), (a) with an unbounded cache and (b) under
an LRU over blocks of the given capacities (GB of KV at bytes_per_token), i.e. the most any KV cache of that size could
serve. Prompts are cut like replay.py (max_model_len - max_out - 8 = 31,736 tokens).
usage: trace_reuse.py <trace.jsonl> <t0> <t1> [bytes_per_token=36864] [max_len=31736] [gb=2,5,10,20,40,80]
       trace_reuse.py --csv <out.csv>      capacity curves of both traces for windows 0-100 / 0-200 / 0-3600 s"""
import csv, json, os, sys
from collections import OrderedDict
W = "/home/ghu4/CXL/workloads"
TRACES = (("conv", f"{W}/mooncake_conversation_trace.jsonl"), ("tool", f"{W}/mooncake_toolagent_trace.jsonl"))

def load(tr, t0, t1, ML):
    reqs = []
    for l in open(tr):
        r = json.loads(l); ts = r["timestamp"] / 1000.0
        if ts < t0: continue
        if ts >= t1: break
        n = min(int(r["input_length"]), ML); reqs.append((ts, r["hash_ids"][: (n + 511) // 512], n))
    return reqs

def run(reqs, cap_blocks):
    """LRU over hash blocks; returns (reusable token share, requests with >= 50% prefix hit, total prompt tokens)"""
    seen = OrderedDict(); hit = 0; hit_req = 0; tot = sum(n for _, _, n in reqs)
    for _, hs, n in reqs:
        k = 0
        for h in hs:
            if h in seen: k += 1
            else: break
        ht = min(n, k * 512); hit += ht; hit_req += ht >= 0.5 * n
        for h in hs: seen[h] = 1; seen.move_to_end(h)
        while cap_blocks and len(seen) > cap_blocks: seen.popitem(last=False)
    return (hit / tot if tot else 0), hit_req, tot

if __name__ == "__main__":
    if sys.argv[1] == "--csv":
        BPT, ML = 36864, 31736; rows = []
        for name, tr in TRACES:
            for t1 in (100, 200, 3600):
                reqs = load(tr, 0, t1, ML)
                for gb in (0.5, 1, 2, 4.49, 5, 10, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 0):
                    s, nr, tot = run(reqs, int(gb * 1e9 / (512 * BPT)) if gb else 0)
                    rows.append(dict(trace=name, window_s=t1, cap_gb=(gb if gb else "inf"), share=round(s, 4), req50=nr, n=len(reqs), tokens=tot))
        with open(sys.argv[2], "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        print("wrote", sys.argv[2]); sys.exit()
    tr, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    BPT = int(sys.argv[4]) if len(sys.argv) > 4 else 36864; ML = int(sys.argv[5]) if len(sys.argv) > 5 else 31736
    GBS = [float(x) for x in (sys.argv[6] if len(sys.argv) > 6 else "2,5,10,20,40,80").split(",")]
    reqs = load(tr, t0, t1, ML); tot = sum(n for _, _, n in reqs)
    print(f"{os.path.basename(tr)} window {t0}-{t1} s: {len(reqs)} requests, {tot} prompt tokens ({tot * BPT / 1e9:.1f} GB of KV), mean prompt {tot / max(1, len(reqs)):.0f}")
    s, nr, _ = run(reqs, 0); print(f"  unbounded cache: reusable share {s:.3f} ({nr} requests with >= 50% prefix hit)")
    for gb in GBS:
        cb = int(gb * 1e9 / (512 * BPT)); s, nr, _ = run(reqs, cb); print(f"  LRU {gb:g} GB ({cb} blocks, {cb * 512 / 1e3:.0f}k tokens): reusable share {s:.3f} ({nr} req >= 50%)")
