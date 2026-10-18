#!/usr/bin/env python3
"""RQ1-B agent runtime validation (2026-10-17): vLLM 0.31 + LMCache 0.5.5 (multi-process, DRAM L1) serving real agent
runs (run_agent.py, OpenAI Agents SDK). Derived from run_2a.py; same process layout (LMCache server on cpus 120-126,
vLLM on 96-119, client on 124-126). Logging-only instrumentation: the LMCache server gets PYTHONPATH=kvevt/ so its
event bus is mirrored to <tag>-kvevents.jsonl (see kvevt/sitecustomize.py); vLLM is unmodified (tool calling enabled
with the hermes parser, GPU KV cache limited with --num-gpu-blocks-override so that the host cache sees the reuse).
Files: <tag>-lmcache.log, <tag>-server.log, <tag>-kvevents.jsonl, <tag>-agent.jsonl, <tag>-status.txt, <tag>-meta.txt.
usage: run_agent_exp.py <out_dir> <tag> <n_tasks> <workers> [--l1-gb 2] [--gpu-blocks 2560] [--max-turns 6]
                        [--seed 11] [--latency-scale 1.0] [--max-model-len 8192] [--model Qwen/Qwen2.5-3B-Instruct-AWQ]"""
import argparse, json, os, signal, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ENV_BIN = "/mnt/local/ghu4/envs/lmcache/bin"; AGENT_PY = "/mnt/local/ghu4/envs/agent/bin/python"
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("tag"); ap.add_argument("n_tasks", type=int); ap.add_argument("workers", type=int)
ap.add_argument("--l1-gb", type=float, default=2.0); ap.add_argument("--gpu-blocks", type=int, default=2560); ap.add_argument("--max-turns", type=int, default=6)
ap.add_argument("--seed", type=int, default=11); ap.add_argument("--latency-scale", default="1.0"); ap.add_argument("--max-model-len", type=int, default=8192)
ap.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct-AWQ")
ap.add_argument("--workload", default="agent_tasks", help="agent_tasks (short tools, synthetic latency) or agent_tasks_lt (real long tools)")
ap.add_argument("--client-cpus", default="124-126", help="cpu list for the agent client (real tools need many cores, e.g. 32-95)")
ap.add_argument("--bg-trace", default="", help="optional background churn: a Mooncake trace replayed by serve_replay.py on the same server (REAL traffic)")
ap.add_argument("--bg-speed", default="0.05"); ap.add_argument("--bg-window", default="0,3600"); ap.add_argument("--bg-dequant", default="0", help="spread requests sharing a quantized trace timestamp over this many trace seconds (the Mooncake traces are quantized to 3 s)")
ap.add_argument("--lazy-offload", default="", help="LMCache MP lazy offload: '' (off, default) or 'threshold,select' e.g. '1,10' — stores are issued after the request finishes (existing LMCache option, no policy change)")      # 1.5B fp16 emits all tool calls at once and answers wrongly (smoke run 2026-10-17); 3B AWQ keeps the loop multi-step
A = ap.parse_args(); out, tag = A.out, A.tag
MODEL = A.model; VPORT, MPPORT, HPORT = 8100, 5555, 8200
os.makedirs(out, exist_ok=True); meta = open(f"{out}/{tag}-meta.txt", "w")
def mark(name, extra=""): meta.write(f"M {name} {time.monotonic_ns()} wall={time.time():.6f} {extra}\n"); meta.flush()
env = dict(os.environ, HF_HOME="/mnt/local/ghu4/hf", XDG_CACHE_HOME="/mnt/local/ghu4/cache", TMPDIR="/mnt/local/ghu4/tmp",
           VLLM_CACHE_ROOT="/mnt/local/ghu4/cache/vllm", PYTHONHASHSEED="0", LMCACHE_DISABLE_BANNER="1")
mark("config", json.dumps(dict(n_tasks=A.n_tasks, workers=A.workers, l1_gb=A.l1_gb, gpu_blocks=A.gpu_blocks, max_turns=A.max_turns, seed=A.seed, latency_scale=A.latency_scale, max_model_len=A.max_model_len, model=MODEL, lazy_offload=A.lazy_offload, workload=A.workload, client_cpus=A.client_cpus, bg_trace=A.bg_trace, bg_speed=A.bg_speed, bg_dequant=A.bg_dequant)))
lm_env = dict(env, PYTHONPATH=f"{HERE}/kvevt", KVEVT_OUT=f"{out}/{tag}-kvevents.jsonl")
srv = [f"{ENV_BIN}/lmcache", "server", "--host", "127.0.0.1", "--port", str(MPPORT), "--http-host", "127.0.0.1", "--http-port", str(HPORT),
       "--chunk-size", "256", "--eviction-policy", "LRU", "--eviction-trigger-watermark", "0.8", "--l1-size-gb", f"{A.l1_gb:g}"]
