#!/usr/bin/env python3
"""KV miss-cost microbenchmark (RQ1 miss-cost feasibility study, 2026-10-18): TTFT of one request as a function of
its prompt length L, of how much of its prefix is cached and where (vLLM GPU prefix cache / LMCache L1 in DRAM or on a
CXL devdax), and of WHERE a miss sits (a hole at position h vs a clean prefix of length h). Streaming completions with
token-id prompts (pseudo-random tokens, like serve_replay.py); first-token time measured at the client. Runs against a
live vLLM + LMCache server; the GPU prefix cache is flushed with filler prompts between the store and the measured hit.

Cases per L (each repeated `reps` times with fresh random prompts):
  cold         the prompt has never been seen (recompute everything; stored to LMCache during prefill)
  gpu          the same prompt again immediately (vLLM's own prefix cache)
  l1           the same prompt after the GPU cache was flushed (loaded from LMCache L1: DRAM or CXL depending on the server)
  prefix<f>    a new prompt sharing the first f·L tokens with a stored one, after a flush (load f·L, recompute the rest)
  hole<f>      the stored prompt with 16 tokens changed at position f·L, after a flush (usable prefix = f·L; the rest is
               cached but unusable — the prefix-dependence test)
  conc4        four different cold prompts in flight at once (per-request TTFT under contention)
Output: one CSV line per request: case, L, f, rep, concurrency, ttft_ms, prompt_tokens, cached_tokens (vLLM's report).
usage: misscost_bench.py <url> <model> <out.csv> [L list=1024,2048,4096,7680] [reps=3] [flush_tokens=48000]"""
import asyncio, csv, json, random, sys, time
import aiohttp

url, model, out = sys.argv[1], sys.argv[2], sys.argv[3]
Ls = [int(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "1024,2048,4096,7680").split(",")]
REPS = int(sys.argv[5]) if len(sys.argv) > 5 else 3; FLUSH = int(sys.argv[6]) if len(sys.argv) > 6 else 48000
rng = random.Random(2026)
def toks(n): return [rng.randrange(1000, 150000) for _ in range(n)]
W = csv.writer(open(out, "w", newline="")); W.writerow(["case", "L", "f", "rep", "conc", "ttft_ms", "total_ms", "prompt_tokens", "cached_tokens", "out_tokens"])

async def one(sess, prompt, max_tokens=8):
    body = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": 0, "ignore_eos": True, "stream": True, "stream_options": {"include_usage": True}}
    t0 = time.monotonic(); first = None; cached = -1; ntok = 0
    async with sess.post(url + "/v1/completions", json=body) as resp:
        async for raw in resp.content:
            line = raw.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]": continue
            d = json.loads(line[6:])
            if d.get("choices") and d["choices"][0].get("text") and first is None: first = time.monotonic()
            if d.get("usage"):
                det = d["usage"].get("prompt_tokens_details") or {}; cached = det.get("cached_tokens", -1) if det else -1; ntok = d["usage"].get("completion_tokens", 0)
    t1 = time.monotonic()
    return ((first or t1) - t0) * 1000, (t1 - t0) * 1000, cached, ntok

async def flush(sess):
    """Push FLUSH tokens of other prompts through the server so that vLLM's GPU prefix cache no longer holds the measured prompt."""
    n = 0
    while n < FLUSH:
        p = toks(4096); n += len(p); await one(sess, p, 1)

async def main():
    conn = aiohttp.TCPConnector(limit=0); tmo = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(connector=conn, timeout=tmo) as sess:
        await one(sess, toks(256), 1)                                                   # warm-up
        for L in Ls:
            for rep in range(REPS):
                base = toks(L)
                t, tt, c, n = await one(sess, base); W.writerow(["cold", L, 1.0, rep, 1, f"{t:.1f}", f"{tt:.1f}", L, c, n])
                t, tt, c, n = await one(sess, base); W.writerow(["gpu", L, 1.0, rep, 1, f"{t:.1f}", f"{tt:.1f}", L, c, n])
                await flush(sess)
                t, tt, c, n = await one(sess, base); W.writerow(["l1", L, 1.0, rep, 1, f"{t:.1f}", f"{tt:.1f}", L, c, n])
                for f in (0.25, 0.5, 0.75):
                    k = int(L * f) // 256 * 256
                    await flush(sess)
                    p = base[:k] + toks(L - k); t, tt, c, n = await one(sess, p); W.writerow([f"prefix", L, f, rep, 1, f"{t:.1f}", f"{tt:.1f}", L, c, n])
                    await flush(sess)
                    p = list(base); p[k:k + 16] = toks(16); t, tt, c, n = await one(sess, p); W.writerow([f"hole", L, f, rep, 1, f"{t:.1f}", f"{tt:.1f}", L, c, n])
                # make sure the base prompt is cached again in L1 for the next rep's reference (it is: stores happen on every prefill)
            # contention: four cold prompts at once
            for rep in range(REPS):
                ps = [toks(L) for _ in range(4)]
                res = await asyncio.gather(*(one(sess, p) for p in ps))
                for t, tt, c, n in res: W.writerow(["conc4", L, 1.0, rep, 4, f"{t:.1f}", f"{tt:.1f}", L, c, n])
            print(f"L={L} done", flush=True)

asyncio.run(main())
