# 2026-11-04 — CXL-enabled LLM serving: end-to-end scheduling and KV retrieval study (exploratory)

**STATUS: IN PROGRESS (branch `explore/cxl-serving-scheduling-gap`, from `evaluation` 8e2d9e3; not merged).** Exploratory
study outside the charter: it does not change the RQ1 conclusions, the Phase 3 negative result or the gates. Raw data:
`experimental_results/2026-11-04-cxl-serving-scheduling-gap/` (`inspect/`, `smoke/`, one directory per experiment family).
Tools: `benchmarks/serving/` (this study) reusing `benchmarks/agent/kvevt/sitecustomize.py` (LMCache event-bus mirror,
2026-10-17) and the conventions of `benchmarks/lmcache/` (2026-10-10 … 10-18).

## Question
How can an LLM serving system convert CXL-expanded KV-cache capacity into end-to-end serving performance? Immediate
focus: cross-request KV prefix reuse in multi-turn serving (not KV offloading inside one decode). Q1 real end-to-end
benefit of a host-tier (DRAM / CXL / SSD) KV hit; Q2 how the existing scheduler handles requests that need KV retrieval;
Q3 whether larger host capacity moves the bottleneck; Q4 how much scheduling opportunity remains.

## Evidence types used in this file
**MEASURED** = real vLLM 0.31.0 + LMCache 0.5.5 serving on c28's RTX 4060 Ti with the logging-only instrumentation below;
**PREVIOUSLY MEASURED** = numbers from closed experiment files, cited with their date; **SIMULATED** = the calibrated
offline scheduling reference of Experiment C (never presented as a measurement); **CLAIRVOYANT / ZERO-DELAY** = references
that use future knowledge or ignore a cost, never implementable policies. Trace replays state their time-scaling factor.

## 1. Environment and source inspection (2026-11-04, `inspect/environment.txt`, `inspect/*-help.txt`)
- **Branches.** `evaluation` (main line, 8e2d9e3), `explore/reuse-window-prefetch` (closed exploratory, a65c6e3),
  `cxlpath`, `main`. This study's branch starts from `evaluation`.
- **Machine.** c28 (Slurm job 326741, cpu=256, ends 2026-11-07 13:12): 1 socket, 128 cores / 256 threads, one NUMA node
  with 755 GiB DRAM (NPS1); kernel 6.14.11 with `memhp_default_state=offline`; GPU **RTX 4060 Ti 8 GiB** (driver
  580.65.06, PCIe 4.0 ×8, 12.3–12.5 GiB/s host↔device measured 2026-10-07/10); NVMe `/mnt/local` (SOLIDIGM 3.5 TB ext4,
  3.3 TB free; cold restore 2.6–2.9 GiB/s, 2026-10-07).
- **CXL: BLOCKED.** The four CZ120 are exposed only as `/dev/dax0.0` (242 GiB), `/dev/dax1.0` (269 GiB), `/dev/dax2.0`
  (512 GiB), all `crw------- root root` since the 2026-10-18 reboot (mtime 2026-10-20 15:32); open() by `ghu4` fails with
  EACCES (test in `environment.txt`). CXL is not online as a NUMA node. No DAX permission, firmware or system change was
  made (not authorised). Consequence: every "CXL hit" of this study is **PREVIOUSLY MEASURED** (2026-10-07 `gpuread`,
  2026-10-11 pure-DAX L1 replay, 2026-10-18 DRAM-vs-DAX microbenchmark) or **not measured**; the DRAM tier is the stand-in
  and the section "What CXL changes" argues from the earlier measurements. Questions that need real CXL access are listed
  in the Limitations.
