# 2026-09-08 — Why a DRAM reader collapses 68.6 → 10.9 GiB/s under NT writers

**STATUS: PART A (mechanism analysis) DONE 2026-09-08 · PART B (measurement
matrix) DONE 2026-09-14 on healthy NPS1 DRAM — see Results below.**
(Blocked 2026-09-08 → 2026-09-09 by the BIOS DRAM-interleave regression,
`hardware/results/2026-09-08-dram-interleave-regression.log`.) Campaign Phase 1
of `2026-09-08-write-tier-campaign.md`. Evidence already in hand comes from
`2026-08-25-direction-gates.md` (Gate 2b) and `2026-08-25-gate2-verification.md`,
both measured on healthy DRAM (NPS4 quadrant, 68.6 GiB/s read ceiling).

## The observation to explain (2026-08-25, 4-thread reader, 8 NT-writer threads, separate CCDs)
| world | DRAM reader | writers |
|---|---:|---:|
| reader alone | 68.6 GiB/s | — |
| + 8 NT writers → DRAM | **10.9 GiB/s (−84%, 6.3×)** | 54.7 |
| + 8 NT writers → CXL | 68.6 GiB/s (= idle) | 43.7 |
Verification battery: stable ±0.5%; reader + writers = 65.6 ≈ 69.4 ceiling;
plain-store writers also collapse the reader (4.1×); 2 NT threads already
suffice (55 GiB/s of writes); 8 readers vs 8 writers reclaim nothing; CCD swap
changes nothing.

## Part A — the hardware mechanism (six questions)

**1. How a DDR controller handles reads vs writes.** Each memory controller
(AMD "UMC", 12 per socket on Turin, one per DDR5 channel) keeps requests in
per-channel queues and schedules them onto banks. Reads are latency-critical:
the core is stalled on them, so the scheduler services reads eagerly and
out-of-order (FR-FCFS: open-row hits first, then oldest). Writes are not
latency-critical — the core already retired the store — so the controller
buffers them and services them opportunistically or in batches.

**2. Separate queues — yes.** There is a read queue and a write queue per
controller (on AMD, per UMC). Being separate is exactly what lets the controller
defer writes; it does not make reads and writes independent in *bandwidth*.

**3. What they share.** (a) The DQ data bus of the channel — bidirectional,
half-duplex: at any instant it carries either read data or write data;
(b) the banks/rows (a write to a bank occupies it like a read does); (c) the
command bus and the scheduler's issue slots; (d) the DRAM's internal write
recovery time (tWR) after each write. So while queues are separate, every
transferred byte competes for the same pipe. Measured: reader + writers sum to
the read-only ceiling (65.6 vs 69.4) — one pipe, conserved.

**4. Write draining and turnaround.** Because switching the bus direction costs
dead cycles (tWTR read-after-write, tRTW write-after-read — several ns each,
i.e. tens of DRAM cycles), controllers avoid alternating. They hold writes
until the write queue crosses a *high watermark*, then switch into a
**write-drain** mode and flush writes in a batch until a *low watermark*,
then return to serving reads. Under a light write load this is nearly free:
drains are short and rare. Under a *saturating* write stream the queue refills
faster than it drains, so the controller lives in drain mode with only brief
read windows between batches — reads see both the batch wait and a turnaround
penalty every window. That is the 6.3×: not "writes are slow" but "the
controller's fairness policy is watermark-driven, and a saturating writer
keeps it above the watermark permanently". This also explains why more reader
threads (8 vs 4) recover nothing: the read windows are the bottleneck, not the
number of outstanding reads.

**5. Why non-temporal stores are the worst case.** A normal store first
performs a read-for-ownership of the line (a *read* transaction, queued with
the reads and subject to the same priority) and only later evicts the dirty
line as a *write*. Half of its DRAM traffic therefore arrives as reads and
competes "politely" in the read queue; the write half is issued lazily by
cache eviction — bursty, but throttled by the cache's own eviction rate.
NT stores skip both: they bypass the cache, combine into full 64-byte lines in
write-combining buffers, and post straight into the controller's write queue
at the core's full store bandwidth, with no RFO read and no cache pacing.
Result: pure write traffic, continuous, full-line, from 2 threads already
55 GiB/s — the write queue never falls below the watermark. Measured contrast:
plain-store writers 4.1× vs NT 6.3× reader collapse. (Note the *application*
sees NT writes as cheaper — 54.9 vs 34.3 GiB/s — precisely because the RFO
tax is gone; the reader pays instead.)

**6. How to verify — counters and experiments.**
- `amd_umc_*` PMUs (12, one per channel): CAS read vs CAS write counts per
  channel → direct measurement of the read/write mix the controller serves and
  of the drain-mode signature (write share ≫ read share during co-run); also
  reveals whether reads are being starved (CAS-read rate vs reader demand).
- `amd_df` PMU: fabric-level traffic per CS/UMC port — cross-check that the
  DRAM-targeted writers hit UMCs and the CXL-targeted ones do not.
- Latency-side evidence (no counters needed): reader pointer-chase latency
  under writers — long-tailed distribution with a periodic structure = drain
  batches; percentiles from `cxlprobe --mode=chase`.
