## Admission analysis of `e66-tool04-80-p7456-priolen` (1159 requests, 83414 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 96 | 6178 | 384 | 2.04 / 15.88 | 0.00 / 1.22 | 0.69 / 1.66 | 0.00 / 0.30 | 0.18 / 0.54 | 0.00 / 0.46 | 0.19 / 0.37 |
| GPU≥50% | 594 | 6194 | 281 | 0.35 / 8.01 | 0.00 / 0.78 | 0.03 / 0.81 | 0.00 / 0.00 | 0.19 / 0.49 | 0.00 / 0.00 | 0.21 / 0.31 |
| 10–50% | 123 | 2211 | 96 | 0.77 / 9.05 | 0.00 / 0.75 | 0.08 / 0.79 | 0.00 / 0.00 | 1.16 / 0.76 | 1.92 / 1.07 | 0.38 / 0.60 |
| miss<10% | 341 | 13883 | 128 | 5.14 / 22.27 | 0.00 / 1.18 | 0.04 / 1.78 | 0.00 / 0.41 | 0.01 / 0.01 | 0.00 / 0.00 | 3.04 / 3.90 |
| mixed | 5 | 1546 | 32 | 3.19 / 13.28 | 1.53 / 1.41 | 1.16 / 2.19 | 0.00 / 0.00 | 0.16 / 0.42 | 0.00 / 0.17 | 0.17 / 0.27 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 96 | 4.17 | 2.85 [68%] | 0.09 [2%] | 0.17 [4%] | 0.14 [3%] | 0.24 [6%] | 0.68 [16%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 594 | 1.59 | 1.11 [69%] | 0.05 [3%] | 0.01 [0%] | 0.00 [0%] | 0.00 [0%] | 0.42 [27%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 123 | 1.60 | 1.13 [70%] | 0.01 [1%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.46 [29%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 341 | 3.36 | 2.13 [63%] | 0.15 [5%] | 0.29 [9%] | 0.00 [0%] | 0.31 [9%] | 0.46 [14%] | 0.00 [0%] | 0.02 [1%] |
| mixed | 5 | 4.20 | 3.22 [77%] | 0.00 [0%] | 0.05 [1%] | 0.05 [1%] | 0.00 [0%] | 0.89 [21%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 96 | 1.21 | 0.01 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 594 | 0.76 | 0.01 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.75 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 341 | 1.12 | 0.04 | 0.02 | 0.00 | 0.00 |
| mixed | 5 | 1.41 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 96 | 0.91 | 0.05 | 0.11 | 0.00 | 0.59 | 0.00 |
| GPU≥50% | 594 | 0.34 | 0.03 | 0.01 | 0.00 | 0.42 | 0.01 |
| 10–50% | 123 | 0.32 | 0.01 | 0.00 | 0.00 | 0.45 | 0.00 |
| miss<10% | 341 | 0.96 | 0.11 | 0.23 | 0.00 | 0.46 | 0.01 |
| mixed | 5 | 1.41 | 0.00 | 0.00 | 0.00 | 0.79 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 96 | 0.03 | 0.00 | 0.03 | 0.24 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 594 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 341 | 0.05 | 0.01 | 0.04 | 0.31 | 0.00 | 0.00 | 0.01 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 96 | 0.45 | 0.01 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 594 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 341 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.17 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 743 | 743 / 0 / 0 | 1280 | 1330 | 204 (93–348) | 0 (48) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3460 | 3460 / 0 / 0 | 128 | 1700 | 977 (283–1904) | 0 (0) |

Requests refused at least once: 44 of 1159; preemptions: 3; running requests that could not get their next chunk: 8.
Admitted external loads: 109; reservation passed at admission p50 0 / max 178 blocks; free blocks at admission p50 5492.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.270 |
| time with free blocks < 50% of the pool | 0.183 |
| time with free blocks < 25% of the pool | 0.099 |
| time with free blocks < 10% of the pool | 0.042 |
| time with free blocks < 5% of the pool | 0.021 |
| blocks held by loads in transfer, mean / max | 6 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 122 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.205 |
| running requests, mean / max | 2.0 / 16 |
| waiting + kv-holding requests, mean / max | 0.5 / 15 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 96 | 0.50 | 0.44 | 0.82 / 0.45 | 0.28 [48] | 6.34 [48] | 2.01 [90] | 5.91 [6] |
| GPU≥50% | 594 | 0.35 | 0.30 | 0.79 / 0.36 | 0.18 [389] | 4.27 [205] | 0.31 [563] | 3.83 [31] |
| 10–50% | 123 | 0.36 | 0.32 | 0.80 / 0.41 | 0.42 [79] | 3.99 [44] | 0.77 [121] | 3.99 [2] |
| miss<10% | 341 | 0.36 | 0.32 | 0.83 / 0.41 | 2.82 [217] | 9.97 [124] | 5.01 [330] | 8.46 [11] |
| mixed | 5 | 0.60 | 0.60 | 0.78 / 0.37 | 0.28 [2] | 5.93 [3] | 3.19 [5] | – |
