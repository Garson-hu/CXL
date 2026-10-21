# 2026-10-21 (second round) — RQ1-B: robust online reuse information and adaptive admission — regime adaptation, residence estimation, bounded metadata and prefix semantics, focused baselines, mechanism

**STATUS: CLOSED (2026-10-21).** Verdict: the online reuse information of the previous rounds is robust enough to drive
admission across capacities and load changes, with one rule and one estimator. **Regime adaptation:** compare the
residence the cache would have if it admitted everything, C / (λ_first + λ_re-seen), with the online median re-lookup
gap of first-touch blocks; filter (the gap rule `2nd_int`) while the former is below the latter, admit everything
otherwise. Selected on the first half, tested on the second: it never leaves the filter regime at 52–419 GiB (0
switches in the scored half; 21–33% of the oracle's usable-hit gain, identical to `2nd_int`) and switches to normal
admission at 839 GiB on both real traces, turning `2nd_int`'s −10 / −19% into 0% with an LRU structure and +12 / +17%
with an SLRU structure (which also lifts the filter regime to 24–35%). The re-seen gap median and a predicted-hits
model are the wrong criteria (0% on the tool-agent trace at 105–419 GiB); hysteresis is not the issue. The rule is
conservative after a load step at large capacity (re-enters filtering after 14 min on one trace, not within the hour
on the other) and is not usable on traces of 100 s. **Residence estimation:** the EWMA of the ages of blocks evicted
*without a hit* and the age of the LRU tail are unbiased (within 2× for 100% of admissions at ≥ 210 GiB); the previous
default (all evictions) and capacity / write rate over-estimate by 1.3–1.4×; the gap rule's hits are the same with
any of them (33 / 32% at 210 GiB) and its writes differ by 0.3 TB; the admission ↔ residence loop is negative and
settles within one residence after a load step (0.7–1.9 min at 210 GiB) with no oscillation (lag-1 autocorrelation
of the admission rate 0.00–0.02). **Bounded metadata and semantics:** a 16–64k-entry ghost (0.5–2 MB) or a 2 × 8 KB
Bloom filter, one float and 9 B per resident block; every input is an LMCache lookup / store / eviction event; the
prefix-semantics audit holds on all 230 policy-capacity runs. **Baselines:** the gap rule with the switch is the best
or within 3 points of the best policy at every capacity on both real traces; TinyLFU (adapted) −7 … −70% beyond
210 GiB; SLRU / ARC are right only at 839 GiB. Gate 2 stays **PARTIAL** (32–35% at 210 GiB).

Evidence types: **TRACE-DRIVEN REPLAY** (`scripts/kv_admission_sim.py`, extended; validated to the block and
audited for the prefix-semantics invariants), **OFFLINE DECISION AUDIT** (per-access bitmaps, per-decision logs with
the block's future next-use gap used for accounting only), **TRACE STATISTICS**, **ORACLE** (Belady with bypass),
**SOURCE INSPECTION** (LMCache 0.5.5 / vLLM 0.31 event paths). CONSTRUCTED dynamic loads (synthetic never-reused
8-block requests injected as a load step, a burst, or requests thinned) and the CONSTRUCTED mixes of the two real
traces are marked as such. No runtime measurement; host-write reductions are replay numbers, not measured DRAM/CXL
interference. Previous round: `2026-10-21-rq1b-adaptive-admission.md`. Companion: `docs/research/rq1-consolidation-2026-10-21.md`
(the standalone RQ1 answer and the value-information interface).
Raw: `experimental_results/2026-10-21-rq1b-robust-admission/` (`val-*`, `g-*` focused grid, `reg-*` regime-rule
variants on the selection and the test half, `fin-*` / `findyn-*` the selected rule everywhere, `est-*` estimators,
`dyn-*` dynamic loads, `meta-*` bounded history under churn, `a-*` agent traces, `dump/` bitmaps / regime logs /
estimator logs / decision logs, `run_all.sh` the exact commands incl. the two mid-course corrections, figures
`fig-robust-*`). Code: `scripts/kv_admission_sim.py`, `kv_robust_tables.py`, `kv_robust_figs.py`.

## Setup
The simulator of the previous round with: a regime switch for the gap rule (`2nd_int_auto`: filter regime = `2nd_int`,
normal regime = admit every miss, structure LRU or SLRU; the rule is re-evaluated every 10 s from online statistics
only and must hold for a hysteresis time before a switch), seven residence estimators computed side by side (EWMA of
eviction ages 1/200 — the previous default —, faster 1/50 and slower 1/1000 EWMAs, EWMA of the ages of blocks evicted
*without a hit* ("dead"), capacity / admission rate, the age of the current LRU tail, the median of the last 200
eviction ages), estimator-accuracy logging (estimate at admission vs the block's realized residence when it is evicted
without a hit), CONSTRUCTED load changes, a prefix-semantics audit, and a per-decision log. Same traces, capacities
(52 / 105 / 210 / 419 / 839 GiB), tail-first order, usable-prefix scoring on the second half, first-half-only
selection of the one tunable (the regime rule), as before. **Validation:** `lru`, `slru`, `2nd`, `2nd_int`, `lhd`,
`oracle` reproduce the previous round to the block (`val-conversation-c3200`), and the audit holds for every policy:
no hit on a bypassed or evicted block, no resident block in the ghost, usable hits never counted behind a hole
(the 2Q / learned-class runs show 1–44 served-but-unusable tail blocks per run, correctly excluded).

## Task A — automatic regime adaptation (Deliverable 1; fig-robust-regime, `reg-*`, `fin-*`)
**A1 why `2nd_int` cannot avoid the loss by itself.** Its rule compares a re-seen block's last gap with the residence
of *admitted* blocks, which under the filter is long (858 s at 839 GiB), so it admits every re-seen block — but it never
admits a first touch, and the loss at large capacity is exactly the first reuse of refused first-touch blocks: at
839 GiB the filter still avoids 9.6k / 9.0k misses on blocks with ≥ 2 past uses (long gaps, age ≥ 300 s) but introduces
11.5k / 12.0k misses on blocks with one past use (55% / 65% of those accesses; per-access comparison, conversation /
tool agent), net −1.96k / −2.99k; at 210 GiB the same two numbers are 12.5k avoided vs 1.7–2.0k introduced. The
rule has no term for the value of an empty slot: when the LRU tail is 186 s old (839 GiB) admitting a first touch
costs nothing, when it is 42 s old (210 GiB) it costs a long-gap block.
**A2 what the previous round's replanned version used, and A3 whether it is observable.** The class tables: per
class (touch count × gap bucket …) the rate of admission candidates and the share of touches looked up again within
w ∈ {15 … 960 s} (policy-independent labels), the residence estimate, the capacity; it maximized Σ_k λ_k F_k(C / Λ)
over nested class sets. All of it is observable at runtime (lookups, stores, evictions, time; §C3) — but the model
over-admits because a re-lookup within the residence is not always a usable hit, and its configuration did not
transfer across halves (previous round). This round keeps only the two aggregates that the regime decision needs:
the candidate rates of first-touch and re-seen blocks and the re-lookup gap distribution.
**A4 the switch criterion.** Normal admission pays when the residence the cache *would* have if it admitted every
candidate, R_all = C / (λ_first + λ_reseen), is long enough to catch the first reuses: the rule compares R_all with
the online median of the re-lookup gap of **first-touch** blocks (`res_ft`, q = 0.5). Alternatives tested on the
selection half (requests 25–50%) and then on the test half: the same rule with the re-seen blocks' gap median (`res`;
q = 0.5 / 0.75 / 0.9), the predicted-hits comparison λ_f F_f(R_all) + λ_r F_r(R_all) ≥ (1 + m) λ_r F_r(R_filter)
(`model`; m = 0 / 0.1 / 0.3), hysteresis 0 / 30 / 120 s, and SLRU instead of LRU as the normal-regime structure.
Share of the oracle's usable-hit gain over LRU, test half (conversation / tool agent; `2nd_int` without a switch in
brackets):

