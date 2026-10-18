# 2026-10-18 — RQ1: future data value and miss-cost feasibility — can realistically obtainable reuse and miss-cost information support better cache-management decisions?

**STATUS: CLOSED 2026-10-18.** Evidence types: **SOURCE INSPECTION** (vLLM 0.31 / LMCache 0.5.5: how a prefix hit
is computed and in which order chunks are evicted), **DIRECTLY MEASURED** (TTFT microbenchmark on c28's 4060 Ti,
Qwen2.5-3B-Instruct-AWQ, LMCache L1 in DRAM and on the CXL devdax), **TRACE-BASED MODELLED COST** (the measured cost
model applied in replays of the real agent traces and of the Mooncake traces at 200 GiB), **ANALYTICAL ESTIMATE** where
marked. Previous RQ1 rounds: `2026-10-17-kv-reuse-oracle-study.md`, `2026-10-17-kv-session-hint-study.md`,
`2026-10-17-rq1b-application-reuse-signals.md`, `2026-10-17-rq1b-agent-runtime-validation.md`, `2026-10-17-rq1b-reuse-horizon.md`.
Raw: `experimental_results/2026-10-18-rq1-misscost/` (`real/<tag>-ttft.csv` microbenchmark, `mc-*-replay.csv` and
`*-replay.csv` replays, figures). Code: `benchmarks/lmcache/misscost_bench.py` + `misscost_run.py` (microbenchmark),
`scripts/kv_agent_replay.py` (prefix-aware scoring, `--order tail`, cost-aware policies, TTFT model, `--mooncake`),
`scripts/kv_misscost_figs.py`.

## Task A — what "future data value" is for a KV block (Deliverable 1)
A KV block (an LMCache chunk of 256 tokens, a vLLM block of 16, a Mooncake hash block of 512) is useful to a future
request only as part of a **contiguous prefix**: both vLLM's prefix cache and LMCache's lookup return the longest
cached prefix of the prompt (LMCache: `fold_unfold_ranked` → `hit_length` = highest servable prefix bit + 1,
`lmcache/v1/multiprocess/modules/lookup.py`; vLLM: block-hash chain). Everything after the first missing block is
recomputed even if it is cached. Therefore:

- **Retention benefit of a block** = P(a future request re-reads this prefix up to or beyond this block) ×
  (recompute cost of the tokens from this block to the end of the re-read prefix − their load cost from the tier that
  holds them). The benefit is **request-level and prefix-dependent**, not per-block additive: losing block i of a cached
  prefix of n blocks destroys the value of blocks i … n−1 for every request that would have used them.
- **Middle blocks have no independent value**: a block whose predecessor is gone is dead weight until it is rewritten.
- **Shared benefit**: a block near the head of a prefix shared by many requests (system prompt, tool schemas) carries
  the recompute of every suffix behind it, for every sharer; this is why frequency (SLRU) captures part of the value.
- **Per-byte**: all blocks of one model have the same size, so benefit per byte = benefit per block; across tiers the
  byte is the same, the avoided cost differs by the load cost of the tier (measured in Task B).
- **Time**: the expected next-use time decides whether a cache of residence T_res will still hold the block (Reuse
  Horizon round): value is realised only if next use < T_res; a time window can be added as a factor, but the previous
  rounds showed the next-use time is not predictable online except for agent loops (lead = tool time).

Answers to the six questions:
1. **Do blocks differ in recompute cost?** Per token, within one model and hardware, only through position: prefill cost
   per token grows with the number of tokens before it (attention), measured in Task B (r(p) = r0 + r1·p). Across
   models it differs by orders of magnitude, but the manager serves one model per cache.
2. **Does prefix length affect the miss penalty?** Yes, twice: the penalty is the recompute of the whole missing suffix
   (length L − usable prefix), and per-token recompute grows with position.
