## Admission analysis of `e66-tool04-80-p7456-priolen-p1` (1159 requests, 83580 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 75 | 6211 | 384 | 1.04 / 3.90 | 0.00 / 0.00 | 0.29 / 0.33 | 0.00 / 0.43 | 0.17 / 0.41 | 0.00 / 0.00 | 0.26 / 0.37 |
| GPU≥50% | 615 | 6187 | 386 | 0.46 / 4.09 | 0.00 / 0.00 | 0.04 / 0.29 | 0.00 / 0.37 | 0.60 / 0.69 | 0.00 / 0.00 | 0.25 / 0.33 |
| 10–50% | 123 | 2211 | 96 | 0.78 / 7.22 | 0.00 / 0.00 | 0.11 / 0.28 | 0.00 / 0.82 | 0.11 / 0.29 | 0.00 / 0.00 | 0.59 / 0.76 |
| miss<10% | 340 | 13883 | 128 | 5.11 / 27.01 | 0.00 / 0.11 | 0.05 / 0.30 | 0.00 / 3.07 | 0.01 / 0.01 | 0.00 / 0.00 | 3.22 / 4.14 |
| mixed | 6 | 1661 | 32 | 1.61 / 2.55 | 0.00 / 0.00 | 0.35 / 0.30 | 0.00 / 0.00 | 0.49 / 0.31 | 0.00 / 0.00 | 0.27 / 0.33 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 75 | 1.17 | 0.07 [6%] | 0.02 [2%] | 0.06 [5%] | 0.02 [2%] | 0.18 [15%] | 0.24 [20%] | 0.15 [13%] | 0.42 [36%] | 0.01 [1%] | 0.01 [0%] | 0.00 [0%] |
| GPU≥50% | 615 | 0.67 | 0.00 [0%] | 0.02 [3%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.29 [43%] | 0.00 [0%] | 0.35 [53%] | 0.00 [0%] |
| 10–50% | 123 | 1.10 | 0.00 [0%] | 0.01 [1%] | 0.00 [0%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.00 [0%] | 0.28 [25%] | 0.00 [0%] | 0.81 [74%] | 0.00 [0%] |
| miss<10% | 340 | 3.48 | 0.00 [0%] | 0.21 [6%] | 0.50 [14%] | 0.07 [2%] | 0.00 [0%] | 0.66 [19%] | 0.00 [0%] | 0.29 [8%] | 0.00 [0%] | 1.76 [50%] | 0.00 [0%] |
| mixed | 6 | 0.61 | 0.07 [11%] | 0.00 [1%] | 0.01 [1%] | 0.00 [0%] | 0.17 [28%] | 0.00 [0%] | 0.00 [0%] | 0.36 [59%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 75 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 615 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.00 | 0.01 | 0.06 | 0.04 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 75 | 0.00 | 0.00 | 0.00 | 0.00 | 0.33 | 0.00 |
| GPU≥50% | 615 | 0.00 | 0.00 | 0.00 | 0.00 | 0.28 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.00 | 0.28 | 0.00 |
| miss<10% | 340 | 0.01 | 0.01 | 0.00 | 0.00 | 0.29 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.30 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 75 | 0.01 | 0.02 | 0.00 | 0.24 | 0.15 | 0.00 | 0.01 | 0.01 | 0.00 |
| GPU≥50% | 615 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.35 | 0.00 |
| 10–50% | 123 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.81 | 0.00 |
| miss<10% | 340 | 0.19 | 0.43 | 0.03 | 0.66 | 0.00 | 0.00 | 0.00 | 1.76 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 75 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 615 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 368 | 322 / 0 / 46 | 1280 | 1330 | 243 (181–1170) | 0 (1762) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3916 | 3916 / 0 / 0 | 128 | 1979 | 878 (353–1887) | 0 (0) |

Requests refused at least once: 38 of 1159; preemptions: 4; running requests that could not get their next chunk: 16.
Admitted external loads: 92; reservation passed at admission p50 0 / max 1464 blocks; free blocks at admission p50 6078.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.273 |
| time with free blocks < 50% of the pool | 0.192 |
| time with free blocks < 25% of the pool | 0.100 |
| time with free blocks < 10% of the pool | 0.037 |
| time with free blocks < 5% of the pool | 0.016 |
| blocks held by loads in transfer, mean / max | 3 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 138 / 3400 |
| steps whose running requests used the whole token budget (share of time) | 0.094 |
| steps with a shortened token budget (share of time) | 0.083 |
| running requests, mean / max | 2.1 / 15 |
| waiting + kv-holding requests, mean / max | 0.4 / 7 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 75 | 0.49 | 0.00 | 0.81 / 0.26 | 0.25 [38] | 2.08 [37] | 0.88 [68] | 2.26 [7] |
| GPU≥50% | 615 | 0.43 | 0.00 | 0.79 / 0.38 | 0.16 [350] | 1.54 [265] | 0.40 [596] | 1.83 [19] |
| 10–50% | 123 | 0.42 | 0.00 | 0.79 / 0.42 | 0.41 [71] | 3.36 [52] | 0.78 [120] | 5.03 [3] |
| miss<10% | 340 | 0.43 | 0.00 | 0.82 / 0.40 | 2.72 [194] | 9.78 [146] | 5.08 [330] | 12.42 [10] |
| mixed | 6 | 0.33 | 0.00 | 0.83 / 0.19 | 0.28 [4] | 2.55 [2] | 0.28 [5] | 1.61 [1] |
