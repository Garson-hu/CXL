#!/usr/bin/env python3
"""Launcher for the KV miss-cost microbenchmark (2026-10-18): LMCache server (L1 in DRAM or on a CXL devdax) + vLLM
with a small GPU KV cache, then misscost_bench.py. Same process layout as run_2a.py / run_agent_exp.py.
usage: misscost_run.py <out_dir> <tag> <dram|dax> [--model Qwen/Qwen2.5-3B-Instruct-AWQ] [--l1-gb 4] [--gpu-blocks 1024]
                       [--Ls 1024,2048,4096,7680] [--reps 3] [--max-model-len 8192]"""
import argparse, json, os, signal, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ENV_BIN = "/mnt/local/ghu4/envs/lmcache/bin"
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("tag"); ap.add_argument("cfg", choices=["dram", "dax"])
ap.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct-AWQ"); ap.add_argument("--l1-gb", type=float, default=4.0); ap.add_argument("--gpu-blocks", type=int, default=1024)
ap.add_argument("--Ls", default="1024,2048,4096,7680"); ap.add_argument("--reps", type=int, default=3); ap.add_argument("--max-model-len", type=int, default=8192)
A = ap.parse_args(); out, tag = A.out, A.tag; VPORT, MPPORT, HPORT = 8100, 5555, 8200
os.makedirs(out, exist_ok=True); meta = open(f"{out}/{tag}-meta.txt", "w")
def mark(name, extra=""): meta.write(f"M {name} {time.monotonic_ns()} wall={time.time():.6f} {extra}\n"); meta.flush()
env = dict(os.environ, HF_HOME="/mnt/local/ghu4/hf", XDG_CACHE_HOME="/mnt/local/ghu4/cache", TMPDIR="/mnt/local/ghu4/tmp", VLLM_CACHE_ROOT="/mnt/local/ghu4/cache/vllm", PYTHONHASHSEED="0", LMCACHE_DISABLE_BANNER="1")
mark("config", json.dumps(dict(cfg=A.cfg, model=A.model, l1_gb=A.l1_gb, gpu_blocks=A.gpu_blocks, Ls=A.Ls, reps=A.reps, max_model_len=A.max_model_len)))
srv = [f"{ENV_BIN}/lmcache", "server", "--host", "127.0.0.1", "--port", str(MPPORT), "--http-host", "127.0.0.1", "--http-port", str(HPORT), "--chunk-size", "256", "--eviction-policy", "LRU", "--eviction-trigger-watermark", "0.8", "--l1-size-gb", f"{A.l1_gb:g}"]
if A.cfg == "dax": srv += ["--l1-devdax-path", "/dev/dax1.0", "--no-l1-use-lazy", "--shm-name", ""]
lm = subprocess.Popen(["taskset", "-c", "120-126"] + srv, stdout=open(f"{out}/{tag}-lmcache.log", "w"), stderr=subprocess.STDOUT, env=env, start_new_session=True)
for _ in range(600):
    time.sleep(1)
    if lm.poll() is not None: sys.exit(f"{tag}: lmcache server exited rc={lm.returncode}")
    try:
        if urllib.request.urlopen(f"http://127.0.0.1:{HPORT}/healthcheck", timeout=2).status == 200: break
    except Exception: pass
else: sys.exit(f"{tag}: lmcache server not healthy")
mark("lmcache_ready")
kv = {"kv_connector": "LMCacheMPConnector", "kv_connector_module_path": "lmcache.integration.vllm.lmcache_mp_connector", "kv_role": "kv_both", "kv_connector_extra_config": {"lmcache.mp.host": "tcp://127.0.0.1", "lmcache.mp.port": MPPORT}}
vl = subprocess.Popen(["taskset", "-c", "96-119", f"{ENV_BIN}/vllm", "serve", A.model, "--port", str(VPORT), "--max-model-len", str(A.max_model_len), "--max-num-seqs", "8", "--num-gpu-blocks-override", str(A.gpu_blocks),
                       "--gpu-memory-utilization", "0.85", "--enforce-eager", "--dtype", "float16", "--kv-transfer-config", json.dumps(kv), "--enable-prompt-tokens-details", "--disable-uvicorn-access-log"],
                      stdout=open(f"{out}/{tag}-server.log", "w"), stderr=subprocess.STDOUT, env=env, start_new_session=True)
for _ in range(1200):
    time.sleep(1)
    if vl.poll() is not None: os.killpg(lm.pid, signal.SIGINT); sys.exit(f"{tag}: vllm exited rc={vl.returncode}")
    try:
        if urllib.request.urlopen(f"http://127.0.0.1:{VPORT}/health", timeout=2).status == 200: break
    except Exception: pass
mark("vllm_ready"); time.sleep(2); mark("bench_start")
rc = subprocess.run(["taskset", "-c", "124-126", f"{ENV_BIN}/python", f"{HERE}/misscost_bench.py", f"http://127.0.0.1:{VPORT}", A.model, f"{out}/{tag}-ttft.csv", A.Ls, str(A.reps), str(max(2 * A.gpu_blocks * 16, 32768))],
                    stdout=open(f"{out}/{tag}-client.txt", "w"), stderr=subprocess.STDOUT, env=env).returncode
mark("bench_end", f"client_rc={rc}"); time.sleep(3)
for p in (vl, lm):
    os.killpg(p.pid, signal.SIGINT)
    try: p.wait(timeout=120)
    except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); p.wait()
mark("done"); meta.close(); print(f"{tag}: client rc={rc}", flush=True)
