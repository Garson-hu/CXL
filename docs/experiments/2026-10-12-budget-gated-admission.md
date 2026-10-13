# 2026-10-12 — Budget-gated admission vs the best safe static split, the current controller and migration

**STATUS: CLOSED 2026-10-13** (opened 2026-10-12; paused 2026-10-12 19:27 – 2026-10-13 10:22). Raw: `experimental_results/2026-10-12-budget-gated-admission/`
(`quiet/`, `calibration/`, `evaluation/`, `varying/`, `longrun/`, `depth/`, `depth-eval/`; 196 runs). Agreed with the user 2026-10-12 (option 1 after `2026-10-11-capacity-matched-kv.md`); no change to
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

## Calibration (2026-10-12 11:30–17:08, `calibration/`, 72 runs, 60 s quiet window each; p99 = p99 during / quiet p99 − 1)
DRAM = mean DRAM write rate GB/s (20 ms peak); hit = hit share of reuse accesses; backlog = max GB. Chosen values in bold.

**Next to Adam (80 threads)**
| config | split 8 / 16 / 24 / 32 / 48% | budget 2 / 4 / 8 / 12 / 16 / 24 / 32 GB/s |
|---|---|---|
| 8B 4× (offered 20.4) | p99 +1.2 / +2.6 / +4.1 / **+5.6** / +7.7; hit .166 / .172 / .185 / **.204** / .167; DRAM 1.3 (16) / 2.8 (20) / 4.4 (40) / 6.1 (50) / 9.3 (72) | p99 +1.0 / +1.3 / +2.1 / +2.9 / +2.9 / +3.1 / **+3.4**; hit .163 / .165 / .167 / .182 / .185 / .188 / **.190**; DRAM 1.0 (5) / 1.6 (7) / 2.5 (11) / 3.9 (21) / 4.1 (18) / 4.6 (20) / 4.9 (20) |
| 8B 8× (offered 39) | p99 +2.4 / **+4.3** / +7.04 / +9.3 / +14.7; hit .151 / **.159** / .168 / .179 / .149; DRAM 2.6 / 5.7 (28) / 9.0 (37) / 12.3 (49) / 18.9 (77) | p99 +1.7 / +2.2 / +3.1 / +3.5 / +4.5 / +5.8 / **+6.8**; hit .147 / .150 / .153 / .157 / .159 / .166 / **.167**; DRAM 1.4 / 2.2 / 3.9 / 5.4 / 6.6 / 8.3 (37) / 8.9 (43) |
| 70B 4× (offered 52) | p99 +4.2 / **+6.4** / +9.2 / +13.5 / +21.7; backlog 251 / **106** / 71 / 40 / 14; DRAM 3.6 / 7.7 (38) / 11.7 (42) / 15.7 (69) / 23.7 (86) | p99 +3.3 / +4.0 / +5.2 / **+6.6** / +7.3 / +8.9 / +10.7; backlog 386 / 255 / 149 / **103** / 88 / 66 / 54; DRAM 1.9 / 3.5 / 6.1 / 8.4 (34) / 9.8 (37) / 11.0 (46) / 14.8 (57) |

