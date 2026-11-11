# 2026-11-10 — GPU KV memory admission of external KV hits (RQ2 validation; exploratory)

**STATUS: ACTIVE (started 2026-11-10; branch `explore/gpu-kv-admission`, from `explore/cxl-serving-scheduling-gap` cb7c4ba =
the verified serving-study commit b7b6823 plus its summary file; not merged anywhere).** This study does not change the
research charter, the charter-RQ1 conclusions, the Phase 3 negative result or the 2026-11-04 serving study; where its
measurements correct a statement of that study, the correction is recorded here (§A1.4) and the old file is left as it is.
Raw data: `experimental_results/2026-11-10-gpu-kv-admission/` (during the study a symlink to
`/mnt/local/ghu4/results/2026-11-10-gpu-kv-admission/` on c28's local NVMe). Tools: `benchmarks/serving/` (the 2026-11-04
harness) plus `kvadm/sitecustomize.py` (admission instrumentation and flag-gated prototypes), `analyze_adm.py`, `run_adm.py`.

## Question
External (host-tier) KV hits waited seconds for admission under GPU KV memory pressure in the 2026-11-04 study although
their transfer takes tens of milliseconds (tool-agent replay at a sustainable load, 320 GB host tier: host-dominant hits
3.3 s TTFT p50 against 0.3 s for GPU-prefix hits; 42 of 148 waited more than 2 s between lookup result and load). That
study explained it from the source as a whole-prefix block reservation. This study asks: **what exactly delays an external
hit (A), which minimal change removes the unnecessary part of the delay (B), and does that improve end-to-end serving
(C, D) beyond one small GPU (E)?** Success criteria are the qualitative gates of the brief (§11 there): a repeatable
bottleneck, a causal explanation, a practical mechanism, an end-to-end gain, no unacceptable loss for misses, and benefit
beyond one pathological configuration.

## Evidence labels
**MEASURED** = real vLLM 0.31.0 + LMCache 0.5.5 serving with logging-only instrumentation (prototype runs additionally name
their flags); **SOURCE** = read from the installed source (file:line of the installed packages); **PREVIOUSLY MEASURED** =
a closed experiment file, cited with its date; **SIMULATED** is not used in this study. Host-tier capacity is pinned DRAM:
every result is a host-memory admission result, not a CXL measurement (§0).

## 0. Environment (2026-11-10)
- **Node** c28, Slurm job 330576 (2026-11-10 13:12 → 2026-11-13 13:12; follow-up job 334219 pending to 2026-11-16): 128 cores /
  256 threads, one NUMA node, 755 GiB DRAM; RTX 4060 Ti 8 GiB (PCIe 4.0 ×8). Software unchanged from the 2026-11-04 study:
  Python 3.12, vLLM 0.31.0, LMCache 0.5.5 (multi-process server), env `/mnt/local/ghu4/envs/lmcache`; model
  Qwen2.5-3B-Instruct-AWQ (36 KiB of fp16 KV per token, 16-token GPU KV blocks = 576 KiB per block).
- **GPU KV pool.** With `--gpu-memory-utilization 0.85` vLLM sizes the pool from the memory free at start-up, and that
  varied between runs of the previous study: 121,792 tokens (7,612 blocks) in `dl-tool-dram320` / `dl-tool-dram80`, 119,296
  tokens (7,456 blocks) in `d-tool-dram80` / `dl-conv-dram320` (server logs, "GPU KV cache size"). Policy comparisons of this
  study therefore pin the pool with `--num-gpu-blocks-override` (`gpu_blocks=`) wherever runs are compared.
- **CXL: still blocked (checked 2026-11-10 15:55).** `/dev/dax0.0`, `/dev/dax1.0`, `/dev/dax2.0` are `crw------- root root`
  (mtime 2026-10-20 15:32); `open()` as `ghu4` fails with EACCES. `/dev/dax2.0` is in addition mounted as a root-owned famfs
  (FUSE) at `/mnt/famfs/dax2.0` and is reserved for another project by the user's rule of 2026-09-17; it was not touched.
  No permission, mount or system setting was changed. Consequence: the host tier of every run is pinned DRAM; §F states what
  that does and does not show about CXL.
- **Larger GPUs (checked 2026-11-10 16:30).** c33 (A100 80 GB) and c29 (H100 94 GB) are allocated to another user until
  2026-11-13 14:04 and 22:01; c30 / c31 (A6000) are in use until at least 2026-11-11. The `rtx4060ti16g` partition has idle
  nodes with the same GPU model and twice the memory — used for Experiment E and, with the pool pinned to c28's 7,456 blocks,
  as additional machines for the controlled scenarios.
- **The 16 GB nodes (results under `E16/`).** c60, c61, c66: RTX 4060 Ti 16 GiB, EPYC 8124P (16 cores), 188 GiB RAM; NVIDIA
  driver 580.82.07 on c60 and c61, 595.58.03 on c66. The software is a copy of c28's environment and model cache on the shared
  scratch file system (`/mnt/beegfs/ghu4/kvadm/`), visible under its c28 path through one symlink; vLLM runs on cores 0–9,
  LMCache on 10–13, the samplers on 14–15 (`remote16.sh`). With the pool pinned the node reproduces c28's controlled trials to
  the hundredth of a second (A3.1). Every comparison of configurations in this report is between runs on the same node
  (the tables name it); where a figure puts pools measured on two nodes side by side, its caption says so. The nodes cannot hold a 320 GB host tier, so the replays with that tier ran on
  c28 only.

## A1. Source inspection: how a waiting request gets GPU KV blocks (SOURCE; vLLM 0.31.0 and LMCache 0.5.5 as installed)
Paths are relative to `/mnt/local/ghu4/envs/lmcache/lib/python3.12/site-packages/`. `S` = `vllm/v1/core/sched/scheduler.py`,
`K` = `vllm/v1/core/kv_cache_manager.py`, `C` = `lmcache/integration/vllm/lmcache_mp_connector.py`,
`M` = `lmcache/integration/vllm/lmcache_mp_metadata.py`, `W` = `vllm/v1/worker/kv_connector_model_runner_mixin.py`.

### A1.1 One engine step
`Scheduler.schedule()` (S:562) has a token budget per step (`max_num_scheduled_tokens`, default = `max_num_batched_tokens` =
2,048; `vllm/config/scheduler.py:42`) and two loops.
1. **Running loop (S:628–870).** Every RUNNING request, in admission order, gets `min(tokens it still needs, budget left)`
   (S:630; `long_prefill_token_threshold`, default 0, would cap a prefill chunk). A prefill in progress therefore takes the
   whole remaining budget of every step until its last chunk. Blocks for the chunk come from
   `KVCacheManager.allocate_slots` (S:745) with no admission gate; if the pool cannot provide them the scheduler preempts
   the most recently admitted running request (S:803; its blocks are freed, its computed tokens are lost, it returns to the
   **front** of the waiting queue, S:1580) unless that request's blocks cannot be freed yet (deferred free, S:2694).
2. **Waiting loop (S:872–1345)** — entered only if nothing was preempted in this step (S:873) and **only while token budget
   is left** (`while token_budget > 0`, S:885), also for requests that need no tokens (a lookup, an external load). It ends
   when `max_num_seqs` requests are running (S:893). Requests that already hold blocks (`kv_holding_waiting`: loads in
   transfer, loads that have arrived) are visited before the plain FCFS queue `waiting` (S:887).

### A1.2 The path of one waiting request (S:885–1340)
1. **Blocked states (S:899 → S:3099).** A request in `WAITING_FOR_REMOTE_KVS` whose load has not been reported finished is
   skipped: it is set aside for this step and the scan continues with the next request (`skip_request`, S:877; the skipped
   requests are put back in their order at the end of the step, S:1345).
2. **Local and external hit (S:931–1010).** For a request without computed tokens the scheduler takes the GPU prefix-cache
   hit, then asks the connector: `get_num_new_matched_tokens` (C:977) submits the LMCache lookup on the first call and
   returns `(None, True)` while it is pending → the request is skipped and the scan continues (S:956). So one pass of the
   scan submits the lookups of all waiting requests it reaches. With the result the call returns `(tokens to load,
   async=True)` for an external hit or `(0, False)`. The connector answers `(0, False)` for a PREEMPTED request (C:1011: a
   preempted hit is recomputed).
3. **What the step computes for it (S:1063–1170).** An external load schedules no tokens in this step (`num_new_tokens = 0`,
   S:1065). Any other request gets `min(tokens to compute, budget left)`: a miss starts with a chunk of at most 2,048 tokens.
4. **Block allocation = the admission gate (S:1195–1220 → K:371–614).** One call of `allocate_slots` with
   `full_sequence_must_fit = scheduler_reserve_full_isl` (**default True**, `vllm/config/scheduler.py:191`) and, for an
   external load only, `reserved_blocks = _inflight_prefill_reserved_blocks() + _spec_decode_step_blocks()` (S:1201). Inside:
   - **Full-sequence gate (K:519–536), every request:** the blocks the whole sequence (prompt plus tokens generated so far)
     still needs — beyond its local prefix-cache blocks, counting cached blocks that sit in the free queue — must not exceed
     the free blocks of the pool, else `None`. This holds for a miss as well: it is *allocated* chunk by chunk but *admitted*
     only if its whole prompt fits in the free blocks at that instant. No reservation is recorded: the check uses the raw
     free count, so two requests can be admitted against the same free blocks.
   - **Allocation gate (K:570–576):** the blocks this call takes — for an external load **all blocks of the external
     prefix at once**, for a miss the blocks of its first chunk — must fit in `free − reserved_blocks`.
     `reserved_blocks` is non-zero only for external loads: the blocks that in-flight prefills (S:3032; running requests
     still prefilling and loads in transfer) need to finish their sequences. The comment at S:1196: "An async load holds
     its blocks for the whole transfer with no forward progress and isn't preemptible here. Admit it only if it fits in
     (free − other in-flight reservations)".
   - Free blocks = `block_pool.get_num_free_blocks()` = every block not referenced by a live request, including blocks that
     still hold evictable prefix-cache content.
5. **Refusal (S:1223–1229).** If `allocate_slots` returns `None` the scheduler **`break`s the scan**: the request stays at
   the head of the queue, nothing behind it is visited in this step, and nothing falls back to another way of serving it.
   It is retried at every later step that reaches the waiting loop. (The `watermark` option, default 0.0, would keep an
   additional share of the pool free for waiting requests.)
6. **External load admitted (S:1258–1282).** Status `WAITING_FOR_REMOTE_KVS`; the request joins `_inflight_prefills`
   (S:1276) and is set aside; the connector marks it (`update_state_after_alloc`, C:1111) and emits **one** retrieve
   operation for the whole range `[local hit, external hit)` with the block ids (C:1388, M:283). The worker starts the load
   after launching the step's forward pass (W:83) and reports finished loads in the result of a later step (W:94); the
   scheduler records them in `update_from_output` (S:3133). At the next step **with token budget left** the request is
   visited in `kv_holding_waiting`, promoted (`_update_waiting_for_remote_kv`, S:3052), and goes through the allocation
   gate again for its uncached tail (not an async load any more, so no reservation) before it becomes RUNNING.
7. **Miss admitted (S:1289–1330).** RUNNING at once with its first chunk; it joins `_inflight_prefills` while it has
   prompt tokens left (S:1324) and leaves when its prefill ends (S:1609).

### A1.3 Answers to the inspection questions of the brief
| question | answer (SOURCE) |
|---|---|
| Where are external hits detected? | `C.get_num_new_matched_tokens` (C:977), called from the waiting loop (S:949) the first time the scan reaches a request without computed tokens; asynchronous (pending → the request is skipped, S:956). With `lmcache.mp.eager_prefetch` the lookup is submitted at arrival (C:1092) but its result is still taken only at a scan visit. |
| Where are GPU KV blocks allocated? | `K.allocate_slots` (K:371), called from the running loop (S:745) and the waiting loop (S:1207). |
| Must all external prefix blocks be reserved before loading? | Yes: the call allocates slots for every external token (`num_external_computed_tokens`) in one piece, and the connector issues one retrieve for the whole range (M:283–330). |
| What happens when the allocation fails? | The scan of the waiting queue stops for this step (S:1223–1229, `break`); no fallback; the request keeps its place. |
| Is the request retried? | At every later step that enters the waiting loop, i.e. every step in which the running requests leave token budget and nothing is preempted. Each retry calls `get_num_new_matched_tokens` again, which adds the hit to the connector's `num_stored_tokens` once more (C:1065) — see A1.4. |
| Are misses admitted with smaller chunks? | Allocated in chunks (≤ 2,048 tokens per step), **but admitted only if the whole sequence fits in the free blocks** (`scheduler_reserve_full_isl`, default True; K:519–536). |
| How is block availability tracked? | A free-block queue in the block pool (`get_num_free_blocks`, `vllm/v1/core/block_pool.py:871`); blocks of finished or preempted requests return to it, with a one-step delay under asynchronous scheduling for a KV-consumer connector (`defer_block_free`, S:176–181, S:2694–2736). |
| Preemption and reclamation? | Only from the running loop, when a RUNNING request cannot get the blocks of its next chunk: the last admitted running request is preempted (S:763–811, S:1538), loses its computed tokens and returns to the front of the waiting queue; an external hit that is preempted is recomputed (C:1011). Requests in `WAITING_FOR_REMOTE_KVS` are not preempted. |
| Does the scan stop after a failed allocation? | Yes (`break`), for hits and misses alike. A pending lookup or a load in transfer does not stop it (skip). |
| When does a finished load become schedulable? | When the worker's result that carries `finished_recving` has been processed (S:3133) **and** a later step enters the waiting loop with token budget left; the promoted request then needs budget for its tail tokens. |

### A1.4 What the source says about the 2026-11-04 explanation (to be tested in A2 / A3)
The earlier report (§7.2c) stated that "a miss is admitted with slots for one 2,048-token chunk and then grows as a running
request" while an external load must reserve its whole prefix. The source supports three more precise statements, and the
experiments below test them:
1. **At the block gate a miss and an external hit of the same length need the same number of free blocks** (the
   full-sequence gate applies to both); the hit additionally has to fit under the in-flight reservation. Whole-prefix
   allocation alone does not distinguish them.
2. **The in-flight reservation should usually be small when a load is evaluated**: the waiting loop runs only when the
   running requests left token budget, i.e. when every running prefill received all the tokens it still needed in this
   step; what remains reserved are the tails of loads in transfer.
3. **An external hit must pass the waiting loop twice** (admission of the load, promotion after the load) and each pass
   needs a step with token budget left, which a running prefill denies for the whole of its prefill; a miss passes once.
   Its lookup result, the finished load and its tail computation are each picked up only at such a step.
A side effect found in the source: every retry of a refused hit increases the connector's `num_stored_tokens` by the hit
length (C:1065), and the store path writes only tokens beyond that counter (M:248), so a hit that was refused at least
once may not store the KV of its new tokens (checked against the logs in §A2).

