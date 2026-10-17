# 2026-10-17 — RQ1-B: can an LLM serving application, its scheduler or an agent framework expose actionable future-reuse information before the KV blocks are evicted?

**STATUS: CLOSED 2026-10-17.** Evidence types: **SOURCE INSPECTION** (vLLM 0.31.0 and LMCache 0.5.5 as installed in
`/mnt/local/ghu4/envs/lmcache`; OpenAI Agents SDK and LangGraph public sources), **REAL APPLICATION** (lead times measured
on the c28 runs of 2026-10-12), **TRACE SIMULATION** (Mooncake traces, Phase 1 protocol), **ORACLE** where marked. Raw:
`experimental_results/2026-10-17-rq1b-application-reuse-signals/` (figures) and
`experimental_results/2026-10-17-kv-session-hint-study/session-hints-8b-200GiB-queue.csv` (+ `run-log-queue.txt`).
Scripts: `scripts/kv_session_hint_study.py` (policies `queue<W>`, `queue<W>+slru`, `queue<W>+end0`), `scripts/kv_queue_signal_figs.py`.
Charter: `docs/research/CHARTER.md`; previous rounds: `2026-10-17-kv-reuse-oracle-study.md`, `2026-10-17-kv-session-hint-study.md`.

## Task A — what the application actually knows between a block's creation and its eviction (inventory)
| # | information | source (file:line) | earliest availability | guaranteed? | refers to | change needed | usefulness for reuse |
|---|---|---|---|---|---|---|---|
| A1.1 | The prompt's prefix block hashes of a request that has ARRIVED but is not yet served | vLLM `v1/request.py:225–288` (`block_hashes` filled in `Request.__init__`); scheduler `v1/core/sched/scheduler.py:2557–2583` (`add_request` → `connector.on_new_request`); LMCache `integration/vllm/lmcache_mp_connector.py:1092–1109` (`on_new_request` submits the lookup when `lmcache.mp.eager_prefetch` is on; default off, line 494–496) | at arrival (queued); lookup otherwise at scheduling (`get_num_new_matched_tokens`, scheduler:949) | yes (the prompt is fixed; aborts are the only exception) | exact blocks (hashes) | enable eager prefetch; add "pin until served" in the eviction policy (LMCache has `pin/unpin` on memory objects, `storage_backend/local_cpu_backend.py:258–266`, used today only during transfers) | positive only; lead time = queue wait: measured p50 0.19–0.26 s, p90 2.6–6 s on c28 at 0.08× (fig-real-leadtime); tens of seconds only under overload |
| A1.2 | Which queued requests will hit existing blocks (lookup result) | LMCache `multiprocess/modules/lookup.py:146` (`lookup`), "Prefetch request completed … retained keys" in the server log | same as A1.1 | yes | exact | none | same as A1.1 |
| A1.3 | Queue wait itself (how long the lookahead is) | vLLM `EngineCoreEventType.QUEUED / SCHEDULED` (`v1/engine/__init__.py:172–177`) | at scheduling | yes | per request | none (stats) | calibrates A1.1 |
| A2.1 | An agent runtime knows, when the model's answer contains tool calls, that it will call the model again with the same history plus the tool results; when the answer is final, that the loop ends | OpenAI Agents SDK run loop ("If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop"; "final output … no tool calls → the loop ends"); LangGraph `prebuilt/chat_agent_executor.py` `should_continue`: `AIMessage.tool_calls` → `tools` node → back to the model, else `END` | at the end of each LLM call (before the tools run) | yes, structural (the loop decision is the framework's own) | the request's prompt + output blocks; the next call re-reads ~82% of them (session study) and 14% of the new ones | the agent must pass {session id, continue/end} per request; vLLM already carries per-request fields to the connector: `cache_salt` (`entrypoints/openai/chat_completion/protocol.py:456`, `v1/request.py:185`) and `kv_transfer_params` (`protocol.py:143/470` → `v1/request.py:105–121` → `request_finished`, `lmcache_mp_connector.py:1250–1300`) | continuation: lead = tool execution time; termination: delay 0 at the last call — the signal the session study measured as `hint:delay=0` (41% of the ceiling on the agent trace) |
| A2.2 | Tool-call dependencies / execution plan beyond the next call | not represented in either framework's loop; plans are LLM output, not runtime state | — | no | — | — | not available as a guaranteed signal |
| A3.1 | Request finished (all tokens generated) | vLLM scheduler `_free_request` → `connector.request_finished` (scheduler:2951–2998); LMCache `request_finished` → `end_session(request_id)` (`lookup.py:511`: removes the per-request session and touches its hashes) | at request end | yes | the request's blocks | none | says nothing about the conversation's future; with LMCache's lazy offload (`lazy_offload_pending_store.py`: stores buffered until `lmcache.mp.lazy_offload_threshold` = 100 finished requests, FIFO) a "dead" decision at request end could cancel the store — otherwise the store has already happened during prefill |
| A3.2 | Request aborted / client disconnected | scheduler `finish_requests(…, FINISHED_ABORTED)` (scheduler:2570, 2585) | at abort | yes | the request's blocks | none | rare; a cancelled request's new blocks are dead with high probability |
| A3.3 | Conversation / session end in chat | not present: a chat request carries no session id by default (`cache_salt` is an optional tenant/isolation key), and the client does not say whether the user will continue | — | no | — | a client-side event (tab closed, conversation deleted) would be late | the session study: termination events ≥ 60 s late are worth 0% |
| A3.4 | Context truncation (the next turn drops part of the history) | visible only when the next request arrives (prefix mismatch) | too late | — | — | — | explains why 18% of a continued turn's blocks are not re-read |
| A3.5 | Cross-session shared prefixes (system prompts, tool descriptions) | prefix matching at lookup; `cache_salt` groups per tenant; `IsolatedLRUEvictionPolicy` keeps one LRU per salt (`distributed/eviction_policy/isolated_lru.py:36`) | at arrival | yes | exact | none | handled by frequency already (these blocks are hit constantly); no hint needed |

