# 2026-09-22 — Evaluation phase 2: three simple policies vs cxlpath (the core figure), and the headline of Observation 2

**STATUS: CLOSED 2026-09-22 (verdict below).** 42 runs: 2 victims × 7 policy settings × 3 repetitions, repetitions
interleaved. Raw: `experimental_results/2026-09-22-three-policies/` (per run: `<tag>-victim.txt`,
`<tag>-producer.txt`, `<tag>-daemon.csv` for cxlpath). Tools: `benchmarks/policy/`.

## Question
A periodic checkpoint copy (64 GiB every 25 s, 8 threads, from a DRAM-resident snapshot) runs beside a
DRAM-bound program. On two axes — how much the victim slows down DURING the copy, and how long the copy
takes — where do the simple policies land, and where does cxlpath land?
- all-DRAM, NT stores (today's staging), and all-DRAM with plain stores (what a memcpy / `tensor.copy_` does);
- all-CXL (everything to dax0.0);
- rate-limited all-DRAM at two rates per victim (the "why not just throttle" alternative);
- cxlpath with a tight and a loose bound.
The all-DRAM vs all-CXL pair beside the CPU Adam step is also the headline figure of Observation 2
("keeping it in DRAM is harmful"), as a per-step timeline.

## Setup (c28; layout per METHODOLOGY: victim, probe and producer on separate CCDs)
- **Victims.** `opt`: fused CPU Adam over 1.5 B fp32 parameters (24 GB of state), 80 threads on cpus 0–79,
  step time stamped per step (`benchmarks/budget/opt_step.py`); `reader`: 8 streaming readers on cpus 0–7,
  throughput sampled every 100 ms (`benchmarks/policy/reader_victim.c`). Probe cpu 80 / 16.
- **Producer** (`benchmarks/policy/ckpt_producer.c`): a 64 GiB snapshot in DRAM (THP, touched serially);
  every 25 s it is copied in 32 MiB chunks by 8 threads (cpus 96–99 + 112–115, four per CCD — one CCD's
  port caps NT writes at ~65–77 GiB/s); 6 periods per run, metrics over the last 3. Policies: `dram` NT
  stores into a touched DRAM staging buffer; `dram-plain` plain AVX2 stores (RFO); `dram-limited` NT stores
  paced per thread at `--rate` (opt: 10 and 20 GiB/s; reader: 20 and 30 GiB/s — the phase-1 budgets under
  a 7% bound were ~9–30 and 28.5); `cxl` NT stores into dax0.0 at offset 64 GiB; `cxlpath` `reserve` /
  `copy_to` / `commit` with stream id 2, the previous period's objects released at the start of the next.
- **cxlpath store:** 64 GiB of each of dax0.0 and dax1.0 + a 48 GiB DRAM pool (tmpfs, pre-allocated and
  mapped populated, see the design changes below); daemon probe on the victim's spare CCD, `--bound`/`--margin`
  opt 1.05/1.02 (tight) and 1.10/1.05 (loose), reader 1.09/1.05 and 1.15/1.08 — from the phase-1 mapping of
  probe rise to victim slowdown (opt: 7% ≈ 1.04×; reader: 7% ≈ 1.09×). Trimming of the DRAM pool off.
- **Metrics** (`analyze_policy.py`): per copy window, victim slowdown = median step time inside the window
  (steps ending in [START, END + 150 ms]) vs the 10 s before it (reader: mean GiB/s inside vs before);
  completion time = END − START. Reported: median over the last 3 windows, then median over 3 repetitions.

## Design changes made while preparing this experiment (recorded in DESIGN.md §10.11; all in the daemon /
store, none in the client API)
1. The DRAM pool is allocated (`fallocate`) at store creation and mapped `MAP_POPULATE`: with first-touch
   faults a spilled 32 MiB chunk was ~5× slower than a CXL chunk (tmpfs = 4 KiB pages; shmem THP needs
   root), and cxlpath ran BELOW all-CXL. Trimming free pool pages is now opt-in (`--trim`).
2. The slack rule (−1/16 when CXL runs below 70% of capacity) no longer fires in the tail epoch of a burst,
   and a stream that goes idle remembers the ratio it ran with while CXL was loaded: periodic 8–16 GiB bursts
   used to lose their whole ramp to tail-off decrements and restart from 0 every burst.
3. The active reference is fed only by epochs in which the writers moved CXL bytes: the 200 ms tail of a
   burst fed it idle values, and the next burst began with a cascade of halvings.
4. `--margin` is a daemon option (the increase margin must be below the bound).
Smoke results without a victim (8 threads, 32 GiB bursts): all-CXL 43.8 GiB/s, all-DRAM 65.4, cxlpath 55.5–56.8
at a 26–31% DRAM share, no halvings. Observation: with per-chunk spill and a fixed thread pool the CXL side
loses saturation as the spill grows (each thread spends time on its DRAM chunks), so the "full" signal
(≥ 90% of capacity) self-limits the spill at the point where CXL drops to ~89% — a sensitivity item.

## Results (median of 3 repetitions; each repetition = median over its last 3 of 6 copy windows; every
producer run rc = 0; per-run lines in `summary.csv`; figures `three-policies.png`, `headline-adam-timeline.png`)

