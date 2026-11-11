## Admission analysis of `e-tool04-80-p7456-priolen-p1` (1159 requests, 83315 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 77 | 6201 | 384 | 1.25 / 6.36 | 0.00 / 0.06 | 0.30 / 0.31 | 0.00 / 0.52 | 0.19 / 0.40 | 0.00 / 0.00 | 0.20 / 0.38 |
| GPU≥50% | 613 | 6188 | 386 | 0.46 / 4.01 | 0.00 / 0.00 | 0.04 / 0.29 | 0.00 / 0.38 | 0.47 / 0.36 | 0.00 / 0.00 | 0.25 / 0.33 |
| 10–50% | 123 | 2211 | 96 | 0.79 / 7.81 | 0.00 / 0.00 | 0.11 / 0.28 | 0.00 / 0.86 | 0.11 / 0.29 | 0.00 / 0.00 | 0.60 / 0.75 |
| miss<10% | 340 | 13883 | 128 | 5.13 / 27.08 | 0.00 / 0.13 | 0.05 / 0.29 | 0.00 / 3.08 | 0.01 / 0.01 | 0.00 / 0.00 | 3.24 / 4.15 |
| mixed | 6 | 1661 | 32 | 0.93 / 2.59 | 0.00 / 0.00 | 0.32 / 0.29 | 0.00 / 0.00 | 0.41 / 0.30 | 0.00 / 0.00 | 0.20 / 0.25 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 77 | 1.30 | 0.07 [6%] | 0.02 [2%] | 0.17 [13%] | 0.02 [1%] | 0.17 [13%] | 0.26 [20%] | 0.14 [11%] | 0.41 [31%] | 0.02 [2%] | 0.01 [1%] | 0.00 [0%] |
| GPU≥50% | 613 | 0.67 | 0.00 [0%] | 0.02 [3%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.29 [43%] | 0.00 [0%] | 0.36 [54%] | 0.00 [0%] |
| 10–50% | 123 | 1.15 | 0.00 [0%] | 0.01 [1%] | 0.00 [0%] | 0.00 [0%] | 0.01 [0%] | 0.01 [1%] | 0.00 [0%] | 0.29 [25%] | 0.00 [0%] | 0.84 [73%] | 0.00 [0%] |
| miss<10% | 340 | 3.50 | 0.00 [0%] | 0.20 [6%] | 0.52 [15%] | 0.07 [2%] | 0.00 [0%] | 0.66 [19%] | 0.00 [0%] | 0.28 [8%] | 0.00 [0%] | 1.77 [51%] | 0.00 [0%] |
| mixed | 6 | 0.59 | 0.07 [12%] | 0.00 [0%] | 0.04 [6%] | 0.00 [0%] | 0.10 [18%] | 0.00 [0%] | 0.00 [0%] | 0.38 [64%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 77 | 0.00 | 0.01 | 0.05 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 613 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.00 | 0.01 | 0.08 | 0.04 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 77 | 0.00 | 0.00 | 0.00 | 0.00 | 0.31 | 0.00 |
| GPU≥50% | 613 | 0.00 | 0.00 | 0.00 | 0.00 | 0.28 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.00 | 0.28 | 0.00 |
| miss<10% | 340 | 0.00 | 0.00 | 0.00 | 0.00 | 0.28 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.29 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 77 | 0.00 | 0.08 | 0.00 | 0.26 | 0.14 | 0.00 | 0.02 | 0.01 | 0.00 |
| GPU≥50% | 613 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.36 | 0.00 |
| 10–50% | 123 | 0.01 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.84 | 0.00 |
| miss<10% | 340 | 0.19 | 0.44 | 0.03 | 0.66 | 0.00 | 0.00 | 0.00 | 1.77 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 77 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 613 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 373 | 327 / 0 / 46 | 1280 | 1330 | 244 (181–1134) | 0 (1762) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3912 | 3912 / 0 / 0 | 128 | 1979 | 881 (355–1892) | 0 (0) |

Requests refused at least once: 40 of 1159; preemptions: 4; running requests that could not get their next chunk: 18.
Admitted external loads: 92; reservation passed at admission p50 0 / max 1464 blocks; free blocks at admission p50 6078.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.274 |
| time with free blocks < 50% of the pool | 0.193 |
| time with free blocks < 25% of the pool | 0.100 |
| time with free blocks < 10% of the pool | 0.037 |
| time with free blocks < 5% of the pool | 0.016 |
| blocks held by loads in transfer, mean / max | 3 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 138 / 3400 |
| steps whose running requests used the whole token budget (share of time) | 0.094 |
| steps with a shortened token budget (share of time) | 0.083 |
| running requests, mean / max | 2.1 / 15 |
| waiting + kv-holding requests, mean / max | 0.4 / 8 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 77 | 0.51 | 0.00 | 0.81 / 0.19 | 0.26 [38] | 2.17 [39] | 0.90 [68] | 2.64 [9] |
| GPU≥50% | 613 | 0.43 | 0.00 | 0.79 / 0.38 | 0.16 [347] | 1.52 [266] | 0.43 [600] | 1.82 [13] |
| 10–50% | 123 | 0.42 | 0.00 | 0.79 / 0.39 | 0.41 [71] | 3.37 [52] | 0.77 [119] | 5.08 [4] |
| miss<10% | 340 | 0.44 | 0.00 | 0.82 / 0.40 | 2.70 [191] | 9.56 [149] | 5.12 [333] | 16.50 [7] |
| mixed | 6 | 0.50 | 0.00 | 0.83 / 0.13 | 0.25 [3] | 1.71 [3] | 0.27 [5] | 0.93 [1] |
