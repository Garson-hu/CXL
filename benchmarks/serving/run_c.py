#!/usr/bin/env python3
"""Experiment C of the CXL-vs-NVMe study (2026-11-12): equal-hit comparison. Every tier serves the SAME request sequence against the
SAME pre-populated prefixes, so the hit lengths and the retrieved bytes are identical by construction and only the medium (and its
software path) differs; nothing depends on what an online cache happened to keep.

  populate   the GPU-flush fillers first (fill x 16,320 tokens; they also fill the DRAM part of a small hybrid L1, so that the pool
             then lands on Device-DAX), then the pool: `pool` prompts, lengths cycling over Ls, each stored by one cold request;
             wait until LMCache's store controller is idle (all L2 stores done, skip_l1 removals applied)
  pass       for each arrival rate in `rates` and each repetition: flush the GPU prefix cache with the fillers, then send one request
             per pool prompt (seeded shuffle) = the pool prompt + a fresh `suffix`-token tail, `out_tokens` output tokens, Poisson
             arrivals at the rate (seeded: the same instants for every tier). Each pool prompt is used once per pass and the GPU was
             flushed before it, so a hit can only come from the host tier under test; the tail (< one chunk) stores nothing new.
Checks made afterwards (analyze_c.py): cached_tokens and retrieved bytes per request equal across tiers; no GPU-prefix hit; the
chunks' medium (DRAM / Device-DAX letters, L2 load tasks) is the intended one for every request.
usage: run_c.py <out> <tag> [pool=48] [Ls=2048,4096,8192,16384] [rates=0.5,2,4,8] [reps=2] [out_tokens=64] [suffix=64] [fill=8] [Cfg key=value ...]"""
import asyncio, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_env import Cfg, ServingEnv, parse_kv
from client import Client, prompt

out, tag = sys.argv[1:3]; kv = dict(a.split("=", 1) for a in sys.argv[3:])
NPOOL = int(kv.pop("pool", "48")); LS = [int(x) for x in kv.pop("Ls", "2048,4096,8192,16384").split(",")]
RATES = [float(x) for x in kv.pop("rates", "0.5,2,4,8").split(",")]; REPS = int(kv.pop("reps", "2"))
OUT = int(kv.pop("out_tokens", "64")); SUF = int(kv.pop("suffix", "64")); NFILL = int(kv.pop("fill", "8"))
cfg = parse_kv([f"{k}={v}" for k, v in kv.items()], Cfg(out=out, tag=tag, l1_gb=80.0, enforce_eager=False))
POOL = [(600_000 + i, LS[i % len(LS)]) for i in range(NPOOL)]; FILL = [prompt(20_000 + i, 16320) for i in range(NFILL)]
env = ServingEnv(cfg).start()

async def settle(timeout=300.0):
    if cfg.tier == "none": return
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        sc = ((env.status() or {}).get("storage_manager") or {}).get("store_controller") or {}
        if sc and not sc.get("pending_keys_count") and not sc.get("in_flight_task_count"): return
        await asyncio.sleep(0.05)
    env.mark("settle_timeout")

async def flush(cl, name):
    for i, f in enumerate(FILL): await cl.one(f"{tag}-{name}-flush{i}", f, case="flush", L=16320, max_tokens=1, grp="fill")
    await settle(); await asyncio.sleep(0.5)

async def main():
    async with Client(env.url(), cfg.model, env.f("client.jsonl"), concurrency_limit=1024) as cl:
        env.mark("warmup"); await cl.sequential([dict(rid=f"{tag}-warm{i}", tokens=prompt(10_000 + i, 1024), case="warm", max_tokens=4) for i in range(3)])
        env.mark("fill_store")
        for i, f in enumerate(FILL): await cl.one(f"{tag}-fill{i}-store", f, case="fill_store", L=16320, max_tokens=1, grp="fill")
        await settle(); env.mark("populate")
        for i, (seed, L) in enumerate(POOL): await cl.one(f"{tag}-pop-{i}-L{L}", prompt(seed, L), case="populate", L=L, max_tokens=1)
        await settle(); env.mark("populated")
        n = 0
        for rate in RATES:
            for rep in range(REPS):
                name = f"r{rate:g}-p{rep}"; await flush(cl, name)
                rng = random.Random(1000 * rep + int(rate * 100)); order = list(range(NPOOL)); rng.shuffle(order)
                reqs = []
                for j, i in enumerate(order):
                    seed, L = POOL[i]; n += 1
                    reqs.append(dict(rid=f"{tag}-{name}-{j}-pool{i}-L{L}", tokens=prompt(seed, L) + prompt(3_000_000 + n, SUF), case="hit", L=L, rep=rep, grp=name, max_tokens=OUT, extra={"rate": rate, "pool": i}))
                env.mark("pass_start", f"rate={rate:g} rep={rep} n={len(reqs)}")
                await cl.open_loop(reqs, rate, seed=7 + rep)
                env.mark("pass_end", f"rate={rate:g} rep={rep}")
                print(f"[{time.strftime('%H:%M:%S')}] rate {rate:g} pass {rep} done", flush=True)
        env.mark("bench_end")

try: asyncio.run(main())
finally: time.sleep(2); env.stop()
