#!/usr/bin/env python3
"""Experiment A (2026-11-04): single-request KV retrieval cost. One server configuration per run (tier dram | ssd | none);
for each prefix length L and repetition, with fresh pseudo-random prompts:
  cold   the prompt has never been seen: full prefill (recompute); its KV is stored to LMCache during the prefill
  gpu    the same prompt again at once: vLLM's own GPU prefix cache serves it (HBM hit)
  flush  the filler prompts (n_fill x fill_len tokens, the same ones every time, so LMCache hits after their first store)
         pushed through the GPU so that the GPU prefix cache no longer holds the measured prompt (recorded, not scored)
  host   the same prompt after the flush: LMCache serves it (DRAM L1, or the fs L2 on the NVMe in the ssd tier)
Then the request's time line is reconstructed from the client, the vLLM hook and the LMCache event bus (analyze_a.py).
usage: run_a.py <out> <tag> [tier=dram] [model=Qwen/Qwen2.5-3B-Instruct-AWQ] [Ls=256,512,1024,2048,4096,8192] [reps=5]
                [gpu_blocks=3072] [l1_gb=20] [fill_len=16320] [n_fill=4] [max_model_len=32768] [other Cfg key=value]"""
import asyncio, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_env import Cfg, ServingEnv, parse_kv
from client import Client, prompt

out, tag = sys.argv[1:3]; kv = dict(a.split("=", 1) for a in sys.argv[3:])
Ls = [int(x) for x in kv.pop("Ls", "256,512,1024,2048,4096,8192").split(",")]; REPS = int(kv.pop("reps", "5"))
FILL_LEN = int(kv.pop("fill_len", "16320")); N_FILL = int(kv.pop("n_fill", "4"))
cfg = parse_kv([f"{k}={v}" for k, v in kv.items()], Cfg(out=out, tag=tag, gpu_blocks=3072, l1_gb=20.0))
env = ServingEnv(cfg).start()

async def settle(timeout=30.0):
    """2026-11-12: wait until LMCache's store controller is idle (no key waiting for, or in, an L2 store). Without it the immediate
    repetition of a prompt read-locks chunks whose L2 store is still running; with --l2-store-policy skip_l1 those chunks are then
    never removed from L1, and the later "host" hit is served partly from DRAM instead of the L2 tier (seen 2026-11-12, Python fs
    adapter, 8,192-token prompts: 16 of 32 chunks). No-op without an L2 tier (the controller is idle at once)."""
    if cfg.tier == "none": return
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        s = env.status() or {}; sc = (s.get("storage_manager") or {}).get("store_controller") or {}
        if sc and not sc.get("pending_keys_count") and not sc.get("in_flight_task_count"): return
        await asyncio.sleep(0.02)
    env.mark("settle_timeout")

async def main():
    async with Client(env.url(), cfg.model, env.f("client.jsonl")) as cl:
        env.mark("warmup_start")
        await cl.sequential([dict(rid=f"{tag}-warm{i}", tokens=prompt(10_000 + i, 1024), case="warm") for i in range(2)] + [dict(rid=f"{tag}-warm2", tokens=prompt(10_000, 1024), case="warm")])
        fillers = [prompt(20_000 + i, FILL_LEN) for i in range(N_FILL)]
        env.mark("fill_store_start")
        await cl.sequential([dict(rid=f"{tag}-fill{i}-store", tokens=f, case="fill_store", grp="fill") for i, f in enumerate(fillers)])
        await settle(120.0)
        n = 0
        for rep in range(REPS):
            for L in Ls:
                seed = 1_000_000 * (rep + 1) + L; p = prompt(seed, L); base = f"{tag}-r{rep}-L{L}"
                env.mark("case", f"rep={rep} L={L} start")
                await cl.one(f"{base}-cold", p, case="cold", L=L, rep=rep)
                await settle(); env.mark("settled", f"rep={rep} L={L}")
                await cl.one(f"{base}-gpu", p, case="gpu", L=L, rep=rep)
                for i, f in enumerate(fillers):
                    await cl.one(f"{base}-flush{i}", f, case="flush", L=L, rep=rep, grp="fill")
                await asyncio.sleep(0.3)
                await cl.one(f"{base}-host", p, case="host", L=L, rep=rep)
                n += 1
                print(f"[{time.strftime('%H:%M:%S')}] rep {rep} L {L} done ({n}/{REPS * len(Ls)})", flush=True)
    env.mark("bench_end")

try:
    asyncio.run(main())
finally:
    time.sleep(2); env.stop()