lm = subprocess.Popen(["taskset", "-c", "120-126"] + srv, stdout=open(f"{out}/{tag}-lmcache.log", "w"), stderr=subprocess.STDOUT, env=lm_env, start_new_session=True)
for _ in range(600):
    time.sleep(1)
    if lm.poll() is not None: sys.exit(f"{tag}: lmcache server exited rc={lm.returncode}")
    try:
        if urllib.request.urlopen(f"http://127.0.0.1:{HPORT}/healthcheck", timeout=2).status == 200: break
    except Exception: pass
else: sys.exit(f"{tag}: lmcache server not healthy")
mark("lmcache_ready")
kv = {"kv_connector": "LMCacheMPConnector", "kv_connector_module_path": "lmcache.integration.vllm.lmcache_mp_connector", "kv_role": "kv_both",
      "kv_connector_extra_config": {"lmcache.mp.host": "tcp://127.0.0.1", "lmcache.mp.port": MPPORT}}
if A.lazy_offload:
    th, sel = (A.lazy_offload.split(",") + ["10"])[:2]
    kv["kv_connector_extra_config"].update({"lmcache.mp.lazy_offload": True, "lmcache.mp.lazy_offload_threshold": int(th), "lmcache.mp.lazy_offload_select_count": int(sel)})
vl = subprocess.Popen(["taskset", "-c", "96-119", f"{ENV_BIN}/vllm", "serve", MODEL, "--port", str(VPORT), "--max-model-len", str(A.max_model_len), "--max-num-seqs", "16",
                       "--num-gpu-blocks-override", str(A.gpu_blocks), "--gpu-memory-utilization", "0.85", "--enforce-eager", "--dtype", "float16",
                       "--enable-auto-tool-choice", "--tool-call-parser", "hermes", "--kv-transfer-config", json.dumps(kv),
                       "--enable-prompt-tokens-details", "--disable-uvicorn-access-log"],
                      stdout=open(f"{out}/{tag}-server.log", "w"), stderr=subprocess.STDOUT, env=env, start_new_session=True)
for _ in range(1200):
    time.sleep(1)
    if vl.poll() is not None: os.killpg(lm.pid, signal.SIGINT); sys.exit(f"{tag}: vllm exited rc={vl.returncode}")
    try:
        if urllib.request.urlopen(f"http://127.0.0.1:{VPORT}/health", timeout=2).status == 200: break
    except Exception: pass
mark("vllm_ready")
stat = subprocess.Popen(["bash", "-c", f"while true; do echo \"T $(date +%s.%N)\"; curl -s http://127.0.0.1:{HPORT}/status; echo; sleep 2; done"],
                        stdout=open(f"{out}/{tag}-status.txt", "w"), stderr=subprocess.DEVNULL, start_new_session=True)
time.sleep(2); mark("serve_start")
cenv = dict(env, AGENT_TOOL_LATENCY_SCALE=A.latency_scale, AGENT_WORKLOAD=A.workload)
bg = None
if A.bg_trace:
    t0, t1 = A.bg_window.split(",")
    bg = subprocess.Popen(["taskset", "-c", "127", f"{ENV_BIN}/python", f"{HERE}/../lmcache/serve_replay.py", f"http://127.0.0.1:{VPORT}", MODEL, A.bg_trace, t0, t1, A.bg_speed, str(A.max_model_len), "256"],
                          stdout=open(f"{out}/{tag}-bg.txt", "w"), stderr=subprocess.STDOUT, env=dict(env, REPLAY_DEQUANT_S=A.bg_dequant), start_new_session=True)
    mark("bg_start", f"trace={os.path.basename(A.bg_trace)} speed={A.bg_speed} dequant={A.bg_dequant}")
rc = subprocess.run(["taskset", "-c", A.client_cpus, AGENT_PY, f"{HERE}/run_agent.py", f"http://127.0.0.1:{VPORT}", MODEL, f"{out}/{tag}-agent.jsonl", str(A.n_tasks), str(A.workers), str(A.max_turns), str(A.seed)],
                    stdout=open(f"{out}/{tag}-client.txt", "w"), stderr=subprocess.STDOUT, env=cenv).returncode
mark("serve_end", f"client_rc={rc}"); time.sleep(8)
if bg: os.killpg(bg.pid, signal.SIGTERM); mark("bg_end")
os.killpg(stat.pid, signal.SIGTERM)
for p in (vl, lm):
    os.killpg(p.pid, signal.SIGINT)
    try: p.wait(timeout=120)
    except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); p.wait()
mark("done"); meta.close(); print(f"{tag}: client rc={rc}", flush=True)
