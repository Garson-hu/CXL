#!/usr/bin/env python3
"""Phase 2, core figure: a periodic checkpoint copy (S GiB every P s) beside a DRAM-bound victim, under the
three simple policies (all-DRAM with NT stores, all-DRAM with plain stores, rate-limited all-DRAM, all-CXL)
and through cxlpath. Records the victim's timeline and the producer's copy windows.
  run_policy.py <outdir> <victim: opt|reader> <policy> <rep> [--rate G] [--bound X] [--margin Y] [--snapshot 64] [--period 30] [--periods 6]
CPU layout: victim opt = cpus 0-79 (probe 80); victim reader = cpus 0-7 (probe 16); producer 8 threads on cpus 96-99 + 112-115."""
import os, signal, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "..", "..", "system", "cxlpath", "build"); BUDGET = os.path.join(HERE, "..", "budget")
out, victim, policy, rep = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
a = dict(zip(sys.argv[5::2], sys.argv[6::2])); rate = a.get("--rate"); bound = a.get("--bound", "1.10"); margin = a.get("--margin"); S = a.get("--snapshot", "64"); P = a.get("--period", "30"); NP = int(a.get("--periods", "6"))
tag = f"{victim}-{policy}" + (f"-b{bound}" if policy == "cxlpath" else "") + (f"-r{rate}" if rate else "") + f"-rep{rep}"
os.makedirs(out, exist_ok=True); probe_cpu = "80" if victim == "opt" else "16"
daemon = None
if policy == "cxlpath":
    subprocess.run([f"{B}/cxlp_mkstore", "policy", "65536", "49152", "/dev/dax0.0", "/dev/dax1.0"], capture_output=True)
    dargs = [f"{B}/cxlpathd", "policy", "--cpu", probe_cpu, "--bound", bound, "--log", f"{out}/{tag}-daemon.csv"] + (["--margin", margin] if margin else [])
    daemon = subprocess.Popen(dargs)
    for _ in range(300):
        time.sleep(0.1)
        if "alive=1" in subprocess.run([f"{B}/cxlp_admin", "policy", "view"], capture_output=True, text=True).stdout: break
env = dict(os.environ, OMP_NUM_THREADS="80", OMP_PROC_BIND="close", OMP_PLACES="{0}:80:1")
vlog = open(f"{out}/{tag}-victim.txt", "w")
if victim == "opt": v = subprocess.Popen(["taskset", "-c", "0-79", "python3", f"{BUDGET}/opt_step.py", "80", "1500", "100000"], stdout=vlog, stderr=subprocess.STDOUT, env=env)
else: v = subprocess.Popen([f"{HERE}/reader_victim", "8", "0"], stdout=vlog, stderr=subprocess.STDOUT)
time.sleep(25)                                                                    # victim settles (Adam: allocation + warm-up)
pargs = [f"{HERE}/ckpt_producer", policy, S, "8", "96", P, str(NP)] + (["--rate", rate] if rate else []) + (["--store", "policy"] if policy == "cxlpath" else [])
plog = open(f"{out}/{tag}-producer.txt", "w"); p = subprocess.run(pargs, stdout=plog, stderr=subprocess.STDOUT); plog.close()
time.sleep(3); v.send_signal(signal.SIGTERM); v.wait(); vlog.close()
if daemon: daemon.send_signal(signal.SIGTERM); daemon.wait(); subprocess.run([f"{B}/cxlp_admin", "policy", "destroy"], capture_output=True)
print(f"{tag}: producer rc={p.returncode}", flush=True)
