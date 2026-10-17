# 2026-10-17 — Phase 1 of the charter: how much is future reuse information worth to a unified DRAM/CXL KV cache, and how much of it is predictable online?

**STATUS: CLOSED 2026-10-17.** Evidence type: **TRACE SIMULATION** (exact replay of the Mooncake traces; no hardware speed enters
the capacity-only model) plus **ESTIMATE** for the prefill-time proxy. Raw: `experimental_results/2026-10-17-kv-reuse-oracle-study/`
(`characterization-*.json`, `characterization-summary.txt`, `oracle-*.csv`, figures `fig-*.png/.svg`). Scripts:
`scripts/kv_reuse_characterization.py` (Step 1), `scripts/kv_oracle_study.py` (Steps 2–4), `scripts/kv_oracle_figs.py`.
Charter: `docs/research/CHARTER.md` — this experiment tests assumptions A1 and A2 and decides Gates 1 and 2.

## Question
RQ1: can future reuse information improve unified memory management, and is that information available online? Concretely:
at the 200 GiB host configuration of the earlier campaigns (DRAM 64 + CXL 136 GiB, Llama-3.1-8B blocks of 64 MiB), how
much better than the strongest capacity-matched baseline can an oracle that knows every future access do, where does its
gain come from, and how much of it do simple online rules that see only the past recover?

