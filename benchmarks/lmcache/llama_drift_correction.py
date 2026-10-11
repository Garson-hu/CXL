#!/usr/bin/env python3
"""llama.cpp slows down as its context grows (36 -> 26 tok/s over 12 min), so "during vs a BEFORE window" overstates
any slowdown, and absolute comparisons with a separate control run are off by a run-to-run level difference (its
BEFORE windows were 7-15% below the control at the same tokens). Method (2026-10-11): each run's own BEFORE window gives
the level, the control run (llama alone, benchmarks/policy/llama_control.sh) gives only the drift shape:
expected = before_rate * control_rate(tokens during) / control_rate(tokens before); slowdown = 1 - during / expected.
Method noise seen: about +-5 points. usage: llama_drift_correction.py <experiment results dir>"""
import gzip, os, re, sys
D = sys.argv[1]
def rd(p): return open(p).read() if os.path.exists(p) else gzip.open(p + ".gz", "rt").read()
ctl = [int(t) for t in re.findall(r"^TOK (\d+)", rd(f"{D}/layer1/llama-control-alone.txt"), re.M)]
def cr(k0, k1): return (k1 - k0) / ((ctl[k1] - ctl[k0]) / 1e9)
def corrected(tk, b0, b1, s0, s1):
    kb0, kb1 = sum(t < b0 for t in tk), sum(t < b1 for t in tk); k0, k1 = sum(t < s0 for t in tk), min(sum(t < s1 for t in tk), len(ctl) - 1)
    before = (kb1 - kb0) / ((b1 - b0) / 1e9); during = (k1 - k0) / ((s1 - s0) / 1e9)
    return 100 * (1 - during / (before * cr(k0, k1) / cr(kb0, kb1))), 100 * (1 - during / before)
def meta(p): return {l.split()[1]: int(l.split()[2]) for l in open(p)}
out = []
M = meta(f"{D}/layer1/sat-llama-meta.txt"); tk = [int(t) for t in re.findall(r"^TOK (\d+)", rd(f"{D}/layer1/sat-llama-neighbor.txt"), re.M)]
c, raw = corrected(tk, M["before_start"], M["before_end"], M["serve_start"], M["serve_end"])
out.append(f"layer1 sat-llama (real serving, saturated): raw {raw:+.1f}% corrected {c:+.1f}%")
for cfg in ("8b-1x", "8b-4x", "8b-8x", "70b-1x", "70b-4x", "70b-8x"):
    for place in ("dram", "cxl"):
        tag = f"llama-{cfg}-{place}"; M = meta(f"{D}/layer2/{tag}-meta.txt"); emu = rd(f"{D}/layer2/{tag}-emu.txt")
        s0 = int(re.search(r"^START (\d+)", emu, re.M)[1]); W = [l.split() for l in emu.splitlines() if l.startswith("W ")]
        s1 = int(W[max(i for i, w in enumerate(W) if float(w[2]) or float(w[3]) or float(w[4]))][1])
        tk = [int(t) for t in re.findall(r"^TOK (\d+)", rd(f"{D}/layer2/{tag}-neighbor.txt"), re.M)]
        c, raw = corrected(tk, M["before_start"], M["before_end"], s0, s1)
        out.append(f"layer2 {tag}: raw {raw:+.1f}% corrected {c:+.1f}%")
open(f"{D}/llama-corrected.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))
