## Admission analysis of `tool08-320-priohits` (544 requests, 21338 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 87 | 6169 | 384 | 5.58 / 11.32 | 0.76 / 1.88 | 0.97 / 1.75 | 0.00 / 0.34 | 0.45 / 0.74 | 0.00 / 0.30 | 0.33 / 0.46 |
| GPU≥50% | 222 | 6251 | 51 | 1.79 / 9.35 | 0.11 / 1.19 | 0.60 / 1.17 | 0.00 / 0.07 | 1.72 / 0.94 | 7.89 / 3.94 | 0.34 / 0.39 |
| 10–50% | 63 | 2038 | 77 | 9.41 / 42.40 | 1.01 / 7.13 | 1.35 / 6.18 | 0.00 / 0.19 | 0.34 / 0.76 | 0.00 / 0.92 | 0.79 / 0.95 |
| miss<10% | 169 | 13883 | 128 | 15.62 / 51.29 | 2.57 / 5.80 | 1.71 / 7.62 | 0.00 / 1.39 | – | – | 3.25 / 4.17 |
| mixed | 3 | 3213 | 160 | 3.09 / 11.99 | 0.46 / 0.52 | 1.08 / 3.21 | 0.49 / 0.56 | 0.76 / 0.61 | 0.22 / 0.20 | 0.25 / 0.42 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 87 | 5.00 | 2.91 [58%] | 0.12 [2%] | 0.66 [13%] | 0.00 [0%] | 0.12 [2%] | 0.39 [8%] | 0.00 [0%] | 0.80 [16%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 222 | 2.47 | 1.43 [58%] | 0.04 [1%] | 0.43 [17%] | 0.00 [0%] | 0.00 [0%] | 0.07 [3%] | 0.00 [0%] | 0.50 [20%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 63 | 13.58 | 7.88 [58%] | 0.63 [5%] | 4.27 [31%] | 0.00 [0%] | 0.00 [0%] | 0.19 [1%] | 0.00 [0%] | 0.58 [4%] | 0.00 [0%] | 0.02 [0%] |
| miss<10% | 169 | 14.82 | 7.88 [53%] | 0.80 [5%] | 4.27 [29%] | 0.00 [0%] | 0.00 [0%] | 1.14 [8%] | 0.00 [0%] | 0.67 [4%] | 0.00 [0%] | 0.05 [0%] |
| mixed | 3 | 5.09 | 2.24 [44%] | 0.05 [1%] | 1.28 [25%] | 0.00 [0%] | 0.00 [0%] | 0.56 [11%] | 0.00 [0%] | 0.79 [16%] | 0.00 [0%] | 0.17 [3%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 87 | 1.62 | 0.02 | 0.24 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 222 | 1.00 | 0.02 | 0.16 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 4.40 | 0.22 | 2.49 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 |
| miss<10% | 169 | 3.71 | 0.29 | 1.78 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 |
| mixed | 3 | 0.52 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 87 | 0.80 | 0.01 | 0.24 | 0.00 | 0.00 | 0.00 | 0.70 | 0.00 | 0.00 |
| GPU≥50% | 222 | 0.39 | 0.01 | 0.26 | 0.00 | 0.00 | 0.00 | 0.49 | 0.00 | 0.01 |
| 10–50% | 63 | 3.46 | 0.41 | 1.73 | 0.00 | 0.00 | 0.00 | 0.58 | 0.00 | 0.00 |
| miss<10% | 169 | 4.13 | 0.50 | 2.30 | 0.00 | 0.00 | 0.00 | 0.67 | 0.00 | 0.03 |
| mixed | 3 | 1.36 | 0.01 | 1.08 | 0.00 | 0.00 | 0.00 | 0.77 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 87 | 0.00 | 0.00 | 0.00 | 0.00 | 0.33 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 222 | 0.00 | 0.00 | 0.01 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.00 | 0.00 | 0.04 | 0.00 | 0.15 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 0.04 | 0.00 | 0.20 | 0.00 | 1.14 | 0.00 | 0.00 | 0.00 | 0.01 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.56 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 87 | 0.22 | 0.03 | 0.00 | 0.00 | 0.00 | 0.05 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 222 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.04 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.13 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.07 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1146 | 1143 / 0 / 3 | 384 | 405 | 162 (40–302) | 0 (174) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5341 | 5341 / 0 / 0 | 128 | 1085 | 509 (95–1381) | 0 (0) |
| promotion after a load | 267 | 267 / 0 / 0 | 39 | 39 | 28 (5–756) | 0 (0) |

Requests refused at least once: 136 of 544; preemptions: 5; running requests that could not get their next chunk: 11.
Admitted external loads: 95; reservation passed at admission p50 0 / max 474 blocks; free blocks at admission p50 1014.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.618 |
| time with free blocks < 50% of the pool | 0.663 |
| time with free blocks < 25% of the pool | 0.542 |
| time with free blocks < 10% of the pool | 0.289 |
| time with free blocks < 5% of the pool | 0.154 |
| blocks held by loads in transfer, mean / max | 26 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 254 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.423 |
| running requests, mean / max | 6.3 / 16 |
| waiting + kv-holding requests, mean / max | 3.4 / 20 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 87 | 0.59 | 0.51 | 0.16 / 0.03 | 2.70 [36] | 6.78 [51] | 9.26 [31] | 5.07 [56] |
| GPU≥50% | 222 | 0.45 | 0.36 | 0.44 / 0.02 | 0.42 [122] | 4.69 [100] | 1.56 [116] | 2.36 [106] |
| 10–50% | 63 | 0.56 | 0.43 | 0.40 / 0.02 | 1.85 [28] | 15.63 [35] | 1.85 [34] | 25.45 [29] |
| miss<10% | 169 | 0.56 | 0.47 | 0.44 / 0.01 | 6.24 [74] | 21.52 [95] | 8.59 [97] | 26.33 [72] |
| mixed | 3 | 1.00 | 0.67 | 0.15 / 0.05 | – | 3.09 [3] | 3.09 [1] | 11.99 [2] |
