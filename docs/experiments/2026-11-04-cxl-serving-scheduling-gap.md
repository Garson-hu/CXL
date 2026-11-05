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
  on the load path; the server has **one** GPU transfer thread by default (`--max-gpu-workers 1`), and more threads do
  not help a single engine: STORE / RETRIEVE requests are routed by an affinity key that is the ZMQ identity of the
  requesting worker process (`mq.py:571–574`, `affinity_pool.py`), so all transfers of one GPU worker are serialized
  on one thread and one CUDA stream whatever the pool size (confirmed in Experiment E: 4 threads = 1 thread to the
  millisecond).
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

### 1.3 Operational notes
- 2026-11-04 20:55: the home directory hit its 40 GB quota (not this study's data: 0.6 GB; the rest is older
  content of the account). The `b-noasync` run was truncated and every queued run failed instantly for 2 minutes; the
  study's results directory was moved to `/mnt/local/ghu4/results/2026-11-04-cxl-serving-scheduling-gap` and
  symlinked from `experimental_results/`, the truncated run archived in `B/flawed/`, and the queue restarted (part 3)
  with the same runs. Which runs were affected is visible in `queue.txt` and the experiment matrix.

## 2. Experiments (plan; results are appended per family as they close)
| family | question | status |
|---|---|---|
| A single-request retrieval cost | TTFT and its stages for cold / GPU hit / DRAM hit / SSD hit / vLLM alone, L = 256 … 16,384 | done (§3) |
| B concurrent serving and scheduling | controlled mixes and real-trace windows; default vs eager prefetch vs 4 transfer threads vs priority ordering vs prefill chunk 512 vs synchronous scheduling vs vLLM alone | controlled mixes done (§4); real-trace configurations running (a first `b-default` run whose s1/s2 sequences re-used their cold prompts across levels is kept in `B/flawed/`, not used) |
| C scheduling gap | calibrated offline reference (zero-delay, clairvoyant resource-constrained) vs measured | done (§6) |
| D capacity | L1 sweep (DRAM; CXL blocked) + SSD-backed + recompute-only on trace replays; offline trace reuse vs capacity | conversation and tool-agent sweeps at 0.08× done (§7.2, §7.2b, admission analysis §7.2c; `d-tool-dram2` re-run queued), lighter-load 0–200 s sweep queued (§7.3) |
| E concurrent retrieval bandwidth | k simultaneous hits, PCIe RX, per-request retrieve time, transfer threads | done (§5) |
| F workload sensitivity | both traces, controlled variations | queued |

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
- *Synchronous scheduling* (`--no-async-scheduling`; vLLM enables async scheduling by default): the hits improve at every
  level, modestly — the four-request burst 723 → 684 / 777 → 752 / 735 → 674 ms, concurrency 8: 1,879 → 1,560 ms,
  concurrency 16: 3,428 → 2,800 ms (cold 3,159 → 2,223), 2 req/s: 640 → 611 ms — at no throughput cost in this regime
  (completed requests/s within 1–2 % of the default: the CPU-side work that async scheduling hides is small next to
  300-ms prefill steps). Table B-2: "load done → noticed" 407 → 48 ms in the ABCD burst and 1,415 → 689 ms at
  concurrency 16, and "scheduled → first token" 21–295 → 12–60 ms, because a step is now planned with the loads that
  have actually finished and the load of a request is submitted in the step that considered it, not one later.
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

## 5. Experiment E — concurrent KV retrieval (MEASURED 2026-11-04, `E/`, figures `E/figs/`)
**Why.** Hits that arrive together load together; the question is which resource bounds concurrent retrieval on this
platform — the host memory, the PCIe link, LMCache's transfer path, or the SSD — and what that does to TTFT.

**How.** `run_e.py`: 3B-AWQ, L1 40 GB DRAM (or the fs L2 on the NVMe with O_DIRECT), 16 host-resident prompts of 4k and
8k tokens (151 / 302 MB of KV each); the GPU cache is flushed, then k ∈ {1, 2, 4, 8, 16} of them are requested at once
(e1, 4 bursts per point, 4 output tokens); e2 adds k cold 4k prompts to k 8k hits; e3 sends k hits with 1 or 64
output tokens. Configurations: 1 and 4 server transfer threads, the SSD tier, and the default without the GPU sampler.

**Result.**
- *DRAM, one engine: loads serialize on one thread and one stream.* k = 1 / 2 / 4 / 8 / 16 hits of 8k tokens: TTFT p50
  51 / 100 / 158 / 256 / 428 ms, max 51 / 103 / 199 / 372 / 719 ms; the last request of a 16-burst gets its KV 573 ms
  after allocation. The per-request transfer interval (retrieve start → end on the stream) grows from 25 to 40 ms
  because the transfer kernels queue on the server's stream; bytes over the span from the first start to the last end
  give 11.9 / 10.1 / 8.7 / 8.0 / 7.7 GB/s — the link is not saturated by a burst, the serialization leaves gaps
  (lookup, per-request submission, the step-boundary notice between loads). 4k tokens: 35 / 77 / 105 / 157 / 257 ms.
- *Four transfer threads: identical to one* (every number within 1 ms), for the reason given in §1.1 (affinity routing
  by worker identity). Only a multi-engine server would use more threads.
