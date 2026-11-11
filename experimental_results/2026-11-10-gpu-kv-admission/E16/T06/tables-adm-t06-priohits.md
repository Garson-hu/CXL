## Admission analysis of `t06-priohits` (853 requests, 46255 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 6180 | 384 | 3.67 / 16.18 | 0.75 / 1.79 | 1.01 / 1.65 | 0.00 / 0.14 | 0.46 / 0.66 | 0.00 / 0.55 | 0.32 / 0.48 |
| GPU≥50% | 377 | 6198 | 195 | 1.80 / 10.53 | 0.00 / 1.20 | 0.76 / 1.20 | 0.00 / 0.01 | 0.12 / 0.30 | 0.00 / 0.00 | 0.35 / 0.41 |
| 10–50% | 89 | 2103 | 87 | 1.91 / 38.74 | 0.00 / 2.84 | 0.68 / 4.26 | 0.00 / 0.17 | 1.15 / 1.01 | 0.83 / 1.12 | 0.51 / 0.82 |
| miss<10% | 262 | 14041 | 128 | 8.57 / 38.60 | 0.00 / 3.05 | 0.79 / 4.42 | 0.00 / 0.55 | 0.01 / 0.01 | 0.00 / 0.00 | 3.25 / 4.16 |
| mixed | 6 | 6661 | 207 | 7.30 / 9.32 | 1.76 / 1.49 | 1.31 / 1.11 | 0.00 / 0.00 | 1.59 / 1.16 | 1.49 / 1.16 | 0.88 / 0.78 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 4.79 | 3.10 [65%] | 0.12 [2%] | 0.39 [8%] | 0.18 [4%] | 0.14 [3%] | 0.86 [18%] | 0.00 [0%] |
| GPU≥50% | 377 | 2.41 | 1.66 [69%] | 0.08 [3%] | 0.09 [4%] | 0.00 [0%] | 0.01 [0%] | 0.57 [24%] | 0.00 [0%] |
| 10–50% | 89 | 7.39 | 4.66 [63%] | 0.48 [6%] | 1.53 [21%] | 0.01 [0%] | 0.17 [2%] | 0.53 [7%] | 0.01 [0%] |
| miss<10% | 262 | 8.02 | 4.81 [60%] | 0.53 [7%] | 1.60 [20%] | 0.00 [0%] | 0.52 [7%] | 0.56 [7%] | 0.00 [0%] |
| mixed | 6 | 4.93 | 3.35 [68%] | 0.27 [6%] | 0.02 [0%] | 0.11 [2%] | 0.00 [0%] | 1.18 [24%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 119 | 1.78 | 0.00 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 377 | 1.11 | 0.04 | 0.04 | 0.00 | 0.00 |
| 10–50% | 89 | 2.18 | 0.19 | 0.48 | 0.00 | 0.00 |
| miss<10% | 262 | 2.13 | 0.18 | 0.73 | 0.00 | 0.00 |
| mixed | 6 | 1.49 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 0.55 | 0.02 | 0.29 | 0.00 | 0.79 | 0.00 |
| GPU≥50% | 377 | 0.55 | 0.04 | 0.04 | 0.00 | 0.57 | 0.00 |
| 10–50% | 89 | 2.39 | 0.28 | 1.05 | 0.00 | 0.52 | 0.00 |
| miss<10% | 262 | 2.67 | 0.34 | 0.85 | 0.00 | 0.56 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 1.11 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|
| host≥50% | 119 | 0.00 | 0.00 | 0.14 | 0.00 |
| GPU≥50% | 377 | 0.00 | 0.00 | 0.01 | 0.00 |
| 10–50% | 89 | 0.00 | 0.00 | 0.17 | 0.00 |
| miss<10% | 262 | 0.00 | 0.02 | 0.52 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 119 | 0.50 | 0.04 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 377 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 262 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.89 | 0.27 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 851 | 851 / 0 / 0 | 384 | 430 | 240 (109–1238) | 0 (186) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4559 | 4559 / 0 / 0 | 128 | 1700 | 685 (161–1853) | 0 (0) |

Requests refused at least once: 65 of 853; preemptions: 3; running requests that could not get their next chunk: 6.
Admitted external loads: 140; reservation passed at admission p50 0 / max 307 blocks; free blocks at admission p50 3803.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.407 |
| time with free blocks < 50% of the pool | 0.385 |
| time with free blocks < 25% of the pool | 0.221 |
| time with free blocks < 10% of the pool | 0.097 |
| time with free blocks < 5% of the pool | 0.052 |
| blocks held by loads in transfer, mean / max | 21 / 2400 |
| in-flight prefill reservation after schedule(), mean / max | 197 / 1976 |
| steps whose running requests used the whole token budget (share of time) | 0.323 |
| running requests, mean / max | 3.7 / 16 |
| waiting + kv-holding requests, mean / max | 1.7 / 18 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 119 | 0.63 | 0.57 | 0.66 / 0.09 | 1.00 [44] | 7.28 [75] | 4.68 [95] | 1.95 [24] |
| GPU≥50% | 377 | 0.50 | 0.42 | 0.69 / 0.30 | 0.22 [188] | 4.68 [189] | 1.63 [345] | 3.18 [32] |
| 10–50% | 89 | 0.44 | 0.38 | 0.71 / 0.24 | 0.56 [50] | 9.85 [39] | 1.69 [80] | 37.89 [9] |
| miss<10% | 262 | 0.43 | 0.36 | 0.74 / 0.25 | 3.84 [150] | 14.17 [112] | 7.81 [236] | 30.78 [26] |
| mixed | 6 | 0.83 | 0.83 | 0.85 / 0.07 | 2.24 [1] | 7.30 [5] | 7.30 [5] | 1.83 [1] |
