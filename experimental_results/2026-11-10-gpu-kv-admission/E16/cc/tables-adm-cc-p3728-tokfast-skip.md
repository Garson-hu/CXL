## Admission analysis of `cc-p3728-tokfast-skip` (816 requests, 22323 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 365 | 2048 | 128 | 0.70 / 2.49 | 0.00 / 0.12 | 0.02 / 0.16 | 0.00 / 0.17 | 0.38 / 0.39 | 0.00 / 0.00 | 0.17 / 0.14 |
| GPU≥50% | 33 | 8192 | 256 | 0.27 / 1.96 | 0.00 / 0.02 | 0.03 / 0.20 | 0.00 / 0.15 | 0.19 / 0.26 | 0.00 / 0.00 | 0.02 / 0.11 |
| miss<10% | 418 | 2048 | 128 | 1.44 / 7.95 | 0.00 / 0.10 | 0.02 / 0.14 | 0.00 / 0.97 | – | – | 0.66 / 0.86 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 365 | 0.84 | 0.04 [5%] | 0.19 [22%] | 0.11 [13%] | 0.04 [4%] | 0.19 [23%] | 0.01 [1%] | 0.00 [1%] | 0.21 [25%] | 0.04 [5%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 33 | 0.63 | 0.02 [3%] | 0.13 [20%] | 0.09 [13%] | 0.01 [1%] | 0.14 [22%] | 0.00 [0%] | 0.01 [2%] | 0.22 [35%] | 0.02 [3%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 418 | 1.21 | 0.00 [0%] | 0.34 [28%] | 0.16 [13%] | 0.04 [3%] | 0.00 [0%] | 0.01 [1%] | 0.00 [0%] | 0.11 [9%] | 0.03 [3%] | 0.52 [43%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 365 | 0.00 | 0.04 | 0.05 | 0.02 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 33 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.04 | 0.04 | 0.02 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|
| host≥50% | 365 | 0.03 | 0.00 | 0.13 | 0.00 | 0.00 |
| GPU≥50% | 33 | 0.04 | 0.00 | 0.16 | 0.00 | 0.00 |
| miss<10% | 418 | 0.03 | 0.00 | 0.11 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 365 | 0.05 | 0.05 | 0.01 | 0.01 | 0.00 | 0.00 | 0.04 | 0.00 | 0.00 |
| GPU≥50% | 33 | 0.05 | 0.07 | 0.00 | 0.00 | 0.01 | 0.00 | 0.02 | 0.00 | 0.00 |
| miss<10% | 418 | 0.27 | 0.11 | 0.02 | 0.01 | 0.00 | 0.00 | 0.03 | 0.52 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 365 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 33 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 37 | 28 / 0 / 9 | 512 | 512 | 442 (63–638) | 34 (353) |
| compute, no computed tokens (miss / GPU-prefix hit) | 127 | 127 / 0 / 0 | 128 | 512 | 252 (6–508) | 0 (0) |

Requests refused at least once: 23 of 816; preemptions: 5; running requests that could not get their next chunk: 12.
Admitted external loads: 563; reservation passed at admission p50 0 / max 387 blocks; free blocks at admission p50 3662.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.219 |
| time with free blocks < 50% of the pool | 0.145 |
| time with free blocks < 25% of the pool | 0.089 |
| time with free blocks < 10% of the pool | 0.034 |
| time with free blocks < 5% of the pool | 0.014 |
| blocks held by loads in transfer, mean / max | 61 / 2688 |
| in-flight prefill reservation after schedule(), mean / max | 50 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.136 |
| steps with a shortened token budget (share of time) | 0.099 |
| running requests, mean / max | 2.4 / 16 |
| waiting + kv-holding requests, mean / max | 1.1 / 29 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 365 | 0.28 | 0.00 | 0.91 / 0.15 | 0.42 [263] | 1.41 [102] | 0.51 [309] | 1.70 [56] |
| GPU≥50% | 33 | 0.30 | 0.00 | 0.85 / 0.19 | 0.20 [23] | 1.50 [10] | 0.24 [29] | 1.52 [4] |
| miss<10% | 418 | 0.37 | 0.00 | 0.97 / 0.17 | 0.76 [264] | 1.91 [154] | 1.05 [355] | 5.64 [63] |
