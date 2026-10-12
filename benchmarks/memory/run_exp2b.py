#!/usr/bin/env python3
"""Experiment 2b of 2026-10-11 (capacity-matched KV tiers, HOST MEMORY TRAFFIC EMULATION with kvemu2), one run:
optional cxlpathd (borrow policies: store "kvemu" on /dev/dax1.0, probe and bound as in the policy campaign) ->
optional neighbour (cpus 0..) -> settle -> 60 s BEFORE window -> kvemu2 -> stop everything.
Files: <tag>-emu.txt, <tag>-neighbor.txt, <tag>-daemon.csv, <tag>-meta.txt.
usage: run_exp2b.py <out_dir> <tag> <trace> <block_KiB> <t0_s> <t1_s> <speed> <policy> <dram_GiB> <cxl_GiB>
         [--neighbor none|reader|opt|pr|llama] [--vthreads 80] [--watermark 0.8] [--store-cap 0] [--loan-block-s 1]
         [--before-s 60] [--reader-chunk <MiB>] [--phases <on_s>:<off_s>] [--phase-budgets <on_GBps>:<off_GBps>]
Added 2026-10-12 (budget-gated admission): the quiet BEFORE window length; the reader's progress granularity; a neighbour
schedule (from kvemu2's START the neighbour runs on_s, is stopped (SIGSTOP) off_s, and so on; "M phase on|off" lines);
with --phase-budgets the budget policy reads its budget from /dev/shm/kv2_budget_<tag>, switched with the phases (an
ORACLE signal). kvemu2 options in the environment (KV2_SPLIT_SHARE, KV2_WARM, KV2_BUDGET_GBPS) are passed through and logged."""
import os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); POL = os.path.join(HERE, "..", "policy"); BUDGET = os.path.join(HERE, "..", "budget")
B = os.path.join(HERE, "..", "..", "system", "cxlpath", "build")
out, tag, trace, blk, t0, t1, speed, policy, dram, cxl = sys.argv[1:11]
a = dict(zip(sys.argv[11::2], sys.argv[12::2]))
neighbor = a.get("--neighbor", "none"); vthreads = int(a.get("--vthreads", "80")); wm = a.get("--watermark", "0.8")
scap = a.get("--store-cap", "0"); lbs = a.get("--loan-block-s", "1")
before_s = float(a.get("--before-s", "60")); rchunk = a.get("--reader-chunk"); phases = a.get("--phases"); pbud = a.get("--phase-budgets")
BOUND = {"none": ("16", "1.09"), "reader": ("16", "1.09"), "opt": ("80", "1.04"), "pr": ("80", "1.055"), "llama": ("80", "1.06")}
os.makedirs(out, exist_ok=True); meta = open(f"{out}/{tag}-meta.txt", "w")
def mark(name, extra=""): meta.write(f"M {name} {time.monotonic_ns()} {extra}\n"); meta.flush()
mark("config", f"trace={os.path.basename(trace)} block_KiB={blk} t0={t0} t1={t1} speed={speed} policy={policy} dram={dram} cxl={cxl} "
               f"watermark={wm} store_cap={scap} neighbor={neighbor} vthreads={vthreads} loan_block_s={lbs} before_s={before_s:g} "
               f"reader_chunk={rchunk} phases={phases} phase_budgets={pbud} " + " ".join(f"{k}={v}" for k, v in sorted(os.environ.items()) if k.startswith("KV2_")))
daemon, store = None, None
if policy.startswith("borrow"):
    store = "kvemu"; cpu, bound = BOUND[neighbor]
    subprocess.run([f"{B}/cxlp_admin", store, "destroy"], capture_output=True)
    subprocess.run([f"{B}/cxlp_mkstore", store, "8192", "4096", "/dev/dax1.0"], capture_output=True, check=True)
    daemon = subprocess.Popen([f"{B}/cxlpathd", store, "--cpu", cpu, "--bound", bound, "--loan-block-s", lbs, "--log", f"{out}/{tag}-daemon.csv"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(300):
        time.sleep(0.1)
        if "alive=1" in subprocess.run([f"{B}/cxlp_admin", store, "view"], capture_output=True, text=True).stdout: break
    mark("daemon_ready", f"probe_cpu={cpu} bound={bound}")
nb = None
if neighbor != "none":
    cpus = f"0-{vthreads - 1}"; venv = dict(os.environ, OMP_NUM_THREADS=str(vthreads), OMP_PROC_BIND="close", OMP_PLACES="{0}:" + str(vthreads) + ":1")
    nlog = open(f"{out}/{tag}-neighbor.txt", "w")
    if neighbor == "opt": nb = subprocess.Popen(["taskset", "-c", cpus, "python3", f"{BUDGET}/opt_step.py", str(vthreads), "1500", "100000"], stdout=nlog, stderr=subprocess.STDOUT, env=venv)
    elif neighbor == "pr": nb = subprocess.Popen(["python3", f"{POL}/gapbs_victim.py", str(vthreads), cpus, "100000", "26"], stdout=nlog, stderr=subprocess.STDOUT)
    elif neighbor == "llama": nb = subprocess.Popen(["python3", f"{POL}/llama_victim.py", str(vthreads), cpus, "100000"], stdout=nlog, stderr=subprocess.STDOUT)
    elif neighbor == "reader": nb = subprocess.Popen([f"{POL}/reader_victim", "8", "0"] + ([rchunk] if rchunk else []), stdout=nlog, stderr=subprocess.STDOUT)
    time.sleep(40 if neighbor in ("pr", "llama") else 25)
    mark("before_start"); time.sleep(before_s); mark("before_end")
args = [f"{HERE}/kvemu2", trace, blk, t0, t1, speed, policy, dram, cxl, wm, "64", "96", "4", "9.5", "7300", scap] + ([store] if store else [])
kenv = dict(os.environ); bfile = None
if pbud:
    bon, boff = pbud.split(":"); bfile = f"/dev/shm/kv2_budget_{tag}"; open(bfile, "w").write(bon + "\n"); kenv["KV2_BUDGET_FILE"] = bfile
efile = f"{out}/{tag}-emu.txt"
kp = subprocess.Popen(args, stdout=open(efile, "w"), stderr=subprocess.STDOUT, env=kenv)
if phases:
    on_s, off_s = map(float, phases.split(":")); t_start = None
    while t_start is None and kp.poll() is None:
        time.sleep(0.05); m = re.search(r"^START (\d+)", open(efile).read(), re.M)
        if m: t_start = int(m[1])
    state, nxt = 1, (t_start or 0) + int(on_s * 1e9)
    while kp.poll() is None:
        if time.monotonic_ns() >= nxt:
            state ^= 1
            if nb: os.kill(nb.pid, signal.SIGCONT if state else signal.SIGSTOP)
            if bfile: open(bfile, "w").write((bon if state else boff) + "\n")
            mark("phase", "on" if state else "off"); nxt += int((on_s if state else off_s) * 1e9)
        time.sleep(0.005)
    if nb and not state: os.kill(nb.pid, signal.SIGCONT)
rc = kp.wait()
if bfile: os.remove(bfile)
mark("emu_end", f"rc={rc}")
if nb: nb.send_signal(signal.SIGTERM); nb.wait()
if daemon:
    daemon.send_signal(signal.SIGTERM); daemon.wait(); subprocess.run([f"{B}/cxlp_admin", store, "destroy"], capture_output=True)
mark("done"); meta.close()
print(f"{tag}: kvemu2 rc={rc}", flush=True)
