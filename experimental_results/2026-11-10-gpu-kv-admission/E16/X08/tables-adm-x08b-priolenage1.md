## Admission analysis of `x08b-priolenage1` (544 requests, 21884 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 91 | 6167 | 320 | 11.91 / 23.14 | 5.16 / 6.76 | 1.29 / 2.44 | 0.00 / 0.35 | 0.76 / 0.82 | 0.00 / 0.39 | 0.42 / 0.54 |
| GPU≥50% | 220 | 6251 | 53 | 3.96 / 20.80 | 1.20 / 3.47 | 0.77 / 2.18 | 0.00 / 0.07 | 0.15 / 0.23 | 0.00 / 0.52 | 0.36 / 0.45 |
| 10–50% | 64 | 2103 | 77 | 2.80 / 18.17 | 0.69 / 3.83 | 0.72 / 1.72 | 0.00 / 0.12 | 0.20 / 0.44 | 0.00 / 0.80 | 0.52 / 0.82 |
| miss<10% | 168 | 13996 | 128 | 11.73 / 44.71 | 1.20 / 3.81 | 1.50 / 5.47 | 0.00 / 1.15 | – | – | 3.21 / 4.12 |
| mixed | 1 | 3151 | 160 | 6.17 / 6.17 | 1.86 / 1.86 | 0.85 / 0.85 | 2.59 / 2.59 | 0.15 / 0.15 | 0.00 / 0.00 | 0.34 / 0.34 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 91 | 10.74 | 6.15 [57%] | 0.33 [3%] | 2.77 [26%] | 0.10 [1%] | 0.05 [0%] | 0.37 [3%] | 0.00 [0%] | 0.98 [9%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 220 | 5.74 | 3.51 [61%] | 0.23 [4%] | 1.16 [20%] | 0.06 [1%] | 0.00 [0%] | 0.06 [1%] | 0.01 [0%] | 0.69 [12%] | 0.00 [0%] | 0.03 [1%] |
| 10–50% | 64 | 5.75 | 3.34 [58%] | 0.13 [2%] | 1.38 [24%] | 0.06 [1%] | 0.00 [0%] | 0.12 [2%] | 0.00 [0%] | 0.68 [12%] | 0.00 [0%] | 0.04 [1%] |
| miss<10% | 168 | 10.43 | 5.62 [54%] | 0.57 [5%] | 2.45 [24%] | 0.04 [0%] | 0.00 [0%] | 0.99 [9%] | 0.00 [0%] | 0.67 [6%] | 0.00 [0%] | 0.10 [1%] |
| mixed | 1 | 5.45 | 1.86 [34%] | 0.00 [0%] | 0.12 [2%] | 0.00 [0%] | 0.00 [0%] | 2.59 [48%] | 0.00 [0%] | 0.88 [16%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 91 | 4.60 | 0.09 | 2.06 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 220 | 2.81 | 0.06 | 0.59 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 2.76 | 0.02 | 1.05 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 168 | 2.79 | 0.10 | 0.90 | 0.00 | 0.00 | 0.00 | 0.01 |
| mixed | 1 | 1.86 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 91 | 0.89 | 0.13 | 0.56 | 0.00 | 0.00 | 0.00 | 0.86 | 0.00 | 0.00 |
| GPU≥50% | 220 | 0.68 | 0.17 | 0.56 | 0.06 | 0.00 | 0.00 | 0.69 | 0.00 | 0.03 |
| 10–50% | 64 | 0.51 | 0.11 | 0.33 | 0.06 | 0.00 | 0.00 | 0.68 | 0.00 | 0.04 |
| miss<10% | 168 | 2.75 | 0.46 | 1.48 | 0.04 | 0.00 | 0.00 | 0.66 | 0.00 | 0.08 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.85 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 91 | 0.00 | 0.00 | 0.01 | 0.34 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 220 | 0.00 | 0.00 | 0.00 | 0.06 | 0.01 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 168 | 0.07 | 0.01 | 0.08 | 0.99 | 0.00 | 0.00 | 0.00 | 0.01 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 2.59 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 91 | 0.33 | 0.03 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 |
| GPU≥50% | 220 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 168 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1302 | 1287 / 0 / 15 | 384 | 387 | 159 (32–360) | 0 (300) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4934 | 4934 / 0 / 0 | 128 | 1700 | 709 (109–1776) | 0 (0) |
| promotion after a load | 31 | 31 / 0 / 0 | 38 | 38 | 16 (9–33) | 0 (0) |

Requests refused at least once: 106 of 544; preemptions: 3; running requests that could not get their next chunk: 7.
Admitted external loads: 103; reservation passed at admission p50 0 / max 209 blocks; free blocks at admission p50 1319.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.606 |
| time with free blocks < 50% of the pool | 0.658 |
| time with free blocks < 25% of the pool | 0.509 |
| time with free blocks < 10% of the pool | 0.258 |
| time with free blocks < 5% of the pool | 0.136 |
| blocks held by loads in transfer, mean / max | 29 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 254 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.418 |
| running requests, mean / max | 6.3 / 16 |
| waiting + kv-holding requests, mean / max | 3.4 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 91 | 0.55 | 0.45 | 0.16 / 0.04 | 11.16 [41] | 12.70 [50] | 5.21 [33] | 16.18 [58] |
| GPU≥50% | 220 | 0.49 | 0.43 | 0.49 / 0.05 | 0.42 [112] | 7.03 [108] | 2.04 [145] | 12.86 [75] |
| 10–50% | 64 | 0.44 | 0.38 | 0.40 / 0.04 | 1.33 [36] | 5.31 [28] | 1.39 [35] | 14.31 [29] |
| miss<10% | 168 | 0.46 | 0.39 | 0.48 / 0.04 | 4.39 [91] | 15.60 [77] | 5.87 [107] | 21.45 [61] |
| mixed | 1 | 1.00 | 1.00 | 0.09 / 0.09 | – | 6.17 [1] | – | 6.17 [1] |
