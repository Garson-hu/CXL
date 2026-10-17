# 2026-10-17 — RQ1-B: do real agent runtime events give accurate, timely and actionable future-reuse information for KV cache management?

**STATUS: CLOSED 2026-10-17.** Evidence types: **REAL APPLICATION** (OpenAI Agents SDK 0.24.0 run loop, unmodified,
driving Qwen2.5-3B-Instruct-AWQ on vLLM 0.31.0 + LMCache 0.5.5 on c28's RTX 4060 Ti; events recorded by logging-only
hooks), **SOURCE INSPECTION** (where an event is produced), **TRACE SIMULATION on the real trace** (capacity sweep of the
host cache with the real events; reported separately from the Mooncake studies, never mixed). Previous rounds:
`2026-10-17-kv-reuse-oracle-study.md` (Gate 1), `2026-10-17-kv-session-hint-study.md`, `2026-10-17-rq1b-application-reuse-signals.md`
(the task-end event there was reconstructed from the trace; this file replaces it with measured events).
Raw: `experimental_results/2026-10-17-rq1b-agent-runtime-validation/` (`real/<tag>-{agent,kvevents}.jsonl`, server logs,
status, meta; `<tag>-calls.csv`, `<tag>-decisions.csv`, `<tag>-trace.jsonl`, `<tag>-summary.json`, `<tag>-replay.csv`, figures).
Code: `benchmarks/agent/` (`agent_tasks.py` workload, `run_agent.py` runner + hooks, `kvevt/sitecustomize.py` LMCache
event mirror, `run_agent_exp.py` launcher, `run_chain.sh`), `scripts/kv_agent_events.py` (join + timing + semantics),
`scripts/kv_agent_replay.py` (replay), `scripts/kv_agent_tables.py` (the tables below).

## Setup (what is real, what is a parameter)
- **Serving stack, unmodified:** `vllm serve Qwen/Qwen2.5-3B-Instruct-AWQ --enable-auto-tool-choice --tool-call-parser hermes
  --max-model-len 8192 --max-num-seqs 16 --num-gpu-blocks-override 2048|3072 --enforce-eager --dtype float16` with the
  LMCache multi-process connector (`kv_role kv_both`) and `lmcache server --chunk-size 256 --eviction-policy LRU
  --eviction-trigger-watermark 0.8 --l1-size-gb 1|4` (DRAM L1; one 256-token chunk of this model = 36 layers × 2 KV heads
  × 128 × fp16 × 256 = 9.44 MB, so 1 GB = 106 chunks, 4 GB = 424). The GPU KV cache is limited to 32k / 48k tokens so
  that the host cache, not the GPU, serves the reuse (as on a loaded server). Eager prefetch and lazy offload are off
  (defaults): the lookup happens at scheduling, the stores during prefill. One extra run tried LMCache's existing lazy
  offload (`lmcache.mp.lazy_offload`, threshold 1), which crashed the engine (Task D).
- **Agent, unmodified framework:** OpenAI Agents SDK `Runner.run(agent, prompt, max_turns=6)`; the loop is the SDK's
  ("tool calls → run the tools → call the model again; a text answer ends the run"). Three local tools
  (`search_reports`, `read_report`, `calculate`) over a seeded corpus of 48 synthetic facility reports (~430 tokens each);
  400 tasks of 6 kinds (energy / water total / uptime comparison / headcount / incidents difference / no-tool question),
  identical across runs (seed 11; 118 of the 400 prompts repeat an earlier task's prompt, which matters below). Report
  ids are random codes that only the search returns, so the loop has real step-to-step dependencies (search → read → …
  → answer): 3 LLM calls per task at the median, 6 at p90, 72% of the answers correct, 1 task of 400 hits `max_turns`.
  **Workload parameters** (stated, not measured): tool latencies 1.5 / 1.0 / 0.3 s standing in for remote tools; 8 or 16
  concurrent agents; max 6 LLM calls per task. Qwen2.5-1.5B-Instruct (fp16) was tried first and dropped: it emits every
  tool call at once with guessed ids, so every task was a two-call loop with a wrong answer (smoke runs, not kept).
- **Instrumentation, logging only (reversible):** (1) the SDK's own `RunHooks` (`on_llm_start/end`, `on_tool_start/end`,
  `on_agent_end`) and a model wrapper that adds an `X-Request-Id` header per chat-completion call (vLLM makes it the
  request id, `chatcmpl-agt<task>c<call>-…`, which LMCache carries in its events) and records submit / response times;
  (2) in the LMCache server process a `sitecustomize.py` on `PYTHONPATH` registers one more subscriber on LMCache's own
  event bus and writes one JSON line per event (`MP_LOOKUP` with the request's chunk hashes, `MP_LOOKUP_PREFETCH_END`
  with the hit count, `MP_STORE_START/END`, `L1_WRITE_RESERVED/FINISHED` with keys, `L1_KEYS_EVICTED` with keys,
  `L1_READ_RESERVED/FINISHED`, `L1_KEYS_ACCESSED`, `MP_VLLM_END_SESSION`, `MP_REQUEST_START/END`). No placement, eviction,
  admission or transfer code is changed; all timestamps are `time.time()` on the same host.
