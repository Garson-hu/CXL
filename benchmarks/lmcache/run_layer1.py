#!/usr/bin/env python3
"""Layer 1 of the LMCache KV-traffic characterization (2026-10-10): real vLLM + LMCache on c28's GPU, a Mooncake trace
window replayed open-loop, optionally beside one neighbour program from the policy campaign.
Order: start the server (cpus 96-127) -> wait until healthy -> start the neighbour (cpus 0..) -> let it settle ->
BEFORE window (server idle) -> start the PCIe sampler -> replay -> stop everything. Mono-ns markers go to <tag>-meta.txt.
Files: <tag>-server.log (vLLM + LMCache log), <tag>-pcie.txt, <tag>-client.txt, <tag>-neighbor.txt, <tag>-meta.txt.
usage: run_layer1.py <out_dir> <tag> <trace.jsonl> <t0_s> <t1_s> <speed>
         [--neighbor none|reader|pr|opt|llama] [--vthreads 80] [--cpu-gb 100] [--before 60] [--model M] [--duration S]"""
import os, signal, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); POL = os.path.join(HERE, "..", "policy"); BUDGET = os.path.join(HERE, "..", "budget")
ENV_BIN = "/mnt/local/ghu4/envs/lmcache/bin"; PORT = 8100; URL = f"http://127.0.0.1:{PORT}"
out, tag, trace, t0, t1, speed = sys.argv[1:7]
a = dict(zip(sys.argv[7::2], sys.argv[8::2]))
neighbor = a.get("--neighbor", "none"); vthreads = int(a.get("--vthreads", "80")); cpu_gb = a.get("--cpu-gb", "100")
before = float(a.get("--before", "60")); model = a.get("--model", "Qwen/Qwen2.5-1.5B-Instruct"); duration = a.get("--duration", "0")
os.makedirs(out, exist_ok=True)
meta = open(f"{out}/{tag}-meta.txt", "w")
def mark(name, extra=""): meta.write(f"M {name} {time.monotonic_ns()} {extra}\n"); meta.flush()

senv = dict(os.environ, HF_HOME="/mnt/local/ghu4/hf", XDG_CACHE_HOME="/mnt/local/ghu4/cache", TMPDIR="/mnt/local/ghu4/tmp",
            VLLM_CACHE_ROOT="/mnt/local/ghu4/cache/vllm", PYTHONHASHSEED="0", LMCACHE_CHUNK_SIZE="256",
            LMCACHE_LOCAL_CPU="True", LMCACHE_MAX_LOCAL_CPU_SIZE=cpu_gb)
mark("config", f"trace={os.path.basename(trace)} t0={t0} t1={t1} speed={speed} neighbor={neighbor} vthreads={vthreads} cpu_gb={cpu_gb} model={model} duration={duration}")
mark("clock", f"wall={time.time():.6f}")       # mono <-> wall offset, to align LMCache log times with the PCIe samples
slog = open(f"{out}/{tag}-server.log", "w")
server = subprocess.Popen(["taskset", "-c", "96-127", f"{ENV_BIN}/vllm", "serve", model, "--port", str(PORT),
                           "--max-model-len", "32768", "--gpu-memory-utilization", "0.85", "--enforce-eager", "--dtype", "float16",
                           "--kv-transfer-config", '{"kv_connector":"LMCacheConnectorV1","kv_role":"kv_both"}',
                           "--enable-prompt-tokens-details", "--disable-uvicorn-access-log"],
                          stdout=slog, stderr=subprocess.STDOUT, env=senv, start_new_session=True)
for _ in range(1200):
    time.sleep(1)
    if server.poll() is not None: sys.exit(f"{tag}: server exited rc={server.returncode}")
    try:
        if urllib.request.urlopen(URL + "/health", timeout=2).status == 200: break
    except Exception: pass
else: sys.exit(f"{tag}: server not healthy after 20 min")
mark("server_ready")

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

plog = open(f"{out}/{tag}-pcie.txt", "w")
sampler = subprocess.Popen(["taskset", "-c", "95", f"{ENV_BIN}/python", f"{HERE}/pcie_sampler.py"], stdout=plog, stderr=subprocess.STDOUT)
time.sleep(2)
mark("serve_start")
clog = open(f"{out}/{tag}-client.txt", "w")
rc = subprocess.run(["taskset", "-c", "124-126", f"{ENV_BIN}/python", f"{HERE}/serve_replay.py", URL, model, trace, t0, t1, speed, "32768", "1024", duration],
                    stdout=clog, stderr=subprocess.STDOUT).returncode
mark("serve_end", f"client_rc={rc}")
time.sleep(5)
for p in (sampler, nb):
    if p: p.send_signal(signal.SIGTERM); p.wait()
os.killpg(server.pid, signal.SIGINT)
try: server.wait(timeout=120)
except subprocess.TimeoutExpired: os.killpg(server.pid, signal.SIGKILL); server.wait()
mark("done"); meta.close()
print(f"{tag}: client rc={rc}", flush=True)
