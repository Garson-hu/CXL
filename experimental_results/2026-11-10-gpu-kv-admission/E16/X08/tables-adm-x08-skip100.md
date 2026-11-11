## Admission analysis of `x08-skip100` (544 requests, 21629 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 6178 | 384 | 6.48 / 22.38 | 0.69 / 2.09 | 0.73 / 2.01 | 0.00 / 2.03 | 0.35 / 0.59 | 0.00 / 0.20 | 0.27 / 0.40 |
| GPU≥50% | 202 | 6237 | 65 | 3.10 / 19.43 | 0.00 / 1.62 | 0.59 / 1.34 | 0.00 / 1.80 | 0.15 / 0.46 | 0.00 / 0.33 | 0.32 / 0.41 |
| 10–50% | 64 | 2103 | 89 | 3.45 / 14.58 | 0.00 / 1.40 | 0.43 / 1.02 | 0.00 / 1.56 | 1.30 / 0.85 | 2.06 / 1.13 | 0.58 / 0.80 |
| miss<10% | 164 | 13883 | 128 | 12.74 / 48.56 | 0.51 / 2.18 | 0.77 / 2.18 | 0.00 / 7.37 | 0.86 / 0.86 | 0.30 / 0.30 | 3.29 / 4.16 |
| mixed | 3 | 6580 | 183 | 7.26 / 10.40 | 3.57 / 3.80 | 1.31 / 1.17 | 1.33 / 1.42 | 0.30 / 0.25 | 0.00 / 0.00 | 0.37 / 0.34 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 6.91 | 4.01 [58%] | 0.34 [5%] | 0.22 [3%] | 0.04 [1%] | 0.27 [4%] | 0.00 [0%] | 0.78 [11%] | 1.24 [18%] | 0.00 [0%] | 0.01 [0%] |
| GPU≥50% | 202 | 4.82 | 2.68 [56%] | 0.28 [6%] | 0.06 [1%] | 0.02 [1%] | 0.02 [0%] | 0.00 [0%] | 0.51 [11%] | 1.25 [26%] | 0.00 [0%] | 0.00 [0%] |
| 10–50% | 64 | 4.10 | 2.07 [50%] | 0.19 [5%] | 0.22 [5%] | 0.10 [2%] | 0.00 [0%] | 0.04 [1%] | 0.47 [11%] | 1.01 [25%] | 0.00 [0%] | 0.01 [0%] |
| miss<10% | 164 | 11.74 | 6.15 [52%] | 0.46 [4%] | 0.24 [2%] | 0.05 [0%] | 0.00 [0%] | 0.00 [0%] | 0.58 [5%] | 4.13 [35%] | 0.00 [0%] | 0.11 [1%] |
| mixed | 3 | 6.65 | 3.80 [57%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.23 [3%] | 0.00 [0%] | 1.20 [18%] | 1.42 [21%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 1.84 | 0.14 | 0.09 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 202 | 1.47 | 0.13 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 1.20 | 0.10 | 0.06 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 1.96 | 0.16 | 0.05 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 3.80 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 1.26 | 0.11 | 0.03 | 0.61 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 202 | 0.73 | 0.11 | 0.01 | 0.49 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.50 | 0.06 | 0.00 | 0.46 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 1.36 | 0.22 | 0.00 | 0.58 | 0.00 | 0.00 | 0.03 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 1.17 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.60 | 0.07 | 0.09 | 0.03 | 0.00 | 1.24 | 0.00 | 0.00 |
| GPU≥50% | 202 | 0.46 | 0.04 | 0.05 | 0.01 | 0.00 | 1.24 | 0.00 | 0.00 |
| 10–50% | 64 | 0.29 | 0.03 | 0.16 | 0.06 | 0.00 | 1.01 | 0.00 | 0.01 |
| miss<10% | 164 | 2.84 | 0.09 | 0.19 | 0.04 | 0.00 | 4.13 | 0.00 | 0.08 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.42 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.19 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 202 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.00 | 0.00 | 0.04 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 481 | 428 / 0 / 53 | 641 | 641 | 584 (373–1231) | 0 (600) |
| promotion after a load | 68 | 68 / 0 / 0 | 128 | 970 | 846 (834–856) | 0 (0) |

Requests refused at least once: 7 of 544; preemptions: 5; running requests that could not get their next chunk: 10.
Admitted external loads: 134; reservation passed at admission p50 0 / max 264 blocks; free blocks at admission p50 745.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.612 |
| time with free blocks < 50% of the pool | 0.663 |
| time with free blocks < 25% of the pool | 0.525 |
| time with free blocks < 10% of the pool | 0.281 |
| time with free blocks < 5% of the pool | 0.137 |
| blocks held by loads in transfer, mean / max | 29 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 246 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.411 |
| running requests, mean / max | 6.3 / 16 |
| waiting + kv-holding requests, mean / max | 3.1 / 21 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.52 | 0.45 | 0.16 / 0.03 | 2.22 [53] | 9.66 [58] | 9.90 [42] | 4.38 [69] |
| GPU≥50% | 202 | 0.45 | 0.40 | 0.52 / 0.04 | 0.39 [112] | 7.30 [90] | 1.58 [117] | 4.97 [85] |
| 10–50% | 64 | 0.42 | 0.36 | 0.24 / 0.01 | 1.45 [37] | 5.49 [27] | 1.42 [31] | 4.59 [33] |
| miss<10% | 164 | 0.51 | 0.45 | 0.47 / 0.04 | 5.64 [80] | 14.74 [84] | 11.30 [105] | 14.47 [59] |
| mixed | 3 | 1.00 | 1.00 | 0.15 / 0.06 | – | 7.26 [3] | – | 7.26 [3] |