## Task B — what each available signal predicts
| signal | granularity | timing | coverage | false positive / negative risk | runtime feasibility |
|---|---|---|---|---|---|
| A1 queued-request prefixes | block | arrival; usable for the queue wait W | the reuses whose next request arrives within W: 22% within 60 s on chat, 80% within 60 s on the agent trace (session study), but W itself is 0.2 s median on a healthy server | none (exact), except aborts | small: eager prefetch + pin until served |
| A2 agent-loop continue / end | the request's context (session) | end of each LLM call; continuation lead = tool time, termination delay 0 | agent workloads only; ~82% of the context is re-read | FP: truncated context (18%); FN: none structurally | small: one per-request field from the agent runtime, consumed at `request_finished` / lazy-offload selection |
| A3 request end / abort | request | request end | all requests | — | none; it is not a reuse prediction |
| history-based estimates (Phase 1) | block / session | at creation | — | lift ≤ 1.5× | — (not pursued) |

## Task C — offline replay evaluation (TRACE SIMULATION; Phase 1 protocol: 200 GiB, 8B blocks, second half scored)
Policies that use only information available at the decision time: static split (B), global LRU (C), SLRU 1/3 (the best
online policy of Phase 1; `queue0+slru`), `queue<W>` (blocks of requests that have arrived but are not served for W
seconds are evicted last — W is the queueing delay, a scenario parameter since the trace records arrivals; W = 0 is what
the trace guarantees), `queue<W>+slru`, the agent task-end event at delay 0 (`hint:delay=0`; realistic for agent runtimes,
an ORACLE for chat because chat clients do not emit it), and the combination `queue<W>+end0`. Upper bound: the block
oracle. Reuse-hit share; in brackets the share of the block oracle's gain over the static split.

