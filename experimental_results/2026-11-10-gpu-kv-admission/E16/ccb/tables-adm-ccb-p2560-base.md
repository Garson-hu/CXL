## Admission analysis of `ccb-p2560-base` (816 requests, 28554 engine steps, pool 2560 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 372 | 2048 | 128 | 1.47 / 7.19 | 0.00 / 0.29 | 0.03 / 0.95 | 0.00 / 0.03 | 0.33 / 0.46 | 0.00 / 0.09 | 0.03 / 0.16 |
| GPU≥50% | 25 | 8192 | 256 | 0.58 / 9.88 | 0.00 / 0.34 | 0.20 / 1.00 | 0.00 / 0.01 | 0.20 / 0.43 | 0.00 / 0.00 | 0.03 / 0.05 |
| miss<10% | 419 | 2048 | 128 | 1.47 / 6.89 | 0.00 / 0.26 | 0.02 / 0.90 | 0.00 / 0.04 | – | – | 0.66 / 0.77 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 372 | 1.82 | 0.88 [48%] | 0.18 [10%] | 0.33 [18%] | 0.11 [6%] | 0.03 [2%] | 0.29 [16%] |
| GPU≥50% | 25 | 1.78 | 0.70 [39%] | 0.20 [11%] | 0.38 [21%] | 0.14 [8%] | 0.01 [0%] | 0.35 [19%] |
| miss<10% | 419 | 1.20 | 0.57 [47%] | 0.14 [12%] | 0.28 [23%] | 0.00 [0%] | 0.04 [3%] | 0.18 [15%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 372 | 0.19 | 0.03 | 0.08 | 0.00 | 0.00 |
| GPU≥50% | 25 | 0.19 | 0.04 | 0.11 | 0.00 | 0.00 |
| miss<10% | 419 | 0.16 | 0.03 | 0.08 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 372 | 0.44 | 0.11 | 0.20 | 0.00 | 0.19 |
| GPU≥50% | 25 | 0.44 | 0.12 | 0.22 | 0.00 | 0.22 |
| miss<10% | 419 | 0.41 | 0.11 | 0.20 | 0.00 | 0.18 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 372 | 0.03 | 0.00 |
| GPU≥50% | 25 | 0.01 | 0.00 |
| miss<10% | 419 | 0.04 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 372 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 25 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 419 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 276 | 276 / 0 / 0 | 512 | 512 | 118 (50–374) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 479 | 479 / 0 / 0 | 128 | 512 | 115 (47–500) | 0 (0) |

Requests refused at least once: 78 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 565; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 2559.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.277 |
| time with free blocks < 50% of the pool | 0.186 |
| time with free blocks < 25% of the pool | 0.114 |
| time with free blocks < 10% of the pool | 0.051 |
| time with free blocks < 5% of the pool | 0.033 |
| blocks held by loads in transfer, mean / max | 89 / 1088 |
| in-flight prefill reservation after schedule(), mean / max | 34 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.226 |
| running requests, mean / max | 1.7 / 14 |
| waiting + kv-holding requests, mean / max | 1.5 / 33 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 372 | 0.28 | 0.12 | 0.87 / 0.15 | 0.43 [266] | 3.16 [106] | 0.64 [308] | 4.46 [64] |
| GPU≥50% | 25 | 0.28 | 0.00 | 0.72 / 0.12 | 0.25 [18] | 4.55 [7] | 0.25 [17] | 3.17 [8] |
| miss<10% | 419 | 0.38 | 0.07 | 0.92 / 0.15 | 0.69 [259] | 2.28 [160] | 1.09 [351] | 4.20 [68] |
