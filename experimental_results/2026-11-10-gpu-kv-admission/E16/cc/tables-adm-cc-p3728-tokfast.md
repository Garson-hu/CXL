## Admission analysis of `cc-p3728-tokfast` (816 requests, 22355 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 2048 | 128 | 0.70 / 5.72 | 0.00 / 0.19 | 0.02 / 0.30 | 0.00 / 0.05 | 0.36 / 0.38 | 0.00 / 0.00 | 0.17 / 0.14 |
| GPU≥50% | 32 | 8192 | 256 | 0.27 / 6.34 | 0.00 / 0.40 | 0.03 / 0.30 | 0.00 / 0.02 | 0.19 / 0.28 | 0.00 / 0.00 | 0.03 / 0.12 |
| miss<10% | 418 | 2048 | 128 | 1.44 / 7.67 | 0.00 / 0.17 | 0.02 / 0.32 | 0.00 / 0.68 | – | – | 0.66 / 0.85 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.92 | 0.04 [4%] | 0.18 [20%] | 0.24 [26%] | 0.03 [3%] | 0.17 [18%] | 0.03 [3%] | 0.01 [1%] | 0.23 [25%] | 0.00 [0%] | 0.00 [0%] | 0.01 [1%] |
| GPU≥50% | 32 | 0.99 | 0.02 [2%] | 0.17 [17%] | 0.37 [37%] | 0.05 [5%] | 0.11 [11%] | 0.00 [0%] | 0.01 [1%] | 0.23 [24%] | 0.00 [0%] | 0.00 [0%] | 0.02 [2%] |
| miss<10% | 418 | 1.17 | 0.00 [0%] | 0.29 [25%] | 0.27 [23%] | 0.03 [2%] | 0.00 [0%] | 0.02 [2%] | 0.00 [0%] | 0.13 [11%] | 0.43 [36%] | 0.00 [0%] | 0.01 [1%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.00 | 0.04 | 0.13 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 32 | 0.00 | 0.09 | 0.27 | 0.03 | 0.00 | 0.00 | 0.00 | 0.01 |
| miss<10% | 418 | 0.00 | 0.03 | 0.12 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.06 | 0.08 | 0.01 | 0.00 | 0.00 | 0.15 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 32 | 0.04 | 0.05 | 0.02 | 0.00 | 0.00 | 0.17 | 0.00 | 0.00 | 0.01 |
| miss<10% | 418 | 0.08 | 0.10 | 0.02 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.01 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.01 | 0.01 | 0.03 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 32 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.18 | 0.05 | 0.02 | 0.00 | 0.00 | 0.43 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 32 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 98 | 81 / 0 / 17 | 512 | 512 | 251 (117–494) | 49 (364) |
| compute, no computed tokens (miss / GPU-prefix hit) | 189 | 189 / 0 / 0 | 128 | 256 | 185 (7–446) | 0 (0) |

Requests refused at least once: 46 of 816; preemptions: 4; running requests that could not get their next chunk: 11.
Admitted external loads: 563; reservation passed at admission p50 0 / max 387 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.218 |
| time with free blocks < 50% of the pool | 0.141 |
| time with free blocks < 25% of the pool | 0.088 |
| time with free blocks < 10% of the pool | 0.034 |
| time with free blocks < 5% of the pool | 0.017 |
| blocks held by loads in transfer, mean / max | 60 / 2624 |
| in-flight prefill reservation after schedule(), mean / max | 49 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.134 |
| steps with a shortened token budget (share of time) | 0.096 |
| running requests, mean / max | 2.3 / 16 |
| waiting + kv-holding requests, mean / max | 1.1 / 32 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.30 | 0.00 | 0.91 / 0.14 | 0.42 [257] | 1.50 [109] | 0.51 [305] | 2.40 [61] |
| GPU≥50% | 32 | 0.34 | 0.00 | 0.89 / 0.21 | 0.19 [21] | 1.50 [11] | 0.24 [28] | 6.17 [4] |
| miss<10% | 418 | 0.37 | 0.00 | 0.97 / 0.15 | 0.73 [265] | 1.82 [153] | 1.06 [353] | 4.27 [65] |