## Method
- Traces: Mooncake conversation (12,031 requests, 3,537 s, 288,500 block accesses, 182,790 blocks), tool agent (23,608 /
  3,537 s / 409,616 / 183,300), synthetic (3,993 / 1,022 s / 121,877 / 43,924); 512-token hash blocks, prefix order. The
  trace carries no session ids; conversations are reconstructed by prefix chains (the request that created the last old
  block of a request's prefix is its previous turn). Every request of the conversation trace and 46% of the tool-agent
  trace start with a shared system block.
- Protocol: requests are split in two halves by count; every policy runs over the whole trace (the first half is its
  warm-up) and is scored on the **second half only**; online predictors are fitted on the first half only (a block created
  in the first half counts as "reused" only if its next use also lies in the first half); oracles see the full future.
  Capacity-only model: stores complete at once; a block is a hit when it is resident at access time; no delayed stores
  (no hit can come from a block whose store would still be pending).
- Metrics (second half): reuse-hit share = hits / accesses to blocks seen before; overall hit rate = hits / all accesses;
  recomputed tokens = misses × 512; bytes written to DRAM / CXL; blocks bypassed (not stored); evictions with a future use
  (premature); useful occupancy (resident blocks with a future use, sampled); moves (GB); prefill-time proxy per request
  (EST: recomputed tokens / 7,300 tok/s + loads × 64 MiB / 9.5 GB/s, the real-run calibration).
- Policies: A `cxlfirst` (all new blocks to CXL, LRU over 136 GiB, DRAM unused); B `split` (32% of new blocks to DRAM by
  hash, LRU per tier); C `global_lru` (one LRU over 200 GiB; the new block takes the freed slot, no cross-tier relocation);
  D `reactive_mig` (CXL-first; a block hit in CXL moves to DRAM, DRAM's LRU block is dropped — kvemu2's `borrowmig` without
  its calm-DRAM condition, i.e. an upper bound of reactive migration); E `oracle_min` (Belady MIN with bypass over 200 GiB:
  a block without a future use is not stored; on a full cache the resident with the farthest next use is evicted unless the
  new block's next use is farther, then the new block is not stored); `oracle_h<H>` (E with next uses beyond H seconds
  counted as never); F `oracle_mig` (E's decisions plus tier assignment that keeps the soonest-reused blocks in DRAM — hits
  identical to E by construction, reports the move volume); online: `slru<p>` (segmented LRU over all slots: new blocks in
  probation, promoted to a protected segment of share p on their first hit, protected LRU demoted; logical segments, no
  data movement), `slru_tier<p>` (the same with the protected segment physically in DRAM: moves counted), `pred_admit`
  (a new block is stored only if P(reused | continuation depth × position), fitted on the first half, ≥ θ), `pred_evict`
  (classes by past reuse count, LRU inside, lowest class evicted first).
- Commands: `python3 scripts/kv_reuse_characterization.py`; `python3 scripts/kv_oracle_study.py` (default set, tag
  `8b-capacity`); `... --policies split,global_lru,reactive_mig,slru,slru_tier,pred_admit --slru-shares 0.33,0.5,0.67,0.8
  --theta 0.12 --horizons "" --tag 8b-capacity-online`; `... --dram 164 --cxl 348 --policies split,global_lru,slru,oracle_min
  --horizons "" --tag 8b-capacity-512GiB` (and 328/696 for 1 TiB); `... --model 70b --policies
  split,global_lru,reactive_mig,slru,oracle_min --horizons "" --tag 70b-capacity`; `python3 scripts/kv_oracle_figs.py`.
  Each run takes ~30 s on one core.

## Step 1 — reuse structure (fig-reuse-classes, fig-reuse-timing-distance, fig-creation-features, fig-chain-features, fig-resident-features-horizon)
| | conversation | tool agent | synthetic |
|---|---|---|---|
| blocks never reused (first-half-created blocks) | 75.8% (72.6%) | 78.5% (76.2%) | 58.4% (55.9%) |
| share of reuses on blocks used 2 / 3–4 / 5–9 / 10–99 / 100+ times | 24 / 29 / 19 / 17 / 11% | 10 / 13 / 9 / 8 / 61% | 4 / 21 / 54 / 21 / 0% |
| share of reuses on the top 0.1 / 1 / 10% of blocks | 15 / 32 / 75% | 63 / 71 / 91% | 1 / 10 / 50% |
| time between uses p10 / p50 / p90 | 0 / 114 / 519 s | 0 / 0 / 243 s | 5 / 59 / 282 s |
| creation → second use p50; lifetime of reused blocks p50 / p90 | 147 s; 276 / 1,317 s | 123 s; 234 / 963 s | 153 s; 448 / 808 s |
| reuses with next use within 60 / 300 / 900 s | 28 / 79 / 97% | 69 / 93 / 100% | 50 / 91 / 100% |
| LRU stack distance of a reuse p10 / p50 / p90 (8B); within 200 GiB | 3 / 522 / 1,974 GiB; 18.6% | 1 / 4 / 1,003 GiB; 64.8% | 44 / 392 / 1,274 GiB; 30.6% |
| P(used again \| past reuses 0 / 1 / 2 / 3–4 / 5+) | 24 / 42 / 50 / 61 / 88% | 22 / 45 / 52 / 61 / 98% | 42 / 84 / 78 / 74 / 72% |
| P(used again \| idle < 60 / 60–300 / 300–900 / > 900 s) | 33 / 18 / 4 / ≤ 2% | 31 / 15 / 2 / 0% | 55 / 33 / 4 / — |

What a block's creator can know (first half → second half of the trace; base rate 24% / 22% / 42%):
- Position in the request: 35 → 27% for blocks 1–3, 23 → 18% for 64+ (conversation); 35 → 29% vs 22 → 16% (tool agent).
- Request length, new blocks in the request, continuation depth: 10–34% in every bucket of the two real traces; a request
  that adds a single block has 1–2% (3% of blocks). Continued conversations are *less* likely to continue again than fresh
  ones (turns so far 0: 30 → 23%; 1–4 turns: 12–14%); the time since the previous turn gives 10–27% in every bucket; the
  answer length 19–35%; the prompt length 15–34%.
- The synthetic trace is the exception: answer length ≤ 50 tokens → 83 → 66%, prompt ≤ 2k tokens → 2%, request length 65+
  blocks → 67 → 59%.
- What is strongly predictive comes only with time: a block already reused once will be reused again with 42–45% (84%
  synthetic), five times with 88–98%; a block idle for more than 300 s is dead with 96–98%. But at 200 GiB and 52 new
  blocks/s the cache turns over every ~60 s while the median first reuse comes after ~150 s, so most blocks are evicted
  before they can show either signal.

## Step 2–3 — the value of future information (fig-oracle-policies, fig-oracle-capacity)
Capacity-only, 8B blocks, 200 GiB, scored on the second half:

| policy | conversation: reuse-hit / overall / recompute Mtok / writes TB | tool agent | synthetic |
|---|---|---|---|
| A CXL-first + LRU | 0.143 / 0.056 / 65.5 / 18.3 | 0.630 / 0.360 / 64.6 / 17.9 | 0.271 / 0.230 / 28.6 / 6.9 |
| B static split + per-tier LRU | 0.174 / 0.068 / 64.7 / 18.0 | 0.647 / 0.370 / 63.6 / 17.6 | 0.344 / 0.292 / 26.3 / 6.6 |
| C global LRU | 0.174 / 0.068 / 64.7 / 18.0 | 0.647 / 0.370 / 63.6 / 17.6 | 0.342 / 0.291 / 26.3 / 6.6 |
| D reactive migration (unconstrained; moved 190 / 194 / 848 GB) | 0.208 / 0.081 / 63.8 / 18.0 | 0.661 / 0.378 / 62.8 / 17.7 | 0.342 / 0.291 / 26.3 / 7.4 |
| E oracle MIN with bypass | **0.797 / 0.311 / 47.8 / 3.2** (74,066 blocks not stored) | **0.940 / 0.537 / 46.7 / 3.0** | **0.696 / 0.592 / 15.1 / 2.0** |
| E, horizon 60 s | 0.359 / 0.140 / 59.7 / 0.8 | 0.733 / 0.419 / 58.6 / 0.8 | 0.606 / 0.516 / 18.0 / 1.1 |
| E, horizon 300 s | 0.760 / 0.296 / 48.8 / 2.5 | 0.922 / 0.527 / 47.7 / 2.5 | 0.696 / 0.592 / 15.1 / 1.8 |
| E, horizon 900 s | 0.797 (= full) | 0.940 (= full) | 0.696 (= full) |
| F oracle + tier assignment (DRAM holds the soonest next uses) | 0.797, moves 2,045 GB | 0.940, moves 2,064 GB | 0.696, moves 1,903 GB |

Useful occupancy (resident blocks with a future use): 0.30–0.31 for every LRU policy, 0.91 for the oracle; premature
evictions (evicted with a future use) 0.32 vs 0.33 — the oracle wins not by evicting better among live blocks but by
never storing the dead ones, which multiplies the capacity available to live blocks by ~4.

Capacity sweep (8B; DRAM 32% of the total): static split 0.174 / 0.471 / 0.701 (conversation) and 0.647 / 0.793 / 0.902
(tool agent) at 200 / 512 / 1024 GiB; oracle 0.797 / 1.000 / 1.000 and 0.940 / 1.000 / 1.000. The oracle at 200 GiB beats
LRU at 1 TiB on both real traces: future information is worth more than 5× the capacity, and with the dead blocks removed
the live working set of the test half fits in 512 GiB. 70B blocks at 200 GiB (1,279 slots): split 0.122 / 0.619 / 0.175,
oracle 0.552 / 0.823 / 0.472.

Prefill-time proxy (EST, per request, second half): conversation 1.48 s (split) → 1.14 s (oracle), tool agent 0.78 → 0.61 s,
synthetic 1.88 → 1.19 s — recomputed tokens −26 / −27 / −43%.

**Gate 1: PASS on all three traces** — reuse-hit share +62 / +29 / +35 points over the best capacity-matched baseline
(criterion ≥ 5), recomputed tokens −26 / −27 / −43% (≥ 20), host writes −82 / −83 / −70% (≥ 50). All three criteria pass.

## Step 4 — online predictability (fig-oracle-gain-captured)
Share of the oracle's gain over the static split captured on the second half (fitted on the first half where applicable):

| online policy | conversation | tool agent | synthetic |
|---|---|---|---|
| SLRU, protected 1/3 (logical; no data movement) | 0.209 → **6%** | 0.661 → **5%** | 0.359 → **4%** |
| SLRU 1/2 / 2/3 / 4/5 | 0.199 / 0.188 / 0.188 | 0.652 / 0.644 / 0.644 | 0.348 / 0.321 / 0.294 |
| SLRU with the protected segment in DRAM (moves 0.4–1.9 TB) | same hits as the logical SLRU | same | same |
| reactive migration (D) | 0.208 → 5% | 0.661 → 5% | 0.342 → −1% |
| admission filter, θ = 0.12 (bypasses the ≤ 12% buckets) | 0.187 → 2% | 0.659 → 4% | 0.282 → −18% |
| admission filter, θ = 0.35 | 0.011 (bypasses almost everything) | 0.621 | 0.157 |
| eviction by past reuse count (lowest class first) | 0.188 → 2% | 0.644 → −1% | 0.208 → −39% |
| for reference: oracle with a 60 s / 300 s horizon | 30% / 94% | 29% / 94% | 74% / 100% |

**Gate 2: FAIL** for the two real workloads — the best online rule captures 6% of the ceiling (criterion ≥ 50%), and the
admission filter that would save the most capacity costs more hits than it gains. The information that carries the
oracle's gain is whether a newly created block will be used at all within the next ~5 minutes (a 300 s horizon gives 94%
of the oracle); no feature available at creation in these traces separates the 24% of blocks that will from the 76% that
will not (every bucket lies between 10% and 35%), and the strong signals (a past reuse, 300 s of idleness) appear only
after a residence longer than the cache's ~60 s turnover at 200 GiB. The synthetic trace is predictable from request
features (answer length ≤ 50 tokens → 66–83% reuse), but it is synthetic.

