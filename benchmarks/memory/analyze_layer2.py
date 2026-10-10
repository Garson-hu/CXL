#!/usr/bin/env python3
"""Summarize layer-2 runs (run_layer2.py / kvemu output) in <dir>: target vs achieved store and load rates, peaks over
20 ms and 1 s windows, backlog and lateness, and the neighbour's slowdown (emulation window vs BEFORE window); for the
100 ms reader also its bandwidth in 100 ms slices with high vs low emulated write rate. Writes <dir>/summary.txt and
<dir>/summary.csv. (2026-10-10)
usage: analyze_layer2.py <dir>"""
import glob, os, re, statistics as st, sys

D = sys.argv[1]
out = open(os.path.join(D, "summary.txt"), "w"); csv = open(os.path.join(D, "summary.csv"), "w")
csv.write("tag,place,speed,block_KiB,target_GBps,store_GBps,load_GBps,peak20ms_store,peak1s_store,backlog_max_GB,late_max_ms,neighbor,slowdown_pct\n")
def say(s=""): print(s); out.write(s + "\n")
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")

for meta in sorted(glob.glob(os.path.join(D, "*-meta.txt"))):
    tag = os.path.basename(meta)[:-9]; M, cfg = {}, {}
    for l in open(meta):
        f = l.split(); M[f[1]] = int(f[2])
        if f[1] == "config": cfg = dict(x.split("=", 1) for x in f[3:])
    emu = open(os.path.join(D, f"{tag}-emu.txt")).read()
    start = int(re.search(r"^START (\d+)", emu, re.M)[1])
    W = [tuple(float(x) for x in l.split()[1:]) for l in emu.splitlines() if l.startswith("W ")]
    planned = re.search(r"# planned: .*", emu)[0]; summ = re.search(r"^S .*", emu, re.M)
    # active window = until the planned end (target > 0 somewhere after) ; use all W lines up to the last nonzero target
    last = max(i for i, w in enumerate(W) if w[1] > 0 or w[2] > 0 or w[3] > 0)
    W = W[: last + 1]; end = int(W[-1][0]); span = (end - start) / 1e9
    tg = [w[1] for w in W]; stw = [w[2] for w in W]; ldw = [w[3] for w in W]; bl = [w[4] for w in W]; late = [w[5] for w in W]
    sec = lambda v: [sum(v[i:i + 50]) / 50 for i in range(0, len(v) - 49, 50)]
    say(f"## {tag}  ({cfg.get('place')}, {cfg.get('speed')}x, block {int(cfg.get('block_KiB', 0)) // 1024} MiB, tier {cfg.get('cap')} GiB, {span:.0f} s)")
    say(f"  {planned[2:]}")
    if summ: say(f"  {summ[0][2:]}")
    say(f"  target  mean {st.mean(tg):.2f} GB/s; 20 ms p50 {q(tg, .5):.2f} p99 {q(tg, .99):.2f} max {max(tg):.2f}; 1 s max {max(sec(tg)):.2f}")
    say(f"  stores  mean {st.mean(stw):.2f} GB/s; 20 ms p50 {q(stw, .5):.2f} p99 {q(stw, .99):.2f} max {max(stw):.2f}; 1 s max {max(sec(stw)):.2f}")
    say(f"  loads   mean {st.mean(ldw):.2f} GB/s; 20 ms p50 {q(ldw, .5):.2f} p99 {q(ldw, .99):.2f} max {max(ldw):.2f}; 1 s max {max(sec(ldw)):.2f}")
    say(f"  backlog p99 {q(bl, .99):.2f} GB max {max(bl):.2f} GB; job start lateness p99 {q(late, .99):.1f} ms max {max(late):.1f} ms")
    slow = ""
    nf = os.path.join(D, f"{tag}-neighbor.txt")
    if os.path.exists(nf) and "before_start" in M:
        b0, b1 = M["before_start"], M["before_end"]; txt = open(nf).read()
        if "[STEP]" in txt:
            s = [(int(t), float(v)) for v, t in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", txt)]
            bef = [v for t, v in s if b0 <= t < b1]; dur = [v for t, v in s if start <= t < end]
            slow = 100 * (st.median(dur) / st.median(bef) - 1)
            say(f"  neighbour step: before {st.median(bef):.4f} s (n={len(bef)}), during {st.median(dur):.4f} s (n={len(dur)}) -> {slow:+.2f}% slower")
        elif "TOK" in txt:
            tk = [int(t) for t in re.findall(r"^TOK (\d+)", txt, re.M)]
            rb = sum(1 for t in tk if b0 <= t < b1) / ((b1 - b0) / 1e9); rd = sum(1 for t in tk if start <= t < end) / span
            slow = 100 * (1 - rd / rb); say(f"  neighbour llama.cpp: before {rb:.2f} tok/s, during {rd:.2f} tok/s -> {slow:+.2f}% slower")
        else:
            s = [(int(t), float(v)) for t, v in re.findall(r"^T (\d+) ([\d.]+)$", txt, re.M)]
            bef = [v for t, v in s if b0 <= t < b1]; dur = [v for t, v in s if start <= t < end]
            slow = 100 * (1 - st.mean(dur) / st.mean(bef))
            say(f"  neighbour reader: before {st.mean(bef):.2f} GiB/s, during {st.mean(dur):.2f} GiB/s -> {slow:+.2f}% slower")
            wr = {int(w[0]) // 100_000_000: 0.0 for w in W}
            for w in W: wr[int(w[0]) // 100_000_000] = max(wr[int(w[0]) // 100_000_000], w[2] + w[3])
            thr = q(list(wr.values()), .9); lo_t = q(list(wr.values()), .25)
            hi = [v for t, v in s if start <= t < end and wr.get(t // 100_000_000, 0) >= thr]
            lo = [v for t, v in s if start <= t < end and wr.get(t // 100_000_000, 0) <= lo_t]
            if hi and lo: say(f"    100 ms slices in the top 10% of emulated traffic (>= {thr:.1f} GB/s): {st.mean(hi):.2f} GiB/s; bottom 25% (<= {lo_t:.1f}): {st.mean(lo):.2f} GiB/s")
    csv.write(f"{tag},{cfg.get('place')},{cfg.get('speed')},{cfg.get('block_KiB')},{st.mean(tg):.3f},{st.mean(stw):.3f},{st.mean(ldw):.3f},{max(stw):.2f},{max(sec(stw)):.2f},{max(bl):.2f},{max(late):.1f},{cfg.get('neighbor')},{slow if slow == '' else f'{slow:.2f}'}\n")
    say()
out.close(); csv.close()
