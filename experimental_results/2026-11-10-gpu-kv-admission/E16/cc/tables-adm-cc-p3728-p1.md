## Admission analysis of `cc-p3728-p1` (816 requests, 22256 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 368 | 2048 | 128 | 0.73 / 6.03 | 0.00 / 0.21 | 0.02 / 0.33 | 0.00 / 0.05 | 0.37 / 0.39 | 0.00 / 0.00 | 0.17 / 0.14 |
| GPU≥50% | 30 | 8192 | 512 | 0.25 / 4.18 | 0.00 / 0.13 | 0.02 / 0.26 | 0.00 / 0.00 | 0.17 / 0.26 | 0.00 / 0.00 | 0.03 / 0.14 |
| miss<10% | 418 | 2048 | 128 | 1.44 / 7.64 | 0.00 / 0.18 | 0.02 / 0.32 | 0.00 / 0.66 | – | – | 0.66 / 0.85 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 368 | 0.98 | 0.04 [4%] | 0.20 [21%] | 0.26 [26%] | 0.05 [5%] | 0.16 [17%] | 0.02 [2%] | 0.01 [1%] | 0.23 [23%] | 0.00 [0%] | 0.00 [0%] | 0.02 [2%] |
| GPU≥50% | 30 | 0.64 | 0.01 [2%] | 0.10 [16%] | 0.15 [23%] | 0.05 [8%] | 0.12 [19%] | 0.00 [0%] | 0.00 [0%] | 0.19 [30%] | 0.00 [0%] | 0.00 [0%] | 0.01 [2%] |
| miss<10% | 418 | 1.17 | 0.00 [0%] | 0.29 [25%] | 0.29 [25%] | 0.04 [4%] | 0.00 [0%] | 0.04 [3%] | 0.00 [0%] | 0.12 [10%] | 0.37 [32%] | 0.00 [0%] | 0.01 [1%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 368 | 0.00 | 0.05 | 0.13 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 30 | 0.00 | 0.01 | 0.10 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.04 | 0.12 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 368 | 0.07 | 0.09 | 0.02 | 0.00 | 0.00 | 0.15 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 30 | 0.05 | 0.04 | 0.02 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.01 |
| miss<10% | 418 | 0.07 | 0.10 | 0.02 | 0.00 | 0.00 | 0.11 | 0.00 | 0.00 | 0.01 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 368 | 0.01 | 0.01 | 0.02 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 30 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.18 | 0.07 | 0.04 | 0.00 | 0.00 | 0.37 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 368 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 30 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 74 | 59 / 0 / 15 | 512 | 512 | 314 (118–519) | 49 (364) |
| compute, no computed tokens (miss / GPU-prefix hit) | 226 | 226 / 0 / 0 | 128 | 256 | 193 (56–446) | 0 (0) |

Requests refused at least once: 51 of 816; preemptions: 3; running requests that could not get their next chunk: 7.
Admitted external loads: 562; reservation passed at admission p50 0 / max 387 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.219 |
| time with free blocks < 50% of the pool | 0.142 |
| time with free blocks < 25% of the pool | 0.091 |
| time with free blocks < 10% of the pool | 0.034 |
| time with free blocks < 5% of the pool | 0.017 |
| blocks held by loads in transfer, mean / max | 60 / 2624 |
| in-flight prefill reservation after schedule(), mean / max | 49 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.134 |
| steps with a shortened token budget (share of time) | 0.097 |
| running requests, mean / max | 2.3 / 16 |
| waiting + kv-holding requests, mean / max | 1.1 / 32 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 368 | 0.29 | 0.00 | 0.91 / 0.14 | 0.42 [261] | 1.50 [107] | 0.51 [306] | 2.41 [62] |
| GPU≥50% | 30 | 0.30 | 0.00 | 0.90 / 0.42 | 0.20 [21] | 1.48 [9] | 0.22 [27] | 4.18 [3] |
| miss<10% | 418 | 0.36 | 0.00 | 0.97 / 0.15 | 0.74 [268] | 1.82 [150] | 1.06 [354] | 4.25 [64] |