3. **Per-block additive or prefix-dependent?** Prefix-dependent: the cost of a miss at block i is the recompute of blocks
   i … L/B of that request, so a single eviction at the head of a chain costs the whole chain; evictions at the tail
   cost one block. Only tail evictions are "additive".
4. **Do retained middle blocks have value?** No, unless and until the head is restored (a request that recomputes the
   prefix re-stores it, so the middle blocks become live again — the value is then in avoided writes, not reads).
5. **Do several blocks share one benefit?** Yes: a suffix of n blocks saves one contiguous recompute; it is paid for
   once, by whichever block is lost first.
6. **Can value be estimated at admission / eviction?** The structural part (position in the request, length of the
   cached chain behind a block, prompt length, model) is known from the request and the cache's own state. The
   probabilistic part (whether, when and how far a future request re-reads the prefix) is the reuse information of the
   previous rounds — agent continue events for agents, nothing for chat.

**What this already implies for the retention order:** evict from the tail of a cached chain, never from its head.
vLLM frees a request's GPU blocks in reverse order so that tail blocks are evicted first; LMCache 0.5.5's L1 LRU
touches a request's chunks in reverse (`for key in reversed(keys): self._order.move_to_end(key)`,
`lmcache/v1/distributed/eviction_policy/lru.py`), so the head chunk is the most recently used and the tail is evicted
first. Both production systems therefore already act on the prefix-dependence of the miss cost without any future
information. The replays of the earlier rounds scored chunk hits individually and ordered a request's chunks head-first;
Task D re-scores them prefix-aware with the real tail-first order.

## Task B — miss-cost characterization (Deliverable 2; DIRECTLY MEASURED unless marked)
**Setup.** `benchmarks/lmcache/misscost_run.py` + `misscost_bench.py`: Qwen2.5-3B-Instruct-AWQ on the 4060 Ti, vLLM 0.31
with its GPU KV cache limited to 16k tokens, LMCache 0.5.5 L1 of 4 GB in DRAM (`dram3b`) or on the CXL devdax
`/dev/dax1.0` (`dax3b`); streaming completions with pseudo-random token prompts of L = 1024 / 2048 / 4096 / 7680 tokens,
3 repetitions, first-token time at the client. Cases: cold (nothing cached), the same prompt again (vLLM GPU prefix
cache), the same prompt after 32k tokens of other prompts flushed the GPU cache (served from LMCache L1), a prompt
with 16 tokens changed at position f·L (hole: the suffix is cached but unusable), a fresh prompt sharing the first f·L
tokens (clean prefix), and four cold prompts at once. Raw: `real/dram3b-ttft.csv`, `real/dax3b-ttft.csv`; fit and figure:
`scripts/kv_misscost_figs.py` → `misscost-summary.json`, fig-misscost-ttft.

| quantity (3B-AWQ, 4060 Ti, 1 request) | DRAM L1 | CXL devdax L1 |
|---|---|---|
| cold TTFT at 1k / 2k / 4k / 7.7k tokens | 154 / 309 / 649 / 1324 ms | 155 / 310 / 650 / 1329 ms |
| recompute per token, fitted r(p) = r0 + r1·p | r0 = 0.134 ms, r1 = 9.4 ns/token² (+7% per 1k tokens of position; 1.54× at 7.7k) | same |
| TTFT with the whole prompt in vLLM's GPU cache (floor) | 85–108 ms | 57–135 ms |
| TTFT with the whole prompt in LMCache L1 (7.7k tokens = 277 MB) | 79–121 ms | 58–67 ms |
| load cost per token from L1 (TTFT above the floor) | < 0.01 ms (within noise) | < 0.01 ms (within noise) |
| recompute / load ratio | ≥ 15× (one request), ≥ 50× (four at once) | same |
| hole at f = 0.25 / 0.5 / 0.75 of 4096 tokens (model: 508 / 367 / 226) | 591 / 390 / 216 ms | 552 / 375 / 219 ms |
| hole at f = 0.25 / 0.5 / 0.75 of 7680 tokens (model: 1019 / 713 / 408) | 1161 / 788 / 2580† ms | 1101 / 757 / 444 ms |
| four cold prompts at once, per-request TTFT at 1k … 7.7k | 462 / 940 / 1974 / 4059 ms (3.1× one request) | 609 / 1249 / 1991 / 4081 ms |

