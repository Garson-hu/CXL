#!/usr/bin/env python3
"""Tail latency of the llama.cpp victim: inter-token intervals inside the copy windows vs the 10 s before each window.
Per run: p50 and p99 of the interval (ms) before / inside, and the max stall; medians over the last 3 windows.
usage: tail_latency.py <outdir> [prefix]"""
import glob, os, re, statistics as st, sys
out = sys.argv[1]; prefix = sys.argv[2] if len(sys.argv) > 2 else ""
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
rows = []
for pf in sorted(glob.glob(f"{out}/{prefix}*-producer.txt")):
    tag = os.path.basename(pf)[:-len("-producer.txt")]
    if not tag.startswith("llama"): continue
    wins = [(int(m[1]), int(m[2])) for m in re.findall(r"COPY (\d+) START (\d+) END (\d+)", open(pf).read())]
    toks = [int(m) for m in re.findall(r"^TOK (\d+)", open(f"{out}/{tag}-victim.txt").read(), flags=re.M)]
    iv = [(toks[i], (toks[i] - toks[i - 1]) / 1e6) for i in range(1, len(toks))]          # (end ns, interval ms)
    per = []
    for s0, s1 in wins[-3:]:
        inside = [v for t, v in iv if s0 <= t <= s1 + 150_000_000]; before = [v for t, v in iv if s0 - 10_000_000_000 <= t < s0 - 500_000_000]
        if inside and before: per.append((q(before, .5), q(before, .99), q(inside, .5), q(inside, .99), max(inside)))
    if not per: continue
    m = [st.median(x[i] for x in per) for i in range(5)]
    rows.append((tag, m)); print(f"{tag:34s} before p50 {m[0]:6.1f} ms p99 {m[1]:6.1f}   inside p50 {m[2]:6.1f} p99 {m[3]:6.1f} max {m[4]:7.1f}   p99 inside/before {m[3]/m[1]:.2f}x")