| rule | 52 GiB | 210 GiB | 419 GiB | 839 GiB | switches |
|---|---|---|---|---|---|
| `res` q 0.5 (re-seen gap median) | 21 / 21% [21 / 21] | 33 / **0%** [33 / 32] | 10 / **0%** [23 / 21] | 0 / 0% [−10 / −19] | 2–4 / 1 |
| `res` q 0.75 | 21 / 21 | 33 / **0** | 23 / **0** | −14 / 0 | 2 / 1 |
| `res` q 0.9 | 21 / 21 | 33 / 33 | 22 / 21 | −10 / 0 | 2 / 2 |
| `model` m 0 / 0.1 / 0.3 | 21 / 21 | 0 / 0, 0 / 12, 33 / 33 | 0 / 0 | 0 / 0 | 1–2 |
| **`res_ft` q 0.5 (first-touch gap median)** | 21 / 21 | 33 / 32 | 22 / 21 | **0 / 0** (normal; SLRU structure +12 / +17) | 0 at ≤ 210 GiB; 4 at 419 GiB, all in the first 10 min; 1 at 839 GiB |
| `res_ft` q 0.75 / 0.9 | 21 / 21 | 33 / 32 | 23 / 21 | −10 / −19 (back to the filter) | 0–2 |
| `res` q 0.5 with SLRU as the normal structure | 26 / 24 | 35 / 5 | 15 / 1 | 12 / 17 | 2–4 / 1 |

