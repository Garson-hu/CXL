## Admission analysis of `x08-priolenage3` (544 requests, 21238 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 6175 | 384 | 4.15 / 12.74 | 0.46 / 1.28 | 0.95 / 2.06 | 0.00 / 0.35 | 0.49 / 0.73 | 0.00 / 0.33 | 0.31 / 0.46 |
| GPU≥50% | 213 | 6251 | 50 | 1.76 / 12.89 | 0.00 / 1.23 | 0.67 / 1.33 | 0.00 / 0.04 | 0.32 / 0.22 | 0.00 / 0.00 | 0.33 / 0.42 |
| 10–50% | 63 | 2038 | 96 | 1.62 / 8.55 | 0.00 / 1.41 | 0.57 / 0.93 | 0.00 / 0.06 | 0.36 / 0.54 | 0.00 / 0.00 | 0.43 / 0.70 |
| miss<10% | 169 | 13886 | 128 | 8.88 / 56.62 | 0.91 / 3.56 | 1.25 / 5.08 | 0.00 / 2.31 | – | – | 3.23 / 4.16 |
| mixed | 5 | 4348 | 160 | 5.61 / 7.69 | 1.88 / 1.86 | 0.79 / 1.46 | 0.00 / 0.89 | 0.67 / 0.63 | 0.00 / 0.12 | 0.33 / 0.33 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 4.75 | 2.45 [52%] | 0.16 [3%] | 0.93 [20%] | 0.01 [0%] | 0.05 [1%] | 0.33 [7%] | 0.00 [0%] | 0.80 [17%] | 0.00 [0%] | 0.01 [0%] |
| GPU≥50% | 213 | 2.61 | 1.39 [53%] | 0.10 [4%] | 0.53 [20%] | 0.00 [0%] | 0.00 [0%] | 0.03 [1%] | 0.00 [0%] | 0.49 [19%] | 0.00 [0%] | 0.05 [2%] |
| 10–50% | 63 | 2.43 | 1.38 [57%] | 0.01 [1%] | 0.43 [18%] | 0.00 [0%] | 0.00 [0%] | 0.05 [2%] | 0.00 [0%] | 0.54 [22%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 169 | 10.95 | 5.53 [51%] | 0.41 [4%] | 2.84 [26%] | 0.01 [0%] | 0.00 [0%] | 1.24 [11%] | 0.00 [0%] | 0.68 [6%] | 0.00 [0%] | 0.23 [2%] |
| mixed | 5 | 4.96 | 1.90 [38%] | 0.01 [0%] | 1.09 [22%] | 0.11 [2%] | 0.00 [0%] | 1.01 [20%] | 0.00 [0%] | 0.84 [17%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 1.14 | 0.04 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 213 | 0.94 | 0.05 | 0.23 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 |
| 10–50% | 63 | 1.13 | 0.01 | 0.28 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 2.55 | 0.10 | 0.86 | 0.00 | 0.00 | 0.00 | 0.00 | 0.06 |
| mixed | 5 | 1.81 | 0.00 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 0.73 | 0.04 | 0.57 | 0.00 | 0.00 | 0.00 | 0.71 | 0.00 | 0.01 |
| GPU≥50% | 213 | 0.45 | 0.06 | 0.29 | 0.00 | 0.00 | 0.00 | 0.49 | 0.00 | 0.04 |
| 10–50% | 63 | 0.25 | 0.01 | 0.13 | 0.00 | 0.00 | 0.00 | 0.53 | 0.00 | 0.00 |
| miss<10% | 169 | 2.52 | 0.27 | 1.48 | 0.01 | 0.00 | 0.00 | 0.68 | 0.00 | 0.11 |
| mixed | 5 | 0.00 | 0.01 | 0.79 | 0.00 | 0.00 | 0.00 | 0.66 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 0.00 | 0.00 | 0.04 | 0.00 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 213 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.00 | 0.00 | 0.01 | 0.00 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 0.46 | 0.03 | 0.50 | 0.00 | 1.24 | 0.00 | 0.00 | 0.00 | 0.06 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.89 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 0.27 | 0.03 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 |
| GPU≥50% | 213 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.12 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 811 | 804 / 0 / 7 | 384 | 391 | 143 (36–372) | 0 (160) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6006 | 6006 / 0 / 0 | 128 | 1700 | 734 (104–1657) | 0 (0) |
| promotion after a load | 94 | 94 / 0 / 0 | 57 | 57 | 27 (15–53) | 0 (0) |

Requests refused at least once: 119 of 544; preemptions: 7; running requests that could not get their next chunk: 58.
Admitted external loads: 104; reservation passed at admission p50 0 / max 227 blocks; free blocks at admission p50 1002.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.619 |
| time with free blocks < 50% of the pool | 0.680 |
| time with free blocks < 25% of the pool | 0.530 |
| time with free blocks < 10% of the pool | 0.264 |
| time with free blocks < 5% of the pool | 0.136 |
| blocks held by loads in transfer, mean / max | 26 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 253 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.424 |
| running requests, mean / max | 6.5 / 16 |
| waiting + kv-holding requests, mean / max | 2.4 / 17 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 0.65 | 0.50 | 0.15 / 0.03 | 1.53 [33] | 6.34 [61] | 9.12 [28] | 3.66 [66] |
| GPU≥50% | 213 | 0.45 | 0.34 | 0.44 / 0.01 | 0.46 [117] | 4.53 [96] | 1.40 [115] | 2.20 [98] |
| 10–50% | 63 | 0.44 | 0.35 | 0.20 / 0.03 | 0.71 [35] | 3.89 [28] | 1.41 [30] | 2.04 [33] |
| miss<10% | 169 | 0.53 | 0.47 | 0.36 / 0.03 | 4.16 [80] | 13.99 [89] | 6.68 [97] | 13.88 [72] |
| mixed | 5 | 0.80 | 0.80 | 0.10 / 0.02 | 2.95 [1] | 7.28 [4] | – | 5.61 [5] |