| policy | conversation | tool agent | synthetic |
|---|---|---|---|
| static split (B) / global LRU (C) | 0.174 | 0.647 | 0.344 |
| SLRU 1/3 (online, Phase 1 best) | 0.209 (6%) | 0.661 (5%) | 0.361 (5%) |
| queue, W = 1 / 5 / 10 s | 0.174 / 0.175 / 0.176 (0 / 0 / 0%) | 0.647 / 0.647 / 0.648 (0%) | 0.344 / 0.374 / 0.397 (0 / 9 / 15%) |
| queue, W = 30 / 60 / 300 s | 0.189 / 0.202 / 0.191 (2 / 5 / 3%) | 0.651 / 0.658 / 0.655 (1 / 4 / 3%) | 0.396 / 0.363 / 0.352 (15 / 5 / 2%) |
| queue + SLRU, W = 10 / 30 / 60 s | 0.210 / 0.224 / 0.214 (6 / 8 / 6%) | 0.662 / 0.667 / 0.663 (5 / 7 / 5%) | 0.403 / 0.466 / 0.414 (17 / 35 / 20%) |
| task-end event, delay 0 (agent: realistic; chat: ORACLE) | 0.506 (53%) | 0.766 (41%) | 0.485 (40%) |
| task-end + queue, W = 10 / 30 / 60 s | 0.519 / 0.541 / 0.558 (55 / 59 / 62%) | 0.775 / 0.783 / 0.788 (44 / 46 / 48%) | 0.524 / 0.535 / 0.509 (51 / 54 / 47%) |
| block oracle (E) | 0.797 (100%) | 0.940 (100%) | 0.696 (100%) |

Measured lead times on c28 (fig-real-leadtime; vLLM + LMCache MP, Qwen2.5-1.5B, 0.08× load, eager prefetch off):
request arrival → LMCache lookup done (= the queue wait) p50 0.19–0.26 s, p90 2.6–6.0 s; lookup → first token (chunked
prefill) p50 5.6–7.9 s, p90 9–21 s. At the 0.2× overload point of 2026-10-10 the queue wait was 40–145 s.

- **The scheduler-queue signal is exact but too short-sighted.** With the queue waits a healthy server has (≤ 10 s) it
  recovers ≤ 0.3% of the ceiling on the two real traces (15% on synthetic, whose turns come 55 s apart); only a server
  that is already overloaded (W ≥ 30–60 s) gets 2–5%, and on top of the task-end event it adds 2–9 points of the gain.
  The reason is Phase 1's: the median gap between a block's uses is ~2 minutes on chat, far beyond any queue.
- **The agent-loop termination event is the only realistic signal with substance:** 41% of the ceiling on the agent
  trace (0.647 → 0.766, +12 points; 48% with a 60 s queue), the same 53% on chat where it is an oracle. Its value is
  retention (freeing the blocks of finished tasks at once): in the replay it cuts recompute by 11 / 14 / 17% and writes
  by only 10 / 12 / 11% (agent / chat / synthetic; fewer re-stores after misses). The bytes of an ending task's own
  blocks — up to −57 / −65 / −43% of all writes, the session study's admission oracle — are avoided only where the store
  is deferred past the request end (LMCache's lazy offload) and dropped on the event; otherwise the KV has been written
  during prefill and the event cannot undo it. The replay does not model the lazy-offload timing.
- Honest limit of the trace: the tool-agent trace has no task ids or loop decisions; "session continues" is reconstructed
  from prefix chains, so the replay's task-end event is TAKEN FROM THE TRACE (the session's last turn, i.e. derived from
  later accesses). It is a stand-in for the event an agent runtime emits at its final output — which the source
  inspection shows is structural — not an online hint obtained from the trace. If part of that trace is human-driven,
  the 41% is an upper bound for the agent-loop signal. Only a real agent run with logged loop decisions (item 7 below)
  turns this into an online measurement.

