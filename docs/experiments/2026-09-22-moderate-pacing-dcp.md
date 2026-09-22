# 2026-09-22 — Phase 2 follow-up: real applications as moderate victims, producer pacing as the last resort, and the headline with the real PyTorch checkpoint producer

**STATUS: CLOSED 2026-09-22 — item 3 (the real PyTorch producer) stands; items 1–2 are SUPERSEDED.** The C
producer used in items 1–2 copied a snapshot that was 98% zero lines, and on c28 zero lines are written at
near-full speed beside a co-runner while data-carrying lines are not ([2026-09-22-zero-line-writes.md](2026-09-22-zero-line-writes.md),
found while analysing item 3). Items 1–2 are therefore re-measured with a pseudo-random snapshot in
[2026-09-22-three-policies-realdata.md](2026-09-22-three-policies-realdata.md); their tables below are kept
for the record of what was run, not as results. Follows the frozen
[2026-09-22-three-policies.md](2026-09-22-three-policies.md) (same protocol, same tools). Raw:
`experimental_results/2026-09-22-moderate-pacing-dcp/` (per run `<tag>-victim.txt`, `<tag>-producer.txt`,
`<tag>-daemon.csv`; driver lines in `progress.txt`; `summary.csv`, `summary-dcp.csv`). Tools:
`benchmarks/policy/` (`run_policy.py --vthreads/--scale`, `torch_ckpt_producer.py`, `analyze_dcp.py`,
`plot_policy.py`, `plot_timeline.py`).

## Questions
1. The loan had only been demonstrated on a synthetic reader. Do the real applications behave as moderate
   victims when they run on 32 of the 128 cores (a realistic co-location), and does cxlpath then lend DRAM
   to them safely?
