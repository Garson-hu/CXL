#!/usr/bin/env python3
"""Open-loop replay of a Mooncake trace window against a vLLM OpenAI server (with LMCache behind it). (2026-10-10)
Each 512-token hash block becomes a fixed pseudo-random token sequence (same as probe_rate.py), so requests that share
hash blocks share prefixes. Request i is sent at (ts_i - t0) / speed seconds after the start, whatever happened to
earlier requests. Streaming completions with the trace's output length (capped), ignore_eos.
Output, one line per request: "REQ <idx> <trace_s> <send_ns> <first_token_ns> <end_ns> <prompt_tokens> <out_tokens>
<cached_tokens>" (mono ns; cached = vLLM's prompt_tokens_details.cached_tokens when the server reports it, else -1).
usage: serve_replay.py <url> <model> <trace.jsonl> <t0_s> <t1_s> <speed> [max_model_len=32768] [max_out=1024] [duration_s=0]
  duration_s > 0: stop sending after that many seconds and cancel requests still open (saturated runs); 0 = run to the end."""
import asyncio, json, os, random, sys, time
import aiohttp

url, model, trace = sys.argv[1], sys.argv[2], sys.argv[3]
t0, t1, speed = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
max_len = int(sys.argv[7]) if len(sys.argv) > 7 else 32768
max_out = int(sys.argv[8]) if len(sys.argv) > 8 else 1024
duration = float(sys.argv[9]) if len(sys.argv) > 9 else 0.0
cache = {}
def block_tokens(h):
    if h not in cache:
        rng = random.Random(h * 2654435761 + 12345); cache[h] = [rng.randrange(1000, 150000) for _ in range(512)]
    return cache[h]

reqs = []
DEQ = float(os.environ.get("REPLAY_DEQUANT_S", "0"))   # > 0: spread requests that share a quantized timestamp uniformly over the quantum (2026-10-17; default off)
for line in open(trace):
    r = json.loads(line); ts = r["timestamp"] / 1000.0
    if ts < t0: continue
    if ts >= t1: break
    out = min(int(r["output_length"]), max_out)
    toks = [t for h in r["hash_ids"] for t in block_tokens(h)][: r["input_length"]][: max_len - out - 8]
    reqs.append((ts, toks, out))
if DEQ > 0:
    groups = {}
    for i, (ts, toks, out) in enumerate(reqs): groups.setdefault(ts, []).append(i)
    for ts, idxs in groups.items():
        for k, i in enumerate(idxs): reqs[i] = (ts + DEQ * (k + 0.5) / len(idxs), reqs[i][1], reqs[i][2])
    reqs.sort(key=lambda x: x[0])

async def one(sess, i, ts, toks, out, start):
    await asyncio.sleep(max(0.0, start + (ts - t0) / speed - time.monotonic()))
    body = {"model": model, "prompt": toks, "max_tokens": out, "temperature": 0, "ignore_eos": True, "stream": True,
            "stream_options": {"include_usage": True}}
    send = time.monotonic_ns(); first = 0; ntok = 0; cached = -1
    try:
        async with sess.post(url + "/v1/completions", json=body) as resp:
            async for raw in resp.content:
                line = raw.decode().strip()
                if not line.startswith("data: ") or line == "data: [DONE]": continue
                d = json.loads(line[6:])
                if d.get("choices") and d["choices"][0].get("text"):
                    if not first: first = time.monotonic_ns()
                    ntok += 1
                if d.get("usage"):
                    det = d["usage"].get("prompt_tokens_details") or {}
                    cached = det.get("cached_tokens", -1) if det else -1
                    ntok = d["usage"].get("completion_tokens", ntok)
    except Exception as e:
        print(f"ERR {i} {e!r}", flush=True)
    print(f"REQ {i} {ts:.3f} {send} {first} {time.monotonic_ns()} {len(toks)} {ntok} {cached}", flush=True)

async def main():
    print(f"# serve_replay {trace} [{t0}, {t1}) s at {speed}x: {len(reqs)} requests, start {time.monotonic_ns()}", flush=True)
    conn = aiohttp.TCPConnector(limit=0); tmo = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(connector=conn, timeout=tmo) as sess:
        start = time.monotonic()
        tasks = [asyncio.create_task(one(sess, i, ts, toks, out, start)) for i, (ts, toks, out) in enumerate(reqs)]
        done, pending = await asyncio.wait(tasks, timeout=duration if duration > 0 else None)
        for t in pending: t.cancel()
        if pending: print(f"# duration limit {duration} s reached: {len(pending)} requests cancelled or never sent", flush=True)
    print(f"# serve_replay end {time.monotonic_ns()}", flush=True)

asyncio.run(main())
