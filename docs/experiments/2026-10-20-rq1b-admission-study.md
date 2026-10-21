# 2026-10-20 — RQ1-B: historical reuse-aware admission — mechanism, static rules vs online learning, feedback correctness, generalization, oracle gap

**STATUS: CLOSED (2026-10-20).** Verdict: the learned admission filter's benefit is **second-touch admission** — refusing
first-touch blocks cuts host-cache writes by 69–77% and lengthens the LRU residence from 42 s to one reuse horizon (123–156 s),
which is where the reuses are. Written out as a parameter-free rule (admit a block only if its hash was looked up before) the
mechanism captures 26% / 29% of the oracle's hit gain at 210 GiB on the conversation / tool-agent traces (learned class policy
22% / 25%; best request-structure rule 16% / 12%) and 22% / 24% at 419 GiB (learned 16% / 16%); the learned class rates add
capacity awareness (15–20% vs 5–14% at 52–105 GiB; no harm where the capacity already covers the reuse horizon, where the rule
is −9 … −303%). Censoring and delayed labels are real but not binding (±3 points); frozen statistics decay (17–18%, 0% after a
phase change). The remaining gap is one category — the reused 20% of fresh requests' new blocks, 45% of the oracle's extra hits —
that neither history nor the request separates. Gate 2 stays PARTIAL. Evidence types: **TRACE-DRIVEN REPLAY** (the capacity simulator with prefix-aware
scoring and LMCache's tail-first order, on the real Mooncake conversation / tool-agent traces, the SYNTHETIC Mooncake
trace, two REAL agent runtime traces, and two **CONSTRUCTED** mixed traces assembled from the two real traces),
**OFFLINE DECISION AUDIT** (per-access and per-admission comparison of policies against LRU and the oracle),
**ORACLE** (Belady with bypass). No runtime measurement. Previous round: `2026-10-18-rq1b-history-learning.md`.
Raw: `experimental_results/2026-10-20-rq1b-admission-study/` (`g-*` main grid, `v-*` variants, `s2-*` second-touch rule, `m-*` mixed traces,
`a-*` agent traces, `dump/` hit and admission dumps, `run_all.sh` the exact commands). Code: `scripts/kv_agent_replay.py`
(static rules, corrected class, exploration, bypass feedback, freezing, reason-coded and admission dumps),
`scripts/kv_hits_compare.py`, `kv_hits_explain.py`, `kv_admit_gap.py`, `kv_mix_traces.py`, `kv_admission_tables.py`,
`kv_admission_figs.py` (fig-admission-grid, fig-admission-walkforward).

**A correction to the previous round.** The 2026-10-18 learned class was meant to be (root, position bucket,
continuation-depth bucket) but its depth term was computed after the request's own earlier blocks had been marked
"seen", so it equalled the position: the class was effectively (root, position). This round fixes it (depth =
number of blocks of the request that existed before the request started) and, because the fix makes the previous
numbers not reproducible by the current code, re-runs every configuration; the 2026-10-18 figures stand as a
position-only variant.

## Setup
Mooncake traces at 8B block size (512 tokens = 67.1 MB), capacities 50 / 100 / 200 / 400 / 800 GiB (800 … 12,800
blocks), LMCache order (tail first), prefix-aware scoring on the second half of the requests, writes counted in the
scored half, TTFT model from the miss-cost round. Policies: global LRU; SLRU 1/3; four **static** admission rules on
LRU — bypass a new block at position ≥ 8 in its request (`static_d8`), of a request whose existing prefix is ≥ 8 blocks
(`static_p8`), the 8th or later *new* block of its request (`static_n8`), position ≥ 8 and prefix ≥ 8 (`static_dp8_8`)
— never a request's first block; a **static rule on cache history**, added after the main grid (`static_2nd1` / `2nd8` /
`2nd32`, files `s2-*`: a block seen before is always admitted, a never-seen block only in the first 1 / 8 / 32 positions of its
request); two **learned** admission policies with the cache's own feedback (`lhd`: class =
(root, position bucket 0–7 / 8–15 / 16–31 / 32+, prefix bucket 0–7 / 8–15 / 16+), `cond`: per root), bypass when the
class's decayed hit-before-eviction rate (Beta prior 0.3, strength 20, decay 4τ = 1200 s) is below 0.15 after ≥ 50
samples; the oracle. The threshold 0.15 and the bucket edges are the previous round's hand-set values; §B tests the
rules' sensitivity and §C the threshold's; nothing was chosen on the scored half.

## Task A — where the admission benefit comes from (Deliverable 1; per-access and per-admission accounting, 200 GiB)
Three policies on the same LRU cache: LRU without a filter, the learned class filter, and the parameter-free
second-touch rule (`static_2nd1`, §B: a block is admitted only if its hash was looked up before).