- **The re-seen gap median is the wrong horizon.** On the tool-agent trace it is 15 s (most re-touches of re-seen
  blocks are immediate — the shared system prompt), so R_all (43–210 s) always exceeds it and the rule stays in
  normal admission from 105 GiB up (0% instead of 21–32%); on the conversation trace it is 86–97 s and the rule
  flaps at 419 GiB (4 switches, 10% instead of 23%). The predicted-hits model has the same bias (re-lookups counted
  as hits). **The first-touch gap median is the right one** (the question is whether first reuses will be caught):
  with it the rule never leaves the filter regime at 52–419 GiB on either trace (0 switches; 21–33% = `2nd_int`) and
  switches to normal admission at 839 GiB at 96–108 s (during warm-up, no flapping afterwards): 0 / 0% with LRU as the
  normal structure instead of −10 / −19%, +12 / +17% with SLRU. It was also first on the selection half (0% at 839 GiB
  vs −4 … −13% for q 0.75 / 0.9 and the re-seen rule). The 4 switches at 419 GiB (108 / 360 / 540 / 600 s on the
  conversation trace, 96 / 384 / 492 / 600 s on the tool-agent trace) all fall in the first 10 min while the
  first-touch gap statistics converge; none in the scored half.
- **Hysteresis** (0 / 30 / 120 s) changes nothing when the rule's inputs are far from the threshold (0 switches) and
  does not rescue a rule whose inputs sit near it (`res` q 0.5 at 419 GiB: 4 switches with every hold).
- **Normal-regime structure:** SLRU is the right structure for the normal regime — it is +13 / +16% above LRU at
  839 GiB because it keeps a second-touch priority inside the cache without refusing anything — and it also helps in
  the filter regime (35% vs 33% at 210 GiB, 26% vs 21% at 52 GiB on the conversation trace). With the selected rule
  and the SLRU structure the policy is above `2nd_int` at every capacity on both traces — 26 / 30 / 35 / 22 / 12% and
  24 / 30 / 34 / 21 / 17% at 52 / 105 / 210 / 419 / 839 GiB (`2nd_int` 21 / 29 / 33 / 23 / −10 and 21 / 26 / 32 / 21 /
  −19; SLRU alone 1 / 4 / 5 / 0 / 13 and 1 / 3 / 5 / 0 / 16) — and on the selection half (25–33% at 52–210 GiB, 16–18%
  at 419 GiB vs `2nd_int` 18–20%, 5–6% at 839 GiB vs −7 / −13%). The SLRU structure's probation segment is what makes
  a first touch cheap in the normal regime and a long-gap re-seen block cheap in the filter regime.
