#!/usr/bin/env python3
"""Idle-gap control for Experiment A (2026-11-04): with NO instrumentation in the server processes (hooks off, samplers
off), how does the TTFT of a host hit and of a GPU-prefix hit depend on how long the server was idle before the request?
For each gap in GAPS seconds and each repetition: the prompt is stored (cold), the GPU cache flushed (fillers), the client
sleeps `gap`, then sends the host hit; then sleeps `gap` again and sends the same prompt (GPU hit). After the last
repetition of the longest gap, one `nvidia-smi` query records the GPU's PCIe link generation, SM clock and P-state after
`gap` seconds of idleness (the query itself wakes the GPU, so it is taken once, after the measurements).
usage: run_a_idle.py <out> <tag> [L=4096] [gaps=0,0.05,0.2,1,3] [reps=6] [Cfg key=value ...]"""
import asyncio, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_env import Cfg, ServingEnv, parse_kv
from client import Client, prompt

out, tag = sys.argv[1:3]; kv = dict(a.split("=", 1) for a in sys.argv[3:])
L = int(kv.pop("L", "4096")); GAPS = [float(x) for x in kv.pop("gaps", "0,0.05,0.2,1,3").split(",")]; REPS = int(kv.pop("reps", "6"))
cfg = parse_kv([f"{k}={v}" for k, v in kv.items()], Cfg(out=out, tag=tag, gpu_blocks=3072, l1_gb=20.0, enforce_eager=False, hooks=False, samplers=False))
env = ServingEnv(cfg).start()
FILL = [prompt(20_000 + i, 16320) for i in range(4)]

async def main():
    async with Client(env.url(), cfg.model, env.f("client.jsonl")) as cl:
        await cl.sequential([dict(rid=f"{tag}-warm{i}", tokens=prompt(10_000 + i, 1024), case="warm") for i in range(2)])
        await cl.sequential([dict(rid=f"{tag}-fill{i}", tokens=f, case="fill_store", grp="fill") for i, f in enumerate(FILL)])
        for gap in GAPS:
            for rep in range(REPS):
                p = prompt(3_000_000 + int(gap * 1000) * 100 + rep, L); base = f"{tag}-g{gap:g}-r{rep}"
                await cl.one(f"{base}-cold", p, case="cold", L=L, rep=rep, grp=f"gap{gap:g}")
                for i, f in enumerate(FILL): await cl.one(f"{base}-flush{i}", f, case="flush", L=16320, rep=rep, grp="fill")
                await asyncio.sleep(gap); await cl.one(f"{base}-host", p, case="host", L=L, rep=rep, grp=f"gap{gap:g}", extra={"gap_s": gap})
                await asyncio.sleep(gap); await cl.one(f"{base}-gpu", p, case="gpu", L=L, rep=rep, grp=f"gap{gap:g}", extra={"gap_s": gap})
            print(f"[{time.strftime('%H:%M:%S')}] gap {gap} done", flush=True)
        await asyncio.sleep(GAPS[-1])
        q = subprocess.run(["nvidia-smi", "--query-gpu=pcie.link.gen.current,pcie.link.width.current,clocks.sm,clocks.mem,pstate,power.draw", "--format=csv"], capture_output=True, text=True).stdout
        open(env.f("gpu-state-after-idle.txt"), "w").write(f"after {GAPS[-1]} s idle:\n{q}")
        env.mark("bench_end")

try: asyncio.run(main())
finally: time.sleep(2); env.stop()