† store/evict stall: with the L1 at capacity the 0.75-hit case at 7680 tokens took 2.6 s in the DRAM run (3 of 3
repetitions) — the eviction in the store path delayed the load; not reproduced in the CXL run. The clean-prefix cases
(× in the figure) under-report the hit at f = 0.5 and 0.75 because the base prompt's middle chunks had been evicted
from the 4 GB L1 by the 32k-token flushes between cases (each flush stores 1.2 GB); the hole cases, which follow a
fresh store, are the valid prefix-hit measurement (vLLM's `cached_tokens` confirms the usable length = f·L in every case).

Findings:
1. **Recompute is the miss cost; loading from either host tier is free at this scale.** 277 MB of KV come back from
   DRAM or from the CXL devdax in less time than the measurement floor (≥ 4 GB/s per request): the per-token load cost is
   ≤ 1/15 of the recompute cost for one request and ≤ 1/50 under contention. ANALYTICAL ESTIMATE for larger models:
   an 8B model has 2.5× the KV bytes per token (128 KB) and a 70B model 10× (320 KB); at a CXL pair's ~20 GB/s read
   rate a 70B token loads in 0.016 ms against a recompute of ~0.1–0.2 ms/token on an H100 at long contexts, so the ratio
   narrows to roughly 10×; the tier (DRAM or CXL) changes the miss cost of a block by at most that load term.
2. **Per-token recompute cost is nearly uniform, with a mild position dependence.** Within the measured range the cost
   per token rises 7% per 1k tokens of prefix (attention); extrapolated to 32k-token prompts (Mooncake) it would be
   3.2× the position-0 cost (ESTIMATE beyond the measured range). Under load (four prompts at once) all per-token costs
   scale together (3.2×). So the cost of a block differs by its position in a long prompt, not by anything else.
3. **The miss penalty is prefix-dependent and request-level, as predicted.** A hole at f·L costs exactly what a clean
   prefix of f·L would: (1−f) × cold + f × floor, on both the GPU prefix cache and LMCache. Blocks cached behind a hole
   are worth nothing; a scattered miss is as expensive as missing everything after it; only consecutive misses at the
   tail cost their own tokens.
4. **Batch size / contention multiplies the recompute cost (3.1× at four concurrent prefills) but not the load cost**, so
   the value of a usable prefix grows with load.
5. **What the existing real runs add (TRACE-BASED, noisy):** in the 2026-10-11 capacity-matched runs (conversation
   trace at 0.08×, 1.5B model) requests with > 90% of their prompt cached had TTFT p50 1.5–3.4 s against 2.7–14 s for
   < 30% cached at the same prompt lengths; the queueing of that experiment hides the per-token structure, which is why
   the microbenchmark was needed.


## Task C — which cost features are available online (Deliverable 3)
| feature | available at admission / eviction? | change to vLLM / LMCache | how it enters the miss-cost estimate | depends on an unknown future request? | error source |
|---|---|---|---|---|---|
| model identity / configuration (layers, KV heads, dtype → bytes per token; prefill speed) | yes (static) | none | sets r0, r1, l; one set per served model | no | hardware/batch variation of prefill speed (measured spread in Task B) |
| prompt length of the request that stored the block | yes at admission (`Request.num_prompt_tokens`); at eviction from the cache's chain length | none (LMCache already keeps the chain: chunk hashes are prefix-chained) | upper bound of the suffix lost with this block = tokens from its position to the end of its stored chain | the *future* request's prompt may be shorter (uses less of the chain) or longer (adds blocks) | over-estimate when the future request diverges earlier |
| block position in the request | yes (admission: index of the chunk; eviction: stored with the key) | none (LMCache's key order encodes it; a per-key position field is a one-line addition) | recompute per token at that position (r(p)); chain-damage order (tail first) | no | none |
| number of usable cached prefix blocks of a chain | yes at eviction (cache state), yes at lookup (`hit_length`) | none | which block is the tail (cheapest to lose) | no | none |
| historical recompute timing (prefill tokens/s) | yes online (vLLM metrics: prompt tokens and TTFT per request) | none (metrics exist) | r0, r1 per deployment, updated online | no | load-dependent (batching, contention): Task B measured 1 vs 4 concurrent prompts |
| existing KV transfer cost (LMCache load bandwidth) | yes online (LMCache `MP_RETRIEVE_START/END` events: bytes and time) | none | l per tier (DRAM vs CXL) | no | contention on the host memory path |
| which future request will use the chain, and how far | **no** for chat; agent runtimes know "the next call re-reads the whole context" (continue event) | the lifecycle channel of the earlier rounds | P(reuse) and the used suffix length | yes — this is the reuse information | the reuse-prediction problem of the earlier rounds |

So every term of the cost side is available online without future information, and the two production systems already
use the dominant one (tail-first eviction). What remains unknown is the reuse side.

## Task D — value-aware retention (Deliverable 4; TRACE-BASED MODELLED COST)
Replays with `scripts/kv_agent_replay.py` using the measured cost model (r0 = 0.134 ms/token, r1 = 9.4 ns/token², l =
0.005 ms/token, the upper bound of the load cost), **prefix-aware scoring** (a chunk counts only while every earlier
chunk of the request hit; the modelled TTFT of a request = floor + recompute of the unusable suffix at the
position-dependent rate + load of the usable prefix) and LMCache's real eviction order (`--order tail`: a request's
tail chunks are evicted before its head). Policies: global LRU, static split + LRU, SLRU 1/3, session TTL 30 s, the
real lifecycle signal (continue), cost-aware retention (`cost`: among the few least-recently-used candidates evict the
one whose contiguous cached chain is cheapest to recompute — chain length × position-dependent rate, minus the load),
reuse + cost (`slru+cost`, `event_cont+cost`), block oracle. Same capacities, arrival order, warm-up (second half
scored), chunk size, data-availability and scoring for all. Sensitivity: the cost estimate perturbed by ±50% uniform
noise. Traces: the real agent traces of the previous round (real tools with steady background churn, 16 and 8 agents;
short tools, 16 agents) and the Mooncake conversation / tool-agent traces at the 200 GiB setting of Phase 1 (8B model,
512-token blocks of 64 MiB).

### D1. What a cost-only policy does (negative result, mechanism)
The first version of `cost` ranked all resident chunks by chain cost: it evicted the chunks of the shared system prompt
(short chains at low positions, i.e. the cheapest) on every eviction, and because they head every request's prefix,
the usable hit share fell to **0.000** at every capacity (fig / `ag-*` logs of the first run). A per-chunk cost that is
not weighted by reuse likelihood is actively harmful under prefix semantics: the cheapest chunk to recompute is often
the one everybody reads. The policy kept below therefore uses the cost only to break ties among the 4 … cap/16 least
recently used chunks (recency stays the reuse estimate), which is the most a runtime could justify.

### D2. Agent traces (prefix-aware, tail order; usable-prefix hit share | modelled mean TTFT | share of the oracle's TTFT gain over LRU)
| trace, capacity (C / W_live) | LRU | SLRU | continue | cost | SLRU + cost | continue + cost | oracle |
|---|---|---|---|---|---|---|---|
| real tools, 16 agents, real churn: 24 chunks (1.3) | 0.904 / 33 ms | 0.954 / 26 ms / 52% | 0.981 / 22 ms / 81% | 0.901 / 34 ms / −3% | 0.954 / 26 ms / 52% | 0.977 / 22 ms / 76% | 0.999 / 19 ms |
| same, 32 chunks (1.7) | 0.930 / 30 ms | 0.960 / 25 ms / 42% | 0.984 / 21 ms / 77% | 0.909 / 33 ms / −28% | 0.959 / 25 ms / 40% | 0.984 / 21 ms / 77% | 1.000 / 19 ms |
| same, 48 chunks (2.5) | 0.987 / 21 ms | 0.972 / 23 ms / −122% | 0.996 / 19 ms / 72% | 0.981 / 22 ms / −50% | 0.966 / 24 ms / −172% | 0.994 / 20 ms / 50% | 1.000 / 19 ms |
| same, 96 chunks (5.0) | 0.995 / 20 ms | 0.995 / 20 ms / −1% | 0.996 / 19 ms / 34% | 0.995 / 20 ms / 0% | 0.996 / 19 ms / 17% | 0.996 / 19 ms / 34% | 1.000 / 19 ms |
| real tools, 8 agents, real churn: 24 chunks (1.9) | 0.924 / 30 ms | 0.971 / 23 ms / 61% | 0.992 / 20 ms / 90% | 0.921 / 30 ms / −5% | 0.971 / 23 ms / 61% | 0.992 / 20 ms / 90% | 0.999 / 18 ms |
| same, 32 chunks (2.5) | 0.955 / 25 ms | 0.973 / 23 ms / 38% | 0.994 / 19 ms / 86% | 0.934 / 28 ms / −45% | 0.973 / 23 ms / 38% | 0.992 / 20 ms / 82% | 1.000 / 18 ms |
| short tools, 16 agents: 24 chunks (0.4) | 0.874 / 46 ms | 0.875 / 46 ms / 1% | 0.921 / 38 ms / 55% | 0.848 / 50 ms / −30% | 0.854 / 50 ms / −24% | 0.907 / 41 ms / 39% | 0.959 / 32 ms |
| same, 32 chunks (0.6) | 0.931 / 37 ms | 0.927 / 37 ms / −11% | 0.952 / 33 ms / 53% | 0.917 / 39 ms / −36% | 0.907 / 41 ms / −64% | 0.947 / 34 ms / 41% | 0.970 / 30 ms |
| same, 96 chunks (1.7) | 0.968 / 31 ms | 0.967 / 31 ms / −3% | 0.968 / 31 ms / 0% | 0.968 / 31 ms / −1% | 0.967 / 31 ms / −4% | 0.968 / 31 ms / −1% | 0.995 / 26 ms |

(Full tables with all capacities, bytes written and cost per retained byte: `ag-*-replay.csv`; session TTL = LRU in
every row.) With the cost estimate perturbed by ±50% the numbers move by at most 2 points of the oracle's gain (the
`-noise0.5` files) — the policy is insensitive to the estimate because it hardly changes any decision.
- **Cost-aware retention never beats LRU** (−3 … −50% of the oracle's TTFT gain, 0% where nothing is at stake): once
  the eviction order is tail-first, every candidate costs one chunk of recompute and the position term (≤ 7% per 1k
  tokens) only shuffles which short prompt's tail goes first — a worse proxy for reuse than recency.
- **Reuse + cost adds nothing to reuse alone:** SLRU + cost = SLRU (±2%), continue + cost ≤ continue (−5 … 0 points).
- **Prefix-aware scoring does not change the previous rounds' conclusions**: on these traces the usable-prefix hit
  share equals the chunk hit share (misses are whole-context misses), and the head-first order of the earlier replays
  differs from LMCache's tail-first order by ≤ 2 points (`ag-*-head` vs `-tail`).
- **Absolute stakes:** the modelled TTFT gap between LRU and the oracle is 1–14 ms per request on these 1–2k-token
  prompts (3B model on the 4060 Ti); the continue signal takes 50–90% of it inside the pressure band, the cost
  information none.

### D3. Mooncake traces at the Phase 1 scale (8B model, 200 GiB = 3200 blocks of 64 MiB; also 100 and 400 GiB)
The most favourable case for cost-awareness: 32k-token prompts, where the extrapolated per-token recompute cost at the
end of a prompt is 3× that at its start. Prefix-aware scoring, tail order; TTFT modelled at the microbenchmark's rates
(the absolute seconds are the 3B / 4060 Ti rates applied to 8B-sized blocks, i.e. a relative scale, not a prediction).

| trace, capacity | LRU | SLRU | cost | SLRU + cost | oracle |
|---|---|---|---|---|---|
| conversation, 100 GiB | 0.130 / 5.2% of prompt tokens / 3.07 s | 0.147 / 5.8% / 3.04 s / 5% | 0.128 / 5.1% / 3.07 s / 0% | 0.145 / 5.8% / 3.05 s / 5% | 0.610 / 24.3% / 2.52 s |
| conversation, 200 GiB | 0.178 / 7.1% / 3.03 s | 0.209 / 8.3% / 2.98 s / 6% | 0.175 / 7.0% / 3.03 s / 0% | 0.209 / 8.3% / 2.98 s / 6% | 0.797 / 31.7% / 2.30 s |
| conversation, 400 GiB | 0.376 / 15.0% / 2.80 s | 0.376 / 15.0% / 2.82 s / −2% | 0.375 / 14.9% / 2.80 s / 0% | 0.374 / 14.9% / 2.81 s / −1% | 0.967 / 38.5% / 2.06 s |
| tool agent, 100 GiB | 0.624 / 36.9% / 1.45 s | 0.631 / 37.3% / 1.44 s / 4% | 0.623 / 36.8% / 1.45 s / 0% | 0.631 / 37.3% / 1.43 s / 5% | 0.851 / 50.4% / 1.16 s |
| tool agent, 200 GiB | 0.648 / 38.3% / 1.42 s | 0.661 / 39.1% / 1.40 s / 6% | 0.647 / 38.3% / 1.42 s / 0% | 0.661 / 39.1% / 1.40 s / 6% | 0.940 / 55.6% / 1.05 s |
| tool agent, 400 GiB | 0.748 / 44.3% / 1.30 s | 0.748 / 44.2% / 1.30 s / 0% | 0.747 / 44.2% / 1.30 s / 0% | 0.748 / 44.3% / 1.30 s / 0% | 1.000 / 59.2% / 0.97 s |

(usable-prefix hit share / usable share of prompt tokens / modelled mean TTFT / share of the oracle's TTFT gain over
LRU.) Chunk hits and usable-prefix hits coincide (0.174 vs 0.174 at 200 GiB: the misses are whole-prefix misses, so
the Phase 1 numbers stand as prefix-aware numbers), head-first and tail-first orders give the same result (the whole
request ages out together at a one-minute turnover), the cost information recovers 0% of the oracle's TTFT gain, and
SLRU + cost = SLRU (5–6%). The oracle's TTFT gain is large in absolute terms — 0.73 s per request on conversation
(24%), 0.37 s on the tool agent (26%) at 200 GiB — and comes entirely from knowing *which* prefixes will be re-read,
not from what they cost.



## Go / No-Go (Deliverable 5)
**Q1. Is miss-cost heterogeneity significant?** Structurally yes, otherwise no. The one large difference between
blocks is positional in the prefix-dependent sense — a head block carries the recompute of its whole cached chain, a
hole makes the suffix worthless (measured: TTFT with a hole at f·L equals TTFT with a clean prefix of f·L) — and
vLLM and LMCache already exploit it by evicting tails first. Beyond that, the recompute cost per token varies mildly
with position (+7% per 1k tokens, 1.5× at 8k, extrapolated 3× at 32k), and the load cost from DRAM or from the CXL
devdax is below the measurement floor (≤ 1/15 of the recompute for one request, ≤ 1/50 under contention; ESTIMATE
≤ 1/10 for a 70B model at the host read bandwidth). The tier a block lives in does not change its miss cost
measurably at this scale.
**Q2. Is the cost information available online?** Yes, all of it: model, position, chain length, prompt length,
measured prefill and load rates (Task C), without future information and without changes to vLLM or LMCache.
**Q3. Does cost-aware retention improve the application-relevant benefit?** No. With reuse likelihood kept primary
(recency), the cost tie-break recovers −50 … +2% of the oracle's TTFT gain on the agent traces and 0% on the Mooncake
traces at 100–400 GiB; a pure cost ranking is destructive (0 hits). The result is insensitive to ±50% error in the
cost estimate because the cost hardly changes any decision.
**Q4. Does it complement reuse information?** No. SLRU + cost = SLRU, continue + cost ≤ continue, on every trace and
capacity.
**Q5. Is it useful for the unified DRAM/CXL manager?** As an accounting rule, yes; as an information source, no. The
value of a block is P(reuse) × recompute of the chain behind it, and the manager must keep chains whole (demote or
evict tails, never heads) — a constraint RQ2 must preserve when it moves blocks between tiers. Because the load cost
from CXL is indistinguishable from DRAM's for reads at this scale, placement between the two tiers does not change the
miss cost of KV blocks; the placement decision is therefore free to follow capacity and the write-side constraints of
RQ3. What RQ2 cannot get from RQ1 is a better value estimate than recency / frequency plus the agent lifecycle events.

**Gate 2 stays PARTIAL** (unchanged threshold; this round adds no online reuse information). A miss-cost criterion
is not a substitute for the predictability gate and none is introduced.

### RQ1 final decision update (all rounds: oracle, prediction, session hint, application signals, agent runtime, reuse horizon, miss cost)
- **What data-value information can we actually obtain?** Exact prefix structure and position (the cost side,
  already used by the eviction order), recency and frequency of use (LRU / SLRU), the agent runtime's continue / end
  decisions (zero delay, block-exact), and the deployment's measured recompute and load rates. Nothing that predicts
  whether a chat prefix will be re-read, and nothing that makes one block's miss cost differ from another's beyond
  its chain position.
- **Which cache decisions can it improve?** Eviction order (tail-first; in production already); retention of live
  agent contexts when the cache turns over within about two reuse horizons and still holds the live set (continue
  signal: 77–93% of the oracle's gain, +3 … +7 points, Reuse Horizon round); write avoidance and release of dead
  occupancy by the end event (simulated −49% of writes, Agent Runtime round). Not: admission by predicted reuse, not:
  cost-weighted retention.
- **In which workload / capacity regimes?** Agents only, in the band W_live ≲ C ≲ P · H; at a 200 GiB tier serving
  ≤ 64 agents the cache sits in the LRU regime, where no online signal adds anything (ESTIMATE from the public trace).
- **Do these limits affect RQ2's feasibility?** They bound it: RQ2 cannot be a "better value estimation" contribution.
  Its joint decision has a fixed, cheap value model (recency / frequency, lifecycle events, chain structure) and a
  uniform miss cost per chunk; any joint benefit must come from the movement-cost side — where and when bytes are
  written (RQ3's write budget, CXL-first paths, tail-only demotion), not from which bytes are kept.
- **Is there evidence to enter the joint benefit analysis?** On the value side, no new evidence and none to expect;
  the value input is settled and small. If the joint analysis is entered, it is on the premise that movement cost and
  interference, not value estimation, decide the benefit — a different premise from the charter's H2 as written. That
  decision is not taken here.
- **Effect on the core hypothesis:** "jointly considering future data value and movement cost" retains the movement
  half; the value half reduces to information every cache already has (plus agent lifecycle events in a narrow band).

