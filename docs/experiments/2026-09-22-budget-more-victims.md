# 2026-09-22 — Phase 1 extended: two more real victims (GAPBS PageRank, llama.cpp CPU decoding)

**STATUS: CLOSED 2026-09-22.** Extends `2026-09-21-dram-write-budget.md` (frozen) with the two victims the
benchmark survey recommended; same protocol, same driver (`benchmarks/budget/run_budget.py pr|llama`).
Raw data sits beside the first sweep: `experimental_results/2026-09-21-dram-write-budget/{pr,llama}.csv`,
`raw-{pr,llama}.log`.

## Victims
- **GAPBS PageRank** (`~/apps/gapbs/pr`, wrapper `benchmarks/policy/gapbs_victim.py`): Kronecker graph
  `-g 26` (67 M vertices, 1.05 G undirected edges, ~9 GB CSR), 80 OpenMP threads on cpus 0–79; metric =
  median trial time of trials 4–30 (1.079 s alone; the six zero-level runs spread 1.6%).
- **llama.cpp CPU decoding** (`~/apps/llama.cpp`, built without AVX512-BF16/VNNI because the machine's
  binutils 2.30 rejects them; wrapper `benchmarks/policy/llama_victim.py` over a copy of `llama-simple`
  with a `-t` option, which flushes every token): Qwen2.5-7B-Instruct Q8_0 (8.1 GB GGUF on the local NVMe),
  greedy decoding, 80 threads on cpus 0–79; metric = tokens/s over 500 ms windows (35.6 tok/s alone, i.e.
  ~290 GB/s of weight reads; six zero-level runs spread 0.6%; llama-bench gives 37.3 for the same setting).

## Results (medians of 3; writers on cpus 96+, probe cpu 80)
| write stream (achieved) | PageRank slowdown | llama.cpp slowdown |
|---|---|---|
| pure → DRAM 10 / 20 / 30 / 40 / 60 GiB/s | 3.2 / 8.2 / 11.8 / 17.9 / 27.7% | 3.0 / 6.4 / 11.1 / 15.5 / 17.7% (60 asked, 45.7 achieved) |
| copy → DRAM 10 / 20 / 30 / 40 GiB/s | 6.5 / 14.8 / 23.9 / 32.6% (40 asked, 38.9) | 5.7 / 13.5 / 19.9 / 24.8% |
| copy → CXL 20 / 40 GiB/s | 4.9 / 12.6% | 4.6 / 11.0% (39.2) |

**DRAM write budget under the bound (GiB/s; CXL pair capacity 43.9):**
| victim | stream | 5% | 7% | 10% |
|---|---|---|---|---|
| PageRank | pure → DRAM | 13.7 | 17.6 | 25.0 |
| PageRank | copies → DRAM | 7.7 | 10.6 | 14.2 |
| PageRank | copies → CXL | 20.2 | 25.4 | 33.2 |
| llama.cpp | pure → DRAM | 15.9 | 21.2 | 27.7 |
| llama.cpp | copies → DRAM | 8.8 | 11.7 | 15.6 |
| llama.cpp | copies → CXL | 21.1 | 27.2 | 36.3 |

## What this adds
- Both real applications behave like the CPU Adam step (saturated regime), not like the synthetic reader:
  under a 7% bound DRAM takes only 18–21 GiB/s of pure writes and 11–12 GiB/s of copies, well below the
  CXL pair's capacity. Their curves are monotonic and repeatable (no anomaly like the Adam copy at 10 GiB/s).
- **Copies to CXL are not free beside a read-saturated victim either:** 20 GiB/s of copies into CXL cost
  PageRank 4.9% and llama.cpp 4.6%, 40 GiB/s cost 11–13% — the source read. Under a 7% bound the copy rate
  into CXL that these victims tolerate is 25–27 GiB/s, i.e. the bound binds on the source side before the
  CXL capacity does. Consequence for the design (see the phase-2 file): lending DRAM cannot help such a
  producer, and holding the bound would require pacing the producer itself, which the controller does not do.
- Beside both victims copy writers saturate at ~42 GiB/s from a DRAM source (source-bound); pure writers
  beside llama.cpp at ~45–51 (its weight reads leave little DRAM bandwidth), beside PageRank at ~68.
