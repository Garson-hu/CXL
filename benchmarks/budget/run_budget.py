#!/usr/bin/env python3
"""Phase 1 driver: how much DRAM write traffic can a co-running DRAM-bound program tolerate?
  run_budget.py synth|lulesh|opt <outdir> [reps]
Victim / probe / writer placement (METHODOLOGY: separate CCDs):
  synth : victim cpus 0-7, probe cpu 16, writers spread over cpus 32-127   (one process: overlap by construction)
  lulesh, opt : victim cpus 0-79 (80 threads), probe cpu 80, writers cpus 96-127 (separate process; overlap checked)
Every row of <outdir>/<victim>.csv is one run; raw stdout of every run goes to <outdir>/raw-<victim>.log."""
import os, signal, statistics as st, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); victim, out = sys.argv[1], sys.argv[2]; reps = int(sys.argv[3]) if len(sys.argv) > 3 else 3
os.makedirs(out, exist_ok=True); raw = open(f"{out}/raw-{victim}.log", "a"); csvp = f"{out}/{victim}.csv"
if not os.path.exists(csvp): open(csvp, "w").write("victim,rep,mode,target,asked_GiBs,write_GiBs,metric,value,probe_p50_ns,overlap_ok\n")
def row(*a): open(csvp, "a").write(",".join(str(x) for x in a) + "\n")
def log(s): raw.write(s + "\n"); raw.flush()

if victim == "synth":
    cfgs = [(0, "pure", "dram")] + [(r, m, "dram") for r in (10, 20, 30, 40, 50, 60, 80, 110, 150, 200) for m in ("pure", "copy")] + [(r, m, "/dev/dax0.0") for r in (10, 20, 30, 40) for m in ("pure", "copy")]
    for rep in range(1, reps + 1):
        for r, m, tgt in cfgs:
            o = subprocess.run([f"{HERE}/budget_synth", str(r), m, tgt, "10"], capture_output=True, text=True).stdout.strip(); log(o)
            kv = dict(x.split("=") for x in o.split()[1:]); row("synth", rep, m, tgt, r, kv["write_GiBs"], "victim_GiBs", kv["victim_GiBs"], kv["probe_p50"], 1); print(rep, o, flush=True)
    sys.exit(0)

env = dict(os.environ, OMP_NUM_THREADS="80", OMP_PROC_BIND="close", OMP_PLACES="{0}:80:1", LULESH_STEP_TIMES="1")
if victim == "lulesh":
    # libveloc was built with GCC 12.4: its libstdc++ must be on the path (the first run silently produced no steps)
    V = os.path.expanduser("~/apps/veloc-inst"); env["LD_LIBRARY_PATH"] = f"{V}/lib64:" + os.path.expanduser("~/checkpoint/veloc_lib/lib64:") + "/opt/ohpc/pub/compiler/gcc/12.4.0/lib64:" + env.get("LD_LIBRARY_PATH", "")
    cmd = ["mpirun", "--bind-to", "none", "-np", "1", "-x", "LULESH_STEP_TIMES", "-x", "OMP_NUM_THREADS", "-x", "OMP_PROC_BIND", "-x", "OMP_PLACES", "-x", "LD_LIBRARY_PATH", "./lulesh2.0.veloc", "-s", "200", "-i", "40"]
    cwd = os.path.expanduser("~/apps/lulesh-veloc"); skip = 5
    steps = lambda txt: [float(l.split("dt=")[1].split()[0]) for l in txt.splitlines() if l.startswith("[STEP]")]
elif victim == "opt":
    cmd = ["taskset", "-c", "0-79", "python3", f"{HERE}/opt_step.py", "80", "1500", "60"]; cwd = HERE; skip = 5
    steps = lambda txt: [float(l.split()[2]) for l in txt.splitlines() if l.startswith("[STEP]")]
elif victim == "pr":                                   # GAPBS PageRank, Kronecker 2^26, 30 trials of ~1.1 s
    cmd = ["python3", f"{HERE}/../policy/gapbs_victim.py", "80", "0-79", "30"]; cwd = HERE; skip = 3
    steps = lambda txt: [float(l.split()[2]) for l in txt.splitlines() if l.startswith("[STEP]")]
elif victim == "llama":                                # llama.cpp decoding, Qwen2.5-7B Q8_0, ~60 s of generation; "steps" = tok/s per 500 ms (higher is better)
    cmd = ["python3", f"{HERE}/../policy/llama_victim.py", "80", "0-79", "2200"]; cwd = HERE; skip = 6
    steps = lambda txt: [float(l.split()[2]) for l in txt.splitlines() if l.startswith("T ")]
levels = [(0, "pure", "dram")] + [(r, m, "dram") for r in (10, 20, 30, 40, 60, 80, 110) for m in ("pure", "copy")] + [(r, "copy", "/dev/dax0.0") for r in (20, 40)] + [(0, "pure", "dram")]
for rep in range(1, reps + 1):
    for r, m, tgt in levels:
        pf = f"{out}/probe-{victim}.tmp"; pl = subprocess.Popen([f"{HERE}/probe_log", "80", pf]); w = None; wstart = 0
        if r:
            n = min(32, max(2, (r + 7) // 8)); w = subprocess.Popen([f"{HERE}/dram_writer", str(r), m, tgt, str(n), "96"], stdout=subprocess.PIPE, text=True)
            wstart = int(w.stdout.readline().split()[1]); time.sleep(3)
        t0 = time.monotonic_ns(); o = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout; t1 = time.monotonic_ns()   # LULESH prints [STEP] on stderr
        wr, ok = 0.0, 1
        if w: w.send_signal(signal.SIGTERM); end = w.stdout.read().split(); w.wait(); wend = int(end[1]); wr = float(end[2].split("=")[1]); ok = int(wstart < t0 and wend > t1)
        pl.send_signal(signal.SIGTERM); pl.wait()
        pv = [float(l.split()[1]) for l in open(pf) if t0 <= int(l.split()[0]) <= t1]; s = steps(o)[skip:]
        if not s: print("VICTIM PRODUCED NO STEPS — aborting:\n" + o[-2000:], flush=True); sys.exit(3)
        med = st.median(s); row(victim, rep, m, tgt, r, wr, "median_step_s", f"{med:.5f}", f"{st.median(pv):.1f}" if pv else "nan", ok)
        log(f"## rep{rep} {m} {tgt} asked={r} write={wr} steps={len(s)} median={med:.5f} overlap={ok}\n" + "\n".join(l for l in o.splitlines() if l.startswith("[STEP]") or "Elapsed" in l))
        print(f"rep{rep} {victim} {m:4s} {tgt:12s} asked {r:3d} wrote {wr:6.2f} GiB/s  median step {med:.5f} s  probe {st.median(pv) if pv else float('nan'):.1f} ns  overlap {ok}", flush=True)
os.remove(pf)
