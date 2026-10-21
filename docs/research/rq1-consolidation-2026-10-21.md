# RQ1 consolidation report — is future reuse information valuable and predictable? (2026-10-21)

**Scope.** This document consolidates the RQ1 rounds of 2026-10-17 … 2026-10-21 into one standalone answer. It
separates **information quality** (what the host can know about a KV block's future reuse, and how accurately) from
**policy effectiveness** (what a cache does with it). Every number is a trace-driven replay or a trace statistic
unless marked REAL (measured on c28) or ORACLE (uses the future). Host-write reductions are replay quantities, not
measured DRAM/CXL interference. Gate 2 is judged against the CHARTER's unchanged thresholds. The round reports with
the raw data are listed at the end; the value-information interface for RQ2 is the last section.

## 1. How much theoretical value does the oracle prove? (ORACLE)
A Belady-with-bypass oracle (admit only blocks that will be reused before they would be evicted) on the real
Mooncake traces at 210 GiB serves 80% / 94% of the reuse accesses (conversation / tool agent) against 17% / 65% for
the best capacity-matched baseline (2026-10-17 oracle study), i.e. a usable-prefix hit share of 0.797 / 0.940 vs
LRU's 0.178 / 0.648 (2026-10-21), −26 … −43% recomputed tokens, −70 … −83% host writes. Gate 1 passed on all three
criteria. The source of the value is one fact: 58–79% of the blocks written by LRU are never read again, and a cache
that refuses them keeps the others 3–4× longer. The value scales with capacity pressure: at 839 GiB the oracle is at
1.000 and LRU at 0.62–0.86; at 52 GiB the oracle is 0.45 / 0.77 vs LRU 0.12 / 0.62.

## 2. Which future reuse information cannot be predicted reliably?
- **The first reuse of a new block.** Among the blocks a request creates, 16–24% will be read again; nothing available
  at creation separates them: request features give a lift ≤ 1.25 (position, length, prefix, root), chronological
  predictors reach an average precision ≤ 1.3× the base rate (2026-10-18 history round), and the share of first touches
  re-looked-up within a realistic cache residence is 16–21% for the best class (fresh request, first 8 blocks) and
  5–14% for the rest (2026-10-21). A perfect "this session continues" hint would recover 40–54% of the oracle's gain
  (ORACLE, 2026-10-17 session-hint study); every realistic chat-side signal recovered 0%.
- **Which second-touch admissions will die.** 49–52% of the blocks admitted at their second touch are never read again
  and no feature of their past (touch count 1, last gap, position, request type, sharing) separates them (hindsight
  re-lookup rates 31–35% within the residence for every short-gap class).
- **The next gap of a long-gap block.** The last inter-touch gap predicts the next within 2× for 59–73% of the blocks;
  for gaps beyond twice the residence, 10–20% of refused blocks come back in time (2026-10-21).
- **Popularity.** It does not persist: 9–18% of a 5-minute window's top-100 blocks stay in the next window.
- **Synthetic (memoryless) reuse.** On the SYNTHETIC Mooncake trace every history-based rule is within ±6% of LRU.

## 3. Which historical information can be obtained online?
All of the following is observable from the host cache's own events (LMCache 0.5.5 source, §8), with the labels
verified policy-independent (identical statistics under LRU, second touch and the oracle):
- whether a block's hash was looked up before (ghost history: exact 16–64k entries, 0.5–2 MB, or a 2 × 8 KB
  double-buffered Bloom filter);
- the time since that lookup (the block's last gap) and the number of past touches;
- the cache's residence (age of blocks at eviction: EWMA of the ages of blocks evicted without a hit, or the age of
  the current LRU tail — both unbiased, within 2× of the realized residence for 100% of admissions at ≥ 210 GiB,
  86–90% at 52 GiB);
- per class (touch count × gap), the rate of re-lookups within w seconds (policy-independent labels: a touch at t0
  is labelled by whether the hash is looked up again by t0 + w, for both admitted and refused blocks);
- the request structure at the touch (position in the request, existing-prefix length);
- for agent workloads only, the runtime's continue / end decision (REAL: timely and block-exact, 2026-10-17).

