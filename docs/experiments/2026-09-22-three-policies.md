# 2026-09-22 — Evaluation phase 2: three simple policies vs cxlpath (the core figure), and the headline of Observation 2

**STATUS: RUNNING (started 2026-09-22).** 42 runs: 2 victims × 7 policy settings × 3 repetitions, repetitions
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

## Results
*(when the campaign has finished)*
