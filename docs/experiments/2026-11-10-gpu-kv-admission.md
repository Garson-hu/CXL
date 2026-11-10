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

**Result 5 — a side effect of retries (SOURCE A1.4, confirmed).** Of the external loads whose lookup result was polled once,
137 of 137 with new chunks stored them all; of those polled twice or more (refused and retried; median 32 polls, max 320),
17 of 17 stored nothing: after a refusal the request's new tokens do not reach the host tier.

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

**Explanation.** These trials answer the brief's questions for the block gate: admission of an external hit starts to fail
when the free blocks fall below the blocks of its whole sequence — the same point at which a miss of that length fails;
the number of concurrent requests is irrelevant beyond the blocks they hold; and a miss does not "make progress while the
hit waits" at the gate: what progresses are requests already RUNNING, which take their next chunk without a gate. What the
hit loses relative to a miss is not at the gate but around it (parts 3–5): its lookup result, its finished load and its
promotion are each picked up only at a step with token budget left, and a miss that starts in between takes the budget
first.