**Next to the reader (8 threads; the reader's mean bandwidth loss was 0.6–4.1%)**
| config | split 8 / 16 / 24 / 32 / 48% | budget 2 … 32 GB/s |
|---|---|---|
| 8B 4× | p99 +0.7 / +1.9 / +1.9 / **+1.4** / +2.6; hit as above (**.204** at 32%) | p99 +2.5 / +0.6 / +1.3 / +1.3 / +2.6 / +2.0 / **+2.6**; hit as above (**.190** at 32) |
| 8B 8× | p99 +2.6 / +3.9 / +2.0 / **+3.9** / +5.3; hit .151 / .159 / .168 / **.179** / .149 | p99 +1.3 / +1.3 / +2.6 / +3.9 / +2.6 / +2.6 / **+2.6**; hit … **.166** at 32 |
| 70B 4× | p99 +3.9 / +2.0 / +2.6 / **+4.0** / +8.3; backlog 251 / 107 / 70 / **39** / 11 | p99 +2.6 / +2.0 / +2.6 / +2.0 / +2.0 / +2.0 / **+3.5**; backlog 388 … **52** at 32 |

What the sweep shows:
- **Smoothness buys SLO room.** At about the same mean DRAM rate the budget's p99 is lower than the split's (8B 4×: 4.6
  GB/s at +3.1% vs 4.4 GB/s at +4.1%; 8B 8×: 8.9 GB/s at +6.8% vs 9.0 GB/s at +7.0%; 70B 4×: 9.8 GB/s at +7.3% vs 7.7 GB/s
  at +6.4%), with 20 ms peaks of 20 GB/s instead of 40–50 at 8B 4×. Next to Adam the budget family stays inside the SLO
  up to 32 GB/s at 8B 4× and 8B 8×, where the split fails from 48% and 24%.
- **But the one-block bucket caps DRAM's share of the writes at ~25%** (8B 4×: 4.9 of 19.1 GB/s at 32 GB/s, budget
  utilization 15%): the four blocks of a chunk fall due together, the first takes the whole bucket and the other three go
  to CXL whatever the budget. The hit share is highest when DRAM's share of new blocks equals its 32% share of capacity
  (split 32%: .204 at 8B 4×, .179 at 8B 8×; 48%: .167 / .149 — the tiers then turn over at different paces), so the budget
  family tops out at .190 / .167. At 8B 4× next to Adam the split (32%, +5.6%) therefore beats the budget (32 GB/s, +3.4%)
  on hit share inside the SLO; at 8B 8× the split's 24% fails the SLO by 0.04 points and the safe 16% (.159) is behind
  the budget (.167). A deeper bucket (one chunk) would trade peaks for share — not part of this experiment.
- 70B 4× is overloaded in every setting that meets the SLO (backlog ≥ 100 GB, stores 1.7 s late): hit shares there are
  inflated by the backlog and not used for selection.

**Selection rule and chosen settings (`select_settings.py`, rule 2, fixed 2026-10-12 17:15 before any affected run).**
Feasible = the swept values such that the value and every smaller one meet the SLO; chosen = the feasible value with the
highest hit share, or the largest feasible value when the family is overloaded (any run with a backlog > 100 GB). Rule 1
(`chosen-rule1.txt`) took the largest feasible value, which next to the reader picked the 48% split, a share with a lower
hit share than 32% at both 8B rates; it also set the oracle's no-neighbour budget to the best-hit budget, which at 70B 4×
picked 2 GB/s through the backlog artifact. Rule 2 sets the oracle's no-neighbour budget to the largest swept value
(32 GB/s; no neighbour, no SLO). The change touched no run already made: the first evaluation run (opt, 8B 4×, split 32%)
has the same value under both rules; the reader runs began after 18:25 and the varying-load runs after 23:00.
| neighbour | 8B 4× | 8B 8× | 70B 4× |
|---|---|---|---|
| Adam | split 32%, budget 32 GB/s | split 16%, budget 32 GB/s | split 16%, budget 12 GB/s |
| reader | split 32%, budget 32 GB/s | split 32%, budget 32 GB/s | split 32%, budget 32 GB/s |
| oracle, Adam stopped | 32 GB/s | 32 GB/s | 32 GB/s |

## Progress — PAUSED 2026-10-12 19:27 (the user releases c28; resume when a new allocation is granted)
Chain `run_bga_chain.sh` started 11:30, stopped 19:25 between runs: the run in flight (reader, 70B 4×, borrowmig, rep 1)
was allowed to finish (M done 19:27), then no process was left and the cxlpath store was destroyed. **Nothing was
interrupted; no partial file exists.** Chain log kept as `chain-log-2026-10-12.txt`.
| phase | done | remaining |
|---|---|---|
| quiet baselines | 2 of 2 | — |
| calibration | 72 of 72 (+ `chosen.txt` rule 2, `chosen-rule1.txt`) | — |
| evaluation | 29 of 78: rep 1 complete except `reader-70b-4x-cxlfirst-r1` | 49 (that one + reps 2–3: split, budget, borrowtier, borrowmig × 3 configs × 2 neighbours) |
| varying load | 0 of 24 | 24 (8B 8×, 70B 4× × 6 policies × 2 reps, Adam 30 s on / 30 s off) |
| long run | 0 of 3 | 3 (70B 4× next to Adam, 720 s: budget 12, split 16%, cxlfirst) |