**A5–A6 adaptation under load changes (`findyn-*`; CONSTRUCTED; share of the run's oracle gain).** At 210 GiB the
rule stays in the filter regime through every scenario (0 switches): LRU structure 28 / 30 / 32 / 25% (step up /
step down / burst / thin, conversation) and 28 / 30 / 31 / 26% (tool agent) = `2nd_int`; SLRU structure 31 / 32 /
33 / 25% and 33 / 31 / 33 / 28%. At 839 GiB a doubled write stream (step up) makes filtering pay again (`2nd_int`
+17 / +19%): the rule re-enters the filter regime 14 min after the step on the conversation trace (then two short
flips; +5%) and not within the hour on the tool-agent trace (0%); when the extra load stops (step down) it returns
to normal admission in 10–14 min (switches at 1,340–1,650 s → filter and 2,475–2,715 s → normal; +4 / 0%); the burst
(2.4 min) triggers one switch on the conversation trace and none on the tool-agent trace. The SLRU-structured
version is never negative at 839 GiB (3–14% conversation, 9–21% tool agent; `2nd_int` −22 … +19%). The adaptation
time is set by the decay of the statistics (4τ = 20 min) and the hysteresis is irrelevant; a faster decay would
react faster and flap more — the rule errs on the conservative side (it stays in normal admission, i.e. at LRU /
SLRU, rather than filtering wrongly).

## Task B — stable residence estimation (Deliverable 2; fig-robust-est, `est-*`, `dyn-*`)
**B1 estimator accuracy (`2nd_int` driven by the previous default; the others in shadow; log10 of estimate at
admission / realized residence of that block when evicted without a hit; both traces agree within 0.01):**

| estimator | 52 GiB bias / within 2× | 210 GiB | 419 GiB | what it measures |
|---|---|---|---|---|
| EWMA of eviction ages 1/200 (previous default) | +0.09 / 89% | +0.12 / 97% | +0.11 / 99% | all evictions — blocks that were hit live longer, so it over-estimates by 1.3× |
| EWMA 1/50 | +0.08 / 83% | +0.11 / 94% | +0.10 / 94% | faster, noisier |
| EWMA 1/1000 | +0.09 / 94% | +0.12 / 99% | +0.11 / 100% | slower, smoother, same bias |
| **EWMA of dead-eviction ages** | **+0.01 / 90%** | **+0.00 / 100%** | **+0.01 / 100%** | the residence of a block that is not hit — the quantity the gap rule needs |
| capacity / admission rate | +0.12 / 90% | +0.15 / 98% | +0.15 / 97% | over-estimates by 1.4× (hits do not consume slots but admissions do) |
| **age of the LRU tail** | −0.01 / 86% | +0.00 / 100% | +0.00 / 100% | the next victim's age — instantaneous, no lag, nothing to tune |
| median of the last 200 eviction ages | +0.03 / 85% | +0.05 / 98% | +0.05 / 98% | robust but still includes hit blocks |

The two unbiased estimators are the dead-eviction EWMA and the LRU-tail age (mean |error| 0.04–0.07 in log10 at
≥ 210 GiB, i.e. ±10–17%; at 52 GiB ±30%, where the residence is 90 s and single requests of 20–60 blocks move it).
**Which estimator drives the rule makes almost no difference to the hits** (210 GiB, conversation / tool agent:
33 / 32% with every estimator; 419 GiB 20–23%; 52 GiB 18–22%) and a small one to the writes (dead and tail: 2.4–2.6 TB,
rate 2.7–2.9 TB): the gap rule's decisions sit far from the estimate for most blocks (§E: only 3–6% of its
admissions are lost to an over-estimate).
**B2 dynamic loads (CONSTRUCTED: +50 never-reused blocks / s from minute 36 = "step up" ≈ doubling the write
stream; the same from minute 15 to 36 then off = "step down"; +150 / s for 2.4 min = "burst"; half the requests
dropped from minute 36 = "thin"; 210 GiB; usable share / share of the run's oracle gain):**

| scenario | LRU | SLRU | `2nd` | **`2nd_int`** | TinyLFU (adapted) | oracle |
|---|---|---|---|---|---|---|
| conversation stable / burst / step down / step up / thin | 0.178 / 0.170 / 0.175 / 0.134 / 0.254 | 5 / 5 / 4 / 5 / 5% | 26 / 26 / 26 / 23 / 24% | **33 / 32 / 30 / 28 / 25%** | 27 / 21 / 21 / 21 / 14% | 0.797 / 0.786 / 0.798 / 0.793 / 0.851 |
| tool agent stable / burst / step down / step up / thin | 0.648 / 0.638 / 0.644 / 0.622 / 0.691 | 5 / 5 / 3 / 6 / 5% | 29 / 29 / 29 / 26 / 28% | **32 / 31 / 30 / 28 / 26%** | 24 / 22 / 20 / 20 / 16% | 0.940 / 0.936 / 0.940 / 0.935 / 0.957 |

The gap rule loses 2–8 points of the oracle's gain under the load changes (TinyLFU 6–13), writes 2.0–3.1 TB
(LRU 14–23 TB). Adaptation delay (time after the step until the estimate is within 20% of its new level; `2nd_int`,
210 GiB, both traces): step up — dead-eviction EWMA 0.8–1.1 min, tail age 0.7–0.8 min, EWMA 1/200 0.9–1.1 min, EWMA
1/50 0.5–0.7 min, EWMA 1/1000 1.6–1.9 min, capacity / rate 1.5–1.7 min (the residence falls from 223–228 s to
152–155 s under the doubled write stream); step down and burst — all estimators within 0.0–0.4 min (the level moves
by ≤ 30%). The admission rate under `2nd_int` follows the load with no oscillation: per 5-s window the lag-1
autocorrelation is 0.00–0.02 (LRU 0.12–0.15 — the request stream's own burstiness) and the coefficient of variation
0.88 reflects the bursty request arrivals, not the policy (fig-robust-dyn).
**B3 feedback between the estimate and the admissions.** The loop is negative: more refusals → fewer writes → longer
residence → more gaps fit → more admissions → shorter residence. With λ(R) the rate of re-seen candidates whose gap
≤ R (increasing in R) the fixed point R = C / λ(R) is unique, and the replay shows the rule converging to it rather
than oscillating: under `2nd_int` the admission rate per 5 s has no periodic component, the residence estimate
settles within ~2 residences after each load step, and the realized residence of the filter (234 / 231 s at 210 GiB)
is stable across the fifths. Fixed admission (`2nd`) has no loop (its estimate is passive) and its realized residence
(141 / 156 s) is below the gap rule's because it writes more. No smoothing, bounded updates or hysteresis were
needed for the gap rule; the regime switch is the only place where hysteresis matters (§A).

## Task C — bounded history and prefix semantics (Deliverable 3)
**C1 metadata cost.**
| structure | size | per-access cost | retention | errors |
|---|---|---|---|---|
| exact ghost, 16k entries | 0.5 MB (32 B / entry) | 1 lookup + 1 list move | 16k / new-hash rate = 310 s at 52 / s; 155 s at 100 / s | forgets 20–30% of second touches at 52 / s (21–29k of ~40k); under +50 / s churn 29–32k forgotten and the hit share 0.312–0.327 (unbounded 0.286–0.317) |
| exact ghost, 64k entries | 2 MB | same | 1,240 s | forgets 0.3–1.9k (4k under churn); = unbounded |
| Bloom 2 × 8 KB (65,536 bits, k 4, reset every 8k inserts) | 16 KB | 4 hash probes | ≈ 8–16k inserts (one reset period kept) | 11k false-positive admissions / hour (= first-touch blocks admitted; 0.339 / 0.723 = exact); under churn the filter fills twice as fast: 18k FP, 0.248 / 0.676 |
| residence estimator | one float (+ 8 B store time per resident block) | O(1) at eviction | – | §B |
| regime rule | 4 touch-count classes × 10 counters + the labels in flight (≤ 56k entries, 1.8 MB, bounded by the 960-s deadline) | O(1) per lookup; a 4-class evaluation every 10 s | – | §A |
Under a high unique-prefix arrival rate the ghost's retention shrinks with the write stream (new hashes per second),
not with the number of distinct prefixes; the gap rule with a 16k or 64k ghost keeps 0.31–0.33 / 0.71 of the usable
share under the +50 / s churn (0.38 / 0.74 without), the Bloom variant degrades more (its reset period is counted in
inserts) — a time-based reset would fix that.
**C2 prefix correctness (audit on every policy and capacity, `--audit`).** Lookups follow the contiguous prefix: a
hit counts only while every earlier block of the request was served, and the audit counts served-but-unusable tail
blocks separately (0 for the LRU-family policies, 1–44 per run for 2Q / learned class, excluded from the usable
share); a bypassed or evicted block never produces a hit (0 violations in 230 policy-capacity runs); the ghost and
the residency set are disjoint at every hit and at the end; first-touch bypass misses are counted as misses after a
refusal (27.1k / 23.7k of 115k / 114k scored misses for `2nd_int` at 210 GiB) and enter the recompute (59.0 / 58.1 M
tokens vs LRU 64.6 / 63.6 M, oracle 47.8 / 46.7 M); the ghost holds hashes, times and counts, never KV.
**C3 runtime feasibility (LMCache 0.5.5 / vLLM 0.31 source).** Block hashes: at request arrival the connector calls
`cache_engine.lookup(tokens | hashes)` for the tokens beyond vLLM's own prefix-cache hit, and after prefill the store
path (`token_database.process_tokens`, `_prefix_hash` over all chunks; the store mask selects what is written) has
every chunk's hash — so "seen before", the gap and the touch count can be updated at lookup (for the part vLLM did
not serve) and at store (for all chunks). Residence: `StorageBackendListener.on_evict(backend, keys)` is called with
the evicted keys; the resident entry's store time (8 B) gives the age; the LRU-tail age is the age of
`cache_policy`'s first candidate (`LRUCachePolicy.get_evict_candidates`), available at any time. Hits:
`LocalCPUBackend.contains` / `touch_cache` → `update_on_hit`. Minimal metadata: a ghost (16–64k entries or a Bloom
filter), per resident key a store time and a hit flag (9 B), one residence EWMA, four class counters. Directly
available events: lookup (hashes, time), store (hashes), eviction (keys), hit. Not observable at lookup time: blocks
served by vLLM's GPU prefix cache (they reach LMCache only on the store path; the previous round showed this leaves
the policies' gains unchanged); not observable at all: whether a request will be continued — only an agent runtime
can say (continue / end), which is the one application-side event the interface keeps optional.

## Task D — focused baseline comparison (Deliverable 4; fig-robust-grid)
Usable-prefix hit share / share of the oracle's usable-hit gain over LRU / TB written (test half; "64k" = bounded
ghost of 64k entries; `auto` = `2nd_int` with the selected regime rule `res_ft` q 0.5, LRU or SLRU as the normal
structure; `auto*` = the default rule of the first grid, `res` q 0.5, kept for comparison):

