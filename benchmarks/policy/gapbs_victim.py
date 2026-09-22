#!/usr/bin/env python3
"""GAPBS PageRank as a victim: `pr` on a Kronecker graph (2^26 vertices, ~1.05 G undirected edges, ~9 GB CSR),
<trials> trials; every "Trial Time" line is stamped: "[STEP] i <seconds> <mono ns>" (same format as opt_step.py).
usage: gapbs_victim.py <threads> <cpulist> <trials> [scale]"""
import os, signal, subprocess, sys, time
threads, cpus, trials = sys.argv[1], sys.argv[2], sys.argv[3]; scale = sys.argv[4] if len(sys.argv) > 4 else "26"
env = dict(os.environ, OMP_NUM_THREADS=threads, OMP_PROC_BIND="close", OMP_PLACES="{" + cpus.split("-")[0] + "}:" + threads + ":1")
p = subprocess.Popen(["taskset", "-c", cpus, "stdbuf", "-oL", os.path.expanduser("~/apps/gapbs/pr"), "-g", scale, "-n", trials], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
signal.signal(signal.SIGTERM, lambda s, f: p.terminate())
i = 0
for line in p.stdout:
    if line.startswith("Trial Time:"): print(f"[STEP] {i} {float(line.split()[2]):.4f} {time.monotonic_ns()}", flush=True); i += 1
    elif line.startswith("Graph has") or line.startswith("Build Time"): print(f"# {line.strip()} at {time.monotonic_ns()}", flush=True)
p.wait(); print(f"END {time.monotonic_ns()}", flush=True)
