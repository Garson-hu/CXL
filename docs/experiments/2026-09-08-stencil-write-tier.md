# 2026-09-08 — Stencil (pond) with `new` on CXL: rotation strategies

**STATUS: PART 3b DONE 2026-09-08 (CXL-side comparison on crippled DRAM) ·
PART 3c (Case A vs Case B on healthy DRAM) BLOCKED on the BIOS revert.**
Campaign Phase 3 of `2026-09-08-write-tier-campaign.md`. Code:
`benchmarks/stencil/pond.c` (build line in the header); driver
`hardware/scripts/stencil-3b.sh`; raw `experimental_results/2026-09-08-stencil-write-tier/`.

## The benchmark
1-D leapfrog wave stencil: `new[i] = 2·cur[i] − old[i] + c·(cur[i−1] − 2·cur[i] + cur[i+1])`.
Three 8 GiB buffers (≫ 256 MB L3), 16 compute threads on CCD0–1, per step:
read old + cur (16 GiB), write new (8 GiB). Knobs: per-buffer placement
{dram, node1, daxA, daxB}, normal vs NT stores for `new`, threads, steps.
Policies (the rotation problem — next step's `cur` IS last step's `new`):
- **rotate** — pointer rotation; a CXL buffer takes the read role 2 of every 3 steps.
- **copyback** — roles fixed; after compute, copy new (CXL) → the DRAM buffer that will be `cur`.
- **migrate** — copyback whose copy trails the compute chunk-by-chunk on 8 copier threads (CCD4), overlapping.
- **pingpong** — two devices: `cur` is read from the device written last step, `new` goes to the
  other device, `old` is a DRAM copy of `cur` made by copier threads during compute (lagged migration).
  Reads and writes land on different devices every step.

## 3b results — 16 threads, 20 steps, steady-state median (steps 4–20), seconds per step
**Machine caveat that dominates this table:** DRAM interleaving is disabled in BIOS
(`hardware/results/2026-09-08-dram-interleave-regression.log`): DRAM delivers ~25–41 GiB/s
vs CXL Pair B's 45. In this state DRAM — not CXL — is the scarce resource.
| policy | normal stores | NT stores | DRAM traffic / step | CXL traffic / step |
|---|---:|---:|---|---|
| A: all DRAM, rotate | 1.119 | 0.784 | 24 GiB (+8 RFO) | — |
| B: rotate (new→daxB) | 0.555 (0.42–0.84) | 0.442 | mixed, rotates | mixed, rotates |
| B: copyback | 0.762 | 0.768 | 16 rd + 8 wr (copy) | 8 rd (copy) + 8 wr |
| B: migrate | 0.803 | 0.774 | 16 rd + 8 wr (overlapped) | 8 rd + 8 wr |
| B: pingpong (daxB/daxA) | 0.565 (0.49–0.57) | 0.458 | 8 rd + 8 wr (copy) | 16 rd + 8 wr, two devices |
Rotate per-step pattern (normal stores): read-cur-from-CXL step 0.42 s; all-DRAM step 0.56 s;
write-new-to-CXL step 0.84 s (normal stores to CXL = 8 GiB RFO reads + 8 GiB writebacks over the link).

## What 3b establishes (and what it cannot yet)
1. **The benchmark's accounting is consistent with the microbenchmarks:** all-DRAM 24 GiB/step
   in 1.119 s = 21 GiB/s effective (32 GiB with RFO → 29 GiB/s), matching crippled-DRAM
   membench (25–41). Every policy runs correctly (role rotation verified step by step).
2. **NT stores pay everywhere:** all-DRAM 1.119 → 0.784 s (−30%: the RFO tax removed on
   DRAM); CXL write steps also drop (rotate 0.555 → 0.442).
3. **In today's state the ranking is inverted relative to the thesis:** with DRAM at ~28 GiB/s
   and CXL at 45, every byte moved OFF DRAM helps — including READS. Hence rotate and
   pingpong (both read `cur` from CXL) beat copyback/migrate (which pay an extra DRAM
   write per step) and all beat all-DRAM by ~2×. **This is a preview of the
   high-DRAM-pressure regime the thesis targets, not a verdict on the strategies:** the
   intended trade-off (cheap DRAM reads vs expensive CXL reads) does not exist while DRAM
   is crippled. 3c on healthy DRAM (~95 GiB/s) is required to rank the strategies.
4. **Pingpong is the most stable** (min–max 0.49–0.57 vs rotate's 0.42–0.84) and has the
   lowest DRAM traffic per step (16 GiB) — the property that should matter once DRAM is the
   contended tier; its two-device split matches the 9/2 isolation result (reads on one
   device, writes on the other).
5. Migrate's overlap buys nothing here because the copy's destination (DRAM) is the
   bottleneck; it is designed for the regime where CXL→DRAM copy bandwidth is spare.

## 3c plan (after BIOS revert)
Same matrix on healthy DRAM, plus: 32 threads; footprint 3 × 16 GiB; an explicit
DRAM-pressure aggressor (8T NT writers on node 0, separate CCD) to reproduce the regime
where write-tier placement should pay; report per-step time, DRAM read BW, CXL write BW.
Decision rule: write-tier wins if copyback/migrate/pingpong beat all-DRAM under pressure
while rotate does not.