| capacity | LRU | SLRU | `2nd` | `2nd` 64k | `2nd_int` | `2nd_int` 64k | **auto (LRU)** | **auto (SLRU)** | auto* (`res` q 0.5) | TinyLFU | oracle |
|---|---|---|---|---|---|---|---|---|---|---|---|
| conversation 52 GiB | 0.117 / 18.5 | 1% | 5% / 6.1 | 5% / 6.0 | 21% / 1.8 | 21% / 1.8 | 21% / 1.8 | **26% / 1.7** | 21% | 13% / 2.4 | 0.446 / 2.9 |
| conversation 105 GiB | 0.130 / 18.4 | 4% | 11% / 5.6 | 12% / 5.5 | 29% / 2.3 | 29% / 2.3 | 29% / 2.3 | **30% / 2.2** | 29% | 21% / 2.1 | 0.610 / 3.2 |
| conversation 210 GiB | 0.178 / 18.0 | 5% | 26% / 4.6 | 27% / 4.4 | 33% / 2.6 | 33% / 2.6 | 33% / 2.6 | **35% / 2.6** | 33% | 27% / 1.8 | 0.797 / 3.2 |
| conversation 419 GiB | 0.376 / 16.5 | 0% | 22% / 3.6 | 22% / 3.5 | **23% / 2.8** | 23% / 2.8 | 22% / 3.9 | 22% / 3.9 | 10% / 11.5 | 4% / 1.8 | 0.967 / 3.0 |
| conversation 839 GiB | 0.624 / 14.8 | 13% | −9% / 3.0 | −9% / 2.9 | −10% / 2.9 | −10% / 2.9 | 0% / 14.3 | **12% / 14.1** | 0% | −55% / 2.4 | 1.000 / 3.0 |
| tool agent 52 GiB | 0.615 / 18.2 | 1% | 6% / 5.7 | 6% / 5.6 | 21% / 1.8 | 21% / 1.8 | 21% / 1.8 | **24% / 1.7** | 21% | 11% / 2.8 | 0.772 / 2.8 |
| tool agent 105 GiB | 0.624 / 18.0 | 3% | 14% / 5.1 | 13% / 5.1 | 26% / 2.3 | 26% / 2.3 | 26% / 2.3 | **30% / 2.2** | 0% / 17.6 | 17% / 2.9 | 0.851 / 3.1 |
| tool agent 210 GiB | 0.648 / 17.6 | 5% | 29% / 4.0 | 29% / 4.0 | 32% / 2.6 | 32% / 2.6 | 32% / 2.6 | **34% / 2.5** | 0% / 17.2 | 24% / 2.7 | 0.940 / 3.0 |
| tool agent 419 GiB | 0.748 / 16.1 | 0% | **24% / 3.0** | 23% / 3.0 | 21% / 2.8 | 21% / 2.8 | 21% / 4.1 | 21% / 4.1 | 0% / 15.7 | 1% / 2.4 | 1.000 / 2.6 |
| tool agent 839 GiB | 0.862 / 14.3 | 16% | −18% / 2.7 | −19% / 2.7 | −19% / 2.7 | −19% / 2.7 | 0% / 14.0 | **17% / 13.7** | 0% | −70% / 2.7 | 1.000 / 2.6 |
| SYNTHETIC 52 / 105 / 210 / 419 / 839 GiB | 0.133 … 0.776 | 1 / −1 / 5 / 6 / 5% | 1 / 4 / 5 / 12 / 16% | same | −2 / −6 / 3 / 1 / 12% | same | −2 / −6 / 3 / 1 / 0% | 0 / −4 / 1 / 2 / 6% | −2 / −6 / 3 / 3 / 0% | −7 / −9 / −12 / −30 / −33% | 0.382 … 1.000 |

