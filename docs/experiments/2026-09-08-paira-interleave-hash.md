# 2026-09-08 — Is Pair A (/dev/dax0.0) interleaved, and can we address its cards?

**STATUS: CLOSED. Verdict: Pair A IS interleaved and the card selection is
HASHED — no single address bit, and no XOR of bits 8/9, isolates a card.
Per-card targeting is impossible on Pair A. Pair B remains the only per-card
instrument on this machine.** Raw:
`experimental_results/2026-09-08-paira-interleave-hash/`.

## Why this ran
Advisor (2026-09-08): "I made dax0.0 devdax as well, so check if that one has
interleaving. Don't only trust the /sys filesystem but experimentally check!"

## Setup
Machine booted 2026-09-05 10:48. `/dev/dax0.0` (242.5 GiB) and `/dev/dax2.0`
(512 GiB) are devdax, root:kmem 0660; `dax1.0` (269.5 GiB) is system-ram = NUMA
node 1. **dax0.0 and dax1.0 are two windows over the SAME physical pair (Pair A)
— they are not independent resources.** Pair A = mem0 (PCI e1:00.0, host bridge
pci0000:e0) + mem2 (c1:00.0, pci0000:c0); `decoder0.0` ways=2 gran=256
target_list=7,6 → this is a LEVEL 1 (root/CFMWS) interleave across two host
bridges, unlike Pair B whose interleave is LEVEL 2 (host bridge `decoder3.0`).

Method (`hardware/scripts/bitprobe.sh`, `cxlprobe --mode=daxstride`): for each
candidate address bit b, read only the chunks where bit b = 0 (stride 2^(b+1),
chunk 2^b, offset 0) and separately where bit b = 1. If bit b selects the card,
one class can reach at most ONE card's ceiling (~22–24 GiB/s here). Then
concurrent co-runs on separate CCDs, and an XOR(bit8,bit9) test.

## Results (8 threads, 3 s; pair ceiling ≈ 45.3 GiB/s, single card ≈ 22.7)
| selecting bit | Pair A class0 / class1 | Pair B class0 / class1 (control) |
|---|---:|---:|
| 8  (256 B)   | 34.07 / 33.33 | **23.90 / 23.88  ← one card** |
| 9  (512 B)   | 43.76 / 38.69 | 43.37 / 42.25 |
| 10 (1 KiB)   | 44.98 / 43.97 | 44.02 / 44.64 |
| 11 (2 KiB)   | 45.05 / 44.34 | 44.51 / 44.62 |
| 12 (4 KiB)   | 44.61 / 44.51 | 44.10 / 44.39 |
| 14 (16 KiB)  | 39.29 / 39.73 | 39.50 / 38.80 |
| 16 (64 KiB)  | 42.00 / 41.53 | 41.96 / 40.48 |

Concurrent co-runs (bit-8 classes, two processes on separate CCDs):
| | Pair A | Pair B (control) |
|---|---:|---:|
| even + even | 41.6 GiB/s | **24.4 (one card shared)** |
| even + odd  | 41.7 GiB/s | 43.7 (two cards) |

XOR(bit8,bit9) test on Pair A (stride 1024, chunk 256): off0+off256 = 32.4,
off0+off512 = 32.5, off0+off768 = 32.3 — all identical, so the XOR of bits 8
and 9 does not select a card either.

## Findings
1. **Pair A is interleaved** — a single 8T stream over the whole window gets
   45.3 GiB/s, double a single card's ~22.7 ceiling.
2. **The card selection is hashed.** Every bit class exceeds a single card's
   ceiling, and same-class co-runs contend exactly as much as different-class
   co-runs (41.6 vs 41.7). There is no address partition to exploit.
3. **The method is sound** — the identical sweep on Pair B cleanly finds its
   plain 256 B stripe (23.90 / 23.88 at bit 8, everything else ~44), so a
   partition would have been detected on Pair A if one existed.
4. Confirms E1 (`2026-08-11-percard-prelim.md`) with much better methodology:
   E1 inferred hashing through NUMA-allocated memory; this uses exact physical
   offsets through devdax.
5. Structural note: **Pair A's interleave is at LEVEL 1 (across host bridges),
   Pair B's is at LEVEL 2 (across root ports of one host bridge).** The AMD
   root/CFMWS path hashes; the host-bridge path uses plain address bits. That
   is why the same trick works on one pair and not the other.

## Consequences
- Per-card experiments stay Pair-B-only. Pair A is usable as a *pair* (either
  as devdax `dax0.0` or as NUMA node 1 via `dax1.0`), never per card.
- Independent CXL units available today: **Pair A** (dax0.0 / node 1) and
  **Pair B** (dax2.0). Two units, both contiguous-mmap-able → cross-pair
  experiments with app-shaped buffers are unblocked.