| quantity (scored half) | conversation: LRU | learned class | second touch | tool agent: LRU | learned class | second touch |
|---|---|---|---|---|---|---|
| admissions (blocks written) | 268,621 (18.0 TB) | 83,160 (5.6 TB, −69%) | 67,858 (4.6 TB, −75%) | 262,741 (17.6 TB) | 74,178 (5.0 TB, −72%) | 60,037 (4.0 TB, −77%) |
| admitted blocks never reused ("useless admissions") | 180,207 (67%) | 48,021 (58%) | 35,116 (52%) | 180,488 (69%) | 42,737 (58%) | 29,630 (49%) |
| refused admissions / of which reused later (≤ 60 s; ≤ 300 s) | – | 169,636 / 43,039 (7,547; 30,618) | 182,789 / 44,143 (7,462; 31,400) | – | 171,938 / 40,054 (8,073; 31,820) | 183,296 / 39,477 (7,584; 31,379) |
| residence of an admitted block (write → eviction, p50) | 42 s | **123 s** | **141 s** | 42 s | **132 s** | **156 s** |
| online residence estimate (capacity / admission rate) at the end | – | 137 s | – | – | 160 s | – |
| misses after an eviction / after a refusal / on never-seen blocks | 43,426 / 0 / 82,659 | 14,971 / 21,265 / 82,659 | 14,201 / 20,730 / 82,659 | 39,715 / 0 / 84,427 | 12,731 / 18,864 / 84,427 | 12,041 / 18,055 / 84,427 |
| hits (usable-prefix hit share) | 9,413 (0.178) | 16,603 (0.313) | 17,908 (0.339) | 72,997 (0.648) | 81,117 (0.717) | 82,616 (0.733) |
| per access vs LRU: avoided misses / introduced misses / net | – | 8,814 / 1,624 / **+7,190** | 9,928 / 1,433 / **+8,495** | – | 9,996 / 1,876 / **+8,120** | 11,264 / 1,645 / **+9,619** |
| share of the oracle's hit gain | – | 22% | 26% | – | 25% | 29% |
| net hits per TB of writes saved | – | 580 / TB | 630 / TB | – | 640 / TB | 710 / TB |

(The block oracle: 47,476 / 44,277 admissions, none useless, 42,096 / 105,929 hits, residence 150 / 162 s.)

**The causal path.** Both filters refuse 63–70% of the admissions LRU would make (169,636–183,296 of 268,621) and
75–78% of the refused blocks are never read again. That cuts the write stream by 69–77%, and since the LRU residence
is capacity divided by the admission rate, the blocks that *are* admitted now stay 123–156 s instead of 42 s — one
reuse horizon (the next use of a reused block comes 102–108 s after the eviction LRU would have done; previous
round, A4) instead of a third of it. The hits gained are exactly the re-reads that fall inside the longer residence.
By the per-access accounting (`kv_hits_explain.py`) the avoided misses are 95–99% in continuation requests (≥ 8
existing blocks) and 100% (second touch) / 94% (learned) on blocks with ≥ 2 past uses — 40–46% of the accesses to
blocks with 2–4 past uses become hits; the introduced misses are 100% / 84% on blocks with exactly one past use
(7–9% of those accesses) — blocks that LRU hit at their second touch but the filter had refused at their first.
The refused-but-reused 39,477–44,143 blocks cost 18,055–21,265 misses after refusal, of which only 1,433–1,876 would
have been hits under LRU — the rest LRU would have evicted anyway. Net: +7,190 … +9,619 hits for 12.4–13.6 TB fewer
writes.

