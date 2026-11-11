## Admission analysis of `cc-p3728-p2` (816 requests, 22341 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 2048 | 128 | 0.71 / 2.46 | 0.00 / 0.05 | 0.02 / 0.23 | 0.00 / 0.12 | 0.37 / 0.38 | 0.00 / 0.00 | 0.17 / 0.14 |
| GPU≥50% | 32 | 8192 | 512 | 0.27 / 2.77 | 0.00 / 0.03 | 0.03 / 0.25 | 0.00 / 0.19 | 0.17 / 0.26 | 0.00 / 0.00 | 0.03 / 0.13 |
| miss<10% | 418 | 2048 | 128 | 1.44 / 7.93 | 0.00 / 0.07 | 0.02 / 0.20 | 0.00 / 0.94 | – | – | 0.67 / 0.86 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.78 | 0.04 [5%] | 0.15 [19%] | 0.09 [12%] | 0.02 [2%] | 0.19 [24%] | 0.00 [0%] | 0.00 [0%] | 0.22 [28%] | 0.03 [4%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.03 [4%] |
| GPU≥50% | 32 | 0.74 | 0.01 [1%] | 0.15 [20%] | 0.11 [15%] | 0.02 [3%] | 0.14 [18%] | 0.00 [0%] | 0.00 [0%] | 0.24 [32%] | 0.02 [3%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.06 [8%] |
| miss<10% | 418 | 1.21 | 0.00 [0%] | 0.31 [26%] | 0.17 [14%] | 0.02 [2%] | 0.00 [0%] | 0.02 [2%] | 0.00 [0%] | 0.12 [10%] | 0.03 [3%] | 0.00 [0%] | 0.47 [39%] | 0.00 [0%] | 0.06 [5%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.00 | 0.02 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 32 | 0.00 | 0.02 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.02 | 0.03 | 0.01 | 0.00 | 0.00 | 0.00 | 0.01 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.04 | 0.03 | 0.01 | 0.14 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 32 | 0.05 | 0.04 | 0.00 | 0.16 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.04 | 0.03 | 0.01 | 0.12 | 0.00 | 0.00 | 0.01 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.03 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 | 0.02 |
| GPU≥50% | 32 | 0.05 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 | 0.06 |
| miss<10% | 418 | 0.26 | 0.11 | 0.01 | 0.02 | 0.00 | 0.00 | 0.03 | 0.00 | 0.47 | 0.00 | 0.04 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 32 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 17 | 12 / 0 / 5 | 512 | 512 | 445 (245–732) | 0 (257) |
| compute, no computed tokens (miss / GPU-prefix hit) | 158 | 158 / 0 / 0 | 128 | 512 | 250 (56–446) | 0 (600) |

Requests refused at least once: 24 of 816; preemptions: 3; running requests that could not get their next chunk: 6.
Admitted external loads: 564; reservation passed at admission p50 0 / max 391 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.219 |
| time with free blocks < 50% of the pool | 0.144 |
| time with free blocks < 25% of the pool | 0.088 |
| time with free blocks < 10% of the pool | 0.035 |
| time with free blocks < 5% of the pool | 0.017 |
| blocks held by loads in transfer, mean / max | 60 / 2688 |
| in-flight prefill reservation after schedule(), mean / max | 50 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.134 |
| steps with a shortened token budget (share of time) | 0.098 |
| running requests, mean / max | 2.4 / 16 |
| waiting + kv-holding requests, mean / max | 1.0 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 366 | 0.29 | 0.00 | 0.91 / 0.15 | 0.42 [261] | 1.41 [105] | 0.51 [308] | 1.70 [58] |
| GPU≥50% | 32 | 0.28 | 0.00 | 0.89 / 0.29 | 0.20 [23] | 1.50 [9] | 0.24 [29] | 2.77 [3] |
| miss<10% | 418 | 0.37 | 0.00 | 0.97 / 0.18 | 0.77 [264] | 1.90 [154] | 1.06 [355] | 5.64 [63] |