## Task D — minimal application modifications (the two schemes worth building, if any)
1. **Agent-runtime lifecycle channel (the one to pursue).** Where: the agent runtime's loop decision (OpenAI Agents SDK
   runner after classifying the output; LangGraph `should_continue`) → one per-request field on the chat-completion call
   (`kv_transfer_params`, already parsed by vLLM into `Request.kv_transfer_params` and handed to the connector at
   `request_finished`; or `cache_salt` as the session key) → LMCache: at `request_finished` the session's blocks become
   evict-first on `end`, and with lazy offload their pending stores are dropped; on `continue` they are pinned for the
   tool's expected duration (bounded). Information origin: the framework's own control flow — earlier than any cache
   history (it exists before the next request is formed), guaranteed, mapped to the request's own blocks (hash-exact).
   Why better than session hints: it is the session hint with delay 0 and no estimation, for the one workload class
   whose runtime actually has it. Expected value on the agent trace: +12 points of reuse-hit share, recompute −11%,
   writes −10% as pure retention; up to −57% of the writes if stores are deferred to request end (lazy offload) and
   dropped on `end` (the session study's admission oracle, not simulated with lazy-offload timing) — to be confirmed
   with real agent events (below).
2. **Queued-request pinning (not worth a project on its own).** Enable `lmcache.mp.eager_prefetch`; pin looked-up blocks
   until the request is served. Exact and cheap, but worth ≤ 0.3% at realistic queue waits; its only real use is to stop
   a block from being evicted between lookup and load, which LMCache's transfer pins already cover.

## RQ1-B progress report (Deliverable 5)
1. **Available at run time today:** queued requests' exact block hashes (at arrival), lookup results, queue waits,
   request end and abort events, per-tenant keys. Not available: anything about a chat user's next message.
2. **Needs application changes:** the agent loop's continue/end decision (one field per request); queued-request pinning
   (two small LMCache changes).
3. **Before eviction?** The queue signal yes, but with a 0.2 s median lead it protects almost nothing that LRU would not
   keep anyway; the agent termination event yes (delay 0). Request-end events arrive after the KV was written unless
   offload is lazy.
4. **Mapping to blocks:** hash-exact for queued requests; the request's own context for the agent event, of which ~82%
   is re-read by the next call.
5. **Hit-rate benefit:** chat — realistic signals recover ≤ 6% of the oracle's gain (SLRU 6%, queue 0–5%); agent —
   41–48% (+12–14 points of reuse-hit share, 0.65 → 0.77–0.79), recompute −11–13%, writes −10–12% (retention only; up to
   −57% only if stores are deferred to request end and dropped on the event).
6. **Worth developing?** For agent workloads, yes, as a small mechanism (one per-request field, a release path and a
   bounded pin) — but it is an interface, not a prediction result, and it does not reach the 50% gate. For chat, no:
   RQ1-B stays unestablished and should not be pursued further with predictors.
7. **Minimal verification still needed:** one real agent run (OpenAI Agents SDK or LangGraph against vLLM + LMCache on
   the 4060 Ti) that logs per LLM call the task id, the loop decision, the tool duration and the prompt's block hashes,
   replayed through `kv_session_hint_study.py` with the real events instead of reconstructed sessions, plus a check
   that LMCache's lazy offload lets a dead request's store be dropped. One day of work, no CXL hardware, no change to the
   production prototype's memory policy.

## Gate update (charter §8)
Gate 2 (information available online): **FAIL for chat; PARTIAL for agent workloads** (41–48% with a realistic event;
criterion 50%). The remaining uncertainty for agents is whether the reconstructed sessions overstate the loop signal —
the verification in item 7 settles it. No further feature search.

## Verdict
The application does know something the memory manager does not, but only in agent runtimes: the loop's own
continue/end decision, available at the end of each LLM call, hash-exact for the request's context, worth about 40–48%
of the block-level ceiling on the agent trace. The scheduler's queue knows the exact next reads but only 0.2 s ahead on
a healthy server, which is worth nothing against a two-minute reuse gap. Chat applications have no early signal at all.
RQ1-B is therefore answered "no" for chat and "partly, by interface rather than prediction" for agents.
