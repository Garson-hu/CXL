## Admission analysis of `tool04-320-tokfast11` (1159 requests, 88182 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 122 | 7074 | 384 | 1.38 / 23.18 | 0.00 / 0.80 | 0.29 / 0.40 | 0.00 / 1.78 | 0.15 / 0.40 | 0.00 / 0.00 | 0.27 / 0.50 |
| GPU≥50% | 610 | 6186 | 386 | 0.32 / 4.24 | 0.00 / 0.02 | 0.03 / 0.27 | 0.00 / 0.49 | 0.53 / 0.62 | 0.00 / 0.00 | 0.22 / 0.31 |
| 10–50% | 122 | 2496 | 106 | 0.78 / 21.91 | 0.00 / 0.22 | 0.03 / 0.28 | 0.00 / 2.50 | 0.11 / 0.38 | 0.00 / 0.00 | 0.60 / 1.05 |
| miss<10% | 293 | 13689 | 128 | 5.31 / 29.38 | 0.00 / 0.10 | 0.03 / 0.26 | 0.00 / 3.76 | 0.05 / 0.04 | 0.00 / 0.00 | 3.10 / 4.18 |
| mixed | 12 | 1844 | 32 | 1.76 / 2.77 | 0.00 / 0.00 | 0.30 / 0.28 | 0.00 / 0.00 | 0.48 / 0.42 | 0.00 / 0.00 | 0.49 / 0.47 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 122 | 3.38 | 0.06 [2%] | 0.13 [4%] | 1.31 [39%] | 0.09 [3%] | 0.23 [7%] | 0.40 [12%] | 0.08 [3%] | 0.37 [11%] | 0.71 [21%] | 0.00 [0%] |
| GPU≥50% | 610 | 0.79 | 0.00 [0%] | 0.03 [4%] | 0.08 [11%] | 0.00 [0%] | 0.01 [1%] | 0.01 [1%] | 0.00 [0%] | 0.25 [32%] | 0.41 [51%] | 0.00 [0%] |
| 10–50% | 122 | 3.05 | 0.00 [0%] | 0.10 [3%] | 0.73 [24%] | 0.03 [1%] | 0.04 [1%] | 0.11 [4%] | 0.00 [0%] | 0.26 [9%] | 1.78 [58%] | 0.00 [0%] |
| miss<10% | 293 | 4.12 | 0.00 [0%] | 0.14 [3%] | 0.56 [14%] | 0.01 [0%] | 0.00 [0%] | 0.36 [9%] | 0.00 [0%] | 0.26 [6%] | 2.80 [68%] | 0.00 [0%] |
| mixed | 12 | 0.70 | 0.10 [14%] | 0.02 [2%] | 0.00 [0%] | 0.00 [0%] | 0.23 [33%] | 0.00 [0%] | 0.00 [0%] | 0.35 [50%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 122 | 0.00 | 0.04 | 0.69 | 0.06 | 0.00 | 0.00 |
| GPU≥50% | 610 | 0.00 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 |
| 10–50% | 122 | 0.00 | 0.01 | 0.18 | 0.02 | 0.00 | 0.00 |
| miss<10% | 293 | 0.00 | 0.01 | 0.08 | 0.01 | 0.00 | 0.00 |
| mixed | 12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 122 | 0.00 | 0.11 | 0.00 | 0.00 | 0.29 | 0.00 |
| GPU≥50% | 610 | 0.01 | 0.01 | 0.00 | 0.00 | 0.25 | 0.00 |
| 10–50% | 122 | 0.00 | 0.03 | 0.00 | 0.00 | 0.25 | 0.00 |
| miss<10% | 293 | 0.01 | 0.00 | 0.00 | 0.00 | 0.25 | 0.00 |
| mixed | 12 | 0.02 | 0.00 | 0.00 | 0.00 | 0.26 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 122 | 0.07 | 0.50 | 0.01 | 0.40 | 0.08 | 0.00 | 0.71 | 0.00 |
| GPU≥50% | 610 | 0.02 | 0.06 | 0.00 | 0.01 | 0.00 | 0.00 | 0.40 | 0.00 |
| 10–50% | 122 | 0.08 | 0.52 | 0.01 | 0.11 | 0.00 | 0.00 | 1.78 | 0.00 |
| miss<10% | 293 | 0.13 | 0.48 | 0.00 | 0.36 | 0.00 | 0.00 | 2.80 | 0.00 |
| mixed | 12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 122 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 610 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 122 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 293 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 853 | 817 / 0 / 36 | 384 | 511 | 365 (200–1493) | 0 (1728) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3950 | 3950 / 0 / 0 | 128 | 1700 | 818 (206–1736) | 0 (0) |

Requests refused at least once: 47 of 1159; preemptions: 3; running requests that could not get their next chunk: 6.
Admitted external loads: 169; reservation passed at admission p50 0 / max 1694 blocks; free blocks at admission p50 5886.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.258 |
| time with free blocks < 50% of the pool | 0.175 |
| time with free blocks < 25% of the pool | 0.092 |
| time with free blocks < 10% of the pool | 0.034 |
| time with free blocks < 5% of the pool | 0.016 |
| blocks held by loads in transfer, mean / max | 6 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 124 / 1962 |
| steps whose running requests used the whole token budget (share of time) | 0.070 |
| steps with a shortened token budget (share of time) | 0.080 |
| running requests, mean / max | 1.9 / 12 |
| waiting + kv-holding requests, mean / max | 0.5 / 9 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 122 | 0.48 | 0.00 | 0.81 / 0.26 | 0.27 [63] | 2.59 [59] | 0.76 [110] | 18.53 [12] |
| GPU≥50% | 610 | 0.38 | 0.00 | 0.80 / 0.38 | 0.16 [380] | 1.58 [230] | 0.29 [591] | 1.93 [19] |
| 10–50% | 122 | 0.37 | 0.00 | 0.80 / 0.35 | 0.45 [77] | 6.64 [45] | 0.73 [118] | 36.31 [4] |
| miss<10% | 293 | 0.40 | 0.00 | 0.82 / 0.42 | 2.53 [177] | 13.21 [116] | 5.30 [289] | 26.39 [4] |
| mixed | 12 | 0.50 | 0.00 | 0.77 / 0.36 | 0.30 [6] | 1.97 [6] | 1.11 [11] | 2.49 [1] |