2. Beside a saturated victim even all-CXL exceeded a 7% bound (the copy's source reads). Does pacing the
   producer as the last resort — built for this experiment — bring cxlpath inside the bound, and at what
   completion cost?
3. Does the headline hold when the producer is the real library — `torch.distributed.checkpoint.async_save`
   staging a 16 GiB CPU-resident state dict through its stock DRAM stager vs through `CxlpathWriter`?

## Setup (c28; layout per METHODOLOGY: victim, probe and producer on separate CCDs)
- **Item 1 (moderate victims).** `opt32` = the fused CPU Adam step over 1.5 B fp32 parameters on cpus 0–31;
  `llama32` = llama.cpp decoding Qwen2.5-7B Q8 with 32 threads on cpus 0–31; `pr32` = GAPBS PageRank on a
  2^25 Kronecker graph with 32 threads (2^25 rather than 2^26 so that a trial stays ~1 s at 32 threads).
  Probe cpu 80. Producer as before (8 threads, cpus 96–99 + 112–115): 64 GiB every 25 s (PageRank: 192 GiB
  every 30 s); 6 periods, metrics over the last 3; 3 repetitions, interleaved. Policies: all-DRAM (NT),
  all-CXL, DRAM throttled 20 GiB/s, cxlpath bound 1.09/margin 1.05 and 1.05/1.02, guard 1.3.
- **Item 2 (pacing).** The 80-thread saturated victims of the closed experiment (Adam, llama.cpp, PageRank
  2^26 with 192 GiB copies) with the daemon's pacing controller on (default since commit 95e4a54) and a
  bound set from the phase-1 probe level of a ~7% slowdown: Adam 1.04/1.02, llama.cpp 1.06/1.03, PageRank
  1.055/1.03; guard 1.3. Pacing controller (DESIGN.md §10.11 item 15): when no loan is possible and the
  50-epoch probe mean stays above bound × the calibrated idle level for two consecutive epochs, a per-stream
  token bucket is switched on at 0.75 × the achieved CXL rate; every further two epochs over the bound
  multiply it by 0.75, calm epochs (below margin × idle) add 1/16 of the CXL capacity, and reaching the
  capacity switches pacing off; floor 1/32 of the capacity. `reserve` waits for tokens.
- **Item 3 (real producer).** `benchmarks/policy/torch_ckpt_producer.py`: a PyTorch process holds a 16 GiB
  CPU state dict (16 tensors of 1 GiB) and calls `dcp.async_save` every 30 s, 5 times, `torch` threads = 8 on
  cpus 96–99 + 112–115. `dcp-dram` = `FileSystemWriter` combined with DCP's own `BlockingAsyncStager`
  (`cache_staged_state_dict=True`: a pinned DRAM copy of the state dict is allocated once and refilled with
  `tensor.copy_` every checkpoint; the background thread then serialises it to `.distcp` files on the NVMe).
  `dcp-cxlpath` = `CxlpathWriter` (`client="hl"`, two 16 GiB buffer sets on dax0.0, CPU tensors copied with
  NT stores by 8 pinned threads through `cxlp_copy_in_par`, drained to the same NVMe by the daemon). Note on
  the stock library: `async_save` without a stager does not copy a CPU-resident state dict at all — it hands
  the live tensors to the serialisation thread — so the stager is the only stock way to snapshot CPU-offloaded
  state; in a 2 GiB functional test it copied at 66 GiB/s (8 threads, plain stores) after a 0.8 s one-time
  allocation, and the CXL path at 42 GiB/s. Victims: Adam on 80 threads (the headline, saturated) and
  llama.cpp on 32 threads (moderate). Metrics as before over the STAGE window (the time the training thread
  is blocked in `async_save`), plus the time to durable (`PERSIST` lines: the DCP future for `dcp-dram`, the
  buffer-set drain flag for `dcp-cxlpath`).

## Results, item 1 (SUPERSEDED — zero-line snapshot; see the real-data file): real applications on 32 threads as moderate victims
(median of 3 repetitions, each = median over its last 3 windows; ranges over repetitions in parentheses; figure
`moderate-32threads.png`)

| victim (32 threads) | policy | copy GiB/s | completion s | victim slowdown | DRAM share |
|---|---|---|---|---|---|
| llama.cpp decoding | all-DRAM, NT (today) | 85.8 | 0.75 | **23.7%** (22.7–23.7) | 1.00 |
| llama.cpp | all-CXL | 43.4 | 1.48 | 0.1% (−0.8–2.6) | 0 |
| llama.cpp | DRAM throttled 20 | 20.0 | 3.20 | 6.0% (5.5–6.6) | 1.00 |
| llama.cpp | **cxlpath** bound 1.09 | 52.1 | **1.23** (1.19–1.27) | **−0.3%** (−0.8–0.1) | 0.17 (0.14–0.20) |
| llama.cpp | cxlpath bound 1.05 | 50.9 | 1.26 (1.17–1.36) | 1.1% (−0.3–1.9) | 0.15 (0.08–0.23) |
| PageRank 2^25 (192 GiB copies) | all-DRAM, NT | 87.3 | 2.20 | **67.5%** (59.7–67.5) | 1.00 |
| PageRank | all-CXL | 43.9 | 4.37 | −0.1% (−1.7–−0.1) | 0 |
| PageRank | DRAM throttled 20 | 20.0 | 9.60 | 10.0% (8.9–11.6) | 1.00 |
| PageRank | **cxlpath** bound 1.09 | 55.8 | **3.44** (3.39–3.51) | 8.3% (6.8–8.6) | 0.21 (0.20–0.23) |
| PageRank | cxlpath bound 1.05 | 52.3 | 3.67 (3.46–3.71) | **6.3%** (5.2–6.7) | 0.17 (0.15–0.21) |
| Adam step | all-DRAM, NT | 79.4 | 0.81 | **93%** (75–140) | 1.00 |
| Adam | all-CXL | 43.9 | 1.46 | 10.2% (10.2–10.3) | 0 |
| Adam | DRAM throttled 20 | 20.0 | 3.20 | 18.7% (18.1–18.8) | 1.00 |
| Adam | cxlpath bound 1.09 (guard denies the loan; paced 21–44% of the epochs) | 39.9 | 1.61 (1.59–1.61) | 9.5% (9.4–9.8) | 0 |
| Adam | cxlpath bound 1.05 (paced 58–65% of the epochs) | 34.4 | 1.86 (1.83–2.10) | 7.4% (6.0–7.9) | 0 |

What the daemon logs say (`*-daemon.csv`): beside llama.cpp-32 and PageRank-32 the loaded probe level is
1.12–1.16× the calibrated idle level (135 ns), below the 1.3 guard, so the loan is granted; the spill ratio
settles at 3–4/16 and the DRAM share of the chunks at 15–23%. Beside the 32-thread Adam step the level is
1.38–1.49× idle — the guard denies the loan, and the pacing controller runs instead (item 2).

Reading: with a quarter of the cores the three applications leave DRAM headroom, and today's DRAM staging
still hurts them badly — as much as or more than at 80 threads for two of them (PageRank 68% vs 44%, Adam
93% vs 16%; llama.cpp 24% vs 34%): the copy stream now gets the full 80–87 GiB/s a CCD can push into DRAM
and the victim sits right at the write-drain cliff. All-CXL removes the harm entirely (≤ 0.1%) beside the two read-dominated
applications. cxlpath lends 15–23% of the chunks and finishes 1.2× (llama.cpp) and 1.2–1.3× (PageRank)
faster than all-CXL with the victim inside a 7% bound at the tight setting (PageRank 6.3%, llama.cpp 1%),
i.e. 2.6× (llama.cpp) and 2.6–2.8× (PageRank) faster than a throttled DRAM writer at equal or lower harm.
The Adam step at 32 threads is not a moderate victim by the probe's measure (it still streams 24 GB of
state per step; the probe reads 1.4× idle) — the guard correctly refuses the loan and pacing takes over.