## 4. Why are second touch and the reuse interval valuable?
Because they encode the two facts behind the oracle's gain. (i) Most new blocks are dead: refusing first touches
removes 69–77% of host writes and lengthens the LRU residence from 42 s to 123–234 s at 210 GiB — one reuse horizon
(the next use of a reused block comes ~105 s after LRU would have evicted it). (ii) A block that was looked up twice
is reused predictably (average precision 0.75–0.99 for observed blocks vs 0.20–0.65 base), and *when* it will be
reused is predicted by its last gap: within the residence for 31–35% of short-gap blocks vs 10–17% of long-gap ones.
"Admit a re-seen block only if its last gap fits the current residence" (`2nd_int`) therefore admits the blocks the
cache can actually keep until their reuse. Its information quality: useful-admission rate 49–53% (LRU 31–33%, oracle
100%), false bypass 17–19% of refusals reused within 300 s, residence-estimate error < 2× for 97–100% of admissions;
only 3–6% of its admissions are lost to an over-estimated residence.

## 5. Why does adaptive admission beat fixed policies under some conditions, and not others?
The value of refusing first touches depends on one ratio: the residence the cache would have if it admitted
everything, against the horizon at which blocks come back. Below that point (52–419 GiB on the Mooncake traces) the
gap rule returns 21–33% of the oracle's usable-hit gain with 1.8–2.8 TB written (LRU 16–19 TB) and is the best or
within 2–3 points of the best policy; it beats the strongest existing admission policy (TinyLFU, adapted) by 6–20
points and the 2026-10-20 learned class policy by 6–14 points, identically on the selection and the test half. The
adaptation inside that regime is the residence estimate: at 52 GiB the rule refuses 71% of the re-seen admissions
plain second touch makes (residence 30 → 90 s, hit share 0.132 → 0.185). Above that point (839 GiB: the LRU residence
of 186 s already covers the median first-reuse gap) every refusing filter loses — second touch −9 / −18%, the gap
rule −10 / −19%, TinyLFU −55 / −70% — because the first reuses it refuses (11.5–12.0k lost hits at 839 GiB) outnumber
the long-gap reuses it protects (9.0–9.6k); non-refusing policies with a second-touch priority (SLRU +13 / +16%,
ARC +13 / +18%) are right there. The regime rule of the 2026-10-21 robust-admission round makes that switch
online: compare the residence the cache would have if it admitted every candidate, C / (λ_first + λ_re-seen), with
the online median re-lookup gap of first-touch blocks; filter below, admit everything above (30-s hysteresis). It
keeps the filter at 52–419 GiB (no switch in the scored half, 21–33%) and goes to normal admission at 839 GiB on both
traces — 0% with an LRU structure, +12 / +17% with an SLRU structure, which also lifts the filter regime to 24–35% —
selected on the first half and confirmed on the second. The re-seen gap median (dominated by immediate re-touches) and
a predicted-hits model are the wrong criteria. The rule is conservative after a load step at large capacity (it
re-enters filtering 14 min after a doubled write stream on one trace and not within the hour on the other) and does
not work at the second timescale of the agent traces.

## 6. In which cache regimes is the information reliable?
- **Reliable (filtering pays):** host caches whose admit-all residence is below the first-reuse gap median —
  52–419 GiB for the Mooncake traces (gap p50 123–147 s, p90 480–620 s, LRU residence 9–87 s); both real traces, the
  constructed interleaved and phase-change mixes (27–32%), with a 16k- or 64k-entry ghost or a Bloom filter, under
  a doubled unique-prefix arrival rate (the ghost's retention shrinks with the write stream, not with the prefix
  count), after a cold start (the gap rule needs ~200 evictions), and across the estimator choices (33–34% at
  210 GiB whichever estimator drives it).
- **Unreliable or useless:** first-touch value (always ~16%); the synthetic memoryless trace (±6%); real agent caches
  that hold the live working set (48 chunks: every filter −80 … −345%); frozen statistics after a phase change (0%).