**The mechanism is second-touch admission.** The learned class policy has no "seen before" feature; it reaches the
same per-access signature through the existing-prefix bucket of its class (first-touch blocks sit in requests with
few existing blocks, whose classes learn a low hit-before-eviction rate; re-touched blocks sit in continuation
requests, whose classes learn a high one). Written out as a rule — admit a block only when its hash has been looked
up before — the mechanism is sharper: no new block of the scored half is admitted at all (every request on these
traces starts with an already-seen root, so the "first block" exception never fires), the admissions are 18–19%
fewer than the learned policy's, 48–51% of them are useful (learned 42%, LRU 31–33%), and the net gain is 18%
higher (26% / 29% of the oracle's gain vs 22% / 25%). The learned policy admits 15,302 / 14,141 more blocks than the
rule and 12,905 / 13,107 more never-reused ones: the class ambiguity of §E. What the learned policy adds is not in the mechanism
but in *when* to apply it (§B, §D2: small capacities, capacity that covers the horizon).

**Why admission and not retention ranking.** Retention ranking chooses *which* resident block to drop; it cannot
change how long blocks stay, because the residence is set by the write rate: 268k admissions into 3,200 slots give
42 s whatever the order. The reuse that matters arrives at ~105 s. The only online lever that moves the residence is
the admission rate, and the filters triple it. A perfect ranking inside a 42-s residence can at most reorder the
~5% of hits that fall near the boundary (SLRU's +1,648); a filter that cuts admissions by 69–77% reaches the reuses at
60–150 s that no ranking can.

## Task B — learned admission vs static rules (Deliverable 2; fig-admission-grid)
Usable-prefix hit share / TB written / share of the oracle's hit gain over LRU, same traces, capacities, order,
warm-up and scoring. Three kinds of policy, kept apart as the brief asks:
- **static rules on request structure** (no state beyond the request): `d8` = bypass position ≥ 8, `p8` = bypass
  requests with ≥ 8 existing blocks, `n8` = bypass the 8th+ new block of a request, `dp8_8` = both;
- **static rule on cache history** (state = the set of hashes ever looked up, no learned parameter): `2nd` =
  second-touch admission — a block is admitted only if its hash was looked up before; a never-seen block is admitted
  only as the first block of a request (`2nd8`: or in the first 8 positions). In the replay the set of seen hashes
  is unbounded (366k hashes for the hour-long traces); a deployment would bound it (Bloom filter or a decayed ghost
  list) — not tested;
- **online learned** (`lhd` = the class policy of this round; `frozen` = its statistics updated only during the first
  20% of the trace); and the block **oracle**.

| capacity | LRU | SLRU | d8 | p8 | n8 | dp8_8 | 2nd (second touch) | lhd online | lhd frozen 20% | oracle |
|---|---|---|---|---|---|---|---|---|---|---|
| conversation 52 GiB | 0.117 / 18.5 | 0.120 / 1% | 0.136 / 4.3 / 6% | 0.118 / 0% | 0.125 / 2% | 0.119 / 1% | 0.132 / 6.1 / 5% | **0.164 / 2.0 / 15%** | – | 0.446 / 2.9 |
| conversation 105 GiB | 0.130 / 18.4 | 0.147 / 4% | 0.200 / 3.9 / 15% | 0.137 / 2% | 0.151 / 4% | 0.135 / 1% | 0.181 / 5.6 / 11% | **0.218 / 2.9 / 20%** | – | 0.610 / 3.2 |
| conversation 210 GiB | 0.178 / 18.0 | 0.209 / 5% | 0.273 / 3.4 / 15% | 0.210 / 5% | 0.277 / 8.9 / 16% | 0.208 / 5% | **0.339 / 4.6 / 26%** | 0.313 / 5.6 / 22% | 0.289 / 6.4 / 18% | 0.797 / 3.2 |
| conversation 419 GiB | 0.376 / 16.5 | 0.376 / 0% | 0.329 / −8% | 0.356 / −3% | 0.476 / 7.5 / 17% | 0.377 / 0% | **0.504 / 3.6 / 22%** | 0.467 / 7.8 / 16% | – | 0.967 / 3.0 |
| conversation 839 GiB | 0.624 / 14.7 | **0.674 / 13%** | 0.360 / −70% | 0.507 / −31% | 0.648 / 6.4 / 6% | 0.533 / −24% | 0.591 / 3.0 / −9% | 0.606 / 10.1 / −4% | – | 1.000 / 3.0 |
| tool agent 52 GiB | 0.615 / 18.2 | 0.616 / 1% | 0.460 / −99% | 0.617 / 1% | 0.619 / 2% | 0.617 / 1% | 0.625 / 5.7 / 6% | **0.639 / 2.0 / 16%** | – | 0.772 / 2.8 |
| tool agent 105 GiB | 0.624 / 18.0 | 0.631 / 3% | 0.490 / −59% | 0.628 / 2% | 0.630 / 3% | 0.627 / 1% | 0.656 / 5.1 / 14% | **0.666 / 2.9 / 20%** | – | 0.851 / 3.1 |
| tool agent 210 GiB | 0.648 / 17.6 | 0.661 / 5% | 0.525 / −42% | 0.668 / 7% | 0.682 / 9.8 / 12% | 0.669 / 7% | **0.733 / 4.0 / 29%** | 0.717 / 5.0 / 25% | 0.696 / 6.1 / 17% | 0.940 / 3.0 |
| tool agent 419 GiB | 0.748 / 16.1 | 0.748 / 0% | 0.551 / −78% | 0.740 / −3% | 0.779 / 8.4 / 12% | 0.749 / 0% | **0.809 / 3.0 / 24%** | 0.766 / 8.4 / 16% | – | 1.000 / 2.6 |
| tool agent 839 GiB | 0.862 / 14.3 | **0.884 / 16%** | 0.562 / −217% | 0.813 / −36% | 0.860 / −1% | 0.822 / −29% | 0.837 / 2.7 / −18% | 0.880 / 10.2 / 14% | – | 1.000 / 2.6 |
| synthetic 210 GiB (SYNTHETIC) | 0.348 / 6.6 | 0.365 / 5% | 0.151 / −57% | 0.140 / −60% | 0.352 / 1% | 0.198 / −43% | 0.364 / 3.7 / 5% | 0.313 / 5.5 / −7% | – | 0.696 / 2.0 |

Second-touch variants (`s2-*`): `2nd8` (first 8 positions of a fresh request admitted on first touch) 20% / 21% at
210 GiB with 7.6 / 7.3 TB, 19% / 20% at 419 GiB, 6% at 839 GiB (conversation); `2nd32` 4–9%. Synthetic trace: `2nd`
+1 / +4 / +5 / +12 / +16% from 52 to 839 GiB, `lhd` −7 … −11% everywhere.
Request-structure rule sensitivity at 210 GiB (`v-*-static`): conversation d4 7% / d16 16% / n4 **20%** / n16 8% /
p4 5% / p16 4% / dp4_8 5% / dp8_4 5% / dp16_8 4%; tool agent d4 **−111%** / d16 13% / n4 16% / n16 6% / p4 9% /
p16 3% / dp4_8 7% / dp8_4 8% / dp16_8 3%.

- **The best admission policy at 200–400 GiB on both real traces is the parameter-free second-touch rule, not the
  learned one:** 26% / 29% of the oracle's gain at 210 GiB (learned 22% / 25%) and 22% / 24% at 419 GiB (learned 16%
  / 16%), with fewer writes (4.6 / 4.0 TB vs 5.6 / 5.0 at 210 GiB; 3.6 / 3.0 vs 7.8 / 8.4 at 419 GiB), and it is the
  only filter clearly positive on the synthetic trace (5–16%; n8 0–5%, learned −7 … −11%). It is a classical ghost-cache admission (admit on the
  second access), and it is exactly the mechanism the learned policy had converged to (§A).
- **The learned class policy wins at small capacities** (52–105 GiB: 15–20% vs 5–14%) because it admits far less
  (2.0–2.9 TB vs 5.1–6.1 TB): with a 30-s residence even second-touch blocks (next use p50 102–108 s) are evicted
  before their reuse, and the class statistics learn that only the classes with a short reuse distance pay off; the
  second-touch rule admits every re-seen block regardless of capacity.
- **Request-structure static rules capture 2–20% and are fragile.** "8th+ new block" (n8) is the only one that is
  never harmful on the real traces (2–17%); position rules (d8), the best on the conversation trace at 100–200 GiB
  (15%), are catastrophic on the tool-agent trace (−42 … −217%: its shared system prompts are longer than 8 blocks,
  so the rule bypasses the prefix everybody re-reads) and on both traces at 839 GiB (−70%); prefix-length rules add
  2–7%; on the synthetic trace every request-structure rule but n8 is harmful (−43 … −60%).
- **Where the cache already keeps a block for a reuse horizon, every filter loses and the learned policy loses
  least.** At 839 GiB (LRU residence 186 s) the second-touch rule is −9% / −18% (it refuses the first-touch
  admissions whose reuse LRU would now have kept), the learned policy −4% / +14%, SLRU +13% / +16%. On the real agent
  traces (§D) the same happens at 32–48 chunks: second touch −101 … −303% (short tool) and −229% (long tool with
  churn), learned 0–1% / 57%.
- **Online updating matters under drift, not on a stationary trace:** frozen after the first 20% of the trace the
  class policy still recovers 17–18% (vs 22–25%); its hits per fifth decay (conversation: 2,952 → 2,511 in the last
  fifth, online 3,161 → 2,899) because the frozen counters keep decaying toward the prior. On the constructed traces
  (§D4) the frozen policy recovers 0–8%.



## Task C — online feedback correctness audit (Deliverable 3)
### C1. What the cache can observe
The replay labels a class from events a host cache really sees: an admitted block's first hit after admission
(LMCache: a lookup that finds the key, `MP_LOOKUP_PREFETCH_END` / `L1_READ_RESERVED`) and its eviction without a hit
(`L1_KEYS_EVICTED`); the hash of a *bypassed* block is seen again when a later request looks it up (the lookup is by
hash, so the miss on a bypassed hash is observable as "would have hit if kept"). Both are available at runtime without
changing vLLM or LMCache (the agent-runtime round mirrored exactly these events). What is not observable: whether a
bypassed block *would* have survived until that lookup had it been admitted — the counterfactual residence — which
the audit replaces with the online residence estimate (capacity / recent admission rate).
### C2. Selection bias (censored feedback)
In the 2026-10-18 implementation a bypassed block gave no feedback at all, so once a class fell below the threshold it
could only recover through the decay of its statistics toward the prior (4τ = 20 min) — an implicit, slow
exploration. This round measures the effect and tests three remedies: (i) decay only (the previous behaviour);
(ii) ε-exploration — admit 5% of would-be-bypassed blocks so that every class keeps receiving labels; (iii) bypass
feedback — a bypassed hash that is requested again within the online residence estimate labels its class 1, one that
is not labels it 0 (both observable). §C-results compares them.
### C3. Delayed labels
A negative label arrives at eviction, i.e. one residence time after admission (39 s at 200 GiB); a positive label at
the first hit (1.3 s to 108 s). Until the label arrives the class statistics do not change, so the estimate lags the
workload by about one residence time; the decay constant (1200 s) is 30× longer, so the lag is not the binding delay.
The freeze experiment (§D3: statistics frozen after the first 20% of the trace) measures what continuous updating is
worth against this delay.
### C4. Adaptation mechanism
Exponentially decayed class counters with a Beta prior and a minimum sample count are the simplest mechanism that
(a) forgets, (b) falls back to "admit" when a class is new or rarely seen, and (c) needs one counter pair per class;
sliding windows and EMA are equivalent at this granularity. Exploration (ii) or bypass feedback (iii) is the only
addition the audit found necessary; see the results.

### Task C — results (conversation / tool agent, 210 GiB; share of the oracle's gain, TB written)
| variant | conversation | tool agent |
|---|---|---|
| learned class, decay only (the baseline; implicit exploration through 4τ = 1,200 s decay) | 22% / 5.6 TB | 25% / 5.0 TB |
| + ε-exploration (5% of refusals admitted: 9,353 / 8,513 explored blocks) | 21% / 5.1 TB | 23% / 5.7 TB |
| + bypass feedback (refused hashes requested again within the residence estimate count as 1) | 21% / 7.2 TB | 22% / 7.4 TB |
| minimum 200 samples per class instead of 50 | 21% / 5.9 TB | 21% / 5.7 TB |
| threshold 0.10 / 0.15 / 0.25 | 19% / 22% / 22% (6.3 / 5.6 / 2.8 TB) | 21% / 25% / 22% (6.4 / 5.0 / 2.8 TB) |
| per-root class (`cond`) at 0.10 / 0.15 / 0.25 | 12% / 16% / 19% | 12% / 14% / 4% |
| feedback label delay p50 / p90 (admission → label) | 114 / 144 s | 120 / 162 s |

- **Censoring is real but not binding.** A refused class receives no labels until its counters decay back above the
  threshold (≈ 1,200 s), so on a stationary trace the filter under-admits classes whose reuse rate sits near the
  threshold. Making the feedback uncensored — by exploration or by counting the re-requests of refused hashes —
  changes the result by −1 … −3 points of the oracle's gain and adds 0.5–2.4 TB of writes: the extra labels mostly
  re-admit blocks that the capacity cannot keep anyway (bypass feedback labels a re-request within the *estimated*
  residence, 137–160 s, as useful, which is optimistic). The decay is a sufficient exploration mechanism on these
  traces; on the phase-change trace (§D3) it is also what lets the policy recover.
- **Delayed labels:** the median label arrives 114–120 s after admission (p90 144–162 s) — the residence under the
  filter itself — so the class statistics lag the workload by about two minutes; with a 20-minute decay this is not
  the limiting factor.
- **The threshold is not sensitive for the class policy (19–25% between 0.10 and 0.25)** and the per-root policy is
  (4–19%); the write volume is sensitive (2.8–6.4 TB). The 0.15 used throughout is the previous round's hand-set value, not tuned on these traces.
- **Information availability:** every signal the filter uses is a lookup, a hit or an eviction of a hash (LMCache
  publishes all three on its event bus; the agent-runtime round recorded them); the online residence estimate
  (capacity / recent admission rate, 137–160 s) tracks the measured residence under the filter (123–132 s) within 15%.
  No future information enters: the class statistics are updated only when a label resolves, the admission decision
  reads the statistics as they are at that instant.


## Task D — generalization and drift (Deliverable 4; fig-admission-walkforward)
**D1 across workloads.** The same policy and threshold: conversation 22%, tool agent 25%, synthetic −7% (200 GiB);
the second-touch rule 26% / 29% / +5%. On both real traces the best policy at every capacity from 52 to 419 GiB is one of
the two history-based filters (learned at 52–105 GiB, second touch at 210–419 GiB); on the synthetic trace, whose reuse is memoryless per block, every request-structure filter and the
learned one lose and only the second-touch rule gains (its "seen before" is the one signal the synthetic generator
does carry).
**D2 across capacity.** The learned filter's value peaks where the LRU residence is far below the reuse horizon
(52–210 GiB: 15–25%) and fades when the cache already keeps a block for one horizon (419 GiB: 16%; 839 GiB: −4% /
+14%, where LRU's residence is 186 s); it never becomes destructive, unlike the request-structure rules, because the
classes' hit-before-eviction rates rise with the residence and the filter admits more (9% → 31% of new blocks from
210 to 419 GiB). The second-touch rule has the opposite profile: weak at 52–105 GiB (5–14%: it admits every re-seen
block and the 30-s residence wastes most of them), best at 210–419 GiB (22–29%), negative at 839 GiB on the
conversation trace (−9%: a fixed rule cannot notice that the capacity now keeps first-touch blocks until their
reuse). The crossover lies where the LRU residence reaches roughly a third of the reuse horizon (between 21 s at 105 GiB and
42 s at 210 GiB; horizon ~105 s).
**D3 across time (walk-forward).** At 200 GiB the online policy is above LRU in every fifth of the scored half
(conversation 3,161 / 3,311 / 3,585 / 3,647 / 2,899 hits vs LRU 1,893 / 1,952 / 1,989 / 1,829 / 1,750; tool agent 16,207 …
15,849 vs 14,791 … 14,624), including the first fifth: the statistics converge during the unscored first half (the
label delay is two minutes, the trace an hour). The frozen variant decays in the last fifths; the conversation
trace's hot-set change after 20 minutes (previous round) does not hurt the online policy because the classes are
request-structural, not block identities.
**D4 constructed mixed traces (CONSTRUCTED from the two real traces, 200 GiB).**
| policy | interleaved (both streams in parallel) | phase change (conversation, then tool agent) |
|---|---|---|
| LRU / SLRU | 0.464 / 0.476 (4%) | 0.645 / 0.662 (6%) |
| static n8 / dp8_8 | 0.476 (4%) / 0.468 (1%) | 0.684 (13%) / 0.662 (6%) |
| learned class, online | **0.521 (19%, +9,752 hits, 6.1 TB vs 36.4)** | **0.712 (26%, +13,012, 10.6 TB vs 35.7)** |
| learned root, online | 0.508 (14%) | 0.690 (15%) |
| learned class / root, frozen after 20% | 0.487 (8%) / 0.477 (4%) | 0.645 (0%) / 0.645 (0%) |
| static second touch / second touch with first 8 free | 0.502 (12%, +6,257, 10.8 TB) / 0.482 (6%) | **0.735 (31%, +15,367, 8.6 TB)** / 0.710 (22%) |
| oracle | 0.775 | 0.936 |

With the two workloads interleaved, the request-structure rule that was best on each alone (n8) is worth 4%: it
cannot treat the two roots differently; the second-touch rule keeps 12% (it needs no per-root knowledge but admits
every re-seen block of both streams, 10.8 TB); the learned class policy keeps 19% with 6.1 TB because its classes
are per root and it refuses the re-seen blocks of the low-reuse classes. After the phase change the frozen
statistics are worthless (they were learned on the conversation phase and decay to the prior during the tool-agent
phase: 0%), the online policy re-learns within the first fifth of the new phase (hits per fifth 24,840 / 25,122 /
24,060 / 25,033 / 24,354 vs LRU 22,444 …) and reaches 26%; the second-touch rule, which has nothing to re-learn,
reaches 31%.
**Real agent traces (`a-*`, `s2-a-*`).** On the real-tool trace with churn a request-structure rule is as good as
or better than the learned ones (4th+ new block 89–91% of the oracle's gain at C / W_live 1.3–1.7, learned root
85–88%, learned class 56–60%, second touch 55–56%): one root, short uniform contexts, nothing to learn. At 48 chunks,
where the capacity covers the live set, the second-touch rule turns destructive (−229%; short-tool trace −101% at
32 and −303% at 48 chunks) while the learned class policy stays at 57% / 0–1%: agent blocks are reused 3–5 s after
their first touch, and refusing the first touch loses that reuse whenever the cache would have kept the block. On
the short-tool trace nothing but the continue signal helps (53–56%). The learned policy's value is in workloads with
several request classes and in not filtering when the capacity suffices.


## Task E — the remaining oracle gap (Deliverable 5; `kv_admit_gap.py`, admission dumps)
Every NEW block of the scored half, classified by the oracle's and the learned class policy's admission decisions
(conversation / tool agent, 200 GiB; 82,659 / 84,427 new blocks):

| class | share of new blocks | reused later | next use p50 / p90 | stack distance p50 | where they are |
|---|---|---|---|---|---|
| oracle admits, model admits | 1.5% / 1.3% | 100% | 102 s / 285–324 s | 480–504 GiB | mostly continuation requests (62–71%) |
| **oracle admits, model bypasses** | **17.9% / 17.1%** | **100%** (79–83% within 300 s) | 102–111 s / 411–507 s | 499–544 GiB | **97–98% in fresh requests (< 8 existing blocks), all positions** |
| oracle bypasses, model admits | 7.6% / 7.6% | 1% | – | – | 73–79% in continuation requests: pure write waste (424–429 GB) |
| oracle bypasses, model bypasses | 72.9% / 74.1% | 1% | – | – | the never-reused majority (94% / 84% in fresh requests) |

At 400 GiB the model admits more (30.5% / 43.2%: it now keeps the first 8 blocks of fresh requests, 7.2–10.5% of
them right and 23–33% wasted) and still refuses 13.1% / 8.3% that the oracle admits (positions 8+ of fresh requests).

- **The gap is one identifiable category and it is not learnable from history or the request:** the reused minority
  of *fresh* requests' new blocks. In the "fresh request, position p" classes 20.6% of the blocks come back (p50 after
  110 s, within 300 s for 80%) and 79.4% never do; nothing in the request (length, position: lift ≤ 1.25, previous
  round A3) and nothing in the cache's history (the block is new) separates them; the class rate (0.206 reused, but
  only ~0.1 *hit before eviction* at a 42–120 s residence) sits below any useful threshold, so the policy refuses the
  whole class and loses all 14,826 / 14,407 reuses — 45% of the oracle's extra hits. Those blocks are re-read by the
  next turn of a conversation that is starting now; only the application knows which conversations will continue
  (the agent-runtime round's continue signal is that information, for agents).
- **The second component is wasted admissions in continuation requests** (7.6% of new blocks, 1% reused): the class
  policy admits them because their class rate hovers around the threshold; a finer class (deeper position buckets)
  or a higher threshold removes part of it at the cost of the 1.5% that are right (threshold 0.25: writes 2.8 TB,
  same hits).
- **The second-touch rule has the same gap and no wasted admissions among new blocks:** it admits no new block of
  the scored half, so "oracle admits / rule refuses" is 19.4% / 18.3% of new blocks (100% reused, 94% in fresh
  requests, next use p50 102–108 s) and "oracle refuses / rule admits" is empty; its remaining waste is on re-seen
  blocks (52% / 49% of its admissions are never reused — any block seen twice is admitted whatever its class).
- **Nothing left to learn at the block level:** both "both bypass" classes are 99% dead, "both admit" 100% alive; the
  model's errors are the class-level ambiguity of fresh requests (information not available) and threshold noise
  (model), in a 2:1 ratio of lost hits to wasted writes.


## Task F — decision quality (Deliverable 3/6 support)
| measure (200 GiB) | conversation | tool agent |
|---|---|---|
| useful-admission rate (admitted blocks that are read again): LRU → learned class → second touch | 33% → **42%** → **48%** (oracle 100%, static n8 40%) | 31% → **42%** → **51%** (static n8 36%) |
| admission precision on NEW blocks, label = reused at any time | 17% (1,287 of 7,545 admitted new blocks) | 15% |
| admission recall on NEW blocks (reused new blocks that were admitted) | 7.6% | 7.0% |
| precision / recall on all admissions, label = hit before eviction | 42% / – (the policy's own label) | 42% / – |
| false bypass (refused, reused within the realistic horizon = 300 s): learned / second touch | 30,618 of 169,636 refusals (18%) / 31,400 of 182,789 (17%) | 31,820 of 171,938 (19%) / 31,379 of 183,296 (17%) |
| false admission (admitted, never reused): learned / second touch | 48,021 of 83,160 (58%) / 35,116 of 67,858 (52%) | 42,737 of 74,178 (58%) / 29,630 of 60,037 (49%) |
| avoided pollution (dead occupancy share of cache-time): LRU → learned → second touch | 0.70 → 0.58 → 0.55 | 0.70 → 0.57 → 0.53 |
| write reduction: learned / second touch | −69% (18.0 → 5.6 TB) / −75% (4.6 TB) | −72% (17.6 → 5.0 TB) / −77% (4.0 TB) |
| net useful hits: learned / second touch | +7,190 / +8,495 (+76% / +90% over LRU's 9,413) | +8,120 / +9,619 (+11% / +13% over 72,997) |
| residence estimate (online) vs measured | 137 vs 123 s | 160 vs 132 s |
| update cost / metadata: learned | O(1) per access; one counter pair per class (roots × 4 × 3; 12 / 48 entries); per cached block a class id and a hit flag (2 bytes) | same |
| update cost / metadata: second touch | O(1) per access; a set of seen hashes (366k entries for the hour-long trace, unbounded in the replay; a Bloom filter or decayed ghost list in practice — not tested) | same |

Two labels, two answers: measured against "reused at any time" the filter is a poor classifier of new blocks
(precision 15–17%, recall 7–8%) because it refuses the ambiguous fresh-request classes wholesale; measured against
what the cache can use — "hit before a realistic eviction horizon", with the horizon estimated online from the
admission rate — it raises the useful-admission rate from a third to 42% and that is what produces the hits. The
calibration of the class rates could not be checked against a ground truth without future information; the
proxy is the residence estimate, within 15% of the measured residence.


## Task G — what this gives the unified DRAM/CXL manager (analysis only)
- **What value information it provides:** at block creation / host admission, a per-class probability that the block
  will be read again before the cache would evict it, learned from the cache's own lookups, hits and evictions (no
  application signal, no model), plus an online estimate of the residence time. It identifies **low-value data**
  reliably: 75% of what it refuses is never read again; the refusals are the deep new blocks of continuing
  conversations, the second and later blocks of single-turn requests at small capacities, and the low-reuse roots of
  the tool-agent trace.
- **What it cannot judge:** the 20% of fresh-request blocks that will be re-read by a next turn (the remaining
  oracle gap, 45% of the oracle's extra hits) — only the application can say which conversations continue — and the
  ambiguous classes near the threshold (7.6% of new blocks admitted in vain).
- **Effect on capacity and host writes:** −66 … −72% of host-cache writes at 100–400 GiB on both real traces with
  +12 … +25% of the oracle's hit gain, and a residence 3× longer at the same capacity (the same hit share as a
  cache ~2× larger under LRU: 0.313 at 200 GiB vs LRU's 0.376 at 400 GiB). The write reduction is a replay result,
  not a measured interference reduction.
- **As an input to the joint value-and-movement-cost analysis:** yes, as the admission-side value signal — but the
  signal is simpler than a learned model: "has this hash been looked up before" (second touch) carries most of it
  (26–29% of the oracle's gain at 210 GiB, −75 … −77% writes), and the learned class rates add the capacity
  awareness (when the residence is too short even for re-seen blocks, and when it is long enough that filtering
  hurts). Both are online, cheap and self-labelling; their outputs (admit / refuse per block, residence estimate)
  are what a movement-cost decision needs on the write side. What neither supplies is a retention-side value
  beyond recency, nor anything for fresh requests.


## Updated RQ1 assessment (Deliverable 6)
- **What reuse information is actually learned:** the per-class rate at which newly admitted blocks are read again
  before eviction, by (root, position bucket, existing-prefix bucket); it is the complement of "which blocks will be
  reused": a reliable "will not be used in time" for 63–65% of the admissions LRU makes.
- **What can be updated online, reliably:** these class rates, from lookups / hits / evictions, with a two-minute
  label delay and a 20-minute decay; censoring of refused classes is real but handled by the decay (explicit
  exploration or bypass feedback changed the result by ≤ 3 points and cost writes).
- **Why admission works where retention ranking did not:** the residence is set by the admission rate; refusing
  69–77% of the writes triples the residence to one reuse horizon; a ranking cannot change the residence.
- **What the learning actually amounts to:** second-touch admission. The learned classes converge to "refuse
  first-touch blocks, admit re-seen ones", and the rule written out directly — admit a block only when its hash has
  been looked up before, no parameter — captures **more** of the oracle's gain at 210–419 GiB (26% / 29% and 22% /
  24% vs the learned 22% / 25% and 16% / 16%) with fewer writes (−75 … −77%). A request-structure rule ("8th+ new
  block") captures 12–17%.
- **Static rule vs online learning:** the learned policy's additional value is not hit share at the capacities
  where admission matters most but *knowing when to filter*: at 52–105 GiB it keeps 15–20% where second touch
  gets 5–14% (it refuses re-seen blocks whose class cannot survive a 30-s residence); where the capacity covers the
  reuse horizon it stays within −4% of LRU while the second-touch rule is −9% (conversation 839 GiB) and −101 …
  −303% (real agent traces at 32–48 chunks); request-structure rules are fragile across traces (−42 … −217%) and
  capacities (−24 … −70%); under workload mix the learned policy is ahead (interleaved: 19% vs second touch 12% vs n8 4%) and under a phase change both online methods re-learn or need nothing to learn (second touch 31%, learned 26%) while frozen statistics are worthless (0%).
- **How much it improves cache decisions:** learned +7,190 / +8,120 net hits in the scored half (22% / 25% of the
  oracle's gain, usable-prefix hit share 0.178 → 0.313 and 0.648 → 0.717), −69 … −72% writes, useful-admission
  rate 33% → 42%; second touch +8,495 / +9,619 (26% / 29%, 0.339 / 0.733), −75 … −77% writes, 48% / 51%.
- **Errors that remain unavoidable:** the reused 20% of fresh requests' blocks (45% of the oracle's extra hits), which
  no history or request feature separates; residual wasted admissions near the threshold (7.6% of new blocks).
- **Gate 2 (≥ 50% of the oracle's gain):** still **PARTIAL** — 22–29% on the real traces at 210 GiB (second touch
  or learned), robustly, and the two together cover 52–419 GiB; the threshold is unchanged. For RQ2 the value
  information now has three parts: recency (retention), a history-based admission filter — second touch plus the
  learned class rates for capacity awareness — with its residence estimate (admission, writes), and the agent
  lifecycle events (fresh-request reuse for agents only).

