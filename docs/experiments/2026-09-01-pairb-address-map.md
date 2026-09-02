# 2026-09-01 — Pair B address map: which mmap offset hits which card

**STATUS: CLOSED. Verdict: Pair B is 256-byte striped across its two cards with
PLAIN MODULO selection — `card = (offset >> 8) & 1` — uniform across the whole
512 GiB. Software CAN target an individual card of Pair B through /dev/dax2.0.**
Raw: `experimental_results/2026-09-01-pairb-address-map/`.

## Setup
Admin switched dax2.0 to devdax (2026-09-01 17:45) and granted group kmem
(0660). /dev/dax2.0 = Pair B = cards at PCI 01:00.0 (mem1, via port3 dport0 =
00:01.1) and 02:00.0 (mem3, via dport1 = 00:01.2); root decoder0.2 ways=1 →
port3 decoder3.0 ways=2 gran=256 (locked). Tools: `cxlprobe` daxstream /
daxchase / **daxstride (new mode, this date)**; all reads (PROT_READ), memory
idle and unowned. Co-runs = two processes on separate CCDs (`--cpu-offset` 0
vs 16). 3 reps (P3b: 2). Hypotheses tested: H-concat (halves = cards),
H-stripe (256 B modulo), H-hash (XOR of higher bits, as E1 found on Pair A).

## P1 — halves solo (128 GiB vs 384 GiB offsets)
| | chase p50 / mean | 8T stream |
|---|---:|---:|
| low half @128G | 219 ns / 222–227 | 46.0 GiB/s |
| high half @384G | 219 ns / 226–227 | 46.0 GiB/s |
Both halves reach the PAIR ceiling → **H-concat refuted**.

## P2 — co-run scaling (8T + 8T, separate CCDs)
same-low 24.0+24.0 · same-high 24.0+24.0 · cross-half 24.0+24.0 GiB/s — identical
everywhere: one shared device pair, no address-range partition.

## P2L — chase @128G under 8T load
idle p50 219 → 279 (same half @160G) / 269–289 (other half @384G); means ~300
vs ~325 ns. Load anywhere in the window slows a chase anywhere.

## P3 — 256-byte classes (stride 512, chunk 256, offset 0 = even / 256 = odd)
| config | GiB/s |
|---|---:|
| even class alone (8T) | 23.9 / 23.9 / 23.8 |
| odd class alone (8T) | 23.9 / 23.9 / 23.7 |
| all chunks (control) | 44.9 / 44.8 / 44.9 |
| even (CCD0) + odd (CCD1) | 22.3+22.0 = **44.3** · 21.1+21.0 · 21.4+21.3 |
| even + even (control) | 12.6+11.7 = **24.3** · 12.4+12.0 · 12.3+12.0 |
Each class alone = exactly one card's ceiling; even+odd fill the pair; even+even
share one card → **H-stripe with plain modulo. H-hash refuted for Pair B.**

## P3b — parity uniformity across the window
even@1G co-run with even@{33, 129, 257, 385, 500} GiB → always ~12+12 = 24 GiB/s
(shared card). The parity rule holds across address bits 30–38; no higher-bit
XOR term.

## The rule (with assumptions stated)
```
off  = byte offset within /dev/dax2.0            (= HPA − window base)
pos  = (off >> 8) & 1                            (256 B granularity, 2 ways)
card = decoder3.0.target_list[pos]               (pos 0 → dport0 → 00:01.1 → mem1
                                                  pos 1 → dport1 → 00:01.2 → mem3)
DPA  = (off >> 9) << 8 | (off & 0xFF)
```
**Proven:** the two 256-B parity classes are two physically distinct cards
(disjoint ceilings, additive co-run, uniform across 512 GiB). **Assumption:**
the LABELS — which class is the card at 01:00.0 vs 02:00.0 — come from
decoder3.0's target_list order; not yet counter-verified (DF PMU / telemetry
needs root; disjointness is what the experiments need, labels are cosmetic).

## First single-CZ120 numbers
Per-card sequential read ceiling **23.9 GiB/s @8T** (≈ x8 PCIe-5 link). Pair
ceiling 44.9–46.0. Whole-pair chase 219 ns p50 / ~225 mean — the lowest CXL
latency measured on this machine (May Pair B: 276.5 ns; the 2026-08-27 BIOS
visit also sped up DRAM, so no single cause is attributed).

## Corrections to earlier records
- `hardware/results/2026-08-28-post-reboot-fused-node.log` said a
  "linear/concatenated layout [is] implied" for Pair B — **refuted** here.
- The endpoint decoders' sysfs (`ways=1`, 256 GiB each) was the misleading
  half; `decoder3.0 ways=2 gran=256` is what the hardware does.
- E1 (2026-08-11) showed root-level interleave on Pair A is hashed — that stands
  and still makes Pair A unsplittable. Pair B's host-bridge-level interleave uses
  plain bits, so the same stripe trick that failed on Pair A works here.

## What this unlocks (no further admin change needed)
Per-card experiments via dax offsets: card-vs-card interference behind one host
bridge (the never-published measurement), per-card write streams with hot reads
on the neighbor card (Gate-2's co-location knob at card granularity), per-card
direction matrices. Pair A stays the "normal" CXL NUMA node (node 1, 508 GiB).
Housekeeping: /dev/dax2.0 perms reset on any rebind/reboot without a udev rule.