**Resume (next allocation):** 1. `ls -l /dev/dax0.0 /dev/dax1.0` must show group `kmem` rw (a reboot resets it to
root-only — ask the admin; kvemu2 maps dax0.0, the borrow policies' store is on dax1.0). 2. No leftovers:
`pgrep -fa "kvemu2|cxlpathd|opt_step|reader_victim"`, `system/cxlpath/build/cxlp_admin kvemu view` → "no such store".
3. Binaries present (untracked, on the home file system): `benchmarks/memory/kvemu2`, `benchmarks/policy/reader_victim`,
`system/cxlpath/build/{cxlpathd,cxlp_admin,cxlp_mkstore}`; rebuild kvemu2 if missing with
`cd benchmarks/memory && gcc -O2 -g -std=gnu11 -Wall -Wextra -Wno-misleading-indentation -Wno-unused-variable
-Wno-unused-parameter -mavx2 -pthread -I../../system/cxlpath/include kvemu2.c ../../system/cxlpath/build/libcxlpath.a -lm
-o kvemu2`, reader_victim with `make -C benchmarks/policy reader_victim`. 4. Launch the same chain, detached, inside the
allocation: `cd /home/ghu4/CXL && setsid nohup benchmarks/memory/run_bga_chain.sh 60 > /mnt/local/ghu4/bga-chain-2.log
2>&1 < /dev/null &` — it skips every run with `M done`, re-derives `chosen.txt` (deterministic, rule 2) and continues
with the remaining evaluation runs, the varying-load runs, the long runs and the per-directory analyses (`ALLDONE`).
5. Then `analyze_bga.py` per directory, write the results here, close, INDEX row, commit. **Time:** ≈ 4.9 h evaluation
(8B 8× runs ~8 min, others ~5) + 2.6 h varying + 0.7 h long runs ≈ 8.5 h → request ≥ 12 h of c28 (24 h if the optional
one-chunk-bucket sweep, ~1.5 h, is approved). Needs the whole node: cpus 0–79 (Adam) or 0–7 (reader), probe cpus 16 / 80,
workers 96–127 (+ SMT), logger 95; 64 GiB DRAM tier; 136 GiB on dax0.0; store on dax1.0.

## Interim results — evaluation rep 1 (29 runs, 2026-10-12 17:08–19:27; ONE run per cell, repeats pending)
Settings from the calibration (rule 2); per-tier LRU, common warm-up, 200 GiB effective. p99 = neighbour p99 during /
quiet p99 − 1 (SLO 7%). DRAM = mean DRAM writes GB/s (20 ms peak). Controller = `borrowtier`; migration = `borrowmig`.

| config | policy | next to Adam: hit, p99, DRAM, backlog | next to the reader: hit, p99, DRAM, backlog |
|---|---|---|---|
| 8B 4× | split 32% | .190, +5.3%, 6.2 (45), 2 GB | .190, +1.3%, 6.2 (56), 2 |
| | budget 32 GB/s | .185, +3.5%, 5.2 (21), 3 | .185, +1.3%, 5.2 (22), 3 |
| | controller | .161, +1.0%, 0.00 (lends nothing), 3 | .161, +1.9%, 0.07 (11), 3 |
| | migration | .161, +1.0%, 0.00, no moves | .187, +0.6%, 0.17 (14), moved 22 GB |
| | cxlfirst | .161, +0.9% | .161, +0.6% |
| 8B 8× | split 16% / 32% | .164, +4.3%, 5.4 (24), 7 | 32%: .192, +2.0%, 11.6 (58), 6 |
| | budget 32 GB/s | **.180**, +6.6% (one minute +7.1%), 8.8 (42), 6.5 | .179, +2.6%, 8.8 (44), 6 |
| | controller | .157, +1.0%, 0.00, 26 | .161, +2.0%, 1.8 (58), 12 |
| | migration | .157, +1.0%, 0.00, no moves | .176, +2.0%, 1.9 (48), moved 43 GB, 2 |
| | cxlfirst | .157, +1.1%, 26 | .157, +3.2%, 26 |
| 70B 4× | split 16% / 32% | .118, +6.2%, 7.9 (38), backlog max 147 GB, per minute 147 / 54 / 99 / 19 | 32%: .122, +4.0%, 16.0 (68), 26 |
| | budget 12 / 32 GB/s | .118, +6.2%, 8.5 (32), 138 GB, per minute 138 / 43 / 95 / 9 | 32: .120, +3.3%, 15.8 (68), 34 |
| | controller | .131*, +2.1%, 0.00, **712 GB growing** (407 / 506 / 712 / 706) | .118, +6.1%, 9.1 (72), 40 |
| | migration | .131*, +2.1%, 0.00, 709 GB growing | .119, **+7.5%** (violates), 8.9 (68), 54 |
| | cxlfirst | .132*, +1.7%, 707 GB growing | — (not yet run) |

\* inflated by the backlog (overload artifact).

Read so far (to be confirmed by the repeats):
- Next to Adam the existing controller lends nothing in any configuration (its guard reads Adam's own DRAM load as
  "busy"): hit share as CXL-first (.157–.161) and, at 70B 4×, a backlog growing past 700 GB. Both admission policies do
  much better inside the SLO: at 8B 8× the budget reaches .180 against the best safe split's .164 (the split's 24%
  failed the SLO in calibration by 0.04 points; the budget's smoother writes let it spend 8.8 GB/s at +6.6%), at 8B 4×
  the split is slightly ahead (.190 vs .185; both inside), at 70B 4× they are equal (backlog bounded at ~140 GB, draining
  between bursts, Adam +6.2%).
- Next to the reader the controller's loans are bursty (20 ms peaks 58–72 GB/s) and at 70B 4× migration breaks the SLO
  (+7.5%); the split and the budget stay at +1.3 to +4.0% with 3× the DRAM rate.
- Migration recovers most of the hit share with far fewer DRAM writes where DRAM is calm (8B 4×: .187 for 0.17 GB/s vs
  .190 for 6.2 GB/s), but does not exceed the admission policies, and does nothing next to Adam.
- The budget's one-minute p99 at 8B 8× next to Adam touched +7.1% — the SLO is met on the whole window, not in every
  minute; the repeats will show whether that is noise.

## Resumed 2026-10-13 10:22 (allocation 311690; dax0.0/dax1.0 still kmem-rw, no reboot; binaries unchanged; HEAD 3762292)
The chain skipped the 101 finished runs, re-derived the same `chosen.txt` and continued with `reader-70b-4x-cxlfirst-r1`
(log `chain-log-2026-10-13.txt`). **Added at the user's request: a bucket-depth sweep** (`run_bga_depth.sh`, waits for the
main chain, then rebuilds kvemu2 with `KV2_BUCKET_BLOCKS`, default 1 = the old behaviour): depths 2 / 4 / 8 blocks ×
budgets 8 / 16 / 32 GB/s next to Adam at 8B 4× and 8B 8× on the calibration segment (depth 1 = the existing calibration
runs; 18 runs); then the (depth, budget) pair with the highest hit share inside the SLO per configuration
(`select_depth.py`) × 3 runs on the evaluation segment next to Adam (`depth-eval/`), comparable with `evaluation/`.
Reported per run: hit share, DRAM write rate and 20 ms peak, budget utilization, Adam p99.