## Results, item 2 (SUPERSEDED — zero-line snapshot; see the real-data file): producer pacing beside the saturated (80-thread) victims
(figure `pacing-saturated.png`)

| victim (80 threads) | policy | copy GiB/s | completion s | victim slowdown | paced epochs |
|---|---|---|---|---|---|
| Adam | all-CXL (closed experiment) | 18.3 | 3.50 | 6.6% | — |
| Adam | cxlpath bound 1.04 | 17.9 | 3.57 (3.54–3.58) | 6.5% (6.5–6.6) | 0–3% |
| llama.cpp | all-CXL (closed experiment) | 43.6 | 1.47 | 10.4% | — |
| llama.cpp | cxlpath bound 1.10 (closed, unpaced) | 43.0 | 1.48 | 9.7% (9.4–10.6) | — |
| llama.cpp | cxlpath bound 1.06 | 39.5 (34.8–43.3) | 1.62 (1.48–1.84) | 8.7% (8.2–10.5) | 8–28% |
| PageRank 2^26 | all-CXL (closed experiment) | 43.8 | 4.71 | 14.4% | — |
| PageRank | cxlpath bound 1.10 (closed, unpaced) | 43.8 | 4.38 | 14.6% (14.0–15.6) | — |
| PageRank | cxlpath bound 1.055 | 43.8 (29.4–43.9) | 4.38 (4.38–6.54) | 14.6% (8.9–16.9) | 4–39% |
| Adam-32 (item 1) | cxlpath bound 1.05 | 34.4 | 1.86 | 7.4% (vs all-CXL 10.2%) | 58–65% |

- **Where the probe is clean, pacing does its job.** Beside the 32-thread Adam step (probe scatter small,
  level 1.4× idle) pacing to 24–28 GiB/s (median of the paced epochs) brought the harm from 10.2% (all-CXL)
  to 7.4% at 1.86 s, and the looser bound gave 9.5% at 1.61 s — a smooth trade, every repetition within
  ±1 point.
- **Beside the 80-thread Adam step the bound 1.04 is never crossed** (the probe mean sits at 1.93–1.96× idle
  and does not move with a source-bound 18 GiB/s copy): 6.5%, unchanged. Correct: the harm there is the
  source read, and slowing the copy would only stretch it.
- **Beside llama.cpp and PageRank the probe is too noisy for a tight bound.** The probe's loaded level
  beside llama.cpp differed by repetition (207, 275, 323 ns) and its 50-epoch mean crossed 1.06× idle in
  8–28% of the active epochs; pacing engaged and disengaged, and the harm fell from 9.7% to 8.7% at 1.62 s
  (+10% completion). Beside PageRank one repetition paced hard (8 GiB/s, 6.54 s, 8.9%) and two barely paced
  (14.6–16.9%, = unpaced). A single probe sample beside these victims scatters by ±25%; the 50-epoch mean
  still moves with the victim's own phases (PageRank's trial boundaries, llama.cpp's token loop), so a bound
  1.06× idle is inside the victim's own variation.

Reading: pacing is a correct last resort, and it closes the gap where the harm is the destination-side
write drain (Adam-32) — but where the harm is the copy's SOURCE read beside a read-saturated victim, the
only lever is the copy rate itself, and a latency probe on one core cannot resolve a 7% target through
the victim's own noise. To state as a limitation (the probe is a proxy for the victim's slowdown, not a
measurement of it) and as the reason the paper's bound is "protect the reader", not "hit a number".

## Results, item 3: the real producer (PyTorch `dcp.async_save`) — VALID (data-carrying tensors)
Three repetitions, 5 checkpoints each, medians over the last 3 checkpoints; every producer run rc = 0. The
reference for the Adam step is the 15 s before the first checkpoint (with the stock path a persist outlasts
the 30 s period, so the 10 s before a later checkpoint lie inside the previous persist); for llama.cpp, whose
token rate drifts with its growing context, the reference is the 10 s before each stage (`analyze_policy.py`).
Figures: `headline-dcp-adam-timeline.png`, `dcp-headline.png`; per-run lines in `summary-dcp.csv` / `summary.csv`.