(share of the oracle's usable-hit gain over LRU / TB written; LRU and oracle: usable share / TB.)

**Regimes.** Small cache (52–105 GiB): the gap rule, with or without the switch, is the best policy (21–29% on both real
traces; SLRU-structured 24–26% at 52 GiB); second touch alone 5–14%; TinyLFU 11–21%; SLRU / LRU 0–4%. Moderate cache
(210–419 GiB): the gap rule 21–33%, within 3 points of the best at 419 GiB (plain second touch 24% on the tool-agent
trace); TinyLFU falls to 1–4% at 419 GiB. Large cache (839 GiB): every refusing filter loses (−9 … −70%); the
switched rule is at LRU (LRU structure) or at SLRU's +12 … +17% (SLRU structure); ARC / SLRU are the right policies.
Stable vs changing workloads: §B2 (2–8 points lost under the load changes); the constructed phase change and the
interleaved mix: the switched rule stays in the filter regime (0 switches) at 32 / 27% (LRU structure) and 34 / 30% (SLRU) vs `2nd_int` 32 / 27%, TinyLFU 20 / 20%, SLRU 6 / 4%. SYNTHETIC trace: all history rules within −6 … +16% of LRU, TinyLFU −7 … −33%; the
switched rule stays in the filter regime up to 210 GiB and goes to normal admission at 419–839 GiB (0–3%).
Real agent traces (REAL, horizons of seconds; the rule's statistics cannot converge on 100–140-s traces with τ 30 s): the
rule switches to normal admission on both traces at every capacity — short-tool trace = LRU (0%; no harm, where
`2nd_int` is −124 … −345% at 32–48 chunks; SLRU structure −11 … +1%), long-tool trace with churn 32 / 18 / −214% at
24 / 32 / 48 chunks (SLRU structure 51 / 33 / −221%) vs `2nd_int` 55 / 37 / −229% and TinyLFU 70 / 55 / −79% — the
switch fires where filtering still pays (24–32 chunks) and does not prevent the loss at 48 chunks within the trace;
at the second timescale the capacity-vs-live-set criterion of the 2026-10-17 round remains the usable one, and the
2026-10-20 learned class policy the only online rule positive at 48 chunks.

## Task E — mechanism and error analysis (Deliverable 5; per-access bitmaps, `kv_hits_compare.py` / `kv_hits_explain.py`, decision logs)
1. **Hits from less pollution vs hits lost to over-filtering (210 GiB, conversation / tool agent).** Against LRU the
   gap rule avoids 12,526 / 12,551 misses and introduces 1,658 / 1,968 (net +10,868 / +10,583); the avoided misses are
   on blocks with 2–4 past uses (46–48% of those accesses) and 5+ (6–32%), ≥ 300 s old (23% / 8%) or 60–300 s old
   (29%); every introduced miss is the second touch of a refused first-touch block (7–9% of the accesses to blocks
   with one past use). Plain second touch: +8,495 / +9,619; TinyLFU +8,771 / +7,747 (introduces 1,944 / 2,354);
   SLRU +1,648 / +1,520 (all after evictions: it reorders, it does not refuse).
2. **At 839 GiB the balance inverts** (§A1: 9.6k / 9.0k avoided vs 11.5k / 12.0k introduced, net −2.0k / −3.0k for the
   gap rule; TinyLFU −11.0k / −10.8k); the switched rule reproduces LRU exactly (0 avoided, 0 introduced) with the
   LRU structure, and SLRU's +2.6k / +2.5k with the SLRU structure — the regime switch removes the large-cache loss
   entirely, and costs nothing at ≤ 419 GiB (0 switches there).
3. **Residence-estimation error → wrong admissions (decision logs, `2nd_int`, estimator `evict`).** Of the re-seen
   candidates it admits, 34–38% are hit before eviction at 210–419 GiB (20% at 52 GiB) and 3–6% are evicted before a
   next use that the estimate said would fit (the over-estimate's cost); of the candidates it refuses, 50–71% are
   never reused, and 15–49% come back within the estimated residence — those are refused because their *last* gap
   was long although the *next* gap was short: the last gap, not the estimate, is the weaker predictor (it is within
   2× of the next gap for 59–73% of blocks).
4. **Ghost forgetting** turns a re-seen block into a first touch: with 16k entries 21–29k of ~40k second touches per
   hour are forgotten (31–47k under churn), yet the hit share is equal or higher at ≤ 210 GiB because the forgotten
   blocks are the long-gap ones the rule would refuse anyway; at 419 GiB it costs ≤ 0.01.
5. **Online-information errors vs policy errors.** Information: the first-touch cost (no first-touch class above a
   21% re-lookup rate within the residence; 62–80% of the remaining gap) and the dead half of second-touch admissions
   (no separating feature) — not fixable by a better policy; the next gap of long-gap blocks (2× accuracy) — partly.
   Policy: the regime decision (fixed by the first-touch-gap rule), the over-estimate (3–6%), the normal-regime
   structure (SLRU > LRU). Not an error of either: the synthetic trace (memoryless reuse, nothing to learn).

## Metrics (test half, 210 GiB; conversation / tool agent)
| policy | usable share | net usable hits vs LRU | recompute (M tokens) | oracle gain | useful admission | false admission | false bypass (≤ 300 s) | residence p50 (s) | admissions | TB written | metadata |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LRU | 0.178 / 0.648 | – | 64.6 / 63.6 | – | 33 / 31% | 67 / 69% | – | 42 | 268.6k / 262.7k | 18.0 / 17.6 | – |
| SLRU 1/3 | 0.209 / 0.661 | +1,648 / +1,520 | 63.7 / 63.0 | 5 / 5% | 33 / 31% | 67 / 69% | – | 30 | 264.2k / 258.8k | 17.7 / 17.3 | – |
| second touch (64k ghost) | 0.346 / 0.732 | +8,857 / +9,513 | 60.0 / 58.7 | 27 / 29% | 49 / 51% | 51 / 49% | 31.6k / 31.6k | 144 / 156 | 65.5k / 59.8k | 4.4 / 4.0 | 2 MB |
| **`2nd_int` (64k ghost)** | **0.384 / 0.742** | **+10,868 / +10,583** | **59.0 / 58.1** | **33 / 32%** | 49 / 49% | 51 / 51% | 39.1k / 39.3k | 234 / 231 | 39.5k / 39.3k | 2.6 / 2.6 | 2 MB + 1 EWMA |
| `2nd_int` + regime switch (`res_ft`, LRU) | 0.384 / 0.742 | +10,868 / +10,583 | 59.0 / 58.1 | 33 / 32% | 49 / 49% | 51 / 51% | 39.1k / 39.3k | 234 / 231 | 39.5k / 39.3k | 2.6 / 2.6 | 2 MB + 1 EWMA + 4 class counters |
| **`2nd_int` + regime switch (`res_ft`, SLRU)** | **0.395 / 0.748** | **+11,439 / +11,270** | **58.7 / 57.8** | **35 / 34%** | 48 / 48% | 52 / 52% | 39.3k / 39.3k | 180 / 183 | 38.2k / 37.9k | 2.6 / 2.5 | same + SLRU's two lists |
| TinyLFU (adapted) | 0.344 / 0.716 | +8,771 / +7,747 | 60.1 / 59.6 | 27 / 24% | 43 / 38% | 57 / 62% | 47.0k / 44.9k | 357 / 249 | 26.8k / 40.0k | 1.8 / 2.7 | ≤ 32k counters |
| oracle | 0.797 / 0.940 | +32,683 / +32,932 | 47.8 / 46.7 | 100% | 100% | 0% | 0.3k | 150 / 162 | 47.5k / 44.3k | 3.2 / 3.0 | the future |

## Deliverables 6 and 7
The standalone RQ1 consolidation and the value-information interface are in
`docs/research/rq1-consolidation-2026-10-21.md`. Gate 2: unchanged thresholds; still **PARTIAL** (best online policy
32–35% of the oracle's usable-hit gain at 210 GiB, 21–29% at 52–105 / 419 GiB, error cost 13–16% of the gain).