## A2. Admission instrumentation (MEASURED; `benchmarks/serving/kvadm/sitecustomize.py`, `analyze_adm.py`)
**Why.** The 2026-11-04 hooks recorded when a request was queued, when its load started and when it ran, not why it waited
in between. The brief asks for the scheduler's own numbers at every admission attempt.

**How.** `kvadm/sitecustomize.py` is loaded into the vLLM processes instead of the 2026-11-04 hook directory
(`serving_env.py`: `adm=true`); it first loads those hooks unchanged and then wraps, in the EngineCore process, four
functions — each wrapper calls the original with the original arguments and returns its result:
- `connector.get_num_new_matched_tokens` → one `poll` event per visit of a waiting request by the scan: lookup pending, or
  the external tokens to load;
- `KVCacheManager.allocate_slots` → one `adm` event per admission attempt of a request that is not RUNNING: tokens to
  compute, local and external hit tokens, the reservation the scheduler passed, the free blocks before the call, the
  blocks the full sequence needs and the blocks this call takes (computed with the allocator's own
  `get_num_blocks_to_allocate`), the result and the gate that failed (`full` = full-sequence gate, `free` = does not fit
  in the free blocks, `resv` = fits in the free blocks but not under the reservation); failures of RUNNING requests
  (`runfail`) and the tokens the running loop consumed per step;
- `Scheduler._preempt_request` → `preempt`;
- `Scheduler.schedule` → one `kv` line per step: free blocks before / after, pool size, queue lengths, loads in transfer
  and the blocks they hold, in-flight prefills and their reservation, tokens given to RUNNING requests (the budget left
  for the waiting loop is 2,048 minus that), deferred frees, heads of the two queues.
`analyze_adm.py` joins the stream with the per-request records and charges every engine step a request spent waiting to
one reason: its own refusal (`own:<gate>`), a refusal of another request that stopped the scan (`hol:<gate>`), the running
requests using the whole token budget so that the queue was not scanned (`budget`), the scan running out of budget on
requests admitted ahead (`budget_adm`), a pending lookup (`pending`), `slots`, `preempt`, `other`. Phases per request:
`pre` (queued → first visit), `lookup` (first visit → result known), `admit` (result → first successful allocation),
`load` (allocation → the engine notices the finished load), `promote` (noticed → RUNNING), `compute` (RUNNING → first token).
The client additionally records a hash of the generated text (`out_sha`) for the output-equality checks of §G.

### A2.1 Instrumented baseline: tool-agent replay at 0.04×, 320 GB host tier (MEASURED 2026-11-10 16:09–17:33, `replay/tool04-320-base`)
**Why.** The delay to explain was measured on this configuration (`dl-tool-dram320`, 2026-11-05). The replay is repeated with
the admission stream and nothing else changed: trace seconds 0–200 of the Mooncake tool-agent trace at 0.04× (1,159 requests,
4,982 wall s), 320 GB pinned-DRAM tier, 3B-AWQ, `max_num_seqs` 16, chunked prefill 2,048, asynchronous scheduling, stock
vLLM and LMCache. The pool came up at 7,456 blocks (7,612 in the 2026-11-05 run); later runs pin 7,456.

**Result 1 — the run reproduces the earlier one, with the extra instrumentation on.** All 1,159 requests completed; cached
share 0.431 (host 0.120, GPU 0.311); TTFT p50 / p95 / p99 1.563 / 20.76 / 33.86 s (2026-11-05: 1.56 / 20.7 / 33.8 s);
computed 1,117 prompt tokens/s (1,117); host-dominant hits 3.3 s p50, GPU-prefix hits 0.3 s, misses 5.1 s (the same three
numbers; `replay/tables-hitcat-tool04-320-base.md`). The admission stream costs nothing measurable, and a 2 % smaller pool
does not move the aggregates.

**Result 2 — where the waiting time goes (`replay/tables-adm-tool04-320-base.md`, Table 2).** Mean seconds per request
between queueing and RUNNING, charged step by step to the scheduler's reason:

| category | n | wait, mean (s) | token budget used up by running requests (queue not scanned) | scan ran out of budget on earlier admissions | another request refused, scan stopped (`hol:full`) | own refusal (`own:full`) | reservation gate (own + hol) | lookup pending | other |
|---|---|---|---|---|---|---|---|---|---|
| host-dominant hit | 148 | 7.59 | 4.27 (56 %) | 0.27 (4 %) | 1.81 (24 %) | 0.28 (4 %) | 0.02 (0 %) | 0.75 (10 %) | 0.19 (3 %) |
| GPU-prefix hit | 576 | 2.16 | 1.47 (68 %) | 0.10 (4 %) | 0.22 (10 %) | 0.01 (0 %) | 0.00 | 0.36 (16 %) | 0.00 |
| partial hit (10–50 %) | 121 | 3.34 | 2.09 (63 %) | 0.10 (3 %) | 0.71 (21 %) | 0.02 (1 %) | 0.01 | 0.40 (12 %) | 0.02 |
| miss | 301 | 3.87 | 2.36 (61 %) | 0.17 (4 %) | 0.57 (15 %) | 0.34 (9 %) | 0.00 | 0.44 (11 %) | 0.00 |

- **The largest cause for every class is the token budget (56–68 % of the waiting time):** in those steps the running
  requests — one prefill in progress is enough — took all 2,048 tokens, so the waiting loop was not entered and nobody in
  the queue was looked up, admitted or promoted. Such steps cover 18.6 % of the run's wall time.
- **Second: the full-sequence gate (10–28 %),** mostly as head-of-line blocking: the request at the head does not fit and
  the scan stops in front of everyone else. Only 59 of the 1,159 requests were themselves refused at least once.
- **The reservation gate is not a factor:** 4,924 refused attempts in the run — 3,615 of compute requests, 1,303 of external
  loads, 6 of promotions — and all but 17 were refused by the full-sequence gate (a refused load needed 456 blocks for its
  sequence where 287 were free, p50; a refused compute request 1,700 where 821 were free). The reservation the scheduler
  passed was 0 blocks at the median of the admitted loads (max 1,030). One preemption in the run.
- GPU KV memory is under pressure for a small part of the time (free blocks below 25 % of the pool: 9.2 % of the wall
  time; below 10 %: 3.7 %; mean used share 0.26).

![Figure A1](../../experimental_results/2026-11-10-gpu-kv-admission/figs/figA1-wait-by-reason.png)

*Figure A1 — where the waiting time goes, stock server, three replays (this one, A2.2 and the conversation trace under overload).
x: request category (number of requests); y: mean seconds per request between queueing and RUNNING, split by the scheduler's
reason at each engine step. Blue: the running requests used the whole token budget and the queue was not scanned.*

**Result 3 — phases (Table 1 there; median / mean seconds).** Host-dominant hits: `pre` 0.00 / 2.20, `lookup` 0.78 / 4.29,
`admit` 0.00 / 0.32, `load` 0.21 / 0.58, `promote` 0.00 / 0.20, `compute` 0.21 / 0.42. GPU-prefix hits: 0.00 / 1.09,
0.03 / 1.05, 0.00 / 0.01, (small loads) 0.09 / 0.38, 0.00 / 0.14, 0.17 / 0.29. Misses: 0.00 / 1.55, 0.03 / 1.98, 0.00 / 0.34,
–, –, 2.98 / 3.89. The hit's time is not in the allocation (`admit`) but in front of it: waiting for the scan to come
(`pre`), and to come again for the lookup result (`lookup`; the lookup itself takes milliseconds, its result is taken only
at a scan visit).

**Result 4 — the class comparison of the earlier study is confounded by the state of the engine at arrival (Table 6 there).**

| category | n | arrives while a prefill is in flight | TTFT p50, no prefill in flight at arrival (s) [n] | TTFT p50, prefill in flight (s) [n] | TTFT p50, free blocks ≥ 25 % of the pool [n] | TTFT p50, free blocks < 25 % [n] |
|---|---|---|---|---|---|---|
| host-dominant hit | 148 | 51 % | 0.32 [73] | 10.42 [75] | 2.43 [134] | 18.73 [14] |
| GPU-prefix hit | 576 | 28 % | 0.17 [415] | 5.41 [161] | 0.26 [559] | 11.62 [17] |
| partial hit | 121 | 34 % | 0.45 [80] | 8.25 [41] | 0.72 [117] | 11.32 [4] |
| miss | 301 | 36 % | 2.74 [193] | 11.84 [108] | 4.70 [289] | 25.47 [12] |

A host-dominant hit that arrives when no prefill is in flight answers in 0.32 s (twice a GPU-prefix hit, a ninth of a
miss); one that arrives during a prefill needs 10.4 s. The headline "3.3 s against 0.3 s" is the median of a class that is
split half and half between the two states, against a class that is in the fast state 72 % of the time. Host-dominant hits
meet a prefill in flight twice as often as GPU-prefix hits because the category itself depends on the load: a prefix is
served from the host tier exactly when the GPU prefix cache has lost it, i.e. after other requests have churned the pool.
Conditional on the state, an external hit is 1.9× slower than a GPU-prefix hit and faster than a miss in both states.

![Figure A2](../../experimental_results/2026-11-10-gpu-kv-admission/figs/figA2-ttft-by-arrival.png)

*Figure A2 — TTFT p50 per category, split by the state of the engine when the request arrived (blue: no prefill in flight;
orange: a prefill in flight); the number of requests in brackets. Same three replays.*

**Result 5 — a side effect of retries (SOURCE A1.4, confirmed).** Of the external loads whose lookup result was polled once,
137 of 137 with new chunks stored them all; of those polled twice or more (refused and retried; median 32 polls, max 320),
17 of 17 stored nothing: after a refusal the request's new tokens do not reach the host tier. A5 measures the same effect over
all requests of the run — it also hits compute requests whose prefix LMCache holds — and finds 48 requests and 6 % of the bytes.

**Explanation.** Three mechanisms, all in `Scheduler.schedule()`, in the order of their weight in this run:
1. *The waiting queue is served from what the running requests leave of the token budget* (A1.1). A prefill of 13.7k tokens
   takes seven steps of 2,048 tokens (about 3 s on this GPU), a 31k one fifteen; for that long nothing waiting is visited.
   This hits every class; it costs a hit most relative to what it needs (a transfer of 0.05 s and a tail of 0.6k tokens).
2. *The detour of a load.* A compute request that is visited starts at once and from then on is served by the running loop
   ahead of later arrivals. A load that is visited leaves for `WAITING_FOR_REMOTE_KVS`, its completion reaches the scheduler
   with the output of a later step, and it must be visited by the waiting loop again — behind every request that started
   computing in the meantime, a miss admitted in the same scan pass included. This is why, in the same state, a hit is slower
   than a GPU-prefix hit.
3. *The full-sequence gate under memory pressure,* with head-of-line blocking; it treats hits and misses alike.
The whole-prefix reservation of the earlier explanation is real (A1.2, step 4) but is not what makes the hits wait here.

### A2.2 Instrumented baseline under overload: tool-agent replay at 0.08×, 320 GB (MEASURED 2026-11-10 17:47–18:10, `replay/tool08-320-base`)
Trace seconds 0–100 at 0.08× (544 requests, 1,250 wall s), pool pinned at 7,456 blocks. All requests completed; cached share
0.355 (host 0.114, GPU 0.241); TTFT p50 / p95 / p99 12.4 / 40.8 / 47.4 s; GPU busy 0.87; backlog up to 42 (the 2026-11-05 run with
80 GB, `d-tool-dram80`: 12.7 / 40.9 / 48.1 s). Waiting time by reason (`replay/tables-adm-tool08-320-base.md`):

| category | n | wait, mean (s) | token budget | budget used by earlier admissions | `hol:full` | `own:full` | reservation gate | lookup pending |
|---|---|---|---|---|---|---|---|---|
| host-dominant hit | 106 | 18.95 | 10.28 (54 %) | 0.84 (4 %) | 6.04 (32 %) | 0.62 (3 %) | 0.01 | 0.96 (5 %) |
| GPU-prefix hit | 207 | 10.60 | 6.01 (57 %) | 0.48 (5 %) | 3.33 (31 %) | 0.09 (1 %) | 0.00 | 0.62 (6 %) |
| partial hit | 64 | 11.37 | 6.68 (59 %) | 0.56 (5 %) | 3.28 (29 %) | 0.15 (1 %) | 0.00 | 0.59 (5 %) |
| miss | 167 | 12.31 | 6.81 (55 %) | 0.59 (5 %) | 3.35 (27 %) | 0.89 (7 %) | 0.00 | 0.62 (5 %) |

The same order of causes as at the sustainable load: token budget first (54–59 %), the full-sequence gate with head-of-line
blocking second (28–35 %), the reservation gate absent (9 of 6,527 refused attempts; 1,991 of the 2,000 refused load attempts
failed the full-sequence gate, needing 425 blocks where 212 were free at the median). The confound is stronger here: a
host-dominant hit arrives with 16 % of the pool free at the median (GPU-prefix hit 52 %, miss 49 %) and 59 % of them during a
prefill; 65 % arrive with less than a quarter of the pool free (39 % of the GPU-prefix hits).

**Conversation trace at 0.08× (MEASURED 2026-11-10 18:10–18:33, `replay/conv08-320-base`).** Trace seconds 0–100 (291 requests,
1,292 wall s), same server. Cached share 0.075 (host 0.031, GPU 0.044): 11 host-dominant hits, 28 GPU-prefix hits, 186 misses.
TTFT p50 / p95 / p99 14.4 / 41.8 / 49.4 s. Waiting time by reason (`replay/tables-adm-conv08-320-base.md`): token budget 53–65 %
for every class (host-dominant hits 9.95 of 18.77 s, misses 7.98 of 13.75 s), `hol:full` 24–26 %, own refusal 0–10 %, lookup
pending 5–6 %. 6,363 refused attempts, every one at the full-sequence gate (a refused load needed 871 blocks where 542 were free,
p50), none at the reservation; 5 preemptions; free blocks below 25 % of the pool for 0.51 of the wall time. The decomposition
does not depend on the trace.

## A3. Controlled reproduction (MEASURED 2026-11-10 17:33–17:47, c28, `A3/a3-*`, tables `A3/tables-a3-a3.md`)
**Why.** The replay shows what happens to classes of requests that arrive under different conditions. To separate the
mechanisms the pressure has to be set, not inferred, and a hit has to be compared with a miss of the same length in the
same state.

**How.** `run_adm.py`, stock scheduler, 3B-AWQ, pool pinned at 7,456 blocks, 120 GB DRAM tier, 16 output tokens per probe.
Each trial starts K *holders* — long prompts that decode for the whole trial (2,000 output tokens) and hold their blocks —
sized so that a chosen number of blocks is free; then it sends *probes*: `host` = L tokens stored in LMCache and absent from
the GPU prefix cache plus 256 fresh tokens, `cold` = L + 256 fresh tokens. Where the probe cannot fit, the driver cancels one
holder 3 s after the probe (a release of ≈ 1,100–1,800 blocks at a known instant). The pressure a probe meets is read from the
admission stream (free blocks, blocks needed, gate at its first attempt), not from K. 114 trials: part 1, one probe,
L = 1k / 2k / 4k / 8k × free = 3.0 / 1.5 / 0.6 × the probe's need × host / cold × 3 repetitions, K = 6; part 2, the same at
4k with K = 4 and 12; part 3, two probes 5 ms apart with 700 free blocks, four orders; part 4, bursts of 4 and 8 probes of
2k alternating host / cold with room for half; part 5, two probes with more than 5,000 blocks free. No probe timed out, no
hook error.

