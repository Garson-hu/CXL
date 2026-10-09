# 2026-10-09 — KV-cache capacity characterization: how much host memory does the KV cache need, and what is extra capacity worth?

**STATUS: CLOSED 2026-10-09.** Raw: `experimental_results/2026-10-09-kv-capacity-characterization/` (`kv-capacity.txt`,
`kv-capacity.csv`). Script: `scripts/kv_capacity_characterization.py` (reproduces everything below; ~1 min).
Traces: Mooncake FAST'25 `workloads/mooncake_{conversation,toolagent,synthetic}_trace.jsonl` (512-token hash blocks).

## Question
For the advisor's unified DRAM/CXL pool (discussion of 2026-10-09): when DRAM holds *copies* of CXL blocks (our read
path v2 of 2026-10-06), it adds no capacity; when DRAM holds *other* blocks (each block in exactly one place), it adds
its full size. How much does that extra capacity change the share of reuses that find their block in host memory,
for host memory the size of c28's CXL pair?

## Method and assumptions
Three kinds of numbers, kept apart:
1. **Trace counts (exact, no assumption about hardware or model).** Blocks are the traces' hash IDs; an access is a
   request containing the block (each block once per request, prefix order); a reuse is any access after the first.
2. **Model conversion (assumption: KV bytes per token from the published model configuration, bf16).**
   Llama-3.1-8B: 32 layers × 8 KV heads × 128 × 2 × 2 B = 128 KiB/token = 64 MiB/block.
   Llama-3.1-70B: 80 layers × 8 KV heads × 128 × 2 × 2 B = 320 KiB/token = 160 MiB/block.