## Verdict
- **Future reuse information has very large value** at the capacities we can afford: an oracle serves 80 / 94 / 70% of
  reuses where LRU-type policies serve 17 / 65 / 34%, cuts recomputation by a quarter to almost half, and writes 70–83%
  fewer bytes into host memory — the write saving alone would halve neighbour interference and bring 70B 4× under the CXL
  ceiling. The gain comes almost entirely from not storing never-reused blocks, which turn over the whole cache in a
  minute at 200 GiB (A1 supported).
- **It is not predictable online from what these traces contain** (A2 not supported): position, length, continuation,
  turn count, inter-turn gap, answer length and the like move the reuse probability within 10–35% of a 22–24% base rate;
  the strong signals are history and idleness, which a 200 GiB cache does not keep blocks long enough to observe. Simple
  online rules (segmented LRU, reactive promotion, admission filters, frequency eviction) recover ≤ 6% of the ceiling.
- **Migration adds no hits at equal capacity.** Oracle + tier assignment equals the oracle (by construction), and the
  reactive migration's +3 points on the conversation trace equal what a logical segmented LRU gets without moving a
  byte: the gain was frequency-based *retention*, not placement. Physical promotion matters only for DRAM-read speed
  (none for the GPU on c28) or for the write-cost side (RQ3).
- Missing information: a session-level signal that a conversation will continue within minutes (an open client
  connection, an explicit end-of-session or "more turns expected" hint, user state). The trace cannot supply it and no
  per-block or per-request feature in it stands in for it. Whether a serving system can obtain it is a design question
  outside this experiment, not a prediction problem.
- Limits: three traces, one of them synthetic; capacity-only model (no bandwidth or interference — the bandwidth-
  constrained oracle was not needed for the gate decisions); block size and 200 GiB from the earlier campaigns; the
  second half of each trace as the test segment (the oracle's test-half result at ≥ 512 GiB is 1.0 because the live
  working set of that half fits); the prefill-time proxy is an estimate.
