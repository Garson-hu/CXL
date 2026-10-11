#!/usr/bin/env python3
"""Layer 2 of 2026-10-10-lmcache-kv-traffic: host memory traffic emulation (kvemu) of a KV tier, optionally beside one
policy-campaign neighbour (cpus 0..; emulation workers on cpus 96-127 + SMT siblings, the safe placement of
2026-10-09-cxl-topology-interference). Order: neighbour -> settle -> BEFORE window -> kvemu -> stop.
Files: <tag>-emu.txt (kvemu output), <tag>-neighbor.txt, <tag>-meta.txt (mono-ns markers).
usage: run_layer2.py <out_dir> <tag> <trace> <block_KiB> <t0_s> <t1_s> <speed> <capacity_GiB> <dram|cxl>
         [--neighbor none|reader|pr|opt|llama] [--vthreads 80] [--before 60] [--workers 64] [--link 2.9] [--prefill 4600] [--chunk 4] [--store-cap 0]"""
import os, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); POL = os.path.join(HERE, "..", "policy"); BUDGET = os.path.join(HERE, "..", "budget")
out, tag, trace, blk, t0, t1, speed, cap, place = sys.argv[1:10]
a = dict(zip(sys.argv[10::2], sys.argv[11::2]))
neighbor = a.get("--neighbor", "none"); vthreads = int(a.get("--vthreads", "80")); before = float(a.get("--before", "60"))
workers = a.get("--workers", "64"); link = a.get("--link", "2.9"); prefill = a.get("--prefill", "4600"); chunk = a.get("--chunk", "4"); scap = a.get("--store-cap", "0")
os.makedirs(out, exist_ok=True); meta = open(f"{out}/{tag}-meta.txt", "w")
def mark(name, extra=""): meta.write(f"M {name} {time.monotonic_ns()} {extra}\n"); meta.flush()
mark("config", f"trace={os.path.basename(trace)} block_KiB={blk} t0={t0} t1={t1} speed={speed} cap={cap} place={place} neighbor={neighbor} vthreads={vthreads} workers={workers} link={link} prefill={prefill} chunk={chunk} store_cap={scap}")
nb = None
if neighbor != "none":
    cpus = f"0-{vthreads - 1}"; venv = dict(os.environ, OMP_NUM_THREADS=str(vthreads), OMP_PROC_BIND="close", OMP_PLACES="{0}:" + str(vthreads) + ":1")
    nlog = open(f"{out}/{tag}-neighbor.txt", "w")
    if neighbor == "opt": nb = subprocess.Popen(["taskset", "-c", cpus, "python3", f"{BUDGET}/opt_step.py", str(vthreads), "1500", "100000"], stdout=nlog, stderr=subprocess.STDOUT, env=venv)
    elif neighbor == "pr": nb = subprocess.Popen(["python3", f"{POL}/gapbs_victim.py", str(vthreads), cpus, "100000", "26"], stdout=nlog, stderr=subprocess.STDOUT)
    elif neighbor == "llama": nb = subprocess.Popen(["python3", f"{POL}/llama_victim.py", str(vthreads), cpus, "100000"], stdout=nlog, stderr=subprocess.STDOUT)
    elif neighbor == "reader": nb = subprocess.Popen([f"{POL}/reader_victim", "8", "0"], stdout=nlog, stderr=subprocess.STDOUT)
    else: sys.exit(f"unknown neighbor {neighbor}")
    time.sleep(40 if neighbor in ("pr", "llama") else 25)
    mark("before_start"); time.sleep(before); mark("before_end")
elog = open(f"{out}/{tag}-emu.txt", "w")
rc = subprocess.run([f"{HERE}/kvemu", trace, blk, t0, t1, speed, cap, place, workers, "96", chunk, link, prefill, scap], stdout=elog, stderr=subprocess.STDOUT).returncode
mark("emu_end", f"rc={rc}")
if nb: nb.send_signal(signal.SIGTERM); nb.wait()
mark("done"); meta.close()
print(f"{tag}: kvemu rc={rc}", flush=True)
