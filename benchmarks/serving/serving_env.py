#!/usr/bin/env python3
"""Serving environment for the 2026-11-04 serving-scheduling study: LMCache 0.5.5 multi-process server + vLLM 0.31.0
OpenAI server on c28's RTX 4060 Ti, with the logging-only instrumentation and the samplers. Same process layout as
benchmarks/lmcache/run_2a.py / misscost_run.py (vLLM on CCD 6-7, LMCache on the tail of CCD 7, samplers on their own cpu).

Tiers (cfg.tier):  dram  L1 = pinned host DRAM of l1_gb GB
                   ssd   L1 = l1_gb GB DRAM staging + fs L2 adapter on ssd_path with --l2-store-policy skip_l1 (keys leave
                         L1 after the L2 store, so a later hit is a disk read into L1 and then a GPU transfer); ssd_odirect
                         (default true) opens the files with O_DIRECT, otherwise the page cache (755 GiB of DRAM) serves the reads
                   dax   L1 on /dev/dax1.0 (CXL devdax, l1_gb GB) -- BLOCKED since 2026-10-18 (root 0600), kept for the record
                   none  no LMCache at all (vLLM alone: recompute-only reference)
Files written to <out>/<tag>-*: lmcache.log, server.log (vLLM), kvevents.jsonl (LMCache event bus), vllmevt.req.<pid>.jsonl /
vllmevt.step.<pid>.jsonl (vLLM hooks), gpu.txt (gpu_sampler), cpu.txt (cpu_sampler), status.txt (LMCache /status every 5 s),
meta.txt (M <name> <mono_ns> wall=<s> ...).
usage (manual): serving_env.py start <out> <tag> [key=value ...]   then serving_env.py stop <out> <tag>
Library: env = ServingEnv(Cfg(...)); env.start(); ...; env.stop()"""
import dataclasses, json, os, signal, subprocess, sys, threading, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
ENV_BIN = "/mnt/local/ghu4/envs/lmcache/bin"
BASE_ENV = dict(HF_HOME="/mnt/local/ghu4/hf", XDG_CACHE_HOME="/mnt/local/ghu4/cache", TMPDIR="/mnt/local/ghu4/tmp",
                VLLM_CACHE_ROOT="/mnt/local/ghu4/cache/vllm", PYTHONHASHSEED="0", LMCACHE_DISABLE_BANNER="1", HF_HUB_OFFLINE="1")

@dataclasses.dataclass
class Cfg:
    out: str; tag: str
    model: str = "Qwen/Qwen2.5-3B-Instruct-AWQ"
    tier: str = "dram"
    l1_gb: float = 40.0
    ssd_path: str = "/mnt/local/ghu4/kvl2"
    keep_ssd: bool = False          # keep the run's fs L2 directory after stop() (default: delete it)
    ssd_odirect: bool = True      # O_DIRECT file reads/writes in the fs adapter (otherwise the page cache serves the "SSD" hits)
    dax_path: str = "/dev/dax1.0"
    chunk: int = 256
    gpu_workers: int = 1
    cpu_workers: int = 1
    transfer_mode: str = "lmcache_driven"
    eager_prefetch: bool = False
    l2_prefetch_max_in_flight: int = 8
    watermark: float = 0.8
    max_model_len: int = 32768
    max_num_seqs: int = 16
    max_batched: int = 0            # 0 = vLLM default
    long_prefill_threshold: int = 0 # 0 = vLLM default
    gpu_blocks: int = 0             # 0 = all the memory allows
    gpu_util: float = 0.85
    enforce_eager: bool = True
    sched_policy: str = "fcfs"
    async_sched: str = ""           # "" = default, "on" / "off"
    vllm_cpus: str = "96-119"
    lm_cpus: str = "120-127"
    gpu_sampler_cpu: str = "95"
    cpu_sampler_cpu: str = "94"
    hooks: bool = True
    samplers: bool = True
    vport: int = 8100; mpport: int = 5555; hport: int = 8200
    extra_vllm: str = ""            # extra vllm serve args, space separated
    extra_lm: str = ""              # extra lmcache server args

def parse_kv(args, cfg):
    for a in args:
        k, v = a.split("=", 1); f = {x.name: x for x in dataclasses.fields(Cfg)}[k]
        setattr(cfg, k, (v.lower() in ("1", "true", "yes")) if f.type is bool else f.type(v))
    return cfg

