## Admission analysis of `cc-p3728-base` (816 requests, 22266 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 2048 | 128 | 1.31 / 6.63 | 0.00 / 0.17 | 0.03 / 0.86 | 0.00 / 0.02 | 0.36 / 0.51 | 0.00 / 0.10 | 0.03 / 0.19 |
| GPU≥50% | 38 | 8192 | 256 | 0.59 / 9.29 | 0.00 / 0.21 | 0.04 / 1.00 | 0.00 / 0.00 | 0.22 / 0.38 | 0.00 / 0.10 | 0.03 / 0.13 |
| miss<10% | 418 | 2048 | 128 | 1.38 / 6.56 | 0.00 / 0.17 | 0.02 / 0.80 | 0.00 / 0.02 | – | – | 0.65 / 0.78 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 1.65 | 0.86 [52%] | 0.20 [12%] | 0.18 [11%] | 0.12 [7%] | 0.02 [1%] | 0.27 [17%] | 0.00 [0%] |
| GPU≥50% | 38 | 1.69 | 0.80 [47%] | 0.19 [11%] | 0.32 [19%] | 0.11 [7%] | 0.00 [0%] | 0.26 [16%] | 0.00 [0%] |
| miss<10% | 418 | 0.98 | 0.49 [50%] | 0.15 [15%] | 0.17 [17%] | 0.00 [0%] | 0.02 [2%] | 0.16 [16%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.12 | 0.01 | 0.03 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 38 | 0.11 | 0.03 | 0.07 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.11 | 0.01 | 0.04 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.41 | 0.14 | 0.13 | 0.00 | 0.18 | 0.00 |
| GPU≥50% | 38 | 0.47 | 0.13 | 0.21 | 0.00 | 0.19 | 0.00 |
| miss<10% | 418 | 0.38 | 0.14 | 0.12 | 0.00 | 0.16 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|
| host≥50% | 360 | 0.00 | 0.02 | 0.00 | 0.00 |
| GPU≥50% | 38 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.02 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 38 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 79 | 79 / 0 / 0 | 512 | 512 | 190 (4–508) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 177 | 177 / 0 / 0 | 128 | 257 | 70 (2–380) | 0 (0) |

Requests refused at least once: 44 of 816; preemptions: 7; running requests that could not get their next chunk: 16.
Admitted external loads: 563; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 3662.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.216 |
| time with free blocks < 50% of the pool | 0.132 |
| time with free blocks < 25% of the pool | 0.085 |
| time with free blocks < 10% of the pool | 0.038 |
| time with free blocks < 5% of the pool | 0.020 |
| blocks held by loads in transfer, mean / max | 89 / 1664 |
| in-flight prefill reservation after schedule(), mean / max | 35 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.232 |
| running requests, mean / max | 2.1 / 16 |
| waiting + kv-holding requests, mean / max | 1.4 / 30 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 360 | 0.26 | 0.12 | 0.93 / 0.16 | 0.43 [268] | 3.04 [92] | 0.69 [306] | 4.33 [54] |
| GPU≥50% | 38 | 0.32 | 0.03 | 0.86 / 0.16 | 0.24 [26] | 2.58 [12] | 0.28 [30] | 5.28 [8] |
| miss<10% | 418 | 0.33 | 0.09 | 0.96 / 0.16 | 0.74 [278] | 1.53 [140] | 0.83 [356] | 4.07 [62] |
