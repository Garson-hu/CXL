# 2026-10-06 — Gates for the controller and plugin changes of 2026-10-06: measured CXL capacity, the loan-must-pay rule, CPU tensors as objects

**STATUS: CLOSED 2026-10-06.** Raw: `experimental_results/2026-10-06-fullness-v2/` (final runs at top level; the two
earlier attempts under `attempt1-chunk-rate-rule/` and `attempt2-block2s/`; `E2b-gate.txt`). Code: DESIGN §10.11 items
19 and 21. Victims and protocol as in `2026-09-22-three-policies-realdata.md` (llama.cpp on 32 threads; the 8-thread reader).

## Question
After the daemon judges "CXL is full" from the rate measured under the current co-runner (not a constant) and hands the
loan back when it does not pay, does the loan still work beside the reader, and what happens beside llama.cpp-32, where
the old rule never lent and where DRAM chunks are slower than CXL chunks?

## What the first two attempts taught
1. **Per-chunk rates cannot judge the loan.** Attempt 1 compared each device's bytes/time per chunk from the ledger:
   beside the reader DRAM chunks measured 2.3 GiB/s per thread against 5.5–7.4 for CXL chunks (the CXL figure rises
   while neighbouring threads are busy with DRAM chunks), so the rule withdrew a loan that was paying: reader 1.36–1.39 s
   at 3% with a 5–7% share, against 1.07 s at 6.2% with 27% before. The judgement has to be aggregate: while DRAM is lent,
   the stream's total rate (CXL + DRAM) must exceed what CXL alone achieved.
2. **A failed trial must be remembered.** With a 2 s block after a failed trial (attempt 2) the loan was re-tried in every
   burst beside llama.cpp-32 and each trial cost time (2.32–2.71 s against 2.16 s all-CXL), because the first DRAM chunks
   slow the whole thread pool before the two-epoch test fires. The block is now 60 s (`--loan-block-s`).

## Results (final rules; medians over the last 3 of 6 windows per run)
| victim | run | completion s | slowdown | DRAM share | before (constant capacity, `three-policies-realdata`) |
|---|---|---|---|---|---|
| reader, 8 threads | cxlpath bound 1.09, rep 1 | 1.06 | 6.4% | 0.30 | 1.07 s, 6.2%, 0.27 |
| llama.cpp-32 | cxlpath bound 1.09, reps 1–3 | 2.23 / 2.27 / 2.26 | 0.5 / 0.0 / 0.4% | 0.00 | 2.18 s, −0.8%, 0.00 (never "full"); all-CXL 2.16 s |

Beside llama.cpp-32 the measured capacity (≈ 30–32 GiB/s) now says "full", the loan is tried once, the total rate
drops (DRAM chunks at ~1.7 GiB/s per thread against 3.9 for CXL), two epochs later the loan is handed back and blocked
for a minute: the cost of the trial is 0.1 s per minute of bursts. Beside the reader nothing changed.

## Plugin gate E2b (CPU tensors as objects)
`clients/pytorch/test_dcp_cpu_objects.py`: a 1.5 GiB CPU state dict through `dcp.async_save` three times with the
tensors mutated after each save: staged in 0.07 s (21.8 GiB/s with 8 pinned copy threads; 7 objects), v1 reloaded from
CXL byte-exact, v3 durable after 4 s, v1 reclaimed and reloaded from the object file, v3 reloaded from the file after the
store was destroyed. One bug found and fixed: a CPU-only state dict never committed its (empty) buffer set, so the third
version waited forever for a set to overwrite; the empty set is now committed as already durable.

## Verdict
The controller's capacity is measured and the loan is withdrawn where it does not pay, without regression beside the
reader; the real PyTorch producer's CPU tensors now take the per-chunk placement path. Both changes are in.