## 7. When must the cache fall back to normal admission?
When the residence that admitting everything would produce is at or above the horizon at which refused blocks come
back: on the Mooncake traces at 839 GiB (admit-all residence 186–209 s vs first-reuse gap p50 123–147 s), on the real
agent traces once the capacity holds the live set (48 chunks), and whenever the ghost cannot retain one reuse horizon
of hashes (< 8k entries at 52 new hashes / s). The online test is the regime rule above; it fires at 839 GiB on the
Mooncake traces (admit-all residence 186–209 s vs a first-touch gap median of ~90–100 s) and keeps filtering below;
its fallback should be SLRU rather than LRU (second-touch priority without refusal). At the agent timescale
(traces of 100–140 s) the rule's statistics do not converge; the capacity-vs-live-set criterion of 2026-10-17 applies.

## 8. What metadata and runtime events does deployment need? (LMCache 0.5.5 / vLLM 0.31, source inspection)
| need | source in LMCache | when available | cost |
|---|---|---|---|
| chunk hashes of a request | `cache_engine.lookup(tokens / hashes)` at request arrival (`vllm_v1_adapter` calls it for the tokens beyond vLLM's own prefix-cache hits); the store path (`token_database.process_tokens`) computes the prefix hash of **every** chunk after prefill, the store mask only selects which are written | lookup: arrival; store: after prefill | already computed |
| "seen before", last gap, touch count | ghost history keyed by the chunk hash, updated at lookup / store (and at eviction, when the resident entry moves to the ghost) | first lookup = creation; gap after the second | 16–64k entries × 32 B (0.5–2 MB) or a 2 × 8 KB double-buffered Bloom filter (no gap, membership only); O(1) per block |
| residence | eviction ages: `StorageBackendListener.on_evict(backend, keys)` fires with the evicted keys; the resident entry's store time is kept by the backend (`LocalCPUBackend.hot_cache`, `cache_policy.update_on_put / update_on_hit / get_evict_candidates`) | every eviction (lag = one residence); the LRU-tail age is available at any time | one EWMA; 8 B store time per resident key |
| hits / hit before eviction | `LocalCPUBackend.contains` / `touch_cache` → `cache_policy.update_on_hit` | at lookup | flag per resident key |
| class re-lookup rates (optional) | the lookups above, labelled by the next lookup of the same hash or a 960-s deadline | 2 min delay (p50) | 4–13 classes × 10 counters; ≤ 56k labels in flight (1.8 MB) |
| agent continue / end (optional, agents only) | the application (OpenAI Agents SDK / LangGraph loop), relayed as an event; the `MP_VLLM_END_SESSION` channel exists for end | at the decision, before the next request (REAL: 0.4 s after the last KV write) | none |
Not observable at lookup time: blocks served by vLLM's GPU prefix cache (they never reach the LMCache lookup) — they
are visible on the store path, and with a 34–69 GiB GPU cache in front the policies' gains are unchanged (±0.002)
while the host's own hit share falls (LRU 0.178 → 0.06). Not observable at all: the request's future (continuation),
except through the agent hint.

## 9. What information gaps remain?
At 210–419 GiB the gap rule leaves 67–80% of the oracle's remaining gain in the first-touch cost (blocks whose first
reuse is a miss because the first touch was refused — information the host does not have), 12% in blocks admitted
but evicted before a long-gap reuse (the dead half of second-touch admissions — no separating feature), and ≤ 20% in
long-gap re-seen blocks refused by the gap rule (the last gap is a 2×-accurate predictor). Nothing in the remaining
gap is a model limitation that more history would fix; the first-touch part needs the application, the dead-admission
part has no observable predictor.