## Evaluation results (78 runs, 2026-10-12 17:08 – 2026-10-13 14:17; 3 independent runs per cell except CXL-first ×1)
Hit shares, DRAM rates and backlogs reproduce across repeats (hit ±0.001, backlog ±1 GB); the neighbour's p99 moves by
about ±0.5 points. Mean over the runs, [min..max] for the p99. Settings as chosen by rule 2.

| config, policy | next to Adam: hit | Adam p99 | DRAM GB/s | backlog GB | next to the reader: hit | reader p99 | DRAM GB/s | backlog GB |
|---|---|---|---|---|---|---|---|---|
| 8B 4× split 32% | 0.190 | +5.8 [5.3..6.1] | 6.2 | 2 | 0.190 | +2.2 [1.3..2.6] | 6.2 | 2 |
| 8B 4× budget 32 GB/s | 0.185 | +3.7 [3.5..4.0] | 5.2 | 3 | 0.185 | +1.7 [1.3..2.6] | 5.2 | 3 |
| 8B 4× controller | 0.161 | +1.0 | 0.00 (lends nothing) | 3 | 0.161 | +1.3 | 0.07 | 3 |
| 8B 4× controller + migration | 0.161 | +1.1 | 0.00 (no moves) | 3 | 0.188 [0.187..0.190] | +1.1 | 0.17 | 2 |
| 8B 4× CXL-first | 0.161 | +0.9 | 0 | 3 | 0.161 | +0.6 | 0 | 3 |
| 8B 8× split 16% / 32% | 0.164 | +4.6 [4.3..4.9] | 5.4 | 7 | 32%: 0.192 | +2.6 [2.0..3.3] | 11.6 | 6 |
| 8B 8× budget 32 GB/s | 0.180 | **+7.1 [6.6..7.6]** | 8.8 | 6 | 0.179 | +2.6 [2.0..3.3] | 8.8 | 6 |
| 8B 8× controller | 0.157 | +1.1 | 0.00 | 26 | 0.161 | +2.2 | 1.8 | 11 |
| 8B 8× controller + migration | 0.157 | +1.0 | 0.00 | 27 | 0.180 [0.176..0.182] | +2.2 | 1.9 | 3 |
| 8B 8× CXL-first | 0.157 | +1.1 | 0 | 26 | 0.157 | +3.2 | 0 | 26 |
| 70B 4× split 16% / 32% | 0.118* | +6.8 [6.2..7.1] | 7.9 | 146 | 32%: 0.122* | +4.7 [4.0..5.4] | 16.0 | 25 |
| 70B 4× budget 12 / 32 GB/s | 0.118* | +6.6 [6.2..6.9] | 8.5 | 138 | 32: 0.120* | +3.7 [3.3..4.0] | 15.9 | 34 |
| 70B 4× controller | 0.131* | +2.3 | 0.00 | 709 (growing) | 0.118* | +6.8 [6.1..7.6] | 9.4 | 41 |
| 70B 4× controller + migration | 0.131* | +2.1 | 0.00 | 710 (growing) | 0.119* | **+7.2 [6.9..7.5]** | 9.2 | 41 |
| 70B 4× CXL-first | 0.132* | +1.7 | 0 | 707 (growing) | 0.131* | +3.3 | 0 | 709 (growing) |

