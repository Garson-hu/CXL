## Admission analysis of `t06-p2` (853 requests, 45918 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 6177 | 384 | 2.62 / 37.77 | 0.00 / 3.71 | 0.53 / 1.81 | 0.00 / 5.56 | 0.70 / 0.66 | 0.00 / 0.01 | 0.58 / 0.66 |
| GPU≥50% | 411 | 6221 | 176 | 1.15 / 15.18 | 0.00 / 0.34 | 0.33 / 0.44 | 0.13 / 1.54 | 1.55 / 1.30 | 0.00 / 0.00 | 0.39 / 0.43 |
| 10–50% | 89 | 2103 | 93 | 1.90 / 40.27 | 0.00 / 0.73 | 0.30 / 0.71 | 0.15 / 5.28 | 0.64 / 0.59 | 0.00 / 0.00 | 0.68 / 0.94 |
| miss<10% | 264 | 14041 | 128 | 9.54 / 43.39 | 0.00 / 0.85 | 0.33 / 0.37 | 2.18 / 7.60 | 0.05 / 0.05 | 0.00 / 0.00 | 3.52 / 4.52 |
| mixed | 6 | 3156 | 160 | 4.98 / 23.87 | 0.00 / 3.18 | 0.66 / 1.00 | 0.00 / 2.58 | 1.05 / 0.98 | 0.00 / 0.00 | 0.80 / 0.76 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 11.75 | 0.04 [0%] | 0.39 [3%] | 6.63 [56%] | 1.39 [12%] | 0.36 [3%] | 0.39 [3%] | 0.41 [3%] | 0.65 [6%] | 0.36 [3%] | 0.02 [0%] | 1.08 [9%] | 0.01 [0%] | 0.03 [0%] |
| GPU≥50% | 411 | 2.34 | 0.00 [0%] | 0.13 [5%] | 0.61 [26%] | 0.17 [7%] | 0.01 [0%] | 0.01 [0%] | 0.00 [0%] | 0.35 [15%] | 0.07 [3%] | 0.00 [0%] | 0.99 [42%] | 0.00 [0%] | 0.00 [0%] |
| 10–50% | 89 | 6.75 | 0.00 [0%] | 0.28 [4%] | 2.18 [32%] | 0.32 [5%] | 0.02 [0%] | 0.19 [3%] | 0.00 [0%] | 0.32 [5%] | 0.03 [1%] | 0.01 [0%] | 3.40 [50%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 264 | 8.82 | 0.00 [0%] | 0.42 [5%] | 2.40 [27%] | 0.51 [6%] | 0.00 [0%] | 0.95 [11%] | 0.00 [0%] | 0.33 [4%] | 0.01 [0%] | 0.01 [0%] | 4.18 [47%] | 0.00 [0%] | 0.01 [0%] |
| mixed | 6 | 7.74 | 0.00 [0%] | 0.56 [7%] | 3.78 [49%] | 0.14 [2%] | 0.72 [9%] | 0.00 [0%] | 0.00 [0%] | 0.96 [12%] | 0.00 [0%] | 0.00 [0%] | 1.59 [20%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.00 | 0.16 | 2.83 | 0.71 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 411 | 0.00 | 0.02 | 0.25 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.00 | 0.04 | 0.57 | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 264 | 0.00 | 0.04 | 0.59 | 0.22 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.30 | 2.73 | 0.14 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.03 | 1.08 | 0.20 | 0.50 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 411 | 0.01 | 0.07 | 0.02 | 0.34 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.01 | 0.31 | 0.07 | 0.32 | 0.00 | 0.00 | 0.00 |
| miss<10% | 264 | 0.02 | 0.02 | 0.00 | 0.33 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.30 | 0.00 | 0.70 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.18 | 2.65 | 0.44 | 0.39 | 0.41 | 0.00 | 0.36 | 0.02 | 1.08 | 0.01 | 0.02 |
| GPU≥50% | 411 | 0.09 | 0.29 | 0.08 | 0.01 | 0.00 | 0.00 | 0.07 | 0.00 | 0.99 | 0.00 | 0.00 |
| 10–50% | 89 | 0.22 | 1.30 | 0.13 | 0.19 | 0.00 | 0.00 | 0.03 | 0.01 | 3.40 | 0.00 | 0.00 |
| miss<10% | 264 | 0.36 | 1.80 | 0.29 | 0.95 | 0.00 | 0.00 | 0.01 | 0.01 | 4.18 | 0.00 | 0.01 |
| mixed | 6 | 0.25 | 0.75 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.58 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 411 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 264 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 775 | 680 / 0 / 95 | 384 | 464 | 530 (35–1130) | 0 (1753) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5049 | 4900 / 0 / 149 | 128 | 1700 | 700 (158–1815) | 0 (600) |

Requests refused at least once: 74 of 853; preemptions: 7; running requests that could not get their next chunk: 14.
Admitted external loads: 103; reservation passed at admission p50 467 / max 1825 blocks; free blocks at admission p50 3378.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.417 |
| time with free blocks < 50% of the pool | 0.398 |
| time with free blocks < 25% of the pool | 0.224 |
| time with free blocks < 10% of the pool | 0.093 |
| time with free blocks < 5% of the pool | 0.048 |
| blocks held by loads in transfer, mean / max | 10 / 1920 |
| in-flight prefill reservation after schedule(), mean / max | 233 / 1934 |
| steps whose running requests used the whole token budget (share of time) | 0.074 |
| steps with a shortened token budget (share of time) | 0.146 |
| running requests, mean / max | 4.0 / 16 |
| waiting + kv-holding requests, mean / max | 1.9 / 28 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.72 | 0.00 | 0.50 / 0.05 | 1.20 [23] | 3.96 [60] | 1.99 [54] | 26.49 [29] |
| GPU≥50% | 411 | 0.63 | 0.00 | 0.69 / 0.32 | 0.18 [154] | 1.49 [257] | 1.09 [376] | 6.47 [35] |
| 10–50% | 89 | 0.56 | 0.00 | 0.68 / 0.23 | 0.37 [39] | 6.43 [50] | 1.78 [79] | 7.96 [10] |
| miss<10% | 264 | 0.56 | 0.00 | 0.74 / 0.35 | 3.01 [117] | 14.96 [147] | 9.15 [242] | 33.57 [22] |
| mixed | 6 | 1.00 | 0.00 | 0.82 / 0.16 | – | 4.98 [6] | 2.45 [5] | 23.87 [1] |
