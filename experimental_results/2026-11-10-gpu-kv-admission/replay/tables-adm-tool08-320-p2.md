## Admission analysis of `tool08-320-p2` (544 requests, 21127 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 6221 | 384 | 12.93 / 36.21 | 0.26 / 4.01 | 0.76 / 1.44 | 0.00 / 7.13 | 0.96 / 0.90 | 0.00 / 0.01 | 0.63 / 0.74 |
| GPU≥50% | 201 | 6193 | 62 | 1.57 / 30.42 | 0.00 / 2.11 | 0.44 / 1.14 | 0.17 / 3.45 | 0.65 / 0.61 | 0.00 / 0.00 | 0.42 / 0.46 |
| 10–50% | 64 | 2103 | 89 | 10.05 / 47.30 | 0.00 / 2.63 | 0.56 / 1.45 | 3.23 / 9.57 | 0.78 / 0.70 | 0.00 / 0.03 | 0.71 / 1.08 |
| miss<10% | 164 | 13883 | 128 | 18.68 / 51.77 | 0.00 / 2.09 | 0.43 / 1.14 | 10.51 / 13.61 | 1.10 / 1.10 | 0.00 / 0.00 | 3.69 / 4.70 |
| mixed | 5 | 7056 | 384 | 31.82 / 44.52 | 1.36 / 1.65 | 0.82 / 0.64 | 27.13 / 18.53 | 1.06 / 0.93 | 0.00 / 0.00 | 0.69 / 0.67 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 13.50 | 0.02 [0%] | 0.21 [2%] | 8.88 [66%] | 0.64 [5%] | 0.38 [3%] | 0.45 [3%] | 0.30 [2%] | 0.80 [6%] | 0.37 [3%] | 0.17 [1%] | 1.23 [9%] | 0.01 [0%] | 0.04 [0%] |
| GPU≥50% | 201 | 6.73 | 0.00 [0%] | 0.18 [3%] | 4.23 [63%] | 0.25 [4%] | 0.01 [0%] | 0.04 [1%] | 0.01 [0%] | 0.45 [7%] | 0.33 [5%] | 0.08 [1%] | 1.10 [16%] | 0.00 [0%] | 0.04 [1%] |
| 10–50% | 64 | 13.70 | 0.00 [0%] | 0.33 [2%] | 7.79 [57%] | 0.47 [3%] | 0.02 [0%] | 0.12 [1%] | 0.00 [0%] | 0.48 [3%] | 0.04 [0%] | 0.03 [0%] | 4.24 [31%] | 0.00 [0%] | 0.18 [1%] |
| miss<10% | 164 | 16.85 | 0.00 [0%] | 0.56 [3%] | 7.44 [44%] | 0.42 [3%] | 0.00 [0%] | 2.53 [15%] | 0.00 [0%] | 0.45 [3%] | 0.10 [1%] | 0.04 [0%] | 5.23 [31%] | 0.00 [0%] | 0.07 [0%] |
| mixed | 5 | 21.76 | 0.00 [0%] | 0.60 [3%] | 15.70 [72%] | 1.54 [7%] | 0.32 [1%] | 0.57 [3%] | 0.00 [0%] | 0.88 [4%] | 1.26 [6%] | 0.00 [0%] | 0.88 [4%] | 0.01 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.00 | 0.04 | 3.68 | 0.27 | 0.00 | 0.00 | 0.00 | 0.02 |
| GPU≥50% | 201 | 0.00 | 0.05 | 1.98 | 0.07 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 64 | 0.00 | 0.04 | 2.39 | 0.21 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.04 | 1.88 | 0.15 | 0.00 | 0.00 | 0.00 | 0.02 |
| mixed | 5 | 0.00 | 0.01 | 1.64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.04 | 0.81 | 0.01 | 0.58 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.07 | 0.62 | 0.02 | 0.44 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.04 | 0.89 | 0.02 | 0.46 | 0.00 | 0.00 | 0.00 | 0.00 | 0.04 |
| miss<10% | 164 | 0.03 | 0.61 | 0.05 | 0.45 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.10 | 4.17 | 0.32 | 0.45 | 0.30 | 0.00 | 0.37 | 0.17 | 1.23 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.06 | 1.62 | 0.17 | 0.04 | 0.01 | 0.00 | 0.33 | 0.08 | 1.10 | 0.00 | 0.03 |
| 10–50% | 64 | 0.25 | 4.50 | 0.23 | 0.12 | 0.00 | 0.00 | 0.04 | 0.03 | 4.24 | 0.00 | 0.14 |
| miss<10% | 164 | 0.49 | 4.95 | 0.23 | 2.53 | 0.00 | 0.00 | 0.10 | 0.04 | 5.23 | 0.00 | 0.05 |
| mixed | 5 | 0.59 | 13.69 | 1.54 | 0.57 | 0.00 | 0.00 | 1.26 | 0.00 | 0.88 | 0.01 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 201 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 972 | 878 / 0 / 94 | 384 | 446 | 233 (142–457) | 0 (1800) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6486 | 6486 / 0 / 0 | 128 | 1085 | 608 (107–1678) | 0 (600) |

Requests refused at least once: 117 of 544; preemptions: 8; running requests that could not get their next chunk: 16.
Admitted external loads: 128; reservation passed at admission p50 305 / max 1954 blocks; free blocks at admission p50 1771.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.638 |
| time with free blocks < 50% of the pool | 0.691 |
| time with free blocks < 25% of the pool | 0.556 |
| time with free blocks < 10% of the pool | 0.303 |
| time with free blocks < 5% of the pool | 0.156 |
| blocks held by loads in transfer, mean / max | 29 / 2688 |
| in-flight prefill reservation after schedule(), mean / max | 307 / 2615 |
| steps whose running requests used the whole token budget (share of time) | 0.042 |
| steps with a shortened token budget (share of time) | 0.193 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 5.1 / 23 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.76 | 0.00 | 0.11 / 0.03 | 10.96 [26] | 15.57 [84] | 2.64 [30] | 16.25 [80] |
| GPU≥50% | 201 | 0.54 | 0.00 | 0.47 / 0.04 | 0.32 [92] | 2.08 [109] | 0.90 [117] | 14.26 [84] |
| 10–50% | 64 | 0.62 | 0.00 | 0.23 / 0.05 | 0.77 [24] | 18.74 [40] | 1.11 [31] | 23.17 [33] |
| miss<10% | 164 | 0.68 | 0.00 | 0.41 / 0.04 | 6.50 [53] | 21.71 [111] | 12.70 [89] | 28.03 [75] |
| mixed | 5 | 0.60 | 0.00 | 0.16 / 0.10 | 32.48 [2] | 2.31 [3] | 1.40 [1] | 32.48 [4] |