\* overloaded: hit shares inflated by the backlog, not comparable between policies that keep up and ones that do not.

- Both admission policies beat the existing controller next to Adam at every load (0.180–0.190 vs 0.157–0.161; the
  controller lends nothing beside Adam in any run), and both bound the 70B 4× backlog (138–146 GB) where the
  controller's grows past 700 GB.
- Static split vs budget: 8B 4× — the split has slightly more hits (0.190 vs 0.185), the budget is clearly safer (+3.7
  vs +5.8) and cannot use its margin (one-block cap). 8B 8× — the budget's 0.180 vs 0.164 comes at +7.1% p99 [6.6..7.6],
  ON the SLO, not inside it; held strictly to 7%, the safe budget is 24 GB/s (calibration +5.8%, hit 0.166), which ties the
  split. 70B 4× — a tie. So far dynamic admission's advantage is smoothness (lower p99 at the same mean DRAM rate), not
  more hits.
- Next to the reader, migration is the cheapest way to the full hit share (0.188 / 0.180 for 0.2 / 1.9 GB/s of DRAM
  writes vs 6–12 GB/s for the split and the budget), but at 70B 4× the controller's bursty loans put the reader at
  +6.8% and migration at +7.2%, above the SLO, while the split and the budget move 16 GB/s at +4.7 / +3.7%.
