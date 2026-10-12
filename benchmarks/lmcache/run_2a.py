#!/usr/bin/env python3
"""Experiment 2a (2026-10-12): real vLLM + LMCache in multi-process mode, capacity-matched L1 placements.
  dram    --l1-size-gb TOTAL (pinned DRAM)
  hybrid  LMCache's DRAM-first hybrid L1: --l1-size-gb TOTAL/2 DRAM + TOTAL/2 Device-DAX overflow on /dev/dax1.0
          (a DAX L2 adapter on the same device turns into the L1 overflow; LMCache 0.5.5 has no CXL-first order)
  dax     --l1-devdax-path /dev/dax1.0, TOTAL GiB (pure CXL L1)
Same trace window, rate, model and eviction watermark (0.8) for all; vLLM on cpus 96-119, LMCache server on 120-126,
replay client on 124-126 shared, PCIe sampler v2 on cpu 95; /status of the server polled every 5 s (L1 usage).
Files: <tag>-lmcache.log, <tag>-server.log (vLLM), <tag>-pcie.txt, <tag>-client.txt, <tag>-status.txt, <tag>-meta.txt.
usage: run_2a.py <out_dir> <tag> <trace> <t0_s> <t1_s> <speed> <dram|hybrid|dax> [total_GiB=40] [--ckpt S:P:mode[:rate]]
  --ckpt (experiment 3): ckpt_cxl copies S GiB DRAM -> /dev/dax0.0 every P s (full | rate:<GB/s> | kvprio, the last with
  kvprio_gate.py) with its CXL latency reader, from just before serving to the end: <tag>-ckpt.txt, <tag>-gate.txt."""
import json, os, signal, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ENV_BIN = "/mnt/local/ghu4/envs/lmcache/bin"
out, tag, trace, t0, t1, speed, cfg = sys.argv[1:8]
rest = sys.argv[8:]; ckpt = None
if "--ckpt" in rest: i = rest.index("--ckpt"); ckpt = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
total = float(rest[0]) if rest else 40.0
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"; VPORT, MPPORT, HPORT = 8100, 5555, 8200
os.makedirs(out, exist_ok=True); meta = open(f"{out}/{tag}-meta.txt", "w")
def mark(name, extra=""): meta.write(f"M {name} {time.monotonic_ns()} {extra}\n"); meta.flush()
env = dict(os.environ, HF_HOME="/mnt/local/ghu4/hf", XDG_CACHE_HOME="/mnt/local/ghu4/cache", TMPDIR="/mnt/local/ghu4/tmp",
           VLLM_CACHE_ROOT="/mnt/local/ghu4/cache/vllm", PYTHONHASHSEED="0", LMCACHE_DISABLE_BANNER="1")
mark("config", f"trace={os.path.basename(trace)} t0={t0} t1={t1} speed={speed} cfg={cfg} total_GiB={total} model={MODEL} ckpt={ckpt}")
mark("clock", f"wall={time.time():.6f}")
srv = [f"{ENV_BIN}/lmcache", "server", "--host", "127.0.0.1", "--port", str(MPPORT), "--http-host", "127.0.0.1", "--http-port", str(HPORT),
       "--chunk-size", "256", "--eviction-policy", "LRU", "--eviction-trigger-watermark", "0.8"]
if cfg == "dram": srv += ["--l1-size-gb", f"{total:g}"]
elif cfg == "dax": srv += ["--l1-size-gb", f"{total:g}", "--l1-devdax-path", "/dev/dax1.0", "--no-l1-use-lazy", "--shm-name", ""]
elif cfg == "hybrid":
    srv += ["--l1-size-gb", f"{total / 2:g}", "--l1-devdax-path", "/dev/dax1.0", "--no-l1-use-lazy", "--shm-name", "",
            "--l2-adapter", json.dumps({"type": "dax", "devices": [{"device_path": "/dev/dax1.0", "max_dax_size_gb": total / 2}]})]
else: sys.exit(f"unknown cfg {cfg}")
lm = subprocess.Popen(["taskset", "-c", "120-126"] + srv, stdout=open(f"{out}/{tag}-lmcache.log", "w"), stderr=subprocess.STDOUT, env=env, start_new_session=True)
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
vl = subprocess.Popen(["taskset", "-c", "96-119", f"{ENV_BIN}/vllm", "serve", MODEL, "--port", str(VPORT), "--max-model-len", "32768",
                       "--gpu-memory-utilization", "0.85", "--enforce-eager", "--dtype", "float16", "--kv-transfer-config", json.dumps(kv),
                       "--enable-prompt-tokens-details", "--disable-uvicorn-access-log"],
                      stdout=open(f"{out}/{tag}-server.log", "w"), stderr=subprocess.STDOUT, env=env, start_new_session=True)
for _ in range(1200):
    time.sleep(1)
    if vl.poll() is not None: os.killpg(lm.pid, signal.SIGINT); sys.exit(f"{tag}: vllm exited rc={vl.returncode}")
    try:
        if urllib.request.urlopen(f"http://127.0.0.1:{VPORT}/health", timeout=2).status == 200: break
    except Exception: pass
mark("vllm_ready")
samp = subprocess.Popen(["taskset", "-c", "95", f"{ENV_BIN}/python", f"{HERE}/pcie_sampler.py"], stdout=open(f"{out}/{tag}-pcie.txt", "w"), stderr=subprocess.STDOUT)
stat = subprocess.Popen(["bash", "-c", f"while true; do echo \"T $(date +%s.%N)\"; curl -s http://127.0.0.1:{HPORT}/status; echo; sleep 5; done"],
                        stdout=open(f"{out}/{tag}-status.txt", "w"), stderr=subprocess.DEVNULL, start_new_session=True)
ck = gate = None
if ckpt:
    f = ckpt.split(":"); S, P, mode = f[0], f[1], f[2]; rate = f[3] if len(f) > 3 else "0"
    if mode == "kvprio": gate = subprocess.Popen(["taskset", "-c", "94", f"{ENV_BIN}/python", f"{HERE}/kvprio_gate.py", "1.0", "5"], stdout=open(f"{out}/{tag}-gate.txt", "w"), stderr=subprocess.STDOUT); time.sleep(2)
    ck = subprocess.Popen([f"{HERE}/ckpt_cxl", S, P, mode, rate, "1"], stdout=open(f"{out}/{tag}-ckpt.txt", "w"), stderr=subprocess.STDOUT)
    time.sleep(3 + float(S) / 10)                            # the source buffer is filled and copied once before the first burst
    mark("ckpt_started", ckpt)
time.sleep(2); mark("serve_start")
rc = subprocess.run(["taskset", "-c", "124-126", f"{ENV_BIN}/python", f"{HERE}/serve_replay.py", f"http://127.0.0.1:{VPORT}", MODEL, trace, t0, t1, speed],
                    stdout=open(f"{out}/{tag}-client.txt", "w"), stderr=subprocess.STDOUT).returncode
mark("serve_end", f"client_rc={rc}"); time.sleep(5)
samp.send_signal(signal.SIGTERM); samp.wait(); os.killpg(stat.pid, signal.SIGTERM)
for p in (ck, gate):
    if p: p.send_signal(signal.SIGTERM); p.wait()
for p in (vl, lm):
    os.killpg(p.pid, signal.SIGINT)
    try: p.wait(timeout=120)
    except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); p.wait()
mark("done"); meta.close(); print(f"{tag}: client rc={rc}", flush=True)