- Both PMUs need `perf_event_paranoid ≤ 1` or CAP_PERFMON — currently 2
  (admin item in the campaign TODO).

## Part B — the minimal experiment matrix (to run after the BIOS revert)
Reader: 4T stream-read on node 0, CCD0. Writers on CCD1 (cpu-offset 16),
targeting node 0. 3 reps, 4 s per point, medians.
| axis | values |
|---|---|
| traffic | read-only · write-only · read+write |
| writer threads | 1, 2, 4, 8, 16 |
| store type | normal (`stream-write`) · NT (`stream-write-nt`) |
Outputs per point: reader GiB/s, writer GiB/s, sum vs read-only ceiling, reader
chase latency (mean/p50/p99); with counters: per-UMC CAS read/write ratio.
Expected shape: reader falls to the floor as soon as writer bandwidth
saturates (≈2 NT threads / ≈8 plain threads); sum stays ≈ ceiling; NT floor
below plain floor; chase latency shows batch structure.
Files when run: this document gets a **Results** section appended; raw under
`experimental_results/2026-09-08-dram-write-drain/`.

## Results — 2026-09-14, healthy DRAM, NPS1 (node 0 = all 12 channels; 8 CCDs × 16 cores)
Scripts: `hardware/scripts/dram-write-drain-1b.sh` (single-CCD matrix, writers on CCD1 =
cpus 16..), `dram-write-drain-1b2.sh` (multi-CCD matrix, conservation, writer/mixed
victims — writers on CCD2–7 = cpus 32..); summaries `summarize-1b.py`, `summarize-1b2.py`.
Raw: `experimental_results/2026-09-08-dram-write-drain/` (`1b-*.csv` first pass, `1b2-*.csv`
verified pass, `*-stderr.log` with wall-clock windows, `1b-machine-state.txt`). Machine: c28
after the 2026-09-09 reboot, one NUMA node, idle load 0.07, `perf_event_paranoid=2` (no UMC
counters). 3 reps per point, medians; victim 4 s; membench 1 GiB/thread for victims.

**Overlap rule learned the hard way (recorded so it is never repeated).** The first
multi-CCD pass (`1b-multiccd`, `1b-conservation`, tags `1b-rw-*-w32/64/96`, `1b-rw32-*`)
launched 32–96 writer threads with 1 GiB each and started the victim 2.5 s later. The
aggressor's 32–96 GiB page-fault/pre-touch phase had not finished, so the victim measured
next to a memset, not next to NT streams, and reported "no collapse" (reader 96.8 GiB/s
under "294 GiB/s" of writes). Those rows are kept in the CSVs but are **invalid**. The
verified pass (`1b2`) uses 256 MiB/thread aggressors, a 12 s settle, a 30 s aggressor
window, a liveness check after the victim, and `measure_start/end_epoch` stamps (added to
membench 2026-09-14) that `summarize-1b2.py` checks: 102 windows, 3 rejected (32T reader
under 96 NT writers — its own 32 GiB pre-touch under pressure ran past the aggressor's
window; that cell is reported as missing). The single-CCD pass (≤16 GiB pre-touch) is
consistent with its re-verified 16-thread point (77.5 NT / 80.7 plain) and is kept.

**Idle references (CCD0, node 0):** reader 4T 96.4 GiB/s, reader 32T (CCD0–1) 140.7;
pointer chase 131 ns mean / p50 130 / p99 270 / p99.9 300; plain-store writer 4T 64.5;
NT writer 4T 79.6; mixed 16T (67% reads, random lines) 28.6.
**Aggressor alone (write-only, own window):** CCD1 NT 54 (1T) → 79 (2–16T), plain 37 → 65;
CCD2–3 NT 138 / plain 110; CCD2–5 NT 273 / plain 137; CCD2–7 NT 294 / plain 138;
80T NT on CCD3–7 with 256 MiB buffers 280–283.

### Table 1 — 4T reader (CCD0) vs writers on the NEIGHBOUR CCD1 (first pass, valid)
| store | writers | write-only GiB/s | reader w/ writers | writers w/ reader | sum | reader loss | chase mean / p50 / p99 / p99.9 ns |
|---|---:|---:|---:|---:|---:|---:|---|
| NT | 1 | 54.1 | 87.6 | 53.6 | 141 | −10% | 142 / 139 / 269 / 309 |
| NT | 2 | 79.3 | 75.9 | 73.9 | 150 | −22% | 150 / 139 / 269 / 319 |
| NT | 4 | 79.4 | 75.9 | 74.1 | 150 | −22% | 149 / 139 / 269 / 319 |
| NT | 8 | 77.8 | 76.5 | 72.9 | 150 | −21% | 147 / 139 / 269 / 309 |
| NT | 16 | 77.3 | 77.5 | 72.1 | 150 | −20% | 141 / 129 / 269 / 299 |
| plain | 1 | 37.0 | 91.6 | 35.9 | 128 | −6% | 142 / 129 / 269 / 299 |
| plain | 2 | 62.6 | 81.3 | 60.3 | 142 | −16% | 150 / 139 / 269 / 319 |
| plain | 4 | 65.4 | 80.3 | 63.2 | 143 | −17% | 151 / 139 / 279 / 339 |
| plain | 8 | 65.9 | 80.8 | 63.4 | 144 | −17% | 151 / 139 / 279 / 339 |
| plain | 16 | 65.1 | 80.5 | 62.9 | 143 | −17% | 138 / 129 / 269 / 309 |

