# 2026-09-22 — Machine fact: beside a co-running program, an NT write of an all-zero cache line is nearly free, a write of any other line is not

**STATUS: CLOSED 2026-09-22 (a methodology finding; consequences listed at the end).** Raw:
`experimental_results/2026-09-22-zero-line-writes/` (`measurements.txt`, the three test programs).

## Question
Why did the PyTorch producer's stage into CXL run at 28.8 GiB/s beside the 32-thread llama.cpp victim while the
C producer's all-CXL copy ran at 43.4 GiB/s on the same cpus (both 43.4–43.9 alone)?

## Setup
c28; 8 copy/write threads on cpus 96–99 + 112–115 (4 per CCD), 4 GiB per test; source THP-backed and touched;
destination `/dev/dax0.0` at offset 64 GiB, or a touched THP DRAM buffer. Victim: llama.cpp decoding (Qwen2.5-7B
Q8, 32 threads on cpus 0–31), started 45 s before each test. Programs: `cptest.c` (the C producer's per-thread
loop vs `cxlp_copy_in_par`), `datadep.c` (pure NT writes of a constant, pure reads, copies), `datadep2.c` (six
source patterns, copies to CXL and to DRAM).

## Result
The producers were the same; the DATA differed. The C producer touched its snapshot with one 8-byte word per
4 KiB (63 of every 64 cache lines all-zero); the PyTorch tensors hold non-zero values.

| source pattern (copy, 8 threads) | alone → CXL | alone → DRAM | beside llama32 → CXL | beside llama32 → DRAM |
|---|---|---|---|---|
| all zeros | 43.8 | 94.5 | **43.7** | **82.3** |
| one 8 B word per 4 KiB (the old snapshot) | 43.9 | 94.5 | 43.7 | 82.8 |
| one zero line in two | 43.9 | 94.4 | 35.8 | 75.1 |
| one non-zero byte per 64 B line | 43.8 | 94.4 | 28.9 | 19.1 |
| all ones | 43.9 | 94.5 | 29.2 | 18.8 |
| random | 43.9 | 94.3 | **28.8** | **18.7** |

Pure NT writes of a constant beside llama32: zeros 41 GiB/s, ones 27.8. Pure reads: 136 GiB/s for either
source. THP or 4 KiB pages: no difference; Python or C process: no difference.

Reading: the hardware treats a 64-byte line whose bytes are all zero as a special case on the write path (the
granularity is exactly one cache line: a single non-zero byte removes the effect; a half-zero source lands
half-way). Alone, both kinds of write reach the same ceiling (the CXL link, the DRAM write drain), so the
difference is invisible; beside llama.cpp on 32 threads, zero-line writes keep 93–100% of their rate while
data-carrying writes drop to 66% (CXL) and 20% (DRAM). The co-runner matters: beside the 8-thread streaming
reader (~100 GiB/s) a random-data copy into DRAM runs at 92.8 GiB/s (`three-policies-realdata`, reader-dram),
the same as the zero snapshot did (93.7), so the slow path is not triggered by memory traffic alone — what
in llama.cpp triggers it (32 cores of AVX-512 compute; its own write stream; power/fabric clock) is OPEN and
is to be isolated with a compute-only co-runner and a 32-thread reader once the machine is free. The
mechanism is not documented for this CPU; the observation is consistent with a data-less "zero line"
transaction on the fabric or at the memory controller that bypasses whatever resource the data-carrying
writes queue on. The write-drain cliff experiment of 2026-09-08 (`membench`, non-zero pattern), the
phase-1 budgets (`writer.h`: constant 0x5a and a memset(1) source) and the PyTorch producer (item 3 of
`2026-09-22-moderate-pacing-dcp.md`) all wrote data-carrying lines and stand. **The phase-2 C producer
(`ckpt_producer.c`) copied a 98%-zero snapshot in every run of `2026-09-22-three-policies.md` and in
items 1–2 of `2026-09-22-moderate-pacing-dcp.md`; those copy rates (all-DRAM 86–94 GiB/s beside moderate
victims; all-CXL 43.4–43.9) and the harm they caused are for zero-line writes, not for checkpoint data.**

## Verdict
- **Invariant (added to METHODOLOGY.md):** every write experiment on c28 must write data-carrying lines —
  a pseudo-random or at least per-line non-zero source; never a sparse-touched or zero-filled buffer. Check
  the source pattern before trusting any write number measured beside a co-runner.
- `ckpt_producer.c` now fills its snapshot with xorshift pseudo-random data (8 threads). Phase 2 is being
  re-run with it (`2026-09-22-three-policies-realdata.md`); the zero-line results are kept as raw data and are
  cited only for what they are.
- For the paper: real checkpoint data beside a moderate co-runner streams into DRAM at ~19 GiB/s where zeros
  streamed at 83 — DRAM staging of real data is much slower than the earlier figure suggested, and the CXL
  destination (29 GiB/s under the same co-runner) loses less. To be confirmed by the re-run before it is
  written anywhere.
