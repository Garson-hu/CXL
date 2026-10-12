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
