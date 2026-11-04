#!/usr/bin/env python3
"""Experiment B (2026-11-04): concurrent serving and scheduling behaviour with controlled request mixes, one server
configuration per invocation (the chain script runs the configurations one after the other with the SAME request
sequences: the seeds fix every prompt, every type and every arrival instant).

Request types: host  a prompt of the pre-populated pool (stored in LMCache during the populate phase and evicted from
                     the GPU prefix cache by the time it is re-used; the tier actually served is classified after the
                     run from vLLM's cached_tokens and LMCache's retrieve bytes)
               cold  a never-seen prompt (full prefill)
Scenarios (each request id = <tag>-<scenario>-<index>-<type>-L<len>; scenario boundaries in <tag>-meta.txt):
  s0  the four-request example: A = 8k host hit, B = 1k GPU hit (sent alone just before), C = 4k cold, D = 4k host hit,
      sent 5 ms apart in the orders ABCD / DCBA / CADB, `reps` times each
  s1  closed loop, concurrency c in CONC: the same 64-request mixed sequence (50 % host / 50 % cold; L in 1k/2k/4k/8k)
  s2  open loop, Poisson arrivals at RATES req/s over the same 96-request mixed sequence (seeded exponential gaps)
  s3  bursts of k in BURSTS simultaneous mixed requests, 4 bursts per k, 4 s apart
  s4  (Experiment F) open loop at F_RATE req/s, 48 requests, hit share in SHARES x length class short (1k / 2k) or long (8k)
Every request asks for OUT output tokens (ignore_eos). Pool: 64 prompts (16 per length 1k/2k/4k/8k).
usage: run_b.py <out> <tag> [scenarios=s0,s1,s2,s3] [conc=1,2,4,8,16] [rates=0.5,1,2,4] [bursts=4,8,16] [reps=5] [out_tokens=32] [f_rate=2] [shares=0,0.25,0.5,0.75,1]
                [prio=none|hits_first|cold_first] [Cfg key=value ...]   (e.g. eager_prefetch=true gpu_workers=4 sched_policy=priority)"""
import asyncio, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_env import Cfg, ServingEnv, parse_kv
from client import Client, prompt

out, tag = sys.argv[1:3]; kv = dict(a.split("=", 1) for a in sys.argv[3:])
SCEN = kv.pop("scenarios", "s0,s1,s2,s3").split(","); CONC = [int(x) for x in kv.pop("conc", "1,2,4,8,16").split(",")]
RATES = [float(x) for x in kv.pop("rates", "0.5,1,2,4").split(",")]; BURSTS = [int(x) for x in kv.pop("bursts", "4,8,16").split(",")]
REPS = int(kv.pop("reps", "5")); OUT = int(kv.pop("out_tokens", "32")); PRIO = kv.pop("prio", "none")
F_RATE = float(kv.pop("f_rate", "2")); SHARES = [float(x) for x in kv.pop("shares", "0,0.25,0.5,0.75,1").split(",")]
cfg = parse_kv([f"{k}={v}" for k, v in kv.items()], Cfg(out=out, tag=tag, l1_gb=40.0, enforce_eager=False))
if PRIO != "none": cfg.sched_policy = "priority"
LENS = [1024, 2048, 4096, 8192]; POOL = [(500_000 + i, LENS[i % 4]) for i in range(64)]     # (seed, L)
FILL = [prompt(20_000 + i, 16320) for i in range(8)]                                         # 8 x 16k = 130k tokens > the GPU KV
env = ServingEnv(cfg).start()
cold_seed = [900_000]
def cold_prompt(L): cold_seed[0] += 1; return prompt(cold_seed[0], L)
def prio(t): return None if PRIO == "none" else ({"host": 0, "gpu": 0, "cold": 1} if PRIO == "hits_first" else {"host": 1, "gpu": 1, "cold": 0})[t]
def req(rid, t, L, p, **k): return dict(rid=rid, tokens=p, case=t, L=L, max_tokens=OUT, priority=prio(t), **k)

def mixed_sequence(n, seed):
    """n requests: alternating pool hits (random pool entry, no immediate repeat) and cold prompts, lengths from LENS"""
    rng = random.Random(seed); seq = []; last = -1
    for i in range(n):
        L = rng.choice(LENS)
        if i % 2 == 0:
            j = rng.randrange(64)
            while j == last: j = rng.randrange(64)
            last = j; s, Lp = POOL[j]; seq.append(("host", Lp, prompt(s, Lp)))
        else: seq.append(("cold", L, cold_prompt(L)))
    return seq

