# 2026-10-21 — Hardware validation: does reuse-aware admission actually remove the DRAM/CXL write interference? (Phase 3, HW)

**STATUS: CLOSED 2026-10-22 (campaign 2026-10-21 22:06 – 2026-10-22 05:11 on c28, job 315259; 71 runs).** **Verdict: the Phase 3
claim holds on the hardware for its DRAM side, with a quantified bias.** Replaying the Phase 3 write decisions physically
beside the real 80-thread Adam step: the admit-all stream breaks the 7% p99 SLO at every configuration (+8.3 … +9.0% at
8B 8×, +14.1 … +15.7% at 70B 4×, +25% at 70B 8×; medians +4.4 … +12.7%), the RQ1-filtered stream stays inside it with
margin (+1.6 … +2.8% at 8B 8× / 70B 4×, +4.0% at 70B 8×; medians ≤ 0.8%), and the independent budget-gated placement,
decided live, redirects 9–29% of the DRAM candidates and trims that to +1.0 … +2.5%. The Phase 3 interference model is
right in verdict and order but low by 0.2–1.2 points for the filtered stream (its 10-ms bursts of 13–19 GB/s, 10× the
mean, are not in a mean-rate curve) and high for admit-all beyond its calibrated range (36% predicted vs 25% measured at
70B 8×). Two conditions found, not costs: a writer on the victim's own CCD doubles the filtered stream's harm (+5.4 …
+6.5%, no margin) and regular stores (read-for-ownership) do the same (+6.1%); with DMA-like non-temporal writes from
another core group the numbers above hold. Evidence boundary: CPU replay of the DRAM-targeted part only — the CXL
devices were not writable (blocker below), no GPU DMA, no LMCache runtime, Adam as the only victim. One correction to the
Phase 3 text: its "0 budget refusals" was wrong (the bucket redirected 15–35% of the DRAM candidates in its own CSVs).
Research assessment unchanged: no basis for a minimal unified manager on H2 (Task G). Question: the Phase 3 joint benefit
analysis (`2026-10-21-joint-benefit-analysis.md`) concluded from trace-driven replay plus the measured interference
curves that the RQ1 admission removes 88–91% of the host KV writes and all of their tail, so that the filtered stream
costs the Adam neighbour an estimated p99 +0.1–1.9% and the cost module never fires. Is that true on the real machine
when the SAME write decisions are replayed as physical host-memory writes beside the real Adam step? Evidence types:
**HW** (this file: real Adam + a CPU replay of the Phase 3 write logs on c28), **SIM** (the Phase 3 write logs and
predictions, re-used), **EST** (the interference curve interpolation being tested). No change to the research
direction, to RQ1, to `cxlpathd` or to the simulator's decisions. Raw: `experimental_results/2026-10-21-hw-validation-filtered-writes/`
(`machine-state.txt`, `run_all.sh` = exact commands, `writelogs/`, `sim/`, `smoke/`, `alone/`, `fid/`, `corun/`, `ctrl/`, `x8/`,
`writelog-stats.md`). Code: `benchmarks/memory/kvreplay.c` (new), `run_kvreplay.py` (new), `analyze_kvreplay.py` (new),
`scripts/kv_writelog_stats.py` (new), `scripts/kv_joint_sim.py --write-log` (new option, results unchanged).

