## Admission analysis of `e-tool04-80-big-p1` (1159 requests, 81511 engine steps, pool 19916 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 9553 | 544 | 1.38 / 2.98 | 0.00 / 0.05 | 0.28 / 0.29 | 0.00 / 0.00 | 0.44 / 0.45 | 0.00 / 0.00 | 0.31 / 0.40 |
| GPU≥50% | 662 | 6180 | 386 | 0.50 / 7.65 | 0.00 / 0.02 | 0.09 / 0.29 | 0.00 / 0.92 | 0.47 / 0.40 | 0.00 / 0.00 | 0.25 / 0.35 |
| 10–50% | 124 | 2214 | 101 | 0.80 / 19.46 | 0.00 / 0.01 | 0.19 / 0.29 | 0.00 / 2.93 | 0.70 / 0.51 | 0.00 / 0.00 | 0.58 / 0.82 |
| miss<10% | 339 | 13742 | 128 | 5.67 / 23.94 | 0.00 / 0.02 | 0.03 / 0.29 | 0.00 / 3.39 | 0.01 / 0.01 | 0.00 / 0.00 | 3.33 / 4.24 |
| mixed | 4 | 1546 | 32 | 2.59 / 2.72 | 0.00 / 0.00 | 0.72 / 0.53 | 0.00 / 0.00 | 0.66 / 0.52 | 0.00 / 0.00 | 0.60 / 0.44 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 0.79 | 0.09 [11%] | 0.08 [10%] | 0.24 [30%] | 0.38 [49%] | 0.00 [0%] |
| GPU≥50% | 662 | 1.22 | 0.00 [0%] | 0.09 [8%] | 0.00 [0%] | 0.28 [23%] | 0.85 [69%] |
| 10–50% | 124 | 3.25 | 0.00 [0%] | 0.24 [7%] | 0.01 [0%] | 0.29 [9%] | 2.71 [83%] |
| miss<10% | 339 | 3.69 | 0.00 [0%] | 0.25 [7%] | 0.00 [0%] | 0.29 [8%] | 3.16 [85%] |
| mixed | 4 | 1.05 | 0.10 [10%] | 0.00 [0%] | 0.29 [27%] | 0.66 [63%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 30 | 0.00 | 0.05 | 0.00 | 0.00 |
| GPU≥50% | 662 | 0.00 | 0.02 | 0.00 | 0.00 |
| 10–50% | 124 | 0.00 | 0.01 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.02 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok |
|---|---|---|---|---|
| host≥50% | 30 | 0.01 | 0.28 | 0.00 |
| GPU≥50% | 662 | 0.01 | 0.28 | 0.00 |
| 10–50% | 124 | 0.00 | 0.29 | 0.00 |
| miss<10% | 339 | 0.00 | 0.29 | 0.00 |
| mixed | 4 | 0.00 | 0.53 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok |
|---|---|---|---|---|
| host≥50% | 30 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 662 | 0.07 | 0.00 | 0.85 |
| 10–50% | 124 | 0.23 | 0.00 | 2.71 |
| miss<10% | 339 | 0.23 | 0.00 | 3.16 |
| mixed | 4 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 30 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 662 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 124 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 1159; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 42; reservation passed at admission p50 34 / max 1496 blocks; free blocks at admission p50 18539.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.110 |
| time with free blocks < 50% of the pool | 0.018 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 3 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 141 / 1921 |
| steps whose running requests used the whole token budget (share of time) | 0.069 |
| steps with a shortened token budget (share of time) | 0.084 |
| running requests, mean / max | 2.2 / 16 |
| waiting + kv-holding requests, mean / max | 0.5 / 9 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 0.50 | 0.00 | 0.93 / 0.81 | 0.27 [15] | 2.51 [15] | 1.38 [30] | – |
| GPU≥50% | 662 | 0.44 | 0.00 | 0.92 / 0.77 | 0.16 [371] | 1.60 [291] | 0.50 [662] | – |
| 10–50% | 124 | 0.42 | 0.00 | 0.92 / 0.77 | 0.41 [72] | 7.38 [52] | 0.80 [124] | – |
| miss<10% | 339 | 0.44 | 0.00 | 0.93 / 0.79 | 2.69 [191] | 12.00 [148] | 5.67 [339] | – |
| mixed | 4 | 0.75 | 0.00 | 0.94 / 0.69 | 0.23 [1] | 2.59 [3] | 2.59 [4] | – |
