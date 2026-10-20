# 2026-10-18 — RQ1-B: historical reuse-pattern learning and continually updated online prediction — can future KV reuse be learned from past requests, and does that improve cache decisions?

**STATUS: CLOSED 2026-10-20** (the round was interrupted by a cluster power loss on 2026-10-18; the tool-agent replays were rerun on 2026-10-20, everything else is from 2026-10-18). Evidence types: **OFFLINE TRACE ANALYSIS** (characterization of the Mooncake
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


## Task F — cache-level utility of learned online policies (Deliverable 4; TRACE-DRIVEN REPLAY, fig-history-policies, `*-replay.csv`, `hits/`)
Replay with `kv_agent_replay.py`: prefix-aware scoring (a chunk counts only while every earlier chunk of the request
hit), LMCache's tail-first order, same capacity / arrival order / warm-up (second half scored) / block size / data
availability for every policy. Learned policies use only the cache's own history: at every eviction the evicted block
is a negative sample of its class if it never hit since admission, and the first hit after admission is a positive
sample; the learned probability is used (a) as the retention priority among the least-recently-used window (cap/16
candidates) and (b), when `--admit-th` is set, to bypass admission of blocks whose class probability is below the
threshold (never the first block of a request). Classes: `pop` decayed popularity of the block (τ = 300 s), `lhd`
(root, position bucket, continuation-depth bucket) hit rate (LHD-like), `olr` online logistic regression on
creation-time features, `cond` per-root hit rate. Baselines: static split + LRU, global LRU, SLRU 1/3, LFU (decayed
popularity without decay), the agent continue signal where applicable, the block oracle. The admission threshold 0.15
was chosen on the agent traces and applied unchanged to the Mooncake traces (not tuned per trace).

### F1. Mooncake traces, 8B blocks (usable-prefix hit share | TB written in the scored half | share of the oracle's hit gain over LRU)
| trace, capacity | LRU | SLRU | LFU | pop | lhd | lhd + bypass | cond + bypass | olr + bypass | oracle |
|---|---|---|---|---|---|---|---|---|---|
| conversation 100 GiB | 0.130 / 18.4 | 0.147 / 18.2 / 4% | 0.133 / 1% | 0.142 / 3% | 0.130 / 0% | 0.116 / 2.7 / 12%† | 0.193 / 2.5 / 13% | 0.205 / 2.2 / 18% | 0.610 / 3.2 |
| conversation 200 GiB | 0.178 / 18.0 | 0.209 / 17.7 / 5% | 0.178 / 0% | 0.188 / 2% | 0.177 / 0% | **0.273 / 4.0 / 15%** | **0.274 / 5.2 / 16%** | 0.115 / 0.2 / −10% | 0.797 / 3.2 |
| conversation 400 GiB | 0.376 / 16.5 | 0.376 / 0% | 0.380 / 1% | 0.388 / 2% | 0.378 / 0% | 0.397 / 7.1 / 3% | 0.399 / 9.6 / 4% | 0.135 / −41% | 0.967 / 3.0 |
| tool agent 100 GiB | 0.624 / 18.0 | 0.631 / 3% | 0.625 / 1% | 0.630 / 3% | 0.623 / 0% | 0.647 / 3.3 / 13% | 0.653 / 3.2 / 13% | 0.649 / 1.9 / 14% | 0.851 / 3.1 |
| tool agent 200 GiB | 0.648 / 17.6 | 0.661 / 5% | 0.649 / 0% | 0.653 / 2% | 0.646 / 0% | **0.691 / 3.8 / 15%** | **0.689 / 6.1 / 14%** | 0.682 / 1.4 / 15% | 0.940 / 3.0 |
| tool agent 400 GiB | 0.748 / 16.1 | 0.748 / 0% | 0.749 / 1% | 0.753 / 2% | 0.748 / 0% | 0.763 / 7.3 / 6% | 0.763 / 10.6 / 6% | 0.720 / −11% | 1.000 / 2.6 |
| synthetic 200 GiB (SYNTHETIC) | 0.348 / 6.6 | 0.365 / 5% | – | 0.346 / 0% | 0.343 / −1% | 0.301 / 5.0 / −9% | 0.272 / 4.2 / −21% | 0.310 / −11% | 0.696 / 2.0 |

(† at 100 GiB the lhd bypass over-fires on the conversation trace: hit share below LRU although the hit gain over LRU
is positive — the share metric counts usable hits of *all* reuses while bypassed blocks' later reads become misses.)

- **Retention-only learning adds nothing over LRU / SLRU** (pop +2–3%, lhd / olr / cond 0%, LFU 0–1%, SLRU 4–5%),
  on both real traces at every capacity: the observed-block predictions of Task B are accurate but concern blocks
  LRU already keeps; the blocks LRU loses are needed 108 s after an eviction that happens 39 s after their last use,
  and no ranking among the cached blocks can keep them 3.5× longer while the cache fills with new blocks.
- **Learned admission is the first online method that clearly beats SLRU on the real traces:** at 200 GiB the
  class-feedback policies raise the usable-prefix hit share from 0.178 (LRU) / 0.209 (SLRU) to 0.273–0.274 on the
  conversation trace and from 0.648 / 0.661 to 0.689–0.691 on the tool-agent trace — **14–16% of the oracle's hit
  gain, +4,700 … +5,100 net hits in the scored half** (7,000–7,400 LRU misses avoided, 1,900–2,300 new misses) — while
  writing **4–6 TB instead of 18 TB (−66 … −78%)**. At 100 GiB 12–14%, at 400 GiB 3–6%; the online logistic version is
  unstable (badly calibrated: −10 … −41% at 200–400 GiB on the conversation trace).
- **The synthetic trace is hurt (−9 … −38%)**: its reuse is not class-structured, so a fixed bypass threshold removes
  reused blocks. A deployment would have to confirm the class rates on its first minutes before enabling the bypass;
  this chronological check was not automated here (the threshold is one hand-set value for all traces).

### F2. Which misses the learning avoids (conversation, 200 GiB, lhd + bypass vs LRU; `kv_hits_explain.py`)
| accesses by | LRU misses avoided (share of the class's accesses) | new misses introduced |
|---|---|---|
| block position 0–7 / 8–31 / 32+ in the request | 7,141 (18.1%) / 0 / 0 | 0 / 1,638 (2.9%) / 487 (1.2%) |
| request: fresh (< 8 old blocks) / continuation (≥ 8) | 1,449 (1.8%) / 5,692 (10.4%) | 0 / 2,125 (3.9%) |
| block's past uses at the access: new / 1 / 2–4 / 5+ | 0 / 3,198 (15.4%) / 2,517 (15.7%) / 1,426 (8.9%) | 0 / 891 / 665 / 569 |
| block age: < 60 s / 60–300 s / > 300 s | 620 (0.7%) / 3,943 (24.1%) / 2,578 (7.8%) | 986 / 414 / 725 |

The mechanism is one rule the feedback discovers within the first minutes: **new blocks deep in a continuing
conversation (position ≥ 8 of a request with ≥ 8 old blocks) almost never hit before they are evicted**, so the
policy stops storing them — the A3 cell "continuation depth 1–31: reuse 0.05–0.10" turned into an admission decision
by the cache's own labels. Not writing them removes three quarters of the write traffic and roughly triples the
residence of what remains, so the *leading* blocks of a conversation — the ones its next turn re-reads first — are
still there 108 s later (avoided hits: positions 0–7, age 60–300 s, 1–4 past uses). The cost is the 5–10% of deep
continuation blocks that would have been reused (new misses at positions 8+). The tool-agent trace shows the same
pattern (avoided hits 8.3% of position 0–7 accesses, introduced 2.2% of positions 8–31). It is the oracle's lever —
not storing blocks that will not be read — applied to the one class that history can identify; the oracle, bypassing
76% of blocks with perfect knowledge, reaches 0.797 where the rule reaches 0.274, because the rule cannot tell which
of the fresh requests' blocks (base rate 24%) will have a next turn.

### F3. Real agent traces (from the Reuse Horizon round's traces; `ag-*-replay.csv`)
With one root and short contexts the class feedback degenerates into "admit the first ~6 chunks of a request", which
on the real-tool trace with churn equals the structure of the workload (late chunks are the final call's tool
outputs): `cond` + bypass recovers 85–88% of the oracle's gain at C / W_live = 1.3–1.7 (0.987–0.989 vs LRU
0.904–0.930, continue signal 0.981–0.984) with a third of the writes; `lhd` + bypass 56–60%; on the short-tool trace
all learned policies are within 0–16% of LRU. Retention-only learning: 9–38% (`lhd`, `cond`) at C < 1.5 W_live, 0
above.

### F4. Overheads
Per cached block: use count, last-use time, last interval, decayed popularity (32 bytes against a 64 MiB block);
class tables: roots × 4 position buckets × 3 depth buckets counters; per access O(1) updates; per eviction a scan of
at most cap/16 least-recent candidates (≤ 200 at 3,200 blocks); no training phase, labels are the cache's own hits and
evictions. The online logistic model adds 8 standardised features and one SGD step per label.


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


## Task H — synthesis (Deliverable 6: the comprehensive RQ1 picture)
1. **Do historical patterns hold unused future-reuse information?** Partly. The reuse of blocks that have been used
   before is highly predictable from their own history (AP 0.75 / 0.99 against base rates 0.20 / 0.65, stable over
   time), but LRU and SLRU already keep those blocks for as long as the capacity allows; the information that was
   unused is the *negative* one — which classes of new blocks the cache never gets to use again — and it is learnable
   from the cache's own feedback within minutes.
2. **What can be learned stably?** Per-block reuse likelihood from count, last interval and decayed popularity; the
   next-use time within a factor of two; per-class (root, position, continuation depth) hit-before-eviction rates;
   the tool-agent trace's per-root reuse rates. Not learnable: whether a *fresh* request's blocks will have a next
   turn (AP within 1.3× of the 4–16% base rate), and the next hot prefixes (popularity does not persist between
   5-minute windows).
3. **What can be updated online?** All of the above, with O(1) per access and labels that arrive with the next use or
   at eviction; no model needed a training phase, and the tables converge inside the first fifth of the trace.
4. **Which granularity?** Block-level history for retention relevance; request-class level (position × continuation
   depth × root) for admission; session level only where the application supplies it (agents). Application / tenant
   level could not be tested: the public traces carry no such ids.
5. **Which methods improved the cache, not just the metrics?** Only learned admission (class-feedback bypass): +4.7k
   … +5.1k hits and −66 … −78% writes at 200 GiB on both real traces (14–16% of the oracle's gain). Retention ranking
   by learned probabilities, decayed popularity, LFU and the online logistic model changed nothing or hurt.
6. **Does history improve admission of new blocks?** Yes, by class exclusion rather than by prediction: it removes the
   deep blocks of continuations (and, on the tool-agent trace, the two low-reuse roots) and cannot identify the reused
   minority of fresh requests.
7. **Is history better suited to retention of existing prefixes?** As a prediction, yes; as a cache decision, no:
   what it predicts well, LRU keeps anyway, and what LRU loses it cannot bring back without more capacity.
8. **Next-use time / distance?** Predictable within 2× for 59–73% of observed blocks (own intervals, root interval
   histogram); useless for new blocks. Sufficient to say "before / after the residence time".
9. **Which workload regimes suit historical learning?** Multi-turn conversation and tool-agent serving where a
   stable minority of request classes produces blocks that are never re-read before eviction (continuation tails, low-
   reuse applications); not synthetic / memoryless reuse, not short-context agents, not caches far above the live
   working set (the gain falls to 3–6% at 400 GiB).
10. **What does it give the unified DRAM/CXL manager?** A cheap, self-labelling admission filter that removes most of
    the never-reused writes (−66 … −78% of host-memory writes at 200 GiB) and a retention-relevance score for observed
    blocks; together with the chain structure (keep heads, evict tails) and the agent lifecycle events this is the
    value information RQ2 can rely on. Its hit-rate value is 14–16% of the oracle's gain; its write-side value is of
    the order of the oracle's own (−72% vs −82%).

### RQ1 after all rounds (updates `decision-2026-10-17.md`)
- Gate 1 (value): PASS. Gate 2 (online predictability, ≥ 50% of the oracle's gain): **still PARTIAL** — the best online
  method on the real traces at 200 GiB recovers 14–16% of the hit gain; the agent continue signal reaches 50–90% only
  inside the capacity-pressure band. The threshold is not changed.
- What is new: a history-based online admission filter is the first method that beats SLRU on both real traces, with a
  write reduction close to the oracle's; its benefit is robust to capacity (12–16% at 100–200 GiB) and to the
  chronological protocol, and negative only on the synthetic trace. It is a practical result, not a predictability
  result: it learns what not to store, not what will be reused.
- What is still missing: any signal that separates the 24% of fresh-request blocks that will be re-read from the 76%
  that will not — not in history, not in the request, only in the application (agents) — and any persistence of
  popularity that would let the cache anticipate the next hot prefixes.

