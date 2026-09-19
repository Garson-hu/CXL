#!/usr/bin/env python3
"""B5 live gate: the GPU path follows DRAM pressure. A real cxlpathd runs; cxlp_gpu_test copies 1 GiB
GPU -> CXL buffer set in a loop; a 64-thread DRAM aggressor is injected for 3 s.
usage: b5_live.py <outdir>"""
import os, subprocess, sys, time, signal
B = "build/"; out = sys.argv[1]; os.makedirs(out, exist_ok=True); fails = []
def sh(*a): return subprocess.run(a, capture_output=True, text=True)
def check(ok, msg): print(("  ok   " if ok else "  FAIL ") + msg); (None if ok else fails.append(msg))
print(sh(B + "cxlp_mkstore", "gpu", "8192", "4096", "/dev/dax0.0", "/dev/dax1.0").stdout.strip())
p = sh(B + "cxlp_gpu_test", "gpu", "paths"); print(p.stdout.strip()); check(p.returncode == 0, "direct, staged and mixed copies byte-exact; staged share exactly as published")
d = subprocess.Popen([B + "cxlpathd", "gpu", "--cpu", "16", "--log", f"{out}/B5-daemon.csv"])
for _ in range(200):
    time.sleep(0.05)
    if "alive=1" in sh(B + "cxlp_admin", "gpu", "view").stdout: break
g = subprocess.Popen([B + "cxlp_gpu_test", "gpu", "live", "15"], stdout=subprocess.PIPE, text=True)
time.sleep(7.0); a = sh(B + "dram_aggressor", "64", "32", "3"); gout = g.communicate()[0]; d.send_signal(signal.SIGTERM); d.wait()
open(f"{out}/B5-gpu-copies.txt", "w").write(gout + a.stdout)
t0 = int([l for l in gout.splitlines() if l.startswith("T0")][0].split()[1])
a0 = (int([l for l in a.stdout.splitlines() if l.startswith("START")][0].split()[1]) - t0) / 1e6
a1 = (int([l for l in a.stdout.splitlines() if l.startswith("END")][0].split()[1]) - t0) / 1e6
cp = [tuple(float(x) for x in l.split()[1:]) for l in gout.splitlines() if l.startswith("COPY")]      # (end ms, staged share, GiB/s)
def seg(lo, hi): return [c for c in cp if lo < c[0] <= hi]
first = seg(0, 600); calm = seg(2500, a0); press = seg(a0 + 700, a1); after = seg(a1 + 2500, 1e9)
fmt = lambda w: "staged share %.2f, %.2f GiB/s (%d copies)" % (sum(c[1] for c in w) / len(w), sum(c[2] for c in w) / len(w), len(w)) if w else "no copies"
print(f"    first 0.6 s                 : {fmt(first)}"); print(f"    calm, before the aggressor  : {fmt(calm)}")
print(f"    aggressor {a0:.0f}-{a1:.0f} ms    : {fmt(press)}"); print(f"    2.5 s after it left         : {fmt(after)}")
check(bool(first) and first[0][1] <= 0.2, "a first burst starts on the direct path (no DRAM traffic)")
check(bool(calm) and sum(c[1] for c in calm) / len(calm) >= 0.9, "DRAM calm: the staged path takes over (full link speed)")
check(bool(press) and sum(c[1] for c in press) / len(press) <= 0.1, "DRAM under pressure: back to the direct path")
check(bool(after) and sum(c[1] for c in after) / len(after) >= 0.9, "pressure gone: staged again")
check("data_errors=0" in gout, "every verified copy byte-exact while paths were switching")
sh(B + "cxlp_admin", "gpu", "destroy"); print("PASS" if not fails else "FAIL: " + "; ".join(fails)); sys.exit(1 if fails else 0)
