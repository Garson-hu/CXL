## Admission analysis of `conv04-320-base` (599 requests, 86389 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 65 | 9871 | 544 | 0.79 / 20.68 | 0.00 / 1.40 | 0.03 / 2.03 | 0.00 / 0.27 | 0.11 / 0.45 | 0.00 / 0.67 | 0.21 / 0.50 |
| GPU≥50% | 54 | 901 | 26 | 0.16 / 29.13 | 0.00 / 1.40 | 0.04 / 2.86 | 0.00 / 0.00 | – | – | 0.11 / 0.32 |
| 10–50% | 131 | 2293 | 104 | 0.77 / 26.53 | 0.00 / 1.16 | 0.03 / 2.08 | 0.00 / 0.02 | 0.10 / 0.53 | 0.00 / 1.25 | 0.45 / 0.77 |
| miss<10% | 339 | 13712 | 128 | 5.15 / 27.21 | 0.00 / 1.44 | 0.03 / 1.78 | 0.00 / 0.32 | 0.05 / 0.04 | 0.00 / 0.00 | 3.03 / 3.84 |
| mixed | 10 | 1763 | 32 | 1.87 / 21.30 | 0.00 / 1.41 | 0.76 / 2.82 | 0.00 / 0.00 | 0.08 / 0.44 | 0.00 / 0.51 | 0.20 / 0.38 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 65 | 4.82 | 3.06 [63%] | 0.15 [3%] | 0.69 [14%] | 0.12 [3%] | 0.27 [6%] | 0.53 [11%] |
| GPU≥50% | 54 | 4.26 | 2.44 [57%] | 0.15 [3%] | 1.21 [28%] | 0.00 [0%] | 0.00 [0%] | 0.46 [11%] |
| 10–50% | 131 | 3.47 | 2.08 [60%] | 0.12 [3%] | 0.75 [22%] | 0.01 [0%] | 0.10 [3%] | 0.41 [12%] |
| miss<10% | 339 | 3.53 | 2.11 [60%] | 0.11 [3%] | 0.53 [15%] | 0.00 [0%] | 0.32 [9%] | 0.46 [13%] |
| mixed | 10 | 5.19 | 3.29 [63%] | 0.24 [5%] | 0.99 [19%] | 0.08 [1%] | 0.00 [0%] | 0.60 [12%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 65 | 1.20 | 0.07 | 0.13 | 0.00 | 0.00 |
| GPU≥50% | 54 | 1.04 | 0.06 | 0.31 | 0.00 | 0.00 |
| 10–50% | 131 | 0.92 | 0.04 | 0.19 | 0.00 | 0.00 |
| miss<10% | 339 | 1.28 | 0.05 | 0.10 | 0.00 | 0.00 |
| mixed | 10 | 1.26 | 0.07 | 0.07 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 65 | 1.11 | 0.06 | 0.41 | 0.00 | 0.45 |
| GPU≥50% | 54 | 1.40 | 0.09 | 0.90 | 0.00 | 0.46 |
| 10–50% | 131 | 1.05 | 0.07 | 0.56 | 0.00 | 0.40 |
| miss<10% | 339 | 0.83 | 0.06 | 0.43 | 0.00 | 0.46 |
| mixed | 10 | 1.32 | 0.07 | 0.89 | 0.00 | 0.54 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 65 | 0.27 | 0.00 |
| GPU≥50% | 54 | 0.00 | 0.00 |
| 10–50% | 131 | 0.02 | 0.00 |
| miss<10% | 339 | 0.32 | 0.00 |
| mixed | 10 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 65 | 0.52 | 0.01 | 0.13 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 131 | 0.07 | 0.01 | 0.00 | 0.00 | 0.07 | 0.00 |
| miss<10% | 339 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 10 | 0.47 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 574 | 574 / 0 / 0 | 1504 | 1505 | 1065 (523–1269) | 0 (53) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4051 | 4051 / 0 / 0 | 128 | 1596 | 793 (199–1867) | 0 (0) |
| promotion after a load | 341 | 341 / 0 / 0 | 128 | 495 | 91 (42–144) | 0 (0) |

Requests refused at least once: 39 of 599; preemptions: 2; running requests that could not get their next chunk: 4.
Admitted external loads: 93; reservation passed at admission p50 0 / max 696 blocks; free blocks at admission p50 5554.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.261 |
| time with free blocks < 50% of the pool | 0.177 |
| time with free blocks < 25% of the pool | 0.095 |
| time with free blocks < 10% of the pool | 0.033 |
| time with free blocks < 5% of the pool | 0.015 |
| blocks held by loads in transfer, mean / max | 13 / 2080 |
| in-flight prefill reservation after schedule(), mean / max | 119 / 2186 |
| steps whose running requests used the whole token budget (share of time) | 0.205 |
| running requests, mean / max | 1.8 / 12 |
| waiting + kv-holding requests, mean / max | 0.5 / 8 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 65 | 0.37 | 0.31 | 0.75 / 0.38 | 0.29 [41] | 13.48 [24] | 0.71 [62] | 17.88 [3] |
| GPU≥50% | 54 | 0.33 | 0.30 | 0.73 / 0.32 | 0.14 [36] | 8.40 [18] | 0.16 [52] | 29.87 [2] |
| 10–50% | 131 | 0.31 | 0.27 | 0.80 / 0.36 | 0.45 [91] | 5.74 [40] | 0.73 [126] | 13.80 [5] |
| miss<10% | 339 | 0.36 | 0.34 | 0.80 / 0.39 | 2.82 [217] | 10.30 [122] | 4.73 [327] | 27.21 [12] |
| mixed | 10 | 0.40 | 0.40 | 0.78 / 0.52 | 0.30 [6] | 17.15 [4] | 1.87 [10] | – |