- **Not observable without changing vLLM (recorded as limits):** which prompt tokens vLLM served from its own GPU prefix
  cache per block (only the total `cached_tokens` per request is reported, GPU + LMCache together); the moment vLLM frees
  a request's GPU blocks (the connector's `request_finished` → `end_session` event is the proxy, 0.4 s after the last
  lookup at the median); KV of decode tokens (LMCache stores prefill chunks; a decoded answer is stored only when it is
  part of the next prompt); any eviction reason beyond LRU order.
- **Runs:** `k8-l1g` (8 agents, L1 1 GB), `k16-l1g` (16 agents, L1 1 GB), `k8-l4g` (8 agents, L1 4 GB), `k8-l1g-lazy`
  (8 agents, 1 GB, lazy offload on). 400 tasks, 1557–1564 LLM calls, 5.2 / 2.9 / 5.2 min of serving each.

## Task A — the real event order (fig-agent-timeline-k8-l1g, one task; the table gives the distributions)
For every LLM call: the SDK submits the request → vLLM schedules it and the connector's lookup reaches the LMCache
server **12 ms later (p50; p90 58–72 ms)** — on this small model at 8–16 agents there is no queue; → the lookup result
comes 2 ms later; → the new prompt chunks are **stored during prefill**, before the first output token; → the response
arrives 0.4 s (p50) / 1.5 s (p90) after the lookup; → the SDK's `on_llm_end` fires: if the output carries tool calls the
runtime **knows it will continue** and runs the tools (1.0–1.5 s here); the next call is submitted 1.2–1.3 s after the
decision. If the output is text, `on_agent_end` fires — the runtime **knows the task has ended** — and vLLM's
`request_finished` reaches LMCache (`end_session`) within the same 0.4 s. The KV of the final prompt was written
**0.40–0.45 s before** the end decision (p50; 1.2–1.5 s at p90). Under LRU the task's private chunks are then evicted one
cache turnover later: 21 s (8 agents, 1 GB), 10 s (16 agents, 1 GB), 99 s (8 agents, 4 GB). Events that do not exist in
the loop: nothing between "tool calls present" and "no tool calls"; no plan beyond the next call; no cancellation other
than `max_turns` (1 of 400).

| | k8-l1g | k16-l1g | k8-l4g |
|---|---|---|---|
| tasks / LLM calls | 400 / 1562 | 400 / 1564 | 400 / 1557 |
| LLM calls per task p50 / p90 | 3 / 6 | 3 / 6 | 3 / 6 |
| outcomes | task_end 399, abort:max_turns 1 | task_end 399, abort:max_turns 1 | task_end 399, abort:max_turns 1 |
| request submit → LMCache lookup, s (p50 / p90) | 0.012 / 0.058 | 0.014 / 0.072 | 0.012 / 0.058 |
| lookup → response (prefill + decode), s | 0.42 / 1.52 | 0.54 / 1.69 | 0.41 / 1.48 |
| tool execution, s | 1.09 / 1.50 | 1.08 / 1.51 | 1.08 / 1.50 |
| continue decision → next call's lookup, s | 1.30 / 1.62 | 1.25 / 1.61 | 1.22 / 1.60 |
| continue: context chunks re-read by the next call | 100% | 100% | 100% |
| continue: next call's chunks that already exist | 87% | 87% | 87% |
| continue: context chunks evicted before the next call | 0.0% | 0.0% | 0.0% |
| continue: next call fully hit in LMCache | 100% | 99% | 99% |
| end: private chunks never read again | 704 / 837 (84%) | 706 / 835 (85%) | 698 / 833 (84%) |
| end: shared chunks read again by other tasks | 1631 / 1772 (92%) | 1632 / 1774 (92%) | 1629 / 1772 (92%) |
| end decision − last KV write of the task, s | 0.40 / 1.21 | 0.45 / 1.48 | 0.41 / 1.20 |
| end decision − last LMCache lookup of the task, s | 0.38 / 0.79 | 0.42 / 1.20 | 0.36 / 0.75 |
| age of the task's private chunks at the end, s | 1.10 / 3.64 | 1.30 / 3.96 | 1.08 / 3.66 |
| end decision → eviction of its private chunks under LRU, s | 20.9 / 24.3 | 10.2 / 12.3 | 98.8 / 111.3 |
| L1 turnover (write → eviction), s | 22.3 / 27.6 | 11.8 / 15.6 | 100.4 / 114.0 |
| write → next reuse of a chunk, s | 1.3 / 61.0 | 1.4 / 33.2 | 1.3 / 59.1 |
| chunks written / evicted / unique | 1030 / 952 / 852 | 1035 / 957 / 852 | 920 / 584 / 849 |
| final call's new chunks, share of all writes | 51% | 48% | 57% |
| REAL reuse-hit share in LMCache (chunks seen before that hit) | 0.971 (6918/7125) | 0.965 (6891/7139) | 0.986 (6999/7099) |

