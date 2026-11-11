## Admission analysis of `conv08-320-p2` (291 requests, 20792 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 9550 | 544 | 4.78 / 28.36 | 0.00 / 1.31 | 0.80 / 1.81 | 0.00 / 5.13 | 0.87 / 0.83 | 0.00 / 0.00 | 0.70 / 0.72 |
| GPU≥50% | 28 | 906 | 16 | 1.42 / 39.32 | 0.00 / 3.26 | 0.61 / 0.69 | 0.17 / 3.03 | – | – | 0.47 / 0.47 |
| 10–50% | 67 | 2103 | 96 | 7.84 / 53.61 | 0.00 / 2.94 | 0.64 / 0.85 | 1.99 / 10.48 | 0.85 / 0.69 | 0.00 / 0.00 | 0.77 / 1.03 |
| miss<10% | 182 | 13883 | 128 | 16.29 / 51.82 | 0.00 / 2.59 | 0.61 / 0.84 | 10.50 / 12.95 | 1.16 / 1.16 | 0.00 / 0.00 | 3.40 / 4.43 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 9.08 | 0.10 [1%] | 0.38 [4%] | 5.54 [61%] | 0.38 [4%] | 0.89 [10%] | 0.85 [9%] | 0.94 [10%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 28 | 6.98 | 0.00 [0%] | 0.14 [2%] | 5.29 [76%] | 0.00 [0%] | 0.00 [0%] | 0.49 [7%] | 0.00 [0%] | 0.11 [2%] | 0.95 [14%] | 0.00 [0%] |
| 10–50% | 67 | 14.31 | 0.00 [0%] | 0.43 [3%] | 8.51 [59%] | 0.01 [0%] | 0.22 [2%] | 0.54 [4%] | 0.00 [0%] | 0.02 [0%] | 4.57 [32%] | 0.01 [0%] |
| miss<10% | 182 | 16.38 | 0.00 [0%] | 0.60 [4%] | 7.59 [46%] | 0.00 [0%] | 2.35 [14%] | 0.51 [3%] | 0.01 [0%] | 0.00 [0%] | 5.31 [32%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.00 | 0.08 | 1.23 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.10 | 3.17 | 0.00 | 0.00 | 0.00 |
| 10–50% | 67 | 0.00 | 0.07 | 2.87 | 0.00 | 0.00 | 0.00 |
| miss<10% | 182 | 0.00 | 0.06 | 2.53 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.09 | 1.05 | 0.66 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.20 | 0.49 | 0.00 | 0.00 |
| 10–50% | 67 | 0.02 | 0.30 | 0.52 | 0.00 | 0.00 |
| miss<10% | 182 | 0.04 | 0.29 | 0.51 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.20 | 3.09 | 0.89 | 0.00 | 0.94 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.04 | 1.92 | 0.00 | 0.00 | 0.00 | 0.11 | 0.95 | 0.00 |
| 10–50% | 67 | 0.34 | 5.32 | 0.22 | 0.00 | 0.00 | 0.02 | 4.57 | 0.01 |
| miss<10% | 182 | 0.50 | 4.77 | 2.35 | 0.00 | 0.01 | 0.00 | 5.31 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | hol:full | other | pending |
|---|---|---|---|---|---|
| host≥50% | 14 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 67 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 182 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 206 | 206 / 0 / 0 | 1968 | 1977 | 584 (134–1097) | 0 (906) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6716 | 6716 / 0 / 0 | 128 | 1059 | 526 (81–1323) | 0 (600) |

Requests refused at least once: 90 of 291; preemptions: 9; running requests that could not get their next chunk: 18.
Admitted external loads: 19; reservation passed at admission p50 462 / max 1726 blocks; free blocks at admission p50 2640.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.627 |
| time with free blocks < 50% of the pool | 0.683 |
| time with free blocks < 25% of the pool | 0.548 |
| time with free blocks < 10% of the pool | 0.260 |
| time with free blocks < 5% of the pool | 0.141 |
| blocks held by loads in transfer, mean / max | 6 / 2864 |
| in-flight prefill reservation after schedule(), mean / max | 298 / 2255 |
| steps whose running requests used the whole token budget (share of time) | 0.080 |
| steps with a shortened token budget (share of time) | 0.118 |
| running requests, mean / max | 6.2 / 15 |
| waiting + kv-holding requests, mean / max | 3.3 / 16 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.79 | 0.00 | 0.24 / 0.09 | 1.41 [3] | 7.13 [11] | 2.91 [6] | 21.83 [8] |
| GPU≥50% | 28 | 0.68 | 0.00 | 0.49 / 0.07 | 0.22 [9] | 1.47 [19] | 1.14 [17] | 8.72 [11] |
| 10–50% | 67 | 0.60 | 0.00 | 0.29 / 0.06 | 0.53 [27] | 13.66 [40] | 1.48 [37] | 23.56 [30] |
| miss<10% | 182 | 0.63 | 0.00 | 0.41 / 0.04 | 5.74 [68] | 22.12 [114] | 11.22 [104] | 27.45 [78] |