def share_sequence(n, seed, share, cls):
    """n requests with a `share` of pool hits (random pool entries of the length class), the rest cold prompts of the class"""
    rng = random.Random(seed); lens = [1024, 2048] if cls == "short" else [8192]; seq = []; last = -1
    cand = [j for j in range(64) if POOL[j][1] in lens]
    for i in range(n):
        if rng.random() < share:
            j = rng.choice(cand)
            while j == last and len(cand) > 1: j = rng.choice(cand)
            last = j; s_, Lp = POOL[j]; seq.append(("host", Lp, prompt(s_, Lp)))
        else:
            L = rng.choice(lens); seq.append(("cold", L, cold_prompt(L)))
    return seq

async def flush(cl, name):
    for i, f in enumerate(FILL): await cl.one(f"{tag}-{name}-flush{i}", f, case="flush", L=16320, max_tokens=1)
    await asyncio.sleep(0.5)

async def main():
    async with Client(env.url(), cfg.model, env.f("client.jsonl")) as cl:
        env.mark("warmup"); await cl.sequential([req(f"{tag}-warm{i}", "warm", 1024, prompt(10_000 + i, 1024)) for i in range(3)])
        env.mark("populate")
        for i, (s, L) in enumerate(POOL): await cl.one(f"{tag}-pop{i}", prompt(s, L), case="populate", L=L, max_tokens=1)
        await flush(cl, "pop")
        if "s0" in SCEN:
            env.mark("s0")
            A = ("host", 8192, prompt(POOL[3][0], 8192)); D = ("host", 4096, prompt(POOL[2][0], 4096)); Bp = prompt(600_000, 1024)
            orders = {"ABCD": "ABCD", "DCBA": "DCBA", "CADB": "CADB"}
            for rep in range(REPS):
                for oname, order in orders.items():
                    await flush(cl, f"s0-{oname}-r{rep}")
                    await cl.one(f"{tag}-s0-{oname}-r{rep}-Bwarm", Bp, case="gpuwarm", L=1024, max_tokens=1)   # B's prompt into the GPU cache
                    C = ("cold", 4096, cold_prompt(4096)); items = {"A": A, "B": ("gpu", 1024, Bp), "C": C, "D": D}
                    reqs = [req(f"{tag}-s0-{oname}-r{rep}-{ch}", items[ch][0], items[ch][1], items[ch][2], grp=f"s0-{oname}", rep=rep) for ch in order]
                    await cl.burst(reqs, spacing_ms=5.0); await asyncio.sleep(1.0)
        if "s1" in SCEN:
            for c in CONC:
                seq = mixed_sequence(64, 11)          # same types / lengths / pool entries at every level; the cold prompts are fresh (LMCache keeps the earlier ones)
                env.mark("s1", f"conc={c}"); await flush(cl, f"s1-c{c}")
                gen = (req(f"{tag}-s1-c{c}-{i}-{t}-L{L}", t, L, p, grp=f"s1-c{c}") for i, (t, L, p) in enumerate(seq))
                await cl.closed_loop(gen, c, len(seq)); await asyncio.sleep(1.0)
        if "s2" in SCEN:
            for r in RATES:
                seq = mixed_sequence(96, 12)
                env.mark("s2", f"rate={r}"); await flush(cl, f"s2-r{r:g}")
                reqs = [req(f"{tag}-s2-r{r:g}-{i}-{t}-L{L}", t, L, p, grp=f"s2-r{r:g}") for i, (t, L, p) in enumerate(seq)]
                await cl.open_loop(reqs, r, seed=100 + int(r * 10)); await asyncio.sleep(2.0)
        if "s3" in SCEN:
            for k in BURSTS:
                env.mark("s3", f"k={k}")
                for b in range(4):
                    seq = mixed_sequence(k, 1000 + 10 * k + b); await flush(cl, f"s3-k{k}-b{b}")
                    reqs = [req(f"{tag}-s3-k{k}-b{b}-{i}-{t}-L{L}", t, L, p, grp=f"s3-k{k}", rep=b) for i, (t, L, p) in enumerate(seq)]
                    await cl.burst(reqs); await asyncio.sleep(4.0)
        if "s4" in SCEN:
            for cls in ("short", "long"):
                for sh in SHARES:
                    seq = share_sequence(48, 4000 + int(sh * 100) + (0 if cls == "short" else 1), sh, cls)
                    env.mark("s4", f"share={sh:g} class={cls}"); await flush(cl, f"s4-{cls}-h{sh:g}")
                    reqs = [req(f"{tag}-s4-{cls}-h{sh:g}-{i}-{t}-L{L}", t, L, p, grp=f"s4-{cls}-h{sh:g}") for i, (t, L, p) in enumerate(seq)]
                    await cl.open_loop(reqs, F_RATE, seed=500 + int(sh * 100)); await asyncio.sleep(2.0)
        env.mark("bench_end")

try: asyncio.run(main())
finally: time.sleep(2); env.stop()
