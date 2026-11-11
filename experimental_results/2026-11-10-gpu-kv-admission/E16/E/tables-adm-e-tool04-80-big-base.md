## Admission analysis of `e-tool04-80-big-base` (1159 requests, 81022 engine steps, pool 19916 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 9553 | 544 | 1.96 / 31.10 | 0.00 / 1.80 | 0.62 / 3.15 | 0.00 / 0.00 | 0.17 / 0.68 | 0.00 / 1.07 | 0.26 / 0.55 |
| GPU≥50% | 661 | 6180 | 255 | 0.42 / 14.69 | 0.00 / 1.41 | 0.04 / 1.55 | 0.00 / 0.00 | 0.96 / 0.94 | 0.00 / 0.90 | 0.21 / 0.37 |
| 10–50% | 124 | 2214 | 96 | 0.79 / 18.22 | 0.00 / 1.17 | 0.18 / 2.24 | 0.00 / 0.00 | 1.00 / 0.72 | 0.00 / 0.49 | 0.44 / 0.74 |
| miss<10% | 340 | 13742 | 128 | 5.34 / 21.34 | 0.00 / 1.55 | 0.03 / 1.62 | 0.00 / 0.00 | 0.01 / 0.01 | 0.00 / 0.00 | 3.08 / 3.95 |
| mixed | 4 | 1546 | 32 | 11.18 / 17.00 | 1.83 / 3.78 | 1.17 / 1.18 | 0.00 / 0.00 | 1.49 / 0.89 | 1.06 / 1.30 | 0.80 / 0.51 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 6.71 | 5.40 [81%] | 0.41 [6%] | 0.22 [3%] | 0.68 [10%] | 0.00 [0%] |
| GPU≥50% | 661 | 2.97 | 2.25 [76%] | 0.25 [8%] | 0.00 [0%] | 0.44 [15%] | 0.02 [1%] |
| 10–50% | 124 | 3.46 | 2.71 [78%] | 0.27 [8%] | 0.01 [0%] | 0.46 [13%] | 0.00 [0%] |
| miss<10% | 340 | 3.17 | 2.46 [78%] | 0.25 [8%] | 0.00 [0%] | 0.45 [14%] | 0.01 [0%] |
| mixed | 4 | 7.15 | 5.55 [78%] | 0.47 [7%] | 0.22 [3%] | 0.92 [13%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 30 | 1.69 | 0.12 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 661 | 1.29 | 0.11 | 0.00 | 0.00 | 0.00 |
| 10–50% | 124 | 1.09 | 0.09 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 1.43 | 0.12 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 3.41 | 0.37 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 30 | 2.37 | 0.25 | 0.53 | 0.00 |
| GPU≥50% | 661 | 0.95 | 0.14 | 0.44 | 0.02 |
| 10–50% | 124 | 1.60 | 0.19 | 0.46 | 0.00 |
| miss<10% | 340 | 1.03 | 0.13 | 0.45 | 0.01 |
| mixed | 4 | 0.39 | 0.00 | 0.79 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 30 | 0.00 |
| GPU≥50% | 661 | 0.00 |
| 10–50% | 124 | 0.00 |
| miss<10% | 340 | 0.00 |
| mixed | 4 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 30 | 1.07 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 661 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 124 | 0.02 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 1.30 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 1159; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 42; reservation passed at admission p50 0 / max 1092 blocks; free blocks at admission p50 18090.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.108 |
| time with free blocks < 50% of the pool | 0.017 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 9 / 2464 |
| in-flight prefill reservation after schedule(), mean / max | 123 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.205 |
| running requests, mean / max | 2.1 / 16 |
| waiting + kv-holding requests, mean / max | 0.7 / 18 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 0.43 | 0.37 | 0.93 / 0.80 | 0.29 [17] | 15.76 [13] | 1.96 [30] | – |
| GPU≥50% | 661 | 0.36 | 0.33 | 0.93 / 0.78 | 0.18 [426] | 6.50 [235] | 0.42 [661] | – |
| 10–50% | 124 | 0.36 | 0.32 | 0.93 / 0.78 | 0.42 [79] | 7.36 [45] | 0.79 [124] | – |
| miss<10% | 340 | 0.37 | 0.33 | 0.94 / 0.79 | 2.83 [213] | 11.02 [127] | 5.34 [340] | – |
| mixed | 4 | 0.75 | 0.75 | 0.94 / 0.78 | 0.21 [1] | 11.18 [3] | 11.18 [4] | – |
