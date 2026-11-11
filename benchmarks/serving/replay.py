#!/usr/bin/env python3
"""Open-loop replay of a Mooncake trace window against the instrumented serving environment (2026-11-04; the replay
of benchmarks/lmcache/serve_replay.py, 2026-10-10, moved onto client.py so that every request carries X-Request-Id and
the same record format). Each 512-token hash block of the trace becomes a fixed pseudo-random token sequence, so
requests that share hash blocks share prefixes; request i is sent at (ts_i - t0) / speed wall seconds after the start
whatever happened to earlier requests (offered load only); the trace's output length is capped at max_out; prompts are
cut to max_model_len - max_out - 8 tokens. REPLAY_DEQUANT_S > 0 spreads requests that share a quantized timestamp over
the quantum. One server configuration per invocation; the trace window is replayed once.
prio_from=<client.jsonl of an earlier replay of the same window> (2026-11-10): oracle hits-first priority, a baseline that uses vLLM's own
priority scheduling (--scheduling-policy priority): request i is sent with priority 0 if at least half of its prompt was served from a
cache in that earlier run, with priority 1 otherwise (a client cannot know this in advance; the earlier run stands in for that knowledge).
prio=len (2026-11-11): shortest-prompt-first, a baseline a client can realize with vLLM's priority scheduling: the priority of a request is
its number of prompt tokens (lower is served first; ties by arrival).
usage: replay.py <out> <tag> <trace.jsonl> <t0_s> <t1_s> <speed> [max_out=1024] [dequant_s=0] [prio_from=<client.jsonl> | prio=len] [Cfg key=value ...]"""
import asyncio, json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_env import Cfg, ServingEnv, parse_kv
from client import Client

out, tag, trace = sys.argv[1:4]; t0, t1, speed = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
kv = dict(a.split("=", 1) for a in sys.argv[7:]); MAX_OUT = int(kv.pop("max_out", "1024")); DEQ = float(kv.pop("dequant_s", "0")); PRIO_FROM = kv.pop("prio_from", ""); PRIO_MODE = kv.pop("prio", "")
cfg = parse_kv([f"{k}={v}" for k, v in kv.items()], Cfg(out=out, tag=tag, l1_gb=40.0, enforce_eager=False))
PRIO = None
assert PRIO_MODE in ("", "len"), PRIO_MODE
if PRIO_MODE == "len": cfg.sched_policy = "priority"
if PRIO_FROM:
    PRIO = {}; cfg.sched_policy = "priority"
    for line in open(PRIO_FROM):
        r = json.loads(line)
        if r.get("case") == "trace": PRIO[int(r["rid"].rsplit("-", 1)[1])] = 0 if max(0, r.get("cached_tokens") or 0) >= 0.5 * (r.get("prompt_tokens") or 1) else 1
cache = {}
def block_tokens(h):
    if h not in cache:
        rng = random.Random(h * 2654435761 + 12345); cache[h] = [rng.randrange(1000, 150000) for _ in range(512)]
    return cache[h]
reqs = []
for line in open(trace):
    r = json.loads(line); ts = r["timestamp"] / 1000.0
    if ts < t0: continue
    if ts >= t1: break
    o = min(int(r["output_length"]), MAX_OUT)
    toks = [t for h in r["hash_ids"] for t in block_tokens(h)][: r["input_length"]][: cfg.max_model_len - o - 8]
    reqs.append((ts, toks, o, len(r["hash_ids"])))
if DEQ > 0:
    groups = {}
    for i, (ts, *_) in enumerate(reqs): groups.setdefault(ts, []).append(i)
    for ts, idxs in groups.items():
        for k, i in enumerate(idxs): reqs[i] = (ts + DEQ * (k + 0.5) / len(idxs),) + reqs[i][1:]
    reqs.sort(key=lambda x: x[0])
print(f"{len(reqs)} requests, trace window {t0}-{t1} s at {speed}x = {(t1 - t0) / speed:.0f} wall s, prompt tokens {sum(len(r[1]) for r in reqs)}", flush=True)
env = ServingEnv(cfg).start()

async def main():
    async with Client(env.url(), cfg.model, env.f("client.jsonl"), concurrency_limit=4096) as cl:
        env.mark("replay_start", f"trace={os.path.basename(trace)} t0={t0} t1={t1} speed={speed} n={len(reqs)} max_out={MAX_OUT} dequant={DEQ}")
        start = time.monotonic() + 1.0
        items = [dict(rid=f"{tag}-{i}", tokens=toks, case="trace", L=len(toks), max_tokens=o, extra={"trace_s": ts, "blocks": nb}, priority=(len(toks) if PRIO_MODE == "len" else None if PRIO is None else PRIO.get(i, 1))) for i, (ts, toks, o, nb) in enumerate(reqs)]
        times = [(ts - t0) / speed for ts, *_ in reqs]
        done = 0
        async def progress():
            while True:
                await asyncio.sleep(60); print(f"[{time.strftime('%H:%M:%S')}] {cl.f.tell()} bytes of records; elapsed {time.monotonic() - start:.0f} s", flush=True)
        pt = asyncio.create_task(progress())
        await cl.timed(items, times, t_start=start); pt.cancel()
        env.mark("replay_end")

try: asyncio.run(main())
finally: time.sleep(2); env.stop()
