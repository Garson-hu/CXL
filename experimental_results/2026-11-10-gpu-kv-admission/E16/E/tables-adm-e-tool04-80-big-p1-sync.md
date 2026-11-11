## Admission analysis of `e-tool04-80-big-p1-sync` (1159 requests, 77836 engine steps, pool 19916 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 9553 | 544 | 1.00 / 2.26 | 0.00 / 0.00 | 0.22 / 0.20 | 0.00 / 0.00 | 0.24 / 0.31 | 0.00 / 0.00 | 0.18 / 0.32 |
| GPU≥50% | 662 | 6180 | 386 | 0.52 / 8.32 | 0.00 / 0.01 | 0.09 / 0.19 | 0.00 / 1.06 | 0.23 / 0.20 | 0.00 / 0.00 | 0.19 / 0.24 |
| 10–50% | 124 | 2214 | 96 | 0.79 / 19.76 | 0.00 / 0.01 | 0.23 / 0.19 | 0.00 / 3.24 | 0.34 / 0.29 | 0.00 / 0.00 | 0.39 / 0.65 |
| miss<10% | 339 | 13742 | 128 | 6.04 / 24.19 | 0.00 / 0.01 | 0.05 / 0.18 | 0.00 / 3.78 | 0.00 / 0.00 | 0.00 / 0.00 | 3.19 / 4.14 |
| mixed | 4 | 1546 | 32 | 1.01 / 1.44 | 0.00 / 0.00 | 0.30 / 0.23 | 0.00 / 0.00 | 0.30 / 0.25 | 0.00 / 0.00 | 0.40 / 0.29 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 0.51 | 0.03 [7%] | 0.07 [14%] | 0.13 [25%] | 0.28 [55%] | 0.00 [0%] |
| GPU≥50% | 662 | 1.26 | 0.00 [0%] | 0.10 [8%] | 0.00 [0%] | 0.17 [14%] | 0.99 [78%] |
| 10–50% | 124 | 3.46 | 0.00 [0%] | 0.24 [7%] | 0.01 [0%] | 0.18 [5%] | 3.03 [88%] |
| miss<10% | 339 | 3.97 | 0.00 [0%] | 0.26 [7%] | 0.00 [0%] | 0.17 [4%] | 3.54 [89%] |
| mixed | 4 | 0.48 | 0.03 [7%] | 0.00 [0%] | 0.09 [19%] | 0.36 [74%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 30 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 662 | 0.00 | 0.01 | 0.00 | 0.00 |
| 10–50% | 124 | 0.00 | 0.01 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.01 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok |
|---|---|---|---|---|
| host≥50% | 30 | 0.03 | 0.18 | 0.00 |
| GPU≥50% | 662 | 0.01 | 0.17 | 0.00 |
| 10–50% | 124 | 0.02 | 0.17 | 0.00 |
| miss<10% | 339 | 0.02 | 0.17 | 0.00 |
| mixed | 4 | 0.00 | 0.23 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok |
|---|---|---|---|---|
| host≥50% | 30 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 662 | 0.07 | 0.00 | 0.99 |
| 10–50% | 124 | 0.21 | 0.00 | 3.03 |
| miss<10% | 339 | 0.24 | 0.00 | 3.54 |
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
Admitted external loads: 42; reservation passed at admission p50 48 / max 1652 blocks; free blocks at admission p50 18390.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.111 |
| time with free blocks < 50% of the pool | 0.018 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 2 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 155 / 1912 |
| steps whose running requests used the whole token budget (share of time) | 0.070 |
| steps with a shortened token budget (share of time) | 0.063 |
| running requests, mean / max | 2.3 / 16 |
| waiting + kv-holding requests, mean / max | 0.5 / 9 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 30 | 0.50 | 0.00 | 0.93 / 0.81 | 0.25 [15] | 1.68 [15] | 1.00 [30] | – |
| GPU≥50% | 662 | 0.47 | 0.00 | 0.92 / 0.77 | 0.16 [353] | 1.21 [309] | 0.52 [662] | – |
| 10–50% | 124 | 0.48 | 0.00 | 0.92 / 0.77 | 0.38 [65] | 6.64 [59] | 0.79 [124] | – |
| miss<10% | 339 | 0.46 | 0.00 | 0.94 / 0.79 | 2.73 [183] | 11.89 [156] | 6.04 [339] | – |
| mixed | 4 | 0.75 | 0.00 | 0.95 / 0.69 | 0.19 [1] | 1.01 [3] | 1.01 [4] | – |
