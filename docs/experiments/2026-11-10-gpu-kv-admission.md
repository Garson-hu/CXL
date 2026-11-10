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
  nodes with the same GPU model and twice the memory (probe job 334260 on c23: RTX 4060 Ti 16 GiB, EPYC 7302P 16 cores,
  125 GiB RAM) — used for Experiment E.

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
