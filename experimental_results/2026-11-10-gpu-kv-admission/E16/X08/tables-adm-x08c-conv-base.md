## Admission analysis of `x08c-conv-base` (291 requests, 21176 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 7833 | 416 | 25.45 / 31.74 | 6.76 / 9.78 | 2.78 / 6.23 | 0.00 / 1.72 | 0.39 / 0.75 | 0.00 / 0.31 | 0.41 / 0.50 |
| GPU≥50% | 28 | 906 | 25 | 12.90 / 41.40 | 2.23 / 6.12 | 1.77 / 8.51 | 0.00 / 0.04 | – | – | 0.37 / 0.52 |
| 10–50% | 66 | 2103 | 79 | 10.85 / 40.51 | 1.34 / 6.51 | 1.52 / 5.95 | 0.00 / 0.08 | 0.19 / 0.68 | 0.00 / 0.47 | 0.85 / 0.97 |
| miss<10% | 186 | 13883 | 128 | 15.35 / 43.04 | 2.68 / 5.06 | 2.42 / 7.74 | 0.00 / 1.03 | – | – | 3.32 / 4.14 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 18.78 | 9.93 [53%] | 0.86 [5%] | 4.99 [27%] | 0.19 [1%] | 1.83 [10%] | 0.98 [5%] | 0.00 [0%] |
| GPU≥50% | 28 | 14.67 | 9.25 [63%] | 0.73 [5%] | 3.86 [26%] | 0.00 [0%] | 0.04 [0%] | 0.79 [5%] | 0.00 [0%] |
| 10–50% | 66 | 12.59 | 8.18 [65%] | 0.59 [5%] | 3.04 [24%] | 0.00 [0%] | 0.10 [1%] | 0.67 [5%] | 0.00 [0%] |
| miss<10% | 186 | 13.83 | 8.03 [58%] | 0.65 [5%] | 3.38 [24%] | 0.00 [0%] | 1.01 [7%] | 0.76 [5%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 11 | 5.33 | 0.57 | 3.88 | 0.00 | 0.00 |
| GPU≥50% | 28 | 4.29 | 0.24 | 1.58 | 0.00 | 0.00 |
| 10–50% | 66 | 4.51 | 0.16 | 1.83 | 0.00 | 0.00 |
| miss<10% | 186 | 3.62 | 0.19 | 1.24 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 11 | 4.04 | 0.24 | 1.07 | 0.00 | 0.88 |
| GPU≥50% | 28 | 4.96 | 0.49 | 2.28 | 0.00 | 0.78 |
| 10–50% | 66 | 3.65 | 0.42 | 1.21 | 0.00 | 0.67 |
| miss<10% | 186 | 4.41 | 0.46 | 2.12 | 0.00 | 0.76 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.00 | 0.00 | 1.72 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.04 | 0.00 | 0.00 |
| 10–50% | 66 | 0.00 | 0.00 | 0.08 | 0.00 | 0.00 |
| miss<10% | 186 | 0.00 | 0.02 | 1.01 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.19 | 0.00 | 0.00 | 0.00 | 0.11 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 66 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 |
| miss<10% | 186 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 535 | 535 / 0 / 0 | 832 | 871 | 542 (116–766) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5786 | 5786 / 0 / 0 | 128 | 1035 | 407 (92–1323) | 0 (0) |
| promotion after a load | 55 | 55 / 0 / 0 | 128 | 970 | 537 (3–550) | 0 (0) |

Requests refused at least once: 82 of 291; preemptions: 5; running requests that could not get their next chunk: 10.
Admitted external loads: 14; reservation passed at admission p50 0 / max 95 blocks; free blocks at admission p50 1913.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.606 |
| time with free blocks < 50% of the pool | 0.652 |
| time with free blocks < 25% of the pool | 0.511 |
| time with free blocks < 10% of the pool | 0.246 |
| time with free blocks < 5% of the pool | 0.127 |
| blocks held by loads in transfer, mean / max | 5 / 1008 |
| in-flight prefill reservation after schedule(), mean / max | 265 / 1890 |
| steps whose running requests used the whole token budget (share of time) | 0.454 |
| running requests, mean / max | 5.8 / 13 |
| waiting + kv-holding requests, mean / max | 3.1 / 15 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.73 | 0.64 | 0.17 / 0.06 | 29.72 [3] | 25.45 [8] | 9.03 [5] | 29.72 [6] |
| GPU≥50% | 28 | 0.64 | 0.61 | 0.57 / 0.05 | 0.32 [10] | 17.74 [18] | 5.84 [18] | 25.53 [10] |
| 10–50% | 66 | 0.47 | 0.42 | 0.50 / 0.09 | 0.84 [35] | 16.28 [31] | 2.58 [41] | 23.27 [25] |
| miss<10% | 186 | 0.56 | 0.53 | 0.52 / 0.07 | 5.43 [81] | 20.07 [105] | 9.52 [111] | 24.27 [75] |