## 10. Gate 2 and the overall RQ1 answer
**RQ1: future reuse information is valuable (Gate 1 PASS) and the part of it that is predictable online is the
reuse of already-seen blocks, timed by their last gap against the cache's residence; the reuse of new blocks is not
predictable by the host.** Gate 2 (a predictor using only past-observable features, fitted on segment 1 and evaluated
on segment 2, must capture ≥ 50% of the oracle's gain with error cost ≤ 25% of that gain): the best online policy
captures 32–33% of the oracle's usable-hit gain at 210 GiB and 21–29% at 52–105 / 419 GiB, with an error cost of
13–16% of the gain (introduced misses 1.7–2.0k vs avoided 12.5k at 210 GiB) — the second criterion is met, the first
is not: **Gate 2 remains PARTIAL**, as in every round since 2026-10-17; the missing information is named (§2, §9).
Policy effectiveness and information quality are different things: the 33% is bounded by the first-touch gap, not by
the quality of the second-touch signal (useful-admission rate 49–53%, residence estimate within 2×).

## Value-information interface for RQ2 (what the runtime can hand to a unified manager; not a design)
Per KV block (LMCache key = model / worker / chunk prefix hash, which identifies the block's position in its prefix
chain):

| field | meaning | available at | source | error / limitation |
|---|---|---|---|---|
| `seen_before` | the hash was looked up at least once before | block creation (first lookup / store) | ghost history or Bloom filter | Bloom false positives = spurious "seen" (≈ 2% at 8 KB × 2, reset every 8k inserts; 16% at 4 KB — harmful); exact ghost forgets after N / new-hash-rate seconds (16k entries = 310 s at 52 /s) |
| `touches` | number of past lookups (0, 1, 2, 3+) | creation (0) / after each lookup | ghost + resident metadata | capped; forgotten after ghost eviction |
| `last_gap` | seconds since the previous lookup | needs ≥ 1 past lookup | ghost timestamp | predicts the next gap within 2× for 59–73% |
| `residence_window` | expected time a newly admitted block stays if not hit | cache-level, updated at each eviction (or read from the LRU tail) | EWMA of dead eviction ages / LRU-tail age | unbiased; within 2× for 100% (≥ 210 GiB), 86–90% (52 GiB); follows a doubled write stream within 0.7–1.1 min at 210 GiB |
| `reuse_class` | first touch / re-seen with `last_gap` ≤ `residence_window` / re-seen with longer gap / hot (3+ touches) | creation / after lookups | the two fields above | hindsight re-lookup rate within the residence: 8–21% / 31–35% / 10–20% / similar to the gap class |
| `admission_value` | the gap rule's decision: admit iff `touches` ≥ 1 and `last_gap` ≤ `residence_window` (always admit in the normal regime) | at the store decision | rule | useful-admission rate 49–53% (LRU 31–33%); error cost 13–16% of the gain |
| `reuse_rate[w]` (optional) | per class, share of touches looked up again within w ∈ {15 … 960 s} | after ~50 labelled touches per class; labels resolve at the next lookup or 960 s | policy-independent labels | coarse (4–13 classes); not a calibrated per-block probability — the per-block first-touch probability is ~16% with no usable lift |
| `regime` | filter / normal, from the admit-all residence vs the first-touch re-lookup gap median | cache-level, re-evaluated every 10 s, 30-s hysteresis | candidate rates of first-touch and re-seen blocks + their re-lookup CDFs (4 classes) | ≤ 1 switch per hour in the scored half at 52–839 GiB; after a load step it re-enters filtering only after 10–20 min (the statistics' decay) or not at all — errs toward normal admission; needs minutes of history, not usable on 100-s traces |
| `lifecycle` (agents only) | the agent loop's continue / end for the request's context | at the loop's decision | the application | 100% of the context is re-read after "continue"; useless for chat; helps only under capacity pressure (2026-10-17) |
What is **not** provided: a calibrated probability of reuse for a new block (the host has none); a retention value
beyond recency; anything about the request's future for chat workloads.

## Round reports (raw data under `experimental_results/`)
`docs/experiments/2026-10-17-kv-reuse-oracle-study.md` (Gate 1), `2026-10-17-kv-session-hint-study.md`,
`2026-10-17-rq1b-application-reuse-signals.md`, `2026-10-17-rq1b-agent-runtime-validation.md` (REAL agent runs),
`2026-10-17-rq1b-reuse-horizon.md`, `2026-10-18-rq1-misscost-feasibility.md` (REAL TTFT microbenchmark),
`2026-10-18-rq1b-history-learning.md`, `2026-10-20-rq1b-admission-study.md`, `2026-10-21-rq1b-adaptive-admission.md`,
`2026-10-21-rq1b-robust-admission.md`; decision log `docs/research/decision-2026-10-17.md`; charter
`docs/research/CHARTER.md`.
