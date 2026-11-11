## Admission analysis of `tool04-320-base` (1159 requests, 87135 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 148 | 6521 | 384 | 3.34 / 30.11 | 0.00 / 2.20 | 0.78 / 4.29 | 0.00 / 0.32 | 0.21 / 0.58 | 0.00 / 0.20 | 0.21 / 0.42 |
| GPU≥50% | 576 | 6187 | 386 | 0.27 / 13.24 | 0.00 / 1.09 | 0.03 / 1.05 | 0.00 / 0.01 | 0.09 / 0.38 | 0.00 / 0.14 | 0.17 / 0.29 |
| 10–50% | 121 | 2428 | 107 | 0.78 / 20.12 | 0.00 / 1.14 | 0.03 / 2.06 | 0.00 / 0.02 | 0.11 / 0.42 | 0.00 / 0.54 | 0.45 / 0.83 |
| miss<10% | 301 | 13712 | 128 | 5.05 / 26.55 | 0.00 / 1.55 | 0.03 / 1.98 | 0.00 / 0.34 | 0.05 / 0.03 | 0.00 / 0.00 | 2.98 / 3.89 |
| mixed | 13 | 1844 | 32 | 3.09 / 35.05 | 1.63 / 3.41 | 0.99 / 5.16 | 0.00 / 0.41 | 0.17 / 0.42 | 0.00 / 0.42 | 0.20 / 0.40 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 148 | 7.59 | 4.27 [56%] | 0.27 [4%] | 1.81 [24%] | 0.01 [0%] | 0.19 [3%] | 0.28 [4%] | 0.01 [0%] | 0.75 [10%] |
| GPU≥50% | 576 | 2.16 | 1.47 [68%] | 0.10 [4%] | 0.22 [10%] | 0.00 [0%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.36 [16%] |
| 10–50% | 121 | 3.34 | 2.09 [63%] | 0.10 [3%] | 0.71 [21%] | 0.01 [0%] | 0.02 [1%] | 0.02 [1%] | 0.00 [0%] | 0.40 [12%] |
| miss<10% | 301 | 3.87 | 2.36 [61%] | 0.17 [4%] | 0.57 [15%] | 0.00 [0%] | 0.00 [0%] | 0.34 [9%] | 0.00 [0%] | 0.44 [11%] |
| mixed | 13 | 9.82 | 5.64 [57%] | 0.37 [4%] | 2.52 [26%] | 0.05 [1%] | 0.14 [1%] | 0.41 [4%] | 0.00 [0%] | 0.68 [7%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 148 | 1.83 | 0.12 | 0.24 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 576 | 0.91 | 0.05 | 0.13 | 0.00 | 0.00 | 0.00 |
| 10–50% | 121 | 1.03 | 0.04 | 0.07 | 0.00 | 0.00 | 0.00 |
| miss<10% | 301 | 1.34 | 0.08 | 0.13 | 0.00 | 0.00 | 0.00 |
| mixed | 13 | 2.44 | 0.12 | 0.79 | 0.05 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 148 | 2.05 | 0.13 | 1.50 | 0.00 | 0.00 | 0.00 | 0.61 |
| GPU≥50% | 576 | 0.56 | 0.04 | 0.09 | 0.00 | 0.00 | 0.00 | 0.35 |
| 10–50% | 121 | 0.98 | 0.05 | 0.64 | 0.00 | 0.00 | 0.00 | 0.39 |
| miss<10% | 301 | 1.02 | 0.09 | 0.44 | 0.00 | 0.00 | 0.00 | 0.43 |
| mixed | 13 | 2.71 | 0.20 | 1.63 | 0.00 | 0.00 | 0.00 | 0.62 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | own:full | own:resv | pending |
|---|---|---|---|---|---|---|
| host≥50% | 148 | 0.03 | 0.00 | 0.28 | 0.01 | 0.00 |
| GPU≥50% | 576 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |
| 10–50% | 121 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 |
| miss<10% | 301 | 0.00 | 0.00 | 0.34 | 0.00 | 0.00 |
| mixed | 13 | 0.00 | 0.00 | 0.41 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 148 | 0.19 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 576 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 121 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 301 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 13 | 0.40 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1303 | 1286 / 0 / 17 | 384 | 456 | 287 (151–1119) | 0 (1087) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3615 | 3615 / 0 / 0 | 128 | 1700 | 821 (243–1866) | 0 (0) |
| promotion after a load | 6 | 6 / 0 / 0 | 28 | 28 | 12 (11–25) | 0 (0) |

Requests refused at least once: 59 of 1159; preemptions: 1; running requests that could not get their next chunk: 2.
Admitted external loads: 187; reservation passed at admission p50 0 / max 1030 blocks; free blocks at admission p50 5209.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.255 |
| time with free blocks < 50% of the pool | 0.170 |
| time with free blocks < 25% of the pool | 0.092 |
| time with free blocks < 10% of the pool | 0.037 |
| time with free blocks < 5% of the pool | 0.018 |
| blocks held by loads in transfer, mean / max | 12 / 2240 |
| in-flight prefill reservation after schedule(), mean / max | 108 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.186 |
| running requests, mean / max | 1.8 / 15 |
| waiting + kv-holding requests, mean / max | 0.8 / 18 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 148 | 0.51 | 0.44 | 0.75 / 0.25 | 0.32 [73] | 10.42 [75] | 2.43 [134] | 18.73 [14] |
| GPU≥50% | 576 | 0.28 | 0.24 | 0.83 / 0.44 | 0.17 [415] | 5.41 [161] | 0.26 [559] | 11.62 [17] |
| 10–50% | 121 | 0.34 | 0.32 | 0.80 / 0.40 | 0.45 [80] | 8.25 [41] | 0.72 [117] | 11.32 [4] |
| miss<10% | 301 | 0.36 | 0.31 | 0.83 / 0.44 | 2.74 [193] | 11.84 [108] | 4.70 [289] | 25.47 [12] |
| mixed | 13 | 0.54 | 0.46 | 0.77 / 0.43 | 0.30 [6] | 17.98 [7] | 3.09 [13] | – |
