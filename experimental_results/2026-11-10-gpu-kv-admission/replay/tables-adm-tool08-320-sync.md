## Admission analysis of `tool08-320-sync` (544 requests, 21112 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 6178 | 384 | 20.76 / 44.92 | 6.96 / 8.27 | 8.69 / 10.55 | 0.00 / 0.63 | 0.36 / 0.50 | 0.00 / 0.29 | 0.27 / 0.33 |
| GPU≥50% | 201 | 6214 | 51 | 6.50 / 40.69 | 2.25 / 5.91 | 0.58 / 5.57 | 0.00 / 0.05 | 0.54 / 0.31 | 0.00 / 0.00 | 0.33 / 0.32 |
| 10–50% | 64 | 2103 | 82 | 11.34 / 38.35 | 1.57 / 6.45 | 1.42 / 5.74 | 0.00 / 0.09 | 1.25 / 0.70 | 1.31 / 0.90 | 0.56 / 0.78 |
| miss<10% | 167 | 13883 | 128 | 14.90 / 44.39 | 1.87 / 4.94 | 1.82 / 7.49 | 0.00 / 0.87 | – | – | 3.18 / 4.05 |
| mixed | 2 | 7490 | 384 | 10.00 / 10.00 | 1.71 / 1.30 | 7.17 / 7.17 | 0.00 / 0.00 | 0.42 / 0.42 | 0.50 / 0.28 | 0.35 / 0.28 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 20.25 | 11.53 [57%] | 1.77 [9%] | 5.77 [28%] | 0.02 [0%] | 0.60 [3%] | 0.52 [3%] | 0.00 [0%] | 0.02 [0%] |
| GPU≥50% | 201 | 11.53 | 6.92 [60%] | 1.04 [9%] | 3.22 [28%] | 0.00 [0%] | 0.05 [0%] | 0.28 [2%] | 0.01 [0%] | 0.02 [0%] |
| 10–50% | 64 | 12.38 | 7.66 [62%] | 1.05 [8%] | 3.23 [26%] | 0.00 [0%] | 0.12 [1%] | 0.28 [2%] | 0.00 [0%] | 0.04 [0%] |
| miss<10% | 167 | 13.31 | 7.77 [58%] | 1.15 [9%] | 3.24 [24%] | 0.00 [0%] | 0.86 [6%] | 0.27 [2%] | 0.00 [0%] | 0.02 [0%] |
| mixed | 2 | 9.18 | 6.99 [76%] | 0.86 [9%] | 0.10 [1%] | 0.00 [0%] | 0.25 [3%] | 0.99 [11%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 5.26 | 0.64 | 2.37 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 201 | 3.97 | 0.41 | 1.52 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 4.20 | 0.28 | 1.97 | 0.00 | 0.00 | 0.00 |
| miss<10% | 167 | 3.41 | 0.32 | 1.21 | 0.00 | 0.00 | 0.00 |
| mixed | 2 | 0.84 | 0.47 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 5.91 | 1.00 | 3.27 | 0.00 | 0.34 | 0.00 | 0.02 |
| GPU≥50% | 201 | 2.94 | 0.63 | 1.69 | 0.00 | 0.28 | 0.00 | 0.02 |
| 10–50% | 64 | 3.43 | 0.74 | 1.25 | 0.00 | 0.27 | 0.00 | 0.04 |
| miss<10% | 167 | 4.36 | 0.82 | 2.02 | 0.00 | 0.27 | 0.00 | 0.02 |
| mixed | 2 | 6.15 | 0.39 | 0.00 | 0.00 | 0.63 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.01 | 0.03 | 0.60 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.00 | 0.00 | 0.05 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.09 | 0.00 | 0.00 |
| miss<10% | 167 | 0.00 | 0.01 | 0.86 | 0.00 | 0.00 |
| mixed | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.25 | 0.03 | 0.00 | 0.00 | 0.01 | 0.00 |
| GPU≥50% | 201 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.01 | 0.01 | 0.00 | 0.00 | 0.03 | 0.00 |
| miss<10% | 167 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 2 | 0.00 | 0.00 | 0.03 | 0.00 | 0.25 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 2125 | 2125 / 0 / 0 | 384 | 418 | 218 (32–549) | 0 (162) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4646 | 4646 / 0 / 0 | 128 | 1085 | 683 (114–1327) | 0 (0) |
| promotion after a load | 60 | 60 / 0 / 0 | 128 | 661 | 445 (51–548) | 0 (0) |

Requests refused at least once: 133 of 544; preemptions: 7; running requests that could not get their next chunk: 7.
Admitted external loads: 118; reservation passed at admission p50 0 / max 307 blocks; free blocks at admission p50 1141.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.613 |
| time with free blocks < 50% of the pool | 0.659 |
| time with free blocks < 25% of the pool | 0.529 |
| time with free blocks < 10% of the pool | 0.266 |
| time with free blocks < 5% of the pool | 0.140 |
| blocks held by loads in transfer, mean / max | 22 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 296 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.439 |
| running requests, mean / max | 6.3 / 16 |
| waiting + kv-holding requests, mean / max | 5.9 / 34 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.66 | 0.65 | 0.15 / 0.03 | 19.03 [37] | 21.35 [73] | 16.26 [34] | 21.35 [76] |
| GPU≥50% | 201 | 0.51 | 0.46 | 0.57 / 0.04 | 0.43 [99] | 12.68 [102] | 1.64 [117] | 20.69 [84] |
| 10–50% | 64 | 0.56 | 0.52 | 0.28 / 0.03 | 1.61 [28] | 16.34 [36] | 1.45 [32] | 19.68 [32] |
| miss<10% | 167 | 0.58 | 0.52 | 0.49 / 0.05 | 5.64 [70] | 18.13 [97] | 9.75 [96] | 22.68 [71] |
| mixed | 2 | 1.00 | 1.00 | 0.26 / 0.23 | – | 10.00 [2] | 10.00 [1] | 9.63 [1] |