class ServingEnv:
    def __init__(self, cfg: Cfg):
        self.c = cfg; self.p = {}; self.threads = []; self.stop_evt = threading.Event()
        os.makedirs(cfg.out, exist_ok=True); self.meta = open(f"{cfg.out}/{cfg.tag}-meta.txt", "a")
    def f(self, suffix): return f"{self.c.out}/{self.c.tag}-{suffix}"
    def mark(self, name, extra=""):
        self.meta.write(f"M {name} {time.monotonic_ns()} wall={time.time():.6f} {extra}\n"); self.meta.flush()
    def url(self): return f"http://127.0.0.1:{self.c.vport}"

    def _wait(self, url, proc, name, timeout):
        for _ in range(timeout):
            time.sleep(1)
            if proc.poll() is not None: raise RuntimeError(f"{name} exited rc={proc.returncode} (see {self.c.out}/{self.c.tag}-*.log)")
            try:
                if urllib.request.urlopen(url, timeout=2).status == 200: return
            except Exception: pass
        raise RuntimeError(f"{name} not healthy after {timeout} s")

    def start(self):
        c = self.c; env = dict(os.environ, **BASE_ENV)
        self.mark("config", json.dumps(dataclasses.asdict(c)))
        if c.tier != "none":
            srv = [f"{ENV_BIN}/lmcache", "server", "--host", "127.0.0.1", "--port", str(c.mpport), "--http-host", "127.0.0.1", "--http-port", str(c.hport),
                   "--chunk-size", str(c.chunk), "--eviction-policy", "LRU", "--eviction-trigger-watermark", f"{c.watermark:g}",
                   "--max-gpu-workers", str(c.gpu_workers), "--max-cpu-workers", str(c.cpu_workers), "--supported-transfer-mode", c.transfer_mode,
                   "--l2-prefetch-max-in-flight", str(c.l2_prefetch_max_in_flight), "--l1-size-gb", f"{c.l1_gb:g}"]
            if c.tier == "dax": srv += ["--l1-devdax-path", c.dax_path, "--no-l1-use-lazy", "--shm-name", ""]
            elif c.tier == "ssd":
                # one directory per run: the fs L2 is persistent, and a second run with the same prompts would otherwise find them on disk
                self.ssd_dir = os.path.join(c.ssd_path, c.tag); os.makedirs(self.ssd_dir, exist_ok=True)
                srv += ["--l2-adapter", json.dumps({"type": "fs", "base_path": self.ssd_dir, "use_odirect": bool(c.ssd_odirect)}), "--l2-store-policy", "skip_l1"]
            elif c.tier != "dram": raise ValueError(c.tier)
            if c.extra_lm: srv += c.extra_lm.split()
            lm_env = dict(env)
            if c.hooks: lm_env.update(PYTHONPATH=f"{REPO}/benchmarks/agent/kvevt", KVEVT_OUT=self.f("kvevents.jsonl"))
            self.p["lmcache"] = subprocess.Popen(["taskset", "-c", c.lm_cpus] + srv, stdout=open(self.f("lmcache.log"), "w"), stderr=subprocess.STDOUT, env=lm_env, start_new_session=True)
            self._wait(f"http://127.0.0.1:{c.hport}/healthcheck", self.p["lmcache"], "lmcache server", 600); self.mark("lmcache_ready")
        vl = [f"{ENV_BIN}/vllm", "serve", c.model, "--port", str(c.vport), "--max-model-len", str(c.max_model_len), "--max-num-seqs", str(c.max_num_seqs),
              "--gpu-memory-utilization", f"{c.gpu_util:g}", "--dtype", "float16", "--enable-prompt-tokens-details", "--disable-uvicorn-access-log",
              "--scheduling-policy", c.sched_policy]
        if c.enforce_eager: vl.append("--enforce-eager")
        if c.gpu_blocks: vl += ["--num-gpu-blocks-override", str(c.gpu_blocks)]
        if c.max_batched: vl += ["--max-num-batched-tokens", str(c.max_batched)]
        if c.long_prefill_threshold: vl += ["--long-prefill-token-threshold", str(c.long_prefill_threshold)]
        if c.async_sched == "on": vl.append("--async-scheduling")
        elif c.async_sched == "off": vl.append("--no-async-scheduling")
        if c.tier != "none":
            kv = {"kv_connector": "LMCacheMPConnector", "kv_connector_module_path": "lmcache.integration.vllm.lmcache_mp_connector", "kv_role": "kv_both",
                  "kv_connector_extra_config": {"lmcache.mp.host": "tcp://127.0.0.1", "lmcache.mp.port": c.mpport, "lmcache.mp.eager_prefetch": bool(c.eager_prefetch)}}
            vl += ["--kv-transfer-config", json.dumps(kv)]
        if c.extra_vllm: vl += c.extra_vllm.split()
        v_env = dict(env)
        if c.hooks: v_env.update(PYTHONPATH=f"{HERE}/vllmevt", VLLMEVT_OUT=self.f("vllmevt"))
        self.p["vllm"] = subprocess.Popen(["taskset", "-c", c.vllm_cpus] + vl, stdout=open(self.f("server.log"), "w"), stderr=subprocess.STDOUT, env=v_env, start_new_session=True)
        self._wait(f"{self.url()}/health", self.p["vllm"], "vllm", 1500); self.mark("vllm_ready")
        if c.samplers:
            pids = [f"pid:vllm={self.p['vllm'].pid}"]
            if "lmcache" in self.p: pids.append(f"pid:lmcache={self.p['lmcache'].pid}")
            for child in self._children(self.p["vllm"].pid): pids.append(f"pid:vllm_child{child}={child}")
            self.p["gpu"] = subprocess.Popen(["taskset", "-c", c.gpu_sampler_cpu, f"{ENV_BIN}/python", f"{HERE}/gpu_sampler.py", "0", "50"], stdout=open(self.f("gpu.txt"), "w"), stderr=subprocess.STDOUT, env=env)
            self.p["cpu"] = subprocess.Popen(["taskset", "-c", c.cpu_sampler_cpu, f"{ENV_BIN}/python", f"{HERE}/cpu_sampler.py", "100", f"vllm={c.vllm_cpus}", f"lmcache={c.lm_cpus}"] + pids,
                                             stdout=open(self.f("cpu.txt"), "w"), stderr=subprocess.STDOUT, env=env)
            if c.tier != "none":
                t = threading.Thread(target=self._status_loop, daemon=True); t.start(); self.threads.append(t)
        self.mark("env_ready"); return self

    def _children(self, pid):
        try: return [int(x) for x in subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True).stdout.split()]
        except Exception: return []

    def _status_loop(self):
        f = open(self.f("status.txt"), "a")
        while not self.stop_evt.wait(5.0):
            try:
                s = urllib.request.urlopen(f"http://127.0.0.1:{self.c.hport}/status", timeout=3).read().decode()
                f.write(f"S {time.monotonic_ns()} {s.strip()}\n"); f.flush()
            except Exception as e:
                f.write(f"# {time.monotonic_ns()} status error {e!r}\n"); f.flush()
        f.close()

    def status(self):
        try: return json.loads(urllib.request.urlopen(f"http://127.0.0.1:{self.c.hport}/status", timeout=3).read().decode())
        except Exception: return None

    def stop(self):
        self.mark("stop"); self.stop_evt.set()
        for name in ("gpu", "cpu"):
            if name in self.p:
                self.p[name].send_signal(signal.SIGTERM)
                try: self.p[name].wait(timeout=10)
                except subprocess.TimeoutExpired: self.p[name].kill()
        for name in ("vllm", "lmcache"):
            if name in self.p:
                try: os.killpg(self.p[name].pid, signal.SIGINT)
                except ProcessLookupError: pass
                try: self.p[name].wait(timeout=120)
                except subprocess.TimeoutExpired:
                    os.killpg(self.p[name].pid, signal.SIGKILL); self.p[name].wait()
        if getattr(self, "ssd_dir", None) and not self.c.keep_ssd:
            import shutil; shutil.rmtree(self.ssd_dir, ignore_errors=True)
        self.mark("stopped"); self.meta.close()

if __name__ == "__main__":
    mode, out, tag = sys.argv[1:4]; cfg = parse_kv(sys.argv[4:], Cfg(out=out, tag=tag))
    if mode == "start":
        env = ServingEnv(cfg).start(); json.dump({k: p.pid for k, p in env.p.items()}, open(env.f("pids.json"), "w")); print("ready", env.url())
    elif mode == "stop":
        pids = json.load(open(f"{out}/{tag}-pids.json"))
        for name in ("gpu", "cpu"):
            if name in pids:
                try: os.kill(pids[name], signal.SIGTERM)
                except ProcessLookupError: pass
        for name in ("vllm", "lmcache"):
            if name in pids:
                try: os.killpg(pids[name], signal.SIGINT)
                except ProcessLookupError: pass
        print("stop signals sent")
