# 2026-08-11 — Per-card preliminaries (E1–E4) + NPS4 postscript

**STATUS: CLOSED (frozen); the per-card direction is PARKED. Verdict in
`INDEX.md`.** Machine at run time: node 1 = Pair A (mem0 e1:00.0 + mem1
c1:00.0), dax2.0 = Pair B under famfs FUSE (root, since 2026-06-18). Tools:
`benchmarks/memory/cxlprobe.c` (written for this campaign) + `membench` (May
parameters). Raw log: `hardware/results/2026-08-11-prelim-fourexp.log`.

## E1 — stripe-trick: can software address one card of a 2-way pair? **NO**
256 B / 2-way interleave ⇒ reading every other 256 B slice should isolate one
card if way = PA bit 8. Measured: full-seq 47.5 GiB/s; offset-0 class 37.8;
offset-256 class 36.7 — **both classes exceed a single card's ~24 GiB/s x8
ceiling**, and an A+A co-run reaches ~full-pair bandwidth (40.9 total). ⇒ AMD
Turin hashes way-selection with address bits above the page offset; no
page-color trick can target a card (THP also unavailable on the CXL node:
AnonHugePages=0, MADV_COLLAPSE rc=-1). **Implication: BIOS de-interleave is the
only path to per-card control.**

## E2 — cross-pair interference: **BLOCKED**
/dev/dax2.0 opens + mmaps but SIGBUS on first read — famfs FUSE holds the
device exclusively; famfs volume empty; file creation is root-only. Needs a
world-readable famfs file OR ~1 h unmount. Tooling ready (`cxlprobe
daxstream/daxchase`).

## E3 — tail latency (chase, 4 GiB region, 2 M samples)
| config | mean | p50 | p90 | p99 | p99.9 | p99.99 | max (ns) |
|---|---:|---:|---:|---:|---:|---:|---:|
| cxl idle | 291.4 | 279 | 299 | 559 | 679 | 3449 | 84009 |
| cxl +4T load | 351.6 | 320 | 460 | 690 | 840 | 2950 | 150650 |
| cxl +12T load | 345.5 | 319 | 419 | 689 | 799 | 2359 | 21749 |
| dram idle | 178.8 | 169 | 229 | 329 | 439 | 1769 | 17539 |
| dram +12T load | 179.7 | 169 | 229 | 329 | 429 | 1969 | 17319 |

**No Melody-style µs p99.9 tails on CZ120** (sub-µs at all loads); p99.99+
spikes appear on BOTH nodes (system noise). Real signal: CXL median +15% / p90
+40–54% under own load while DRAM is flat ⇒ **congestion, not spikes, is the
design signal**; tail-aware routing looks weak on this hardware.

## E4 — twins: Pair A (today) vs Pair B (2026-05-19), same membench params
| metric | Pair B (May) | Pair A (Aug 11) | Δ |
|---|---:|---:|---:|
| ptr-chase latency | 276.5 ns | 295.9 ns | +7.0% |
| seq read 1T | 19.5 | 16.65 GiB/s | −14.6% |
| seq write 1T | 18.5 | 15.65 GiB/s | −15.4% |
| random read 1T | 1.58 | 1.48 GiB/s | −6.4% |
| stream-read 4T | 35.6 | 31.26 GiB/s | −12.2% |
| stream-read 32T | 35.5 (flat @4T) | **47.72 (still scaling)** | **+34.4%** |

DRAM drift control across the 3 months: latency +11%, seq read −3.7% ⇒ small
deltas inconclusive, the +34% ceiling gap far exceeds drift. Hypothesis: Pair A
"farther but wider" (spans two fabric quadrants → two I/O paths), Pair B
single-quadrant (one path → 35.5 flat).

## Postscript 2026-08-14 — NPS4 reboot CONFIRMS the E4 hypothesis
Admin BIOS visit (~08-12) switched NPS1→NPS4 (nodes 0–3 = CPU quadrants,
node 4 = CXL Pair A). CXL decoders UNCHANGED (3 windows, all 2-way/256 B) — the
CXL de-interleave knob was not applied; the "3 dax regions vs 4 cxl devices"
puzzle is firmware window carving, not a kernel flaw. NPS4 exposes per-card
affinity: **mem0→node 3, mem1→node 0 (Pair A spans quadrants 0+3); mem2,
mem3→node 1 (Pair B in one quadrant)** — independent confirmation of the
farther-but-wider hypothesis. Speeds re-verified: CXL 287 ns / 45.4 GiB/s @8T;
DRAM node 0 improved to 174.8 ns (quadrant-local). Log:
`hardware/results/2026-08-14-post-reboot-nps4-check.log`.

## Why parked
Per-card control still needs the BIOS CXL-interleave change (advisor lukewarm;
needs a real-app motivation to reopen). E1's negative result, E3's congestion
signal, and E4's +34% remain citable characterization for the direction-aware
thesis (`../PAPER.md`).