- Method note: rule 2 takes the largest feasible value, so several chosen settings straddle the SLO in the independent
  evaluation (p99 noise ±0.5 points). A selection margin (e.g. ≤ 6% in calibration) would avoid that; not applied here,
  since changing the rule after seeing the evaluation would be tuning on it.

## Varying neighbour load (24 runs, 2026-10-13 14:17–16:13; Adam 30 s on / 30 s off; 2 runs per cell; p99 over on phases)
| config, policy | hit | Adam p99 | DRAM GB/s (mean) | budget on / off | backlog GB |
|---|---|---|---|---|---|
| 8B 8× split 16% | 0.164 | +4.9 [4.7..5.0] | 5.4 | — | 7 |
| 8B 8× budget 32 fixed | 0.179 | +7.6 [7.5..7.6] | 8.8 | 32 / 32 | 7 |
| 8B 8× budget oracle | 0.179 | +7.3 [7.0..7.5] | 8.8 | 32 / 32 (identical: the Adam-safe budget is already the largest swept) | 6 |
| 8B 8× controller | 0.159 | +1.2 | 0.7 (lends in off phases) | — | 26 |
| 8B 8× controller + migration | 0.169 | +2.0 | 0.7 | — | 26 |
| 8B 8× CXL-first | 0.157 | +1.3 | 0 | — | 26 |
| 70B 4× split 16% | 0.118 | +6.6 [6.5..6.7] | 7.9 | — | 145 |
| 70B 4× budget 12 fixed | 0.118 | +6.8 [6.6..7.0] | 8.5 | 12 / 12 | 137 |
| 70B 4× budget oracle | 0.118 | +6.8 [6.7..6.9] | 12.2 | 12 / 32 | **60 [58..61]** |
| 70B 4× controller | 0.120 | +2.2 | 6.1 (lends in off phases) | — | 201 |
| 70B 4× controller + migration | 0.121 | +2.4 | 6.1 | — | 199 |
| 70B 4× CXL-first | 0.132 | +2.1 | 0 | — | 702 |

- At 70B 4× the oracle, which raises the budget to 32 GB/s while Adam is paused, drains the backlog in the off phases:
  peak backlog 60 GB against 137 (fixed budget) and 145 (split) at the same Adam p99 on the on phases (+6.8 vs +6.8 /
  +6.6). That is the value of adapting the budget to the neighbour: not more hits, but a backlog that empties whenever
  DRAM is free. The controller also lends in the off phases (6.1 GB/s mean) but nothing in the on phases, so its backlog
  (201 GB) stays above the fixed policies'.
- At 8B 8× the oracle test is degenerate (the Adam-safe budget equals the no-neighbour budget, 32 GB/s), and the fixed
  budget's +7.6% confirms the evaluation: 32 GB/s is above the SLO next to Adam. Migration gains 0.169 vs 0.159 from
  moves during the off phases.

