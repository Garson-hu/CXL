#!/usr/bin/env python3
"""Workload client for the 2026-11-04 serving-scheduling study: streaming completions with token-id prompts against the
vLLM OpenAI server, one JSON line per request in the record file:
  {"rid": X-Request-Id (= vLLM's request id, = LMCache's session id), "case", "L", "rep", "grp", "send_mono_ns",
   "send_wall", "first_mono_ns" (first token chunk at the client), "end_mono_ns", "ttft_ms", "total_ms", "prompt_tokens",
   "cached_tokens" (vLLM's prompt_tokens_details.cached_tokens: GPU prefix cache + external hits), "out_tokens",
   "status" (HTTP), "error", "resp_id", "priority", "out_sha" / "out_head" (sha1 and first characters of the generated text; added 2026-11-10)}
Prompts are pseudo-random token ids in [1000, 150000) drawn from a seeded generator (the convention of serve_replay.py and
misscost_bench.py), so two prompts share a prefix iff they are drawn from the same seed. time.monotonic_ns() is the clock
vLLM's EngineCore uses (time.monotonic()), so client and engine timestamps are directly comparable on this host."""
import asyncio, hashlib, json, random, time
import aiohttp

def prompt(seed, n):
    rng = random.Random(seed); return [rng.randrange(1000, 150000) for _ in range(n)]

def prompt_with_prefix(seed, k, seed2, n):
    """the first k tokens of prompt(seed, .) followed by n - k tokens drawn from seed2 (a prefix-sharing variant)"""
    return prompt(seed, k) + prompt(seed2, n)[: max(0, n - k)]

class Client:
    def __init__(self, url, model, record_path, concurrency_limit=256):
        self.url, self.model = url, model; self.f = open(record_path, "a", buffering=1); self.sem = asyncio.Semaphore(concurrency_limit); self.sess = None
    async def __aenter__(self):
        self.sess = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None, sock_read=None), connector=aiohttp.TCPConnector(limit=512)); return self
    async def __aexit__(self, *a):
        await self.sess.close(); self.f.close()

    async def one(self, rid, tokens, case="", L=0, rep=0, grp="", max_tokens=8, priority=None, extra=None, t_send=None, body_extra=None):
        """send one request (optionally delayed until monotonic t_send) and record it; returns the record; body_extra = further fields of
        the request body (e.g. {"cache_salt": ...}: vLLM and LMCache then share no cached prefix with requests of another salt)"""
        body = {"model": self.model, "prompt": tokens, "max_tokens": max_tokens, "temperature": 0, "ignore_eos": True, "stream": True, "stream_options": {"include_usage": True}}
        if priority is not None: body["priority"] = priority
        if body_extra: body.update(body_extra)
        if t_send is not None:
            d = t_send - time.monotonic()
            if d > 0: await asyncio.sleep(d)
        rec = {"rid": rid, "case": case, "L": len(tokens), "rep": rep, "grp": grp, "priority": priority, "prompt_tokens": len(tokens)}
        if extra: rec.update(extra)
        first = None; ntok = 0; cached = -1; resp_id = None; status = None; err = None; text = []
        async with self.sem:
            send = time.monotonic_ns(); rec["send_mono_ns"] = send; rec["send_wall"] = time.time()
            try:
                async with self.sess.post(self.url + "/v1/completions", json=body, headers={"X-Request-Id": rid}) as resp:
                    status = resp.status
                    if status != 200: err = (await resp.text())[:300]
                    else:
                        async for raw in resp.content:
                            line = raw.decode().strip()
                            if not line.startswith("data: ") or line == "data: [DONE]": continue
                            d = json.loads(line[6:]); resp_id = resp_id or d.get("id")
                            if d.get("choices") and d["choices"][0].get("text"):
                                text.append(d["choices"][0]["text"])
                                if first is None: first = time.monotonic_ns()
                            if d.get("usage"):
                                det = d["usage"].get("prompt_tokens_details") or {}; cached = det.get("cached_tokens", -1) if det else -1
                                ntok = d["usage"].get("completion_tokens", 0); rec["prompt_tokens"] = d["usage"].get("prompt_tokens", len(tokens))
            except Exception as e:
                err = repr(e)[:300]
            end = time.monotonic_ns()
        rec.update(first_mono_ns=first, end_mono_ns=end, ttft_ms=((first or end) - send) / 1e6, total_ms=(end - send) / 1e6, cached_tokens=cached, out_tokens=ntok, status=status, error=err, resp_id=resp_id)
        out_text = "".join(text)       # 2026-11-10: the generated text, for output-equality checks between policies (temperature 0)
        rec.update(out_sha=hashlib.sha1(out_text.encode()).hexdigest()[:16], out_head=out_text[:32])
        self.f.write(json.dumps(rec, separators=(",", ":")) + "\n")
        return rec

    async def sequential(self, reqs):
        """reqs: list of dicts with the arguments of one(); sent one after the other"""
        return [await self.one(**r) for r in reqs]

    async def burst(self, reqs, spacing_ms=0.0):
        """all requests sent at once (or spacing_ms apart), run concurrently"""
        t0 = time.monotonic()
        return await asyncio.gather(*(self.one(**r, t_send=t0 + i * spacing_ms / 1000) for i, r in enumerate(reqs)))

    async def open_loop(self, reqs, rate, seed=0, t_start=None):
        """Poisson arrivals at `rate` requests per second in the given order (exponential gaps, seeded); open loop."""
        rng = random.Random(seed); t = t_start if t_start is not None else time.monotonic() + 0.5; tasks = []
        for r in reqs:
            tasks.append(asyncio.create_task(self.one(**r, t_send=t))); t += rng.expovariate(rate)
        return await asyncio.gather(*tasks)

    async def timed(self, reqs, times, t_start=None):
        """send request i at t_start + times[i] seconds (open loop with an explicit schedule)"""
        t0 = t_start if t_start is not None else time.monotonic() + 0.5
        return await asyncio.gather(*(self.one(**r, t_send=t0 + ti) for r, ti in zip(reqs, times)))

    async def closed_loop(self, gen, concurrency, n_total):
        """`concurrency` workers each take the next request from gen (an iterator of one() kwargs) until n_total are done"""
        it = iter(gen); lock = asyncio.Lock(); done = []
        async def worker():
            while True:
                async with lock:
                    if len(done) + len(active) >= n_total: return
                    try: r = next(it)
                    except StopIteration: return
                    active.add(r["rid"])
                rec = await self.one(**r)
                active.discard(r["rid"]); done.append(rec)
        active = set()
        await asyncio.gather(*(worker() for _ in range(concurrency)))
        return done
