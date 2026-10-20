# 2026-10-18 — RQ1-B: historical reuse-pattern learning and continually updated online prediction — can future KV reuse be learned from past requests, and does that improve cache decisions?

**STATUS: ACTIVE (2026-10-18).** Evidence types: **OFFLINE TRACE ANALYSIS** (characterization of the Mooncake
conversation / tool-agent traces, the SYNTHETIC Mooncake trace, and two REAL agent runtime traces of the earlier rounds),
**OFFLINE PREDICTION STUDY** (strictly chronological, prequential; predictions use only past accesses, labels resolve
later), **TRACE-DRIVEN REPLAY** (the capacity simulator with prefix-aware scoring and LMCache's eviction order, learned
policies that use only the cache's own history as labels), **ORACLE** (Belady with bypass). No runtime measurement in
this round. Previous RQ1 rounds: `2026-10-17-kv-reuse-oracle-study.md` (Gate 1; creation-time features), `2026-10-17-kv-session-hint-study.md`,
`2026-10-17-rq1b-application-reuse-signals.md`, `2026-10-17-rq1b-agent-runtime-validation.md`, `2026-10-17-rq1b-reuse-horizon.md`,
`2026-10-18-rq1-misscost-feasibility.md`. Raw: `experimental_results/2026-10-18-rq1b-history-learning/` (`*-history.json`,
`*-predict.json`, `*-replay.csv`, `hits/*.bin`, figures). Code: `scripts/kv_history_characterize.py`,
`scripts/kv_online_predict.py`, `scripts/kv_agent_replay.py` (learned policies `pop`, `lhd`, `olr`, `cond`, `--admit-th`,
`--dump-hits`), `scripts/kv_hits_compare.py`.

## What the traces contain (Task A, first part)
| trace | requests / span | fields | sessions / tenants / app ids | block ids | shared-prefix structure |
|---|---|---|---|---|---|
| Mooncake conversation | 12,031 / 3,537 s | timestamp (ms, quantized to 3 s), input_length, output_length, hash_ids (512-token blocks, globally prefix-chained) | none | 182,790 | one root: every request starts with the same block 0 (one system prompt); 7,373 distinct depth-2 prefixes, none with ≥ 100 new blocks per half |
| Mooncake tool agent | 23,608 / 3,537 s | same | none | 183,300 | 4 roots: block 0 (10,938 requests), 46 (9,203), 74 (3,449), one more; 6,554 depth-2 prefixes |
| Mooncake synthetic (SYNTHETIC) | 3,993 / 1,022 s | same | none | 43,924 | 2,211 roots (no shared system prompt) |
| real agent, short tools (`k16-l1g`) | 1,564 calls / 400 tasks / 175 s | lookup time, 256-token chunk hashes, task id, continue / end decision | task id (REAL) | 842 | one root (the agent's system prompt + tools), 16 depth-4 prefixes |
| real agent, long tools + churn (`lt-k16-l1g-bg2`) | 531 calls / 200 tasks / 139 s | same | task id | 163 | one root |
| public Exgentic/agent-llm-traces | 1,781 sessions | timestamps and token counts only | session id | **none** | not usable for reuse prediction |

Nothing in the public KV traces identifies a session, tenant, application or request category; the only online
context is what the request itself carries (its prefix chain, length, position of each block, how much of it already
existed) and the time. The real agent traces carry the task id (and the continue / end decision) but are too small for
learning beyond what the earlier rounds measured.

## Task A — historical reuse patterns (Deliverable 1; `kv_history_characterize.py`, `*-history.json`, fig-history-*)
### A1. Cross-request prefix reuse
- **Sharing.** 24% (conversation) / 22% (tool agent) / 42% (synthetic) of blocks are ever reused. Of the reused blocks,
  58% / 55% are read by exactly one other request, and 3% / 3.5% by ten or more. Reuse is concentrated: the top 0.1% of
  blocks carry 15% (conversation) and **63%** (tool agent: the shared system prompts of the 4 roots) of all reuses, the
  top 10% carry 75% / 91%. 929 / 950 blocks are read by ≥ 10 requests over more than half the trace — the long-lived
  shared prefixes (system prompts and their first turns). Everything else is low-frequency: most reuses are the next
  turn of the same conversation.
- **Prefix groups.** The conversation trace has one root and no large sub-group (7,373 depth-2 prefixes, none with 100
  new blocks per half): there is no learnable "application" structure, only individual conversations. The tool-agent
  trace has 3 large roots with stable, very different new-block reuse rates: root 0: 0.27 → 0.22 (halves), root 46:
  0.02 → 0.02, root 74: 0.02 → 0.00 (Spearman between halves 0.5 over 3 roots); the two low-reuse roots hold 13% of
  all new blocks. A rule learned on the first half (bypass roots with rate < 0.05) would skip 13% of the second half's
  new blocks and lose 1.2% of its reused blocks — a real, small, learnable conditional pattern.
- **Reappearing after eviction (A4 below):** of the blocks LRU evicts at 200 GiB and that are then needed again, 52–55%
  had already been reused at least once before the eviction (the history "knew" them); 45–48% were first-timers.

### A2. Temporal patterns
- **Inter-reuse intervals:** conversation p10 / p50 / p90 = 0 / 114 / 519 s; tool agent 0 / 0 / 243 s (half of its
  reuses are same-timestamp fan-outs of parallel sub-requests); synthetic 5 / 59 / 282 s. Per block (≥ 4 uses) the
  intervals are semi-regular: coefficient of variation p50 = 0.54 / 0.55 / 0.83 — more regular than a memoryless
  process (CV 1) but not periodic. The traces are one-hour samples: no time-of-day effect can be measured.
- **Burstiness:** request arrivals have a Fano factor of 2.1 (conversation) / 3.6 (tool agent) per 10 s — bursty, partly
  an artifact of the 3-s timestamp quantization.
- **Popularity does not persist:** between consecutive 5-minute windows the Spearman correlation of block popularity is
  −0.30 (the popular blocks of one window are absent from the next); only 9% (conversation) / 18% (tool agent) of a
  window's top-100 blocks are in the next window's top-100, and 34% / 28% of them are never used again after their
  window. In the conversation trace the top-100 retention drops from 45% in the first 20 minutes to ≈ 0 afterwards
  (fig-history-conversation): the hot set changes completely — a phase change inside the hour.
- **Hot-to-cold is the rule:** a prefix is hot while its conversation is active (minutes) and then dies; there are no
  cold-to-hot transitions of any size except the long-lived system prompts, which never cool.

### A3. Conditional reuse of NEW blocks (what a request reveals at creation time)
| context (online-available) | conversation: rate by cell (base 0.242) | tool agent (base 0.215) | synthetic (base 0.416) |
|---|---|---|---|
| root (first block) | one root | 0.24 / 0.02 / 0.01 (lift 1.13 overall) | one request per root |
| position in the request (blocks 0–7 / 8–15 / 16–31 / 32–63 / 64+) | 0.30 / 0.25 / 0.22 / 0.21 / 0.21 | 0.27 / 0.18 / 0.22 / 0.22 / 0.20 | 0.33 / 0.38 / 0.37 / 0.36 / 0.53 |
| continuation depth (old blocks 0 / 1–7 / 8–31 / 32+) | 0.25 / 0.10 / 0.09 / 0.17 | 0.25 / 0.05 / 0.10 / 0.18 | 0.43 / 0.20 / – / 0.05 |
| request length (per 8k tokens) | 0.21–0.29 (max lift 1.24) | 0.15–0.29 (1.36) | 0.12–0.66 (1.58) |
| time since the previous turn | all "fresh" (the hash chain does not identify the previous turn) | same | same |

The best online context lifts the reuse probability of a new block by at most 1.25× (conversation) / 1.36× (tool
agent); the one strong conditional (continuations' new blocks reuse at 0.05–0.10 vs 0.25 for fresh requests) says
which blocks are *less* likely to be reused. Within-group predictability is not better than global: the groups that
exist (roots) separate a 2% class from a 24% class in the tool-agent trace and nothing in the conversation trace.

### A4. Reuse distance and cache pressure (LRU at 100 / 200 / 400 GiB, 8B blocks)
| trace | capacity | LRU reuse-hit | reuses missed (premature evictions) | of which the block had ≥ 1 past reuse | last access → eviction (p50) | eviction → missed reuse (p50) |
|---|---|---|---|---|---|---|
| conversation | 100 / 200 / 400 GiB | 0.130 / 0.179 / 0.382 | 87% / 82% / 62% | 53% / 52% / 51% | 18 / 39 / 81 s | 117 / 108 / 132 s |
| tool agent | 100 / 200 / 400 GiB | 0.621 / 0.645 / 0.743 | 38% / 36% / 26% | 55% / 54% / 55% | 21 / 39 / 84 s | 108 / 96 / 108 s |
| synthetic | 100 / 200 / 400 GiB | 0.185 / 0.297 / 0.494 | 82% / 70% / 51% | 73% / 70% / 65% | 13 / 28 / 62 s | 74 / 79 / 92 s |

At 200 GiB LRU keeps a block for 39 s after its last use; the missed reuse comes 108 s after the eviction, i.e. the
block would have had to stay 3.5× longer. Half of the prematurely evicted blocks had reuse history — the information
that an "observed-block" predictor can use; the other half were first-timers whose only context is the request.

## Tasks B, C, D, E — what history predicts, with continually updated online models (Deliverables 2 and 3; `kv_online_predict.py`, `*-predict.json`, fig-predict-*)
**Protocol (Task D).** One pass over the trace in time order. At every access the models score the block with their
state at that instant; the access then updates the state. A prediction's label ("used again within H seconds")
resolves when the block is used again before t + H (the models learn from it then) or when t + H passes without a
use (processed as the clock advances). The first 20% of the trace is the only period on which decay constants and
thresholds were chosen; the remaining 80% is scored in five chronological fifths. Nothing is initialised from
whole-trace statistics; unseen contexts fall back to the running prior. Two problems are kept apart: **NEW** blocks at
their first access (admission) and **OBSERVED** blocks at a later access (retention). H = 60 s (≈ the LRU residence at
200 GiB) and 300 s.

**Models (Deliverable 2; all O(1) per access, state per block = count, last use, last interval, decayed popularity):**
`base` running prior; `root` per-root decayed rate (backoff to base below 50 samples); `ctx` per (root, position
bucket, continuation-depth bucket) decayed rate (backoff to root); `cnt` per past-use-count bucket; `cntrec` per
(count bucket, last-interval bucket); `interval` P(next interval ≤ H) from the block's own intervals (≥ 2) else the
root's online interval histogram; `pop` decayed popularity (τ = 300 s) mapped through an online rate table; `olr`
online logistic regression (SGD, lr 0.05, L2 10⁻⁴, 8–9 standardised features: log count, age, last and mean
interval, popularity, position, depth, prompt length, time since last use; lazy labels). Metrics: average precision
(AP = PR-AUC; random = base rate), precision at recall 0.5, calibration error (10 bins), AP per fifth.

### NEW blocks: not predictable from history (admission)
| trace, H | n | base rate | base | root | ctx | olr | best / random |
|---|---|---|---|---|---|---|---|
| conversation, 60 s | 141,570 | 0.037 | 0.035 | 0.035 | **0.045** | 0.037 | 1.2× |
| conversation, 300 s | 141,570 | 0.157 | 0.150 | 0.150 | **0.184** | 0.162 | 1.2× |
| tool agent, 60 s | 142,857 | 0.037 | 0.035 | 0.040 | **0.051** | 0.042 | 1.4× |
| tool agent, 300 s | 142,857 | 0.155 | 0.148 | 0.169 | **0.207** | 0.169 | 1.3× |
| synthetic, 300 s | 28,643 | 0.325 | 0.335 | 0.324 | 0.324 | **0.370** | 1.1× |

A new block's chance of being re-read within the residence time of a 200 GiB cache is 3.7%, and the best online
context raises the average precision to 4.5–5.1%; within 300 s the lift is 1.2–1.3× (the tool-agent roots and the
position / depth cells of A3). The per-fifth values move between 0.03 and 0.06 with no trend; the online logistic
model is badly calibrated (error 0.33–0.65) because its positives are rare and its features carry no signal. This
confirms the Phase 1 result with a continually updated model instead of a fitted one: **history does not tell which new
blocks will be reused.**

### OBSERVED blocks: strongly predictable (retention)
| trace, H | n | base rate | cnt | cntrec | interval | pop | olr | AP per fifth (pop) |
|---|---|---|---|---|---|---|---|---|
| conversation, 60 s | 89,181 | 0.200 | 0.604 | 0.749 | 0.703 | **0.746** | 0.723 | 0.78 / 0.70 / 0.80 / 0.75 / 0.72 |
| conversation, 300 s | 89,181 | 0.477 | 0.729 | 0.749 | 0.491 | **0.750** | 0.725 | 0.74 / 0.77 / 0.79 / 0.77 / 0.71 |
| tool agent, 60 s | 186,941 | 0.651 | 0.957 | **0.988** | 0.982 | 0.987 | 0.930 | 0.99 / 0.98 / 0.99 / 0.99 / 0.99 |
| tool agent, 300 s | 186,941 | 0.782 | 0.969 | 0.977 | 0.815 | **0.977** | 0.926 | 0.98 / 0.98 / 0.98 / 0.98 / 0.97 |
| synthetic, 60 s | 75,742 | 0.459 | 0.604 | 0.587 | 0.528 | 0.611 | 0.547 | base 0.635: history is worse than the prior |

Once a block has been used twice, its past says a lot: count × last-interval tables and decayed popularity reach
AP 0.75 against a 0.20 base rate on the conversation trace (precision 0.99–1.00 at recall 0.5: the top half of the
true positives can be identified almost without error), 0.99 on the tool-agent trace, stably across the five fifths;
calibration errors are 0.02–0.04 (the tables) against 0.17–0.31 (logistic model, prior). The signal is simple: blocks
that came back quickly and often come back again; a long last interval means the conversation has ended. The
synthetic trace is the exception (its reuse is generated without per-block memory).

### Next-use time (observed blocks with ≥ 2 past intervals, else the root's interval median)
conversation: median |log(predicted / actual)| = 0.49, 59% within 2×, 87% within 5× (median predicted 66 s vs actual
96 s); tool agent: 73% within 2× (dominated by same-timestamp fan-outs); synthetic: 28% within 2×. The next-use time of
an observed block is predictable to within a factor of two for most blocks — enough to say "before" or "after" a
residence time of 40 s, which is what retention needs.

### Drift and unseen contexts
No trend across the fifths for the observed-block models; the conversation trace's hot set changes completely after
20 minutes (A2) and the models follow because they are per-block and decayed. Unseen roots exist only in the synthetic
trace (one root per request; AP there equals the base rate). The whole-trace priors used by the earlier rounds would
not have changed any of these numbers (the tables converge within the first fifth).

### Related methods (literature, for orientation; none run here)
The observed-block result is the classical one: frequency- and recency-conditioned reuse probability is what LRFU
(Lee et al. 2001), GDSF (Cherkasova 1998), ARC (Megiddo & Modha, FAST'03) and LHD (Beckmann, Chen & Cidon, NSDI'18:
hit density learned per class from the cache's own age / hit statistics) exploit; LeCaR / CACHEUS (Vietri et al.
HotStorage'18, Rodriguez et al. FAST'21) switch online between LRU and LFU experts; LRB (Song et al. NSDI'20) learns a
relaxed-Belady next-request distance with gradient boosting on recency / frequency deltas. Context-conditioned reuse
prediction is the CPU-cache line of Hawkeye (Jain & Lin, ISCA'16), Glider (Shi et al. MICRO'19) and Mockingjay
(Shah et al. ISCA'22), whose "context" is the program counter — the analogue here is the prefix root / request
context, which the traces show carries little. KV-specific systems — vLLM prefix caching, SGLang's RadixAttention
(Zheng et al. 2023), LMCache, Mooncake (Qin et al. FAST'25), CachedAttention / AttentionStore (Gao et al. ATC'24) — use
LRU over the prefix tree, session-aware offload and scheduler-aware prefetch; none learns admission.


<!-- F -->

## Task G — prefetch feasibility (Deliverable 5; analysis only)
- **Is there a lower copy?** In the studied configuration the host cache (DRAM + CXL) is the only tier below the GPU:
  an evicted block is gone and must be recomputed; "prefetching" it is admission or retention by another name. A
  DRAM ← CXL prefetch inside the host tier is the only real data movement a predictor could trigger, and the
  miss-cost round measured that loading from the CXL devdax costs the same as from DRAM at this scale (≤ 1/15 of the
  recompute per token, below the TTFT floor), so it would gain nothing measurable in TTFT. Only a deployment with an
  SSD or remote KV copy changes this, and none exists here.
- **Would there be time?** Yes: the missed reuses come 96–132 s (p50) after the eviction at 100–400 GiB, against 3–6 ms
  to move one 64 MiB block at 10–20 GB/s; a predictor that scores a block at its last access has 39 s (the residence)
  before the eviction and ~100 s before the reuse. Timing is never the constraint.
- **Would a predictor know what to fetch?** For observed blocks yes (AP 0.75–0.99 within 60–300 s, next-use time
  within 2× for 59–73%); for new blocks no. Prefetching the predicted observed blocks is exactly the retention
  decision evaluated in Task F; it would displace the same capacity.
- **Conclusion:** no prefetch opportunity exists beyond retention in this configuration; if a lower copy existed, the
  predictor side is ready (lead ≈ 100 s, precision ≈ 1 at recall 0.5) and the question would become bandwidth and
  write interference (RQ3), not information.


<!-- H -->
