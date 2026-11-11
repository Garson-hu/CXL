## Admission analysis of `ccb-p2560-skip30` (816 requests, 28526 engine steps, pool 2560 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 370 | 2048 | 128 | 0.82 / 4.21 | 0.00 / 0.12 | 0.02 / 0.46 | 0.00 / 0.10 | 0.24 / 0.38 | 0.00 / 0.09 | 0.03 / 0.15 |
| GPU≥50% | 28 | 8192 | 128 | 0.58 / 4.27 | 0.00 / 0.02 | 0.05 / 0.57 | 0.00 / 0.14 | 0.12 / 0.27 | 0.00 / 0.06 | 0.03 / 0.11 |
| miss<10% | 418 | 2048 | 128 | 1.43 / 7.18 | 0.00 / 0.08 | 0.02 / 0.47 | 0.00 / 0.53 | – | – | 0.66 / 0.79 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:blocks |
|---|---|---|---|---|---|---|---|
| host≥50% | 370 | 1.13 | 0.57 [50%] | 0.13 [12%] | 0.14 [12%] | 0.23 [21%] | 0.06 [5%] |
| GPU≥50% | 28 | 1.07 | 0.49 [45%] | 0.13 [12%] | 0.13 [12%] | 0.25 [24%] | 0.07 [6%] |
| miss<10% | 418 | 1.08 | 0.51 [47%] | 0.15 [14%] | 0.00 [0%] | 0.15 [14%] | 0.27 [25%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 370 | 0.09 | 0.02 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.01 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.06 | 0.02 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | pol:blocks |
|---|---|---|---|---|---|
| host≥50% | 370 | 0.22 | 0.07 | 0.17 | 0.00 |
| GPU≥50% | 28 | 0.29 | 0.09 | 0.19 | 0.00 |
| miss<10% | 418 | 0.24 | 0.07 | 0.15 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | pol:blocks |
|---|---|---|---|---|---|
| host≥50% | 370 | 0.03 | 0.01 | 0.00 | 0.05 |
| GPU≥50% | 28 | 0.06 | 0.02 | 0.00 | 0.07 |
| miss<10% | 418 | 0.21 | 0.05 | 0.00 | 0.27 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 370 | 0.09 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.06 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 566; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 2559.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.279 |
| time with free blocks < 50% of the pool | 0.181 |
| time with free blocks < 25% of the pool | 0.116 |
| time with free blocks < 10% of the pool | 0.056 |
| time with free blocks < 5% of the pool | 0.036 |
| blocks held by loads in transfer, mean / max | 80 / 1152 |
| in-flight prefill reservation after schedule(), mean / max | 35 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.226 |
| running requests, mean / max | 1.8 / 14 |
| waiting + kv-holding requests, mean / max | 1.1 / 17 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 370 | 0.28 | 0.12 | 0.87 / 0.12 | 0.41 [266] | 2.16 [104] | 0.46 [298] | 2.08 [72] |
| GPU≥50% | 28 | 0.36 | 0.04 | 0.72 / 0.02 | 0.25 [18] | 2.10 [10] | 0.24 [17] | 0.73 [11] |
| miss<10% | 418 | 0.36 | 0.07 | 0.95 / 0.10 | 0.69 [266] | 2.15 [152] | 0.78 [336] | 3.57 [82] |
