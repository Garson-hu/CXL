#!/usr/bin/env python3
"""One hardware co-run of the 2026-10-21 validation (Phase 3 filtered-write interference): optional neighbour (the 80-thread Adam
step on cpus 0-79, as on 2026-10-12) -> 25 s settle -> quiet BEFORE window -> kvreplay replays a write log window -> stop.
kvreplay is started first (it maps and pre-faults its arena, prints READY and waits for the go-file), so the pre-fault never
overlaps the quiet window. Files: <tag>-replay.txt (kvreplay output), <tag>-neighbor.txt, <tag>-meta.txt ("M <mark> <mono_ns> ...").
With <writelog> = none the neighbour runs alone for --alone-s after the quiet window (the null distribution of the slowdown).
usage: run_kvreplay.py <out_dir> <tag> <writelog|none> <t0_s> <t1_s> [--neighbor none|opt] [--vthreads 80] [--before-s 60]
         [--alone-s 300] [--dram-gib 64] [--replay "<extra kvreplay options>"]"""
import os, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); BUDGET = os.path.join(HERE, "..", "budget")
out, tag, wlog, t0, t1 = sys.argv[1:6]
a = dict(zip(sys.argv[6::2], sys.argv[7::2]))
neighbor = a.get("--neighbor", "none"); vthreads = int(a.get("--vthreads", "80")); before_s = float(a.get("--before-s", "60"))
alone_s = float(a.get("--alone-s", "300")); dram_gib = a.get("--dram-gib", "64"); extra = a.get("--replay", "").split()
os.makedirs(out, exist_ok=True); meta = open(f"{out}/{tag}-meta.txt", "w")
def mark(name, more=""): meta.write(f"M {name} {time.monotonic_ns()} {more}\n"); meta.flush()
mark("config", f"writelog={wlog} t0={t0} t1={t1} neighbor={neighbor} vthreads={vthreads} before_s={before_s:g} alone_s={alone_s:g} dram_gib={dram_gib} replay={' '.join(extra)}")
go = f"/dev/shm/kvreplay_go_{tag}"
if os.path.exists(go): os.remove(go)
rp = None; rfile = f"{out}/{tag}-replay.txt"
if wlog != "none":
    rp = subprocess.Popen([f"{HERE}/kvreplay", wlog, t0, t1, dram_gib, "--wait-file", go] + extra, stdout=open(rfile, "w"), stderr=subprocess.STDOUT)
nb = None
if neighbor == "opt":
    cpus = f"0-{vthreads - 1}"; venv = dict(os.environ, OMP_NUM_THREADS=str(vthreads), OMP_PROC_BIND="close", OMP_PLACES="{0}:" + str(vthreads) + ":1")
    nb = subprocess.Popen(["taskset", "-c", cpus, "python3", f"{BUDGET}/opt_step.py", str(vthreads), "1500", "100000"], stdout=open(f"{out}/{tag}-neighbor.txt", "w"), stderr=subprocess.STDOUT, env=venv)
    mark("neighbor_start", f"cpus={cpus}")
if rp:                                                       # the replayer must be READY (arena pre-faulted) before the quiet window
    for _ in range(6000):
        if rp.poll() is not None or "READY" in open(rfile).read(): break
        time.sleep(0.1)
    if rp.poll() is not None: mark("replay_failed", f"rc={rp.returncode}"); print(open(rfile).read()[-2000:]); sys.exit(1)
    mark("replay_ready")
if nb: time.sleep(25)
mark("before_start"); time.sleep(before_s); mark("before_end")
if rp:
    open(go, "w").close(); mark("replay_go")
    rc = rp.wait(); os.remove(go); mark("replay_end", f"rc={rc}")
else:
    mark("during_start"); time.sleep(alone_s); mark("during_end")
if nb: nb.send_signal(signal.SIGTERM); nb.wait()
mark("done"); meta.close()
print(f"{tag}: done" + (f" (kvreplay rc={rc})" if rp else ""), flush=True)
