## Admission analysis of `e-tool04-80-p7456-priolen` (1159 requests, 83165 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 6178 | 384 | 2.10 / 15.96 | 0.00 / 1.28 | 0.71 / 1.71 | 0.00 / 0.29 | 0.19 / 0.55 | 0.00 / 0.45 | 0.19 / 0.37 |
| GPU≥50% | 592 | 6194 | 281 | 0.36 / 8.08 | 0.00 / 0.79 | 0.03 / 0.80 | 0.00 / 0.00 | 0.19 / 0.10 | 0.00 / 0.00 | 0.20 / 0.31 |
| 10–50% | 123 | 2211 | 96 | 0.78 / 9.11 | 0.00 / 0.75 | 0.08 / 0.85 | 0.00 / 0.02 | 1.17 / 0.76 | 1.93 / 1.07 | 0.39 / 0.59 |
| miss<10% | 341 | 13883 | 128 | 5.17 / 22.45 | 0.00 / 1.20 | 0.04 / 1.79 | 0.00 / 0.40 | 0.01 / 0.01 | 0.00 / 0.00 | 3.08 / 3.92 |
| mixed | 5 | 1546 | 32 | 3.21 / 13.36 | 1.54 / 1.42 | 1.17 / 2.20 | 0.00 / 0.00 | 0.17 / 0.42 | 0.00 / 0.17 | 0.17 / 0.27 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 4.28 | 2.93 [69%] | 0.10 [2%] | 0.18 [4%] | 0.14 [3%] | 0.24 [6%] | 0.69 [16%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 592 | 1.60 | 1.11 [70%] | 0.04 [3%] | 0.01 [0%] | 0.00 [0%] | 0.00 [0%] | 0.43 [27%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 123 | 1.68 | 1.18 [70%] | 0.01 [1%] | 0.01 [1%] | 0.00 [0%] | 0.02 [1%] | 0.46 [27%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 341 | 3.39 | 2.16 [64%] | 0.15 [4%] | 0.29 [8%] | 0.00 [0%] | 0.31 [9%] | 0.46 [14%] | 0.00 [0%] | 0.02 [1%] |
| mixed | 5 | 4.22 | 3.23 [77%] | 0.00 [0%] | 0.05 [1%] | 0.05 [1%] | 0.00 [0%] | 0.89 [21%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 98 | 1.26 | 0.02 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 592 | 0.78 | 0.01 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.75 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 341 | 1.15 | 0.04 | 0.02 | 0.00 | 0.00 |
| mixed | 5 | 1.42 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 0.96 | 0.05 | 0.11 | 0.00 | 0.60 | 0.00 |
| GPU≥50% | 592 | 0.33 | 0.03 | 0.01 | 0.00 | 0.43 | 0.01 |
| 10–50% | 123 | 0.38 | 0.01 | 0.01 | 0.00 | 0.46 | 0.00 |
| miss<10% | 341 | 0.97 | 0.11 | 0.24 | 0.00 | 0.46 | 0.01 |
| mixed | 5 | 1.41 | 0.00 | 0.00 | 0.00 | 0.79 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 0.03 | 0.00 | 0.02 | 0.24 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 592 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 |
| miss<10% | 341 | 0.04 | 0.01 | 0.03 | 0.31 | 0.00 | 0.00 | 0.01 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 98 | 0.44 | 0.01 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 592 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 341 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.17 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 707 | 707 / 0 / 0 | 1280 | 1330 | 196 (89–346) | 0 (48) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3497 | 3497 / 0 / 0 | 128 | 1700 | 973 (278–1904) | 0 (0) |

Requests refused at least once: 44 of 1159; preemptions: 3; running requests that could not get their next chunk: 8.
Admitted external loads: 110; reservation passed at admission p50 0 / max 178 blocks; free blocks at admission p50 5492.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.271 |
| time with free blocks < 50% of the pool | 0.184 |
| time with free blocks < 25% of the pool | 0.100 |
| time with free blocks < 10% of the pool | 0.043 |
| time with free blocks < 5% of the pool | 0.021 |
| blocks held by loads in transfer, mean / max | 6 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 122 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.207 |
| running requests, mean / max | 2.1 / 16 |
| waiting + kv-holding requests, mean / max | 0.6 / 15 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 0.51 | 0.44 | 0.82 / 0.41 | 0.29 [48] | 6.39 [50] | 2.04 [92] | 5.96 [6] |
| GPU≥50% | 592 | 0.35 | 0.31 | 0.79 / 0.36 | 0.18 [386] | 4.30 [206] | 0.31 [561] | 3.90 [31] |
| 10–50% | 123 | 0.36 | 0.32 | 0.80 / 0.41 | 0.42 [79] | 4.10 [44] | 0.78 [121] | 4.12 [2] |
| miss<10% | 341 | 0.37 | 0.33 | 0.82 / 0.41 | 2.84 [216] | 9.90 [125] | 5.06 [330] | 8.62 [11] |
| mixed | 5 | 0.60 | 0.60 | 0.78 / 0.37 | 0.27 [2] | 5.99 [3] | 3.21 [5] | – |