- **Software.** Python 3.12.15, vLLM 0.31.0, LMCache 0.5.5 (g05a013b2), torch 2.13.0+cu130 in
  `/mnt/local/ghu4/envs/lmcache`; models on disk: Qwen2.5-3B-Instruct-AWQ (36 KiB of KV per token in fp16: 36 layers ×
  2 KV heads × 128 × 2 B × 2) and Qwen2.5-1.5B-Instruct (28 KiB/token). Traces: Mooncake conversation (12,031 requests
  over 3,537 s = 3.4 req/s, prompts p50 6.9k / p90 27k tokens) and tool-agent (23,608 requests, 6.7 req/s, p50 6.3k /
  p90 16.8k), both with `hash_ids` of 512-token blocks.
- **GPU memory.** 3B-AWQ, fp16 KV, `--gpu-memory-utilization 0.85`: 4.25 GiB of KV = 123,840 tokens eager, 3.74 GiB
  with CUDA graphs; 1.5B fp16: 3.1 GiB = 116,176 tokens. The single-request experiments cap the GPU KV at 3,072 blocks
  (49,152 tokens) so that the GPU prefix cache can be flushed quickly.

### 1.1 How vLLM 0.31 + LMCache 0.5.5 (multi-process mode) actually serve a request with a host-cache hit (SOURCE INSPECTION)
- **Lookup is asynchronous.** `LMCacheMPConnector.get_num_new_matched_tokens` submits the lookup to the LMCache server
  and returns `(None, True)` while it is pending; the scheduler then `skip_request()`s the request and continues with the
  next waiting request (`scheduler.py:955–961`). With `lmcache.mp.eager_prefetch` (default **off**) the lookup is
  submitted at arrival (`on_new_request`) instead of at the first scheduling attempt.
