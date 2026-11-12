#!/usr/bin/env python3
"""Experiment E (2026-11-04): concurrent KV retrieval. A pool of host-resident prompts (pre-populated, GPU cache flushed)
is requested k at a time; per request the LMCache retrieve instants / bytes and vLLM's instants are recorded, and the GPU
sampler's 5 ms PCIe RX bins give the aggregate host-to-GPU bandwidth. One server configuration per invocation
(gpu_workers 1 / 4, transfer mode, ...).
Scenarios:  e1  k in KS simultaneous host hits of L tokens, each L in LS, `reps` bursts per (k, L) (flush before each)
            e2  k host hits of L_HIT tokens + k cold prompts of L_COLD tokens at once (transfer while the GPU computes)
            e3  k host hits with 1 output token vs 64 output tokens (loads beside decode steps)
usage: run_e.py <out> <tag> [ks=1,2,4,8,16] [Ls=4096,8192] [reps=4] [scenarios=e1,e2,e3] [fill_first=false] [Cfg key=value ...]"""
import asyncio, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_env import Cfg, ServingEnv, parse_kv
from client import Client, prompt

out, tag = sys.argv[1:3]; kv = dict(a.split("=", 1) for a in sys.argv[3:])
KS = [int(x) for x in kv.pop("ks", "1,2,4,8,16").split(",")]; LS = [int(x) for x in kv.pop("Ls", "4096,8192").split(",")]
REPS = int(kv.pop("reps", "4")); SCEN = kv.pop("scenarios", "e1,e2,e3").split(",")
FILL_FIRST = kv.pop("fill_first", "false").lower() in ("1", "true", "yes")   # 2026-11-12: store the flush fillers before the pool (a small hybrid L1 then holds the pool on Device-DAX)
cfg = parse_kv([f"{k}={v}" for k, v in kv.items()], Cfg(out=out, tag=tag, l1_gb=40.0, enforce_eager=False, max_num_seqs=32))
FILL = [prompt(20_000 + i, 16320) for i in range(8)]
env = ServingEnv(cfg).start()
seed = [700_000]
def fresh(L): seed[0] += 1; return prompt(seed[0], L)

async def settle(timeout=300.0):
    """2026-11-12: wait until LMCache's store controller is idle (L2 stores done, skip_l1 removals applied); see run_a.py"""
    if cfg.tier == "none": return
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        sc = ((env.status() or {}).get("storage_manager") or {}).get("store_controller") or {}
        if sc and not sc.get("pending_keys_count") and not sc.get("in_flight_task_count"): return
        await asyncio.sleep(0.05)
    env.mark("settle_timeout")

async def flush(cl, name):
    for i, f in enumerate(FILL): await cl.one(f"{tag}-{name}-flush{i}", f, case="flush", L=16320, max_tokens=1)
    await settle(); await asyncio.sleep(0.5)

async def main():
    async with Client(env.url(), cfg.model, env.f("client.jsonl")) as cl:
        env.mark("warmup"); await cl.sequential([dict(rid=f"{tag}-warm{i}", tokens=prompt(10_000 + i, 1024), case="warm", max_tokens=4) for i in range(3)])
        pool = {L: [prompt(800_000 + 100 * L + i, L) for i in range(max(max(KS), 8))] for L in LS}
        if FILL_FIRST:
            env.mark("fill_store")
            for i, f in enumerate(FILL): await cl.one(f"{tag}-fill{i}-store", f, case="fill_store", L=16320, max_tokens=1)
            await settle()
        env.mark("populate")
        for L in LS:
            for i, p in enumerate(pool[L]): await cl.one(f"{tag}-pop-L{L}-{i}", p, case="populate", L=L, max_tokens=1)
        await settle(); env.mark("populated")
        if "e1" in SCEN:
            for L in LS:
                for k in KS:
                    env.mark("e1", f"k={k} L={L}")
                    for rep in range(REPS):
                        await flush(cl, f"e1-k{k}-L{L}-r{rep}")
                        await cl.burst([dict(rid=f"{tag}-e1-k{k}-L{L}-r{rep}-{i}", tokens=pool[L][i], case="host", L=L, rep=rep, grp=f"e1-k{k}-L{L}", max_tokens=4) for i in range(k)])
                        await asyncio.sleep(0.5)
        if "e2" in SCEN:
            L = LS[-1]
            for k in KS:
                if k > 8: continue
                env.mark("e2", f"k={k} L={L}")
                for rep in range(REPS):
                    await flush(cl, f"e2-k{k}-r{rep}")
                    reqs = [dict(rid=f"{tag}-e2-k{k}-r{rep}-h{i}", tokens=pool[L][i], case="host", L=L, rep=rep, grp=f"e2-k{k}", max_tokens=4) for i in range(k)]
                    reqs += [dict(rid=f"{tag}-e2-k{k}-r{rep}-c{i}", tokens=fresh(4096), case="cold", L=4096, rep=rep, grp=f"e2-k{k}", max_tokens=4) for i in range(k)]
                    await cl.burst(reqs); await asyncio.sleep(0.5)
        if "e3" in SCEN:
            L = LS[-1]
            for k in (4, 8):
                for o in (1, 64):
                    env.mark("e3", f"k={k} out={o}")
                    for rep in range(REPS):
                        await flush(cl, f"e3-k{k}-o{o}-r{rep}")
                        await cl.burst([dict(rid=f"{tag}-e3-k{k}-o{o}-r{rep}-{i}", tokens=pool[L][i], case="host", L=L, rep=rep, grp=f"e3-k{k}-o{o}", max_tokens=o) for i in range(k)], spacing_ms=20.0)
                        await asyncio.sleep(0.5)
        env.mark("bench_end")

try: asyncio.run(main())
finally: time.sleep(2); env.stop()
