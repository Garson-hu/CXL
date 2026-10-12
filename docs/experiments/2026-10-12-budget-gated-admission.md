# 2026-10-12 — Budget-gated admission vs the best safe static split, the current controller and migration

**STATUS: ACTIVE.** Raw: `experimental_results/2026-10-12-budget-gated-admission/` (`quiet/`, `calibration/`, `evaluation/`,
`varying/`, `longrun/`). Agreed with the user 2026-10-12 (option 1 after `2026-10-11-capacity-matched-kv.md`); no change to
cxlpathd, no cross-writer admission.

## Question
Under the same neighbour-slowdown SLO (p99 ≤ 7%), does budget-gated admission — new KV blocks go to DRAM only while a
DRAM write budget allows — get a higher hit share, a lower backlog, or better use of DRAM under changing neighbour load
than the best safe static split? Without migration, how close does it come, i.e. are promotion/demotion needed? Why it
matters: in `2026-10-11-capacity-matched-kv.md` a fixed 32% split beat the controller-driven policies on hit share while
staying within 7% p99 next to Adam at 8B 4×, so the controller may be too conservative.

## Setup (host memory traffic emulation, kvemu2; c28; 2026-10-12)
- Policies, all with DRAM 64 GiB + CXL 136 GiB (200 GiB effective), per-tier LRU, the same warm-up state
  (`KV2_WARM=common`: both tiers filled by a capacity-share split of the warm-up blocks), same traces and windows:
  `split` (share s of new blocks to DRAM by hash, `KV2_SPLIT_SHARE`); `budget` (new block to DRAM when a token bucket
  refilled at B GB/s holds a whole block, depth one block — unused budget is lost, DRAM writes stay smooth; else CXL);
  `borrowtier` (current cxlpathd loans, `--loan-block-s 1`, unchanged controller); `borrowmig` (CXL-first + loans +
  calm-time migration); `cxlfirst`.
- Neighbours: the 80-thread Adam step (cpus 0–79; step time) and the 8-thread DRAM reader (cpus 0–7; seconds per GiB in
  100 ms samples, progress counted every 64 MiB — the old 1 GiB counting quantized samples to ~10% steps, so the reader's
  tails in earlier files are not measurable). Quiet = the neighbour's BEFORE window without KV traffic.
- SLO: p99 during / quiet p99 − 1 ≤ 7%. Also reported: median slowdown, p99 during / quiet median − 1 (includes the
  workload's own tail), reader mean bandwidth loss.
- Calibration (independent of evaluation): trace segment from 2040 s (8B 4× and 70B 4× [2040, 2760), 8B 8× [2040, 3480));
  split s ∈ {8, 16, 24, 32, 48}%, budget B ∈ {2, 4, 8, 12, 16, 24, 32} GB/s, both neighbours. Fixed rule
  (`select_settings.py`): per neighbour × configuration × family, the largest value such that it and every smaller one
  meet the SLO.
- Evaluation: the windows of 2b (8B 4× and 70B 4× [600, 1320), 8B 8× [600, 2040)); chosen split, chosen budget,
  borrowtier, borrowmig × 3 independent runs, cxlfirst × 1; both neighbours.
- Varying load: 8B 8× and 70B 4× evaluation windows, Adam 30 s on / 30 s off (SIGSTOP); policies fixed at their
  Adam-safe settings, the controller, and an ORACLE budget (Adam-safe B while Adam runs, the calibration's best-hit budget
  while it is stopped — an upper bound, not a mechanism); 2 runs each. Adam's SLO counted over steps inside "on" phases.
- Long run: 70B 4× next to Adam, [600, 3480) at 4× (720 s; overlaps the calibration segment — it tests stability, not
  tuning); per-minute backlog, achieved store rate and Adam p99.
- Tools: `kvemu2.c` (budget policy, `KV2_SPLIT_SHARE`, `KV2_WARM`, budget column in W lines), `run_exp2b.py`
  (`--before-s`, `--reader-chunk`, `--phases`, `--phase-budgets`), `reader_victim.c` (chunk argument),
  `quiet_baseline.py`, `analyze_bga.py`, `select_settings.py`, `run_bga_chain.sh`.

## Correction to `2026-10-11-capacity-matched-kv.md` (frozen)
kvemu2 counts migration copies inside the DRAM write rate. `borrowmig` at 8B 4× wrote 34.5 GB to DRAM in 188 s, of which
20.6 GB were moves: ~0.18 GB/s in all, ~3% of the 6.2 GB/s the split writes — not "0.2 GB/s of loans + 0.11 GB/s of moves
(~5%)" as written there; the INDEX row's "~0.3 GB/s" should read ~0.2 GB/s.

## Tool checks (2026-10-12, 8B 4×, short windows, no neighbour)
- `budget` at 4 GB/s: DRAM writes 2.35 GB/s mean, 20 ms peak 6.8 GB/s; `split` 16%: 3.6 GB/s mean, 20 ms peak 17.6 GB/s.
  A budget switched from 1 to 12 GB/s through the file took effect within the run; at 12 GB/s the one-block bucket wrote
  4.1 GB/s (stores come in bursts and credit is not banked between them).
- Common warm-up: `cxlfirst` starts with DRAM full (1,024 + 2,176 slots), like `split` and `budget`.
- Over 160 trace seconds, a 60% DRAM share gave a lower hit share than 16% (0.202 vs 0.231). Hypothesis to check in the
  calibration sweep: under per-tier LRU the hit share is best when DRAM's share of new blocks matches its 32% share of
  capacity, so the tiers turn over at the same pace.

## Quiet baselines (2026-10-12 11:07–11:28, `quiet/`, `quiet_baseline.py`, each neighbour alone for 600 s)
| neighbour | samples | own p99 / median | p99 across ten 60 s windows (spread) | median across windows (spread) |
|---|---|---|---|---|
| Adam, 80 threads, step 0.143 s | 4,175 steps | 1.003 | 0.999–1.007 (0.8%) | 0.1% |
| reader, 8 threads, 100 ms samples | 5,897 | 1.026 | 0.994–1.006 (1.3%) | 0.6% |

Both tails are stable to ≤ 1.3% between 60 s windows (≤ 0.7% for 120 s), well inside the 7% target, so each run keeps a
60 s quiet window. Adam's own tail is small (p99 0.3% above its median), the reader's 2.6%.
