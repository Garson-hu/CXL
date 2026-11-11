## Admission analysis of `x08c-conv-p2` (291 requests, 20761 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 9550 | 544 | 4.86 / 28.42 | 0.00 / 2.66 | 0.79 / 1.06 | 0.00 / 3.70 | 0.88 / 0.79 | 0.00 / 0.00 | 0.67 / 0.69 |
| GPU≥50% | 28 | 906 | 16 | 1.47 / 39.76 | 0.00 / 3.14 | 0.58 / 1.52 | 0.17 / 3.02 | – | – | 0.43 / 0.47 |
| 10–50% | 67 | 2103 | 96 | 7.87 / 52.62 | 0.00 / 2.82 | 0.64 / 0.82 | 2.00 / 10.71 | 0.85 / 0.74 | 0.00 / 0.85 | 0.77 / 0.98 |
| miss<10% | 182 | 13883 | 128 | 16.33 / 52.01 | 0.00 / 2.44 | 0.61 / 1.09 | 10.42 / 12.91 | 1.16 / 1.16 | 0.00 / 0.00 | 3.41 / 4.41 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 8.21 | 0.09 [1%] | 0.36 [4%] | 4.67 [57%] | 0.12 [1%] | 0.37 [5%] | 1.23 [15%] | 0.12 [1%] | 0.84 [10%] | 0.40 [5%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 28 | 7.68 | 0.00 [0%] | 0.20 [3%] | 5.85 [76%] | 0.06 [1%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.49 [6%] | 0.00 [0%] | 0.11 [1%] | 0.97 [13%] | 0.00 [0%] |
| 10–50% | 67 | 14.44 | 0.00 [0%] | 0.46 [3%] | 8.52 [59%] | 0.03 [0%] | 0.01 [0%] | 0.30 [2%] | 0.00 [0%] | 0.54 [4%] | 0.00 [0%] | 0.01 [0%] | 4.56 [32%] | 0.01 [0%] |
| miss<10% | 182 | 16.45 | 0.00 [0%] | 0.61 [4%] | 7.68 [47%] | 0.01 [0%] | 0.00 [0%] | 2.29 [14%] | 0.00 [0%] | 0.52 [3%] | 0.03 [0%] | 0.00 [0%] | 5.31 [32%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.00 | 0.20 | 2.34 | 0.12 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.09 | 3.05 | 0.00 | 0.00 | 0.00 |
| 10–50% | 67 | 0.00 | 0.06 | 2.76 | 0.00 | 0.00 | 0.00 |
| miss<10% | 182 | 0.00 | 0.06 | 2.37 | 0.01 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.03 | 0.39 | 0.00 | 0.64 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.06 | 0.90 | 0.06 | 0.49 | 0.00 | 0.00 | 0.00 |
| 10–50% | 67 | 0.02 | 0.28 | 0.00 | 0.52 | 0.00 | 0.00 | 0.00 |
| miss<10% | 182 | 0.04 | 0.54 | 0.00 | 0.51 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.13 | 1.81 | 0.00 | 1.23 | 0.12 | 0.00 | 0.40 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.05 | 1.89 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.11 | 0.97 | 0.00 |
| 10–50% | 67 | 0.37 | 5.48 | 0.03 | 0.25 | 0.00 | 0.00 | 0.00 | 0.01 | 4.56 | 0.01 |
| miss<10% | 182 | 0.51 | 4.77 | 0.00 | 2.29 | 0.00 | 0.00 | 0.03 | 0.00 | 5.31 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 67 | 0.00 | 0.00 | 0.00 | 0.05 | 0.00 |
| miss<10% | 182 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 227 | 223 / 0 / 4 | 1968 | 1977 | 1118 (132–1159) | 0 (1221) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6611 | 6611 / 0 / 0 | 128 | 1059 | 537 (82–1346) | 0 (600) |
| promotion after a load | 44 | 44 / 0 / 0 | 128 | 970 | 530 (517–817) | 0 (0) |

Requests refused at least once: 91 of 291; preemptions: 8; running requests that could not get their next chunk: 16.
Admitted external loads: 19; reservation passed at admission p50 294 / max 1721 blocks; free blocks at admission p50 2326.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.626 |
| time with free blocks < 50% of the pool | 0.685 |
| time with free blocks < 25% of the pool | 0.546 |
| time with free blocks < 10% of the pool | 0.246 |
| time with free blocks < 5% of the pool | 0.135 |
| blocks held by loads in transfer, mean / max | 6 / 2864 |
| in-flight prefill reservation after schedule(), mean / max | 297 / 2255 |
| steps whose running requests used the whole token budget (share of time) | 0.080 |
| steps with a shortened token budget (share of time) | 0.114 |
| running requests, mean / max | 6.2 / 15 |
| waiting + kv-holding requests, mean / max | 3.3 / 16 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.71 | 0.00 | 0.26 / 0.04 | 4.86 [4] | 8.50 [10] | 2.91 [7] | 8.50 [7] |
| GPU≥50% | 28 | 0.64 | 0.00 | 0.49 / 0.07 | 0.23 [10] | 1.58 [18] | 1.23 [17] | 17.03 [11] |
| 10–50% | 67 | 0.57 | 0.00 | 0.29 / 0.06 | 0.79 [29] | 13.52 [38] | 1.50 [36] | 23.75 [31] |
| miss<10% | 182 | 0.63 | 0.00 | 0.41 / 0.05 | 5.77 [68] | 22.48 [114] | 11.24 [104] | 27.47 [78] |