| victim | policy | copy rate GiB/s | completion s | victim slowdown during the copy | DRAM share |
|---|---|---|---|---|---|
| reader (moderate, ~100 GiB/s) | all-DRAM, NT stores (today) | 93.7 | 0.68 | **26.7%** (23.4–27.7) | 1.00 |
| reader | all-DRAM, plain stores | 60.8 | 1.05 | 24.4% | 1.00 |
| reader | all-CXL | 43.9 | 1.46 | 0.3% | 0 |
| reader | DRAM throttled 20 GiB/s | 20.0 | 3.20 | 6.7% | 1.00 |
| reader | DRAM throttled 30 GiB/s | 30.0 | 2.13 | 10.1% | 1.00 |
| reader | **cxlpath**, bound 1.09 (tight) | 64.7 (59–72) | 0.99 (0.89–1.08) | 4.0% (2.6–8.7) | 0.34 (0.27–0.47) |
| reader | **cxlpath**, bound 1.15 (loose) | 66.0 (64–71) | 0.97 (0.90–1.00) | 5.9% (4.6–6.1) | 0.38 (0.33–0.44) |
| Adam step (saturated, ~340 GB/s) | all-DRAM, NT stores (today) | 18.6 | 3.44 | **15.6%** | 1.00 |
| Adam | all-DRAM, plain stores | 9.2 | 6.92 | 11.2% | 1.00 |
| Adam | all-CXL | 18.3 | 3.50 | 6.6% | 0 |
| Adam | DRAM throttled 10 GiB/s | 10.0 | 6.40 | 7.8% | 1.00 |
| Adam | DRAM throttled 20 GiB/s | 20.0 | 3.20 | 16.9% | 1.00 |
| Adam | **cxlpath**, bound 1.05 / 1.10 | 18.0 | 3.55 | 6.5% | 0.00 |

Repeatability: beside the Adam step every policy's three repetitions agree within 0.3 points of slowdown and
0.1 s; beside the reader the simple policies agree within ±2 points, cxlpath's operating point varies more
(slowdown 2.6–8.7%, DRAM share 27–47% at the tight bound) because the controller's per-stream memory keeps
ramping across the 6 periods and a 1.09× probe bound maps to a victim slowdown of about 7 ± 2 points
(within one run the per-window slowdown rose from 3.9% to 10.0% over the six periods in repetition 1).

Two regimes:
1. **Moderate victim (the reader leaves DRAM headroom).** Today's practice (all-DRAM, NT) finishes fastest
   (0.68 s) but slows the reader by 27%; all-CXL removes the harm (0.3%) at 2.1× the completion time; a
   throttled DRAM writer that stays under 7% needs 3.2 s. cxlpath lends DRAM for 34–38% of the chunks and
   finishes in 0.97–0.99 s at 4–6% harm: **1.5× faster than all-CXL, 3.3× faster than the throttled writer at
   equal harm, and 5× less harm than today's practice at 1.4× its completion time.** Its 65–66 GiB/s is 0.9
   of the sum of the CXL capacity (44) and the 7% DRAM budget for copies (28.5).
2. **Saturated victim (the Adam step leaves nothing).** The copy is SOURCE-bound at ~18 GiB/s whatever its
   destination (the 8 copy threads read the snapshot out of a DRAM that the victim saturates), so all
   unthrottled policies complete in 3.4–3.6 s; what the destination changes is the harm: 15.6% into DRAM vs
   6.6% into CXL (2.4× less). cxlpath lends nothing (DRAM share 0.00): CXL never reaches 90% of its capacity,
   and a loan could not have helped a source-bound producer. Throttling to the same ~7% harm costs 6.4 s,
   1.8× longer. Plain-store staging (what `memcpy` / `tensor.copy_` do) is worse still: 6.9 s at 11%.
   A curiosity: the throttled-20 writer completes faster (3.2 s) than the unthrottled one (3.4 s) — pacing
   gaps let the source reads through; both are source-bound.

## Verdict
- **The core figure works and says what the motivation needs:** the simple policies each fail on one axis,
  cxlpath sits inside the bound at a completion time no throttled writer reaches. The multiple is regime-
  dependent and must be stated so: ≈1.5× all-CXL / ≈3.3× throttling for a moderate victim; ≈ all-CXL
  (correctly, no loan) with 2.4× less harm than DRAM staging for a saturated victim. "Roughly the sum" holds
  for the moderate victim (0.9 of it); the paper should say "approaches the sum", not "doubles".
- **Observation 2 headline (`headline-adam-timeline.png`):** a CPU-offloaded training step (Adam over 24 GB)
  runs 15–17% slower for the whole 3.5 s a 64 GiB checkpoint is copied out of DRAM into DRAM staging; into
  CXL staging the same copy costs 6.5% (the source read) and finishes at the same time; throttling to 10 GiB/s
  costs 7.8% for 6.4 s. This is the real-application version of "keeping it in DRAM is harmful" (O2) and the
  precise form of O3 ("the write half leaves DRAM; the source read remains").
- **Controller findings for the sensitivity section:** (a) a probe bound maps to victim slowdown with ±2–3
  points of scatter, and the tight/loose bounds produced nearly the same operating point — the ramp rate and
  the ≥ 90%-capacity fullness rule limit the loan more than the bound does; (b) per-stream memory keeps
  ramping across periods, so the operating point drifts upward over a run; (c) beside a saturated victim the
  fullness signal (not the probe) is what keeps the loan at zero. Items for the sensitivity study: bound,
  step, fullness threshold, number of periods to steady state.
- Next: the two further victims (GAPBS PageRank, llama.cpp CPU decoding) through the phase-1 protocol, then
  the same core experiment beside them; the real PyTorch and VeloC clients replace the synthetic producer in
  the real-application section.
