## Admission analysis of `x08c-conv-skip30` (291 requests, 21064 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 9550 | 544 | 12.69 / 23.49 | 2.50 / 5.51 | 1.08 / 3.02 | 1.88 / 2.02 | 0.83 / 0.65 | 0.00 / 0.02 | 0.30 / 0.38 |
| GPU≥50% | 28 | 906 | 26 | 5.88 / 19.01 | 1.96 / 3.35 | 0.84 / 2.48 | 0.00 / 0.01 | – | – | 0.34 / 0.45 |
| 10–50% | 67 | 2103 | 89 | 3.55 / 23.15 | 0.41 / 3.03 | 0.86 / 2.17 | 0.00 / 0.96 | 1.21 / 0.80 | 0.00 / 0.00 | 0.73 / 0.89 |
| miss<10% | 182 | 13883 | 128 | 12.51 / 46.40 | 1.14 / 3.03 | 0.95 / 2.43 | 0.00 / 6.78 | 1.32 / 1.32 | 0.00 / 0.00 | 3.32 / 4.17 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | preempt |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 11.21 | 6.54 [58%] | 0.40 [4%] | 1.18 [11%] | 0.41 [4%] | 0.02 [0%] | 1.06 [9%] | 1.61 [14%] | 0.00 [0%] |
| GPU≥50% | 28 | 5.84 | 4.49 [77%] | 0.36 [6%] | 0.27 [5%] | 0.00 [0%] | 0.00 [0%] | 0.71 [12%] | 0.01 [0%] | 0.00 [0%] |
| 10–50% | 67 | 6.21 | 4.25 [68%] | 0.25 [4%] | 0.50 [8%] | 0.02 [0%] | 0.00 [0%] | 0.71 [11%] | 0.48 [8%] | 0.00 [0%] |
| miss<10% | 182 | 12.24 | 7.15 [58%] | 0.45 [4%] | 0.74 [6%] | 0.00 [0%] | 0.22 [2%] | 0.74 [6%] | 2.95 [24%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 14 | 4.20 | 0.18 | 1.12 | 0.00 | 0.00 |
| GPU≥50% | 28 | 2.93 | 0.15 | 0.27 | 0.00 | 0.00 |
| 10–50% | 67 | 2.58 | 0.10 | 0.35 | 0.00 | 0.00 |
| miss<10% | 182 | 2.58 | 0.11 | 0.33 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks |
|---|---|---|---|---|---|---|
| host≥50% | 14 | 1.90 | 0.18 | 0.00 | 0.94 | 0.00 |
| GPU≥50% | 28 | 1.56 | 0.20 | 0.00 | 0.71 | 0.00 |
| 10–50% | 67 | 1.26 | 0.09 | 0.10 | 0.71 | 0.00 |
| miss<10% | 182 | 1.47 | 0.22 | 0.00 | 0.74 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | pol:blocks | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.31 | 0.04 | 0.06 | 0.00 | 0.00 | 1.61 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |
| 10–50% | 67 | 0.38 | 0.05 | 0.05 | 0.00 | 0.00 | 0.48 | 0.00 |
| miss<10% | 182 | 3.10 | 0.12 | 0.41 | 0.22 | 0.00 | 2.94 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | own:full | pending |
|---|---|---|---|---|---|
| host≥50% | 14 | 0.00 | 0.00 | 0.02 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 67 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 182 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 1574 | 1574 / 0 / 0 | 128 | 1980 | 604 (111–1147) | 0 (384) |
| promotion after a load | 7 | 7 / 0 / 0 | 128 | 134 | 49 (48–52) | 0 (0) |

Requests refused at least once: 20 of 291; preemptions: 6; running requests that could not get their next chunk: 12.
Admitted external loads: 19; reservation passed at admission p50 0 / max 88 blocks; free blocks at admission p50 1243.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.608 |
| time with free blocks < 50% of the pool | 0.656 |
| time with free blocks < 25% of the pool | 0.508 |
| time with free blocks < 10% of the pool | 0.276 |
| time with free blocks < 5% of the pool | 0.128 |
| blocks held by loads in transfer, mean / max | 5 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 264 / 1904 |
| steps whose running requests used the whole token budget (share of time) | 0.452 |
| running requests, mean / max | 5.9 / 14 |
| waiting + kv-holding requests, mean / max | 2.3 / 13 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.64 | 0.64 | 0.43 / 0.06 | 4.28 [5] | 12.69 [9] | 9.46 [8] | 12.71 [6] |
| GPU≥50% | 28 | 0.61 | 0.57 | 0.57 / 0.09 | 0.22 [11] | 6.95 [17] | 2.17 [17] | 6.56 [11] |
| 10–50% | 67 | 0.45 | 0.40 | 0.35 / 0.06 | 0.79 [37] | 9.96 [30] | 2.62 [38] | 4.82 [29] |
| miss<10% | 182 | 0.57 | 0.54 | 0.47 / 0.06 | 4.40 [79] | 17.58 [103] | 10.43 [114] | 21.64 [68] |
