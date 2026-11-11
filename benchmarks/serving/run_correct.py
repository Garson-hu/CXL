#!/usr/bin/env python3
"""Output-correctness check of the KV paths (2026-11-10 admission study, brief section 9): the same prompts are answered (temperature 0,
OUT output tokens, ignore_eos) four ways on one server and the generated text is compared with the first way, request by request:
  compute   every prompt alone on an idle engine, nothing cached (the reference; it also stores the prompt's KV in LMCache)
  host      after a flush of the GPU prefix cache: every prompt alone again -> served by a load from LMCache
  gpu       immediately once more -> served from the GPU prefix cache
  host+load after another flush: groups of four prompts are sent 0.3 s after a 28k-token miss has started prefilling (the situation in
            which the prototype mechanisms act: the hits are admitted during the prefill; the stock scheduler serves them after it)
  cold+load the same prompts with a cache salt (vLLM and LMCache then share nothing with the unsalted requests), sent the same way next
            to a 28k-token prefill: COMPUTED under the same load. Its difference from the reference is the engine's own variability
            when only the batch composition changes -- the yardstick for host+load.
A loaded prefix that did not correspond to the prompt, or a block that was missing or stale when attention used it, changes the text.
Prints the counts and writes <out>/<tag>-correct.md. One server configuration per invocation.
usage: run_correct.py <out> <tag> [n=24] [out_tokens=32] [Cfg key=value ...]"""
import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_env import Cfg, ServingEnv, parse_kv
from client import Client, prompt

out, tag = sys.argv[1:3]; kv = dict(a.split("=", 1) for a in sys.argv[3:])
N = int(kv.pop("n", "24")); OUT = int(kv.pop("out_tokens", "32"))
cfg = parse_kv([f"{k}={v}" for k, v in kv.items()], Cfg(out=out, tag=tag, l1_gb=40.0, enforce_eager=False, adm=True))
LENS = [1024, 2048, 4096, 8192]; TAIL = 100                       # a tail that is not a whole LMCache chunk: recomputed on every path
P = [prompt(4_100_000 + i, LENS[i % 4] + TAIL) for i in range(N)]
env = ServingEnv(cfg).start(); RES = {}
async def main():
    async with Client(env.url(), cfg.model, env.f("client.jsonl")) as cl:
        async def one(phase, i, toks, **k):
            r = await cl.one(f"{tag}-{phase}-{i}", toks, case=phase, L=len(toks), max_tokens=OUT, **k); RES[(phase, i)] = r; return r
        async def flush(name):
            for j in range(8): await cl.one(f"{tag}-flush-{name}-{j}", prompt(20_000 + j, 16320), case="flush", L=16320, max_tokens=1)
            await asyncio.sleep(1.0)
        env.mark("warmup"); await cl.sequential([dict(rid=f"{tag}-warm{i}", tokens=prompt(10_000 + i, 1024), case="warm", L=1024, max_tokens=4) for i in range(3)])
        env.mark("compute")
        for i in range(N): await one("compute", i, P[i])
        await asyncio.sleep(2.0); await flush("a"); env.mark("host")
        for i in range(N): await one("host", i, P[i]); await one("gpu", i, P[i])
        await flush("b"); env.mark("host+load")                  # the flush (8 x 16,320 tokens) exceeds a pool of up to 8,000 blocks: pin gpu_blocks on larger GPUs
        for g in range(0, N, 4):
            blk = asyncio.create_task(cl.one(f"{tag}-blk-h{g}", prompt(4_300_000 + g, 28000), case="blocker", L=28000, max_tokens=4)); t0 = time.monotonic()
            await asyncio.gather(*(one("host+load", i, P[i], t_send=t0 + 0.3 + 0.05 * (i - g)) for i in range(g, min(N, g + 4)))); await blk
        env.mark("cold+load")
        for g in range(0, N, 4):
            blk = asyncio.create_task(cl.one(f"{tag}-blk-c{g}", prompt(4_400_000 + g, 28000), case="blocker", L=28000, max_tokens=4)); t0 = time.monotonic()
            await asyncio.gather(*(one("cold+load", i, P[i], t_send=t0 + 0.3 + 0.05 * (i - g), body_extra={"cache_salt": "kvadm-correct"}) for i in range(g, min(N, g + 4)))); await blk
        env.mark("bench_end")
try: asyncio.run(main())
finally: time.sleep(2); env.stop()
def same(a, b): return a is not None and b is not None and a["status"] == 200 and b["status"] == 200 and a["out_sha"] == b["out_sha"]
L = [f"## Output correctness, `{tag}` ({N} prompts of 1k-8k + {TAIL} tokens, {OUT} output tokens, temperature 0)\n", "| path | requests | HTTP 200 | cached tokens / prompt tokens | text identical to the computed reference | TTFT p50 (s) |", "|---|---|---|---|---|---|"]
for ph, refph in (("compute", None), ("host", "compute"), ("gpu", "compute"), ("host+load", "compute"), ("cold+load", "compute")):
    v = [RES.get((ph, i)) for i in range(N)]; ok = [r for r in v if r and r["status"] == 200]
    idn = "–" if refph is None else f"{sum(same(RES.get((ph, i)), RES.get((refph, i))) for i in range(N))} / {N}"
    tt = sorted(r["ttft_ms"] for r in ok)
    L.append(f"| {ph} | {len(v)} | {len(ok)} | {sum(max(0, r['cached_tokens'] or 0) for r in ok)} / {sum(r['prompt_tokens'] for r in ok)} | {idn} | {tt[len(tt) // 2] / 1000:.2f} |" if ok else f"| {ph} | {len(v)} | 0 | – | – | – |")
T = "\n".join(L) + "\n"; open(f"{out}/{tag}-correct.md", "w").write(T); print(T)
