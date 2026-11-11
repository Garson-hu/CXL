## Admission analysis of `x08-skip30-nores` (544 requests, 21619 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 6177 | 384 | 7.53 / 32.72 | 1.00 / 3.19 | 0.84 / 1.95 | 0.00 / 3.67 | 0.45 / 0.72 | 0.00 / 0.24 | 0.35 / 0.44 |
| GPU≥50% | 219 | 6221 | 50 | 3.53 / 21.00 | 0.55 / 2.85 | 0.75 / 1.47 | 0.00 / 1.27 | 0.14 / 0.13 | 0.00 / 0.00 | 0.36 / 0.42 |
| 10–50% | 64 | 2103 | 89 | 3.27 / 20.18 | 0.00 / 3.01 | 0.70 / 1.38 | 0.00 / 1.03 | 1.30 / 1.01 | 1.26 / 1.00 | 0.58 / 0.82 |
| miss<10% | 164 | 13883 | 128 | 12.14 / 45.42 | 0.08 / 2.39 | 0.77 / 2.18 | 0.00 / 6.74 | 2.30 / 2.30 | 1.09 / 1.09 | 3.29 / 4.20 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 9.77 | 5.42 [55%] | 0.37 [4%] | 1.33 [14%] | 0.33 [3%] | 0.05 [1%] | 0.78 [8%] | 1.48 [15%] | 0.01 [0%] | 0.01 [0%] |
| GPU≥50% | 219 | 5.60 | 3.49 [62%] | 0.33 [6%] | 0.48 [9%] | 0.00 [0%] | 0.00 [0%] | 0.58 [10%] | 0.68 [12%] | 0.00 [0%] | 0.03 [1%] |
| 10–50% | 64 | 5.55 | 3.49 [63%] | 0.26 [5%] | 0.61 [11%] | 0.00 [0%] | 0.03 [1%] | 0.53 [10%] | 0.60 [11%] | 0.00 [0%] | 0.01 [0%] |
| miss<10% | 164 | 11.33 | 6.12 [54%] | 0.46 [4%] | 0.86 [8%] | 0.00 [0%] | 0.20 [2%] | 0.59 [5%] | 2.94 [26%] | 0.00 [0%] | 0.15 [1%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 2.57 | 0.16 | 0.46 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 219 | 2.44 | 0.15 | 0.26 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 2.44 | 0.17 | 0.40 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 2.05 | 0.17 | 0.16 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 1.10 | 0.10 | 0.10 | 0.64 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 219 | 0.70 | 0.12 | 0.07 | 0.57 | 0.00 | 0.00 | 0.01 |
| 10–50% | 64 | 0.73 | 0.09 | 0.04 | 0.52 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 1.32 | 0.20 | 0.03 | 0.59 | 0.00 | 0.00 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 1.38 | 0.06 | 0.74 | 0.00 | 0.00 | 1.48 | 0.00 | 0.00 |
| GPU≥50% | 219 | 0.35 | 0.07 | 0.15 | 0.00 | 0.00 | 0.68 | 0.00 | 0.02 |
| 10–50% | 64 | 0.24 | 0.01 | 0.17 | 0.00 | 0.00 | 0.60 | 0.00 | 0.01 |
| miss<10% | 164 | 2.74 | 0.09 | 0.67 | 0.20 | 0.00 | 2.93 | 0.00 | 0.11 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.16 | 0.00 | 0.03 | 0.00 | 0.05 | 0.00 | 0.01 |
| GPU≥50% | 219 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 7 | 7 / 0 / 0 | 384 | 445 | 165 (163–168) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 1739 | 1739 / 0 / 0 | 128 | 1542 | 587 (82–978) | 0 (0) |
| promotion after a load | 181 | 181 / 0 / 0 | 57 | 57 | 33 (14–451) | 0 (0) |

Requests refused at least once: 32 of 544; preemptions: 12; running requests that could not get their next chunk: 25.
Admitted external loads: 106; reservation passed at admission p50 0 / max 218 blocks; free blocks at admission p50 897.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.611 |
| time with free blocks < 50% of the pool | 0.660 |
| time with free blocks < 25% of the pool | 0.512 |
| time with free blocks < 10% of the pool | 0.302 |
| time with free blocks < 5% of the pool | 0.171 |
| blocks held by loads in transfer, mean / max | 24 / 2160 |
| in-flight prefill reservation after schedule(), mean / max | 249 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.414 |
| running requests, mean / max | 6.2 / 16 |
| waiting + kv-holding requests, mean / max | 3.5 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.48 | 0.39 | 0.14 / 0.02 | 4.70 [50] | 10.66 [47] | 8.50 [36] | 7.53 [61] |
| GPU≥50% | 219 | 0.51 | 0.44 | 0.47 / 0.02 | 0.33 [107] | 7.30 [112] | 1.94 [129] | 5.67 [90] |
| 10–50% | 64 | 0.45 | 0.38 | 0.38 / 0.01 | 0.99 [35] | 6.11 [29] | 1.48 [35] | 5.56 [29] |
| miss<10% | 164 | 0.50 | 0.42 | 0.47 / 0.02 | 4.94 [82] | 16.09 [82] | 9.77 [104] | 15.23 [60] |
