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

## 2. Experiments (plan; results are appended per family as they close)
| family | question | status |
|---|---|---|
| A single-request retrieval cost | TTFT and its stages for cold / GPU hit / DRAM hit / SSD hit / vLLM alone, L = 256 … 16,384 | running |
| B concurrent serving and scheduling | controlled mixes and real-trace windows; default vs eager prefetch vs 4 transfer threads vs priority ordering | planned |
| C scheduling gap | calibrated offline reference (zero-delay, clairvoyant resource-constrained) vs measured | planned |
| D capacity | L1 sweep (DRAM; CXL blocked) + SSD-backed + recompute-only on trace replays | planned |
| E concurrent retrieval bandwidth | k simultaneous hits, PCIe RX, per-request retrieve time, transfer threads | planned |
| F workload sensitivity | both traces, controlled variations | planned |

## Change history
- 2026-11-04 — file created with the environment and source inspection; experiments started.