| victim | DCP path | training thread blocked in `async_save` | stage rate | victim slowdown during the stage | after the stage, until durable | durable after |
|---|---|---|---|---|---|---|
| Adam step, 80 threads (saturated) | stock: `BlockingAsyncStager` into pinned DRAM + `FileSystemWriter` | **1.58–1.62 s** | 10.0 GiB/s (plain stores, source-bound) | **11.9–12.2%** | +1.5–1.6% for the first 7 s, +0.3–0.4% for the rest | 30.7–32.7 s |
| Adam step | `CxlpathWriter`: NT copy into a CXL buffer set, daemon drains CXL → NVMe | **0.80–0.82 s** | 19.6–19.9 GiB/s (source-bound) | **7.1–7.3%** | 0.0% | 18.2–18.9 s |
| llama.cpp, 32 threads (moderate) | stock | 0.31 s | 52.0 GiB/s | 13.5–14.1% | (drift-dominated, not separable) | 26.8–27.1 s |
| llama.cpp, 32 threads | `CxlpathWriter` | 0.55–0.56 s | 28.8 GiB/s | 2.0–3.8% | (same) | 18.1–18.4 s |

What the real library shows that the synthetic producer could not:
1. **The headline holds with the real producer, and the stock path is worse than the synthetic all-DRAM
   copy suggested.** DCP's stager copies with `tensor.copy_` (plain stores: read + RFO + write), so beside a
   saturated Adam step it stages 16 GiB at 10 GiB/s — the training thread is blocked for 1.6 s and the step
   runs 12% slower meanwhile; through cxlpath the same call blocks for 0.8 s (2.0× shorter) at 7.2%
   (the source read). The time to a durable checkpoint is 31–33 s vs 18–19 s (1.7×): the stock serialiser
   writes `.distcp` files through the page cache at 0.5 GiB/s from one thread, the daemon drains the CXL
   buffer set with O_DIRECT at 0.9 GiB/s.
2. **The drain's DRAM footprint is visible.** After the stage, the stock path keeps the step 1.5% slower
   for ~7 s (the serialiser reads the pinned copy and its buffered writes fill the page cache) and 0.4%
   slower until durable; the cxlpath drain reads CXL and costs the step nothing (0.0% in every
   checkpoint of every repetition) — Observation 3 in its real-library form.
3. **Beside the moderate llama.cpp the stock stager is FASTER (0.31 s vs 0.55 s) but hurts 4–6× more**
   (14% vs 2–4% over the stage window; the windows are short — 6–11 tokens — so the llama.cpp percentages
   carry ±3 points). Two facts explain the 0.55 s: the DCP plugin stages into a CXL buffer set, which is
   outside the loan (buffer sets are fixed CXL regions; only `reserve` chunks can be lent DRAM), and beside
   llama.cpp a data-carrying NT copy into CXL runs at 29 GiB/s, not 43 (the zero-line finding). Giving the
   plugin the loan means staging CPU tensors through `reserve` chunks instead of a buffer set — a
   phase-3 item.
4. The first checkpoint of the stock path costs 5–7 s (the 16 GiB pinned copy is allocated by
   `cudaHostAlloc` on first use); excluded by the last-3 rule and worth a sentence in the paper.

## Verdict
- **Item 3 (valid):** with the real `torch.distributed.checkpoint` producer beside a saturated CPU Adam step,
  CXL staging through cxlpath halves the time the training thread is blocked (0.8 vs 1.6 s), cuts the
  slowdown during the stage from 12% to 7% (the remaining 7% is the source read), removes the 0.4–1.5%
  tail that DRAM staging leaves for the 30 s of serialisation, and makes the checkpoint durable 1.7× sooner
  (19 vs 31–33 s). This is the headline figure of Observation 2 in its final form (`headline-dcp-adam-timeline.png`).
- **Items 1–2 (superseded):** measured with a 98%-zero snapshot; the moderate-victim campaign and the
  pacing runs are repeated with a pseudo-random snapshot in `2026-09-22-three-policies-realdata.md`. What
  survives from them: the controller mechanics (the guard's regime decision from the probe level, the
  pacing controller engaging where the probe is clean and not where the victim's phases move it) — the
  numbers do not.
- New gaps for phase 3: the DCP plugin's buffer sets are outside the DRAM loan; llama.cpp's token rate
  drifts over a run (use a fixed-length decode per trial, as PageRank does, for long runs).
