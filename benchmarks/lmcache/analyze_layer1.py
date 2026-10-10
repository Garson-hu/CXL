#!/usr/bin/env python3
"""Summarize layer-1 runs (run_layer1.py output) in <dir>: per run, the GPU's measured PCIe traffic (payload =
NVML / calibration factor), its bursts, what LMCache says it stored / retrieved, TTFT, and the neighbour's slowdown
(serving window vs the 60 s BEFORE window), plus, for the 100 ms reader, its bandwidth in 100 ms slices with and without
a KV store burst. Writes <dir>/summary.txt. (2026-10-10)
usage: analyze_layer1.py <dir>"""
import glob, os, re, statistics as st, sys

D = sys.argv[1]
TXF, RXF = 1.12, 1.09                     # NVML MB/s per payload MB/s (feasibility/pcie-calibration.txt)
BURST = 0.5                                # GB/s payload: a 20 ms window above this is "in a burst"
out = open(os.path.join(D, "summary.txt"), "w")
def say(s=""): print(s); out.write(s + "\n")
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")

for meta in sorted(glob.glob(os.path.join(D, "*-meta.txt"))):
    tag = os.path.basename(meta)[:-9]; M = {}
    for l in open(meta):
        f = l.split(); M[f[1]] = int(f[2])
    s0, s1 = M["serve_start"], M["serve_end"]; span = (s1 - s0) / 1e9
    say(f"## {tag}  (serving {span:.0f} s)")
    # --- PCIe
    P = {"TX": [], "RX": []}; C = []
    for l in open(os.path.join(D, f"{tag}-pcie.txt")):
        if l.startswith("P "):
            _, d, t, v = l.split(); t = int(t)
            if s0 <= t <= s1: P[d].append((t, float(v) / 1000 / (TXF if d == "TX" else RXF)))
        elif l.startswith("C "):
            _, t, tx, rx = l.split(); t = int(t)
            if s0 < t <= s1: C.append((t, int(tx) / TXF / 1e9, int(rx) / RXF / 1e9))     # payload GB in a 5 ms bin
    cov = {d: len(P[d]) * 0.02 / span for d in P}
    say(f"  20 ms throughput counter coverage: TX {cov['TX']:.0%}, RX {cov['RX']:.0%} of the serving time" + ("" if C else "  (v1 sampler: totals below scale with coverage)"))
    series = {"TX": [(t, x) for t, x in P["TX"]], "RX": [(t, x) for t, x in P["RX"]]}; binw = 0.02
    if C:                                                               # v2: 5 ms bins of the cumulative counter
        series = {"TX": [(t, tx / 0.005) for t, tx, rx in C], "RX": [(t, rx / 0.005) for t, tx, rx in C]}; binw = 0.005
        say(f"  cumulative counter: {len(C)} bins of 5 ms ({len(C) * 0.005 / span:.0%} of the serving time)")
    for d, name in (("TX", "GPU->host (KV stores)"), ("RX", "host->GPU (KV loads)")):
        v = [x for _, x in series[d]]
        if not v: continue
        tot = sum(v) * binw
        say(f"  PCIe {name}: {tot:.1f} GB payload, mean {tot / span:.3f} GB/s; {binw * 1000:.0f} ms bins p50 {q(v, .5):.3f} p90 {q(v, .9):.3f} "
            f"p99 {q(v, .99):.3f} max {max(v):.3f} GB/s; bins above {BURST} GB/s: {sum(1 for x in v if x > BURST) / len(v):.1%}")
        runs, cur, starts = [], [], []
        for t, x in series[d]:
            if x > BURST:
                if not cur: starts.append(t)
                cur.append(x)
            elif cur: runs.append(cur); cur = []
        if cur: runs.append(cur)
        if runs:
            dur = [len(r) * binw for r in runs]; byt = [sum(r) * binw for r in runs]; peak = [max(r) for r in runs]
            gaps = [(b - a) / 1e9 for a, b in zip(starts, starts[1:])]
            say(f"    bursts: {len(runs)}; duration p50 {q(dur, .5) * 1000:.0f} ms p90 {q(dur, .9) * 1000:.0f} ms max {max(dur) * 1000:.0f} ms; "
                f"bytes p50 {q(byt, .5):.3f} GB p90 {q(byt, .9):.3f} GB max {max(byt):.2f} GB; peak bin p50 {q(peak, .5):.2f} GB/s max {max(peak):.2f}; "
                f"start-to-start gap p50 {q(gaps, .5):.2f} s p10 {q(gaps, .1):.2f} s")
    # --- LMCache log
    stv, rtv = [], []
    for l in open(os.path.join(D, f"{tag}-server.log"), errors="replace"):
        l = re.sub(r"\x1b\[[0-9;]*m", "", l)
        m = re.search(r"Stored (\d+) out of total (\d+) tokens\. size: ([\d.]+) GB, cost ([\d.]+) ms, throughput: ([\d.]+) GB/s", l)
        if m: stv.append((int(m[1]), float(m[3]), float(m[4]), float(m[5])))
        m = re.search(r"Retrieved (\d+) out of (\d+) required tokens.*?size: ([\d.]+) gb, cost ([\d.]+) ms, throughput: ([\d.]+) GB/s", l, re.I)
        if m: rtv.append((int(m[1]), float(m[3]), float(m[4]), float(m[5])))
    if "clock" in M:
        wall = float(open(meta).read().split("wall=")[1].split()[0]); off = M["clock"] / 1e9 - wall     # mono = wall + off
        import datetime
        def mono_of(line):
            m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3})\]", line)
            return int((datetime.datetime.strptime(m[1], "%Y-%m-%d %H:%M:%S,%f").timestamp() + off) * 1e9) if m else None
        evs = []
        for l in open(os.path.join(D, f"{tag}-server.log"), errors="replace"):
            l = re.sub(r"\x1b\[[0-9;]*m", "", l)
            m = re.search(r"Retrieved (\d+) out of (\d+) required tokens.*?size: ([\d.]+) gb, cost ([\d.]+) ms", l, re.I)
            if m and mono_of(l): evs.append((mono_of(l), float(m[3]), float(m[4])))
        rxw = P["RX"]; rows = []
        for t, gib, ms in evs:                     # counter windows within 200 ms before the log line (the log comes after the copy)
            w = [x for tt, x in rxw if t - 200_000_000 <= tt <= t + 40_000_000]
            if w: rows.append((gib, ms, sum(w) * 0.02, max(w), sum(1 for x in w if x > 1.0)))
        if rows:
            say(f"  retrieves vs counter ({len(rows)}): LMCache GiB p50 {q([r[0] for r in rows], .5):.3f}, its time p50 {q([r[1] for r in rows], .5):.1f} ms; "
                f"counter bytes within 200 ms before the log line p50 {q([r[2] for r in rows], .5):.3f} GB, peak window p50 {q([r[3] for r in rows], .5):.2f} GB/s, "
                f"windows above 1 GB/s p50 {q([r[4] for r in rows], .5)} (x 20 ms)")
    for name, x in (("stored", stv), ("retrieved", rtv)):
        if x: say(f"  LMCache {name}: {len(x)} operations, {sum(a[0] for a in x)} tokens, {sum(a[1] for a in x):.1f} GiB; "
                  f"its own per-operation figure p50 {q([a[3] for a in x], .5):.1f} GB/s")
        else: say(f"  LMCache {name}: none")
    # --- client
    R = []
    for l in open(os.path.join(D, f"{tag}-client.txt")):
        if l.startswith("REQ "):
            f = l.split(); R.append(dict(send=int(f[3]), first=int(f[4]), end=int(f[5]), ptok=int(f[6]), otok=int(f[7]), cached=int(f[8])))
    ok = [r for r in R if r["first"]]
    ttft = [(r["first"] - r["send"]) / 1e9 for r in ok]
    ctext = open(os.path.join(D, f"{tag}-client.txt")).read()
    errs = ctext.count("\nERR "); offered = int(re.search(r": (\d+) requests", ctext)[1])
    cancelled = re.search(r"(\d+) requests cancelled or never sent", ctext)
    done = [r for r in R if r["end"] and r["end"] <= s1]
    say(f"  offered {offered} requests; answered {len(R)}" + (f", cancelled or never sent {cancelled[1]}" if cancelled else "") + f" ({errs} errors)")
    say(f"  achieved: {len(done) / span:.3f} requests/s, {sum(r['ptok'] for r in done) / span:.0f} prompt tokens/s, "
        f"{sum(r['otok'] for r in done) / span:.0f} output tokens/s (answered requests over the serving window)")
    if ttft:
        say(f"  TTFT p50 {q(ttft, .5):.2f} s p90 {q(ttft, .9):.2f} p99 {q(ttft, .99):.2f} max {max(ttft):.2f}; prompt tokens {sum(r['ptok'] for r in R)}, "
            f"vLLM-cached {sum(max(0, r['cached']) for r in R)}")
        n = len(ok); thirds = [sorted(ok, key=lambda r: r["send"])[i * n // 3:(i + 1) * n // 3] for i in range(3)]
        say("  TTFT p50 by third of the run: " + " / ".join(f"{q([(r['first'] - r['send']) / 1e9 for r in t], .5):.2f} s" for t in thirds if t))
    ev = sorted([(r["send"], 1) for r in R] + [(r["end"], -1) for r in R if r["end"]])
    cur, mx, back = 0, 0, []
    for t, d in ev:
        cur += d; mx = max(mx, cur); back.append((t, cur))
    if back: say(f"  backlog (requests sent, not yet answered): max {mx}; at the end of the serving window {cur}")
    # --- neighbour
    nf = os.path.join(D, f"{tag}-neighbor.txt")
    if os.path.exists(nf) and "before_start" in M:
        b0, b1 = M["before_start"], M["before_end"]; txt = open(nf).read()
        if re.search(r"^T \d+ [\d.]+$", txt, re.M) and "TOK" not in txt:            # reader: GiB/s every 100 ms
            s = [(int(a), float(b)) for a, b in re.findall(r"^T (\d+) ([\d.]+)$", txt, re.M)]
            bef = [v for t, v in s if b0 <= t < b1]; dur = [v for t, v in s if s0 <= t < s1]
            say(f"  neighbour reader: before {st.mean(bef):.2f} GiB/s, serving {st.mean(dur):.2f} GiB/s -> {100 * (st.mean(dur) / st.mean(bef) - 1):+.2f}%; "
                f"worst 100 ms slices: p1 {q(bef, .01):.2f} -> {q(dur, .01):.2f}, min {min(bef):.2f} -> {min(dur):.2f} GiB/s")
            tx = P["TX"]; i = 0; hi, lo = [], []
            for t, v in s:
                if not (s0 <= t < s1): continue
                w = [x for tt, x in tx if t - 100_000_000 < tt <= t]
                if w: (hi if max(w) > 1.0 else lo if max(w) < 0.1 else []).append(v)
            if hi and lo: say(f"    100 ms slices with a store burst (>1 GB/s): {st.mean(hi):.2f} GiB/s (n={len(hi)}); without (<0.1): {st.mean(lo):.2f} (n={len(lo)}) -> {100 * (st.mean(hi) / st.mean(lo) - 1):+.2f}%")
        elif "[STEP]" in txt:                                                     # Adam step / PageRank trial: seconds
            s = [(int(t), float(v)) for v, t in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", txt)]
            bef = [v for t, v in s if b0 <= t < b1]; dur = [v for t, v in s if s0 <= t < s1]
            say(f"  neighbour step time: before median {st.median(bef):.4f} s (n={len(bef)}), serving {st.median(dur):.4f} s (n={len(dur)}) -> {100 * (st.median(dur) / st.median(bef) - 1):+.2f}% slower; "
                f"p99 {q(bef, .99):.4f} -> {q(dur, .99):.4f} s, max {max(bef):.4f} -> {max(dur):.4f} s")
        elif "TOK" in txt:                                                        # llama.cpp: tokens
            tk = [int(t) for t in re.findall(r"^TOK (\d+)", txt, re.M)]
            rb = sum(1 for t in tk if b0 <= t < b1) / ((b1 - b0) / 1e9); rd = sum(1 for t in tk if s0 <= t < s1) / span
            say(f"  neighbour llama.cpp: before {rb:.2f} tok/s, serving {rd:.2f} tok/s -> {100 * (1 - rd / rb):+.2f}% slower")
            gb = [(b - a) / 1e6 for a, b in zip(tk, tk[1:]) if b0 <= a and b < b1]; gd = [(b - a) / 1e6 for a, b in zip(tk, tk[1:]) if s0 <= a and b < s1]
            if gb and gd: say(f"    time per token p50 {q(gb, .5):.1f} -> {q(gd, .5):.1f} ms, p99 {q(gb, .99):.1f} -> {q(gd, .99):.1f} ms, max {max(gb):.1f} -> {max(gd):.1f} ms")
    say()
out.close()