## Blocker recorded first: the CXL devices are not writable (Task B)
`/dev/dax0.0`, `dax1.0`, `dax2.0` are `root:root 0600` since the 2026-10-18 power-loss reboot (`machine-state.txt`,
2026-10-21 21:5x; the admin's hand fix of 2026-10-10 did not survive the reboot, as `2026-10-09-cxl-topology-interference.md`
warned). `dax2.0` is a root famfs mount (another user's). `ghu4` has no sudo. The user's rule and the brief forbid changing
permissions or regions. Consequence for this round: **the CXL-targeted part of every stream cannot be written physically.**
The replayer counts it, keeps its timing, and reports it as "not issued"; **the DRAM-targeted part — the part that
carries the measured interference (CXL writes from an unrelated core group cost a DRAM reader ≤ 2%, 2026-10-09/10) — is
replayed physically.** The CXL path capacity (46 GB/s), the CXL backlog and CXL read/write contention therefore stay
model-based in this round; the DRAM-side interference claim is what the hardware tests.

## Setup (what runs, what is measured)
- **Machine** (`machine-state.txt`): c28, EPYC 9745 (128 cores / 256 cpus, 8 CCDs = L3 groups of 16 cores: CCD k = cpus
  16k–16k+15 and SMT siblings +128), one NUMA node (DRAM 755 GB), CXL devdax only (not system-ram), THP `always`, no
  other users' processes, GPU idle. Slurm job 315259 (256 cpus, until 2026-10-23 15:27).
- **Neighbour:** the 80-thread fused Adam step over 1.5 B fp32 parameters (24 GB of state, read-modify-write every step;
  `benchmarks/budget/opt_step.py 80 1500 …`, `taskset -c 0-79`, OMP close binding) — exactly the 2026-10-12 victim
  (cpus 0–79 = CCDs 0–4, step 0.143 s). Protocol per run: Adam starts → 25 s settle → 60 s quiet window → replay → stop.
  **SLO metric unchanged: p99 step time during the replay / p99 in the quiet window − 1 ≤ 7%** (also median and p95
  slowdowns, p99 / quiet median, per-minute p99).
- **Streams** (`writelogs/`, regenerated from the Phase 3 simulator with `--write-log`; the simulator's CSV rows for all
  15 policy × configuration pairs are IDENTICAL to the committed Phase 3 rows, so the logs are the Phase 3 decisions):
  *admit-all* = `split_lru` (every new block stored, 32% hash share to DRAM); *filtered* = `value_split` (RQ1 admission:
  gap rule + regime switch, same hash share, no cost module); *filtered + budget* = the filtered stream whose DRAM
  candidates (the hash share) pass a token bucket decided LIVE on the real clock by the replayer, at the Phase 3
  selection (B / depth: conversation 8B 8× 8 GB/s / 1, 70B 4× 4 / 1, 70B 8× 12 / 1; tool agent 8B 8× 32 / 1, 70B 4× 8 / 1)
  — the independent combination's placement, so its refusals are counted on hardware. Window = the scored half of each
  trace in wall seconds (8B 8× ≈ 211 s, 70B 4× ≈ 414–423 s at trace speed; all stores offered inside the window, by
  time, not by request index — 1–2% more stores than the CSV's scored-request count).
- **Replayer** (`kvreplay.c`): one job per store, due at its offer time (request arrival + 70 ms per block of prefill,
  as in the simulator); 64 worker threads on cpus 96–127 + 224–255 (CCDs 6–7, kvemu2's placement of 2026-10-11/12),
  logger on cpu 95; each store is written into the next 64 / 162 MiB slot of a 64 GiB DRAM arena (huge pages,
  pre-faulted before the quiet window) with **non-temporal AVX2 stores from a cache-resident pseudo-random source**
  (no DRAM reads — the shape of a DMA write; data lines, never zero lines), paced at 9.5 GB/s per block stream (one
  GPU→host link, as kvemu2); start and end of every store, 10 ms rates, backlog (bytes due minus bytes done) and
  start delays are recorded. Controls: `--store plain` (regular stores: read-for-ownership + write-back), `--store none`
  (same threads and pacing into a 32 KiB L1-resident buffer: CPU activity without memory traffic), `--cpus 64-79,192-207`
  (32 workers on CCD 4, i.e. on Adam's own cores). **This is a CPU replay of the traffic shape, not GPU DMA and not the
  LMCache runtime**; every number below is labelled HW (CPU replay).
- **Not replayed:** CXL-targeted stores (blocker above); loads (hits are tier-independent reads by the GPU, 2026-10-07);
  the checkpoint co-writer.

## Task A — the Phase 3 write data, verified (`writelog-stats.md`, `scripts/kv_writelog_stats.py`)
- **Reproduction:** re-running the simulator with the new `--write-log` option gives CSV rows identical in every field
  (hit share, blocks written per tier, GB, DRAM rate, estimated p99, backlog, drops, recomputed tokens, wall span) to the
  committed Phase 3 runs for all 5 configurations × 3 policies. The write logs are therefore the Phase 3 decisions.
- **Denominators:** the scored window in wall seconds is the simulator's own (8B 8×: 235–446 s = 211 s; 70B 4×:
  470–885 s = 414 s; tool agent 464–887 s = 423 s); bytes in the window = stores in the window × block bytes; the CSV's
  "written blocks" count stores of scored REQUESTS (3,863 / 7,332 DRAM / CXL at 70B 4× filtered) and the window by TIME
  holds 1–2% more (3,916 / 7,357: stores of first-half requests whose prefill ends inside the window). Rates in the
  Phase 3 tables are bytes / wall span of the window. **The earlier correction stands:** the whole trace holds 2.1× the
  window's bytes (70B 4× filtered: 1,393 + 2,767 GB whole trace vs 657 + 1,235 GB in the window), which is what the
  2026-10-20/21 admission reports printed as "TB written (scored half)".
- **Time resolution, stated:** the Mooncake traces stamp REQUESTS at 1 ms; the position of a block's store inside a
  request is the simulator's prefill model (block j offered j × 70 ms after arrival) and, on the hardware, the 9.5 GB/s
  link pacing (a 67 MB block takes 7 ms, a 168 MB block 18 ms). So the 100 ms and 1 s statistics below are trace-driven;
  the 10 ms statistics depend on those two modelling choices and are reported as such, not as measured burst data.
- **Streams at three time scales** (DRAM-targeted part, GB/s; `paced` view = what the replayer issues; `offered` = bytes at
  their offer instants; `served` = the simulator's completion model):

| configuration, stream | mean | 10 ms p99 / max (paced) | 100 ms p99 / max | 1 s p99 / max | 10 ms bins > 8 GB/s | longest run of 10 ms bins > 8 GB/s |
|---|---|---|---|---|---|---|
| conv 8B 8× admit-all | 12.2 | 54 / 89 | 23 / 28 | 20.7 / 22.4 | 52% | 20 (0.2 s) |
| conv 8B 8× filtered | 1.50 | 13.4 / 27 | 5.7 / 7.0 | 4.9 / 5.4 | 4.1% | 2 |
| conv 8B 8× filtered + budget (simulated bucket) | 1.12 | 6.7 / 8.2 | 3.4 / 4.4 | 2.9 / 3.2 | 0.2% | 1 |
| conv 70B 4× admit-all | 16.5 | 69 / 122 | 37 / 46 | 32.2 / 35.8 | 66% | 190 (1.9 s) |
| conv 70B 4× filtered | 1.59 | 17.2 / 38 | 8.5 / 12.8 | 6.8 / 7.9 | 11% | 5 |
| conv 70B 4× filtered + budget (simulated bucket) | 1.04 | 9.5 / 9.5 | 3.4 / 4.1 | 2.6 / 3.3 | 7.5% | 2 |
| conv 70B 8× admit-all | 31.6 | 96 / 150 | 59 / 74 | 54.7 / 57.7 | 89% | 821 (8 s) |
| conv 70B 8× filtered | 3.11 | 19 / 44 | 12.2 / 17.7 | 10.2 / 11.1 | 20% | 34 |
| tool 8B 8× admit-all | 11.6 | 59 / 163 | 24 / 35 | 19.8 / 20.1 | 47% | 20 |
| tool 8B 8× filtered | 1.52 | 13.4 / 32 | 5.4 / 8.4 | 4.6 / 5.8 | 4.0% | 2 |
| tool 70B 4× admit-all | 15.8 | 78 / 202 | 39 / 67 | 30.4 / 33.5 | 60% | 133 |
| tool 70B 4× filtered | 1.43 | 16.6 / 38 | 7.3 / 11.9 | 6.0 / 6.4 | 9.9% | 4 |

  Reading: the filtered DRAM stream is 8–11× smaller in the mean and its 1-s peaks (5–11 GB/s) sit at or just above the
  measured safe budget (6–8 GB/s beside Adam at a 7% p99 SLO), for a few seconds per window; the admit-all stream sits
  above it 45–90% of the time with runs of 0.2–8 s. At 10 ms the filtered stream still shows single-block bursts of
  13–19 GB/s (p99) and up to 27–44 GB/s (two to four blocks in flight) — these are what a per-second average hides and
  what the hardware run decides. The CXL-targeted part (not issued this round) is 3–7 GB/s mean after filtering (1-s
  p99 8–17 GB/s) and 25–65 GB/s before it (the Phase 3 saturation case).

## Task B — the hardware, as found (`machine-state.txt`, 2026-10-21 21:5x)
No other user's processes, load 0.4, GPU idle, 727 GB of DRAM free; Slurm job 315259 holds all 256 cpus until 2026-10-23
15:27. CPU plan (same as 2026-10-12): Adam on cpus 0–79 (CCDs 0–4), replayer workers on cpus 96–127 + 224–255 (CCDs
6–7), logger on cpu 95 (CCD 5); the CCD-4 control puts 32 workers on cpus 64–79 + 192–207, i.e. on Adam's own cores.
The DAX permission blocker is recorded above; `kvreplay` was run without `--cxl-dev`, so no attempt was made to open or
change any device, region or famfs mount. The earlier low-interference results for CXL writes hold for writers on a
core group other than the reader's own and its paired one (2026-10-09); nothing in this round extends them.

## Task C — the replayer reproduces the planned streams (`fid/`, no neighbour; HW, CPU replay)
| run (full scored window) | planned mean / 1-s max / 100-ms max / 10-ms p99 (paced view of the log) | measured mean / 1-s max / 100-ms max / 10-ms p99 / 10-ms max (GB/s, from the per-store start/end stamps) | start delay p99 / max (ms) | per-store rate p50–p99 | stores issued DRAM / not issued CXL | replayer CPU (core-seconds / window) |
|---|---|---|---|---|---|---|
| conv 8B 8× admit-all | 12.20 / 22.4 / 27.6 / 53.7 | 12.20 / 22.4 / 27.6 / 53.0 / 90.0 | 0.07 / 0.40 | 9.48 GB/s | 40,508 / 83,471 | 136 / 223 s |
| conv 8B 8× filtered | 1.50 / 5.4 / 7.0 / 13.4 | 1.50 / 5.4 / 7.1 / 13.4 / 26.8 | 0.21 / 0.25 | 9.48 | 4,721 / 10,125 | 13.5 / 211 s |
| conv 70B 4× admit-all | 16.46 / 35.8 / 46.3 / 68.7 | 16.46 / 35.8 / 46.4 / 68.2 / 108.9 | 0.20 / 1.09 | 9.48 | 42,064 / 86,994 | 335 / 429 s |
| conv 70B 4× filtered | 1.59 / 7.9 / 12.8 / 17.2 | 1.59 / 7.9 / 12.8 / 17.1 / 37.4 | 0.21 / 0.25 | 9.48 | 3,916 / 7,357 | 21.6 / 414 s |
| tool 8B 8× admit-all | 11.64 / 20.1 / 35.0 / 58.7 | 11.64 / 20.1 / 35.0 / 58.2 / 123.4 | 0.19 / 1.93 | 9.48 | 39,117 / 82,697 | 147 / 225 s |
| tool 70B 4× admit-all | 15.77 / 33.5 / 66.6 / 77.6 | 15.77 / 33.3 / 67.1 / 75.6 / 159.2 | 0.20 / 0.24 | 9.48 | 40,855 / 86,443 | 363 / 435 s |

Every store started within 0.25 ms of its due time (one 1.9 ms outlier), was written at the paced 9.48 GB/s, and the
measured rate statistics equal the plan at 1 s, 100 ms and 10 ms (p99): the physical stream IS the Phase 3 DRAM-targeted
stream, bursts included, with a DRAM-side backlog of at most 0.1–2.6 GB (the bytes in flight). The replayer's CPU use is
0.03–0.05 cores for the filtered streams and 0.6–0.8 cores for admit-all, on CCDs Adam does not use. One caveat found
and handled: the logger's 10-ms W lines can be distorted by a stalled sample (one bin of 1,116 GB/s in the 70B 4× admit-all
run = an 11 GB jump across a ~0.7 s NFS flush), so all rate statistics in this file come from the per-store records, and
the W lines serve only the backlog and lateness columns.

## Task D / E — the real Adam step beside the replayed streams (`corun/`, 3 repetitions each; HW, CPU replay of the DRAM-targeted part; fig-hwval-timeline, fig-hwval-slowdown, fig-hwval-bursts)
| configuration | stream | DRAM GB/s issued: mean / 1-s max / 10-ms p99 / 10-ms max (HW) | Adam p99 slowdown, 3 runs (mean) | median / p95 slowdown (mean of 3) | busiest minute p99 | Phase 3 prediction: p99 (DRAM mean) | live bucket: DRAM candidates → written / redirected to CXL | SLO 7% |
|---|---|---|---|---|---|---|---|---|
| conv 8B 8× | admit-all (split + LRU) | 12.20 / 22.4 / 53.0 / 90 | +8.56 / +8.25 / +8.98 (**+8.60**) | +4.54 / +7.44 | +9.1 | +10.07 (12.92) | – | FAIL |
| conv 8B 8× | RQ1-filtered (value_split) | 1.50 / 5.4 / 13.4 / 27 | +1.75 / +1.89 / +1.89 (**+1.84**) | +0.42 / +1.40 | +2.2 | +1.38 (1.49) | – | ok |
| conv 8B 8× | filtered + live budget (independent) | 1.18 / 3.5 / 6.7 / 20 | +1.12 / +1.05 / +1.12 (**+1.10**) | +0.35 / +0.91 | +1.3 | +0.91 (1.12) | 4,721 → 3,704–3,726 / 995–1,017 (21%) | ok |
| conv 70B 4× | admit-all (split + LRU) | 16.46 / 35.8 / 68.7 / 114 | +14.10 / +14.72 / +14.60 (**+14.47**) | +5.90 / +11.96 | +15.8 | +13.94 (16.88) | – | FAIL |
| conv 70B 4× | RQ1-filtered (value_split) | 1.58 / 7.9 / 17.1 / 37 | +2.81 / +2.45 / +2.74 (**+2.67**) | +0.12 / +1.73 | +3.3 | +1.45 (1.56) | – | ok |
| conv 70B 4× | filtered + live budget (independent) | 1.13 / 3.7 / 9.5 / 28 | +1.12 / +0.98 / +1.19 (**+1.10**) | +0.14 / +0.89 | +1.5 | +0.83 (1.02) | 3,916 → 2,784–2,793 / 1,123–1,132 (29%) | ok |
| tool 8B 8× | admit-all (split + LRU) | 11.64 / 20.1 / 58.4 / 116 | +8.98 / +8.84 / +8.77 (**+8.86**) | +4.42 / +7.56 | +10.0 | +9.30 (12.30) | – | FAIL |
| tool 8B 8× | RQ1-filtered (value_split) | 1.51 / 5.8 / 13.4 / 32 | +1.62 / +1.68 / +1.61 (**+1.64**) | +0.44 / +1.19 | +2.2 | +1.39 (1.51) | – | ok |
| tool 8B 8× | filtered + live budget (independent) | 1.38 / 5.3 / 11.0 / 24 | +1.40 / +1.12 / +1.19 (**+1.24**) | +0.40 / +1.03 | +1.6 | +1.04 (1.28) | 4,836 → 4,393–4,411 / 425–443 (9%) | ok |
| tool 70B 4× | admit-all (split + LRU) | 15.77 / 33.5 / 77.5 / 131 | +15.73 / +15.71 / +15.65 (**+15.70**) | +5.45 / +12.19 | +19.2 | +13.66 (16.13) | – | FAIL |
| tool 70B 4× | RQ1-filtered (value_split) | 1.43 / 6.4 / 16.4 / 38 | +2.32 / +2.31 / +2.31 (**+2.31**) | +0.12 / +1.61 | +2.7 | +1.32 (1.42) | – | ok |
| tool 70B 4× | filtered + live budget (independent) | 1.27 / 6.0 / 9.5 / 27 | +1.05 / +1.61 / +1.68 (**+1.45**) | +0.16 / +1.21 | +2.0 | +0.99 (1.21) | 3,611 → 3,194–3,198 / 413–417 (11%) | ok |

Null: the Adam step alone, quiet window vs the following 7 minutes: p99 0.0% / −0.6% / −0.1% (3 runs; per-minute p99 −1.0 … +0.4%).

1. **Admit-all breaks the SLO on the hardware at every configuration**: p99 +8.3 … +9.0% at 8B 8× and +14.1 … +15.7% at
   70B 4×, with the median step +4.4 … +6.0% — the whole step-time distribution shifts (fig-hwval-timeline, top). The
   2026-10-12 finding reproduces with the Phase 3 stream itself.
2. **The RQ1-filtered stream stays inside the SLO with margin**: p99 +1.6 … +2.8% (median +0.1 … +0.5%), busiest minute
   ≤ +3.3%. The harm is small, not zero, and larger for 70B blocks, whose 1-s peaks reach 6.4–7.9 GB/s (the measured
   safe budget's edge).
3. **The live budget does act**: 9–29% of the DRAM candidates were redirected to CXL (the hash-share candidates of a long
   prompt or of concurrent requests arrive faster than B × 70 ms refills one block), the DRAM stream drops to
   1.1–1.4 GB/s with the 10-ms p99 pinned at one block in flight (6.7 / 9.5 GB/s), and Adam's p99 improves by 0.4–1.6
   points to +1.0 … +1.7%. The Phase 3 text's "0 budget refusals" was wrong (correction below).
4. **Repeatability**: ≤ 0.7 points between repetitions in every cell; null runs −0.6 … 0.0%. Differences of ≥ 1 point are
   real; the filtered-vs-budget gap is solid at 70B 4× (1.6 / 0.9 points) and marginal at 8B 8× (0.4–0.7).
5. **Bursts the per-second average hides are there after filtering**: measured 10-ms p99 13–17 GB/s (9–11× the mean), 10-ms
   maxima 27–38 GB/s, 1-s maxima 5–8 GB/s (fig-hwval-bursts). They are what costs the ~1 point that the mean-rate curve
   does not predict (Task F).

## Task F — the Phase 3 cost model against the hardware
| configuration | admit-all: predicted → measured [range] (Δ points) | filtered: predicted → measured (Δ) | filtered + budget: predicted → measured (Δ) |
|---|---|---|---|
| conv 8B 8× | +10.1 → +8.60 [+8.25, +8.98] (−1.5) | +1.4 → +1.84 [+1.75, +1.89] (+0.5) | +0.9 → +1.10 [+1.05, +1.12] (+0.2) |
| conv 70B 4× | +13.9 → +14.47 [+14.10, +14.72] (+0.5) | +1.4 → +2.67 [+2.45, +2.81] (+1.2) | +0.8 → +1.10 [+0.98, +1.19] (+0.3) |
| tool 8B 8× | +9.3 → +8.86 [+8.77, +8.98] (−0.4) | +1.4 → +1.64 [+1.61, +1.68] (+0.2) | +1.0 → +1.24 [+1.12, +1.40] (+0.2) |
| tool 70B 4× | +13.7 → +15.70 [+15.65, +15.73] (+2.0) | +1.3 → +2.31 [+2.31, +2.32] (+1.0) | +1.0 → +1.45 [+1.05, +1.68] (+0.5) |

- **F1 — peaks:** the DRAM-targeted stream on the hardware equals the replay plan at 1 s, 100 ms and 10 ms (Task C), and
  keeps doing so beside Adam (start delay p99 ≤ 0.2 ms, max ≤ 3.2 ms in every co-run).
- **F2 — filtered p99:** measured +1.6 … +2.8% against a predicted +1.3 … +1.5%: right in sign, order and verdict (inside
  the 7% SLO by ≥ 4 points), low by 0.2–1.2 points, the error growing with the block size. With the live budget
  +1.1 … +1.5% measured vs +0.8 … +1.0% predicted (+0.2 … +0.5).
- **F3 — admit-all:** +8.6 … +15.7% measured vs +9.3 … +13.9% predicted (−1.5 … +2.0): the curve is right where it was
  calibrated (the hash-split family at 12–16 GB/s) and slightly low for the tool-agent 70B stream, whose 100-ms peaks
  (67 GB/s) exceed the conversation stream's (46) at the same mean.
- **F4 — non-linearity:** p99 is not proportional to the mean rate: a tenth of the admit-all rate costs a fifth of its
  p99 (70B 4×: 1.6 vs 16.5 GB/s → +2.7 vs +14.5%), and at nearly the same mean the burstier filtered stream costs 2.4×
  the budget-gated one (+2.7% at 1.58 GB/s vs +1.1% at 1.13 GB/s). The burst structure, not only the mean, sets the
  cost at the 1-point level.
- **F5 — short bursts:** present after filtering (10-ms bursts 10–20× the mean), absent from the model (which maps a
  family's mean rate to p99). Their cost is ~1 point of p99 at 70B: inside the margin, a systematic bias nevertheless.
- **F6 — DRAM write parallelism:** 64 workers on two CCDs sustained every stream with no backlog beyond the bytes in
  flight (≤ 2.9 GB); the model's assumption that DRAM writes complete at line rate holds up to 16.5 GB/s mean / 130 GB/s
  in 10 ms.
- **F7 — CXL read/write contention:** NOT tested (blocker); the 46 GB/s path and its backlog remain model-based.
- **F8 — CPU / CCD topology:** changes the result (controls below): the same filtered stream written from Adam's own CCD
  costs +5.4 … +6.5% instead of +2.7%, of which the CPU sharing itself is worth ≤ 2.4 points (measured with the
  admit-all thread pattern); the admit-all stream from Adam's CCD +33% instead of +14.5%. The Phase 3 curves — and every
  interference number of this project — hold for a writer on a core group the victim does not use.

**Correction to `2026-10-21-joint-benefit-analysis.md` (frozen; recorded here):** that file says "the token bucket at the
selected 2–32 GB/s refuses nothing: 0 DRAM-budget refusals in the test runs" and "0 drops, 0 vetoes, 0 budget refusals in
every test run". Drops and vetoes are right; the refusals are wrong: the file's own CSVs show `indep` writing 15–35% fewer
DRAM blocks than `value_split` under the same admission (conv 70B 4×: 2,529 vs 3,863; conv 8B 8×: 3,464 vs 4,624; tool 70B
4×: 3,039 vs 3,563; tool 8B 8×: 4,070 vs 4,770; conv 70B 8×: 2,824 vs 3,765) — those are DRAM candidates the bucket sent
to CXL; the hardware's live bucket sends 9–29%. The Phase 3 hit shares and write volumes already include these
redirections, so no number there changes; the sentence "the cost module never fires" has to be read as "the congestion
drop and the regime veto never fire" — the budget-gated placement does act, value-blind, and the joint policy inherits it.

## Controls — writer placement and store primitive (`ctrl/`, 70B 4× conversation beside Adam; HW)
| control | Adam p99 slowdown (runs) | median | the same stream from CCDs 6–7 with NT stores | reading |
|---|---|---|---|---|
| admit-all, 32 writers on CCD 4 (Adam's cpus 64–79 + SMT siblings) | +33.3 / +32.6% | +13.1% | +14.5% | writing from the victim's own core group more than doubles the harm |
| same threads, same pacing, no memory traffic (`--store none` on CCD 4) | +2.5 / +2.3% | +0.7% | – | the CPU-sharing part is ~2.4 points; the other ~16 points are the memory path of the shared CCD |
| same, from CCDs 6–7 | +0.07% | +0.07% | – | the replayer's own CPU use from another CCD costs nothing |
| filtered, writers on CCD 4 | +5.4 / +6.5% | +0.07% | +2.7% | inside the SLO without margin (busiest minute +8.5%) |
| admit-all, regular stores (read-for-ownership + write-back) from CCDs 6–7 | +30.4% | +12.4% | +14.5% | the primitive matters 2×: regular stores read every line first |
| filtered, regular stores | +6.1 / +6.1% | +0.07% | +2.7% | at the SLO edge (busiest minute +7.4%) |

The interference numbers of this file are conditions as much as measurements: they hold for a writer on a core group
other than the victim's, with writes that do not read the destination (non-temporal stores here, DMA writes in the real
system). On the victim's CCD, or with ordinary stores, the filtered stream's cost doubles to +5–6.5% — still inside the
7% SLO, with no margin — and the admit-all stream fails by 4–5×.

## The heaviest Phase 3 configuration — 70B 8× conversation (`x8/`, 2 runs each; HW)
| stream | DRAM GB/s: mean / 1-s max / 10-ms p99 (HW) | Adam p99 slowdown | median | Phase 3 prediction | live bucket (12 GB/s): candidates → written / redirected |
|---|---|---|---|---|---|
| admit-all | 31.6 / 57.7 / 93 | +24.6 / +25.4% | +12.7% | +36.0% (extrapolated beyond the 24 GB/s calibration range, flagged in Phase 3) | – |
| RQ1-filtered | 3.11 / 11.1 / 19.0 | +4.06 / +3.93% | +0.84% | +2.84% | – |
| filtered + live budget | 2.45 / 7.3 / 9.5 | +2.38 / +2.45% | +0.80% | +1.91% | 3,862 → 3,043 / 819 (21%) |

At the heaviest real configuration the filtered stream costs +4.0% (inside the SLO by 3 points; the model said 2.8), the
budget brings it to +2.4%, and the admit-all stream +25% (the model's extrapolation said 36: the curve bends above its
calibrated range).

## Task G — what the hardware changes in the research assessment (Deliverable 5)
- **Does real hardware support "filtered traffic has negligible interference"?** Small, not negligible, and inside the SLO
  with margin: +1.6 … +2.8% at 8B 8× / 70B 4×, +4.0% at 70B 8× (p99; medians ≤ 0.8%), repeatable to ±0.4 points, against
  +8.6 … +25% for admit-all. **Case A** of the brief holds for the DRAM side, under the conditions above (NT / DMA-like
  writes from another core group) and within the evidence boundary (CPU replay, CXL part not issued, Adam as the victim).
- **Does the independent budget still have real work?** Yes: it redirects 9–29% of the DRAM candidates on the real clock
  and buys 0.4–1.6 points of p99 (more at larger blocks and loads). It is a value-blind safety mechanism that acts on
  the bursts the admission leaves; Phase 3's "0 refusals" is corrected above. Its action does not change the Phase 3
  comparison, which already included it (the independent and the joint policy both place through it).
- **Was any DRAM/CXL resource contention missed?** Three things, two of them conditions rather than costs: (1) the
  10-ms burst structure of the filtered stream costs ~1 point of p99 beyond the mean-rate model — a modelling bias,
  inside the margin; (2) writer threads on the victim's CCD double the harm (a placement condition the system must
  keep, as `cxlpathd` already does for CXL writers); (3) read-for-ownership stores double it (the write path must stay
  DMA-like or non-temporal). CXL read/write contention on the cards remains untested this round.
- **Has the evidence on the core hypothesis changed?** No. The hardware confirms the premise of the Phase 3 result: after
  value-aware admission the DRAM-side movement cost is small enough that there is nothing left to trade off against
  value at these scales; the residual the budget removes (~1 point) is value-blind. The joint-vs-independent comparison
  of Phase 3 stands as it was, with the model's bias (≤ 1.2 points) far below the SLO margin and symmetric between the
  policies.
- **Worth entering the minimal system implementation?** Not on H2 — the Phase 3 recommendation is unchanged. What the
  hardware adds is a positive, measured statement for the RQ1 + RQ3 claim: reuse-aware admission turns a stream that
  breaks the neighbour's SLO by 1.2–3.6× into one that fits it with margin, on the real machine, and a budget-gated split
  behind it keeps the residual bursts in check. The boundary that still has to be stated with it: CPU replay of the
  DRAM-targeted part; the CXL path untested since the 2026-10-18 reboot (admin fix needed); one victim.

