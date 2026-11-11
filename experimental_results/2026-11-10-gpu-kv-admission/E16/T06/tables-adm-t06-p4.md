## Admission analysis of `t06-p4` (853 requests, 46345 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 70 | 6178 | 384 | 1.93 / 18.84 | 0.00 / 1.07 | 0.52 / 0.45 | 0.00 / 1.91 | 0.64 / 0.60 | 0.00 / 0.00 | 0.45 / 0.54 |
| GPU≥50% | 424 | 6203 | 176 | 1.22 / 14.96 | 0.00 / 0.54 | 0.34 / 0.35 | 0.14 / 1.70 | 1.03 / 0.74 | 0.00 / 0.06 | 0.41 / 0.47 |
| 10–50% | 89 | 2103 | 93 | 1.91 / 18.66 | 0.00 / 0.53 | 0.30 / 0.32 | 0.15 / 3.70 | 0.63 / 0.66 | 0.00 / 0.00 | 0.71 / 1.01 |
| miss<10% | 264 | 14041 | 128 | 9.47 / 42.15 | 0.00 / 0.61 | 0.33 / 0.35 | 2.18 / 7.63 | 0.04 / 0.04 | 0.00 / 0.00 | 3.67 / 4.51 |
| mixed | 6 | 3156 | 107 | 3.94 / 35.75 | 0.00 / 4.13 | 0.66 / 0.68 | 0.00 / 1.58 | 1.04 / 0.89 | 0.00 / 0.00 | 0.62 / 1.00 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 70 | 4.03 | 0.04 [1%] | 0.06 [2%] | 1.27 [32%] | 0.26 [6%] | 0.42 [10%] | 0.12 [3%] | 0.16 [4%] | 0.58 [14%] | 0.89 [22%] | 0.01 [0%] | 0.21 [5%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 424 | 2.62 | 0.00 [0%] | 0.14 [5%] | 0.43 [16%] | 0.25 [9%] | 0.02 [1%] | 0.00 [0%] | 0.00 [0%] | 0.34 [13%] | 0.21 [8%] | 0.04 [2%] | 1.19 [45%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 89 | 4.60 | 0.00 [0%] | 0.27 [6%] | 0.42 [9%] | 0.25 [5%] | 0.03 [1%] | 0.00 [0%] | 0.00 [0%] | 0.32 [7%] | 0.15 [3%] | 0.04 [1%] | 3.13 [68%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 264 | 8.59 | 0.00 [0%] | 0.40 [5%] | 1.04 [12%] | 0.33 [4%] | 0.00 [0%] | 0.24 [3%] | 0.00 [0%] | 0.33 [4%] | 1.02 [12%] | 0.06 [1%] | 5.16 [60%] | 0.00 [0%] | 0.00 [0%] |
| mixed | 6 | 7.28 | 0.00 [0%] | 0.07 [1%] | 2.59 [36%] | 2.21 [30%] | 0.65 [9%] | 0.00 [0%] | 0.00 [0%] | 0.87 [12%] | 0.11 [2%] | 0.12 [2%] | 0.66 [9%] | 0.01 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 70 | 0.00 | 0.03 | 0.78 | 0.26 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 424 | 0.00 | 0.02 | 0.35 | 0.17 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.00 | 0.01 | 0.37 | 0.15 | 0.00 | 0.00 | 0.00 |
| miss<10% | 264 | 0.00 | 0.02 | 0.39 | 0.21 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.01 | 2.38 | 1.74 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:tok | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 70 | 0.01 | 0.01 | 0.44 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 424 | 0.01 | 0.00 | 0.34 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.01 | 0.00 | 0.31 | 0.00 | 0.00 | 0.00 |
| miss<10% | 264 | 0.02 | 0.00 | 0.33 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.68 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 70 | 0.03 | 0.49 | 0.00 | 0.12 | 0.16 | 0.00 | 0.89 | 0.01 | 0.21 | 0.00 | 0.00 |
| GPU≥50% | 424 | 0.10 | 0.08 | 0.07 | 0.00 | 0.00 | 0.00 | 0.21 | 0.04 | 1.19 | 0.00 | 0.01 |
| 10–50% | 89 | 0.24 | 0.04 | 0.09 | 0.00 | 0.00 | 0.00 | 0.15 | 0.04 | 3.13 | 0.00 | 0.00 |
| miss<10% | 264 | 0.37 | 0.65 | 0.13 | 0.24 | 0.00 | 0.00 | 1.02 | 0.06 | 5.16 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.21 | 0.47 | 0.00 | 0.00 | 0.00 | 0.11 | 0.12 | 0.66 | 0.01 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 70 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 424 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 264 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 303 | 257 / 0 / 46 | 1504 | 1505 | 1323 (1292–1992) | 0 (1503) |
| compute, no computed tokens (miss / GPU-prefix hit) | 1855 | 1742 / 0 / 113 | 128 | 1700 | 600 (237–1598) | 0 (600) |

Requests refused at least once: 23 of 853; preemptions: 9; running requests that could not get their next chunk: 19.
Admitted external loads: 95; reservation passed at admission p50 297 / max 1749 blocks; free blocks at admission p50 3933.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.415 |
| time with free blocks < 50% of the pool | 0.394 |
| time with free blocks < 25% of the pool | 0.224 |
| time with free blocks < 10% of the pool | 0.095 |
| time with free blocks < 5% of the pool | 0.046 |
| blocks held by loads in transfer, mean / max | 8 / 3456 |
| in-flight prefill reservation after schedule(), mean / max | 231 / 1967 |
| steps whose running requests used the whole token budget (share of time) | 0.095 |
| steps with a shortened token budget (share of time) | 0.140 |
| running requests, mean / max | 4.0 / 16 |
| waiting + kv-holding requests, mean / max | 1.6 / 27 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 70 | 0.69 | 0.00 | 0.58 / 0.08 | 0.68 [22] | 2.30 [48] | 1.73 [56] | 8.88 [14] |
| GPU≥50% | 424 | 0.64 | 0.00 | 0.67 / 0.29 | 0.19 [153] | 1.59 [271] | 1.13 [386] | 6.97 [38] |
| 10–50% | 89 | 0.57 | 0.00 | 0.68 / 0.26 | 0.39 [38] | 6.16 [51] | 1.91 [82] | 3.77 [7] |
| miss<10% | 264 | 0.56 | 0.00 | 0.74 / 0.35 | 3.02 [115] | 15.05 [149] | 9.16 [247] | 30.64 [17] |
| mixed | 6 | 0.83 | 0.00 | 0.82 / 0.16 | 3.94 [1] | 2.45 [5] | 2.45 [5] | 3.94 [1] |
