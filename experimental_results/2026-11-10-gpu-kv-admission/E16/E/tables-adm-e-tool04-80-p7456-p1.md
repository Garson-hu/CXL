## Admission analysis of `e-tool04-80-p7456-p1` (1159 requests, 84001 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 88 | 6308 | 384 | 1.64 / 25.63 | 0.00 / 0.58 | 0.35 / 0.59 | 0.00 / 2.61 | 0.44 / 0.46 | 0.00 / 0.00 | 0.30 / 0.43 |
| GPU≥50% | 602 | 6187 | 386 | 0.43 / 5.98 | 0.00 / 0.11 | 0.03 / 0.32 | 0.00 / 0.54 | 0.64 / 0.71 | 0.00 / 0.00 | 0.25 / 0.33 |
| 10–50% | 123 | 2211 | 101 | 0.80 / 24.01 | 0.00 / 0.13 | 0.17 / 0.29 | 0.00 / 3.47 | 0.11 / 0.29 | 0.00 / 0.00 | 0.58 / 0.71 |
| miss<10% | 340 | 13883 | 128 | 5.72 / 29.86 | 0.00 / 0.13 | 0.05 / 0.33 | 0.00 / 3.99 | 0.01 / 0.01 | 0.00 / 0.00 | 3.29 / 4.20 |
| mixed | 6 | 1661 | 32 | 1.99 / 10.50 | 0.00 / 0.77 | 0.61 / 0.47 | 0.00 / 0.32 | 0.66 / 0.60 | 0.00 / 0.00 | 0.60 / 0.53 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 88 | 4.25 | 0.05 [1%] | 0.17 [4%] | 1.81 [43%] | 0.15 [3%] | 0.25 [6%] | 0.29 [7%] | 0.19 [4%] | 0.48 [11%] | 0.01 [0%] | 0.86 [20%] | 0.00 [0%] |
| GPU≥50% | 602 | 0.98 | 0.00 [0%] | 0.05 [5%] | 0.16 [17%] | 0.01 [1%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.27 [28%] | 0.00 [0%] | 0.47 [48%] | 0.00 [0%] |
| 10–50% | 123 | 3.90 | 0.00 [0%] | 0.16 [4%] | 1.19 [31%] | 0.01 [0%] | 0.01 [0%] | 0.05 [1%] | 0.00 [0%] | 0.29 [7%] | 0.00 [0%] | 2.21 [57%] | 0.00 [0%] |
| miss<10% | 340 | 4.46 | 0.00 [0%] | 0.19 [4%] | 0.94 [21%] | 0.05 [1%] | 0.00 [0%] | 0.60 [13%] | 0.00 [0%] | 0.29 [6%] | 0.00 [0%] | 2.38 [54%] | 0.00 [0%] |
| mixed | 6 | 2.15 | 0.07 [3%] | 0.00 [0%] | 0.76 [35%] | 0.00 [0%] | 0.35 [16%] | 0.00 [0%] | 0.00 [0%] | 0.64 [30%] | 0.00 [0%] | 0.32 [15%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 88 | 0.00 | 0.04 | 0.48 | 0.07 | 0.00 | 0.00 |
| GPU≥50% | 602 | 0.00 | 0.01 | 0.08 | 0.01 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.01 | 0.12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.00 | 0.01 | 0.10 | 0.02 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.76 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 88 | 0.02 | 0.20 | 0.00 | 0.00 | 0.37 | 0.00 |
| GPU≥50% | 602 | 0.01 | 0.04 | 0.00 | 0.00 | 0.27 | 0.00 |
| 10–50% | 123 | 0.01 | 0.00 | 0.00 | 0.00 | 0.28 | 0.00 |
| miss<10% | 340 | 0.01 | 0.04 | 0.00 | 0.00 | 0.29 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.47 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 88 | 0.11 | 1.09 | 0.07 | 0.29 | 0.19 | 0.00 | 0.01 | 0.86 | 0.00 |
| GPU≥50% | 602 | 0.02 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.47 | 0.00 |
| 10–50% | 123 | 0.14 | 1.07 | 0.01 | 0.05 | 0.00 | 0.00 | 0.00 | 2.21 | 0.00 |
| miss<10% | 340 | 0.17 | 0.80 | 0.04 | 0.60 | 0.00 | 0.00 | 0.00 | 2.38 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.32 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 88 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 602 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 557 | 522 / 0 / 35 | 384 | 456 | 242 (75–365) | 0 (1728) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4256 | 4256 / 0 / 0 | 128 | 1650 | 751 (185–1870) | 0 (0) |

Requests refused at least once: 51 of 1159; preemptions: 3; running requests that could not get their next chunk: 7.
Admitted external loads: 106; reservation passed at admission p50 34 / max 1770 blocks; free blocks at admission p50 5520.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.270 |
| time with free blocks < 50% of the pool | 0.188 |
| time with free blocks < 25% of the pool | 0.097 |
| time with free blocks < 10% of the pool | 0.037 |
| time with free blocks < 5% of the pool | 0.017 |
| blocks held by loads in transfer, mean / max | 4 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 138 / 1924 |
| steps whose running requests used the whole token budget (share of time) | 0.072 |
| steps with a shortened token budget (share of time) | 0.087 |
| running requests, mean / max | 2.0 / 13 |
| waiting + kv-holding requests, mean / max | 0.6 / 9 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 88 | 0.55 | 0.00 | 0.74 / 0.18 | 0.27 [40] | 2.84 [48] | 1.53 [74] | 11.37 [14] |
| GPU≥50% | 602 | 0.43 | 0.00 | 0.79 / 0.43 | 0.16 [346] | 1.54 [256] | 0.40 [593] | 1.94 [9] |
| 10–50% | 123 | 0.41 | 0.00 | 0.79 / 0.40 | 0.41 [72] | 7.21 [51] | 0.78 [120] | 34.35 [3] |
| miss<10% | 340 | 0.44 | 0.00 | 0.82 / 0.40 | 2.72 [191] | 12.23 [149] | 5.67 [330] | 18.69 [10] |
| mixed | 6 | 0.67 | 0.00 | 0.78 / 0.21 | 0.27 [2] | 2.59 [4] | 1.71 [4] | 10.50 [2] |