**Result (Tables A3-1 … A3-6).**

| probe | free ≥ need: first attempt | TTFT (s), free = 3.0× / 1.5× | free = 0.6× need: first attempt (free / needed blocks) | admitted after the release (s) | TTFT (s) |
|---|---|---|---|---|---|
| host 1k | admitted, 3 of 3 | 0.34 / 0.32 | refused, full-sequence gate, 3 of 3 (68 / 80) | 0.06 | 3.32 |
| cold 1k | admitted | 0.36 / 0.35 | refused, full-sequence gate (64 / 80) | 0.06 | 3.34 |
| host 2k | admitted | 0.34 / 0.35 | refused, full-sequence gate (104 / 144) | 0.07 | 3.33 |
| cold 2k | admitted | 0.61 / 0.62 | refused, full-sequence gate (100 / 144) | 0.05 | 3.57 |
| host 4k | admitted | 0.34 / 0.34 | refused, full-sequence gate (180 / 272) | 0.06 | 3.34 |
| cold 4k | admitted | 1.03 / 1.04 | refused, full-sequence gate (178 / 272) | 0.07 | 4.01 |
| host 8k | admitted | 0.34 / 0.37 | refused, full-sequence gate (336 / 528) | 0.07 | 3.37 |
| cold 8k | admitted | 1.87 / 1.93 | refused, full-sequence gate (334 / 528) | 0.07 | 4.90 |

- **The block gate is symmetric.** With enough free blocks a hit is admitted at its first attempt whatever its length
  (TTFT 0.32–0.37 s under six decoding requests; lookup 0.05 s, load 0.13 s, tail 0.14 s) and a miss as well. With too few,
  the hit and the miss of the same length are refused by the same gate — the full-sequence gate, never the reservation
  (0 blocks reserved in all 72 trials) — and both are admitted within one engine step (0.05–0.07 s) of the release. The
  threshold is the request's own need: 80 / 144 / 272 / 528 blocks for 1k / 2k / 4k / 8k (+256); admitted at 139 / 234 /
  425 / 807 free, refused at 64–68 / 100–104 / 178–180 / 334–336.
- **The number of running requests does not matter at equal free blocks** (Table A3-2): 4k probes behind 4 and 12 holders
  behave as behind 6 (admitted at 420–446 free, refused at 171–203; TTFT 0.33–0.37 s for the hit).
- **Order decides who waits, not hit or miss** (Table A3-3, 700 free blocks): whichever probe comes first is admitted; the
  second is refused by the full-sequence gate (a hit of 4k with 189 free, a miss of 4k with 189 free, a miss of 8k with
  445–461 free) and enters when the first one finishes. In second position the hit's TTFT is 2.64 s, the 4k miss's 3.33 s.
- **Without memory pressure a hit next to a prefill is no faster than the prefill** (Table A3-5, > 5,000 blocks free): hit
  first, then an 8k miss 5 ms later → hit 1.70 s, miss 1.62 s (the hit's load is noticed 1.5 s after it was issued, i.e.
  when the miss's four chunks are through); miss first → miss 1.63 s, hit 1.77 s (its lookup result is taken 1.1 s after
  the first visit). Alone the same hit takes 0.34 s.
- **In bursts hits are not ahead of misses** (Table A3-4): TTFT p50 1.83–2.01 s (hits) vs 1.69–1.83 s (misses) for four
  probes, 2.41–2.86 vs 2.21–2.27 s for eight; half of each burst is refused at first by the full-sequence gate.

![Figure 1](../../experimental_results/2026-11-10-gpu-kv-admission/figs/fig1-occupancy-vs-wait.png)

*Figure 1 — GPU KV occupancy against the admission wait of external hits. Left, controlled probes: x = free blocks at the
probe's first admission attempt divided by the blocks its whole sequence needs (log scale); y = seconds from the lookup result to
admission. Hits (dots) and misses of the same length (crosses) fall on the same two levels: admitted at once when the sequence
fits, admitted when the holder is released (3 s) when it does not. Right, the host-dominant hits of the three stock replays:
x = share of the pool in use when the request arrived; y = seconds from queueing to the admission of its load (log scale);
triangles arrived while a prefill was in flight. At low occupancy the wait is 3–30 ms without a prefill in flight and 1–30 s
with one; occupancy alone does not predict the wait until the pool is nearly full.*

![Figure 2](../../experimental_results/2026-11-10-gpu-kv-admission/figs/fig2-length-vs-wait.png)

*Figure 2 — prefix length against the admission wait (left) and TTFT (right), controlled probes of part 1. x: length of the
cached prefix (the probe has 256 fresh tokens more); lines: external hit and miss at three levels of free blocks relative to the
probe's need. The wait is 0 s or the 3 s until the release for every length and for hits and misses alike; the TTFT of a hit
does not grow with its prefix, that of a miss does.*

**Explanation.** These trials answer the brief's questions for the block gate: admission of an external hit starts to fail
when the free blocks fall below the blocks of its whole sequence — the same point at which a miss of that length fails;
the number of concurrent requests is irrelevant beyond the blocks they hold; and a miss does not "make progress while the
hit waits" at the gate: what progresses are requests already RUNNING, which take their next chunk without a gate. What the
hit loses relative to a miss is not at the gate but around it (parts 3–5): its lookup result, its finished load and its
promotion are each picked up only at a step with token budget left, and a miss that starts in between takes the budget
first.

### A3.1 The same trials with the full-sequence gate switched off (MEASURED 2026-11-10 18:18–18:49, 16 GB node c60, pool pinned at 7,456 blocks; `E16/a3gate/a3g-base`, `a3g-noisl`)
**Why.** A1 says the admission asymmetry of the earlier explanation is removed by `scheduler_reserve_full_isl`, which is on by
default. If that is right, switching it off (`--no-scheduler-reserve-full-isl`, a stock flag) must bring the asymmetry back.

**How.** The 114 trials of A3, twice on one node: stock flags, and with the gate off. Nothing else differs.

**Result.**
| probe, free = 0.6 × need | gate on: first attempt | gate on: TTFT (s) | gate off: first attempt | gate off: TTFT (s) |
|---|---|---|---|---|
| host 4k (needs 256 blocks at once; 180 free) | refused (`full`) | 3.35 | refused (`free`) | 3.34 |
| cold 4k (first chunk 128 blocks; 178 free) | refused (`full`) | 4.00 | **admitted** | 3.62 |
| host 8k (512 at once; 335 free) | refused (`full`) | 3.37 | refused (`free`) | 3.36 |
| cold 8k (first chunk 128; 334 free) | refused (`full`) | 4.89 | **admitted** | 4.10 |
| host 1k (64 at once; 68 free) | refused (`full`) | 3.32 | admitted (the load fits; the tail does not yet) | 0.31 |
| cold 1k (80 in one chunk; 68 free) | refused (`full`) | 3.36 | refused (`free`) | 3.34 |

With the gate on, the node reproduces c28's A3 to the hundredth of a second (hit and miss refused together, admitted 0.06–0.08 s
after the release). With the gate off, **a miss is admitted with its first chunk where a hit of the same length is refused
for its whole prefix** — the mechanism of the 2026-11-04 explanation, observed directly — and the run has 23 preemptions and
46 failed chunk allocations of running requests against 2 and 4 with the gate on. In the two-probe trials the gate-off server
admits the 8k miss next to the 4k hit that came first (700 free blocks), and the hit's TTFT rises from 0.35 to 1.52 s.

**Explanation.** The earlier explanation describes vLLM without the full-sequence reservation. vLLM 0.31's default closes that
gap from the other side: it makes a miss wait for its whole sequence as well. Switching the gate off does not help hits (they
are refused at the same free-block counts as before) and costs preemptions.

## A4. Answers to the analysis questions of Experiment A
First admission attempts against the occupancy at that instant (`replay/tables-first-<tag>.md`, `adm_first_attempts.py`; MEASURED,
stock runs; refused attempts / attempts):

| run | kind of request | attempts | pool in use < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| `tool04-320-base` | external load | 191 | 0 / 118 | 0 / 16 | 3 / 25 | 7 / 16 | 11 / 13 | 3 / 3 |
| `tool04-320-base` | compute (miss, GPU-prefix hit) | 968 | 0 / 738 | 0 / 117 | 8 / 61 | 13 / 31 | 6 / 15 | 6 / 6 |
| `tool08-320-base` | external load | 126 | 0 / 10 | 0 / 15 | 2 / 34 | 4 / 20 | 21 / 30 | 17 / 17 |
| `tool08-320-base` | compute | 418 | 0 / 166 | 0 / 53 | 11 / 63 | 16 / 46 | 23 / 49 | 26 / 41 |
| `conv08-320-base` | external load | 14 | 0 / 3 | 0 / 3 | 0 / 1 | 2 / 2 | 2 / 3 | 2 / 2 |
| `conv08-320-base` | compute | 277 | 0 / 92 | 0 / 38 | 15 / 61 | 18 / 32 | 23 / 36 | 17 / 18 |

1. **At what GPU KV occupancy does external-hit admission begin to fail?** When the free blocks fall below the blocks of the
   request's whole sequence. In the controlled trials that is exact (A3: a 4k hit needs 272 blocks, is admitted with 425 free and
   refused with 180). In the replays none of the 1,369 first attempts made while less than 75 % of the pool was in use was
   refused; of the loads' first attempts in the two tool-agent replays (sustainable load, overload) 12 % and 6 % were refused
   at 75–90 %, 44 % and 20 % at 90–95 %, 85 % and 70 % at 95–98 %, and all above 98 %. Compute requests follow the same curve.
2. **How many blocks does the hit need?** The refused loads needed 450 blocks for their full sequence at the sustainable load
   (p50; 312–1,505 p10–p90; about 7.2k tokens) and 409 under overload; the loads admitted at once needed 387 (p50).
3. **How many are available?** 353 free blocks at the refused first attempts at the sustainable load (p50; 139–906), 217 under
   overload (34–382): the request needs 1.6× and 2.0× what is free (median). Admitted first attempts saw 5,542 and 1,222 free.
4. **Why can a miss make progress while a hit waits?** At the block gate it cannot: with vLLM 0.31's default
   (`scheduler_reserve_full_isl`) a hit and a miss of the same length are refused at the same free-block count and admitted in
   the same step after a release (A3). What makes progress while a hit waits are (a) requests that are already RUNNING, which
   take the blocks of every further chunk without a gate, (b) a miss that was visited by the same scan pass: it starts
   computing at once and from then on is served by the running loop, while the hit leaves for the load and needs two more
   visits by the waiting loop. With the gate switched off the miss-first asymmetry of the 2026-11-04 explanation appears
   (A3.1), at the price of preemptions.
5. **Does the waiting-queue scan or the token budget also contribute?** It is the main contributor: the waiting loop runs only
   on budget the running requests leave, and one prefill in progress leaves none.
6. **What fraction of the waiting time comes from each mechanism?** For host-dominant hits: token budget (queue not scanned)
   56 % at the sustainable load and 54 % under overload, plus 4 % of budget used by earlier admissions of the same scan;
   full-sequence gate 28 % and 35 % (of which head-of-line blocking 24 % and 32 %, own refusal 4 % and 3 %); in-flight
   reservation gate 0.3 % and 0.1 %; pending lookup 10 % and 5 %. The other classes have the same order (A2.1, A2.2).
7. **Does the proposed cause explain the long delays in the real tool-agent trace?** No. Whole-prefix reservation under the
   in-flight reservation refused 17 of 4,924 attempts at the sustainable load, 9 of 6,527 under overload and none in the
   conversation replay. The long delays are explained by the token budget of the step (hits wait for running prefills like
   everybody else, and need more step boundaries than a miss), by the full-sequence gate with head-of-line blocking when the
   pool is more than about 75 % in use, and — for the size of the class gap — by the fact that prefixes are served from the
   host tier mostly when the engine is busy and the pool has been churned (A2.1, Result 4).

**A side observation: a waiting request does not pin its GPU-cached prefix.** Between a request's first visit and its
admission its GPU prefix hit can be evicted by the requests that run meanwhile: 20 requests lost 101k tokens of prefix that
way at the sustainable load (3.3 % of the GPU-prefix tokens seen at the first visits), 36 requests lost 117k tokens (11.7 %)
under overload; every one of them was then served by a load from the host tier. Part of what the replays count as host-tier
hits are GPU-prefix hits that waited too long — the host tier catches what the queueing delay costs the GPU cache.

## A5. A side effect of admission retries: KV that never reaches the host tier (SOURCE + MEASURED; `store_loss.py`, `replay/tables-store-loss.md`)
**Why.** A1.4 noted that every poll of a waiting request adds the LMCache hit length to the connector's stored-token counter. A2.1
(Result 5) confirmed it for refused loads. The same code path serves every request that has *any* LMCache hit — also a GPU-prefix
hit whose prefix LMCache holds as well, and a near-miss that shares one 256-token chunk with an earlier prompt — so the size of the
effect was measured over all requests.

**How (SOURCE).** `get_num_new_matched_tokens` runs `tracker.increase_num_stored_tokens(ret)` whenever the lookup result `ret` is
non-zero (C:1065) — on every call, and the stock scheduler calls it again at every step in which it visits a request it could not
admit (A1.3). The store path writes the chunks from `start_token_idx = tracker.num_stored_tokens` (M:252). After k polls the
counter stands at k × ret: the tokens between ret and k × ret are never stored, and nothing at all once k × ret exceeds the prompt
(a refused request is polled 32 times at the median, A2.1). LMCache finds a prefix chunk by chunk, so chunks stored behind such a
hole cannot be found by a later request either.

**Result (MEASURED; the first three rows are the 2026-11-05 runs, which had no admission instrumentation).** A request "with a new
chunk" has at least one full 256-token chunk beyond what a cache served; expected bytes = new full chunks × 256 tokens × 36 KiB.

| run | requests with ≥ 1 new chunk | of those stored nothing | GB stored | GB expected | missing | polled with a result once: n / stored nothing | polled ≥ 2 times: n / stored nothing / GB stored of expected |
|---|---|---|---|---|---|---|---|
| `dl-tool-dram320` (2026-11-05, tool-agent 0.04×) | 981 | 48 | 187.9 | 200.5 | 6 % | – | – |
| `d-tool-dram80` (2026-11-05, tool-agent 0.08×) | 478 | 77 | 74.6 | 107.5 | 31 % | – | – |
| `dl-conv-dram320` (2026-11-05, conversation 0.04×) | 584 | 26 | 198.4 | 209.3 | 5 % | – | – |
| `tool04-320-base` | 981 | 48 | 187.9 | 200.5 | 6 % | 927 / 1 | 54 / 47 / 2.2 of 21.8 |
| `tool08-320-base` | 477 | 82 | 73.8 | 107.2 | 31 % | 368 / 0 | 109 / 82 / 9.4 of 45.0 |
| `conv08-320-base` | 290 | 54 | 76.7 | 112.6 | 32 % | 209 / 0 | 81 / 54 / 10.3 of 48.3 |
| `tool08-320-sync` (stock flag) | 477 | 87 | 71.8 | 107.2 | 33 % | 363 / 0 | 114 / 87 / 9.7 of 47.2 |
| `tool08-320-tokfast11` (prototype v1.1, counter repaired at every poll) | 475 | 1 | 108.7 | 105.1 | 0 % | 146 / 0 | 329 / 1 / 88.9 of 86.4 |

