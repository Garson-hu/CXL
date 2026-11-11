## Admission analysis of `x08-p2` (544 requests, 21197 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 6268 | 384 | 16.30 / 39.66 | 2.03 / 5.17 | 0.72 / 1.04 | 0.00 / 8.34 | 0.97 / 0.91 | 0.00 / 0.00 | 0.65 / 0.78 |
| GPU≥50% | 195 | 6180 | 77 | 1.46 / 27.59 | 0.00 / 1.94 | 0.41 / 1.24 | 0.17 / 3.05 | 0.67 / 0.54 | 0.00 / 0.00 | 0.43 / 0.46 |
| 10–50% | 64 | 2103 | 94 | 10.10 / 47.23 | 0.00 / 2.77 | 0.58 / 1.06 | 3.53 / 9.92 | 0.76 / 0.71 | 0.00 / 1.03 | 0.70 / 1.03 |
| miss<10% | 164 | 13883 | 128 | 18.22 / 52.17 | 0.00 / 2.28 | 0.43 / 1.01 | 10.36 / 13.59 | 1.10 / 1.10 | 0.00 / 0.00 | 3.71 / 4.67 |
| mixed | 2 | 7353 | 384 | 32.19 / 32.19 | 1.97 / 1.55 | 0.83 / 0.83 | 27.17 / 27.17 | 1.28 / 1.20 | 0.00 / 0.00 | 1.28 / 1.18 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 15.46 | 0.01 [0%] | 0.23 [2%] | 10.77 [70%] | 0.93 [6%] | 0.31 [2%] | 0.39 [3%] | 0.32 [2%] | 0.82 [5%] | 0.37 [2%] | 0.14 [1%] | 1.16 [7%] | 0.01 [0%] | 0.00 [0%] |
| GPU≥50% | 195 | 6.24 | 0.00 [0%] | 0.18 [3%] | 3.95 [63%] | 0.25 [4%] | 0.01 [0%] | 0.04 [1%] | 0.01 [0%] | 0.42 [7%] | 0.20 [3%] | 0.07 [1%] | 1.10 [18%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 64 | 13.86 | 0.00 [0%] | 0.31 [2%] | 8.01 [58%] | 0.63 [5%] | 0.02 [0%] | 0.19 [1%] | 0.00 [0%] | 0.49 [4%] | 0.02 [0%] | 0.02 [0%] | 4.16 [30%] | 0.01 [0%] | 0.00 [0%] |
| miss<10% | 164 | 16.88 | 0.00 [0%] | 0.56 [3%] | 7.67 [45%] | 0.40 [2%] | 0.00 [0%] | 2.56 [15%] | 0.00 [0%] | 0.45 [3%] | 0.10 [1%] | 0.03 [0%] | 5.10 [30%] | 0.01 [0%] | 0.00 [0%] |
| mixed | 2 | 30.75 | 0.00 [0%] | 0.94 [3%] | 24.20 [79%] | 1.25 [4%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 1.21 [4%] | 3.15 [10%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 0.00 | 0.07 | 4.73 | 0.36 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 195 | 0.00 | 0.04 | 1.78 | 0.11 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.03 | 2.51 | 0.22 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.04 | 2.06 | 0.18 | 0.00 | 0.00 | 0.00 |
| mixed | 2 | 0.00 | 0.02 | 1.53 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 0.03 | 0.41 | 0.02 | 0.58 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 195 | 0.07 | 0.74 | 0.01 | 0.41 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.55 | 0.00 | 0.48 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.03 | 0.50 | 0.03 | 0.45 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 2 | 0.00 | 0.00 | 0.00 | 0.82 | 0.01 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 0.10 | 5.36 | 0.50 | 0.39 | 0.32 | 0.00 | 0.37 | 0.14 | 1.16 | 0.01 | 0.00 |
| GPU≥50% | 195 | 0.07 | 1.43 | 0.12 | 0.04 | 0.01 | 0.00 | 0.20 | 0.07 | 1.10 | 0.00 | 0.01 |
| 10–50% | 64 | 0.24 | 4.95 | 0.39 | 0.13 | 0.00 | 0.00 | 0.02 | 0.02 | 4.16 | 0.01 | 0.00 |
| miss<10% | 164 | 0.49 | 5.11 | 0.19 | 2.56 | 0.00 | 0.00 | 0.10 | 0.03 | 5.10 | 0.00 | 0.00 |
| mixed | 2 | 0.92 | 21.86 | 1.25 | 0.00 | 0.00 | 0.00 | 3.15 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | other | own:full | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 195 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.06 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 938 | 835 / 0 / 103 | 384 | 446 | 229 (139–549) | 0 (1830) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6453 | 6449 / 0 / 4 | 128 | 1085 | 610 (106–1670) | 0 (600) |
| promotion after a load | 31 | 31 / 0 / 0 | 128 | 970 | 676 (212–858) | 0 (0) |

Requests refused at least once: 119 of 544; preemptions: 6; running requests that could not get their next chunk: 12.
Admitted external loads: 134; reservation passed at admission p50 358 / max 1954 blocks; free blocks at admission p50 1658.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.637 |
| time with free blocks < 50% of the pool | 0.687 |
| time with free blocks < 25% of the pool | 0.554 |
| time with free blocks < 10% of the pool | 0.307 |
| time with free blocks < 5% of the pool | 0.158 |
| blocks held by loads in transfer, mean / max | 31 / 2688 |
| in-flight prefill reservation after schedule(), mean / max | 309 / 2615 |
| steps whose running requests used the whole token budget (share of time) | 0.043 |
| steps with a shortened token budget (share of time) | 0.190 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 5.3 / 27 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 0.76 | 0.00 | 0.13 / 0.03 | 9.27 [28] | 19.03 [91] | 2.52 [30] | 18.87 [89] |
| GPU≥50% | 195 | 0.56 | 0.00 | 0.54 / 0.03 | 0.28 [86] | 1.68 [109] | 0.91 [119] | 11.67 [76] |
| 10–50% | 64 | 0.64 | 0.00 | 0.23 / 0.05 | 0.65 [23] | 17.85 [41] | 1.13 [30] | 24.35 [34] |
| miss<10% | 164 | 0.65 | 0.00 | 0.42 / 0.05 | 6.19 [58] | 22.40 [106] | 12.39 [89] | 27.34 [75] |
| mixed | 2 | 0.00 | 0.00 | 0.18 / 0.18 | 32.19 [2] | – | – | 32.19 [2] |
