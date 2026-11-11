## Admission analysis of `tool08-320-tokfast` (544 requests, 20049 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 6198 | 384 | 12.65 / 34.00 | 0.00 / 2.34 | 0.80 / 5.70 | 0.00 / 4.10 | 0.90 / 0.89 | 0.00 / 0.01 | 0.85 / 0.92 |
| GPU≥50% | 201 | 6201 | 99 | 2.97 / 29.05 | 0.00 / 0.87 | 1.09 / 5.84 | 0.00 / 0.26 | 0.84 / 0.97 | 0.00 / 0.00 | 0.42 / 0.52 |
| 10–50% | 63 | 2038 | 96 | 12.87 / 61.63 | 0.00 / 0.95 | 11.86 / 18.51 | 0.00 / 0.20 | 0.12 / 0.12 | 0.00 / 0.00 | 0.77 / 0.91 |
| miss<10% | 174 | 13886 | 128 | 22.92 / 64.04 | 0.00 / 1.00 | 14.46 / 20.80 | 0.00 / 1.11 | – | – | 3.91 / 4.87 |
| mixed | 9 | 3195 | 160 | 14.48 / 21.49 | 1.84 / 2.61 | 7.48 / 6.77 | 0.00 / 2.70 | 1.44 / 1.52 | 0.00 / 0.00 | 0.86 / 0.98 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 13.03 | 0.06 [0%] | 0.26 [2%] | 4.60 [35%] | 1.94 [15%] | 0.33 [3%] | 0.72 [6%] | 0.97 [7%] | 4.16 [32%] | 0.00 [0%] |
| GPU≥50% | 201 | 7.05 | 0.02 [0%] | 0.18 [3%] | 1.79 [25%] | 0.68 [10%] | 0.03 [0%] | 0.03 [0%] | 0.04 [1%] | 4.27 [61%] | 0.00 [0%] |
| 10–50% | 63 | 19.67 | 0.11 [1%] | 0.55 [3%] | 5.39 [27%] | 2.11 [11%] | 0.00 [0%] | 0.19 [1%] | 0.00 [0%] | 11.32 [58%] | 0.00 [0%] |
| miss<10% | 174 | 22.92 | 0.08 [0%] | 0.81 [4%] | 5.71 [25%] | 1.09 [5%] | 0.00 [0%] | 1.08 [5%] | 0.00 [0%] | 14.15 [62%] | 0.00 [0%] |
| mixed | 9 | 13.59 | 0.06 [0%] | 0.27 [2%] | 4.18 [31%] | 0.70 [5%] | 0.72 [5%] | 0.00 [0%] | 0.17 [1%] | 7.48 [55%] | 0.01 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.00 | 0.01 | 1.27 | 1.05 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.00 | 0.01 | 0.58 | 0.28 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.01 | 0.01 | 0.62 | 0.30 | 0.00 | 0.00 | 0.00 |
| miss<10% | 174 | 0.00 | 0.01 | 0.61 | 0.38 | 0.00 | 0.00 | 0.00 |
| mixed | 9 | 0.00 | 0.01 | 2.53 | 0.05 | 0.00 | 0.00 | 0.01 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.03 | 0.17 | 1.83 | 0.50 | 0.00 | 0.00 | 3.16 | 0.00 |
| GPU≥50% | 201 | 0.01 | 0.17 | 1.19 | 0.39 | 0.00 | 0.00 | 4.08 | 0.00 |
| 10–50% | 63 | 0.10 | 0.53 | 4.75 | 1.81 | 0.00 | 0.00 | 11.32 | 0.00 |
| miss<10% | 174 | 0.07 | 0.79 | 5.08 | 0.71 | 0.00 | 0.00 | 14.14 | 0.00 |
| mixed | 9 | 0.00 | 0.17 | 0.73 | 0.66 | 0.00 | 0.00 | 5.21 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.01 | 0.06 | 1.45 | 0.11 | 0.72 | 0.96 | 0.77 | 0.00 |
| GPU≥50% | 201 | 0.00 | 0.01 | 0.02 | 0.00 | 0.03 | 0.04 | 0.16 | 0.00 |
| 10–50% | 63 | 0.00 | 0.00 | 0.02 | 0.00 | 0.19 | 0.00 | 0.00 | 0.00 |
| miss<10% | 174 | 0.00 | 0.00 | 0.02 | 0.00 | 1.08 | 0.00 | 0.01 | 0.00 |
| mixed | 9 | 0.06 | 0.03 | 0.59 | 0.00 | 0.00 | 0.17 | 1.85 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 174 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 9 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1225 | 832 / 0 / 393 | 384 | 429 | 248 (23–1139) | 0 (1838) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5934 | 5934 / 0 / 0 | 128 | 1085 | 505 (97–1240) | 0 (0) |

Requests refused at least once: 153 of 544; preemptions: 8; running requests that could not get their next chunk: 18.
Admitted external loads: 123; reservation passed at admission p50 407 / max 1851 blocks; free blocks at admission p50 1607.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.668 |
| time with free blocks < 50% of the pool | 0.726 |
| time with free blocks < 25% of the pool | 0.600 |
| time with free blocks < 10% of the pool | 0.327 |
| time with free blocks < 5% of the pool | 0.174 |
| blocks held by loads in transfer, mean / max | 25 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 323 / 1916 |
| steps whose running requests used the whole token budget (share of time) | 0.043 |
| steps with a shortened token budget (share of time) | 0.239 |
| running requests, mean / max | 6.9 / 16 |
| waiting + kv-holding requests, mean / max | 6.1 / 30 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.72 | 0.00 | 0.12 / 0.02 | 11.07 [27] | 15.25 [70] | 2.04 [23] | 15.26 [74] |
| GPU≥50% | 201 | 0.64 | 0.00 | 0.30 / 0.05 | 0.27 [72] | 6.31 [129] | 1.01 [106] | 6.97 [95] |
| 10–50% | 63 | 0.62 | 0.00 | 0.21 / 0.03 | 0.80 [24] | 23.52 [39] | 1.42 [30] | 28.82 [33] |
| miss<10% | 174 | 0.72 | 0.00 | 0.32 / 0.05 | 4.46 [48] | 28.87 [126] | 14.26 [97] | 38.53 [77] |
| mixed | 9 | 0.44 | 0.00 | 0.03 / 0.00 | 15.28 [5] | 13.10 [4] | – | 14.48 [9] |