- **The stock system loses 5–6 % of the KV it should store at a sustainable load and 31–33 % under overload,** on both traces, with
  and without the instrumentation of this study (the 2026-11-05 rows). Requests polled once store everything (1 exception in 1,504);
  requests polled twice or more store 10–21 % of their bytes, and what they store lies behind a hole.
- The loss grows with congestion because only requests that had to wait are polled again — the busier the engine, the less of
  what it computes reaches the host tier, which is when the host tier would be most useful.
- With the counter repaired (`storefix`, B7) the same replay stores 108.7 GB instead of 73.8 GB.

**Explanation.** A counter that is meant to say "this much of the prompt is already in the store" is incremented by a polling loop
instead of being set once. It is harmless while every request is admitted at its first visit, which is why it does not show in
light-load tests. The 2026-11-04 study's host-tier occupancy and hit shares under overload were measured with this loss in place.

## B. Mechanism evaluation

### B0. The prototype mechanisms (`benchmarks/serving/kvadm/kvadm_policy.py`; flags in the vLLM process environment, `KVADM_POLICY=…`)
**Why these, from A.** The delay has three parts with different remedies. (1) The waiting queue gets only what the running
requests leave of the token budget → keep a bounded share of the budget for short work and keep the scan alive. (2) The load
detour: lookup result, finished load and promotion are each picked up at a step boundary, and a prefill step is long → make
the steps short while such work is under way. (3) The full-sequence gate with head-of-line blocking under memory pressure →
let requests that fit pass a request that does not, with a bound on how long it can be passed and a bounded block
reservation for the hits that are passed. The brief's B2–B5 map onto (3) and onto the two gates of A1.2; A predicts that
relaxing the reservation gate (B2 in its literal form) and chunked loading (B3) cannot help, because the gate that refuses
loads is the full-sequence gate, which every admission shares. Both are tested rather than assumed.

**How they are built.** No vLLM or LMCache source is patched. The hook wraps three existing interfaces of the scheduler
process, and with `KVADM_POLICY` unset every wrapper returns its input (the instrumented baseline):
1. the connector's answer `get_num_new_matched_tokens`: `(None, True)` is what the connector returns for a pending lookup,
   and the stock scheduler then sets the request aside for this step and scans on; `(0, False)` makes it compute the prompt;
