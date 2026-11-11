#!/usr/bin/env python3
"""Experiment A3 / C (2026-11-10): controlled reproduction of GPU-KV admission pressure. One server configuration per
invocation; every trial ("epoch") builds a known GPU KV state from the scheduler's own allocations and then sends probes:

  holders  K long-running requests (prompt of P_h tokens from a per-holder base prompt, HOUT output tokens, streamed).
           They decode for the whole trial and hold ceil((P_h + generated) / 16) GPU KV blocks each; P_h is chosen so
           that `free` blocks are left when the probes arrive. The driver cancels them at the end of the trial, and can
           cancel n_release of them `release_at` seconds after the first probe (a controlled release of blocks).
  probes   host  = a prompt whose first L tokens are stored in LMCache and not in the GPU prefix cache, plus TAIL fresh
                   tokens (an external hit of L tokens);  cold = L + TAIL fresh tokens (a miss of the same length).
The GPU KV pressure a probe meets is not inferred from K: the admission stream (kvadm/sitecustomize.py) records the free
blocks, the blocks needed and the gate at every admission attempt. Trials are marked in <tag>-meta.txt
("M trial ..." JSON, "M release ..."); probes carry grp = trial name. Probe ids: <tag>-<trial>-r<rep>-p<k>-<type>-L<L>.

plans (plan=...):
  a3     part 1  one probe per trial, L in 1k/2k/4k/8k (+TAIL), host vs cold, free = 3.0 / 1.5 / 0.6 x the probe's full
                 block need, K = 6 holders; at 0.6 one holder is released 3 s after the probe
         part 2  the same at L = 4k with K = 4 and K = 12 holders (same free blocks, different numbers of running requests)
         part 3  two probes 5 ms apart under pressure (free = 700 blocks): [host 4k, cold 8k], [cold 8k, host 4k],
                 [cold 4k, cold 8k], [cold 8k, cold 4k]; one holder released after 3 s
         part 4  bursts of 4 and 8 probes of 2k (+TAIL), alternating host / cold, free = half of the burst's need,
                 hits first or misses first; one holder released after 3 s
         part 5  no memory pressure (free > 5,000 blocks): [cold 8k, host 4k] and [host 4k, cold 8k]
  smoke  two trials of part 1 and one of part 3
  c1     compute contention without memory pressure (Experiment C): a blocker miss of c1_blockers tokens starts prefilling,
         external hits of 4k arrive 0.5 / 2.5 / 4.5 s later and a 4k miss 1.5 s later; 6 small decoding holders
  c2     a 16k miss that fits with 100 / 400 blocks to spare starts prefilling; external hits of 4k arrive 0.5 and 2.5 s later
         (the in-flight reservation gate); a holder is released after 8 s
  c3     head-of-line blocking: a 16k miss that does not fit (600 free blocks), then two external hits and a miss of 2k that
         fit, and one more hit 1 s later; a holder is released after 4 s
  c5     bounded reservation (the brief's B2): a 16k external hit that does not fit (300 free blocks) arrives first, then a stream of 2k
         misses that do fit (one every 0.15 s for 4.5 s: more than the GPU can compute, so they take every block that is freed); one of the
         10 holders is released 1.0, 2.5 and 4.0 s after the hit (about 710 blocks each): the hit fits after the second release
usage: run_adm.py <out> <tag> [plan=a3] [reps=3] [holder_out=2000] [probe_out=16] [tail=256] [parts=1,2,3,4,5] [Cfg key=value ...]"""
import asyncio, json, os, re, sys, time, urllib.request
import aiohttp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_env import Cfg, ServingEnv, parse_kv
from client import Client, prompt