## Long run (70B 4× next to Adam, 720 s of traffic, 2026-10-13 16:13–16:54, one run each)
| policy | offered GB/s | achieved stores | hit | Adam p99 (whole run) | per-minute backlog GB | per-minute Adam p99 % |
|---|---|---|---|---|---|---|
| budget 12 GB/s | 54.0 | DRAM 8.7 + CXL 42.8 = 51.5; all bytes done by the end | 0.122 | +6.9 (median +4.1) | 138 46 95 94 67 38 84 87 105 151 240 142 117 | 6.5 6.5 6.7 7.1 6.9 6.9 6.9 6.9 7.3 7.1 7.3 7.5 5.8 |
| split 16% | 54.0 | DRAM 8.1 + CXL 43.4 = 51.5 | 0.122 | +7.3 (median +3.9) | 146 53 99 109 69 38 89 90 106 163 279 145 123 | 6.9 7.2 7.8 7.6 7.3 6.9 7.3 7.4 7.4 6.8 8.2 7.5 6.3 |
| CXL-first | 49.4 | CXL 46.6 | 0.139* | +2.5 | 400 501 708 906 889 831 820 871 866 886 1096 1211 1189 (growing) | 1.9–2.9 |

- **Capacity is marginal, not comfortable.** With ~8 GB/s of DRAM writes the stores reach ~51.5 GB/s against 54.0
  offered over 12 minutes; the backlog does not grow without bound (it drains in the minutes when the offered rate drops
  below ~50 GB/s and empties by the end), but it swings between 38 and 240–280 GB (up to ~5 s of CXL writing) and Adam's
  p99 sits at the SLO for the budget (+6.9; 5 of 13 minutes ≥ 7.0) and above it for the split (+7.3; 10 of 13 minutes).
  Any sustained offered rate above ~52 GB/s would grow the backlog without bound; the offered rate of this trace segment
  (54.0 mean, minutes up to 58) is already above the safe total. Reported as insufficient capacity for a steady 70B 4×
  load next to Adam: a 7% SLO leaves ~6–8 GB/s of DRAM for this writer, and that only just covers the mean deficit.
- CXL-first alone: the backlog grows from 400 GB to 1.2 TB over the run (Adam +2.5%).

## Bucket-depth sweep (18 runs, 2026-10-13 16:55–18:20, calibration segment, next to Adam; depth 1 = the calibration runs)
hit / Adam p99 / DRAM writes GB/s (20 ms peak) / budget utilization. X = fails the SLO.

**8B 4×**
| depth \ budget | 8 GB/s | 16 GB/s | 32 GB/s |
|---|---|---|---|
| 1 | 0.167 / +2.1 / 2.5 (11) / 0.31 | 0.185 / +2.9 / 4.1 (18) / 0.26 | 0.190 / +3.4 / 4.8 (20) / 0.15 |
| 2 | 0.179 / +3.1 / 3.8 (18) / 0.47 | 0.200 / +4.2 / 6.0 (24) / 0.38 | 0.194 / +5.2 / 8.0 (40) / 0.25 |
| 4 | 0.190 / +3.6 / 5.1 (27) / 0.64 | **0.201 / +5.4 / 7.5 (36) / 0.47** | 0.195 / +7.7 X / 11.2 (47) / 0.35 |
| 8 | 0.197 / +5.5 / 7.3 (31) / 0.91 | 0.175 / +6.8 / 10.0 (45) / 0.62 | 0.172 / +9.1 X / 13.1 (52) / 0.41 |

**8B 8×**
| depth \ budget | 8 GB/s | 16 GB/s | 32 GB/s |
|---|---|---|---|
| 1 | 0.153 / +3.1 / 3.8 (17) / 0.48 | 0.159 / +4.5 / 6.1 (26) / 0.38 | **0.167 / +6.8 / 8.9 (43) / 0.28** (24 GB/s: 0.166 / +5.8) |
| 2 | 0.154 / +4.2 / 5.0 (23) / 0.62 | 0.164 / +6.8 / 8.2 (41) / 0.51 | 0.180 / +10.1 X / 13.0 (57) / 0.40 |
| 4 | 0.159 / +4.3 / 6.2 (25) / 0.78 | 0.168 / +7.6 X / 9.7 (46) / 0.60 | 0.172 / +11.4 X |
| 8 | 0.164 / +4.9 / 7.8 (32) / 0.97 | 0.178 / +8.6 X / 12.2 (48) / 0.76 | 0.165 / +12.8 X |

