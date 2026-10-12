#!/usr/bin/env python3
"""Summarize experiment 2b (kvemu2 runs from run_exp2b.py) in <dir> -> <dir>/summary.csv and summary.txt. (2026-10-11)
Per run: offered and achieved store rates (DRAM / CXL), peaks, backlog and lateness, hit share of reuse accesses,
pending misses, mean occupancy per tier and capacity utilization, mean loan (spill16), and the neighbour's slowdown
(BEFORE window as baseline) with its tail.
usage: analyze_exp2b.py <dir>"""
import glob, gzip, os, re, statistics as st, sys

D = sys.argv[1]
def rd(p): return open(p).read() if os.path.exists(p) else gzip.open(p + ".gz", "rt").read()
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
rows = []
for meta in sorted(glob.glob(os.path.join(D, "*-meta.txt"))):
    tag = os.path.basename(meta)[:-9]; M, cfg = {}, {}
    for l in open(meta):
        f = l.split(); M[f[1]] = int(f[2])
        if f[1] == "config": cfg = dict(x.split("=", 1) for x in f[3:])
    if "done" not in M: continue
    emu = rd(f"{D}/{tag}-emu.txt"); start = int(re.search(r"^START (\d+)", emu, re.M)[1])
    W = [[float(x) for x in l.split()[1:]] for l in emu.splitlines() if l.startswith("W ")]
    last = max(i for i, w in enumerate(W) if w[1] or w[2] or w[3] or w[4]); W = W[: last + 1]; end = int(W[-1][0])
    S1 = dict(re.findall(r"(\w+) ([\d.]+)", re.search(r"^S requests.*", emu, re.M)[0])); S2 = dict(re.findall(r"(\w+) ([\d.]+)", re.search(r"^S wall_s.*", emu, re.M)[0]))
    sec = lambda v: [sum(v[i:i + 50]) / 50 for i in range(0, len(v) - 49, 50)]
    off = [w[1] for w in W]; sd = [w[2] for w in W]; sc = [w[3] for w in W]; ld = [w[4] for w in W]; bl = [w[5] for w in W]; lt = [w[6] for w in W]; sp = [w[9] for w in W]
    r = dict(tag=tag, neighbor=cfg.get("neighbor"), policy=tag.split("-")[-1], model=tag.split("-")[1], speed=tag.split("-")[2],
             offered=st.mean(off), store_dram=st.mean(sd), store_cxl=st.mean(sc), load=st.mean(ld), dram_peak20=max(sd), dram_peak1s=max(sec(sd)) if len(sd) >= 50 else max(sd),
             backlog_max=max(bl), late_max=max(lt), hit_share=float(S1["hit_share_of_reuse"]), hits=int(S1["hits"]), pending=int(S1["pending_misses"]),
             util=float(S2["utilization"]), occ_dram=float(S2["occupancy_mean_dram_GiB"]), occ_cxl=float(S2["occupancy_mean_cxl_GiB"]), cap=float(S2["capacity_GiB"]),
             loan=st.mean(sp), borrowed=int(S1["borrowed"]), slow=float("nan"), tail=float("nan"))
    nf = f"{D}/{tag}-neighbor.txt"
    if os.path.exists(nf) and "before_start" in M:
        txt = rd(nf); b0, b1 = M["before_start"], M["before_end"]
        if "[STEP]" in txt:
            s = [(int(t), float(v)) for v, t in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", txt)]
            bef = [v for t, v in s if b0 <= t < b1]; dur = [v for t, v in s if start <= t < end]
            r["slow"] = 100 * (st.median(dur) / st.median(bef) - 1); r["tail"] = 100 * (q(dur, .99) / st.median(bef) - 1)
        else:
            s = [(int(t), float(v)) for t, v in re.findall(r"^T (\d+) ([\d.]+)$", txt, re.M)]
            bef = [v for t, v in s if b0 <= t < b1]; dur = [v for t, v in s if start <= t < end]
            r["slow"] = 100 * (1 - st.mean(dur) / st.mean(bef)); r["tail"] = 100 * (1 - q(dur, .01) / st.mean(bef))
    rows.append(r)
keys = list(rows[0].keys()) if rows else []
with open(f"{D}/summary.csv", "w") as f:
    f.write(",".join(keys) + "\n")
    for r in rows: f.write(",".join(f"{r[k]:.4f}" if isinstance(r[k], float) else str(r[k]) for k in keys) + "\n")
POL = ["dram", "dramcap48", "cxl", "lmcache", "split", "cxlfirst", "borrowtier", "borrowglob"]
out = open(f"{D}/summary.txt", "w")
def say(s=""): print(s); out.write(s + "\n")
for model, speed in (("8b", "4x"), ("8b", "8x"), ("70b", "4x")):
    say(f"## {model} {speed}")
    say(f"  {'policy':11s} {'offered':>7s} {'DRAM wr':>7s} {'CXL wr':>7s} {'DRAM pk':>7s} {'backlog':>8s} {'late ms':>8s} {'hit':>6s} {'pend':>5s} {'util':>5s} {'DRAM GiB':>8s} {'loan':>5s} | reader slow/p1 | Adam slow/p99")
    for p in POL:
        base = {n: next((r for r in rows if r["neighbor"] == n and r["policy"] == p and r["model"] == model and r["speed"] == speed), None) for n in ("none", "reader", "opt")}
        r = base["none"]
        if not r: continue
        rd_ = base["reader"]; op = base["opt"]
        nb = (f" {rd_['slow']:+5.1f}/{rd_['tail']:+5.1f}" if rd_ else "    -     ") + "    | " + (f"{op['slow']:+5.1f}/{op['tail']:+5.1f}" if op else "   -")
        say(f"  {p:11s} {r['offered']:7.1f} {r['store_dram']:7.1f} {r['store_cxl']:7.1f} {r['dram_peak20']:7.1f} {r['backlog_max']:8.1f} {r['late_max']:8.0f} {r['hit_share']:6.3f} {r['pending']:5d} {r['util']:5.2f} {r['occ_dram']:8.1f} {r['loan']:5.2f} |{nb}")
    say()
out.close()
