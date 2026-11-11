## Admission analysis of `conv08-320-base` (291 requests, 21161 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 7833 | 416 | 25.23 / 31.45 | 6.75 / 9.74 | 2.77 / 6.21 | 0.00 / 1.71 | 0.39 / 0.81 | 0.00 / 0.31 | 0.41 / 0.45 |
| GPU≥50% | 28 | 906 | 25 | 12.88 / 41.20 | 3.44 / 6.33 | 1.77 / 8.24 | 0.00 / 0.02 | – | – | 0.39 / 0.53 |
| 10–50% | 66 | 2103 | 83 | 10.81 / 40.31 | 1.34 / 6.46 | 1.52 / 5.96 | 0.00 / 0.08 | 0.19 / 0.68 | 0.00 / 0.47 | 0.80 / 0.95 |
| miss<10% | 186 | 13883 | 128 | 15.33 / 42.97 | 2.56 / 4.96 | 2.77 / 7.74 | 0.00 / 1.05 | – | – | 3.32 / 4.14 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 18.77 | 9.95 [53%] | 0.80 [4%] | 4.96 [26%] | 0.19 [1%] | 1.83 [10%] | 1.04 [6%] | 0.00 [0%] |
| GPU≥50% | 28 | 14.58 | 9.21 [63%] | 0.72 [5%] | 3.82 [26%] | 0.00 [0%] | 0.02 [0%] | 0.81 [6%] | 0.00 [0%] |
| 10–50% | 66 | 12.55 | 8.14 [65%] | 0.58 [5%] | 3.03 [24%] | 0.00 [0%] | 0.10 [1%] | 0.69 [5%] | 0.00 [0%] |
| miss<10% | 186 | 13.75 | 7.98 [58%] | 0.63 [5%] | 3.37 [25%] | 0.00 [0%] | 1.01 [7%] | 0.76 [6%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 11 | 5.32 | 0.57 | 3.84 | 0.00 | 0.00 |
| GPU≥50% | 28 | 4.45 | 0.27 | 1.61 | 0.00 | 0.00 |
| 10–50% | 66 | 4.47 | 0.16 | 1.83 | 0.00 | 0.00 |
| miss<10% | 186 | 3.55 | 0.18 | 1.23 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 11 | 4.07 | 0.23 | 0.99 | 0.00 | 0.92 |
| GPU≥50% | 28 | 4.76 | 0.45 | 2.21 | 0.00 | 0.81 |
| 10–50% | 66 | 3.65 | 0.42 | 1.19 | 0.00 | 0.69 |
| miss<10% | 186 | 4.41 | 0.44 | 2.12 | 0.00 | 0.76 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.00 | 0.00 | 0.00 | 1.71 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 |
| 10–50% | 66 | 0.00 | 0.00 | 0.00 | 0.08 | 0.00 | 0.00 |
| miss<10% | 186 | 0.02 | 0.00 | 0.03 | 1.01 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.19 | 0.00 | 0.00 | 0.11 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 66 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 |
| miss<10% | 186 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 533 | 533 / 0 / 0 | 832 | 871 | 542 (116–766) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5775 | 5775 / 0 / 0 | 128 | 1035 | 405 (92–1309) | 0 (0) |
| promotion after a load | 55 | 55 / 0 / 0 | 128 | 970 | 537 (3–550) | 0 (0) |

Requests refused at least once: 82 of 291; preemptions: 5; running requests that could not get their next chunk: 10.
Admitted external loads: 14; reservation passed at admission p50 0 / max 95 blocks; free blocks at admission p50 1913.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.605 |
| time with free blocks < 50% of the pool | 0.653 |
| time with free blocks < 25% of the pool | 0.511 |
| time with free blocks < 10% of the pool | 0.246 |
| time with free blocks < 5% of the pool | 0.127 |
| blocks held by loads in transfer, mean / max | 5 / 1008 |
| in-flight prefill reservation after schedule(), mean / max | 265 / 1890 |
| steps whose running requests used the whole token budget (share of time) | 0.455 |
| running requests, mean / max | 5.8 / 13 |
| waiting + kv-holding requests, mean / max | 3.1 / 15 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.73 | 0.64 | 0.17 / 0.06 | 29.56 [3] | 25.23 [8] | 9.02 [5] | 29.56 [6] |
| GPU≥50% | 28 | 0.68 | 0.61 | 0.57 / 0.05 | 0.21 [9] | 14.77 [19] | 5.82 [18] | 25.41 [10] |
| 10–50% | 66 | 0.47 | 0.42 | 0.50 / 0.09 | 0.84 [35] | 16.16 [31] | 2.62 [41] | 22.97 [25] |
| miss<10% | 186 | 0.55 | 0.53 | 0.49 / 0.07 | 5.51 [84] | 19.72 [102] | 9.75 [112] | 25.53 [74] |