- **Loads are asynchronous.** A hit returns `(need_to_load, True)`; vLLM allocates the GPU blocks, sets the request to
  `WAITING_FOR_REMOTE_KVS` and skips it (`scheduler.py:1258–1282`); the load is started by the worker **after** the
  forward launch of the step (`kv_connector_model_runner_mixin.py:86–94`: "keeping their host-side submission cost off
  the critical path"), is performed by the LMCache **server** process as a GPU transfer kernel on its own stream that
  reads the pinned host objects directly (CUDA IPC; `lmcache_driven_transfer.py:1287–1530`, `transfer_kv_per_object_group`
  H2D), and is reported finished through `get_transfer_results` at the end of a later step; the scheduler then caches
  the blocks and re-queues the request (`_update_waiting_for_remote_kv`). No CPU staging copy and no pinned bounce buffer
  on the load path; the server has **one** GPU transfer thread by default (`--max-gpu-workers 1`).
- **Ready requests run while loads are in flight, and loaded requests go first.** The waiting loop drains
  `kv_holding_waiting` (requests that already hold GPU blocks, including those whose KV just arrived) before `waiting`
  (`scheduler.py:887`), and a skipped request keeps its queue position.
- **A GPU-prefix-cache hit still goes through LMCache**: the local hit is presented block-aligned (16-token blocks), the
  256-token-chunk lookup reports a strictly longer hit, and vLLM drops the partial tail block and loads one chunk from
  the host (`scheduler.py:974–985`): every repeat request pays a lookup round trip and a small async load (measured
  below).
- **Tiers available in this version**: L1 = pinned DRAM (`--l1-size-gb`) or a devdax arena (`--l1-devdax-path`); L2
  adapters (`--l2-adapter`): `fs` / `fs_native` (file per 256-token chunk; the SSD path of this study, with
  `--l2-store-policy skip_l1` so that a later hit is a disk read), `dax`, `raw_block`, remote stores; L2 → L1 prefetch is
  bounded by `--l2-prefetch-max-in-flight` (default 8). A GDS L1 (`--gds-l1-path`, cuFile) exists but was not tried.
- **Instrumentation (logging only, no code path changed).** (i) `benchmarks/serving/vllmevt/sitecustomize.py`: a
  post-import hook in the vLLM processes that records every finished request's `arrival / queued / scheduled / first
  token / last token` instants (vLLM's own `RequestStateStats`) and every engine step (schedule() time, scheduled tokens,
  queue lengths, number of requests in `WAITING_FOR_REMOTE_KVS`, the instant the model output returned, finished loads);
  (ii) the 2026-10-17 LMCache event-bus mirror (`kvevt`): lookup, lookup end with hit tokens, retrieve start / end
  **on the GPU stream** (true transfer end), bytes, stores, L1 events; (iii) `gpu_sampler.py` (NVML PCIe byte counters
  in 5 ms bins + utilization every 50 ms) and `cpu_sampler.py` (/proc/stat per cpu group, per-process CPU time);
  (iv) the client sets `X-Request-Id`, which vLLM uses as the request id and LMCache as the session id, so the three
  records join exactly. Clocks: client and EngineCore use `CLOCK_MONOTONIC`, LMCache events the wall clock; the hook
  records the wall–monotonic offset at start-up (same host). Overhead measured by a hook-less control run.

### 1.2 Instrumentation control and the GPU's PCIe link power state (MEASURED 2026-11-04, `A/a-3b-dram-nohooks`)
The hook-less, sampler-less control run reproduces the cold and GPU-hit TTFTs of the instrumented run within 1–2 ms
(cold 1k / 4k / 16k: 154.7 / 651.4 / 3401.0 vs 154.9 / 650.5 / 3402.2 ms; GPU hit 19.9 / 21.8 / 33.9 vs 20.1 / 22.4 /
35.2 ms) but its **host hits are 20–34 ms slower** (1k / 4k / 16k: 56.3 / 65.2 / 106.6 vs 22.5 / 34.8 / 85.1 ms). The
instrumentation does not slow anything; it keeps the GPU awake. Attribution (`A/a-3b-dram-{hooksonly,samplersonly,
lmhookonly,vllmhookonly}`, 4 repetitions): host hits are fast (19 / 22 / 34 / 85 ms at 256 / 1k / 4k / 16k) with the
samplers alone, with the LMCache event-bus mirror alone (its subscriber makes LMCache launch host callbacks on the
server's CUDA stream) and with both hooks, and slow (62 / 120 / 69 / 96 ms) with the vLLM hook alone, which touches no GPU
state. The idle-gap control (`A/a-3b-idle`, no instrumentation at all, L = 4096, 6 repetitions per gap) settles it:
a host hit sent immediately after the previous request costs 34.4 ms (34–35), the same as in the instrumented runs, but
after an idle gap of 0.05 / 0.2 / 1 / 3 s it costs 75 / 63 / 71 / 94 ms (min 42–54), and a GPU-prefix hit goes from 22.2 ms
to 37 / 68 / 60 / 62 ms; recompute (652 ms) is unaffected. So **after ≥ 50 ms without GPU work the next short request pays
~30–40 ms** — a power-state ramp of this consumer GPU (persistence mode is disabled; at long idle `nvidia-smi` shows the
PCIe link at Gen 1, `inspect/environment.txt`; a query after a 3 s gap already shows Gen 4 / P2 because the query itself
wakes the device). NVML polling and LMCache's stream callbacks keep the GPU awake. All concurrent-serving runs below keep
the sampler on (busy-GPU condition, which a loaded server is in anyway); the sampler-less B/E variants quantify the
penalty under light load. This is a real deployment effect of a lightly loaded server on this hardware, not an artefact
to hide, and it is not specific to host-tier hits.

## 2. Experiments (plan; results are appended per family as they close)
| family | question | status |
|---|---|---|
| A single-request retrieval cost | TTFT and its stages for cold / GPU hit / DRAM hit / SSD hit / vLLM alone, L = 256 … 16,384 | done (§3) |
| B concurrent serving and scheduling | controlled mixes and real-trace windows; default vs eager prefetch vs 4 transfer threads vs priority ordering vs prefill chunk 512 vs synchronous scheduling vs vLLM alone | running (a first `b-default` run whose s1/s2 sequences re-used their cold prompts across levels is kept in `B/flawed/`, not used) |
| C scheduling gap | calibrated offline reference (zero-delay, clairvoyant resource-constrained) vs measured | planned |
| D capacity | L1 sweep (DRAM; CXL blocked) + SSD-backed + recompute-only on trace replays | planned |
| E concurrent retrieval bandwidth | k simultaneous hits, PCIe RX, per-request retrieve time, transfer threads | planned |
| F workload sensitivity | both traces, controlled variations | planned |

## 3. Experiment A — single-request KV retrieval cost (MEASURED 2026-11-04, `A/`, tables `A/tables-a.md`, figures `A/figs/`)
**Why.** A host-tier hit avoids prefill compute but must move the KV into the GPU; before any scheduling question we
need the real cost of a hit per prefix length and tier, as the serving stack actually delivers it (lookup, transfer,
scheduling, the 1-token step), not as a bandwidth number.

**How.** `run_a.py`: one server configuration per run (3B-AWQ unless stated, CUDA graphs, GPU KV capped at 49,152 tokens,
chunk 256, L1 20 GB DRAM); per prefix length L ∈ {256 … 16,384} and 8 repetitions with fresh pseudo-random prompts:
`cold` (never seen: recompute + store), `gpu` (the same prompt again: vLLM's GPU prefix cache), `flush` (4 × 16,320-token
filler prompts, themselves LMCache hits, evict the prompt from the GPU cache), `host` (the same prompt after the flush:
served by LMCache). Tiers: DRAM L1; `fs` L2 on the NVMe with `skip_l1` (an SSD hit; the first run let the page cache serve
the reads — kept as the "page cache" row — the O_DIRECT rerun is the SSD number); vLLM alone (no LMCache: `cold`, `gpu`
and recompute-after-flush); the 1.5B fp16 model on the DRAM tier; a hook-less control. 8 output tokens, TTFT at the
client. Every request's time line is reconstructed from the three records (Figure A3).

**Result (Table A-1, Figures A1–A3).**
- Recompute costs 0.14 ms per token plus 8.2 ns per token² of position (fit of `calib_c.py` within 1%): 45 ms at 256
  tokens, 155 ms at 1k, 651 ms at 4k, 3.40 s at 16k (3B-AWQ); the 1.5B model is 1.9× faster (79 ms at 1k, 1.76 s at 16k).
- A DRAM host hit costs 19.4 ms at 256 tokens, 22.5 ms at 1k, 34.8 ms at 4k, 51.7 ms at 8k, 85.1 ms at 16k (3B;
  1.5B: 22.7 / 24.8 / 35.6 / 48.9 / 77.3 ms). Its stages (Table A-2): lookup 1.3 ms, host→GPU transfer at **11.3–12.0 GB/s =
  the PCIe 4.0 ×8 link** (3.4 ms per 1k tokens = 37.7 MB at 36 KiB/token; 50 ms for 604 MB at 16k), transfer end →
  scheduled 2.5–3.4 ms (the worker reports the finished load at the end of an engine step, the scheduler re-queues the
  request), the 1-token step that recomputes the last token 10 ms (the CUDA-graph floor; 20 ms in eager mode), client and
  frontend legs 1–8 ms. So TTFT(host hit) ≈ 16 ms + 3.4 ms/1k tokens; TTFT(recompute) ≈ 0.14 ms/token: **the host hit is
  cheaper than recompute from ~100 tokens on, 7× at 1k, 19× at 4k, 40× at 16k**.
- A GPU prefix hit with LMCache in the loop costs 18.6–35 ms; vLLM alone serves the same hit in 11.8–40 ms (12.8 vs 20.1 ms at
  1k). The difference is the mechanism of §1.1: the asynchronous lookup (1.3 ms + a scheduler step), a 1-chunk (9.4 MB)
  load of the dropped partial block (1.0 ms) and the WAITING_FOR_REMOTE_KVS round trip (~3 ms) add ~7 ms to every repeat
  request; at 16k vLLM alone recomputes 16 tokens (its 16-token block tail) where LMCache's chunk covers all but one, so
  there the two paths cross (39.9 vs 35.3 ms).
- The SSD tier through the page cache (the files just written were still in the 755 GiB of DRAM) costs 22–160 ms; here
  the L2→L1 prefetch happens inside the lookup phase (lookup 3.8 ms at 256 tokens → 63 ms at 16k, a CPU copy at
  ~10 GB/s) and is followed by the same GPU transfer. Note that with an L2 the lookup prefetches the whole prompt from L2
  **even when vLLM's GPU cache holds it** (the `gpu` case: +50 ms of lookup at 16k), because the lookup runs before vLLM
  decides what it needs.
- **SSD hit with O_DIRECT (`a-3b-ssd-odirect`, the real NVMe path):** 24.3 ms at 256 tokens, 37.5 at 1k, 68.8 at 2k,
  110 at 4k, 170 at 8k, 318 ms at 16k — i.e. 3.4× a DRAM hit at 4k and 3.7× at 16k, still 11× faster than recompute at
  16k. The extra time is the L2→L1 prefetch inside the lookup phase: 16 ms at 1k, 58 at 4k, 114 at 8k, 220 ms at 16k =
  **2.7 GB/s from the NVMe** (604 MB at 16k; the device's O_DIRECT read rate measured 2.6–2.9 GiB/s on 2026-10-07), followed
  by the unchanged 12 GB/s GPU transfer. The same prefetch also delays GPU-prefix hits (25 → 288 ms from 256 to 16k
  tokens) and, in this run, the "cold" prompts: the fs L2 directory is persistent and the run reused the seeds of the
  page-cache run, so its `cold` cases were SSD hits from a cold L1 and GPU (37–306 ms, n = 8 per L, the same stages); the
  harness now uses one directory per run (deleted at stop) and a clean rerun is queued. The `host` rows are unaffected
  (the prompt was on disk, not in L1 or in the GPU, in both runs).
- Repetitions agree within 1–2 ms on the 3B model (min–max in Table A-1) except sporadic tail events: in the 1.5B run 7
  of 112 hit requests took 160–400 ms, attributed by their time lines to a lookup that took 120–300 ms (5 cases), a
  finished load noticed by the scheduler 130 ms late (1) and a single-token step of 166 ms (1); the 3B runs show 0–2
  such events per 112 (max 84 and 105 ms). They are recorded in `A/*-timeline.csv`, not explained.

**Explanation / what CXL changes (PREVIOUSLY MEASURED).** The host-hit cost is the PCIe link plus fixed scheduling costs;
the host tier's own read speed does not appear because the link is 12 GB/s and the GPU reads a CUDA-registered CXL devdax
mapping at the same 12.48 GiB/s as pinned DRAM (`2026-10-07-read-cost.md`, 1 GiB copies, 10 repetitions within 1%), the
3B-AWQ DRAM-vs-devdax microbenchmark of 2026-10-18 found the same TTFT (58–67 ms from devdax vs 79–121 ms from DRAM for
7.7k tokens in eager mode, both within the noise of the floor), and the 2026-10-11 replay with a pure devdax L1 was
indistinguishable from DRAM (hits 0.080 vs 0.080, paired TTFT within ±0.04 s). On this platform a CXL KV hit therefore
costs what a DRAM hit costs; what CXL adds is capacity at that cost (Experiment D) — and on the CPU side a 1.7× slower
dependent read and 51 vs 280 GiB/s of streaming bandwidth, which the GPU path does not exercise. Where a faster link
(PCIe 5.0 ×16, ~50 GB/s) exists, the CXL pair's ~50 GiB/s read ceiling would become the limit for concurrent loads
(Experiment E); that regime cannot be measured here.

## 4. Experiment B — concurrent serving and scheduling behaviour (MEASURED 2026-11-04, `B/`, tables `B/tables-b.md`, figures `B/figs/`)
**Why.** One request shows what a hit costs; it does not show whether the scheduler lets a hit *use* its advantage when
other requests are present: whether loads overlap compute, whether loaded requests are served promptly, and where a
hit's time goes under load.

**How.** `run_b.py`: 3B-AWQ, CUDA graphs, L1 40 GB DRAM, `max_num_seqs` 16, chunked prefill with vLLM's default budget of
2048 tokens per step, 32 output tokens per request. A pool of 64 prompts (16 each of 1k / 2k / 4k / 8k tokens) is stored
once; the scenarios draw "host" requests from the pool and "cold" requests from fresh prompts; the tier that actually
served each request is classified afterwards from vLLM's `cached_tokens` and LMCache's retrieve bytes (`host` = more than
one chunk retrieved, `gpu` = vLLM's own prefix cache, `cold` = nothing cached). Scenarios, identical in every
configuration: **s0** the four-request burst of the brief (A = 8k host hit, B = 1k GPU hit, C = 4k cold, D = 4k host hit,
5 ms apart, three orders, 5 repetitions); **s1** closed loop at concurrency 1 / 2 / 4 / 8 / 16 over the same 64-request
sequence (50 % pool hits / 50 % cold, lengths 1k–8k); **s2** open loop (Poisson) at 0.5 / 1 / 2 / 4 req/s over the same
96-request sequence; **s3** bursts of 4 / 8 / 16 simultaneous requests. Configurations: default (asynchronous load,
eager prefetch off, 1 transfer thread), eager prefetch, 4 transfer threads, priority scheduling with hits first / cold
first (vLLM's `--scheduling-policy priority`, the request's `priority` field set by the client), prefill chunk 512
(`--max-num-batched-tokens 512`), synchronous scheduling (`--no-async-scheduling`), vLLM alone, and the default without
the GPU sampler (the idle-GPU penalty of §1.2 under light load). Two caveats: in s3 most pool prompts had already been
evicted by LRU (the run's stores exceed the 32 GB watermark of the 40 GB L1 by then), so s3 is a mostly-cold burst with a
few hits (the per-request tier is known, the mix is just not the intended 50 %); a first run whose s1/s2 cold prompts were
re-used across levels is kept in `B/flawed/` and not used.

**Result, default configuration (Table B-1 / B-2, Figures B1–B5).**
- *Alone (s1, concurrency 1; s2 at 0.5 req/s)* a host hit costs 34 / 54 ms p50 against 319 / 653 ms for a cold request of
  the same length mix, a GPU hit 22 ms: the single-request picture of §3.
- *Under load the hit's advantage disappears in TTFT terms.* Closed loop at concurrency 2 / 4 / 8 / 16: host hits 363 /
  766 / 1,879 / 3,428 ms p50 against cold 329 / 731 / 1,519 / 3,159 ms — the hit is no faster than a recompute of the
  same length, although its GPU work is one token. Open loop at 1 / 2 / 4 req/s: host 263 / 640 / 6,134 ms vs cold 652 /
  995 / 5,420 ms (at 4 req/s the server is overloaded: GPU busy 1.0, 2.8 req/s completed). In the four-request burst
  every order gives the two host hits 720–780 ms and the GPU hit 690–780 ms, i.e. the TTFT of the cold request (650 ms)
  plus one step.
- *Where the time goes (Table B-2, Figure B4).* The transfer itself is short and does overlap compute: 16 / 39 / 318 ms
  at concurrency 2 / 4 / 16 (the last one queues behind other loads on the single transfer thread). What the hit waits
  for is (i) **load done → noticed**: the worker reports finished loads only when an engine step ends, and under load the
  steps are 2048-token prefill chunks of other requests (300–600 ms each); the "load wait" (allocation → noticed) is
  309 / 357 / 1,415 ms at concurrency 2 / 4 / 16 for a 16–318 ms transfer; (ii) **queued → load start**: the waiting-queue
  scan stops when the step's token budget is spent (`scheduler.py:887 ff.`), so a request behind a cold prefill is not
  even looked up until that prefill has consumed its chunks: 12 / 21 / 1,206 ms at concurrency 2 / 4 / 16, 350 ms at
  2 req/s, 646 ms in the CADB order of the burst (A and D sit behind C); (iii) with asynchronous scheduling the load is
  submitted when the step in which the request was considered *executes*, one step later (the cyan segments of Figure
  B4: 360 ms in the DCBA order). "KV ready → scheduled" is 0.1 ms: once noticed, a loaded request is scheduled at the
  very next step (kv-holding requests go first), but its single token then shares that step with other requests'
  prefill chunks, so "scheduled → first token" is 21 / 37 / 295 ms instead of 10 ms.
- *Ordering matters only through those mechanisms.* The cold request's TTFT is the same in all three burst orders
  (651–656 ms); the hits pay 70–130 ms more when they are behind it (CADB) than ahead of it, because their lookup starts
  later, not because the GPU is busier.
- *GPU utilization.* Engine steps with tokens cover 1.0 of the wall time from concurrency 2 on (0.3–0.5 at 0.5–1 req/s);
  NVML's coarse utilization agrees (0.9–1.0). Retrieval never left the GPU idle; the idle time at low load is the
  arrival process.
- *Throughput.* 1.5 / 1.9 / 2.1 / 2.3 / 2.4 completed requests/s at concurrency 1 / 2 / 4 / 8 / 16 (5.8 → 9.4 k prompt
  tokens/s); open loop completes the offered load up to 2 req/s and 2.8 of 4 req/s.
- *Lookup latency under load* is a further cost not visible alone: 1.3 ms for a single request, 9–37 ms median at
  concurrency 2–16, 10 ms at 1 req/s but 295 ms at 2 req/s, and 31–340 ms in the four-request bursts (LMCache's lookup
  pool has one CPU worker by default, and lookups queue behind the stores of the running prefill).
- *Frontend.* client → engine queue is 3–9 ms median up to 1 req/s (means 27–85 ms: a few requests wait behind the
  API-server process's streaming of other requests' tokens), 66 ms median at 2 req/s and 158 ms when overloaded.

**Configurations.** (Table B-1 / B-2; filled as the chain completes.)
- *Eager prefetch* (lookup at arrival): no change at any level (host p50 within ±15 ms of the default except
  concurrency 4: 448 vs 766 ms, where the earlier lookup lets some loads start before the budget runs out). The lookup
  moves to arrival, but the load still starts only when the scheduler reaches the request and is still noticed at a
  step boundary.
- *Four transfer threads*: no change (transfers were never the wait).
- *Priority scheduling, hits first* (vLLM's own `--scheduling-policy priority`; the client marks pool requests priority 0
  and cold requests 1; no code change): no effect up to concurrency 2 / 2 req/s, then the host hits' TTFT p50 falls
  from 766 to 433 ms at concurrency 4, 3,428 → 1,967 ms at concurrency 16 (p95 8,235 → 4,273), 6,134 → 3,079 ms in the
  overloaded 4 req/s run and 3,419 → 2,084 / 2,848 → 1,973 ms in the 8- / 16-request bursts, while the cold requests
  lose 2–15 % (3,159 → 3,648 ms at concurrency 16). Table B-2 shows what changed: "queued → load start" drops from 1,206 to
  34 ms at concurrency 16 and from 4,430 to 1,150 ms at 4 req/s — the hits are now considered before the budget is spent,
  so their lookups and loads start at once — but "load done → noticed" stays at 1.0–1.3 s and "scheduled → first token"
  grows to 0.4–0.7 s, because the loaded hit still has to wait for the running prefill chunks and then shares its step
  with them. Ordering removes the scan problem, not the step-granularity problem.
- *Prefill chunk 512* (`--max-num-batched-tokens 512`, steps of ≤ 512 tokens ≈ 80 ms): the step-granularity wait
  shrinks as expected — "load done → noticed" 309 → 62 ms at concurrency 2, 1,415 → 443 ms at concurrency 16, 1,017 →
  501 ms at 4 req/s — and the hits gain where that wait dominated (concurrency 2: 363 → 180 ms; the ABCD burst 723 →
  699 ms). But the smaller budget also stops the queue scan sooner, so "queued → load start" grows (1,206 → 3,013 ms at
  concurrency 16, 4,430 → 5,753 ms at 4 req/s), the per-step overhead costs 7–8 % of throughput (9.4 → 8.6 k prompt
  tokens/s at concurrency 16, 2.75 → 2.56 req/s at 4 req/s), and at high load the hits end up worse (3,428 → 4,978 ms
  at concurrency 16; 640 → 1,437 ms at 2 req/s). The two waits trade against each other through the token budget; the
  combination hits-first + chunk 512 is queued.
- *Priority, cold first* (the mirror image): hits lose (6,134 → 7,636 ms at 4 req/s, 2,848 → 5,159 ms in the 16-request
  burst), cold requests gain 5–13 % (3,159 → 2,742 ms at concurrency 16); no change at light load. Together the two
  priority runs show that under load the order in which the waiting queue is scanned decides which class pays the
  scan-and-budget wait; the total work does not change.
- *vLLM alone (no host cache, `b-none`)*: every pool request is a recompute. Open loop at 1 req/s: TTFT p50 1,541 ms
  against 652 ms with the DRAM tier (cold requests 1,551 vs 652: the hits' absence also delays the cold ones); at
  2 req/s vLLM alone is overloaded (1.5 req/s completed, TTFT 12.9 s) where the cached server keeps up (2.1 req/s,
  942 ms). Closed loop: 1.5 completed requests/s at concurrency 8–16 (6.0 k prompt tokens/s) against 2.3–2.4 (9.2–9.4 k)
  with the cache — the host tier adds ~55 % of capacity on this 50 % mix — but the TTFT quantiles at concurrency 16 are
  *lower* without the cache (2,259 vs 3,336 ms p50): in a closed loop the faster completions of the hits keep 16
  requests in flight with more cold prefill among them at any time, and the hits themselves wait a full chunk step.
  The end-to-end benefit of the host tier shows in capacity and in open-loop TTFT, not in closed-loop TTFT quantiles.
- *Default without the GPU sampler* (`b-default-nosamp`, s2 / s3 only): within noise of the instrumented default
  (host 52 vs 54 ms at 0.5 req/s, 265 vs 263 at 1 req/s, 640 vs 640 at 2 req/s): at ≥ 0.5 req/s the GPU is never idle
  long enough for the §1.2 penalty.

**Explanation.** The existing scheduler does what §1.1 says: it overlaps loads with compute and never blocks the GPU on a
load. The waits come from three design points that are independent of CXL or of the tier: load completion is sampled
at step granularity, the queue is scanned in arrival order only as far as the token budget reaches, and the step that
finally serves a loaded request is shared with chunks of other requests' prefill. With a 2048-token prefill chunk at
0.14 ms/token each of these is a few hundred milliseconds — the same order as recomputing a 2–4k prompt, which is why
hits stop being faster than misses once the GPU is busy. These are generic serving-scheduler issues (Q4 of §13: they
would exist with a DRAM-only host cache; CXL only makes more requests hit).

## Change history
- 2026-11-04 — file created with the environment and source inspection; experiments started.
