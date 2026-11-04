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
instrumentation does not slow anything; it keeps the GPU's PCIe link awake: `nvidia-smi` reports the link at **Gen 1** when
the GPU is idle (`inspect/environment.txt`, `pcie.link.gen.current = 1`) and Gen 4 while serving; the NVML counter poll of
`gpu_sampler.py` (~1 ms) keeps it at Gen 4, so a host→GPU KV load after an idle gap starts on a 2.5 GT/s link and pays the
retraining. Two control variants (hooks only / samplers only) are queued to attribute the effect; all concurrent-serving
runs below keep the sampler on (busy-link condition) and one sampler-less B/E variant quantifies the idle-link penalty under
load. This is a real deployment effect of a lightly loaded server, not an artefact to hide.

## 2. Experiments (plan; results are appended per family as they close)
| family | question | status |
|---|---|---|
| A single-request retrieval cost | TTFT and its stages for cold / GPU hit / DRAM hit / SSD hit / vLLM alone, L = 256 … 16,384 | running |
| B concurrent serving and scheduling | controlled mixes and real-trace windows; default vs eager prefetch vs 4 transfer threads vs priority ordering | planned |
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

## Change history
- 2026-11-04 — file created with the environment and source inspection; experiments started.
