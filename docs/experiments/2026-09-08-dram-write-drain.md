# 2026-09-08 — Why a DRAM reader collapses 68.6 → 10.9 GiB/s under NT writers

**STATUS: PART A (mechanism analysis) DONE 2026-09-08 · PART B (measurement
matrix) BLOCKED until BIOS Memory/Chipselect Interleaving is reverted to Auto**
(`hardware/results/2026-09-08-dram-interleave-regression.log`). Campaign Phase 1
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