### Table 2 — 4T reader (CCD0) vs writers on CCD2–7 (verified pass `1b2`)
| aggressor (alone) | reader 4T | reader loss | chase mean / p50 / p99 / p99.9 ns |
|---|---:|---:|---|
| 32T NT, CCD2–3 (138 GiB/s) | 78.8 | −18% | 172 / 160 / 340 / 479 |
| 64T NT, CCD2–5 (273) | **8.0** | **12.1× (−92%)** | 769 / 610 / 2450 / 2830 |
| 96T NT, CCD2–7 (294) | **8.9** | **10.8× (−91%)** | 1470 / 1359 / 2869 / 3679 |
| 32T plain, CCD2–3 (110) | 61.5 | −36% | 191 / 170 / 430 / 550 |
| 64T plain, CCD2–5 (137) | 12.4 | 7.7× (−87%) | 280 / 250 / 660 / 910 |
| 96T plain, CCD2–7 (138) | 7.8 | 12.4× (−92%) | 286 / 249 / 679 / 959 |

### Table 3 — other victims on CCD0 (verified pass `1b2`), GiB/s (× slowdown vs idle)
| aggressor (alone) | reader 32T | plain-store writer 4T | NT writer 4T | mixed 16T |
|---|---:|---:|---:|---:|
| 64T NT (273) | 116.4 (−17%) | **8.1 (8.0×)** | 69.4 (−13%) | **4.7 (6.1×)** |
| 96T NT (294) | n/a (window rejected) | **8.9 (7.3×)** | 61.4 (−23%) | **4.0 (7.1×)** |
| 64T plain (137) | 55.1 (2.6×) | 11.0 (5.9×) | 74.6 (−6%) | 12.7 (2.3×) |
| 96T plain (138) | 41.5 (3.4×) | 8.1 (7.9×) | 64.3 (−19%) | 12.3 (2.3×) |

### What the matrix says
1. **The collapse is real on healthy socket-scale DRAM and it is a cliff, not a slope.**
   Writers on one or two CCDs (≤138 GiB/s NT) cost a reader 18–22%; writers on four CCDs
   (273 GiB/s NT ≈ the socket's write ceiling of ~290) cost it 92% — 96 → 8 GiB/s, 12× —
   and pointer-chase p50 goes 130 → 610–1359 ns with a 2.8–3.7 µs p99.9 tail. Reader +
   aggressor sums to 281–303 GiB/s at every collapsed point: **one conserved pipe at
   ~290–300 GiB/s**, exactly as in Part A. The August 6.3× (NPS4 quadrant, 3 channels,
   69 GiB/s pipe, cliff reached by 2 NT threads) is the same cliff at a lower threshold.
2. **Who suffers is decided by direction, not by thread count.** Under saturating NT
   writes: reads 11–12×, plain-store writes 8× (their RFO is a read), mixed 6–7×; **NT
   writes only −13–23%** — they join the drain batches instead of waiting for a read
   window. Plain-store aggressors do their own RFO reads, so the read queue never fully
   starves: a 32T reader keeps 30–40% and mixed keeps 44% under them, but a small 4T reader
   still loses 87–92%.
3. **Neighbour-CCD writers are a separate, smaller effect** (Table 1): 79 GiB/s from CCD1
   costs the CCD0 reader 20–22% while 138 GiB/s from CCD2–3 costs 18% — a shared IOD attach
   path, not the DRAM controllers; latency +8–14%, no tail.
4. **Per-CCD write ceilings** (for planning aggressors): one CCD saturates at ~79 GiB/s NT
   from 2 threads and ~65 plain; 2 CCDs 138, 4 CCDs 273, 6 CCDs 294 NT; plain stores flatten
   at ~138 from 4 CCDs (RFO halves the useful write rate).
5. UMC read/write CAS ratios remain unmeasured (`perf_event_paranoid=2`); the latency tail
   structure and the conserved sum are the drain-mode signatures we could take.

### Consequence for the thesis (PAPER.md not yet edited — to discuss)
At socket scale, a saturating DRAM write stream from a third of the cores (4 of 8 CCDs)
puts the whole socket's DRAM into drain mode: every reader and every ordinary-store writer
on it runs 6–12× slower, with only NT writers unaffected. That is the motivation for a
write tier restated on healthy hardware: the *write streams* (checkpoints, KV inserts,
logs — the aggressors) are what must leave DRAM, because they are the traffic that flips
the controller into drain mode for everyone else. Moving the *victim's* own writes to CXL
does not rescue it while it still reads DRAM (3c, `2026-09-14-stencil-3c.md`); moving the
*aggressor's* writes to CXL does (gate 2b at micro scale; 3c "press-cxl" cell at app scale),
and a program living entirely on CXL is immune to DRAM drain mode (3c Case C).
