#!/usr/bin/env python3
"""Summarize real LMCache multi-process runs (run_2a.py; experiment 2a and, with --ckpt, experiment 3) in <dir>.
Per run: achieved rates and TTFT; LMCache chunk hit share (from the server's "Prefetch request completed: X/Y retained
keys" lines; keys = 256-token chunks); stores; KV traffic on the GPU link (v2 counter, payload); L1 usage (/status).
With a checkpoint: bursts (duration, paused), the CPU CXL reader's latency inside vs outside bursts, the duration and
rate of each host->GPU transfer burst (KV loads, 5 ms bins above 0.5 GB/s) inside vs outside checkpoint bursts, and TTFT
of requests whose first token was waited for during a burst vs not. Writes <dir>/summary.txt. (2026-10-12)
usage: analyze_mp.py <dir>"""
import glob, gzip, os, re, statistics as st, sys, datetime

D = sys.argv[1]; TXF, RXF = 1.12, 1.09
def rd(p): return open(p, errors="replace").read() if os.path.exists(p) else (gzip.open(p + ".gz", "rt", errors="replace").read() if os.path.exists(p + ".gz") else "")
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
out = open(os.path.join(D, "summary.txt"), "w")
def say(s=""): print(s); out.write(s + "\n")
for meta in sorted(glob.glob(os.path.join(D, "*-meta.txt"))):
    tag = os.path.basename(meta)[:-9]; M = {}; wall = None
    for l in open(meta):
        f = l.split(); M[f[1]] = int(f[2])
        if f[1] == "clock": wall = float(f[3].split("=")[1])
    if "done" not in M: continue
    s0, s1 = M["serve_start"], M["serve_end"]; span = (s1 - s0) / 1e9; off = M["clock"] / 1e9 - wall
    say(f"## {tag}  (serving {span:.0f} s)")
    R = [l.split() for l in rd(f"{D}/{tag}-client.txt").splitlines() if l.startswith("REQ ")]
    R = [dict(send=int(f[3]), first=int(f[4]), end=int(f[5]), ptok=int(f[6]), otok=int(f[7]), cached=int(f[8])) for f in R]
    ok = [r for r in R if r["first"]]; tt = [(r["first"] - r["send"]) / 1e9 for r in ok]
    say(f"  requests {len(R)}; achieved {len(R) / span:.3f} req/s, {sum(r['ptok'] for r in R) / span:.0f} prompt tok/s; TTFT p50 {q(tt, .5):.2f} p90 {q(tt, .9):.2f} p99 {q(tt, .99):.2f} s; vLLM-cached tokens {sum(max(0, r['cached']) for r in R)}")
    lm = re.sub(r"\x1b\[[0-9;]*m", "", rd(f"{D}/{tag}-lmcache.log"))
    pf = [(int(a), int(b), int(c), int(d), float(e)) for a, b, c, d, e in re.findall(r"Prefetch request completed \(L1\+L2\): (\d+)/(\d+) retained keys \((\d+) L1, (\d+) L2\) in ([\d.]+) ms", lm)]
    stored = [int(x) for x in re.findall(r"Stored (\d+) tokens in", lm)]; retr = [int(x) for x in re.findall(r"Retrieved (\d+) tokens in", lm)]
    if pf: say(f"  LMCache: lookups {len(pf)}, chunks found {sum(p[0] for p in pf)} of {sum(p[1] for p in pf)} = {sum(p[0] for p in pf) / max(1, sum(p[1] for p in pf)):.3f}; "
               f"prefetch time p50 {q([p[4] for p in pf], .5):.1f} p99 {q([p[4] for p in pf], .99):.1f} ms; stored {len(stored)} ops {sum(stored)} tokens; retrieved {sum(retr)} tokens in {len(retr)} ops")
    C = [(int(t), int(tx) / TXF / 1e9, int(rx) / RXF / 1e9) for t, tx, rx in re.findall(r"^C (\d+) (\d+) (\d+)$", rd(f"{D}/{tag}-pcie.txt"), re.M) if s0 < int(t) <= s1]
    if C: say(f"  GPU link: stores {sum(c[1] for c in C):.1f} GB ({sum(c[1] for c in C) / span:.3f} GB/s), loads {sum(c[2] for c in C):.1f} GB ({sum(c[2] for c in C) / span:.3f} GB/s) incl. ~0.02 GB/s background each")
    used = [int(x) for x in re.findall(r'"memory_used_bytes":\s*(\d+)', rd(f"{D}/{tag}-status.txt"))]; tot = re.findall(r'"memory_total_bytes":\s*(\d+)', rd(f"{D}/{tag}-status.txt"))
    if used: say(f"  L1 used: mean {st.mean(used) / 2**30:.1f} GiB, max {max(used) / 2**30:.1f} of {int(tot[-1]) / 2**30:.0f} GiB")
    al = [float(x) / 1024 for x in re.findall(r"- Total allocated size: ([\d.]+) MB", lm)]
    if tag.startswith("hybrid") and len(al) > 8:              # hybrid: two allocator summaries per check, local DRAM pool first, then DAX
        P = list(zip(al[0::2], al[1::2]))[len(al) // 8:]     # after the first quarter of the checks
        say(f"  hybrid pools after the first quarter: DRAM mean {st.mean(p[0] for p in P):.1f} max {max(p[0] for p in P):.1f} GiB, DAX mean {st.mean(p[1] for p in P):.1f} max {max(p[1] for p in P):.1f} GiB")
    ck = rd(f"{D}/{tag}-ckpt.txt")
    if ck:
        B = [(int(a), int(b), float(c), float(d)) for a, b, c, d in re.findall(r"^C \d+ (\d+) (\d+) ([\d.]+) paused_ms ([\d.]+)", ck, re.M)]
        B = [b for b in B if b[1] > s0 and b[0] < s1]
        dur = [(b[1] - b[0]) / 1e9 for b in B]
        say(f"  checkpoint: {len(B)} bursts of {B[0][2]:.0f} GiB; duration p50 {q(dur, .5):.2f} s max {max(dur):.2f} s; rate p50 {B[0][2] * 2**30 / 1e9 / q(dur, .5):.1f} GB/s; paused per thread p50 {q([b[3] for b in B], .5):.0f} ms; "
            f"busy {sum(dur) / span:.0%} of the serving time")
        inb = lambda t: any(b[0] <= t <= b[1] for b in B)
        Rr = [(int(t), float(v)) for t, v in re.findall(r"^R (\d+) ([\d.]+)", ck, re.M) if s0 <= int(t) <= s1]
        a_in = [v for t, v in Rr if inb(t)]; a_out = [v for t, v in Rr if not inb(t)]
        if a_in and a_out: say(f"  CXL reader (one dependent load): inside bursts p50 {q(a_in, .5):.0f} p99 {q(a_in, .99):.0f} ns, outside p50 {q(a_out, .5):.0f} p99 {q(a_out, .99):.0f} ns")
        runs, cur, t_start = [], [], None
        for t, tx, rx in C:
            if rx / 0.005 > 0.5:
                if not cur: t_start = t
                cur.append(rx)
            elif cur: runs.append((t_start, len(cur) * 0.005, sum(cur))); cur = []
        li = [r for r in runs if inb(r[0])]; lo = [r for r in runs if not inb(r[0])]
        fmt = lambda xs: f"n={len(xs)} duration p50 {q([x[1] for x in xs], .5) * 1000:.0f} ms p90 {q([x[1] for x in xs], .9) * 1000:.0f} ms, rate p50 {q([x[2] / x[1] for x in xs], .5):.1f} GB/s" if xs else "n=0"
        say(f"  KV loads on the link (host->GPU bursts): inside checkpoint bursts {fmt(li)}; outside {fmt(lo)}")
        ti = [(r["first"] - r["send"]) / 1e9 for r in ok if any(b[0] <= r["first"] and b[1] >= r["send"] for b in B)]
        to = [(r["first"] - r["send"]) / 1e9 for r in ok if not any(b[0] <= r["first"] and b[1] >= r["send"] for b in B)]
        if ti and to: say(f"  TTFT, requests overlapping a burst: n={len(ti)} p50 {q(ti, .5):.2f} p90 {q(ti, .9):.2f} s; not overlapping: n={len(to)} p50 {q(to, .5):.2f} p90 {q(to, .9):.2f} s")
    say()
out.close()