Chosen by rule 2 (best hit inside the SLO): 8B 4× depth 4 / 16 GB/s; 8B 8× depth 1 / 32 GB/s (unchanged).
**Depth evaluation** (evaluation segment, next to Adam, 3 runs, `depth-eval/`): 8B 4× depth 4 / 16 GB/s → hit 0.187
[0.185..0.188], Adam p99 +5.3 [5.2..5.4], DRAM 7.9 GB/s (20 ms peak 29), utilization 0.72, backlog 3 GB — against depth 1 /
32 GB/s 0.185 at +3.7 and the 32% split 0.190 at +5.8 on the same segment.

- Depth does what it was meant to: at 8 GB/s the budget's utilization goes from 0.31 to 0.91 (8B 4×) and 0.48 to 0.97
  (8B 8×) between depth 1 and 8, and the admitted DRAM rate from 2.5 to 7.3 and 3.8 to 7.8 GB/s.
- The hit share follows the admitted share, not the depth: it peaks when DRAM gets about its 32% share of the new blocks
  (8B 4×: 0.201 at 7.5 GB/s, split 32%: 0.204 at 6.1) and falls when DRAM gets more (depth 8 / 16 GB/s: 0.175).
- The neighbour's p99 follows the mean DRAM rate more than the depth (≈ +5.5% at 7.3–7.5 GB/s for depth 4 and 8; the
  split's 6.1 GB/s: +5.6%); the 20 ms peaks grow with depth (20 → 31–36 → 45–52 GB/s).
- On the evaluation segment the chosen depth gains +0.002 over depth 1 (0.187 vs 0.185) for +1.6 points of p99 and still
  trails the split (0.190 at +5.8): the calibration-segment optimum (0.201 vs 0.190) did not transfer. At 8B 8× no deeper
  bucket beats depth 1 inside the SLO; with a safety margin, depth 8 / 8 GB/s (0.164 at +4.9, utilization 0.97) equals
  the 16% split (0.164 at +4.6 in the evaluation).

## Verdict (CLOSED 2026-10-13)
**Under the same 7% neighbour-slowdown SLO, budget-gated admission does not get more hits or a lower backlog than
the best safe static split; it equals it.** Its measurable advantages are smoother DRAM writes (lower p99 at the same mean
rate: 20 ms peaks 20–36 GB/s vs 40–50 for the split) and a knob expressed in GB/s, which an online SLO estimator could
set; its disadvantage, the one-block cap (~25% of the writes), is removed by a deeper bucket at the cost of higher peaks,
after which hit share and p99 are those of the equivalent split. Where dynamic admission does pay is adaptation to the
neighbour: with an oracle budget that rises while Adam pauses, the 70B 4× backlog peak falls from 137–145 GB to 60 GB
at the same p99. Both admission policies beat the existing controller next to a DRAM-heavy neighbour (hit share
0.180–0.190 vs 0.157–0.161; the controller lends nothing there and lets the 70B backlog grow past 700 GB); next to a
calm neighbour the controller's migration reaches the split's hit share for 5–30× fewer DRAM writes but its bursty
loans break the SLO at 70B 4×. The 70B 4× long run shows that CXL plus the safe DRAM budget (~46 + 6–8 GB/s) is
insufficient for a steady 54 GB/s load next to Adam: the backlog stays bounded only because the offered rate dips.
Consequences: (1) a complex controller is not justified by hit rate; a static split or a fixed budget with the right
depth gets the same hits inside the SLO; (2) what would justify dynamic management is online estimation of the safe
DRAM write budget (the current probe-based guard finds none beside Adam) and its adaptation to the neighbour's phases;
(3) the selection rule needs a safety margin (chosen settings straddle the SLO with ±0.5-point p99 noise).
Limits: host memory traffic emulation (CPU non-temporal copies on CCDs 6–7, not GPU DMA); one trace (conversation);
200 GiB effective capacity; 70B 4× is a multi-server aggregate; calibration and evaluation segments differ in reuse
structure; 2–3 runs per cell; the oracle is an upper bound, not a mechanism.