- *SSD tier (O_DIRECT)*: the L2→L1 prefetch that runs inside the lookup serializes on the NVMe: 110 / 199 / 392 / 776 /
  1,453 ms for k = 1 … 16 hits of 8k (4.8 GB in 1.45 s = 3.3 GB/s, the device's rate), TTFT p50 160 / 298 / 533 / 984 /
  1,536 ms; 4k: 89 / 175 / 287 / 538 / 743 ms. Concurrent SSD hits are device-bandwidth-bound; beyond k ≈ 2 an 8k hit
  from the SSD costs more than a quarter of its recompute (1.43 s).
- *Loads beside prefill (e2)*: k 8k hits + k 4k cold prompts at once: the hits' TTFT is 702 / 1,355 / 1,692 / 1,759 ms
  for k = 1 / 2 / 4 / 8 (cold: 660 / 1,333 / 2,347 / 3,513 ms) — the §4 step-boundary wait again: the hits' loads finish
  in tens of ms but are served only after the cold prefill chunks that are running (one chunk per 4k prompt per step).
- *Loads beside decode (e3)*: k = 4 / 8 hits with 64 output tokens instead of 1: TTFT 155 / 214 ms instead of 69 / 86 ms,
  because the loads are noticed at the boundaries of the decode steps of the requests already running (≈ 20–30 ms
  each at this batch size) and the hits join a step that also decodes.
- *Without the GPU sampler*: 52 / 103 / 159 / 257 / 430 ms for k = 1 … 16 (8k) against 51 / 100 / 158 / 256 / 426 ms —
  the bursts follow the flush within 0.5 s, so the idle-GPU penalty of §1.2 does not appear.
- *CPU staging*: none on this path (the transfer kernel reads the pinned objects directly); the LMCache server's CPU time
  per retrieved GB is in `E/*-cpu.txt` (P lines) — the lookup and bookkeeping, not a copy.

**Explanation.** On this platform the bound for concurrent DRAM hits is not host memory bandwidth (the DRAM side can feed
> 200 GiB/s) nor the PCIe link (12 GB/s, reached by a single load) but the serialization of transfers per engine in
LMCache and the step-granular hand-over to vLLM; for the SSD it is the device (≈ 3 GB/s). A CXL tier would sit between
the two: its ~50 GiB/s read ceiling (2026-10-07) is above the link, so on this host it would behave exactly like DRAM
for the GPU path; on a host whose link is faster than the CXL pair, concurrent hits would hit the CXL ceiling before
the link — a regime this machine cannot show.

## 6. Experiment C — scheduling gap analysis (SIMULATED reference, calibrated and validated on the measured runs; `C/`, figures `C/figs/`)
**Why.** The waits of §4 are measured; whether removing them is worth a system needs a bound: how much TTFT would a
scheduler with the same resources recover, and which decision accounts for the difference.

**How.** `sched_sim.py` replays each measured request sequence (arrival instants, prompt lengths, tier served, bytes)
through a discrete-event model of one engine: steps of at most 2048 prefill tokens with the measured per-token cost
(r₀ = 0.139 ms, r₁ = 8.2 ns/token², fitted within 1 % on the cold requests of §3), the measured 10.2 ms minimum step,
decode cost per sequence from the engine-step log (1.26 ms per sequence per step), a single transfer channel at the
measured 11.9 GB/s with the measured lookup (1.3 ms) and hand-over (3.2 ms), loads noticed only at step boundaries,
at most 16 running sequences. Policies: **vllm** = the inspected scheduler (arrival order with loaded requests first,
the queue scan stops when the token budget is spent, loads submitted one step late as async scheduling does);
**vllm_sync** and **vllm_hits** mirror the measured synchronous and hits-first configurations; **vllm_scanall** lets the
scan continue past the budget (loads start for every waiting request); **vllm_early** additionally submits loads at
once; **zero** = instantaneous loads (ZERO-DELAY reference, not implementable); **hits** = hits before cold without the
scan limit; **srpt** = CLAIRVOYANT shortest-remaining-prefill-first (needs the future; the mean-TTFT-optimal order for
one server). Objective reported: mean and p95 TTFT; constraints: the GPU, the one transfer channel, the step
granularity, 16 sequences.

**Validation (the measured configuration against its model variant, mean TTFT, `C/c-summary.csv`).** Default: measured
969 / 3,477 / 997 / 1,116 / 2,383 ms vs model 711 / 3,115 / 899 / 992 / 2,227 ms at concurrency 4 / 16, 1 / 2 req/s, 8-burst
(−27 / −10 / −10 / −11 / −7 %; per-request error median −30 to −240 ms, p90 |error| 330–1,430 ms ≈ one prefill chunk).
Synchronous: 901 / 2,982 / 955 / 1,081 / 2,333 vs 698 / 2,619 / 877 / 936 / 2,096 ms (−23 … −8 %). Hits-first: 874 / 3,073 /
962 / 1,069 / 2,069 vs 665 / 2,599 / 816 / 943 / 2,072 ms (−24 … 0 %). The model reproduces the direction and most of the size
of every configuration effect and is 7–27 % optimistic (it has no lookup queueing, no frontend delay and no decode-batch
inefficiency); the reference gains below carry that bias.

**Result (default sequence and arrivals, mean / p95 TTFT in ms; Figures C1–C3).**
| load | measured | model of the existing scheduler | scan past the budget | + loads at once | zero-delay loads | hits first (no scan limit) | clairvoyant SRPT |
|---|---|---|---|---|---|---|---|
| concurrency 4 | 969 / 1,850 | 711 / 1,611 | 692 / 1,591 | 690 / 1,591 | 552 / 1,593 | 690 / 1,591 | 690 / 1,591 |
| concurrency 8 | 1,623 / 4,606 | 1,322 / 4,468 | 1,179 / 3,150 | 1,155 / 3,154 | 1,181 / 3,192 | 1,108 / 3,159 | 1,050 / 2,948 |
| concurrency 16 | 3,477 / 8,234 | 3,115 / 6,702 | 2,404 / 6,152 | 2,367 / 6,152 | 2,795 / 6,416 | 2,215 / 6,152 | 1,817 / 5,132 |
| 1 req/s | 997 / 3,440 | 899 / 3,107 | 795 / 2,499 | 755 / 2,501 | 786 / 2,841 | 720 / 2,321 | 648 / 1,742 |
| 2 req/s | 1,116 / 2,661 | 992 / 2,652 | 844 / 2,002 | 821 / 2,002 | 850 / 2,000 | 809 / 2,002 | 809 / 2,002 |
| 4 req/s (overload) | 5,547 / 10,883 | 4,694 / 8,935 | 3,443 / 8,794 | 3,349 / 8,787 | 4,359 / 8,648 | 2,893 / 8,839 | 1,869 / 10,382 |
| burst of 8 | 2,383 / 4,244 | 2,227 / 4,458 | 1,922 / 4,038 | 1,881 / 4,041 | 1,953 / 4,460 | 1,881 / 4,041 | 1,629 / 3,688 |
| burst of 16 | 3,801 / 7,569 | 3,499 / 7,224 | 2,668 / 7,309 | 2,644 / 7,309 | 3,126 / 7,261 | 2,529 / 7,139 | 2,038 / 6,003 |

- *Which decision accounts for the gap.* At concurrency 16 the model's mean TTFT falls 23 % when the scan continues
  past the budget (every waiting hit's load starts at its first step), 1 % more when loads are submitted at once, and
  only 10 % with instantaneous loads under the existing scan — **the budget-limited scan is the larger of the two
  load-side problems, the load latency itself the smaller**. Ordering adds the rest: hits first 29 %, clairvoyant SRPT
  42 % (60 % under overload, where it also raises p95 by starving long cold prompts).
- *At light load there is nothing to recover*: ≤ 0.5 req/s or concurrency ≤ 2 the references are within 1–5 % of the
  existing scheduler (hits are served from an idle GPU already).
- *The measured knobs sit where the model puts them*: synchronous scheduling ≈ the "+ loads at once" column
  (measured −14 % at concurrency 16), hits-first priority ≈ the "hits first" column for the hits (measured −43 % for the
  hits, −12 % overall).

**Explanation.** The opportunity is real but bounded: 20–40 % of mean TTFT at high load from two scheduler decisions
that are independent of the memory tier (scan the whole queue for loads; serve loaded requests without waiting for a
chunk boundary), nothing at light load, and the clairvoyant bound is only ~20 points further. None of it needs CXL; all
of it applies to any host tier that makes hits frequent. The reference is a model with a stated 7–27 % optimism, not a
measurement.

## 7. Experiment D — host-cache capacity on trace replays (MEASURED 2026-11-04/05, `replay/`, table `replay/tables-d.md`, figures `replay/figs/`; TRACE ANALYSIS `replay/trace-reuse.csv`)

**Why.** Q3 asks whether more host-tier capacity — the resource CXL adds — moves the serving bottleneck. Capacity acts only
through the hit share it buys, so the family has two halves: what prefix reuse the traces *offer* at each capacity (an
offline property of the trace: TRACE ANALYSIS, §7.1) and what the measured server *makes* of those hits (MEASURED replay,
§7.2–7.3). CXL DAX is blocked (root 0600 since 2026-10-18, §1.3), so capacity is pinned DRAM standing in for CXL. PREVIOUSLY
MEASURED on this node: the GPU reads a CXL-backed and a pinned-DRAM buffer at the same 12.5 GiB/s (2026-10-07), and a
DAX-backed LMCache L1 gave the same TTFT as a DRAM one (2026-10-11, 2026-10-18), so the capacity axis transfers to CXL; the
host-side interference axis (CXL writes on the reader's CCD; cxlpath, Phase 3) is not represented here.

**How.** `replay.py` replays trace seconds 0–100 of the Mooncake conversation window (291 requests, 3.34 M prompt tokens;
prompt p50 8.8 k, p90 27.7 k tokens; output p50 398 tokens, 0.7 % capped at 1,024) and of the tool-agent window (544
requests) at 0.08× speed (1,250 wall s; 0.22 req/s and 2.56 k offered prompt tokens/s for the conversation trace), prompts
cut at `max_model_len − output − 8` (≈ 31.7 k), requests that share a quantized timestamp spread over their second; each
512-token hash block of the trace becomes a fixed pseudo-random token sequence, so shared blocks are shared prefixes.
Configurations: DRAM L1 2 / 5 / 10 / 20 / 40 / 80 GB (LMCache LRU, watermark 0.8), SSD-backed (10 GB L1 + fs L2 on the
local NVMe, O_DIRECT, `skip_l1` store policy), vLLM alone (`tier=none`: recompute). Server settings as in B: 3B-AWQ, CUDA
graphs, `max_num_seqs` 16, `max_model_len` 32,768, GPU memory utilisation 0.85 → GPU KV cache 121,792 tokens (3.7
full-length requests), chunked prefill 2,048, async scheduling, the logging-only hooks and the GPU / CPU samplers.
`trace_reuse.py` runs an LRU over 512-token hash blocks with prefix semantics (a request's hit is its longest prefix all
of whose blocks are cached; the request's blocks are then inserted) for the replayed 0–100 s windows, the 0–200 s windows
of the lighter-load sweep (§7.3) and the full hour, at 36 KiB/token (the 3B-AWQ's KV size); one block = 18.9 MB.

### 7.1 What the traces offer (TRACE ANALYSIS, figure D0, `replay/trace-reuse.csv`)
Reusable share of prompt tokens under an LRU of the given capacity (GB of KV at 36 KiB/token; 4.5 GB = the GPU KV cache
of this configuration):

| trace, window | requests | prompt tokens | 2 GB | 4.5 GB | 20 GB | 80 GB | 160 GB | 320 GB | 640 GB | unbounded |
|---|---|---|---|---|---|---|---|---|---|---|
| conversation 0–100 s | 291 | 3.3 M | 0.045 | 0.045 | 0.045 | 0.085 | 0.093 | 0.093 | 0.093 | 0.093 |
| conversation 0–200 s | 599 | 6.9 M | 0.045 | 0.045 | 0.051 | 0.116 | 0.181 | 0.183 | 0.183 | 0.183 |
| conversation 0–3,600 s | 12,031 | 123 M | 0.050 | 0.050 | 0.055 | 0.126 | 0.226 | 0.309 | 0.370 | 0.383 |
| tool-agent 0–100 s | 544 | 4.6 M | 0.300 | 0.325 | 0.333 | 0.363 | 0.369 | 0.369 | 0.369 | 0.369 |
| tool-agent 0–200 s | 1,159 | 9.8 M | 0.317 | 0.343 | 0.355 | 0.400 | 0.446 | 0.447 | 0.447 | 0.447 |
| tool-agent 0–3,600 s | 23,608 | 185 M | 0.350 | 0.380 | 0.388 | 0.435 | 0.503 | 0.558 | 0.593 | 0.595 |

Three facts. (i) The reuse a GPU-sized cache already captures is 4.5 % of prompt tokens on the conversation trace and
32–38 % on the tool-agent trace (consecutive turns and tool calls arrive within seconds of each other); everything a host
tier adds is reuse at a longer distance. (ii) That capacity-sensitive reuse is a long-distance phenomenon: over the full
hour the conversation trace grows from 5 % at GPU size to 13 % at 80 GB, 23 % at 160 GB, 31 % at 320 GB and 37 % at
640 GB — the knee lies at 100–600 GB for this 3B model, i.e. at 1–5 TB for a 70B fp16 model whose KV is ~9× larger per
token — and the tool-agent trace from 38 % to 43 / 50 / 56 / 59 %. The hour of the conversation trace produces 4.5 TB of
KV at 36 KiB/token, so even c28's 1.06 TiB of CXL holds a quarter of it. (iii) A 100-s replay window cannot show this:
within 100 s the conversation trace holds 9.3 % reusable tokens in total (8.5 % at 80 GB) and the tool-agent trace
36.9 % (36.3 % at 80 GB); a 200-s window shows part of the effect (conversation 4.5 → 18.1 % at 160 GB, tool-agent 34 →
45 %). The 0.08× replays below are therefore measurements of what the server does with few host hits, not of the capacity
effect itself; that is the reason for the lighter-load 200-s sweep of §7.3 (queued 2026-11-05 00:50, `queue_i2.sh`,
replacing the 0–50 s mini-sweep planned the evening before, which the table shows would have had no capacity signal).

### 7.2 Measured sweep, conversation trace at 0.08× (figures D1–D4, `replay/tables-d.md`)
| run | cached share (host / GPU) | TTFT p50 / p95 / p99 (s) | hit ≥ 50 % TTFT p50 (s) [n] | miss TTFT p50 (s) [n] | request time p50 (s) | computed tok/s | KV host→GPU / GPU→host (GB) | evicted chunks | L1 max (GB) | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| d-conv-dram2 | 0.044 (0.000 / 0.044) | 16.0 / 48.6 / 56.3 | 12.9 [28] | 16.8 [195] | 43.8 | 2,445 | 0.0 / 77.4 | 8,043 | 1.9 | 0.88 | 26 |
| d-conv-dram5 | 0.044 (0.000 / 0.044) | 16.1 / 48.5 / 56.3 | 12.9 [28] | 16.7 [195] | 42.9 | 2,445 | 0.0 / 77.6 | 7,784 | 4.4 | 0.88 | 26 |
| d-conv-dram10 | 0.044 (0.000 / 0.044) | 16.0 / 48.5 / 56.2 | 12.9 [28] | 16.8 [195] | 43.3 | 2,445 | 0.0 / 77.5 | 7,406 | 8.7 | 0.88 | 26 |
| d-conv-dram20 | 0.044 (0.000 / 0.044) | 16.0 / 48.5 / 56.3 | 12.9 [28] | 16.7 [195] | 43.3 | 2,445 | 0.0 / 77.5 | 6,528 | 17.3 | 0.88 | 26 |
| d-conv-dram40 | 0.048 (0.004 / 0.044) | 16.1 / 47.3 / 54.6 | 17.5 [32] | 16.1 [194] | 42.9 | 2,440 | 0.5 / 77.8 | 5,085 | 34.6 | 0.88 | 26 |
| d-conv-dram80 | 0.073 (0.029 / 0.044) | 14.3 / 42.8 / 48.5 | 16.9 [39] | 15.0 [186] | 36.0 | 2,396 | 3.5 / 79.1 | 1,454 | 68.4 | 0.88 | 23 |
| d-conv-ssd (10 GB L1 + NVMe L2) | 0.058 (0.013 / 0.044) | 14.5 / 44.5 / 53.2 | 12.9 [33] | 15.6 [191] | 37.4 | 2,420 | 1.6 / 102.8 | 11,659 (L1) | 0.7 | 0.88 | 24 |
| d-conv-none (vLLM alone) | 0.044 (0.000 / 0.044) | 15.6 / 47.5 / 55.1 | 12.8 [28] | 16.3 [195] | 42.7 | 2,448 | 0 / 0 | 0 | – | 0.88 | 26 |

All 291 requests of every run completed (no errors). "GPU busy" is the union of engine steps with tokens over the window;
"computed tok/s" counts prompt tokens that were neither GPU- nor host-cached; "KV GB" are the LMCache retrieve / store
event bytes (the raw PCIe counters carry a ~30 GB per-direction baseline from vLLM itself, §1.3).

**Result.** The server is overloaded at this speed: GPU busy share 0.88 in every run, backlog up to 26 requests against
16 decode slots, TTFT p50 16 s / p99 56 s, queue → scheduled p50 10–11 s. Capacity does nothing up to 40 GB, because the
window offers no reuse beyond what the GPU prefix cache already serves (host share 0.000–0.004; the 4.4 % cached share
is identical in the vLLM-alone run). At 80 GB the host tier serves 2.9 % of the prompt tokens (3.5 GB retrieved over the
window) and removes 2 % of the prefill work (2,396 vs 2,445 computed tok/s); TTFT p50 falls 11 % (16.0 → 14.3 s), p95
12 %, p99 14 %, and request completion time p50 falls 17 % (43 → 36 s) — far more than the 2 % of work removed, because
a saturated queue amplifies small reductions of service demand. The SSD-backed configuration lands in between (host
share 1.3 %, TTFT p50 14.5 s): its NVMe L2 never evicts (the 11,659 evictions are from the 10 GB L1), so it finds more
hits than 40 GB of DRAM, and at this load O_DIRECT reads at 2.7 GB/s are not the limit. The host tier's cost is visible
as well: with no hits to serve (≤ 40 GB) the LMCache configurations are 2.5 % slower in TTFT p50 than vLLM alone
(16.0 vs 15.6 s) while storing 77 GB of KV to the host over the window (103 GB in the SSD configuration). Hit requests
do not get a shorter TTFT than misses under this load: in the 80 GB run the 39 requests with ≥ 50 % prefix hits have
TTFT p50 16.9 s against 15.0 s for the 186 misses, whereas GPU-prefix hits do (12.9 vs 16.8 s in every run, vLLM alone
included). Run-to-run reproducibility is good: the four configurations without host hits agree within 0.4 % in TTFT p50
and 1 % in p99 (same offered sequence, same GPU work).

**Explanation.** Two mechanisms, both visible in the step log (`*-steps.csv`). First, the server is bound by GPU KV-cache
capacity, not by compute or by `max_num_seqs`: whenever requests are waiting, 5–11 sequences are running (p50 8, never
16), because 121,792 tokens of KV hold about ten sequences of 11 k prompt + output tokens. A host-tier hit must reserve GPU blocks for its
whole prefix before its load is issued and is not admitted until they are free at once (§7.2c: in this run the 11
host-dominant hits wait 22.9 s p50 from queueing to scheduling against 11.3 s for GPU-prefix hits and 10.6 s for misses,
10.3 s of it between the lookup result and the load), so it neither raises concurrency nor gets in early; a GPU-prefix
hit's blocks are resident and it needs new blocks only for its uncached tail — that is why GPU hits see a lower TTFT and
host hits do not. Second, under overload the TTFT is queueing time (10 of
16 s), first-come-first-served and independent of whether the request has a hit, consistent with B (§4) and C (§6): the
scheduler consults the host tier only when a request reaches the head of the queue, and the finished load is noticed at
step boundaries. On this GPU the capacity that binds is therefore the 4.5 GB of GPU KV, and a host tier — DRAM, SSD or
CXL — relieves compute, not that; the lighter-load sweep (§7.3) measures the host tier where the queue is not saturated.

### 7.2b Measured sweep, tool-agent trace at 0.08× (figures D1–D4, `replay/tables-d-tool.md`)
Same server, same replay speed; the window holds 544 requests and 4.61 M prompt tokens (prompt p50 6.2 k, p90 19 k
tokens; 0.42 req/s, 3.56 k offered prompt tokens/s over ≈ 1,290 wall s). `d-tool-dram2` is re-run at the head of
`queue_i2.sh` (its first run was contaminated by the incident of §15.C) and is added when it lands.

| run | cached share (host / GPU) | TTFT p50 / p95 / p99 (s) | hit ≥ 50 % TTFT p50 (s) [n] | miss TTFT p50 (s) [n] | request time p50 (s) | computed tok/s | KV host→GPU / GPU→host (GB) | evicted chunks | L1 max (GB) | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| d-tool-dram5 | 0.323 (0.084 / 0.239) | 14.6 / 46.0 / 53.1 | 13.3 [290] | 15.7 [187] | 27.4 | 2,407 | 14.2 / 74.8 | 7,524 | 4.4 | 0.88 | 41 |
| d-tool-dram10 | 0.332 (0.097 / 0.235) | 13.2 / 44.6 / 50.1 | 12.4 [302] | 14.9 [177] | 26.2 | 2,380 | 16.5 / 76.1 | 7,221 | 8.8 | 0.88 | 41 |
| d-tool-dram20 | 0.332 (0.095 / 0.237) | 13.1 / 44.6 / 50.1 | 12.4 [302] | 14.9 [177] | 26.2 | 2,380 | 16.2 / 76.2 | 6,517 | 17.2 | 0.88 | 41 |
| d-tool-dram40 | 0.335 (0.093 / 0.242) | 12.9 / 44.0 / 49.2 | 12.3 [305] | 14.5 [175] | 25.5 | 2,374 | 15.8 / 76.3 | 5,089 | 34.3 | 0.88 | 41 |
| d-tool-dram80 | 0.354 (0.110 / 0.243) | 12.7 / 40.9 / 48.1 | 12.4 [313] | 13.8 [167] | 23.5 | 2,322 | 18.7 / 74.6 | 1,455 | 68.5 | 0.87 | 41 |
| d-tool-ssd (10 GB L1 + NVMe L2) | 0.310 (0.057 / 0.252) | 15.6 / 45.6 / 54.2 | 13.6 [271] | 21.0 [207] | 28.2 | 2,443 | 9.8 / 99.0 | 14,160 (L1) | 1.0 | 0.88 | 40 |
| d-tool-none (vLLM alone) | 0.256 (0.000 / 0.256) | 18.5 / 58.4 / 72.7 | 12.6 [226] | 23.8 [250] | 32.5 | 2,586 | 0 / 0 | 0 | – | 0.89 | 46 |

All 544 requests of every run completed. Columns as in §7.2.

**Result.** The tool-agent window overloads the server as well (GPU busy 0.87–0.89, backlog up to 41–46, TTFT p50
13–19 s), but here the host tier matters from the smallest capacity, because this trace's reuse is short-distance
(§7.1): the GPU prefix cache alone serves 25.6 % of the prompt tokens (vLLM alone), 5 GB of DRAM adds 8.4 points from the
host tier and 80 GB 11.0 points (cached share 0.323 → 0.354). The measured cached shares match the offline LRU of §7.1
within one point (0.325 at 4.5 GB, 0.363 at 80 GB), which validates the trace analysis as a predictor of hit share for
this replay. The hits pay off through removed work: computed prefill falls 10 % (2,586 → 2,322 tok/s), and the
saturated queue amplifies that into TTFT p50 −31 % (18.5 → 12.7 s), p95 −30 %, p99 −34 % and request completion p50
−28 % (32.5 → 23.5 s); 5 GB already gives −21 / −21 / −27 %. Between 10 and 40 GB nothing changes (host share
9.3–9.7 %, TTFT p50 12.9–13.2 s), as the window offers no more reuse in that range (§7.1: 0.333 at 20 GB). Stores are
75–76 GB per window in every DRAM run, above the 80 GB tier's watermark (0.8 × 80 GB = 64 GB), so even the largest tier
evicts within 100 trace-seconds (1,455 chunks; 7,524 at 5 GB). The SSD-backed configuration finds *fewer* hits than 5 GB
of DRAM (host share 5.7 % vs 8.4 %; its lookups report 17 % of prompt tokens — 2 % in the 10 GB L1, 15 % in the NVMe
L2 — against 30 % for the 5 GB DRAM L1): joined request by request in trace order, the SSD run retrieved fewer host
tokens on 59 requests and more on 28, losing 0.27 M of the 0.39 M host tokens the DRAM run retrieved, and the lost hits
arrive late in the window (p50 874 s vs 492 s for the kept ones). Its TTFT p50 is 15.6 s (−16 % vs vLLM alone) and it
writes 99 GB to the NVMe over the window. The cause is not isolated in this session; the candidate consistent with the
late losses is the asynchronous L2 store path (a chunk becomes visible to lookups only after its NVMe write completes,
while this trace re-uses prefixes within seconds). On the conversation trace, whose reuse is long-distance and where the
L2 never evicts, the same configuration found more hits than 40 GB of DRAM (§7.2).

Figures D3 / D4 over both traces: computed prefill falls with capacity (conversation 2,445 → 2,396 tok/s, tool-agent
2,586 → 2,322) while the GPU stays saturated (busy share 0.884 → 0.877 and 0.895 → 0.869: the GPU is never idle, the
hits only shorten the queue); stores are 75–79 GB per window at every capacity (everything computed is stored);
retrieves grow from 0 to 3.5 GB (conversation) and 14 to 19 GB (tool-agent); evictions fall from ≈ 8,000 chunks at
2–5 GB to ≈ 1,450 at 80 GB on both traces.

### 7.2c Which requests the host tier helps under overload (both traces; `replay/tables-d-hitcat.md`, `hitcat_d.py`)
`hitcat_d.py` groups the requests of a run by where their prefix came from — host-dominant hits (≥ 50 % of the prompt
retrieved from LMCache), GPU-prefix hits (≥ 50 % served by vLLM's prefix cache), partial hits (10–50 % cached) and misses
(< 10 %) — and reads the per-request timeline of the hooks (§1.1):

| run | category | n | prompt tok p50 | uncached tok p50 | TTFT p50 (s) | queue→sched p50 (s) | lookup p50 (s) | lookup result→load issued p50 (s) | KV load wait p50 (s) | transfer p50 (s) | prefill p50 (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| d-tool-dram80 | host ≥ 50 % | 95 | 6,169 | 592 | 21.0 | 19.7 | 0.66 | 7.1 | 0.86 | 0.09 | 0.34 |
| d-tool-dram80 | GPU ≥ 50 % | 215 | 6,231 | 525 | 6.8 | 5.9 | 0.46 | 1.1 | 0.22 | 0.02 | 0.42 |
| d-tool-dram80 | 10–50 % | 64 | 2,038 | 1,504 | 10.9 | 8.8 | 0.46 | 8.4 | 0.87 | 0.09 | 0.78 |
| d-tool-dram80 | miss < 10 % | 167 | 13,886 | 13,374 | 13.8 | 9.3 | 0.54 | – | – | – | 3.31 |
| d-tool-dram5 | host ≥ 50 % | 79 | 6,188 | 572 | 26.2 | 25.5 | 0.59 | 8.3 | 0.88 | 0.08 | 0.37 |
| d-tool-dram5 | GPU ≥ 50 % | 211 | 6,214 | 568 | 10.4 | 8.9 | 0.47 | 12.5 | 0.30 | 0.02 | 0.43 |
| d-tool-dram5 | miss < 10 % | 187 | 13,544 | 13,032 | 15.7 | 11.8 | 0.49 | – | – | – | 3.13 |
| d-tool-none | GPU ≥ 50 % | 226 | 6,221 | 573 | 12.8 | 11.6 | – | – | – | – | 0.83 |
| d-tool-none | miss < 10 % | 250 | 9,271 | 8,847 | 23.8 | 21.1 | – | – | – | – | 2.57 |
| d-conv-dram80 | host ≥ 50 % | 11 | 7,833 | 665 | 23.8 | 22.9 | 0.61 | 10.3 | 0.18 | 0.11 | 0.42 |
| d-conv-dram80 | GPU ≥ 50 % | 28 | 906 | 394 | 12.9 | 11.3 | 0.55 | – | – | – | 0.58 |
| d-conv-dram80 | miss < 10 % | 186 | 13,886 | 13,374 | 15.1 | 10.6 | 0.60 | – | – | – | 3.50 |

At equal backlog at arrival (fewer than 20 requests outstanding) the ordering is the same: tool-agent 80 GB host-dominant
hits 16.8 s p50 [69] against 2.7 s for GPU-prefix hits [166] and 11.5 s for misses [139]; 5 GB 15.0 / 5.3 / 11.6 s;
conversation 80 GB 23.8 / 11.9 / 14.4 s. ("GPU ≥ 50 %" requests also issue one small LMCache retrieve for the chunk
beyond the GPU prefix, the 1-chunk load of §3; the lookup itself takes 0.5–0.7 s p50 under this load against
milliseconds when idle, §3 — not isolated further.)

**Result.** A host-dominant hit — 6.2 k prompt tokens of which 0.6 k must be computed, the same length as a GPU-prefix
hit and half a miss — has the longest TTFT of all categories in every run with host hits: 3–6× a GPU-prefix hit and
1.4–1.6× a miss twice its length. Its transfer takes 90 ms and the wait for the finished load to be noticed 0.9 s; the
time is between the lookup result and the moment the load is issued: 7.1 s p50 at 80 GB, 8.3 s at 5 GB, and among the
57 of 95 host hits with a gap above 2 s, 12.5 s p50 / 26 s p90. Few requests overtake a waiting host hit (38 of the
≈ 330 requests first scheduled during such gaps at 80 GB arrived after it), so the queue behind it waits as well.

**Explanation (SOURCE INSPECTION, `vllm/v1/core/sched/scheduler.py` of vLLM 0.31, the waiting loop of `schedule()`).**
When the connector reports external tokens with `load_kv_async`, the scheduler schedules no new tokens for the request
and instead allocates slots for *all* external tokens at once (`allocate_slots(…, num_external_computed_tokens,
delay_cache_blocks=True, reserved_blocks=…)`), with `reserved_blocks` = the blocks the in-flight prefills still need
plus the speculative-decode step blocks: "An async load holds its blocks for the whole transfer with no forward progress
and isn't preemptible here. Admit it only if it fits in (free − other in-flight reservations)". If the allocation fails,
the scan `break`s ("The request cannot be scheduled"), the request stays at the head of the waiting queue, and nothing
falls back to computing the prefix. A miss is admitted with slots for one 2,048-token chunk and then grows as a running
request, which the running loop serves before the waiting queue is scanned; a GPU-prefix hit's blocks are resident and
it needs new slots only for its uncached tail. Once a load is issued it finishes in 90 ms, the finished load is noticed
at the next step boundary and the request is drained ahead of the plain queue (`kv_holding_waiting` precedes `waiting`).
Under GPU-KV saturation (§7.2: 5–11 sequences fill the 121,792-token cache; every freed block is claimed by decode growth
and by the in-flight prefills' reservations before the waiting queue is scanned) the whole-prefix reservation — 6.2 k
tokens, 5 % of the GPU KV cache, in one piece — is the hardest allocation in the system, so the requests the host tier
could serve with 90 ms of transfer are admitted last. The capacity effect of §7.2 / §7.2b therefore comes entirely from
the work the hits remove from the GPU (shorter queue for everyone), not from the hits being fast; the hits themselves are
the slowest requests. What would change that is scheduling policy in vLLM, not memory: admitting an async load
incrementally (chunked, as prefill is), reserving blocks for pending loads ahead of new chunked misses, or computing the
prefix when the reservation fails while the KV sits 90 ms away. None of these was implemented or measured here (the
study does not modify vLLM or LMCache); they are inferences from the source and the timeline, and they are the concrete
form of the Q2 / Q4 scheduling opportunity under GPU-KV-bound overload. Bidaw's loading-latency-aware ordering (§14)
addresses the related but different problem of ordering by *transfer* cost; here the transfer is not the cost.

_[pending 2026-11-05 04:30: §7.3 lighter-load sweep (0–200 s at 0.04×, 2 / 80 / 320 GB and vLLM alone, both traces;
`queue_i2.sh`, after the B real-trace chain, F, G, H); `d-tool-dram2` re-run.]_

## 10. Unexpected and negative results (collected; each points to the section with the numbers)
1. **A host hit stops being faster than a miss as soon as the server is loaded** (§4, §6, §7.2): the transfer is 16–40 ms,
   but a hit waits for the scheduler's queue scan (stops when the 2,048-token budget is spent), is submitted one step
   late under async scheduling, and its finished load is noticed only at an engine-step boundary (0.3–1.4 s). Under
   overload host-dominant hits are the *slowest* requests of all (§7.2c): vLLM admits an async load only when the blocks for
   its entire prefix are free at once and otherwise stops the scan, so at equal backlog they wait 3–6× longer than
   GPU-prefix hits of the same length (tool-agent 80 GB: 16.8 vs 2.7 s p50) and longer than misses twice their length
   (11.5 s); the capacity benefit comes from the work removed, never from the hits being fast.
2. **Eager prefetch does nothing measurable** (§4): it moves the lookup to arrival, not the load.
3. **Four transfer threads = one** (§5): LMCache routes an engine's requests to one worker (affinity by ZMQ identity), so
   16 simultaneous 8k hits take 428 ms p50 either way and the PCIe link is never the limit.
4. **Priority ordering only moves the wait between classes** (§4): hits-first −43 % hit TTFT at concurrency 16, cold +2–15 %;
   cold-first the mirror image; total work unchanged. **Prefill chunk 512** trades the step-granularity wait for a longer
   scan wait and costs 7–8 % of throughput; at high load the hits end up worse (3.4 → 5.0 s at concurrency 16).
5. **Synchronous scheduling is a free 10–20 %** for the hits in this regime (§4), the only knob that helped everywhere.
6. **The host tier costs something when it has nothing to serve** (§3, §7.2): a GPU-prefix hit pays a lookup and a 1-chunk
   load (19–35 ms vs 12–40 ms without LMCache); with no host hits the LMCache configurations are 2.5 % slower in TTFT p50
   than vLLM alone and store 77 GB of KV per 100 trace-seconds of the conversation trace.
7. **Closed-loop TTFT quantiles are *lower* without the host tier at concurrency 16** (§4) although the tier adds ~55 % of
   capacity: the faster hits keep more cold prefill in flight at any time. End-to-end benefit shows in capacity and
   open-loop TTFT, not in closed-loop quantiles.
8. **The 100-s trace windows carry almost no capacity-sensitive reuse** (§7.1): conversation 4.5 % at GPU size vs 8.5 % at
   80 GB and 9.3 % unbounded, tool-agent 32.5 % vs 36.3 % and 36.9 % (the measured hit shares of §7.2b match these within
   one point); the planned 0–50 s mini-sweep would have been blind as well. Reuse that needs capacity is
   long-distance (hundreds of GB over the hour for a 3B model), so a capacity experiment needs long windows or a
   trace-driven cache model, not faster replay.
9. **The replayed load is bound by GPU KV capacity, not compute** (§7.2): 121,792 tokens of GPU KV hold ~10 of the trace's
   requests, so 5–11 sequences run when requests wait; a host-tier hit frees compute but not GPU blocks.
10. **The first SSD runs measured the page cache, then the previous run's disk** (§3): the fs L2 is persistent across
    runs and the lookup prefetches from L2 even for GPU hits; fixed with O_DIRECT and per-run directories.
11. **The hook-less control was *slower* on host hits** (§1.2): the GPU's idle-power ramp (≥ 50 ms idle → +30–40 ms on the
    next short request), not instrumentation cost; busy servers are unaffected (`b-default-nosamp` within noise).
12. **vLLM alone moves ~20–30 GB of PCIe traffic per direction per run with no KV tier** (§1.3, §7.2): an unexplained
    baseline, so KV traffic is taken from LMCache's retrieve / store events, not from the PCIe counters.
13. **Run-hygiene incidents** (§15.C): the first `b-default` (sequences re-used across levels), the quota-truncated
    `b-noasync`, the `KeyError` priority runs, two "Server disconnected" answers in a 16-request burst, LMCache
    "preempted" warnings (6 per conversation replay: vLLM preempted a request whose KV had been loaded), and the premature
    start of the lighter-load queue that contaminated `d-tool-dram2` (re-run). None changes a conclusion; all are recorded.
14. **The SSD-backed tier finds fewer of the tool-agent trace's short-distance hits than 5 GB of DRAM** (§7.2b): host share
    5.7 % vs 8.4 %, lookups 17 % vs 30 % of prompt tokens, the losses late in the window; on the conversation trace
    (long-distance reuse, no L2 eviction) it found more than 40 GB of DRAM. Cause not isolated (candidate: the asynchronous
    L2 store path makes a chunk visible only after its NVMe write completes).

## 11. Limitations
- **CXL was not exercised.** The DAX devices are root-only since the 2026-10-18 reboot, so every capacity point is pinned
  DRAM. The transfer to CXL rests on PREVIOUSLY MEASURED equalities (GPU reads from CXL and pinned DRAM at the same
  12.5 GiB/s, 2026-10-07; a devdax-backed L1 gave the same TTFT, 2026-10-11 and 2026-10-18). Not represented: the host-side
  interference of CXL writes on the reader's CCD (Phase 3, cxlpath), CXL's higher load latency on the LMCache server's own
  CPU-side work (lookups, chunk bookkeeping, eviction), and any NUMA effect of a 1 TiB tier.
- **One small GPU, one small model.** An RTX 4060 Ti (8 GiB, PCIe 4.0 ×8) serving a 3B AWQ model (36 KiB KV/token). The
  GPU KV cache (121,792 tokens) binds concurrency at the replayed loads; an H100 serving a 70B model has ~9× the bytes per
  token, 10× the KV capacity and a 4× faster link, so the *magnitudes* here do not transfer — the mechanisms (asynchronous
  lookup/load, step-boundary notice, budget-bounded scan, one transfer thread per engine, GPU blocks needed by a hit) are
  properties of the engine and do.
- **Trace replay is time-scaled and synthetic.** Windows of 100 / 200 trace-seconds at 0.08× / 0.04× keep the request
  sequence and the reuse structure but stretch inter-arrival times, truncate reuse distance (§7.1), and cap outputs at
  1,024 tokens; prompts are pseudo-random token ids built from the trace's hash blocks, so generation quality is
  meaningless and output lengths come from the trace, not the model. One replay per configuration (the controlled
  experiments have 4 repetitions).
- **The scheduling reference is a model** (§6): calibrated and validated at 7–27 % optimism; its zero-delay and clairvoyant
  variants are bounds, not policies, and are labelled so throughout.
- **Instrumentation is logging-only but not free of side effects**: the GPU idle-power effect adds 30–40 ms to isolated
  short requests (§1.2); loaded servers are unaffected.
- **Software versions**: vLLM 0.31.0 with async scheduling on by default and LMCache 0.5.5 multi-process mode (one
  transfer thread per engine, asynchronous lookup); later versions may move the step-boundary notice or the affinity
  routing. "Avoid modifying core vLLM or LMCache behaviour" was respected: every configuration is a command-line flag.
- **Storage**: the SSD tier is this node's NVMe at 2.7 GB/s O_DIRECT; the first SSD runs were invalid (§15.C).
- **Operational**: the home quota filled during the night of 2026-11-04 (older account content); the raw data lives on
  `/mnt/local` behind a symlink, which departs from the repo convention of raw data under `experimental_results/`.
- **Scope**: single engine, no tensor parallelism, no prefill–decode disaggregation, no multi-tenant host memory, no real
  users; the study is about the engine–cache coupling, not about a complete serving system.

## 14. Related work (only references verified in this session or in `Related.md`, 2026-07; no venue is claimed that was not checked)

- **vLLM** — Kwon et al., *Efficient Memory Management for Large Language Model Serving with PagedAttention*, SOSP 2023
  (arXiv 2309.06180). The engine measured here (0.31.0): paged GPU KV blocks, prefix caching, chunked prefill, the
  WAITING / WAITING_FOR_REMOTE_KVS queue and the token-budget scan whose behaviour §4 and §6 quantify. Its KV-connector
  interface is what LMCache plugs into; the step-boundary notice of finished loads (§1.1) is a property of this interface.
- **LMCache** — arXiv 2510.09665 (the project's paper; the 0.5.5 multi-process server used here). KV tiering substrate
  (GPU → pinned host memory → disk / remote) with chunked prefix lookup and CUDA-IPC transfer. §3 and §5 measure its
  retrieval cost and its per-engine serialisation; the results are about the vLLM–LMCache coupling, not LMCache alone.
- **CacheGen** — Liu et al., *CacheGen: KV Cache Compression and Streaming for Fast Large Language Model Serving*, 2024
  (UChicago knowledge record 4r8rp-nx329). Compresses KV 3.5–4.3× and streams it adaptively; relevant to §5 because
  compression shrinks the bytes per hit, which only matters where the link is the bottleneck — on c28 it is not (§5: loads
  serialise on one thread well below the 12.5 GiB/s link).
- **SGLang / RadixAttention** — Zheng et al., *SGLang: Efficient Execution of Structured Language Model Programs*, NeurIPS
  2024. Radix-tree prefix reuse inside GPU memory; the GPU-prefix hits of §7 (4.4 % of the conversation trace, 32–38 % of
  the tool-agent trace at GPU size) are the regime it exploits; a host tier only adds the longer-distance reuse of §7.1.
- **Mooncake** — Qin et al., FAST 2025 (arXiv 2407.00079). Disaggregated KV-centric serving with a DRAM/SSD/RDMA KV pool,
  prefill–decode separation and overload rejection; the source of the two traces replayed in §7–8. Their trace-level reuse
  is reproduced by `trace_reuse.py` (§7.1): the capacity that pays is hundreds of GB per 3B-sized model.
- **CachedAttention / AttentionStore** — Gao et al., ATC 2024. Multi-turn KV persistence across HBM/DRAM/SSD with
  layer-wise prefetch and scheduler-aware eviction; the earliest statement of the problem §4 measures (loads must be
  overlapped with the scheduler) and a reference design for the "prefetch at arrival" behaviour that LMCache's
  `eager_prefetch` only partially provides (§4: no measurable effect).
- **Bidaw** — Hu, Zhang, Zhou, Wei, Zhong, Chen, *Bidaw: Enhancing Key-Value Caching for Interactive LLM Serving via
  Bidirectional Computation–Storage Awareness*, FAST 2026, pp. 101–116. Two-tier host-memory + SSD KV store for multi-turn
  serving; the compute engine schedules requests by KV-loading latency and KV size, the store uses the generated responses
  to predict reuse at eviction; reports up to 3.58× lower latency and 1.83× higher throughput than prior work, approaching
  the all-in-host-memory bound. This is the closest published work to the scheduling gap of §4 and §6 (tier-aware,
  size-aware ordering of requests that need retrieval): the opportunity those sections quantify is one Bidaw already
  claims, on a different engine; no CXL in it.
- **KVCache Cache in the Wild** — arXiv 2506.02634: characterisation of KV-cache reuse at a large cloud provider; the
  same long-distance reuse structure that §7.1 finds in the Mooncake traces.
- **CXL-based KV storage** — *Exploring CXL-based KV Cache Storage for LLM Serving* (NeurIPS 2024 ML-for-Systems
  workshop), **Beluga** (SIGMOD 2026, arXiv 2511.20172; real CXL switch pool, flat KV pool), **TraCT** (arXiv 2512.18194;
  emulated CXL, phase- and recency-aware KV placement), **CXL-SpecKV** (FPGA 2026, arXiv 2512.11920; FPGA near-data KV).
  All treat CXL as capacity or transfer substrate; none measures what the serving scheduler does with the hits, which is
  the gap §4–6 fill on commodity parts, nor the GPU-KV-capacity bound of §7.2.
- **Tiered-memory systems** — Memstrata (Zhong et al., OSDI 2024; the project's inspiration), Pond (ASPLOS 2023), TPP
  (ASPLOS 2023): VM/page-granular CXL tiering; they bound the host-side interference axis that this study does not
  exercise (CXL blocked) and that the project's Phase 3 results cover (§13).
- **Phase disaggregation and offloading** — DistServe (OSDI 2024, arXiv 2401.09670), InfiniGen (OSDI 2024), FlexGen (ICML
  2023): background for why prefill compute, not decode, is what a host-tier hit saves (§3: 0.14 ms/token + 8.2 ns/token²).

## 15. Appendix

### 15.A Configuration (exact, from `*-meta.txt` and the process list)
- **Node** c28 (Slurm job 326741, 2026-11-04 → 2026-11-07 13:12): AMD EPYC Turin, 755 GiB DRAM (NPS1), RTX 4060 Ti 8 GiB on
  PCIe 4.0 ×8 (cudaMemcpy pinned → GPU 12.5 GiB/s, PREVIOUSLY MEASURED 2026-10-07), local NVMe `/mnt/local` (O_DIRECT reads
  2.6–2.9 GiB/s), 4× CZ120 as devdax `/dev/dax0.0–2.0` (root 0600, unusable). Kernel 6.14.11. Details: `inspect/environment.txt`.
- **Software** Python 3.12.15, vLLM 0.31.0, LMCache 0.5.5 (g05a013b2), torch 2.13.0+cu130, env `/mnt/local/ghu4/envs/lmcache`;
  figures with matplotlib 3.11.2 from `/mnt/local/ghu4/envs/agent`. Models `Qwen/Qwen2.5-3B-Instruct-AWQ` (36 KiB KV/token,
  primary) and `Qwen/Qwen2.5-1.5B-Instruct` (28 KiB/token, §3 only). Traces `workloads/mooncake_conversation_trace.jsonl`
  (12,031 requests / 3,600 s) and `workloads/mooncake_toolagent_trace.jsonl` (23,608 / 3,600 s).
- **vLLM server (default configuration)** — `vllm serve Qwen/Qwen2.5-3B-Instruct-AWQ --port 8100 --max-model-len 32768
  --max-num-seqs 16 --gpu-memory-utilization 0.85 --dtype float16 --enable-prompt-tokens-details --disable-uvicorn-access-log
  --scheduling-policy fcfs --kv-transfer-config '{"kv_connector": "LMCacheMPConnector", "kv_connector_module_path":
  "lmcache.integration.vllm.lmcache_mp_connector", "kv_role": "kv_both", "kv_connector_extra_config": {"lmcache.mp.host":
  "tcp://127.0.0.1", "lmcache.mp.port": 5555, "lmcache.mp.eager_prefetch": false}}'`; pinned to CPUs 96–119; variants add
  `--max-num-batched-tokens 512`, `--no-async-scheduling`, `--scheduling-policy priority`, `--enforce-eager`, or drop the
  connector (`tier=none`). GPU KV cache with CUDA graphs: 121,792 tokens.
- **LMCache server (default)** — `lmcache server --host 127.0.0.1 --port 5555 --http-host 127.0.0.1 --http-port 8200
  --chunk-size 256 --eviction-policy LRU --eviction-trigger-watermark 0.8 --max-gpu-workers 1 --max-cpu-workers 1
  --supported-transfer-mode lmcache_driven --l2-prefetch-max-in-flight 8 --l1-size-gb <L1>`; pinned to CPUs 120–127; the
  SSD tier adds `--l2-adapter '{"type":"fs","base_path":"/mnt/local/ghu4/kvl2/<run>","use_odirect":true}' --l2-store-policy
  skip_l1` (directory deleted when the run stops); variants `--max-gpu-workers 4`.
- **Client / drivers** `benchmarks/serving/client.py` (streaming chat completions, `X-Request-Id`, prompts = pseudo-random
  token ids in [1000, 150000)); drivers pinned to CPUs 80–87; GPU sampler (NVML, 5 ms PCIe counters) on CPU 95, CPU sampler
  on CPU 94. Logging-only hooks: `vllmevt/sitecustomize.py` (engine), `benchmarks/agent/kvevt/sitecustomize.py` (LMCache).
- **Raw data** `/mnt/local/ghu4/results/2026-11-04-cxl-serving-scheduling-gap/` (symlinked from
  `experimental_results/2026-11-04-cxl-serving-scheduling-gap/` after the home-quota incident of 2026-11-04, §1.3); per run:
  `<tag>-client.jsonl`, `-meta.txt`, `-server.log`, `-lmcache.log`, `-kvevents.jsonl`, `-vllmevt.req/step.*.jsonl`, `-gpu.txt`,
  `-cpu.txt`, `-status.txt`, `-driver.txt`, and the analysis outputs `-requests.csv`, `-steps.csv`, `-scenarios.csv`, `-replay.json`.

### 15.B Experiment matrix
_[pending: `matrix.py` output over all runs once the queue finishes — one row per run with configuration, status, request counts and errors.]_

### 15.C Runs excluded or failed
| run | problem | disposition |
|---|---|---|
| `B/flawed/b-default` (first) | s1/s2 mixed sequences generated once per scenario: cold prompts of one level were hits at the next | kept in `B/flawed/`, superseded by the per-level regeneration |
| `A/a-3b-ssd` (first SSD run) | no O_DIRECT → served by the page cache | `host` rows kept and labelled; O_DIRECT reruns (`a-3b-ssd-odirect`, `-odirect2`) |
| `A/a-3b-ssd-odirect` | found its prompts already on disk (persistent fs L2 of the previous run) for the cold cases | `host` rows valid; clean rerun `a-3b-ssd-odirect2` with a per-run L2 directory |
| `B/flawed/b-noasync` (first) | truncated when `/home` hit its 40 GB quota (2026-11-04 20:55) | rerun after moving the results to `/mnt/local` |
| `B/b-prio-hits`, `b-prio-cold` (first) | driver `KeyError: 'warm'` in the priority map | fixed (`.get(t, 1)`), reruns succeeded |
| `B` s3-k16 | two flush requests answered "Server disconnected" | recorded in the client file, excluded from the statistics |
| `replay/flawed/dl-conv-dram2`, `d-tool-dram2` (first) | the lighter-load queue started while `d-tool-dram2` ran (its trigger string appeared in a note appended to `queue.txt`); the stray driver sent 599 conversation requests to the running server for 6 min | both quarantined; `d-tool-dram2` re-run first in `queue_i2.sh` |

## Change history
- 2026-11-04 — file created with the environment and source inspection; experiments started.
- 2026-11-05 — §7 Experiment D: trace reuse analysis (D0) and the conversation-trace capacity sweep at 0.08× (overloaded, GPU-KV-bound); tool-agent sweep and lighter-load sweep pending; §2 table updated.
- 2026-11-05 — §14 related work (verified references; Bidaw FAST'26 identified as the closest work to the scheduling gap).
- 2026-11-05 — §10 unexpected/negative results, §11 limitations, §15 appendix (configuration, excluded runs; matrix pending) drafted.
- 2026-11-05 — §7.2b tool-agent sweep at 0.08× and §7.2c hit-category / admission analysis (host-tier hits admitted last under GPU-KV saturation: whole-prefix block reservation, source-inspected; `hitcat_d.py`, `replay/tables-d-hitcat.md`); §7.2 explanation sharpened; §10 items 1, 8, 14; §2 table; figure D2 legend moved.
