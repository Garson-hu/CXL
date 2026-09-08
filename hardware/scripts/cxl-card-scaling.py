#!/usr/bin/env python3
"""Phase 2b: aggregate CXL bandwidth vs number of cards (1 / 2 / 4), traffic mode
(read / NT-write / mixes), and total threads. 1 card = Pair B even 256B class;
2 cards = Pair B all chunks; 4 cards = Pair B + Pair A concurrently.
Each process gets its own CPU block (32 cpus = 2 CCDs) and dax region."""
import subprocess, re, csv, sys, statistics, time, os
CP = "benchmarks/memory/cxlprobe"
OUT = "experimental_results/2026-09-08-cxl-card-scaling"; os.makedirs(OUT, exist_ok=True)
SECS = 4; REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
MODES = {"read": 1.0, "write": 0.0, "mix31": 0.75, "mix11": 0.5, "mix13": 0.25}
# (dax, reader-region, writer-region, stride, chunk) per device config; class offset 0
CFG = {1: [("/dev/dax2.0", "32G", "160G", 512, 256)],
       2: [("/dev/dax2.0", "32G", "160G", 256, 256)],
       4: [("/dev/dax2.0", "32G", "160G", 256, 256), ("/dev/dax0.0", "32G", "128G", 256, 256)]}

def launch(dax, region, kind, stride, chunk, threads, cpu_off, tag):
    mode = "daxstride" if kind == "read" else "daxstridewr"
    cmd = [CP, f"--mode={mode}", f"--dax={dax}", f"--dax-offset={region}", "--size=4G",
           f"--threads={threads}", f"--secs={SECS}", f"--stride={stride}", f"--chunk={chunk}",
           "--offset=0", f"--cpu-offset={cpu_off}", f"--tag={tag}"]
    return tag, threads, subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

rows = []
with open(f"{OUT}/scaling.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["rep", "devices", "mode", "T", "proc", "threads", "bw_gib_s"])
    for rep in range(1, REPS + 1):
        for devices, cfg in CFG.items():
            for T in (4, 8, 16, 32):
                for mode, rfrac in MODES.items():
                    nr = round(T * rfrac); nw = T - nr
                    procs, cpu = [], 0
                    for i, (dax, rreg, wreg, st, ch) in enumerate(cfg):
                        share = len(cfg)
                        tr = max(1, nr // share) if nr else 0
                        tw = max(1, nw // share) if nw else 0
                        if tr: procs.append(launch(dax, rreg, "read", st, ch, tr, cpu, f"r{i}")); cpu += 32
                        if tw: procs.append(launch(dax, wreg, "write", st, ch, tw, cpu, f"w{i}")); cpu += 32
                    for tag, th, p in procs:
                        out = p.communicate()[0]
                        m = re.search(r"bw=([\d.]+)", out); bw = float(m.group(1)) if m else float("nan")
                        w.writerow([rep, devices, mode, T, tag, th, bw]); f.flush()
                        rows.append((rep, devices, mode, T, tag, th, bw))
                    print(f"rep{rep} dev{devices} {mode:6s} T={T:2d}  agg={sum(r[6] for r in rows if r[:4]==(rep,devices,mode,T)):6.1f}", flush=True)
# summary: median over reps of aggregate
agg = {}
for rep, d, m, T, tag, th, bw in rows: agg.setdefault((d, m, T, rep), 0.0); agg[(d, m, T, rep)] += bw
med = {}
for (d, m, T, rep), v in agg.items(): med.setdefault((d, m, T), []).append(v)
with open(f"{OUT}/summary.txt", "w") as s:
    s.write("aggregate GiB/s (median of reps)\ndevices mode    T=4    T=8   T=16   T=32\n")
    for d in (1, 2, 4):
        for m in MODES:
            s.write(f"{d:7d} {m:6s} " + " ".join(f"{statistics.median(med[(d,m,T)]):6.1f}" for T in (4,8,16,32)) + "\n")
print(open(f"{OUT}/summary.txt").read())
