## Admission analysis of `ccb-p3728-skip30` (816 requests, 28143 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 2048 | 128 | 1.01 / 5.89 | 0.00 / 0.15 | 0.03 / 0.56 | 0.00 / 0.12 | 0.32 / 0.48 | 0.00 / 0.10 | 0.03 / 0.19 |
| GPU≥50% | 38 | 8192 | 256 | 0.58 / 5.29 | 0.00 / 0.08 | 0.03 / 0.47 | 0.00 / 0.07 | 0.20 / 0.35 | 0.00 / 0.06 | 0.03 / 0.15 |
| miss<10% | 418 | 2048 | 128 | 1.40 / 6.63 | 0.00 / 0.11 | 0.02 / 0.55 | 0.00 / 0.28 | – | – | 0.66 / 0.81 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 1.41 | 0.73 [52%] | 0.18 [13%] | 0.01 [1%] | 0.00 [0%] | 0.15 [11%] | 0.27 [19%] | 0.04 [3%] | 0.00 [0%] | 0.01 [1%] |
| GPU≥50% | 38 | 1.03 | 0.49 [47%] | 0.16 [15%] | 0.00 [0%] | 0.00 [0%] | 0.10 [10%] | 0.24 [23%] | 0.03 [2%] | 0.00 [0%] | 0.02 [2%] |
| miss<10% | 418 | 0.93 | 0.45 [48%] | 0.17 [18%] | 0.01 [1%] | 0.00 [1%] | 0.00 [0%] | 0.17 [18%] | 0.11 [12%] | 0.00 [0%] | 0.02 [2%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.13 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 38 | 0.07 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.09 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.27 | 0.10 | 0.00 | 0.19 | 0.00 | 0.00 |
| GPU≥50% | 38 | 0.22 | 0.09 | 0.00 | 0.17 | 0.00 | 0.00 |
| miss<10% | 418 | 0.28 | 0.10 | 0.00 | 0.16 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.03 | 0.03 | 0.01 | 0.00 | 0.00 | 0.04 | 0.00 | 0.01 |
| GPU≥50% | 38 | 0.02 | 0.01 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.02 |
| miss<10% | 418 | 0.08 | 0.05 | 0.01 | 0.00 | 0.00 | 0.11 | 0.00 | 0.02 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 38 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 47 | 34 / 0 / 13 | 65 | 65 | 126 (60–767) | 600 (600) |

Requests refused at least once: 7 of 816; preemptions: 7; running requests that could not get their next chunk: 16.
Admitted external loads: 566; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.217 |
| time with free blocks < 50% of the pool | 0.132 |
| time with free blocks < 25% of the pool | 0.083 |
| time with free blocks < 10% of the pool | 0.034 |
| time with free blocks < 5% of the pool | 0.016 |
| blocks held by loads in transfer, mean / max | 96 / 1408 |
| in-flight prefill reservation after schedule(), mean / max | 37 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.228 |
| running requests, mean / max | 2.1 / 16 |
| waiting + kv-holding requests, mean / max | 1.2 / 31 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.28 | 0.14 | 0.91 / 0.17 | 0.43 [258] | 2.89 [102] | 0.64 [305] | 2.87 [55] |
| GPU≥50% | 38 | 0.24 | 0.03 | 0.86 / 0.10 | 0.25 [29] | 2.03 [9] | 0.26 [30] | 2.05 [8] |
| miss<10% | 418 | 0.37 | 0.09 | 0.93 / 0.17 | 0.68 [265] | 1.75 [153] | 0.88 [361] | 3.02 [57] |