## Task B — what the decisions mean for the blocks (REAL; fig-agent-signal-<tag>)
- **Continue.** Known at `on_llm_end`, i.e. at the moment the response is parsed, before any tool runs. At that moment
  the next request's prefix is determined (the current context plus the tool outputs), but only the current context
  exists in the cache: the next call re-reads **100%** of the current context chunks (precision 1.0 in all 3482 continue
  decisions; the SDK appends and never truncates within `max_turns`) and **87%** of the next call's chunks already exist
  (the rest are the tool result and the assistant message, which cannot be cached before they exist). The lead time
  decision → next lookup is the tool time (1.25–1.30 s p50, 1.6 s p90). With L1 ≥ 1 GB no context chunk was evicted
  between the decision and the next call (0 of 3482), and the next call hit fully in LMCache in 99–100% of the cases —
  LRU already keeps the context because the reuse interval (1.3 s) is 8–80× shorter than the turnover (10–99 s).
  Class: **guaranteed** (framework control flow) for "the context will be re-read"; the exact new chunks are unknown.
- **End.** Known at `on_agent_end` (text output, no tool calls), 0.4 s after the last lookup and after the last KV write.
  Of the ending task's **private** chunks (never referenced by another task before), **84–85% are never read again**;
  the 15–16% that are read again belong to tasks whose prompt repeats an earlier one (118 of 400 by construction) — a
  later task with the same question re-reads them 33–61 s later (p90 of write → next reuse). Of the chunks the task
  **shares** with other tasks (system prompt + tool schemas = 3 of every request's chunks), **92% are read again** by
  others. So the end event is a reliable negative signal for the task's own context but must not touch shared blocks:
  the manager needs the task id on each request (to count live referencing tasks) — the same per-request field the
  earlier source inspection identified (`kv_transfer_params` / `cache_salt`). Class: **guaranteed** for "this task will
  not read these blocks again"; **probabilistic** (85% here, workload-dependent) for "nobody will".
- **Retrospective** information (only the simulator has it): which of the dead-marked private blocks a later identical
  prompt will re-read; which new chunks the next call will add; the block oracle.

## Task C — timing against the cache (REAL; fig-agent-leadtimes-<tag>)
| interval | k8-l1g | k16-l1g | k8-l4g | what it means |
|---|---|---|---|---|
| request submit → LMCache lookup | 0.012 / 0.058 s | 0.014 / 0.072 s | 0.012 / 0.058 s | queue lookahead on this server: nothing |
| block creation (KV write) → continue decision | 1.1 / 3.6 s (private chunks) | 1.3 / 4.0 s | 1.1 / 3.7 s | the context is seconds old when the runtime decides |
| continue decision → next call's lookup (= reuse) | 1.30 / 1.62 s | 1.25 / 1.61 s | 1.22 / 1.60 s | the hint's lead = tool time |
| decision → eviction of the context (LRU) | never before the next call | never | never | turnover 12–100 s ≫ 1.3 s |
| end decision − last KV write of the task | +0.40 / +1.21 s | +0.45 / +1.48 s | +0.41 / +1.20 s | the write precedes the event: not cancellable |
| end decision → eviction of its private chunks (LRU) | 20.9 / 24.3 s | 10.2 / 12.3 s | 98.8 / 111 s | the occupancy the event could release |
| L1 turnover (write → eviction) | 22.3 / 27.6 s | 11.8 / 15.6 s | 100 / 114 s | |
| write → next reuse of a chunk | 1.3 / 61 s | 1.4 / 33 s | 1.3 / 59 s | within-task at p50; duplicate prompts at p90 |
| REAL reuse-hit share in LMCache | 0.971 | 0.965 | 0.986 | at the configured L1 |

(p50 / p90.) Compared with the Mooncake traces of Phase 1 (turnover ≈ 1 min at 200 GiB; next-turn gap p50 123 s for
conversation, 0 s for the tool-agent trace with p90 150 s): this agent loop reuses its context 1–2 s after the decision,
so a correct hint arrives long before any useful decision point only when the cache turns over faster than the tool
runs — i.e. when the cache is smaller than the live working set. "A correct hint arriving after the relevant cache
decision is not actionable": for the **end** event this is the case for the write (it is 0.4 s late), not for the
eviction (10–100 s early).

## Task D — replay of the real traces with the real events (TRACE SIMULATION on REAL traces; fig-agent-replay-<tag>)
Policies decide with information available at their decision time; `event_*` use the recorded continue / end events
at their recorded times; `ttl` and `event_*` need the task id per request. Reuse-hit share on the second half of each
trace; in brackets the share of the block oracle's gain over global LRU; w = chunks written. The 24–32-chunk rows are
below the live working set (8 agents ≈ 50 chunks, 16 agents ≈ 100); the 96–128-chunk rows are the 1 GB of the real runs.

Replay of k8-l1g — reuse-hit share (share of the oracle's gain over global LRU) and chunks written (w):

| capacity | split | lru | slru | ttl30 | event_end | event_both | event_both+slru | event_end+defer | oracle |
|---|---|---|---|---|---|---|---|---|---|
| 24 chunks = 0.23 GB | 0.914 w1428 | 0.940 w1229 | 0.941 (3%) w1231 | 0.940 (0%) w1229 | 0.946 (22%) w1157 | 0.949 (31%) w1147 | 0.949 (30%) w1149 | 0.952 (42%) w576 | 0.968 w668 |
| 32 chunks = 0.30 GB | 0.950 w1170 | 0.953 w1110 | 0.954 (4%) w1109 | 0.953 (0%) w1110 | 0.954 (4%) w1108 | 0.954 (3%) w1109 | 0.954 (3%) w1109 | 0.953 (1%) w555 | 0.974 w645 |
| 48 chunks = 0.45 GB | 0.959 w1070 | 0.959 w1068 | 0.960 (5%) w1064 | 0.959 (0%) w1068 | 0.958 (-2%) w1070 | 0.958 (-2%) w1070 | 0.958 (-2%) w1070 | 0.957 (-6%) w534 | 0.981 w618 |
| 96 chunks = 0.91 GB | 0.967 w1014 | 0.967 w1013 | 0.966 (-4%) w1017 | 0.967 (0%) w1013 | 0.967 (0%) w1015 | 0.967 (0%) w1015 | 0.967 (0%) w1015 | 0.959 (-28%) w518 | 0.997 w591 |
| 128 chunks = 1.21 GB | 0.970 w992 | 0.970 w990 | 0.969 (-4%) w996 | 0.970 (0%) w990 | 0.970 (0%) w990 | 0.970 (0%) w990 | 0.970 (0%) w990 | 0.961 (-33%) w506 | 1.000 w591 |
| 384 chunks = 3.62 GB | 0.987 w893 | 0.988 w888 | 0.984 (-34%) w907 | 0.988 (0%) w888 | 0.987 (-5%) w890 | 0.987 (-5%) w890 | 0.987 (-5%) w890 | 0.965 (-184%) w487 | 1.000 w591 |

Replay of k16-l1g — reuse-hit share (share of the oracle's gain over global LRU) and chunks written (w):

| capacity | split | lru | slru | ttl30 | event_end | event_both | event_both+slru | event_end+defer | oracle |
|---|---|---|---|---|---|---|---|---|---|
| 24 chunks = 0.23 GB | 0.861 w1819 | 0.867 w1772 | 0.867 (-0%) w1763 | 0.867 (0%) w1772 | 0.903 (39%) w1503 | 0.924 (61%) w1332 | 0.927 (66%) w1296 | 0.942 (81%) w627 | 0.959 w690 |
| 32 chunks = 0.30 GB | 0.916 w1398 | 0.928 w1328 | 0.924 (-9%) w1352 | 0.928 (0%) w1328 | 0.951 (55%) w1136 | 0.953 (59%) w1115 | 0.953 (60%) w1114 | 0.956 (67%) w555 | 0.970 w659 |
| 48 chunks = 0.45 GB | 0.956 w1094 | 0.959 w1071 | 0.958 (-5%) w1080 | 0.959 (0%) w1071 | 0.960 (4%) w1065 | 0.960 (4%) w1065 | 0.960 (4%) w1065 | 0.959 (0%) w532 | 0.980 w628 |
| 96 chunks = 0.91 GB | 0.968 w1009 | 0.968 w1007 | 0.967 (-3%) w1010 | 0.968 (0%) w1007 | 0.968 (0%) w1007 | 0.968 (0%) w1007 | 0.968 (0%) w1007 | 0.960 (-30%) w519 | 0.995 w596 |
| 128 chunks = 1.21 GB | 0.970 w991 | 0.970 w990 | 0.969 (-2%) w995 | 0.970 (0%) w990 | 0.970 (0%) w990 | 0.970 (0%) w990 | 0.970 (0%) w990 | 0.962 (-28%) w509 | 1.000 w595 |
| 384 chunks = 3.62 GB | 0.986 w895 | 0.986 w896 | 0.984 (-18%) w905 | 0.986 (0%) w896 | 0.986 (0%) w896 | 0.986 (0%) w896 | 0.986 (0%) w896 | 0.966 (-146%) w491 | 1.000 w595 |

Replay of k8-l4g — reuse-hit share (share of the oracle's gain over global LRU) and chunks written (w):

| capacity | split | lru | slru | ttl30 | event_end | event_both | event_both+slru | event_end+defer | oracle |
|---|---|---|---|---|---|---|---|---|---|
| 24 chunks = 0.23 GB | 0.914 w1413 | 0.943 w1201 | 0.939 (-14%) w1227 | 0.943 (0%) w1201 | 0.949 (22%) w1141 | 0.950 (23%) w1138 | 0.950 (23%) w1138 | 0.951 (30%) w570 | 0.970 w667 |
| 32 chunks = 0.30 GB | 0.952 w1145 | 0.954 w1103 | 0.953 (-4%) w1106 | 0.954 (0%) w1103 | 0.954 (-1%) w1102 | 0.954 (-1%) w1102 | 0.954 (-1%) w1102 | 0.954 (0%) w546 | 0.976 w642 |
| 48 chunks = 0.45 GB | 0.959 w1063 | 0.959 w1064 | 0.959 (4%) w1060 | 0.959 (0%) w1064 | 0.959 (0%) w1063 | 0.959 (0%) w1063 | 0.959 (0%) w1063 | 0.957 (-7%) w530 | 0.981 w617 |
| 96 chunks = 0.91 GB | 0.967 w1011 | 0.967 w1012 | 0.967 (0%) w1008 | 0.967 (0%) w1012 | 0.967 (0%) w1012 | 0.967 (0%) w1012 | 0.967 (0%) w1012 | 0.959 (-25%) w514 | 0.998 w587 |
| 128 chunks = 1.21 GB | 0.970 w988 | 0.970 w985 | 0.969 (-6%) w995 | 0.970 (0%) w985 | 0.970 (-1%) w986 | 0.970 (-1%) w986 | 0.970 (-1%) w986 | 0.960 (-35%) w504 | 1.000 w587 |
| 384 chunks = 3.62 GB | 0.987 w887 | 0.987 w888 | 0.984 (-19%) w901 | 0.987 (0%) w888 | 0.987 (0%) w888 | 0.987 (0%) w888 | 0.987 (0%) w888 | 0.965 (-160%) w483 | 1.000 w587 |

- **Hits.** At any capacity at or above the live working set LRU already serves 96–99% of the reuses and the real
  events add nothing (−2 … +4% of the remaining gap); the remaining 1–3 points to the oracle are the duplicate-prompt
  re-reads a minute later, which no runtime event announces. Below the live set (16 agents, 0.23–0.30 GB) the end event
  recovers 39–55% and end + continue 60–66% of the oracle's gain (67–88% with deferred stores). Session TTL (10 / 30 s)
  equals LRU everywhere; SLRU is within ±5%.
- **Check against the real system:** the replay at 0.91–1.21 GB gives 0.967–0.970 where the real runs measured 0.971
  (8 agents, 1 GB), 0.965 (16 agents) and 0.986 at 4 GB (replay 0.987 at 3.6 GB).
- **Writes.** The end event alone changes nothing (the KV is written before it). With the store deferred until the
  request ends and dropped on `end` (LMCache's lazy offload would hold it; the drop is not implemented), writes fall
  from 1007–1013 to 518–519 chunks at 0.91 GB (**−49%**; the final call's new chunks are 48–57% of all writes) at the
  cost of 0.8 points of reuse-hit share (the duplicate-prompt re-reads of dropped chunks); the oracle writes 591–596.
- **Dead occupancy.** Under LRU 74–86% of the cache-time at ≥ 0.9 GB holds blocks that are never read again; the event
  policies do not lower it (they only change the eviction order), they would release it only if the manager shrank or
  shared the cache.

- **Deferred stores in the real system (k8-l1g-lazy): not measurable with LMCache 0.5.5.** With `lmcache.mp.lazy_offload`
  on (threshold 1, an existing option, no policy change) vLLM's engine core died at the first finished request:
  `ValueError: mark req finished failed: req_id chatcmpl-agt0003c01-… not in pending_items`
  (`lazy_offload_policy/fifo.py:73`, raised from the connector's `request_finished` for a request that had queued no
  store, e.g. a fully cached prompt); all 400 tasks aborted (`real/k8-l1g-lazy-server.log`). Fixing it means changing
  LMCache, which is out of scope, so the write-avoidance number above stays a simulation; what the source shows is that
  the deferral window would be the request lifetime (store issued at the scheduler step after `request_finished`, i.e.
  ≈ 0.4 s after the last lookup here) and the end decision arrives inside that window.

## RQ1-B decision for agent workloads (charter Gate 2: ≥ 50% of the oracle's gain, errors ≤ 25% of the gain)
**Verified facts (REAL):** (1) an agent runtime knows continue / end at the end of every LLM call, with no delay
(`on_llm_end` / `on_agent_end`), and nothing more; (2) the information is block-exact for the request's own prefix
chunks: on continue, 100% of the context is re-read 1.3 s later; on end, 84–85% of the task's private chunks are dead
(the rest: identical later prompts) and 92% of its shared chunks are live; (3) the end event arrives 0.4 s **after** the
last KV write, so it can only shorten retention, never cancel a write, unless stores are deferred; (4) at a host cache
≥ the live working set, LRU already captures the within-task reuse (real reuse-hit share 0.965–0.986), because the
reuse interval (1.3 s) is far below the turnover (10–100 s).
**Simulated on the real trace:** the events reach Gate 2 (55–66%) only when the cache is smaller than the live working
set; above it they recover ≤ 4%. Deferred stores + end event cut writes 49% (simulated; the drop is not implemented).
**Not verified:** real tools with latencies of tens of seconds (they lengthen both the lead and the reuse interval);
agents at the 70B / 200 GiB scale of the Mooncake studies (the 4060 Ti cannot run them); chat applications (no event).
**Gate 2: PARTIAL for agent workloads** — information: PASS (available, timely, exact); hit-rate value: FAIL at normal
capacity (≤ 4%), PASS under capacity pressure (55–66%); write value: 49% in simulation only. The reconstructed-event
result of the previous round (41% of the ceiling on the Mooncake agent trace at 200 GiB) is not contradicted but not
confirmed either: that trace's turn structure (p90 gap 150 s) differs from this loop's (1.3 s), and only a real agent
trace at that scale would settle it.

## Recommendation
Real agent runtime signals are actionable, but not for what RQ1 asked. They cannot raise the hit rate of a sensibly
sized host cache (LRU already has the within-task reuse); they can (a) release 74–86% of the cache-time that LRU spends
on dead blocks, and (b) with a deferred store, avoid about half of the KV writes — a write-side and capacity-side value
that belongs to RQ3 (interference) and to capacity sharing, not to reuse prediction. The next stage should therefore
not be built on hit-rate prediction for agents; it should carry the lifecycle event as a cheap release + deferred-store
interface and evaluate its value jointly with the write scheduler. What would still change this verdict: an agent
workload whose tool latencies approach the cache turnover (then the continue signal protects contexts LRU would lose),
measurable only with real long-running tools or a trace that records them.