3. **LRU simulation (exact stack distances; modelling assumptions):** every block is stored in host memory when first
   computed; every later access reads it from host memory, i.e. **no GPU-side prefix cache in front**; LRU eviction;
   uniform block size; all requests of a trace served by one host (the traces' arrival rate as is).
No hardware speed enters any number in this file except the separate, labelled section "Speeds that matter for
interpreting the result".

## Results — trace counts (exact)
| trace | requests | span | distinct blocks | new blocks/s | reuses/s | never reused (all / first half of span) | share of reuses going to blocks reused ≥ 10 times |
|---|---|---|---|---|---|---|---|
| conversation | 12,031 | 3,537 s | 182,790 | 51.7 | 29.9 | 75.8% / 72.6% | 24.7% (0.50% of blocks) |
| toolagent | 23,608 | 3,537 s | 183,300 | 51.8 | 64.0 | 78.5% / 76.2% | 67.5% (0.51% of blocks) |
| synthetic | 3,993 | 1,022 s | 43,924 | 43.0 | 76.3 | 58.4% / 55.9% | 18.5% (2.33% of blocks) |

The end-of-trace effect on "never reused" is 2–3 points (blocks first seen in the first half have half the trace
left to be reused).

## Results — model conversion (assumption 2)
| trace | 8B: distinct KV / new KV / reuse reads | 70B: distinct KV / new KV / reuse reads |
|---|---|---|
| conversation | 11,424 GiB / 3.23 GiB/s / 1.87 GiB/s | 28,561 GiB / 8.07 GiB/s / 4.67 GiB/s |
| toolagent | 11,456 GiB / 3.24 GiB/s / 4.00 GiB/s | 28,641 GiB / 8.10 GiB/s / 10.00 GiB/s |
| synthetic | 2,745 GiB / 2.69 GiB/s / 4.77 GiB/s | 6,863 GiB / 6.72 GiB/s / 11.92 GiB/s |

(Averages over the span; host-memory capacity on c28 is far below the distinct KV of every trace.)

## Results — LRU simulation (assumption 3): share of reuses served from host memory
8B model, by host capacity:

| capacity (GiB) | 40 | 80 | 242.5 | 512 | 592 | 768 | 1024 | 2048 |
|---|---|---|---|---|---|---|---|---|
| conversation | 0.12 | 0.13 | 0.23 | 0.49 | 0.55 | 0.64 | 0.72 | 0.91 |
| toolagent | 0.61 | 0.62 | 0.67 | 0.80 | 0.82 | 0.86 | 0.90 | 0.98 |
| synthetic | 0.09 | 0.15 | 0.35 | 0.59 | 0.64 | 0.74 | 0.83 | 0.98 |

Copies vs other blocks in DRAM (c28 CXL pair = 512 GiB in two windows; dax0.0 alone = 242.5 GiB):

| host memory | conversation 8B | toolagent 8B | synthetic 8B | conversation 70B | toolagent 70B | synthetic 70B |
|---|---|---|---|---|---|---|
| CXL 512 alone (= DRAM holds copies) | 0.49 | 0.80 | 0.59 | 0.19 | 0.65 | 0.31 |
| CXL 512 + DRAM 80 holding other blocks | 0.55 (+0.05) | 0.82 (+0.03) | 0.64 (+0.05) | 0.22 (+0.03) | 0.67 (+0.02) | 0.35 (+0.03) |
| CXL 512 + DRAM 256 holding other blocks | 0.64 (+0.14) | 0.86 (+0.06) | 0.74 (+0.15) | 0.30 (+0.10) | 0.70 (+0.05) | 0.44 (+0.12) |
| CXL 242.5 alone | 0.23 | 0.67 | 0.35 | 0.13 | 0.62 | 0.19 |
| CXL 242.5 + DRAM 256 holding other blocks | 0.48 (+0.26) | 0.79 (+0.12) | 0.58 (+0.23) | 0.19 (+0.05) | 0.65 (+0.03) | 0.31 (+0.12) |

(Differences computed before rounding.) A 40 GiB cache catches 12% / 61% / 9% of the 8B reuses: in a deployment
with a GPU-side prefix cache of that size those reuses never reach host memory, which the simulation ignores.

## Speeds that matter for interpreting the result (not used in any number above)
- Measured on c28 (`2026-10-07-read-cost.md`): the RTX 4060 Ti reads 1 GiB at 12.49 GiB/s from pinned DRAM and
  12.48 GiB/s from registered CXL; a processor's dependent read is 1.67× slower from CXL.
- External, not measured by us (LMCache blog, 2026-08-04, H100 PCIe): GPU load 55.5 GB/s from pinned DRAM,
  50.1 GB/s from registered Device-DAX, 26.0 GB/s through a staging buffer.
- Estimate, not measured: recomputing one 512-token block of the 8B model costs about 2 × 8e9 × 512 = 8.2e12
  floating-point operations (plus attention over the prefix), roughly 15–25 ms on one H100 at 330–550 TFLOP/s
  effective, against about 1.3 ms to load its 64 MiB at 50 GB/s.

## Verdict
- Host memory for the KV cache is capacity-bound in all three traces: one hour of the chat or agent trace produces
  ~11 TiB of distinct 8B KV, against 512 GiB of CXL on c28.
- Letting DRAM hold blocks that are not in CXL (instead of copies) raises the share of reuses served from host memory
  by +3 to +15 points with the full CXL pair and 80–256 GiB of DRAM, and by up to +26 points next to the 242.5 GiB
  window alone. Copies add nothing to this share.
- The agent trace concentrates two thirds of its reuses on 0.5% of the blocks, so a small cache already serves most
  of them; chat and synthetic need capacity.
- What a hit is worth depends on the speeds above: for GPU-read KV a hit saves a recomputation an order of magnitude
  or more longer than the load, while the DRAM-versus-CXL load difference is ~10% on an H100 (external) and 0 on our
  GPU. The trace data therefore favour using DRAM as extra capacity over using it for faster copies, **for GPU-read
  KV**; whether that holds end to end (TTFT) is the job of the capacity-matched LMCache experiment.
- Limits: no GPU-side cache in front, LRU only, one host for a whole trace, 512-token blocks, no SSD tier.