2. the `reserved_blocks` argument of `allocate_slots`;
3. `scheduler_config.long_prefill_token_threshold` (vLLM's own per-step cap of a prefill chunk) and
   `max_num_scheduled_tokens` (the step's token budget), both read at the start of every `schedule()`.

| flag | mechanism | addresses |
|---|---|---|
| `tokres=<n>` | **Token reserve.** Before each step: tokens needed by loads that have arrived (their uncached tail), by waiting compute requests whose need is known and ≤ n (GPU-prefix hits, short prompts) and whose blocks are free, plus 1 token if anything else waits (so that the scan runs). Running long prefills (more than n tokens left) are capped so that this amount, at most n, is left of the budget. | (1) |
| `minchunk=<m>` | A compute request is not started in a step with fewer than min(its need, m) budget tokens left (it is set aside for this step). Default n + 256 with `tokres`, so that the reserve can never start a long prefill: long work stays first-come-first-served. | keeps (1) from turning into round-robin among prefills |
| `fastchunk=<f>` | **Short steps while short work is under way** next to a long prefill (a request not yet visited or its lookup pending, a load in transfer or arrived, a short tail running): the whole step's budget is f instead of 2,048 — more if the short work itself needs more — and each long prefill keeps at least `mincap` = 256 tokens of it. A request counts as short work under way for a bounded number of engine steps per phase (lookup 3, load in transfer 10, promotion 4, short compute request 4; `faststeps` scales them): one that stays longer is waiting for memory or for its turn, which short steps do not help. | (2) |
| `skip=<s>` | **No head-of-line blocking by a request that does not fit.** The two block gates are evaluated before the scheduler tries the allocation; a request that would be refused is set aside for this step instead (requests behind it are visited) until it has waited s seconds since its lookup result; after that the stock behaviour returns: its refusal stops the scan, so freed blocks go to it first. | (3), starvation bound |
| `hitres=<b>` | **Bounded block reservation for skipped hits** (the brief's B2): while external hits are set aside for lack of blocks, other compute requests are admitted only if they leave min(b, blocks those hits need) free. Nothing is reserved when no hit is waiting. | (3), for hits |
| `alpha=<a>` | Scale the stock in-flight reservation charged to a load (1 = stock, 0 = a load is admitted under the same block rule as a miss). | the reservation gate (B2, literal form) |
| `resvall` | A compute request that is started while a prefill is in flight must fit under the in-flight reservation, as the stock scheduler demands of a load; otherwise it is set aside for this step. Needed only because the token reserve lets requests in during a prefill, which the stock scheduler never does. | preemptions caused by (1) |
| `blkfirst` | A compute request that would fail the block gates is never set aside by the token rules (`minchunk`, `resvall`): it gets the stock treatment — its allocation is refused and the scan stops there — unless `skip` is set and it is inside its skip time. Keeps the token reserve from passing a request that waits for *blocks*. | starvation caused by (1) under memory pressure |
| `agecap=<s>` | **Starvation bound.** While a waiting request that is not short work (a compute request that needs more than `tokres` tokens, or an external hit that waits for blocks) has been queued for more than s seconds, every mechanism is suspended and the scheduler runs with its stock rules until that request is admitted. The store-counter fix stays on. | bounds what (1)–(3) can cost long requests |
| `fallback=<s>` | **Compute fallback** (B5): a hit that still fails the gates s seconds after its lookup result is computed instead of loaded if the compute path passes the gates. | (3) |
| `storefix` | Undo the repeated addition to the connector's `num_stored_tokens` when a waiting hit is polled again (A1.4); applied automatically with every mechanism that makes the scheduler poll a request again. | side effect of A |

**Versions of the module, and why there are four.** Each version was replaced because a measurement showed a flaw; the runs made
with the earlier versions are kept and labelled.

| version | commit | flags added / changed | what the measurements with the previous version showed |
|---|---|---|---|
| v1 | 537d2ff | `tokres`, `minchunk`, `fastchunk`, `skip`, `hitres`, `alpha`, `fallback`, `storefix` | – |
| v1.1 | 1b5fa31 | store-counter fix at every poll with a result; the reserve counts a request for a bounded number of steps and a short compute request only if its blocks are free; a long prefill keeps 256 tokens of a short step | `replay/tool08-320-tokfast` (v1): stores fell from 73.8 to 31.3 GB — the fix covered only loads, and `minchunk` makes the scheduler poll GPU-prefix hits again (A5); 24 % of the run in short steps with the prefill at its 128-token floor while the short work was waiting for memory, not tokens; TTFT p95 58.8 s against 40.8 s |
| v1.2 | 9f3b1c8 | `resvall` | `replay/tool08-320-tokfast11` (v1.1): 32 preemptions against 5 — short compute requests admitted during a prefill took blocks the prefill still needed |
| v1.3 | 68acb27 | `agecap` | the same run: requests that are not short work waited behind a continuous stream of short work (longest TTFT 77.7 s against 53.2 s) |
| v1.4 | 49c3585 | `blkfirst` | the same run, traced request by request: in every step in which little budget was left the token rule set a memory-blocked request aside and admitted short work behind it, i.e. an unbounded head-of-line bypass that nobody had asked for; one request that needed 50 blocks waited 48 s after its first refusal while 22 others were admitted |

The configurations evaluated end to end are cumulative: **P1** = `tokres=768,fastchunk=512,resvall,blkfirst` (token reserve and
short steps in their safe form), **P2** = P1 + `skip=3,hitres=600` (bounded head-of-line bypass), **P3** = P2 + `agecap=20`
(starvation bound). `kvadm/test_policy.py` drives the module with stand-ins for the scheduler and checks each rule (9 cases).

### B1. Baseline and the scheduler options vLLM already has (MEASURED 2026-11-10 19:27–19:58, 16 GB node c66, pool pinned at 7,456 blocks; `E16/c1c/`, table `E16/c1c/tables-c1c.md`)
**Why.** A prototype has to beat what the engine can already be configured to do. The options that touch the causes found in A:
synchronous scheduling (`--no-async-scheduling`: one batch in flight instead of two, so an event reaches the scheduler one step
sooner), a per-step cap on a prefill chunk (`--long-prefill-token-threshold 1024`: half of every step's budget is left to other
requests), a smaller step for everybody (`--max-num-batched-tokens 512`), priority scheduling with hits first (needs the client to
label its requests; controlled workloads only, C1) and the full-sequence gate off (A3.1).

**How.** Scenario c1, "compute contention without memory pressure" (`run_adm.py plan=c1`): six small holders decode, 5,500 of the
7,456 blocks are free; a miss of 8k, 16k or 28k tokens (the *blocker*) starts prefilling; external hits of 4k tokens (+256 fresh
tokens) are sent 0.5, 2.5 and 4.5 s after it and a 4k miss 1.5 s after it; 16 output tokens per probe; 3 repetitions; medians. Every
configuration runs the same 9 trials on the same node. The cells are TTFT / request time in seconds.

| blocker | probe | stock | synchronous | prefill cap 1,024 | step budget 512 |
|---|---|---|---|---|---|
| 28k | blocker miss | 7.33 / 8.71 | 7.35 / 8.78 | 8.64 / 9.00 | 8.52 / 9.91 |
| 28k | hit +0.5 s | 7.83 / 8.33 | 7.83 / 8.37 | 2.27 / 7.86 | 9.30 / 9.71 |
| 28k | 4k miss +1.5 s | 6.68 / 7.28 | 6.72 / 7.36 | 2.97 / 7.21 | 8.23 / 8.69 |
| 28k | hit +2.5 s | 5.97 / 6.36 | 5.94 / 6.39 | 4.31 / 6.40 | 7.48 / 7.78 |
| 28k | hit +4.5 s | 4.08 / 4.37 | 4.05 / 4.40 | 3.09 / 4.44 | 5.56 / 5.79 |
| 16k | hit +0.5 s | 4.05 / 4.47 | 4.04 / 4.51 | 2.26 / 4.42 | 4.83 / 5.21 |
| 8k | hit +0.5 s | 2.00 / 2.29 | 1.98 / 2.32 | 1.45 / 2.35 | 2.41 / 2.70 |

**Result.**
- **Stock:** every request sent during the blocker's prefill gets its first token after the blocker's (7.33 s for 28k): the hits at
  7.83 / 5.97 / 4.08 s, the 4k miss at 6.68 s. An external hit on this engine takes 0.2–0.3 s when no prefill is running (the
  hits sent after the 8k blocker has finished: 0.21–0.23 s).
- **Synchronous scheduling** changes nothing here (within 0.03 s): the queue is still not scanned during the prefill.
- **Prefill cap 1,024** lets the first hit in (2.27 s) because half of every step's budget is left over — and the 4k miss as well
  (2.97 instead of 6.68 s), after which two prefills share the steps: the blocker's first token comes 18 % later (8.64 s), and the
  later hits wait while the two prefills use the whole budget (4.31 / 3.09 s). On the overloaded replay the same option is worse
  than stock on every metric (TTFT p50 17.7 against 12.4 s, 74 preemptions against 5; C2): with the cap long prefills advance
  round-robin, more requests hold their blocks at the same time, and the pool fills.
- **A 512-token step for everybody** is worse everywhere (hits 9.30 / 7.48 / 5.56 s, blocker +16 %): the prefill still takes every
  step whole, and small steps cost throughput.

**Explanation.** None of the existing options separates the two things the waiting queue needs — a visit, which costs no GPU work,
and tokens — from the question of who gets the GPU. The cap comes closest and pays for it by starting long work early.

### B2. Token reserve and short steps (`tokres`, `minchunk`, `fastchunk`; MEASURED 2026-11-10 19:27–19:58, same node and scenario; `E16/c1c/`)
**What changed.** Before every step the hook caps the running long prefills (through vLLM's own per-request cap) so that the
tokens short work needs are left in the budget: the uncached tails of loads that have arrived, compute requests that need at most
`tokres` = 768 tokens and whose blocks are free, or a single token if anything else waits, which is enough for the scan to run,
lookups to be submitted and loads to be issued. `minchunk` (1,024) keeps the reserve from starting a long prefill: a compute request
is not started in a step with fewer budget tokens left than min(its need, 1,024), so long work stays first-come-first-served. With
`fastchunk` = 512 the whole step is limited to 512 tokens while short work is in the pipeline (B0), so that the step boundaries a
hit needs come 0.08 s apart instead of 0.3 s.

**What problem it addresses.** Causes 1 and 2 of A: the waiting loop is not entered during a prefill, and a hit needs four step
boundaries (lookup result, load issued, load noticed, tail computed), each a full prefill step away and two batches deep under
asynchronous scheduling.

| blocker | probe: TTFT / request time (s) | stock | reserve only (`tokres=768`) | reserve + 512-token steps | reserve + 256-token steps | reserve + 512-token steps, synchronous |
|---|---|---|---|---|---|---|
| 28k | blocker miss | 7.33 / 8.71 | 7.40 / 8.71 | 8.36 / 9.28 | 8.27 / 9.43 | 8.09 / 9.27 |
| 28k | hit +0.5 s | 7.83 / 8.33 | 4.17 / 8.10 | 1.62 / 5.71 | 1.25 / 4.93 | **0.94** / 4.94 |
| 28k | 4k miss +1.5 s | 6.68 / 7.28 | 6.80 / 7.25 | 7.44 / 7.81 | 7.62 / 7.97 | 7.45 / 7.81 |
| 28k | hit +2.5 s | 5.97 / 6.36 | 5.64 / 6.24 | 1.89 / 6.47 | 1.73 / 6.51 | **1.04** / 6.48 |
| 28k | hit +4.5 s | 4.08 / 4.37 | 3.93 / 4.28 | 2.67 / 4.74 | 1.90 / 4.86 | **1.10** / 4.68 |
| 28k | sum of the five request times | 35.05 | 34.57 | 34.01 | 33.70 | 33.17 |
| 16k | blocker miss | 3.62 / 4.79 | 3.88 / 4.85 | 4.14 / 5.14 | 4.28 / 5.27 | 4.06 / 5.23 |
| 16k | hit +0.5 s | 4.05 / 4.47 | 3.74 / 4.37 | 1.61 / 4.42 | 1.25 / 4.46 | 0.93 / 4.43 |
| 16k | hit +2.5 s | 2.17 / 2.50 | 2.15 / 2.49 | 2.01 / 2.69 | 1.99 / 2.82 | 1.03 / 2.71 |
| 16k | sum of the five request times | 15.77 | 15.67 | 16.76 | 17.32 | 16.99 |
| 8k | hit +0.5 s | 2.00 / 2.29 | 1.98 / 2.28 | 1.55 / 2.31 | 1.31 / 2.34 | 0.93 / 2.31 |
| 8k | sum of the five request times | 7.04 | 7.05 | 7.28 | 7.53 | 7.45 |

**Did it work?** For the first token, yes. The reserve alone admits the hit during the prefill (4.17 instead of 7.83 s) but each of
its step boundaries is still a 2,048-token step (its load phase lasts 2.3 s for a transfer of 0.05 s). With short steps the three
hits answer in 1.6–2.7 s, with 256-token steps in 1.3–1.9 s, and with synchronous scheduling on top — one batch in flight — in
**0.94–1.10 s, 4–8× sooner than stock** and 0.7–0.9 s above a hit on an engine without a prefill. Figure 4 shows the request
timelines of one repetition.

![Figure 4](../../experimental_results/2026-11-10-gpu-kv-admission/figs/fig4-request-timelines.png)

*Figure 4 — what each request of scenario c1 does over time behind a 28k-token prefill, stock (top) and with the token reserve,
512-token steps and synchronous scheduling (bottom); one repetition. Black tick = first token.*

**Side effects (the same table).**
- **The request time of the hits does not improve unless the prefill is long.** After its first token a request decodes one token
  per engine step, and while the blocker is prefilling a step is a 2,048-token chunk (0.3 s): the 16 output tokens of the first hit
  take as long as the rest of the blocker's prefill. Behind the 8k and 16k blockers the hits finish when they finished before
  (2.29 → 2.31 s, 4.47 → 4.43 s); behind the 28k blocker the first hit finishes 41 % sooner (8.33 → 4.94 s) and the two later ones
  2–11 % later. The mechanism moves the first token, not the last.
- **The blocker pays:** first token +10–18 % (7.33 → 8.09–8.36 s at 28k, 3.62 → 4.06–4.28 s at 16k), request time +6–10 %. The 4k
  miss pays +11–18 % (it now shares its steps with decoding hits).
- **Total work is not reduced:** the sum of the five request times is 3–5 % lower at 28k and 3–10 % higher at 8k and 16k.
- Nothing is refused or preempted in this scenario (no memory pressure): 0 preemptions in every configuration.

**Why it works, and why not further.** The hit's four step boundaries now come every 0.08–0.15 s instead of 0.3 s, and its load and
tail ride in steps that also carry a slice of the prefill. What remains is the pipeline itself: five or six short steps from arrival
to first token, plus up to one full prefill step that was already issued when the hit arrived (two under asynchronous scheduling).

### B3. Letting requests that fit pass a request that does not (`skip`, `hitres`; MEASURED 2026-11-10 19:58–20:07, node c66; `E16/c2b/c3b-*`, table `E16/c2b/tables-c3b.md`)
**What changed.** The hook evaluates the two block gates of `allocate_slots` before the scheduler tries the allocation. A request
that would be refused is set aside for this step — the connector's "lookup pending" answer, which the stock scheduler handles by
scanning on — instead of ending the scan. `skip=<s>` bounds this: `s` seconds after its lookup result the request gets the stock
treatment again (its refusal stops the scan, so every block that is freed goes to it first). `hitres=<b>` adds a bounded block
reservation for external hits that are being passed: compute requests are admitted only if they leave min(b, the blocks those hits
need) free; nothing is reserved when no hit is waiting.

**What problem it addresses.** Cause 3 of A (24–35 % of the hits' waiting time in the replays): the request at the head of the
queue does not fit, and the scan stops in front of requests that would.

**How.** Scenario c3 (`run_adm.py plan=c3`): six holders leave 600 free blocks; a 16k miss (needs 1,041) arrives, followed 50, 100
and 150 ms later by two external hits and a miss of 2k (145 blocks each) and 1 s later by another 2k hit; one holder is released
after 4 s (about 1,140 blocks). 3 repetitions; medians of TTFT (s) with the gate of the first attempt.

| probe | stock | `skip=2` | `skip=3,hitres=600` + token reserve and short steps |
|---|---|---|---|
| #1 miss 16k (does not fit) | 7.98 (refused: full-sequence gate) | 7.97 | 7.97 |
| #2 hit 2k | 8.70 | **0.75** | 0.75 |
| #3 hit 2k | 8.65 | **0.82** | 0.82 |
| #4 miss 2k | 8.35 | **0.65** | 0.65 |
| #5 hit 2k, 1 s later | 7.88 | **0.35** | 0.35 |
| refused admission attempts of the probes | 492 | 243 | 120 |
| preemptions | 0 | 0 | 0 |

**Did it work?** Yes, and at no cost in this scenario: the four requests that fit are served in 0.35–0.82 s instead of 7.9–8.7 s,
and the request that does not fit is admitted at the same instant as before (the release) and answers in the same 7.97 s. In the
stock run the four small requests wait twice: first behind the refused request, then — once it is admitted — for its whole prefill.

**Why.** The stock scan confuses "this request cannot be admitted" with "nothing can be admitted". The blocks the small requests
take (435 of the 600 free) are not blocks the large request could have used: it needs 1,041.

**Side effects, and what the reservation is for.** A request that is passed can be starved by the requests that pass it if they
keep taking the blocks that are freed; the `skip` bound limits that to `s` seconds, and `hitres` keeps blocks aside for a passed
hit. Scenario c5 measures both (B3.1).

### B3.1 How long may a request be passed, and how much should be kept for it? (the brief's B2; MEASURED 2026-11-10 22:07–22:38, node c66; `E16/c5/`, table `E16/c5/tables-c5.md`)
**Why.** B3 shows the bypass where the passed request loses nothing. The brief asks what a reservation for a waiting external hit
buys and costs: how much, when, whether it prevents starvation, whether it takes memory from active requests, what it does to
misses, whether it causes preemptions.

**How.** Scenario c5 (`run_adm.py plan=c5`) puts the passed request at risk. Ten holders leave about 330 free blocks. A 16k external
hit arrives (1,040 blocks for its sequence; it does not fit), followed by a stream of thirty 2k misses, one every 0.15 s for
4.5 s (145 blocks each: they fit, and they are more than the GPU can compute, so they take every block that becomes free). One
holder is cancelled 1.0, 2.5 and 4.0 s after the hit (about 710 blocks each): the hit fits after the second release if nobody
else has taken the blocks. 3 repetitions, medians; 16 output tokens per probe.

| configuration | hit: load admitted at (s) | hit: TTFT (s) | misses admitted before the hit (of 30) | first miss admitted at (s) | misses: TTFT p50 / p95 / max (s) | mean request time of the 31 probes (s) | blocks kept free for the hit while it waits (mean) | preemptions |
|---|---|---|---|---|---|---|---|---|
| stock | 2.57 | 4.50 | 0 | 2.59 | 8.39 / 12.84 / 12.91 | 10.94 | – | 0 |
| `skip=3`, no reservation | 3.95 | 5.93 | 7 | 0.11 | 6.21 / 10.60 / 10.67 | 8.19 | – | 0 |
| `skip=8`, no reservation | 4.59 | 5.53 | 9 | 0.11 | 6.14 / 10.90 / 11.27 | 9.16 | – | 0 |
| `skip=3,hitres=300` | 2.97 | 3.33 | 4 | 1.07 | 7.20 / 11.23 / 11.46 | 9.34 | 289 | 0 |
| `skip=3,hitres=600` | 2.91 | 4.86 | 4 | 1.07 | 7.48 / 11.72 / 12.08 | 9.77 | 577 | 0 |
| `skip=3,hitres=1200` | 2.57 | 4.55 | 0 | 2.57 | 8.29 / 12.57 / 12.68 | 10.66 | 980 | 0 |
| P2 (token reserve and short steps + `skip=3,hitres=600`) | 2.91 | 4.86 | 4 | 1.07 | 7.64 / 11.74 / 12.11 | 9.87 | 577 | 0 |

**Result.**
- **Stock:** the hit that does not fit holds back all thirty misses for 2.6 s (it is refused 89 times, once per engine step), and
  when the second release lets it in, the thirty misses start with it: its own first token then takes another 1.9 s.
- **Bypass without a reservation:** the misses flow from the first step (first one admitted after 0.11 s; TTFT p50 6.2 instead of
  8.4 s; mean request time −25 %) — and they take the first two releases. The hit is admitted 1.4 s later than in stock, when its
  3 s are over and the scan stops at it again; its TTFT is 5.9 s instead of 4.5 s. With `skip=8` it is passed for longer and
  admitted 2.0 s later than in stock. The bound is what prevents starvation here; without it nothing would.
- **Bypass with a bounded reservation:** with 300 or 600 blocks kept free, no miss is admitted until the first release; from then
  on four misses pass, and the second release completes the hit's blocks: it is admitted 0.3–0.4 s later than in stock. Misses:
  TTFT p50 7.2–7.5 s (stock 8.4, no reservation 6.2), mean request time −11 to −15 %. (The hit's time from admission to first
  token differs between the rows — 0.35 s with 300 blocks, 1.5–1.9 s elsewhere — with the number of misses that are prefilling
  when its load is issued; that part is the step-boundary effect of A, not the reservation.)
- **A reservation as large as the hit's need** (1,200 ≥ 1,024 blocks) reproduces stock exactly: nothing can pass.
- No preemption in any configuration: a passed request holds no blocks, and the requests that pass are admitted under the stock
  gates.

**Answers to the brief's questions.** *How much?* Enough that one further release completes the hit's need: here 300 blocks of a
1,040-block need were sufficient, and anything up to the need only removes passing. *When?* Only while a hit is actually being
passed — the reservation exists for 16 % of the overloaded replay's wall time and averages 75 blocks of 7,456 (C2). *Can it prevent a
long hit from waiting indefinitely?* The reservation alone cannot (requests that leave it untouched still pass); the time bound
does. *Does it reduce the memory of active requests?* It withholds free blocks from new compute requests, never from running
ones. *Does it increase the misses' waiting time?* Relative to the bypass without reservation, yes (p50 6.2 → 7.2–7.5 s);
relative to stock, no (8.4 s). *Preemptions or throughput?* No preemptions; the mean request time of the probes is 10–25 % lower
than in stock wherever requests pass, and 3 % lower with the full reservation.

### B4. The in-flight reservation charged to a load (`alpha`; MEASURED 2026-11-10 20:07–20:34, node c66; `E16/c2b/c2b-*`, table `E16/c2b/tables-c2b.md`)
**What changed.** `alpha=0` removes the stock reservation from the admission of an external load: the load is admitted if its
blocks are free, as a miss's first chunk would be. This is the literal form of "do not make a hit reserve more than a miss".

**What problem it addresses.** The reservation gate. In the stock replays it refuses almost nothing (A4, question 7), because a
load is only ever evaluated in a step in which no prefill needed more tokens. With the token reserve of B2 that changes: the
scan now runs *during* prefills, when the reservation is large. Scenario c2 (`run_adm.py plan=c2`) sets this up: a 16k miss
starts prefilling in a pool where it fits with 100 or with 400 blocks to spare; external hits of 4k (272 blocks) are sent 0.5 and
2.5 s later; 3 repetitions, medians of TTFT (s) with the gate of the first admission attempt.

| trial | probe | stock | token reserve + short steps | + `alpha=0` | + `alpha=0`, 512 output tokens | reserve + short steps, 512 output tokens | reserve + `skip=1,fallback=1` |
|---|---|---|---|---|---|---|---|
| 100 blocks to spare | 16k miss | 4.04 | 4.34 | 4.73 | 4.74 | 4.34 | 4.34 |
| 100 blocks to spare | hit +0.5 s | 4.22 (full) | 4.52 (**resv**) | **2.16** (ok) | 2.17 (ok) | 7.83 (resv) | 4.52 (full) |
| 100 blocks to spare | hit +2.5 s | 2.35 | 2.68 | 3.50 (full) | 6.55 (full) | 5.98 | 2.68 |
| 400 blocks to spare | 16k miss | 4.01 | 4.64 | 4.92 | 4.91 | 4.49 | 4.65 |
| 400 blocks to spare | hit +0.5 s | 3.80 | **2.11** (ok) | 2.13 | 2.11 | 1.98 | 2.12 |
| 400 blocks to spare | hit +2.5 s | 2.30 (full) | 2.69 (resv) | 1.99 (ok) | 1.97 | 2.16 | 2.70 (full) |
| preemptions / running requests refused their next chunk (6 trials) | | 0 / 0 | 0 / 0 | **6 / 12** | 6 / 12 | 0 / 0 | 0 / 0 |

**Did it work?** It admits the hit — 2.16 instead of 4.52 s when only 100 blocks are spare — and breaks something else every
time: one preemption and two refused chunks of running requests in each of the six trials, the 16k miss's first token 6–9 %
later than with the reserve alone (4.34 → 4.73 s, 4.64 → 4.92 s), and the next hit later (3.50 against 2.68 s; with 512 output
tokens 6.55 against 5.98 s). Where the hit
fits beside what the prefill still needs (400 spare blocks), the token reserve alone admits it under the stock reservation
(3.80 → 2.11 s) and `alpha` adds nothing.

**Why.** The reservation is not an arbitrary penalty on loads. A load takes all its blocks at once and holds them without
computing; if those are blocks a running prefill needs for its remaining chunks, the prefill's next chunk fails and the scheduler
preempts a running request, whose computed tokens are lost. The stock rule is the correct one for a request that enters during a
prefill, and the prototype extends it instead of relaxing it: with `resvall`, a *compute* request that the token reserve lets in
during a prefill must also fit under the in-flight reservation (C2 shows the preemption counts with and without it).

**Verdict.** Negative for `alpha` < 1 (kept as a flag, off in every other run). The reservation gate is a consequence of scanning
during a prefill, not a cause of the delays A measured.

### B5. Compute fallback (`fallback`; same runs, last column)
**What changed.** A hit that still fails the block gates `fallback` seconds after its lookup result is computed instead of
loaded — the connector's answer is turned into `(0, False)` — if the compute path passes the gates at that moment.

**Did it work?** It never fired: 0 fallback decisions in 18 probes (6 of them refused at their first attempt), and the results
are those of the run without it.

**Why.** Wherever the load is refused, computing is refused too. The gate that refuses loads is the full-sequence gate
(1,286 of 1,303 refused load attempts at the sustainable load, A2.1), and it asks for the blocks of the whole sequence whichever
way the prefix is obtained. The remaining case — a load refused only by the in-flight reservation — is the case of B4: starting
the request by computing would take the same blocks from the running prefill, a chunk at a time, and would add 4k tokens of
prefill (about 0.7 s of GPU) to save a transfer of 0.05 s. Recomputing is never the cheaper way to wait for memory on this path.

**Verdict.** Negative; no configuration was found in which the fallback is both possible and better than waiting.

### B6. Chunked external loading (the brief's B3): not possible in this protocol, and it would not help (SOURCE)
(i) The scheduler asks the connector only for requests
without computed tokens (S:931); after a load the request re-enters through the branch for requests that have them (S:1041),
which adopts no further external tokens, so a second load for the same request has no entry point. (ii) The connector's
tracker issues one retrieve per request (`PREFETCHING → WAITING_FOR_LOAD → READY`, C:1388–1402; M:100–110) for the whole range
recorded at lookup, with block ids sliced from the blocks allocated at that moment (M:283–330). (iii) More fundamentally, a
partial first load would not be admitted earlier: the full-sequence gate (K:519–536) requires the blocks of the whole
sequence to be free whatever the first allocation takes, and that gate, not the size of the first allocation, is what
refused 1,286 of 1,303 load attempts at the sustainable load and 1,991 of 2,000 under overload. A request whose first chunk of
KV is on the GPU also cannot run: attention needs the KV of every preceding position, so a partially loaded hit would hold
blocks without making progress — the situation `scheduler_reserve_full_isl` exists to prevent. Loading incrementally would
therefore move the wait from "before the load" to "between the pieces" and hold blocks longer. What can be tested without
changing model semantics is the effect of the gate itself (`--no-scheduler-reserve-full-isl`, a stock flag; A3.1) and of the
reservation (`alpha`; B4).

**Answers to the brief's questions on chunked loading.**
- *Does it enable earlier execution?* No. A request cannot run on the first part of its prefix; execution starts when the last
  piece is on the GPU, which needs the same total of free blocks as the single load.
- *Does it only move the waiting time?* Yes: from before the load to between the pieces — with blocks held in the meantime.
- *Does it increase GPU KV memory pressure?* Yes. A partially loaded request holds blocks without making progress and cannot be
  preempted while a transfer is in flight (S:1196). A3.1 shows the analogous case for misses: with the full-sequence gate off,
  requests are admitted on a first chunk they cannot follow up, and the run has 23 preemptions against 2.
- *Does it require changes to block mapping or connector semantics?* Yes, in three places: the scheduler's connector query (only
  for requests without computed tokens), the connector's per-request state machine (one retrieve), and the slicing of block ids
  at allocation time.
- *Repeated copies or other overhead?* Not measured, because the mechanism was not built: it cannot be expressed through the
  existing interfaces, and (iii) above says the admission would not come earlier if it were.

**Verdict.** Not implemented; incompatible with the connector protocol of vLLM 0.31 / LMCache 0.5.5, and the measured cause of
the refusals (the full-sequence gate) would be unchanged by it.

### B7. The store-counter fix (`storefix`; MEASURED 2026-11-10 22:44–23:05, c28, `replay/tool08-320-storefix`)
**What changed.** At every poll of a waiting request that returns a lookup result, the hook sets the connector's stored-token
counter back to the LMCache hit length if no token of the request has been scheduled yet — i.e. it undoes the repeated addition
described in A5. Nothing else: stock scheduling, stock gates.

**What problem it addresses.** A5: requests that are polled again after a refusal skip the store of their new KV.

**How.** The overloaded tool-agent replay (0.08×, 544 requests, 320 GB tier, pool 7,456 blocks) with this flag alone, against the
stock run of the same replay.

| quantity | stock | store-counter fix alone |
|---|---|---|
| requests with a new chunk that stored nothing | 82 of 477 | 0 of 475 |
| KV stored in the host tier (GB; expected from the new chunks: 105–107) | 73.8 | 108.9 |
| requests polled ≥ 2 times: GB stored of expected | 9.4 of 45.0 | 46.2 of 45.0 |
| share of prompt tokens served from a cache: total / host tier | 0.355 / 0.114 | 0.368 / 0.126 |
| TTFT p50 / p95 / p99 / mean, all requests (s) | 12.45 / 40.8 / 47.4 / 14.67 | 12.16 / 40.9 / 47.3 / 14.43 |
| TTFT mean of the stock run's host-dominant hits / GPU-prefix hits / misses (s) | 19.65 / 11.22 / 16.64 | 19.14 / 11.09 / 16.42 |
| mean request time (s); completed requests / s | 27.6; 0.425 | 27.2; 0.428 |
| requests with TTFT lower / higher by more than 10 % | – | 3 % / 2 % |
| preemptions | 5 | 7 |

**Did it work?** Yes: every request stores its new chunks, 35 GB more KV reaches the host tier in 21 minutes (+48 %), the share
of prompt tokens served from the host tier rises from 11.4 % to 12.6 % within the same window, and no class of requests is slower
(all within 3 % of stock; two runs of the same configuration differ by less than 1 %, G, so the 2 % lower mean TTFT is small but
real). The latency effect is small here
because the replay window is short: the KV that stock fails to store would be reused by later turns of the same sessions.

**Side effects.** The host tier fills faster — with a tier that is already full (80 GB, C2.4) the additional stores displace
other entries. None otherwise: the fix does not change what is admitted or when.

**Why it matters for this project.** It is the one finding of the study that is about the host tier itself: a larger tier cannot
help with KV that was never written to it, and stock loses the most exactly when the engine is congested.

## C. End-to-end results

### C1. Controlled mixed workloads (the brief's Experiment C; MEASURED 2026-11-10 18:53 – 2026-11-11 01:19, 16 GB nodes c60 and c66, `E16/cc/`)
**Why.** The scenarios of B isolate one mechanism each. Before the trace replays, the prototype has to be measured where hits and
misses compete under controlled concurrency, arrival pattern, hit share and — the variable of this study — GPU KV memory pressure,
including cases without any pressure.

**How.** `run_b.py` (the 2026-11-04 driver): 64 prompts of 1k / 2k / 4k / 8k tokens are stored in LMCache and flushed from the GPU
prefix cache before every scenario; requests alternate external hits of those prompts and never-seen prompts of the same lengths
(50 % / 50 %), 32 output tokens. Scenarios: **s1** closed loop with 1, 2, 4, 8, 16 requests in the system (64 requests each);
**s2** open loop, Poisson arrivals at 0.5, 1, 2, 4 requests/s (96 requests each; 4 requests/s is above the engine's capacity of
about 2.8); **s3** synchronized bursts of 4, 8, 16 requests; **s4** open loop at 2 requests/s with an external-hit share of 0, 25,
50, 75, 100 %, for short (1k–2k) and long (8k) prompts. The same seeded request sequences run on every configuration. **GPU KV
memory pressure is set by the pool size** — `--num-gpu-blocks-override` 14,912 / 7,456 / 3,728 / 2,560 blocks (239k / 119k / 60k /
41k tokens; 2,048 blocks equals `max_model_len` and vLLM does not start) — and **measured, not assumed**: the tables give the
time-weighted share of the pool in use during each scenario, from the per-step occupancy stream, and the refused admission
attempts. Server configurations per pool: stock, P1, P2 (B0); at 7,456 blocks also the existing options (synchronous scheduling,
prefill cap 1,024, hits-first priority). All configurations of one pool ran on the same node (14,912 and 2,560 on c66; 7,456 and
3,728 on c60; s4 on c66).

**Result 1 — the workload matrix** (`E16/cc/tables-cc-matrix.md`; p95 values and every scenario in `E16/cc/tables-cc-pools.md` and
`figs/table-fig3-fig6.md`). Each cell: stock → P1 / P2.

| scenario | quantity | pool 14,912 blocks | pool 7,456 blocks | pool 3,728 blocks | pool 2,560 blocks |
|---|---|---|---|---|---|
| closed loop, 16 in the system | external hits: TTFT p50 (s) | 3.37 → 1.17 / 1.17 | 3.43 → 1.18 / 1.17 | 3.27 → 1.19 / 1.14 | 4.37 → 1.23 / 1.15 |
| | misses: TTFT p50 (s) | 3.03 → 3.34 / 3.34 | 3.08 → 3.39 / 3.40 | 2.34 → 3.06 / 3.50 | 4.30 → 7.19 / 7.23 |
| | completed requests / s | 2.42 → 2.31 / 2.31 | 2.38 → 2.27 / 2.27 | 2.36 → 2.31 / 2.31 | 2.38 → 2.34 / 2.34 |
| | request time, mean (s) | 6.57 → 6.85 / 6.85 | 6.67 → 6.94 / 6.94 | 6.70 → 6.75 / 6.76 | 6.52 → 6.37 / 6.39 |
| | pool in use, measured (stock) | 0.21 | 0.42 | 0.80 | 0.82 |
| open loop, 2 requests/s | external hits: TTFT p50 (s) | 0.90 → 0.89 / 0.89 | 0.94 → 0.93 / 0.94 | 0.99 → 0.94 / 0.93 | 0.92 → 0.92 / 0.72 |
| | misses: TTFT p50 (s) | 0.92 → 1.03 / 1.02 | 1.00 → 1.07 / 1.08 | 1.01 → 1.06 / 1.06 | 1.00 → 1.00 / 0.97 |
| | request time, mean (s) | 2.37 → 2.54 / 2.55 | 2.47 → 2.81 / 2.81 | 2.55 → 2.72 / 2.68 | 2.20 → 2.28 / 2.23 |
| | pool in use, measured (stock) | 0.08 | 0.17 | 0.35 | 0.41 |
| open loop, 4 requests/s | external hits: TTFT p50 (s) | 5.91 → 1.73 / 1.84 | 6.40 → 1.81 / 2.16 | 5.73 → 5.44 / 2.15 | 5.66 → 5.44 / 1.40 |
| | misses: TTFT p50 (s) | 5.39 → 6.96 / 6.94 | 5.42 → 7.03 / 7.15 | 5.55 → 6.30 / 6.47 | 5.63 → 5.95 / 6.31 |
| | completed requests / s | 2.79 → 2.67 / 2.67 | 2.75 → 2.66 / 2.64 | 2.76 → 2.68 / 2.67 | 2.76 → 2.72 / 2.72 |
| | request time, mean (s) | 8.85 → 8.07 / 8.13 | 9.20 → 8.06 / 8.36 | 8.09 → 8.26 / 7.77 | 6.99 → 7.21 / 6.02 |
| | pool in use, measured (stock) | 0.24 | 0.48 | 0.75 | 0.77 |
| bursts of 16 | external hits: TTFT p50 (s) | 3.03 → 1.21 / 1.30 | 3.57 → 1.45 / 1.20 | 3.45 → 1.18 / 1.16 | 3.40 → 1.26 / 1.34 |
| | misses: TTFT p50 (s) | 2.78 → 3.00 / 3.01 | 2.77 → 2.96 / 2.94 | 2.85 → 2.95 / 2.95 | 3.28 → 3.24 / 2.99 |
| | request time, mean (s) | 6.15 → 6.31 / 6.32 | 6.12 → 6.27 / 6.28 | 6.05 → 5.47 / 5.50 | 5.29 → 4.61 / 4.62 |
| | pool in use, measured (stock) | 0.14 | 0.31 | 0.52 | 0.50 |
| whole run | refused admission attempts: stock / P1 / P2 | 0 / 0 / 0 | 0 / 0 / 0 | 256 / 300 / 175 | 747 / 777 / 401 |
| whole run | preemptions: stock / P1 / P2 | 0 / 0 / 0 | 0 / 0 / 0 | 7 / 3 / 3 | 0 / 0 / 0 |

![Figure 3](../../experimental_results/2026-11-10-gpu-kv-admission/figs/fig3-concurrency-vs-ttft.png)

*Figure 3 — concurrency against TTFT, closed loop (s1). x: number of requests kept in the system; y: TTFT in seconds (log
scale). One column per pool size; top row external hits, bottom row misses; solid lines p50, dotted p95; stock, P1 and P2 (P1
and P2 coincide here).*

![Figure 3b](../../experimental_results/2026-11-10-gpu-kv-admission/figs/fig3b-rate-vs-ttft.png)

*Figure 3b — the same for the open loop (s2). x: arrival rate in requests per second; 4 requests/s is above the engine's
capacity. With the two smaller pools P1 follows stock at 4 requests/s and P2 does not.*

![Figure 6](../../experimental_results/2026-11-10-gpu-kv-admission/figs/fig6-throughput-vs-pressure.png)

*Figure 6 — throughput and TTFT against measured GPU KV memory pressure. x: time-weighted share of the pool in use during the
scenario, one point per pool size (the largest pool is the leftmost point). Columns: the three saturated scenarios. Rows: prompt
tokens served per second, TTFT p50 of the external hits, TTFT p50 of the misses. Stock, P1 and P2.*

What the matrix shows:
- **Without any memory pressure the hits wait as long as with it, and the token mechanisms remove most of that wait.** With the
  two larger pools no admission attempt is refused in any configuration and at most 49 % of the pool is in use; a hit still gets
  its first token after 3.4 s in the closed loop with 16 requests, 5.9–6.4 s in the open loop above capacity and 3.0–3.6 s in
  bursts of 16 — as long as a miss. With P1 these are 1.2 s, 1.7–1.8 s and 1.2–1.5 s (2.5–3.5× sooner); the p95 falls from 8.2 to
  1.8 s in the closed loop. P2 equals P1 here: its bypass has nothing to act on.
- **The misses pay, and the engine loses a few per cent.** TTFT p50 of the misses +7 to +10 % in the closed loop and in bursts,
  +29 to +30 % in the open loop above capacity; completed requests per second −1 to −5 %.
- **Below saturation the tails move in both directions and the request time gets longer.** With up to 4 requests in the closed
  loop and up to 1 request/s, throughput and the mean request time stay within 3 % and the misses' median within 0.02 s; the
  hits gain already (p50 0.74 → 0.55 s with 4 in the system; p95 1.46 → 0.69 s with 2 in the system and 3.8–4.0 → 1.7–2.4 s at
  1 request/s) and the misses' p95 rises (1.58 → 2.35 s with 4 in the system). At 2 requests/s the medians move by at most
  0.11 s, the hits' p95 falls (2.95 → 1.88 s on the largest pool), the misses' p95 rises (2.15 → 2.58 s) and the mean request
  time is 4–14 % *higher* with P1 (`figs/table-fig3-fig6.md`).
- **Under memory pressure the token mechanisms alone stop working in the open loop, and the bypass restores them.** With the two
  smaller pools 75–82 % of the pool is in use in the closed loop and in the open loop above capacity, and 256 and 747 admission
  attempts are refused in the stock runs. P1 leaves
  the hits of the open loop at 4 requests/s where they were (5.7 → 5.4 s): they now stand behind a request that waits for blocks,
  which P1 does not pass (`blkfirst`). P2 serves them in 2.15 s and 1.40 s at the median (the p95 stays at 10.9 and 8.3 s
  against 11.3 and 11.0 s), with a third to a half fewer refused attempts than stock and a mean request time 4 % and 14 % below
  stock.
- **The smallest pool shows the price most clearly:** in the closed loop the misses' TTFT p50 rises from 4.30 to 7.2 s (+67 %)
  while the hits' falls from 4.37 to 1.2 s.

**Result 2 — the scheduler options vLLM already has, same workloads, pool 7,456 blocks** (`E16/cc/tables-cc-options-7456.md`).

| scenario | configuration | hits: TTFT p50 / p95 (s) | misses: TTFT p50 / p95 (s) | requests / s | request time, mean (s) |
|---|---|---|---|---|---|
| closed loop, 16 in the system | stock | 3.43 / 8.29 | 3.08 / 6.98 | 2.38 | 6.67 |
| | synchronous scheduling | 2.47 / 7.12 | 2.26 / 6.77 | 2.34 | 6.79 |
| | prefill cap 1,024 | 3.25 / 7.44 | 3.28 / 6.80 | 2.37 | 6.70 |
| | hits-first priority (client-labelled) | 3.30 / 4.81 | 3.34 / 6.95 | 2.38 | 6.68 |
| | P1 | 1.18 / 1.84 | 3.39 / 7.39 | 2.27 | 6.94 |
| open loop, 4 requests/s | stock | 6.40 / 11.47 | 5.42 / 10.31 | 2.75 | 9.20 |
| | synchronous scheduling | 6.21 / 11.54 | 5.73 / 10.80 | 2.71 | 9.51 |
| | prefill cap 1,024 | 6.12 / 11.26 | 5.42 / 9.92 | 2.76 | 9.04 |
| | hits-first priority (client-labelled) | 2.93 / 4.24 | 5.68 / 10.40 | 2.77 | 7.66 |
| | P1 | 1.81 / 4.74 | 7.03 / 11.89 | 2.66 | 8.06 |
| bursts of 16 | stock | 3.57 / 7.56 | 2.77 / 7.30 | 1.52 | 6.12 |
| | synchronous scheduling | 3.10 / 7.67 | 2.89 / 7.56 | 1.51 | 6.24 |
| | prefill cap 1,024 | 2.92 / 7.54 | 3.57 / 7.49 | 1.53 | 6.12 |
| | hits-first priority (client-labelled) | 1.84 / 3.99 | 3.48 / 7.59 | 1.51 | 6.22 |
| | P1 | 1.45 / 3.35 | 2.96 / 7.79 | 1.50 | 6.27 |

Synchronous scheduling lowers the TTFT p50 of hits and misses alike by about a quarter in the closed loop (2.47 and 2.26 s) with
2 % less throughput and changes little in the open loop and in bursts; the prefill cap changes little anywhere. **Hits-first
priority is the strong existing option wherever a queue forms:** in the open loop above capacity it halves the hits' TTFT
(2.93 s), costs the misses 5 %, loses no throughput and gives the lowest mean request time of all configurations (7.66 s against
9.20 stock, 8.06 P1); in bursts 1.84 s for hits at +26 % for the misses. It needs the client to say which requests are hits
(here the driver knows), and in the closed loop it lowers only the hits' p95 (4.8 s against 8.3 s), not the median (3.30 s):
there no request waits in the queue for its turn, it waits for token budget. P1 gives the lowest hit TTFT in all three and the highest miss TTFT
in the open loop.

**Result 3 — hit share and prompt length (s4, open loop at 2 requests/s; `E16/cc/tables-s4.md`).** With 8k prompts this rate is far
above capacity when most requests are misses; with 1k–2k prompts the engine is not saturated.

| prompts | hit share | pool 7,456: hits TTFT p50 (s), stock → P1 / P2 | misses TTFT p50 (s) | request time, mean (s) | pool 3,728: hits TTFT p50 (s), stock → P1 / P2 | misses TTFT p50 (s) | request time, mean (s) |
|---|---|---|---|---|---|---|---|
| 8k | 0 % | – | 27.2 → 27.6 / 27.6 | 36.6 → 35.7 / 35.7 | – | 26.9 → 27.7 / 27.7 | 33.7 → 33.6 / 33.6 |
| 8k | 25 % | 29.45 → 1.30 / 1.31 | 21.0 → 22.3 / 22.4 | 31.9 → 26.5 / 26.5 | 27.30 → 1.40 / 1.46 | 20.6 → 22.3 / 22.3 | 27.3 → 24.6 / 24.6 |
| 8k | 50 % | 9.66 → 1.67 / 1.81 | 11.7 → 15.1 / 14.9 | 19.7 → 15.1 / 15.0 | 9.31 → 6.48 / 2.21 | 11.4 → 12.6 / 12.8 | 15.5 → 15.0 / 11.4 |
| 8k | 75 % | 6.92 → 1.79 / 1.78 | 6.6 → 9.7 / 9.3 | 13.3 → 10.9 / 10.9 | 5.47 → 3.95 / 1.60 | 6.3 → 7.0 / 7.0 | 8.7 → 8.2 / 6.5 |
| 8k | 100 % | 0.10 → 0.09 / 0.09 | – | 0.54 → 0.48 / 0.48 | 0.10 → 0.10 / 0.10 | – | 0.55 → 0.48 / 0.48 |
| 1k–2k | 0–100 % | 0.03–0.09, unchanged | 0.31–0.35, unchanged | 0.33–1.04, unchanged | unchanged | unchanged | unchanged |

- With a mix of long hits and long misses the hits' TTFT falls from 7–29 s to 1.3–1.8 s, the misses' rises by 7 % (25 % hits),
  29 % (50 %) and 46 % (75 %), and the mean request time falls by 17–23 %. The prompt tokens served per second are unchanged up to
  50 % hits and 5 % lower at 75 % (11,463 → 10,844).
- With half the pool, P1 keeps only part of the gain (9.3 → 6.5 s at 50 % hits) and P2 the whole (2.2 s), with a mean request time
  26 % below stock and 5.5 % *more* prompt tokens served per second (9,045 → 9,543): here the bypass removes idle waiting instead
  of moving it.
- All misses, all hits, or short prompts: no difference between the configurations. The mechanisms act only where short and long
  work compete for the same engine steps.
- **The gain does not depend on the prefix length.** Over all scenarios of s1–s3, hits of 1k, 2k, 4k and 8k tokens have a TTFT
  p50 of 2.8–4.9 s in stock and 1.1–1.5 s with P1, at every pool size (`figs/table-cc-by-length.md`).

**Explanation.** The first two pools separate the two causes of A. No request is ever refused memory there, so the 3–6 s a hit
waits are engine steps: the running prefills take the whole 2,048-token budget of a step, the waiting queue is scanned only with
what they leave, and a hit — which needs a transfer of 0.05 s and a few hundred tokens of compute — gets in when a prefill ends
(A1.1, A4). The token reserve gives the queue 768 tokens of every step while short work is waiting, and the short steps bound how
long that work waits for the step in flight. The budget is shared, so every token given to a hit is taken from a miss in the same
step, and steps of 512 tokens spread the fixed cost of a step over fewer tokens: that is the misses' +7 to +30 % and the −1 to
−5 % of throughput. The mean request time falls where a queue exists (open loop above capacity: short requests are served
first) and rises where it does not (closed loop: it is the inverse of throughput; 2 requests/s: the misses' prefills are
stretched and nobody was waiting long). The two smaller pools add the second cause: a request that does not fit stops the scan
(A1.2), the hits behind it wait for memory they do not need, and only the bypass (P2) helps — there it also raises throughput,
because blocks and steps that stood idle behind the blocked request are used.

<!-- C2 -->

### C3. Beyond the 8 GB GPU (the brief's Experiment E; MEASURED 2026-11-10 18:21 – 2026-11-11 01:24, 16 GB nodes c60, c61, c66, `E16/E/`)
**Why.** c28's GPU holds 119k tokens of KV for the 3B model. If the delays of A came from that small pool, a larger GPU would
remove them and the study would be about one configuration. The question has two parts: does the *memory* part of the problem
(the full-sequence gate, head-of-line blocking, preemptions) survive a larger pool, and does the *token-budget* part?

**What was available.** c33 (A100 80 GB) and c29 (H100 94 GB) are allocated to another user's jobs until 2026-11-13; the
partition of RTX 4060 Ti 16 GB nodes was free. These nodes have the same GPU model as c28 with twice the memory: the same compute
speed, a GPU KV pool of 19,916 blocks for the 3B model (318,656 tokens, 2.67× c28's) or room for a 7B model with slightly more
than c28's token capacity (Qwen2.5-7B-Instruct-AWQ: 8,753 blocks, 140,048 tokens). **Limitation:** no GPU with more compute was
available; a faster GPU shortens every prefill step and with it the absolute waits, which these runs cannot show.

**How.** Three server sizes on one node type, the same trace window as on c28 (tool-agent, seconds 0–200 at 0.04×; 1,159
requests), 80 GB host tier (the nodes have 188 GiB of RAM):
1. *small pool, small model*: pool pinned at c28's 7,456 blocks (`e-tool04-80-p7456-*`, node c61);
2. *larger pool, same model*: 19,916 blocks (`e-tool04-80-big-*`, c61), also under overload (seconds 0–100 at 0.08×, 120 GB host
   tier, `e-tool08-120-big-*`, c66);
3. *larger model, similar token capacity*: 7B-AWQ, seconds 0–100 at 0.02× — half the arrival rate for a model that computes
   about half as fast, so that the engine is as busy as with the 3B model at 0.04× (`e7-tool02-80-*`, c60; GPU busy 47 % against
   49–50 %).
Each family has its own stock run on its node. Pressure is compared through measured quantities — blocks in the pool, refused
attempts, the time-weighted share of the pool in use, the share of time with a saturated token budget — not through concurrency.

**Result 1 — the node is a valid stand-in for c28.** With the pool pinned, the stock replay on c61 reproduces c28's replay of
2026-11-05 with the same host tier (`dl-tool-dram80`, pool 7,612 blocks): cached share 0.382 against 0.383 (host tier 0.071
against 0.072), TTFT p50 / p95 / p99 2.03 / 22.5 / 34.5 s against 2.04 / 22.5 / 35.2 s (interpolated percentiles of the
`*-replay.json` summaries), 1,214 against 1,212 prompt tokens computed per second, 68.7 GB of host tier in use in both.

**Result 2 — a 2.67× larger pool removes the memory gate and leaves the token budget where it was (stock, same node).**

| quantity | pool 7,456 blocks | pool 19,916 blocks |
|---|---|---|
| refused admission attempts (full-sequence gate / reservation) | 5,041 / 6 | 0 / 0 |
| preemptions | 1 | 0 |
| pool in use, time-weighted mean; time with less than 25 % free | 0.265; 9.6 % | 0.108; 0 % |
| time in steps whose running requests use the whole token budget | 20.3 % | 20.5 % |
| requests served mostly from the host tier / with any load from it | 112 / 127 | 30 / 42 |
| share of prompt tokens from a cache: host tier / GPU prefix | 0.071 / 0.311 | 0.036 / 0.348 |
| TTFT p50 / p95 / p99, all requests (s) | 2.03 / 22.5 / 34.7 | 2.03 / 18.1 / 25.7 |
| TTFT p50 / p95 of the host-dominant hits of the small-pool run (same 112 requests) (s) | 6.60 / 31.3 | 5.59 / 25.0 |

The tail shortens (p95 −20 %, p99 −26 %) and the median does not move. On the large pool a host-dominant hit that arrives while
no prefill is in flight answers in 0.29 s (median, 17 requests); one that arrives during a prefill answers in 15.8 s (13
requests) — with 80 % of the pool free.

**Result 3 — the token mechanisms give the same gain on all three server sizes at the sustainable load** (P1; paired by the
stock run's classes; `E16/E/tables-primary-*.md`, full tables `E16/E/tables-d-*.md`).

| quantity | pool 7,456, 3B (c61) | pool 19,916, 3B (c61) | pool 8,753, 7B (c60) |
|---|---|---|---|
| all requests: TTFT mean (s), stock → P1 | 5.41 → 4.19 (−23 %) | 4.80 → 3.81 (−21 %) | 8.44 → 6.97 (−17 %) |
| all requests: TTFT p50 (s) | 2.03 → 1.40 (−31 %) | 2.03 → 1.38 (−32 %) | 3.69 → 2.64 (−28 %) |
| all requests: TTFT p95 (s) | 22.5 → 20.6 (−8 %) | 18.1 → 17.6 (−3 %) | 32.6 → 29.8 (−9 %) |
| host-dominant hits (n): TTFT mean (s) | (112) 10.50 → 4.25 (−60 %) | (30) 7.39 → 1.38 (−81 %) | (25) 16.49 → 5.76 (−65 %) |
| GPU-prefix hits (n): TTFT mean (s) | (577) 2.89 → 1.33 (−54 %) | (661) 3.48 → 1.68 (−52 %) | (278) 4.74 → 2.34 (−51 %) |
| misses (n): TTFT mean (s) | (339) 8.12 → 8.78 (+8 %) | (340) 7.27 → 8.04 (+11 %) | (175) 14.00 → 14.80 (+6 %) |
| misses: request time mean (s) | 23.85 → 24.53 (+3 %) | 24.82 → 25.50 (+3 %) | 44.80 → 45.41 (+1 %) |
| all requests: request time mean (s) | 12.22 → 11.49 (−6 %) | 12.48 → 11.88 (−5 %) | 22.70 → 21.82 (−4 %) |
| requests with TTFT lower / higher by more than 10 % | 21 % / 15 % | 19 % / 16 % | 17 % / 11 % |
| time in budget-saturated steps | 20.3 % → 7.2 % | 20.5 % → 6.9 % | 19.6 % → 8.2 % |
| requests with TTFT above 30 s | 26 → 22 | 4 → 6 | 31 → 27 |
| completed requests / s; GPU busy | 0.233 → 0.233; 0.50 → 0.51 | 0.233 → 0.233; 0.50 → 0.50 | 0.108 → 0.108; 0.47 → 0.47 |

With synchronous scheduling added on the large pool (`e-tool04-80-big-p1-sync`) the median TTFT falls further (1.09 s, −46 %
against stock) and the mean request time is back at the stock value (12.5 s): mean TTFT −20 %, misses +13 %.

**Result 4 — under overload on the large pool the token mechanisms make everything worse** (seconds 0–100 at 0.08×, 544
requests; `e-tool08-120-big-*`; one request of the P1 run was lost to the client-side connection reset described in G).

| quantity | stock | P1 |
|---|---|---|
| all requests: TTFT p50 / p95 / p99 / mean (s) | 10.42 / 36.4 / 43.0 / 12.72 | 12.43 / 47.0 / 61.2 / 16.44 (+29 %) |
| request time, mean (s) | 32.4 | 39.4 (+22 %) |
| host-dominant hits (17): TTFT mean (s); request time mean (s) | 16.11; 41.6 | 9.84 (−39 %); 42.9 (+3 %) |
| GPU-prefix hits (299): TTFT mean (s) | 11.84 | 13.81 (+17 %) |
| misses (163): TTFT mean (s); request time mean (s) | 14.48; 56.5 | 21.74 (+50 %); 70.3 (+24 %) |
| requests with TTFT lower / higher by more than 10 % | – | 20 % / 54 % |
| requests with TTFT above 30 s / above 60 s | 57 / 0 | 127 / 8 |
| refused admission attempts; preemptions | 0; 0 | 0; 0 |
| waiting time of a request by reason (share, range over the classes) | token budget 57–65 %, running slots 23–33 % | running slots 53–89 %, token rule of the prototype 0–40 % |
| time in budget-saturated steps | 43.5 % | 4.2 % |
| running / waiting requests, time-weighted mean | 9.1 / 4.6 | 10.4 / 6.0 |
| time per output token after the first, p50 (ms) | 74 | 123 |
| prompt tokens computed / s; GPU busy | 2,287; 0.87 | 2,235; 0.90 |

**Explanation.** The two halves of the problem separate cleanly. The memory half (refusals at the full-sequence gate,
head-of-line blocking, preemptions) is a property of the ratio of pool to workload: with 2.67× the pool it is gone at the
sustainable load, and with it a fifth of the tail. The token half does not depend on memory at all: on the large pool the same
fifth of the run has its token budget exhausted, a hit that arrives during a prefill waits 15.8 s with four fifths of the pool
free, and the token reserve recovers the same 17–23 % of mean TTFT on the small pool, the large pool and the larger model, at
the same price (misses +6 to +11 % TTFT, +1 to +3 % request time). Result 4 shows what the saturated token budget is worth
under overload: it is an unintended admission control. With the reserve, requests no longer wait for budget; they are admitted
until the 16 running slots are the limit, more of them decode at once and each more slowly (the same prefill work now runs
beside them instead of before them), every request holds its slot longer, and with no additional compute (the GPU was 87 % busy
before) the mean TTFT and the mean request time rise by 29 % and 22 %. On c28's pool the memory gate plays the role of the
slot limit and the damage is smaller (C2.2).

### C4. Real CXL validation: blocked, documented, nothing changed (checked 2026-11-10 15:55 and 2026-11-11 00:43)
**Why.** The project's host tier is meant to be CXL memory; the brief asks to repeat representative runs on a CXL-backed LMCache if the
devices are accessible, and otherwise to document the blocker and label the results.

**What was checked.** `/dev/dax0.0`, `/dev/dax1.0` and `/dev/dax2.0` are `crw------- root root` (modification time 2026-10-20
15:32). Opening `dax0.0` and `dax1.0` read-only as `ghu4` fails with `EACCES`, at the start of the study and again at its end.
`/dev/dax2.0` is in addition mounted as a root-owned famfs (FUSE) at `/mnt/famfs/dax2.0` and is reserved for another project by the
user's rule of 2026-09-17; it was not opened. No permission, mount or system setting was changed.

**Consequence.** Every host-tier result in this report is measured with pinned DRAM: these are **host-memory admission results**,
not CXL measurements, and no number here is a CXL speedup. What transfers to a CXL tier and what does not, from what was measured:
- The mechanisms of A and B act in the engine's scheduler, before a load is issued and after it has arrived. They do not touch
  the medium the KV is read from.
- The transfer itself is a small part of the delay it sits in: 0.05 s for a 16k prefix against waits of seconds (A2.1). The
  2026-11-04 study measured the host → GPU transfer at the PCIe link's rate (11.3–12.0 GB/s) with DRAM as the source; whether a
  CXL source keeps that rate under this load is not measured here.
- Lookup and retrieval CPU cost on CXL, the effect of concurrent stores on loads (the duplex question, out of scope by the
  brief), and any change of admission behaviour with a slower tier are **not measured**.

## E. Negative results
Every item was measured (or, for item 4, established from the source); the runs are kept, paths in brackets.

1. **The hypothesis the study started from.** "Whole-prefix GPU KV reservation makes external hits wait while misses enter with a
   chunk" does not describe vLLM 0.31 with its defaults. The reservation gate refused 17 of 4,924 attempts at the sustainable load,
   9 of 6,527 under overload and none in the conversation replay (A2, A4); at the block gate a hit and a miss of the same length are
   refused and admitted together (A3). The asymmetry exists only with `--no-scheduler-reserve-full-isl` (A3.1).
2. **Relaxing the reservation of loads** (`alpha=0`, the literal form of B2). It admits the hit 2.4 s sooner in the scenario built
   for it and costs one preemption and two failed chunk allocations in every trial; the next hit is later (B4; `E16/c2b`).
3. **Compute fallback** (B5). Never applicable: where a load is refused, computing is refused by the same full-sequence gate (0
   fallback decisions; `E16/c2b/c2b-tokfast-fb`).
4. **Chunked external loading** (B3). Not expressible in the connector protocol, and a partial load would not be admitted earlier
   and cannot run (B6).
5. **Existing scheduler options as a remedy.** Synchronous scheduling alone: no effect behind a prefill (B1), 7 % higher mean TTFT
   in the overloaded replay. Prefill cap 1,024: helps the first hit in the controlled scenario, worse on every metric in the
   overloaded replay (mean TTFT +27 %, 74 preemptions against 5). A 512-token step: worse everywhere. Full-sequence gate off: hits
   are refused at the same free-block counts as before, 23 preemptions against 2 (A3.1).
6. **Prototype v1** (`replay/tool08-320-tokfast`). Its store-counter fix covered only loads while its own `minchunk` rule made the
   scheduler poll GPU-prefix hits again: the host tier received 31.3 GB instead of 73.8 GB. It also kept the engine in short steps
   for 24 % of the run for requests that were waiting for memory, not tokens. TTFT p95 58.8 s against 40.8 s.
7. **Prototype v1.1 under overload** (`replay/tool08-320-tokfast11`). Hits 4–7× sooner at the median, at the price of misses +32 %
   (p50) and +39 % (mean), p95 +18 %, p99 +38 %, a longest wait of 77.7 s against 53.2 s and 32 preemptions against 5. Its token
   rule let short work pass memory-blocked requests without any bound: a request that needed 50 blocks waited 48 s after its first
   refusal while 22 others were admitted (B0).
8. **The token mechanisms alone under overload** (P1, `replay/tool08-320-p1`). With the unbounded passing removed, mean TTFT and
   mean request time are 9 % *worse* than stock: the token budget no longer starves the queue, and head-of-line blocking takes its
   place (57–68 % of the waiting time of hits against 32 % in stock) (C2.2).
9. **The prototype against oracle priority under overload.** vLLM's existing priority scheduling, given in advance which requests
   are hits, lowers the mean TTFT by 33 % and the mean request time by 16 % with misses +15 %; the best safe prototype
   configuration (P2) reaches −4 % and +2 % with misses +29 % (C2.2). Under overload the prototype does not survive the comparison
   with this baseline.
10. **The conversation trace under overload** (`replay/conv08-320-p2`). 39 of 291 requests are hits; P2 makes those 4–9× faster at
   the median and everything else slower: mean TTFT +6 %, p95 +24 %, mean request time +6 % (C2.3).
11. **The first token is not the last.** Behind 8k and 16k prefills the request time of a hit is unchanged by the prototype although
   its first token comes 2–4× sooner (B2); in the saturated mixed workloads the hits' TTFT p50 falls 2.5–3.5× while the mean
   request time moves between −26 % and +14 % and the completed requests per second between −5 % and +5.5 % (C1).
12. **A pool of 2,048 blocks** (= `max_model_len`) cannot be tested: vLLM does not start (`E16/cc/failed-pool2048`).

## G. Correctness and experimental validity (the brief's section 9)

**What is held constant in every comparison.** Within a table, all configurations ran the same request sequence — the same trace
window, speed, request order, token content and output lengths for the replays (the client derives every prompt from the trace's
hash blocks with a fixed generator), the same seeded prompts, types and arrival instants for the controlled workloads — on the same
node, with the same model, host-tier size, GPU KV pool (pinned with `--num-gpu-blocks-override` wherever a prototype is compared;
the one unpinned run, `tool04-320-base`, came up at the same 7,456 blocks) and the same instrumentation. Only the flags named in
the column differ. No table puts an overloaded baseline next to a lightly loaded prototype: load is offered open-loop from the
trace at the same instants in both.

**Completion.** Every measured request of every run in the configuration matrix completed with HTTP 200: no failure, no timeout,
no cancellation by the server (`experiment-matrix.md`, column `errors` = 0 in all rows). The only errors are client-side connection
resets on *filler* requests — the 16k-token prompts that flush the GPU prefix cache between scenarios of the mixed workloads: 1–4
of the 176 fillers of a run, in stock and prototype runs alike (column `filler_errors`). Runs that did not start are kept and
named: a pool of 2,048 blocks (`E16/cc/failed-pool2048`), one start before the previous server had released the GPU
(`E16/cc/failed-gpu-busy`; the launcher now waits), jobs on a node without the environment (`E16/*/failed-c0`).

**Output correctness, path by path (`run_correct.py`, `E16/correct/`, node c66, 2026-11-11 00:02–00:31).** 48 prompts of 1k–8k
tokens (+100 fresh tokens) are answered five ways on one server and the generated text (32 tokens, temperature 0) is compared
with the first way: computed alone; loaded from LMCache alone; served from the GPU prefix cache alone; loaded from LMCache 0.3 s
after a 28k-token prefill has started (the situation in which the prototype acts); computed in that same situation with a cache
salt, so that neither cache is used.

| configuration | host load, alone | GPU prefix, alone | host load next to a prefill | computed next to a prefill | TTFT p50 of the host loads next to a prefill (s) |
|---|---|---|---|---|---|
| stock | 47 / 48 | 45 / 48 | 45 / 48 | 47 / 48 | 6.79 |
| stock, second run | 47 / 48 | 45 / 48 | 46 / 48 | 47 / 48 | 6.79 |
| P1 | 47 / 48 | 45 / 48 | 47 / 48 | 45 / 48 | 1.13 |
| P1, synchronous scheduling | 47 / 48 | 45 / 48 | 47 / 48 | 45 / 48 | 0.59 |
| P2 | 47 / 48 | 45 / 48 | 47 / 48 | 45 / 48 | 1.13 |

- **The three paths that run alone give the same text in every configuration, request by request** (48 / 48 identical between
  stock and each prototype run, for the computed, the host-loaded and the GPU-prefix answers): the prototype changes nothing in
  what a path produces.
- **Reusing KV instead of computing changes the text of 1 prompt in 48 (host load) and 3 in 48 (GPU prefix) on the stock server
  already.** The cached prefix is bit-identical to what was computed; the uncached tail is then computed in a different chunk
  than in the reference run, and on these random-token prompts a near-tie in the logits flips. A wrong or incomplete prefix would
  change nearly every answer, not one.
- **Next to a prefill the text depends on which requests share an engine step** (stock against its own second run: 47 / 48
  identical; stock against the prototypes: 46 / 48), for loaded and for computed answers alike.

**Output hashes in the replays (`check_runs.py`).** Two stock runs of the overloaded replay produce the same text for 543 of 544
requests. Any change of scheduling changes 2–4 % of the texts, the stock options as much as the prototype: synchronous scheduling
97.2 % identical to stock, prefill cap 97.6 %, store fix alone 98.9 %, P1 97.1 %, P2 97.2 %, P3 96.7 %; at the sustainable load
(c61, pinned pool) P1 97.8 %. Requests that were loaded from LMCache in one run and computed in the other agree as often as the
rest (96–98 % in the prototype runs).

**Blocks, leaks, preemptions, repeated loads** (the same script; the overloaded tool-agent replay, `replay/tables-correctness-tool08.md`).

| check | stock | stock, second run | store fix | P1 | P2 | P2, second run | P3 |
|---|---|---|---|---|---|---|---|
| requests completed | 544 | 544 | 544 | 544 | 544 | 544 | 544 |
| output tokens generated | 112,233 | 112,233 | 112,233 | 112,233 | 112,233 | 112,233 | 112,233 |
| requests with more than one LMCache load | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| preemptions / running requests refused their next chunk | 5 / 10 | 6 / 12 | 7 / 14 | 9 / 18 | 8 / 16 | 7 / 16 | 11 / 22 |
| engine steps with no request holding blocks at which the whole pool is free | 61 / 61 | 61 / 61 | 65 / 65 | 58 / 58 | 60 / 60 | 62 / 62 | 57 / 57 |
| requests that store KV / GB stored | 396 / 73.8 | 393 / 73.7 | 477 / 108.9 | 477 / 108.7 | 477 / 108.8 | 477 / 108.8 | 477 / 108.9 |

No run leaks blocks: whenever nothing is running, loading or holding KV in the queue (and the last holder ended at least 50 ms
earlier, the time vLLM keeps a finished request's blocks until its store is confirmed), the free count equals the pool minus the
null block. No request is loaded twice. The prototype does not allocate, free or map blocks itself — it changes the connector's
answer, the reservation number and the per-step caps — so block validity rests on the stock allocator in every configuration.
Preempted requests recompute their prompt (stock rule); the prototype configurations have 7–11 preemptions against 5–6, the
first version had 32 (B0).

**Repeats and variability.** *Replays:* a second run of the stock overloaded replay differs from the first by 0.07 s in TTFT
p50 (12.45 / 12.38), 0.05 s in p95, 0.03 s in the mean; every class mean within 0.4 %. A second run of P2: p50 8.64 / 8.61,
mean 14.09 / 14.15, class means within 1–8 %. The replay is open-loop with fixed prompts and arrival times, so it is close to
deterministic; differences of a few percent between configurations are differences of the configurations. *Controlled scenarios:*
three repetitions each; the three values of a cell differ by at most 0.02 s in scenarios c1 and c3 (0.13 s with synchronous
scheduling) and by at most 0.4 s in c5. *Across machines:* the pinned-pool stock replay on a 16 GB node reproduces c28's replay of
2026-11-05 (C3, Result 1), and the gain of the prototype at the sustainable load was measured on both (C2, C3). Sample sizes are
given with every table (n per class).

**Instrumentation overhead (`adm_overhead.py`).** The step stream of the 2026-11-04 hooks records the duration of the scheduler's
`schedule()` in both studies; the admission wrappers of this study run inside that interval.

| run | admission stream | steps | `schedule()` mean / p50 / p99 (µs) | total over the run (s) | share of the wall time |
|---|---|---|---|---|---|
| `dl-tool-dram320` (2026-11-05) | no | 87,171 | 129 / 86 / 660 | 11.3 | 0.23 % |
| `tool04-320-base` | yes | 87,151 | 135 / 88 / 699 | 11.8 | 0.24 % |
| `tool08-320-base` | yes | 21,789 | 224 / 144 / 987 | 4.9 | 0.38 % |
| `tool08-320-tokfast11` (policy v1.1) | yes | 21,149 | 322 / 170 / 2,085 | 6.8 | 0.53 % |

The wrappers add 6 µs to a 129 µs call (+5 %), 0.5 s over a replay of 4,982 s; the prototype's decisions add about 100 µs per
step. The instrumented stock replay reproduces the un-instrumented one of 2026-11-05 in every aggregate (A2.1, Result 1), and the
stock store loss of A5 is identical in both (48 requests, 187.9 of 200.5 GB).

**Raw logs.** Every run keeps its client records, per-request timelines, admission stream (every poll, admission attempt,
preemption and one line per engine step), LMCache event mirror, sampler output and server logs; nothing was edited after a run.
Small files are in the results directory of the repo, the streams on c28 (`README.md` there). The prototype's rules are covered by
mock tests (`kvadm/test_policy.py`, 9 cases).
