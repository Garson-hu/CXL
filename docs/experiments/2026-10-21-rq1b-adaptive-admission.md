# 2026-10-21 — RQ1-B: practical and adaptive reuse-aware admission — bounded ghost history, adaptive admission, strong baselines, feedback correctness, oracle gap

**STATUS: CLOSED (2026-10-21).** Verdict: the second-touch benefit survives a bounded history — a ghost of one reuse
horizon of hashes (16k entries ≈ 310 s ≈ 0.5 MB, or a 2 × 8 KB double-buffered Bloom filter) is as good as or better
than the unbounded set, because forgetting implements a gap filter. The one online quantity that makes admission
adaptive is the **cache residence estimate**: the rule "admit a re-seen block only if its last gap fits the current
residence" (`2nd_int`, no parameter) is the best or within 2–3 points of the best policy from 52 to 419 GiB on both
real traces (21–33% of the oracle's usable-hit gain, 1.8–2.8 TB written vs LRU's 16–19 TB), the same on the selection
half and the test half, and on the constructed mixes (27–32%); it beats the strongest existing admission policy
(TinyLFU, adapted) by 6–20 points at every capacity ≤ 419 GiB and the 2026-10-20 learned class policy by 6–14 points. Class tables with policy-independent "looked-up-again" labels learn correctly (identical
under LRU, second touch and the oracle; no censoring, no exploration) but add nothing over the gap rule at ≤ 419 GiB
and write 2–3× more; their configuration (decay, classes, threshold) chosen on the first half did not carry to the
test half (14–31% vs the gap rule's 21–33%; −37 / −51% at 839 GiB), and their one advantage — not refusing first
touches where capacity covers the reuse horizon — holds only for the replanned-threshold variants (839 GiB: −6 … +10%
while every fixed filter is −9 … −70%; short-tool agent trace at 48 chunks: 0% vs −303%; long-tool trace with churn:
−57% vs −229%, where only the 2026-10-20 learned class policy stays positive). The remaining oracle gap at 210–419 GiB is
62–80% the first-touch cost (no first-touch class has more than a 21% chance of a re-lookup within the residence —
information the host does not have), 12–30% blocks admitted but evicted before a long-gap reuse (capacity / dead-block
pollution), ≤ 10% long-gap re-seen blocks refused. Gate 2 stays **PARTIAL** (32–33% at 210 GiB).

Evidence types: **TRACE-DRIVEN REPLAY** (new simulator `scripts/kv_admission_sim.py`, validated to the block against the
2026-10-20 replay), **OFFLINE DECISION AUDIT** (per-access bitmaps, admission dumps, class-table dumps), **ORACLE**
(Belady with bypass), **TRACE STATISTICS**, **SOURCE INSPECTION** (LMCache 0.5.5). No runtime measurement; host-write
reductions are replay numbers, not measured DRAM/CXL interference. Previous round: `2026-10-20-rq1b-admission-study.md`.
Raw: `experimental_results/2026-10-21-rq1b-adaptive-admission/` (`val-*` validation, `g-*` main grid, `gh-*` ghost
bounds, `ab-*` ablations, `tune-*`/`tune2-*` first-half selection (+ `tune2-selection.md`), `sel-*` test-half runs of
the selected configurations, `m-*` constructed mixes, `a-*` real agent traces, `gpu-*` GPU front cache, `sh-*` shadow
tables, `ghost-stats-*.json`, `dump/` bitmaps / admission dumps / plan logs / tables, `run_all.sh` the exact commands,
figures `fig-adm-*`). Code: `scripts/kv_admission_sim.py`, `kv_ghost_stats.py`, `kv_gap_classes.py`,
`kv_shadow_compare.py`, `kv_adm_tables.py`, `kv_adm_figs.py`.

## Setup
**Simulator.** `kv_admission_sim.py` keeps the semantics of `kv_agent_replay.py`: one host KV cache of `cap` blocks
(8B Mooncake blocks of 512 tokens = 67.1 MB; 800 / 1,600 / 3,200 / 6,400 / 12,800 blocks = 52 / 105 / 210 / 419 /
839 GiB), LMCache / vLLM order (a request's blocks are touched tail-first at request end so the tail is evicted
first), prefix-aware scoring (a hit counts only while every earlier block of the request hit; all shares below are
**usable-prefix** shares and the oracle-gain shares are computed on usable hits), the second half of the requests
scored (the first half warms the cache and every online statistic), writes counted in the scored half, residence =
write → eviction, the miss-cost model of the 2026-10-18 round. **Validation (Task G):** `lru`, `slru`, `2nd`
(= `static_2nd1`), `lhd` and `oracle` reproduce the 2026-10-20 numbers exactly — conversation 210 GiB: 9,413 / 11,061 /
17,908 / 16,603 / 42,096 hits, 268,621 / 264,200 / 67,858 / 83,160 / 47,476 writes, residence 42 / 30 / 141 / 123 /
150 s (`val-conversation-c3200.log`); real agent trace at 24 / 48 chunks: 1,007 / 1,100 (LRU), 1,066 / 1,068 (second
touch), 1,071 / 1,108 (learned class) hits — identical.
**Policies (same capacity, order, prefix semantics, scoring; metadata stated in §C).** Replacement policies that write
every miss: `lru` (= first-touch admission), `slru` (1/3 protected), `2q` (Johnson & Shasha: A1in FIFO 25%, A1out ghost
50%, Am LRU), `arc` (Megiddo & Modha, adaptive p, ghosts B1/B2), `wtinylfu` (1% window LRU + SLRU 20/80 main, TinyLFU
admission from the window). Admission filters on an LRU cache: `tinylfu` (adapted: no window — a window would be host
writes; candidate frequency vs the LRU victim's, exact 4-bit counts halved every 10 × capacity accesses, doorkeeper for
first occurrences), `2nd` (second touch: admit only hashes looked up before), `2nd_int` (second touch + the block's
last gap ≤ the online residence estimate), `adapt2` (two classes, first touch / re-seen; first-touch admission is
switched on when the predicted hit rate with it exceeds the one without), `adaptive` (class tables, below), `lhd`
(the 2026-10-20 learned class policy, corrected), and the block `oracle`. A request's first block is always admitted.
**Ghost history.** Hashes not resident, with last-touch time and touch count: unbounded, or an exact LRU list of N
entries, or a TTL, or a double-buffered Bloom filter (membership only). It holds past lookups, never data; a ghost hit
is an admission signal, never a KV hit. The ghost is fed from every request block (LMCache's store path computes every
chunk hash, §G); `--ghost-src host` restricts it to lookups that reach the host.
**Online quantities.** Residence estimate = exponentially weighted mean of the age of evicted blocks (200-eviction
window; `--res-mode rate` = capacity / admission rate instead); per block: touches so far and the gap since the previous
touch (from the ghost / residency metadata); class tables: for every touch of class k, whether the same hash is looked
up again within w for w ∈ {15, 30, 60, 120, 240, 480, 960 s} (resolved at the next lookup or at t + 960 s — a
**policy-independent** label), plus the decayed rate of admission candidates per class; a hierarchical prior
(leaf → ancestors, 10 pseudo-samples); decay 4τ. `adaptive` admits a candidate iff P̂(re-lookup within the residence |
class) ≥ θ, where θ is replanned every 10 s as the threshold that maximizes the predicted hit rate Σ_k λ_k F_k(C / Λ)
over nested class sets (or a fixed θ in the ablations), and refuses a block whose predecessor in the request was just
refused (chain rule). Classes = (touch count 0/1/2/3+, gap bucket, position bucket, existing-prefix bucket) by default;
ablated below.
**Protocols.** Parameter selection strictly on the FIRST half (scored requests 25–50%, cache warmed on 0–25%;
`tune*-*`), then one test on the second half (`sel-*`); walk-forward fifths of the scored half; `--freeze-at 0.2`
(statistics frozen after 20% of the trace); `--cold-start` (ghost and tables cleared at the first scored request).

## Task A — practical bounded ghost history (Deliverable 1; fig-adm-gaps, fig-adm-ghost)
**A1 how long the history must be (trace statistics, `ghost-stats-*.json`).** First-to-second-touch gaps: conversation
p50 / p90 / p99 = 147 / 621 / 2,292 s, tool agent 123 / 477 / 648 s, SYNTHETIC 153 / 454 / 715 s. New hashes arrive at
52 / s (both real traces), so an exact ghost of N entries remembers a hash for N / 52 s: 4k = 77 s, 8k = 155 s,
16k = 310 s, 32k = 620 s, 64k = 1,240 s. Share of second touches a ghost of N entries still recognizes (stack distance
in new hashes ≤ N): conversation 4k 26% / 8k 51% / 16k 71% / 32k 92% / 64k 97%; tool agent 29 / 57 / 80 / 99 / 99%.
Later touches are closer (second → third p50 138 / 126 s; later 72 / 0 s). Real agent trace: gaps p50 3.6 s, p90 12 s,
1.3 new hashes / s — any ghost ≥ 100 entries is unbounded in effect.
**A2–A3 ghost capacity vs admission and hits (`gh-*`; second touch unless stated; usable share / share of the oracle's
gain / TB written / re-lookups the ghost had forgotten).**

| capacity | ghost | conversation: `2nd` | conversation: `2nd_int` | tool agent: `2nd` | tool agent: `2nd_int` |
|---|---|---|---|---|---|
| 52 GiB | 1k entries | 0.140 / 7% / 0.0 / 90,039 | 0.140 / 0.0 | 0.629 / 9% / 0.1 / 83,708 | 0.629 / 0.1 |
| 52 GiB | 4k | 0.198 / 25% / 0.7 / 72,335 | 0.196 / 0.7 | 0.653 / 24% / 0.8 / 66,003 | 0.653 / 0.7 |
| 52 GiB | 16k | 0.147 / 9% / 4.1 / 27,290 | **0.185 / 21% / 1.8** | 0.630 / 10% / 4.2 / 20,320 | **0.648 / 21% / 1.8** |
| 52 GiB | 64k | 0.134 / 5% / 6.0 / 2,009 | 0.185 / 21% / 1.8 | 0.625 / 6% / 5.6 / 359 | 0.648 / 21% / 1.8 |
| 52 GiB | unbounded | 0.132 / 5% / 6.1 | 0.185 / 21% / 1.8 | 0.625 / 6% / 5.7 | 0.648 / 21% / 1.8 |
| 210 GiB | 4k | 0.275 / 16% / 0.6 / 67,751 | 0.275 / 0.6 | 0.696 / 16% / 0.7 / 60,220 | 0.696 / 0.7 |
| 210 GiB | 16k | **0.391 / 34% / 2.9 / 21,444** | **0.391 / 34% / 2.5** | **0.746 / 34% / 3.0 / 14,516** | **0.744 / 33% / 2.6** |
| 210 GiB | 64k | 0.346 / 27% / 4.4 / 1,962 | 0.384 / 33% / 2.6 | 0.732 / 29% / 4.0 / 321 | 0.742 / 32% / 2.6 |
| 210 GiB | unbounded | 0.339 / 26% / 4.6 | 0.384 / 33% / 2.6 | 0.733 / 29% / 4.0 | 0.742 / 32% / 2.6 |
| 419 GiB | 4k | 0.281 / −16% / 0.6 | 0.281 / 0.6 | 0.698 / −20% / 0.7 | 0.698 / 0.7 |
| 419 GiB | 16k | 0.508 / 22% / 2.4 / 17,838 | 0.502 / 21% / 2.3 | 0.801 / 21% / 2.4 / 11,239 | 0.798 / 20% / 2.4 |
| 419 GiB | 64k | 0.509 / 22% / 3.5 / 1,679 | 0.509 / 23% / 2.8 | 0.807 / 23% / 3.0 / 287 | 0.802 / 21% / 2.8 |
| 419 GiB | unbounded | 0.504 / 22% / 3.6 | 0.509 / 23% / 2.8 | 0.809 / 24% / 3.0 | 0.802 / 21% / 2.8 |

TTL instead of entries (`2nd`, conversation / tool agent): 60 s → 0.201 / 0.655 at 52 GiB (the best there), 0.317 /
0.711 at 419 GiB (too short); 300 s ≈ a 16k ghost (0.391-class results: 0.144 / 0.628 at 52, 0.501 / 0.798 at 419 GiB);
1,200 s ≈ unbounded.
- **The second-touch benefit does not need an unbounded set.** 64k entries (2 MB at 32 B / entry) equal the unbounded
  ghost everywhere (forgotten re-lookups 0.3–1.9k of 39–44k second touches); 16k entries (0.5 MB, ≈ 310 s of history)
  **beat** it at 52–210 GiB (0.391 vs 0.339; 0.746 vs 0.733 at 210 GiB; 2.9–3.0 TB vs 4.0–4.6 TB) and lose ≤ 0.01 at
  419 GiB. Forgetting a hash after ~300 s refuses the re-seen blocks whose gap exceeded what the cache can hold —
  the same mechanism as the gap rule `2nd_int`, which reaches the same numbers with the unbounded ghost. With
  `2nd_int` the ghost size is irrelevant above 16k (0.185 / 0.384 / 0.509 at every size ≥ 16k on the conversation trace).
- **Too small a ghost is destructive:** 1–4k entries (20–80 s of history) recognize 2–26% of the second touches,
  admissions drop to 0.04–0.7 TB and the hit share falls below LRU at 419 GiB (−16 / −20%). The knee is one reuse
  horizon of new hashes: 8–16k entries here.
- **A6 flushing under many new prefixes:** turnover is the new-hash rate; the constructed interleaved mix doubles it
  (≈ 100 / s), so 16k entries ≈ 155 s there — and still better than unbounded (`m-mix-interleave-g16k`: `2nd` 0.554 /
  29% / 4.4 TB vs 0.502 / 12% / 10.8 TB unbounded; `2nd_int` 0.554 vs 0.549). The history needed scales with the
  write stream, not with the number of prefixes.
**A4 Bloom filters (`2nd`, membership only; two filters, the current one reset after R inserts, the previous one kept).**
At 210 GiB: 65,536 bits (8 KB) × 2, reset every 8k inserts → 0.339 / 0.723 (= the exact unbounded ghost) with
2.9 TB written and 11.0k admissions caused by false positives (first-touch blocks admitted); 262,144 bits / 32k →
0.336 / 0.720, 7.1k FP; 1,048,576 bits / 128k → 0.325 / 0.724, 2.9k FP (longer memory = more long-gap admissions,
4.3–4.8 TB); 32,768 bits / 8k (≈ 16% FP rate) → 0.237 / 0.674 with 55k FP admissions and 6.6 TB: **false positives are
first-touch admissions and cost hits and writes; false negatives (the reset) act like the TTL.** At 419 GiB the longer
memories win (1M bits: 0.492 / 0.804 vs 8 KB: 0.453 / 0.779); at 52 GiB the 8 KB filter is best (0.142 / 0.628).
**A5 footprint and update cost.** Exact ghost: one hash lookup and one list move per request block, 32 B / entry →
0.5 MB (16k) … 2 MB (64k); Bloom: k = 4 hash probes, 16–256 KB total; the class tables (`adaptive`, `2nd_int` keeps
only the residence estimate) 4–79 leaf classes × 10 floats = 1–11 KB, plus the labels in flight (at most 960 s of
touches: 55–56k pending entries at 210 GiB, 32 B each ≈ 1.8 MB) and the residency metadata (time, count, class per
resident block: 16 B × capacity). Every operation is O(1) per access; the replan is O(classes²) every 10 s.

## Task B — adaptive admission (Deliverable 2; fig-adm-plan, fig-adm-grid)
**The quantity that matters is the residence estimate.** Under second touch the LRU residence is 30 s at 52 GiB, 141 s
at 210 GiB, 342 s at 419 GiB, 858 s at 839 GiB (`g-*`, residence p50), against a re-touch gap of p50 123–147 s, p90
480–620 s. Three online rules of increasing complexity use it (usable share / share of the oracle's gain / TB; the
full grid incl. the baselines is in §C):

| capacity | policy | conversation | tool agent |
|---|---|---|---|
| 52 GiB | `2nd` / `2nd_int` / `adapt2` / `adaptive` | 0.132 / 5% / 6.1 · **0.185 / 21% / 1.8** · 0.192 / 23% / 2.7 · 0.183 / 20% / 2.8 | 0.625 / 6% / 5.7 · **0.648 / 21% / 1.8** · 0.639 / 15% / 3.3 · 0.647 / 20% / 3.0 |
| 105 GiB | | 0.181 / 11% · **0.267 / 29% / 2.3** · 0.260 / 27% / 4.4 · 0.243 / 24% / 5.0 | 0.656 / 14% · **0.683 / 26% / 2.3** · 0.673 / 21% / 5.4 · 0.677 / 23% / 5.0 |
| 210 GiB | | 0.339 / 26% / 4.6 · **0.384 / 33% / 2.6** · 0.358 / 29% / 4.8 · 0.354 / 28% / 7.8 | 0.733 / 29% / 4.0 · **0.742 / 32% / 2.6** · 0.736 / 30% / 4.7 · 0.733 / 29% / 7.4 |
| 419 GiB | | 0.504 / 22% / 3.6 · **0.509 / 23% / 2.8** · 0.463 / 15% / 8.9 · 0.473 / 16% / 11.5 | **0.809 / 24% / 3.0** · 0.802 / 21% / 2.8 · 0.788 / 16% / 8.2 · 0.786 / 15% / 11.6 |
| 839 GiB | | 0.591 / −9% / 3.0 · 0.587 / −10% / 2.9 · 0.612 / −3% / 6.3 · **0.635 / +3% / 13.4** | 0.837 / −18% / 2.7 · 0.835 / −19% / 2.7 · 0.860 / −1% / 6.1 · **0.876 / +10% / 12.6** |

- **`2nd_int` — "admit a re-seen block only if its last gap fits the residence" — is the practical adaptive rule.**
  It has no parameter; at 52 GiB it refuses 71% of the re-seen admissions `2nd` makes (26.6k vs 90.9k admissions),
  which lifts the residence from 30 to 90 s and the hit share from 0.132 to 0.185 (tool agent 0.625 → 0.648); at
  210 GiB it refuses 42% (39.5k vs 67.9k), residence 141 → 234 s, 0.339 → 0.384 / 0.733 → 0.742; at 419 GiB it
  changes little (the residence covers most gaps). Useful-admission rate 49–53%, dead occupancy 0.48–0.57
  (LRU 0.70, oracle 0.05–0.09). It is the best or within 2 points of the best policy of the whole study at 52–210 GiB
  on both real traces (`adapt2` 23% vs 21% at 52 GiB on the conversation trace) and on the constructed mixes (§F),
  within 3 points of the best at 419 GiB (`2nd` 24% vs 21% on the tool-agent trace), identical on the selection and
  the test half, and it needs only the ghost and the residence estimate.
- **The class-table policy learns the right thing but it is not worth its writes at ≤ 419 GiB.** Its tables (§D) put
  first-touch classes at P(re-lookup within 150 s) = 0.08–0.16 and re-seen classes at 0.3–0.8; the replanned threshold
  settles at 0.15–0.25 (fig-adm-plan) and admits 25–40% of the candidates — more than `2nd_int` (7.8 vs 2.6 TB at
  210 GiB) for the same or fewer hits, because the hit-rate model counts every re-lookup within the residence as a
  hit while under LRU with prefix semantics only part of them are usable, so the marginal classes it admits are
  mostly pollution. Where it pays is capacity beyond the reuse horizon: at 839 GiB the replanned threshold falls to ~0.1,
  first-touch classes get admitted and the default configuration is the only filter above LRU (+3% / +10%; `adapt2`
  −3% / −1%; the selected fixed-threshold configuration −37 / −51%; every fixed filter −9 … −70%); on the short-tool
  agent trace at 48 chunks it stays at LRU (0%) where `2nd` is −303%, on the long-tool trace with churn it is −57%
  (`2nd` −229%, only the 2026-10-20 learned class policy +57%) (§F).
- **Ablations at 210 GiB (`ab-*`; conversation / tool agent, usable share, TB):** classes = touch count only 0.358 / 4.8
  · 0.736 / 4.7; touch count × gap 0.370 / 6.1 · 0.737 / 5.8; + position 0.356 / 7.4 · 0.738 / 6.8; full (default)
  0.354 / 7.8 · 0.733 / 7.4 — **fewer classes are better** (79 leaf classes dilute the samples); fixed threshold 0.3
  0.377 / 5.4 · 0.741 / 5.5, 0.5 0.366 / 3.4 · 0.737 / 3.5 — a fixed threshold beats the replanned one (the optimizer's
  bias above); labels = hit-before-eviction 0.221 / 15.0 · 0.665 / 15.2 (collapse, §D); no chain rule 0.348 / 8.2 ·
  0.733 / 7.8; residence from capacity / admission rate 0.338 / 7.3 · 0.733 / 6.9; fixed window 120 / 300 s instead
  of the residence 0.341 / 0.352 · 0.733 / 0.738; re-plan every 60 s 0.351 · 0.723; frozen after 20% 0.184 · 0.648
  (= LRU); cold start 0.228 · 0.669 (recovers in the 4th–5th fifth). At 52 GiB the same order holds (touch count only
  0.192 · 0.639; fixed 0.5 0.197 · 0.654; full 0.183 · 0.647).
- **Selection on the first half, test on the second (`tune2-selection.md`, `sel-*`).** 48 configurations (decay τ
  40 / 75 / 150 / 300 × classes {touch count; + gap; full} × threshold {replanned, 0.3, 0.5}; `adapt2` × τ; `2nd_int`
  × ghost size) were scored on requests 25–50% of both real traces at 52 / 210 / 419 GiB. Best mean share of that
  half's oracle gain: **adaptive with touch-count classes, fixed threshold 0.5, τ 300 (26.2%, min 14.5%)**; runner-up
  touch count × gap with the replanned threshold, τ 150 (25.4%, min 12.4%); `adapt2` τ 150 (24.8%); `2nd_int` with a
  64k-entry ghost (24.7%, **min 17.6%**, the most robust); the full class set never above 25.1%; τ 300 with the
  replanned threshold 18.5–23.4%. Test-half results of the selected configurations (TEST, never used for selection):

| capacity | A: adaptive, touch-count classes, fixed 0.5, τ 300 (selected) | B: adaptive, touch count × gap, replanned, τ 150 (runner-up) | C: adapt2, τ 150 | D: `2nd_int`, 64k ghost | `2nd`, 64k ghost | reference: `adaptive` default (main grid) |
|---|---|---|---|---|---|---|
| conversation 52 / 105 / 210 / 419 / 839 GiB | 14 / 29 / 29 / 11 / −37% (1.4–5.7 TB) | 24 / 24 / 32 / 17 / −2% (3.1–9.5 TB) | 28 / 29 / 29 / 14 / −2% (2.9–8.8 TB) | **21 / 29 / 33 / 23 / −10%** (1.8–2.9 TB) | 5 / 12 / 27 / 22 / −9% | 20 / 24 / 28 / 16 / +3% |
| tool agent 52 / 105 / 210 / 419 / 839 GiB | 19 / 29 / 31 / 8 / −51% | 23 / 24 / 32 / 16 / −6% | 15 / 21 / 30 / 13 / −8% | **21 / 26 / 32 / 21 / −19%** | 6 / 13 / 29 / 23 / −19% | 20 / 23 / 29 / 15 / +10% |
| SYNTHETIC 52 … 839 GiB | −9 / −4 / 7 / 6 / 1% | −2 / 5 / 2 / 4 / 6% | −2 / 4 / 4 / 4 / 6% | −2 / −6 / 3 / 1 / 12% | 1 / 4 / 5 / 12 / 16% | 1 / 3 / 0 / 1 / −2% |
| CONSTRUCTED interleave / phase, 210 GiB | 29% / 28% | 24% / 33% | 20% / 31% | 27% / 32% | 15% / 31% | 23% / 32% |

  **The selection did not carry over for the class-table policy.** Configuration A, the best on the selection half
  (26.2% mean), is below the parameter-free gap rule on the test half at every capacity but one (14–31% vs 21–33%;
  11 / 8% vs 23 / 21% at 419 GiB) and collapses at 839 GiB (−37 / −51%: a fixed threshold 0.5 refuses first touches
  for ever); the runner-up B (replanned threshold) is close to the gap rule at 52–210 GiB (23–32%), behind it at
  419 GiB (16–17% vs 21–23%) and the safest filter at 839 GiB (−2 / −6%). `2nd_int` scores 24.7% on the selection
  half and 21–33% on the test half with nothing selected. The class tables' result depends more on their
  configuration than on their learning, and the configuration that is best under one capacity range is not best
  under another — the gap rule has no such degree of freedom.


## Task C — against strong existing admission and replacement policies (Deliverable 3; fig-adm-grid)
**Mechanisms and applicability (what was implemented, what is adapted).** *2Q* and *ARC* are replacement policies:
every miss is written (into A1in / T1); their ghosts (A1out = 50% of the capacity in entries; B1 + B2 ≤ 2 × capacity)
make a second-touch distinction inside the cache (promotion to Am / T2) rather than at the host-write boundary —
implemented as published, with the tail-first request order applied to their lists. *W-TinyLFU* (Caffeine) admits
every miss into a 1% window and lets TinyLFU decide the window → main promotion; its writes are LRU's. *TinyLFU
admission* needs a candidate that is not yet stored, so the faithful host-cache form is the window-less one used here
(**adapted**: the frequency of the candidate at its lookup vs the LRU victim's; 4-bit counts halved every 10 ×
capacity accesses; a doorkeeper so that first occurrences do not take counters; exact counts, i.e. an upper bound on a
count-min sketch). The *learned class* policy is the 2026-10-20 one. All at the same capacity, order, prefix semantics
and scoring; metadata: 2Q / ARC ghosts 0.5–2 × capacity entries, TinyLFU ≤ 10 × capacity counters + doorkeeper, the
history rules 16–64k ghost entries (§A).

| capacity | LRU | SLRU | 2Q | ARC | W-TinyLFU | TinyLFU (adapted) | second touch | **second touch + gap ≤ residence** | adaptive (class tables) | learned class | oracle |
|---|---|---|---|---|---|---|---|---|---|---|---|
| conversation 52 GiB | 0.117 / 18.5 | 1% / 18.5 | 6% / 18.4 | 3% / 18.4 | 14% / 18.1 | 13% / 2.4 | 5% / 6.1 | **21% / 1.8** | 20% / 2.8 | 14% / 2.0 | 0.446 / 2.9 |
| conversation 105 GiB | 0.130 / 18.4 | 4% | 5% | 7% | 16% / 17.8 | 21% / 2.1 | 11% / 5.6 | **29% / 2.3** | 24% / 5.0 | 18% / 2.9 | 0.610 / 3.2 |
| conversation 210 GiB | 0.178 / 18.0 | 5% | 4% | 5% | 17% / 17.2 | 27% / 1.8 | 26% / 4.6 | **33% / 2.6** | 28% / 7.8 | 22% / 5.6 | 0.797 / 3.2 |
| conversation 419 GiB | 0.376 / 16.5 | 0% | 1% | 5% | −3% / 16.5 | 4% / 1.8 | 22% / 3.6 | **23% / 2.8** | 16% / 11.5 | 15% / 7.8 | 0.967 / 3.0 |
| conversation 839 GiB | 0.624 / 14.8 | **13%** | −32% | **13%** | −55% | −55% / 2.4 | −9% / 3.0 | −10% / 2.9 | 3% / 13.4 | −5% / 10.1 | 1.000 / 3.0 |
| tool agent 52 GiB | 0.615 / 18.2 | 1% | 5% | 3% | 7% | 11% / 2.8 | 6% / 5.7 | **21% / 1.8** | 20% / 3.0 | 15% / 2.0 | 0.772 / 2.8 |
| tool agent 105 GiB | 0.624 / 18.0 | 3% | 5% | 7% | 11% | 17% / 2.9 | 14% / 5.1 | **26% / 2.3** | 23% / 5.0 | 19% / 2.9 | 0.851 / 3.1 |
| tool agent 210 GiB | 0.648 / 17.6 | 5% | 3% | 5% | 13% | 24% / 2.7 | 29% / 4.0 | **32% / 2.6** | 29% / 7.4 | 24% / 5.0 | 0.940 / 3.0 |
| tool agent 419 GiB | 0.748 / 16.1 | 0% | −1% | 6% | −10% | 1% / 2.4 | **24% / 3.0** | 21% / 2.8 | 15% / 11.6 | 7% / 8.4 | 1.000 / 2.6 |
| tool agent 839 GiB | 0.862 / 14.3 | 16% | −41% | **18%** | −74% | −70% / 2.7 | −18% / 2.7 | −19% / 2.7 | 10% / 12.6 | 13% / 10.2 | 1.000 / 2.6 |
| SYNTHETIC 210 GiB | 0.348 / 6.6 | 5% | −2% | 0% | −25% | −12% / 1.1 | 5% / 3.7 | 3% / 1.9 | 0% / 6.2 | −10% / 5.5 | 0.696 / 2.0 |
| CONSTRUCTED interleave 210 GiB | 0.464 / 36.4 | 4% | 7% | 7% | 14% | 20% / 5.2 | 12% / 10.8 | **27% / 4.6** | 23% / 10.0 | 19% / 6.1 | 0.775 / 6.3 |
| CONSTRUCTED phase 210 GiB | 0.645 / 35.7 | 6% | 2% | 1% | 11% | 20% / 4.1 | 31% / 8.6 | **32% / 5.3** | 32% / 11.5 | 23% / 10.6 | 0.936 / 6.2 |

(share of the oracle's usable-hit gain over LRU / TB written; LRU and oracle: usable share / TB.)
- **Does history learning add anything over existing online methods? Yes, 5–10 points at every capacity ≤ 419 GiB,
  and all of it comes from one piece of state the existing methods do not keep: the time of a block's last touch,
  compared with the cache's own residence.** TinyLFU (adapted) is the strongest existing admission policy — 21–27% at
  105–210 GiB with the fewest writes (1.8–2.9 TB) — because its "candidate must out-count the victim" is a second-touch
  rule with a frequency memory; but it keeps filtering when the capacity could hold first-touch blocks (4% / 1% at
  419 GiB, −55 / −70% at 839 GiB) and it is negative on the synthetic trace (−12%) whose reuse is memoryless.
  `2nd_int` is above it everywhere on the real traces (+8 / +8 / +6 / +19 points of the oracle's gain at 52 / 105 /
  210 / 419 GiB on the conversation trace; +10 / +9 / +8 / +20 on the tool-agent trace), on the mixes (+7 / +12) and
  on the synthetic trace (+15), with the same writes.
- **The replacement policies (2Q, ARC, W-TinyLFU) cannot reduce writes and gain ≤ 7% at ≤ 419 GiB** — their
  second-touch distinction happens after the write. ARC is the right policy where capacity covers the horizon
  (839 GiB: +13 / +18%, the best non-oracle there) because its p adapts to the recency / frequency balance without
  refusing anything; `2nd_int`'s failure there (−10 / −19%) is the fixed refusal of first touches.
- **The 2026-10-20 learned class policy is dominated**: 14–24% vs `2nd_int`'s 21–33% at 52–210 GiB, with 1.6–2.5×
  the writes; its class feedback (hit before eviction) is the wrong label (§D).

## Task D — online feedback and learning correctness (Deliverable 4; `sh-*`, `kv_shadow_compare.py`)
- **Observability.** Every input is a hash lookup, a hash store, an eviction or the time: LMCache's connector computes
  the prefix hash of every chunk of a request on the store path (`lmcache/v1/token_database.py`, `process_tokens`:
  `_prefix_hash` runs over all token chunks and the store mask only selects which are stored), so a bypassed block's
  later re-appearance is observable even when vLLM's own prefix cache served the lookup (§G); evictions are the
  cache's own events; the residence estimate needs only the eviction ages.
- **Future reuse of a block vs hit before eviction under the current policy — measured, not argued.** Class tables
  maintained in shadow mode under LRU, second touch and the oracle (same trace, same classes, labels = "looked up
  again within w") are **identical** at every window (mean / max |ΔF| = 0.0000 over the 39–40 leaf classes with
  ≥ 100 samples, both traces): the label does not depend on what the cache did. The same tables with the 2026-10-20
  label "hit before eviction" differ from them by 0.04 (w = 60 s), 0.19 (120 s) and 0.42–0.43 (480 s) and are flat
  across windows (e.g. class 0/0/1/0: 0.04 / 0.12 / 0.22 vs 0.03 / 0.03 / 0.03), because a hit-before-eviction label
  cannot see beyond the residence and is 0 for every bypassed block. Used as the admission signal it collapses the
  policy (0.221 vs 0.354 usable share at 210 GiB, 15 TB written: the policy admits everything because every class's
  rate goes to 0 as soon as the class is refused).
- **Censoring and selection bias:** none by construction — bypassed blocks are labelled by their re-lookups like
  admitted ones; the only censoring is the ghost forgetting a hash before its re-lookup (quantified in §A: 0.3–2k of
  39–44k second touches at 64k entries, 14–21k at 16k entries), and the fixed 960-s deadline (3–4% of second touches
  come later; they are labelled 0 for every window ≤ 960 s, which is correct for any residence the capacities here
  produce). **Exploration is unnecessary** (the 2026-10-20 ε-exploration and bypass-feedback variants were workarounds
  for the policy-dependent label).
- **Delayed labels:** a label resolves at the next lookup (p50 123–147 s after the touch) or at 960 s; the tables lag
  the workload by that much; with decay 4τ = 600–1,200 s this is not the limiting factor (first-half selection:
  τ 150–300 best, 600 clearly worse because the candidate rates lag — `tune-*`).
- **Training-data freshness, drift, confidence:** frozen statistics are worthless (0.184 / 0.648 = LRU at 210 GiB;
  mix-phase 0–1%); cold start recovers in 3–4 fifths (8–10 min) for `adapt2` and the class tables are still below their online level
  in the 5th fifth (fig-adm-walkforward), `2nd_int` needs only ~200 evictions for its residence estimate; confidence is the hierarchical
  prior (10 pseudo-samples toward the parent class) — and the first-half selection shows that fewer classes (4) are
  better than 13–79: the information is in the touch count and the gap, not in finer classes.
- **Time and metadata overhead:** O(1) per access; tables 1–11 KB; labels in flight ≤ 56k entries (1.8 MB);
  ghost 0.5–2 MB (§A5).

## Task E — remaining oracle gap (Deliverable 5; `kv_gap_classes.py`, 210 and 419 GiB)
Every scored access that the oracle hits and the policy misses, by the block's observable past (share of the
oracle-only hits; conversation / tool agent):

| category | `2nd_int` 210 GiB | `2nd_int` 419 GiB | `adaptive` 210 GiB | `2nd` 210 GiB |
|---|---|---|---|---|
| A — first-touch block refused, now its second touch (the first-touch cost) | 68% / 67% | 80% / 81% | 58% / 62% | 61% / 64% |
| B + C — refused at its 3rd+ touch (few samples / shared by 5+ requests), gap > residence or borderline | 13% + 7% / 13% + 8% | 8% / 7% | 7% + 0% / 5% + 0% | 0% |
| D — admitted, evicted before this reuse (gap > residence) | 12% / 12% | 12% / 12% | 35% / 33% | 39% / 36% |
| cold → hot (gap > 600 s, then ≥ 3 touches in 300 s; uses the future) | 0 | 0 | 0 | 0 |

- **A is missing information, not a model limit.** Among the first touches of the scored half, the share re-looked-up
  within the residence is 16% (fresh request, positions 0–7), 11% (fresh, 8+), 8% (continuation, 8+) at 210 GiB and
  21 / 14 / 10% at 419 GiB (tool agent 15 / 13 / 5% and 20 / 17 / 7%): no first-touch class reaches a 25% chance, so
  admitting any of them costs more residence than it returns until the capacity has slack (the 839 GiB regime, where
  `adaptive` does admit them). What separates the 16% from the 84% is whether the conversation will continue — known
  to the application (the agent-runtime round's continue signal), not to the host.
- **B and C are the price of the gap rule:** blocks with 3+ touches whose last gap exceeded the residence estimate are
  refused; in hindsight 10–17% of the refused long-gap re-seen blocks (gap > 2 × residence) come back within the
  residence, 19–20% of the borderline ones (1–2 ×), 31–35% of the short-gap ones — the rule's cut sits where the
  class rate drops below the admitted classes'. A finer estimate (the full class tables) recovers part of C but
  loses it again in D (more admissions, shorter residence).
- **D is capacity and dead-block pollution:** blocks admitted at their second touch whose next gap (150–480 s)
  outlasted the residence; the oracle keeps them because it never stores the 49–52% of admitted blocks that are
  never read again. Those dead admissions are the remaining learnable target — at the second touch, nothing in the
  block's past (touch count 1, gap, position, sharing) separates the 50% that come back from the 50% that do not
  (hindsight re-lookup rates 31–35% within the residence for every short-gap class).
- **Phase changes** (CONSTRUCTED): after the switch the online rules are at their steady state within the first
  fifth (`2nd_int` 25.3k / 25.0k / 24.9k / 25.6k / 25.5k usable hits per fifth; `adaptive` 25.6k …; frozen `adaptive`
  22.5k = LRU); **sharing across sessions**: the Mooncake traces have no session ids; by request sharing, blocks
  touched by 5+ requests contribute C (7–8%); **few-sample prefixes**: B (13%); **cold → hot**: no case with the strict
  definition in either trace.

## Task F — generalization and sensitivity (walk-forward, fig-adm-walkforward)
- **Capacity / write pressure:** §B–C grids (52–839 GiB; pressure = write rate / capacity; the interleaved mix doubles
  the write rate at 210 GiB and `2nd_int` keeps 27%). The crossover where filtering stops paying is the capacity whose
  LRU residence reaches the reuse horizon p90 (≈ 420–620 s: between 419 and 839 GiB here); below it `2nd_int`, above it
  ARC / SLRU or the class tables.
- **Reuse horizons of seconds (REAL agent traces, `a-*`; share of the oracle's gain at 24 / 32 / 48 chunks):**
  short-tool trace `adapt2` 14 / 9 / −83%, `adaptive` 5 / 6 / 0%, `2nd` 8 / −101 / −303%, `2nd_int` 5 / −124 / −345%,
  TinyLFU 0 / −125 / −328%, ARC −14 / −27 / −13%, learned class 7 / 1 / 0%; long-tool trace with churn (`a-lt-k16-bg2`):
  TinyLFU 70 / 55 / −79%, `adapt2` 61 / 47 / −71%, learned class 60 / 56 / **+57%**, `2nd` 56 / 40 / −229%, `2nd_int`
  55 / 37 / −229%, ARC 54 / 46 / −114%, SLRU 53 / 42 / −121%, `adaptive` 23 / 13 / −57%. With gaps of 3.6 s (p50) and
  a 1.3 / s write rate the ghost is never the limit; every filter and every replacement policy but LRU loses as soon
  as the capacity covers the live set (48 chunks); the class tables do no harm there only on the short-tool trace,
  and the 2026-10-20 learned class policy (per-root, position, prefix classes with hit-before-eviction labels) is the
  one online rule positive on the long-tool trace at 48 chunks. The τ / window grid was scaled to seconds for these
  runs (τ 30, windows 2–120 s) — not selected on the first half.
- **Stable vs changing workloads, cross-workload:** fifths at 210 GiB are flat for the online rules (`2nd_int`
  conversation 3,793 / 3,932 / 3,979 / 5,078 / 3,499 usable hits vs LRU 1,893 … 1,750; tool agent 16.7k … 16.2k vs
  14.8k … 14.6k); interleaved mix `2nd_int` 27% (16k ghost 29%), `adaptive` 23%, TinyLFU 20%, learned class 19%,
  request rules 4–7%; phase change `2nd_int` 32%, `adaptive` 32%, `2nd` 31%, TinyLFU 20%; frozen 0–1%; cold start
  `2nd` 31% (nothing to learn), `adapt2` 22%, `adaptive` 16% (recovering).
- **Metadata budgets:** §A (ghost 16k entries suffices), §B (4 classes beat 79); **cold start:** above; **prefix
  sharing patterns:** conversation (one root, 24% of new hashes reused) vs tool agent (four roots, 22%) vs agents
  (53%) — the same rules rank the same way on the two real Mooncake traces; the agent traces differ in regime, not
  in sharing.
- **Over-filtering after drift:** the only over-filtering observed is structural (first-touch refusal where capacity
  covers the horizon), not drift-induced; the frozen-table variants under-filter (they decay to admit-all), they do
  not over-filter.

## Task G — actual cache semantics (validation, GPU front cache, LMCache source)
- **Prefix chain, tail blocks, recompute:** hits are usable-prefix hits (raw hits differ by < 0.3%: 18,184 vs 18,182
  for TinyLFU at 210 GiB; identical for the others); recomputed tokens at 210 GiB: LRU 64.6 M, `2nd_int` 59.0 M,
  `adaptive` 59.8 M, TinyLFU 60.1 M, oracle 47.8 M (conversation; tool agent 63.6 / 58.1 / 58.6 / 59.6 / 46.7 M);
  the chain rule (do not admit a block behind a refused predecessor) is worth 0–0.6 points and 0.4 TB.
- **Ghost vs KV storage:** the ghost holds hashes, times and counts; residency is a separate set; a ghost hit never
  counts as a hit. **Second touch's first-request loss is counted:** misses after a refusal 27.1k (conversation) /
  23.7k (tool agent) of 115k / 114k scored misses for `2nd_int` at 210 GiB.
- **Operation order:** the replay admits at the block's lookup; LMCache stores a request's chunks after prefill
  (store path, `skip_leading_tokens` = chunks already saved) and evicts to make room at store time — the same block
  set is written, up to one request duration later; the lookup of a later request sees the same residency.
- **GPU prefix cache in front (`gpu-*`, 512 / 1,024 blocks = 34 / 69 GiB, LRU, same order):** the served (GPU or
  host) usable share equals the host-only replay within ±0.002 for every policy (conversation: LRU 0.178, `2nd` 0.339–
  0.340, `2nd_int` 0.384–0.386, `adaptive` 0.345–0.360, oracle 0.788–0.795), while the host's own hit share falls
  (LRU 0.178 → 0.060–0.064, `2nd_int` 0.384 → 0.268–0.270): the GPU absorbs the short-gap reuses that LRU's host
  hits were made of, and the admission policies' gains are entirely in the long-gap range the GPU does not cover.
  Whether the ghost sees GPU-served lookups (`all`, via the store path) or not (`host`) changes nothing for `2nd` /
  `2nd_int` and ≤ 0.013 for `adaptive`. The replay's idealization (every lookup reaches the host) therefore
  overstates the host cache's absolute hit share but not the policies' gains.
- **Where the offline model still idealizes:** admission is per block at lookup time (LMCache: per request at store
  time); the residence estimate uses exact eviction ages (LMCache's eviction events give them); the ghost is exact
  (a deployment would use the Bloom variant, §A4); no GPU → host copy bandwidth is modelled.

## Metrics summary (210 GiB, scored half; replay)
| policy | usable share | reuse hits | net usable hits vs LRU | recompute (M tokens) | oracle gain | useful admission | false admission (never reused) | false bypass (reused ≤ 300 s) | dead occupancy | residence p50 (s) | admissions | TB written | ghost / predictor metadata |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LRU | 0.178 / 0.648 | 9,413 / 72,997 | – | 64.6 / 63.6 | – | 33% / 31% | 67% / 69% | – | 0.70 | 42 / 42 | 268.6k / 262.7k | 18.0 / 17.6 | – |
| TinyLFU (adapted) | 0.344 / 0.716 | 18,182 / 80,744 | +8,769 / +7,747 | 60.1 / 59.6 | 27% / 24% | 43% / 38% | 57% / 62% | 47.0k / 44.9k | 0.63 / 0.66 | 357 / 249 | 26.8k / 40.0k | 1.8 / 2.7 | ≤ 32k counters + doorkeeper |
| second touch (64k ghost) | 0.346 / 0.732 | 18,270 / 82,510 | +8,857 / +9,513 | 60.0 / 58.7 | 27% / 29% | 49% / 51% | 51% / 49% | 31.6k / 31.6k | 0.54 / 0.53 | 144 / 156 | 65.5k / 59.8k | 4.4 / 4.0 | 2 MB ghost |
| **second touch + gap ≤ residence (64k ghost)** | **0.384 / 0.742** | 20,281 / 83,580 | **+10,868 / +10,583** | **59.0 / 58.1** | **33% / 32%** | 49% / 49% | 51% / 51% | 39.1k / 39.3k | 0.57 / 0.57 | 234 / 231 | 39.5k / 39.3k | **2.6 / 2.6** | 2 MB ghost + residence EWMA |
| adaptive (class tables, default) | 0.354 / 0.733 | 18,682 / 82,673 | +9,269 / +9,676 | 59.8 / 58.6 | 28% / 29% | 41% / 39% | 59% / 61% | 23.5k / 24.2k | 0.56 / 0.54 | 84 / 87 | 115.8k / 110.0k | 7.8 / 7.4 | ghost + 11 KB tables + 1.8 MB labels |
| learned class (2026-10-20) | 0.313 / 0.717 | 16,559 / 80,800 | +7,146 / +7,803 | 60.9 / 59.4 | 22% / 24% | 42% / 42% | 58% / 58% | 30.6k / 31.8k | 0.58 / 0.57 | 123 / 132 | 83.2k / 74.2k | 5.6 / 5.0 | 12–48 class counters |
| oracle | 0.797 / 0.940 | 42,096 / 105,929 | +32,683 / +32,932 | 47.8 / 46.7 | 100% | 100% | 0% | 0.3k / 0.3k | 0.09 | 150 / 162 | 47.5k / 44.3k | 3.2 / 3.0 | the future |

(conversation / tool agent; "false bypass" = refused admissions whose block was re-looked-up within 300 s — a
realistic horizon, not necessarily a lost hit.)

## Updated RQ1 research report (Deliverable 6)
1. **Does the second-touch benefit survive a bounded history?** Yes. 64k entries (2 MB) reproduce the unbounded result
   everywhere; 16k entries (0.5 MB, ≈ 310 s) or a 2 × 8 KB double-buffered Bloom filter match or beat it at 52–210 GiB
   (0.391 vs 0.339 usable share at 210 GiB on the conversation trace) because forgetting after one reuse horizon is a
   gap filter. Below 8k entries (< 150 s) the rule collapses. The history needed is one reuse horizon of new hashes.
2. **What does adaptive admission add over fixed second touch?** One quantity: the online residence estimate. The rule
   "admit a re-seen block only if its last gap fits the residence" lifts second touch from 5 / 6% to 21% of the
   oracle's gain at 52 GiB and from 26 / 29% to 33 / 32% at 210 GiB, with 40–70% fewer writes, no parameter, and the
   same result from an unbounded, a 16k or a 64k ghost. Class tables with policy-independent labels learn the same
   information correctly but return no more hits for 2–3× the writes at ≤ 419 GiB, and their configuration does not
   transfer across halves or capacities; their one advantage, not refusing first touches once the capacity covers the
   reuse horizon (839 GiB, the short-tool agent trace at 48 chunks), holds for the replanned-threshold variants only.
3. **Which history information matters?** In order: whether the hash was looked up before (second touch: +21–26
   points of the oracle's gain at 210 GiB), the gap since that lookup compared with the cache's residence (+4–7 points
   at 210 GiB, +15 at 52 GiB), the touch count beyond 2 (within noise); position, existing prefix and root add nothing
   once touch count and gap are known (more classes = worse on the first half). The residence estimate itself
   (EWMA of eviction ages, or capacity / admission rate — equivalent) is the second ingredient.
4. **Where does it apply?** Host caches whose LRU residence is below the reuse horizon (here 52–419 GiB for the
   Mooncake traces, i.e. any cache that turns over faster than the p90 gap of ~8–10 min): 21–33% of the oracle's gain
   on both real traces, 27–32% on the constructed mixes, +3–16% on the synthetic trace, and recovery within one fifth
   after a phase change. Not where the capacity already holds first-touch blocks until their reuse (839 GiB; agent
   caches above the live set): there a non-refusing policy (ARC, SLRU, or the class tables) is right; the switch
   condition is observable (residence estimate ≥ the gap p90).
5. **Open challenges relative to existing online methods:** (i) the first-touch cost — 62–80% of the remaining gap —
   is information the host does not have (no first-touch class above 21% re-lookup probability); only the application
   (continue / end) can supply it; (ii) 49–52% of admitted blocks are still never reused and nothing in their past
   separates them at the second touch; (iii) the class-table policy's result depends on its configuration (decay, classes, threshold) more than on its
   learning, and the configuration selected on the first half did not carry to the test half nor to other capacities
   (the replanned hit-rate model over-admits because the prefix-usable fraction of re-lookups is not modelled; a fixed
   threshold is right at one capacity and wrong at another); (iv) the regime switch at large capacity is handled only by
   the replanned class tables, at the cost of writes, and not at all on the long-tool agent trace.
6. **Reliable value inputs for a unified DRAM/CXL manager (RQ2, analysis only):** per block at the host-write boundary —
   "looked up before" (bounded ghost / Bloom), the gap since the last lookup, the cache's residence estimate; from them
   an admission decision (`2nd_int`) or a probability P̂(re-lookup within residence | touch count, gap) with identical
   values under any policy; plus the agent lifecycle events for the fresh-request reuse. Not available: anything about
   first touches beyond the ~16% base rate; retention value beyond recency.
**Gate 2 (≥ 50% of the oracle's gain):** still **PARTIAL** — 32–33% at 210 GiB, 21–29% at 52–105 and 419 GiB, best
online, robust across the two real traces, the mixes and the ghost bounds; the threshold is unchanged. The negative
results stand: class learning does not beat the one-rule policy at the capacities where admission matters; TinyLFU /
2Q / ARC / W-TinyLFU do not reduce writes or do not adapt to capacity; frozen statistics are worthless.
