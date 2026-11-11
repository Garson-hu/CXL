## Admission analysis of `e-tool04-80-p7456-priohits` (1159 requests, 83889 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 6179 | 384 | 1.96 / 13.82 | 0.00 / 1.24 | 0.65 / 1.29 | 0.00 / 0.17 | 0.16 / 0.53 | 0.00 / 0.43 | 0.20 / 0.38 |
| GPU≥50% | 591 | 6193 | 288 | 0.36 / 8.03 | 0.00 / 0.81 | 0.03 / 0.81 | 0.00 / 0.00 | 0.46 / 0.48 | 0.00 / 0.90 | 0.20 / 0.30 |
| 10–50% | 123 | 2211 | 96 | 0.78 / 24.31 | 0.00 / 1.34 | 0.08 / 2.55 | 0.00 / 0.07 | 1.56 / 0.86 | 1.93 / 0.97 | 0.41 / 0.67 |
| miss<10% | 339 | 13886 | 128 | 5.49 / 27.82 | 0.00 / 1.79 | 0.04 / 2.08 | 0.00 / 0.32 | 0.01 / 0.01 | 0.00 / 0.00 | 3.08 / 3.92 |
| mixed | 5 | 1546 | 32 | 3.22 / 20.11 | 1.54 / 1.33 | 1.17 / 3.55 | 0.00 / 0.00 | 0.17 / 0.46 | 0.00 / 0.17 | 0.17 / 0.27 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 3.66 | 2.34 [64%] | 0.09 [3%] | 0.29 [8%] | 0.15 [4%] | 0.17 [5%] | 0.62 [17%] | 0.00 [0%] |
| GPU≥50% | 591 | 1.63 | 1.13 [70%] | 0.04 [3%] | 0.01 [1%] | 0.00 [0%] | 0.00 [0%] | 0.43 [26%] | 0.01 [0%] |
| 10–50% | 123 | 4.02 | 2.52 [63%] | 0.18 [5%] | 0.80 [20%] | 0.00 [0%] | 0.07 [2%] | 0.45 [11%] | 0.00 [0%] |
| miss<10% | 339 | 4.19 | 2.58 [62%] | 0.21 [5%] | 0.61 [15%] | 0.00 [0%] | 0.32 [8%] | 0.45 [11%] | 0.02 [0%] |
| mixed | 5 | 5.51 | 2.88 [52%] | 0.14 [3%] | 1.67 [30%] | 0.12 [2%] | 0.00 [0%] | 0.69 [13%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 101 | 1.13 | 0.03 | 0.08 | 0.00 | 0.00 |
| GPU≥50% | 591 | 0.79 | 0.02 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 1.08 | 0.07 | 0.18 | 0.00 | 0.00 |
| miss<10% | 339 | 1.48 | 0.11 | 0.20 | 0.00 | 0.00 |
| mixed | 5 | 1.19 | 0.14 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 0.54 | 0.02 | 0.16 | 0.00 | 0.56 | 0.00 |
| GPU≥50% | 591 | 0.34 | 0.02 | 0.01 | 0.00 | 0.43 | 0.01 |
| 10–50% | 123 | 1.38 | 0.11 | 0.62 | 0.00 | 0.44 | 0.00 |
| miss<10% | 339 | 1.10 | 0.10 | 0.41 | 0.00 | 0.45 | 0.02 |
| mixed | 5 | 1.30 | 0.00 | 1.64 | 0.00 | 0.61 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|
| host≥50% | 101 | 0.00 | 0.00 | 0.17 | 0.00 |
| GPU≥50% | 591 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.07 | 0.00 |
| miss<10% | 339 | 0.00 | 0.00 | 0.32 | 0.00 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 0.41 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 591 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.17 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 604 | 604 / 0 / 0 | 1280 | 1330 | 869 (740–1306) | 0 (116) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3848 | 3848 / 0 / 0 | 128 | 1616 | 703 (177–1909) | 0 (0) |
| promotion after a load | 2 | 2 / 0 / 0 | 59 | 59 | 29 (29–29) | 0 (0) |

Requests refused at least once: 41 of 1159; preemptions: 2; running requests that could not get their next chunk: 4.
Admitted external loads: 114; reservation passed at admission p50 0 / max 158 blocks; free blocks at admission p50 5497.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.266 |
| time with free blocks < 50% of the pool | 0.181 |
| time with free blocks < 25% of the pool | 0.097 |
| time with free blocks < 10% of the pool | 0.036 |
| time with free blocks < 5% of the pool | 0.016 |
| blocks held by loads in transfer, mean / max | 8 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 120 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.204 |
| running requests, mean / max | 2.0 / 16 |
| waiting + kv-holding requests, mean / max | 0.7 / 15 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 0.50 | 0.42 | 0.82 / 0.45 | 0.27 [51] | 5.93 [50] | 1.86 [94] | 5.45 [7] |
| GPU≥50% | 591 | 0.34 | 0.30 | 0.79 / 0.37 | 0.18 [391] | 4.34 [200] | 0.32 [559] | 3.64 [32] |
| 10–50% | 123 | 0.35 | 0.33 | 0.80 / 0.38 | 0.45 [80] | 6.67 [43] | 0.72 [119] | 33.16 [4] |
| miss<10% | 339 | 0.37 | 0.34 | 0.82 / 0.37 | 2.85 [212] | 11.36 [127] | 5.18 [325] | 27.82 [14] |
| mixed | 5 | 0.60 | 0.60 | 0.78 / 0.37 | 0.27 [2] | 5.98 [3] | 3.22 [5] | – |