out, tag = sys.argv[1:3]; kv = dict(a.split("=", 1) for a in sys.argv[3:])
PLAN = kv.pop("plan", "a3"); REPS = int(kv.pop("reps", "3")); HOUT = int(kv.pop("holder_out", "2000")); POUT = int(kv.pop("probe_out", "16"))
TAIL = int(kv.pop("tail", "256")); PARTS = [int(x) for x in kv.pop("parts", "1,2,3,4,5").split(",")]; TMAX = float(kv.pop("tmax", "25"))
G_BLOCKS = int(kv.pop("growth_blocks", "6"))          # output blocks a holder has added when the probes arrive (calibrated on the first trials)
_HB = kv.pop("hbase", None); C1_LB = [int(x) for x in kv.pop("c1_blockers", "8192,16384,28000").split(",")]
cfg = parse_kv([f"{k}={v}" for k, v in kv.items()], Cfg(out=out, tag=tag, l1_gb=120.0, enforce_eager=False, adm=True))
BS = 16; HBASE = int(_HB) if _HB else 30000          # GPU KV block size (tokens); length of a holder's base prompt
def blocks(n): return -(-n // BS)

# ---------------------------------------------------------------- the plan
def trial(name, K, free, probes, release_at=None, n_release=1): return dict(name=name, K=K, free=free, probes=probes, release_at=release_at, n_release=n_release)
def build_plan():
    T = []
    if PLAN == "smoke":
        T.append(trial("p1-L4096-f1.5-host", 6, int(1.5 * blocks(4096 + TAIL)), [(0.0, "host", 4096)]))
        T.append(trial("p1-L4096-f0.6-cold", 6, int(0.6 * blocks(4096 + TAIL)), [(0.0, "cold", 4096)], release_at=3.0))
        T.append(trial("p3-H4M8", 6, 700, [(0.0, "host", 4096), (0.005, "cold", 8192)], release_at=3.0))
        return [dict(t, rep=0) for t in T]
    if PLAN == "c1":
        # compute contention without memory pressure: one long miss (the blocker) starts prefilling; external hits of 4k (+TAIL)
        # arrive 0.5 / 2.5 / 4.5 s later, a 4k miss 1.5 s later; 6 small decoding holders in the background
        for rep in range(REPS):
            for Lb in C1_LB:
                T.append(dict(trial(f"c1-B{Lb}", 6, 5500, [(0.0, "cold", Lb), (0.5, "host", 4096), (1.5, "cold", 4096), (2.5, "host", 4096), (4.5, "host", 4096)]), rep=rep))
        return T
    if PLAN == "c2":
        # a long prefill under tight memory: the 16k blocker fits with `margin` blocks to spare; external hits of 4k arrive 0.5 and 2.5 s
        # later. With the stock rule a load is admitted only under the blocker's remaining-block reservation.
        for rep in range(REPS):
            for margin in (100, 400):
                T.append(dict(trial(f"c2-m{margin}", 6, blocks(16384 + TAIL) + margin, [(0.0, "cold", 16384), (0.5, "host", 4096), (2.5, "host", 4096)], release_at=8.0), rep=rep))
        return T
    if PLAN == "c3":
        # head-of-line blocking under memory pressure: a 16k miss that does not fit (600 free blocks) is followed by two external hits and a
        # miss of 2k that do; one holder is released 4 s later
        for rep in range(REPS):
            T.append(dict(trial("c3-hol", 6, 600, [(0.0, "cold", 16384), (0.05, "host", 2048), (0.10, "host", 2048), (0.15, "cold", 2048), (1.0, "host", 2048)], release_at=4.0), rep=rep))
        return T
    if PLAN == "c5":
        for rep in range(REPS):
            T.append(dict(trial("c5-res", 10, 300, [(0.0, "host", 16384)] + [(0.05 + 0.15 * i, "cold", 2048) for i in range(30)], release_at=[1.0, 2.5, 4.0]), rep=rep))
        return T
    for rep in range(REPS):
        if 1 in PARTS:
            for L in (1024, 2048, 4096, 8192):
                for rho in (3.0, 1.5, 0.6):
                    for ty in ("host", "cold"):
                        T.append(dict(trial(f"p1-L{L}-f{rho:g}-{ty}", 6, int(rho * blocks(L + TAIL)), [(0.0, ty, L)], release_at=3.0 if rho < 1 else None), rep=rep))
        if 2 in PARTS and rep < 2:
            for K in (4, 12):
                for rho in (1.5, 0.6):
                    for ty in ("host", "cold"):
                        T.append(dict(trial(f"p2-K{K}-f{rho:g}-{ty}", K, int(rho * blocks(4096 + TAIL)), [(0.0, ty, 4096)], release_at=3.0 if rho < 1 else None), rep=rep))
        if 3 in PARTS:
            for nm, pr in (("H4M8", [("host", 4096), ("cold", 8192)]), ("M8H4", [("cold", 8192), ("host", 4096)]), ("C4M8", [("cold", 4096), ("cold", 8192)]), ("M8C4", [("cold", 8192), ("cold", 4096)])):
                T.append(dict(trial(f"p3-{nm}", 6, 700, [(0.005 * i, ty, L) for i, (ty, L) in enumerate(pr)], release_at=3.0), rep=rep))
        if 4 in PARTS and rep < 2:
            for n in (4, 8):
                for first in ("host", "cold"):
                    other = "cold" if first == "host" else "host"
                    T.append(dict(trial(f"p4-n{n}-{first}first", 6, int(0.5 * n * blocks(2048 + TAIL)), [(0.002 * i, first if i % 2 == 0 else other, 2048) for i in range(n)], release_at=3.0), rep=rep))
        if 5 in PARTS:
            for nm, pr in (("M8H4", [("cold", 8192), ("host", 4096)]), ("H4M8", [("host", 4096), ("cold", 8192)])):
                T.append(dict(trial(f"p5-{nm}", 6, 5500, [(0.005 * i, ty, L) for i, (ty, L) in enumerate(pr)]), rep=rep))
    return T
TRIALS = build_plan()
need_pool = {}                                          # host prefixes needed per length (each used once: never in the GPU prefix cache)
for t in TRIALS:
    for _, ty, L in t["probes"]:
        if ty == "host": need_pool[L] = need_pool.get(L, 0) + 1
KMAX = max(t["K"] for t in TRIALS)
def pool_prompt(L, j): return prompt(700_000 + 1000 * (L // 1024) + j, L)
def holder_base(j): return prompt(800_000 + j, HBASE)
fresh = [3_000_000]
def fresh_prompt(n): fresh[0] += 1; return prompt(fresh[0], n)

env = ServingEnv(cfg).start()
m = re.search(r"GPU KV cache size: ([\d,]+) tokens", open(env.f("server.log")).read()); POOL = int(m.group(1).replace(",", "")) // BS
print(f"pool {POOL} blocks; {len(TRIALS)} trials; host prefixes {need_pool}; holders up to {KMAX}", flush=True)

def usage():
    try:
        for l in urllib.request.urlopen(env.url() + "/metrics", timeout=3).read().decode().splitlines():
            if l.startswith("vllm:kv_cache_usage_perc"): return float(l.rsplit(" ", 1)[1])
    except Exception: return None

async def holder(sess, rec_f, rid, tokens, started, extra):
    body = {"model": cfg.model, "prompt": tokens, "max_tokens": HOUT, "temperature": 0, "ignore_eos": True, "stream": True}
    rec = dict(rid=rid, case="holder", L=len(tokens), rep=0, grp=extra["grp"], prompt_tokens=len(tokens), cached_tokens=-1, priority=None, out_tokens=0, status=None, error=None, resp_id=None)
    rec["send_mono_ns"] = time.monotonic_ns(); rec["send_wall"] = time.time(); first = None; n = 0
    try:
        async with sess.post(env.url() + "/v1/completions", json=body, headers={"X-Request-Id": rid}) as resp:
            rec["status"] = resp.status
            async for raw in resp.content:
                line = raw.decode().strip()
                if not line.startswith("data: ") or line == "data: [DONE]": continue
                d = json.loads(line[6:])
                if d.get("choices") and d["choices"][0].get("text"):
                    n += 1
                    if first is None: first = time.monotonic_ns(); started.set()
    except asyncio.CancelledError:
        rec["error"] = "cancelled by the driver"; raise
    except Exception as e:
        rec["error"] = repr(e)[:200]
    finally:
        end = time.monotonic_ns(); started.set()
        rec.update(first_mono_ns=first, end_mono_ns=end, ttft_ms=((first or end) - rec["send_mono_ns"]) / 1e6, total_ms=(end - rec["send_mono_ns"]) / 1e6, out_tokens=n)
        rec_f.write(json.dumps(rec, separators=(",", ":")) + "\n")

async def main():
    used = {L: 0 for L in need_pool}
    async with Client(env.url(), cfg.model, env.f("client.jsonl")) as cl:
        sess = cl.sess
        env.mark("warmup"); await cl.sequential([dict(rid=f"{tag}-warm{i}", tokens=prompt(10_000 + i, 1024), case="warm", L=1024, max_tokens=4) for i in range(3)])
        env.mark("populate")
        for L, n in sorted(need_pool.items()):
            for j in range(n): await cl.one(f"{tag}-pop-L{L}-{j}", pool_prompt(L, j), case="populate", L=L, max_tokens=1)
        for j in range(KMAX): await cl.one(f"{tag}-hbase{j}", holder_base(j), case="populate", L=HBASE, max_tokens=1)
        for i in range(8): await cl.one(f"{tag}-flush{i}", prompt(20_000 + i, 16320), case="flush", L=16320, max_tokens=1)   # 130k tokens > the pool: no pool prefix stays in the GPU prefix cache
        await asyncio.sleep(1.0); print(f"[{time.strftime('%H:%M:%S')}] populated; usage {usage()}", flush=True)
        for n_t, t in enumerate(TRIALS):
            K, F = t["K"], t["free"]; name = f"{t['name']}-r{t['rep']}"
            ph = (POOL - 1 - F) // K - G_BLOCKS; P_h = min(ph * BS, HBASE)
            if P_h < 256: print(f"skip {name}: holders too small"); continue
            evs = [asyncio.Event() for _ in range(K)]
            hs = [asyncio.create_task(holder(sess, cl.f, f"{tag}-{name}-h{j}", holder_base(j)[:P_h], evs[j], dict(grp=name))) for j in range(K)]
            try: await asyncio.wait_for(asyncio.gather(*(e.wait() for e in evs)), 180)
            except asyncio.TimeoutError: print(f"{name}: holders not started in 180 s", flush=True)
            await asyncio.sleep(1.0); u0 = usage()
            reqs = []
            for k, (off, ty, L) in enumerate(t["probes"]):
                if ty == "host":
                    toks = pool_prompt(L, used[L]) + fresh_prompt(TAIL); used[L] += 1
                else: toks = fresh_prompt(L + TAIL)
                reqs.append((off, dict(rid=f"{tag}-{name}-p{k}-{ty}-L{L}", tokens=toks, case=ty, L=L + TAIL, rep=t["rep"], grp=name, max_tokens=POUT, extra=dict(trial=t["name"], K=K, free_target=F, P_h=P_h, pos=k))))
            t0 = time.monotonic() + 0.05
            env.mark("trial", json.dumps(dict(name=name, K=K, free_target=F, P_h=P_h, usage=u0, free_est=None if u0 is None else round((1 - u0) * POOL), t0_mono_ns=int(t0 * 1e9), probes=t["probes"], release_at=t["release_at"])))
            tasks = [asyncio.create_task(cl.one(**r, t_send=t0 + off)) for off, r in reqs]
            if isinstance(t["release_at"], list):           # staged releases: one holder at each instant
                for j, ra in enumerate(t["release_at"]):
                    await asyncio.sleep(max(0.0, t0 + ra - time.monotonic())); hs[K - 1 - j].cancel()
                    env.mark("release", json.dumps(dict(name=name, n=1, at=ra, blocks_each=blocks(P_h))))
            elif t["release_at"] is not None:
                await asyncio.sleep(max(0.0, t0 + t["release_at"] - time.monotonic()))
                for j in range(t["n_release"]): hs[K - 1 - j].cancel()
                env.mark("release", json.dumps(dict(name=name, n=t["n_release"], blocks_each=blocks(P_h))))
            done, pending = await asyncio.wait(tasks, timeout=TMAX)
            for p in pending: p.cancel()
            for h in hs: h.cancel()
            await asyncio.gather(*hs, *pending, return_exceptions=True)
            await asyncio.sleep(1.2)
            if n_t % 10 == 0: print(f"[{time.strftime('%H:%M:%S')}] trial {n_t + 1}/{len(TRIALS)} {name}: usage at probe {u0}, {len(pending)} probes timed out", flush=True)
        env.mark("bench_end")

try: asyncio.run(main())
finally: time.sleep(2); env.stop()
