## Admission analysis of `tool08-320-tokfast11` (544 requests, 21151 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 93 | 6178 | 384 | 4.39 / 27.67 | 0.00 / 1.35 | 0.56 / 2.11 | 0.00 / 3.83 | 0.97 / 0.95 | 0.00 / 0.01 | 0.70 / 0.80 |
| GPU≥50% | 220 | 6221 | 56 | 1.53 / 13.22 | 0.00 / 0.64 | 0.44 / 0.71 | 0.17 / 1.29 | 1.21 / 1.15 | 0.00 / 0.00 | 0.49 / 0.56 |
| 10–50% | 64 | 2103 | 94 | 6.40 / 57.95 | 0.00 / 0.70 | 0.48 / 1.01 | 1.99 / 11.83 | 0.93 / 0.77 | 0.00 / 0.73 | 0.76 / 1.10 |
| miss<10% | 164 | 13883 | 128 | 18.42 / 56.63 | 0.00 / 0.49 | 0.41 / 1.01 | 11.60 / 16.85 | 1.21 / 1.21 | 1.43 / 1.43 | 3.75 / 4.88 |
| mixed | 3 | 4348 | 160 | 8.84 / 14.12 | 1.21 / 1.96 | 0.79 / 0.71 | 5.18 / 4.61 | 1.54 / 1.54 | 0.00 / 0.00 | 1.73 / 1.42 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 93 | 8.25 | 0.03 [0%] | 0.25 [3%] | 3.81 [46%] | 0.56 [7%] | 0.44 [5%] | 0.60 [7%] | 0.35 [4%] | 0.80 [10%] | 1.40 [17%] | 0.01 [0%] | 0.01 [0%] |
| GPU≥50% | 220 | 2.74 | 0.00 [0%] | 0.10 [4%] | 1.09 [40%] | 0.10 [4%] | 0.06 [2%] | 0.02 [1%] | 0.03 [1%] | 0.46 [17%] | 0.85 [31%] | 0.00 [0%] | 0.02 [1%] |
| 10–50% | 64 | 13.63 | 0.05 [0%] | 0.46 [3%] | 4.35 [32%] | 0.17 [1%] | 0.03 [0%] | 0.17 [1%] | 0.00 [0%] | 0.46 [3%] | 7.79 [57%] | 0.03 [0%] | 0.11 [1%] |
| miss<10% | 164 | 18.37 | 0.03 [0%] | 0.72 [4%] | 5.02 [27%] | 0.17 [1%] | 0.00 [0%] | 1.15 [6%] | 0.00 [0%] | 0.43 [2%] | 10.66 [58%] | 0.04 [0%] | 0.15 [1%] |
| mixed | 3 | 8.82 | 0.00 [0%] | 0.39 [4%] | 4.43 [50%] | 0.24 [3%] | 0.58 [7%] | 0.00 [0%] | 0.06 [1%] | 1.16 [13%] | 1.50 [17%] | 0.00 [0%] | 0.46 [5%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 93 | 0.00 | 0.02 | 1.28 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 220 | 0.00 | 0.02 | 0.58 | 0.02 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 64 | 0.00 | 0.02 | 0.62 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.01 | 0.44 | 0.03 | 0.00 | 0.00 | 0.00 | 0.01 |
| mixed | 3 | 0.00 | 0.02 | 1.88 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 93 | 0.06 | 1.17 | 0.33 | 0.00 | 0.00 | 0.56 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 220 | 0.03 | 0.18 | 0.07 | 0.00 | 0.00 | 0.43 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.45 | 0.06 | 0.00 | 0.00 | 0.45 | 0.00 | 0.00 | 0.02 |
| miss<10% | 164 | 0.02 | 0.43 | 0.12 | 0.00 | 0.00 | 0.43 | 0.00 | 0.00 | 0.01 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.71 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 93 | 0.01 | 0.16 | 1.27 | 0.03 | 0.60 | 0.35 | 0.00 | 1.40 | 0.01 | 0.01 |
| GPU≥50% | 220 | 0.00 | 0.05 | 0.33 | 0.01 | 0.02 | 0.03 | 0.00 | 0.85 | 0.00 | 0.01 |
| 10–50% | 64 | 0.05 | 0.41 | 3.29 | 0.05 | 0.13 | 0.00 | 0.00 | 7.79 | 0.03 | 0.09 |
| miss<10% | 164 | 0.03 | 0.68 | 4.15 | 0.02 | 1.14 | 0.00 | 0.00 | 10.66 | 0.03 | 0.13 |
| mixed | 3 | 0.00 | 0.04 | 2.55 | 0.00 | 0.00 | 0.06 | 0.00 | 1.50 | 0.00 | 0.46 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | hol:full | hol:resv | other | own:full | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 93 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |
| GPU≥50% | 220 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.05 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 728 | 612 / 0 / 116 | 384 | 456 | 254 (198–1111) | 0 (2421) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6229 | 6229 / 0 / 0 | 128 | 1067 | 674 (92–1652) | 0 (0) |
| promotion after a load | 47 | 47 / 0 / 0 | 128 | 649 | 304 (194–757) | 0 (0) |

Requests refused at least once: 134 of 544; preemptions: 32; running requests that could not get their next chunk: 54.
Admitted external loads: 120; reservation passed at admission p50 455 / max 1945 blocks; free blocks at admission p50 1817.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.638 |
| time with free blocks < 50% of the pool | 0.696 |
| time with free blocks < 25% of the pool | 0.548 |
| time with free blocks < 10% of the pool | 0.297 |
| time with free blocks < 5% of the pool | 0.161 |
| blocks held by loads in transfer, mean / max | 30 / 3408 |
| in-flight prefill reservation after schedule(), mean / max | 324 / 3617 |
| steps whose running requests used the whole token budget (share of time) | 0.049 |
| steps with a shortened token budget (share of time) | 0.201 |
| running requests, mean / max | 6.8 / 16 |
| waiting + kv-holding requests, mean / max | 4.1 / 20 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 93 | 0.67 | 0.00 | 0.14 / 0.04 | 10.54 [31] | 2.91 [62] | 2.25 [32] | 9.66 [61] |
| GPU≥50% | 220 | 0.62 | 0.00 | 0.32 / 0.02 | 0.27 [84] | 1.67 [136] | 0.95 [118] | 3.61 [102] |
| 10–50% | 64 | 0.64 | 0.00 | 0.25 / 0.04 | 0.65 [23] | 11.68 [41] | 1.34 [33] | 23.93 [31] |
| miss<10% | 164 | 0.70 | 0.00 | 0.40 / 0.02 | 4.14 [50] | 24.20 [114] | 12.40 [92] | 28.86 [72] |
| mixed | 3 | 0.67 | 0.00 | 0.03 / 0.02 | 14.12 [1] | 8.84 [2] | – | 8.84 [3] |
