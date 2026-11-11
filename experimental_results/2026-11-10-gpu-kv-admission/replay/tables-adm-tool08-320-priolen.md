## Admission analysis of `tool08-320-priolen` (544 requests, 20314 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 6169 | 384 | 4.76 / 13.98 | 0.38 / 1.43 | 1.00 / 1.90 | 0.00 / 0.48 | 0.53 / 0.80 | 0.00 / 0.51 | 0.39 / 0.52 |
| GPU≥50% | 217 | 6272 | 48 | 1.97 / 11.64 | 0.05 / 1.20 | 0.67 / 1.37 | 0.00 / 0.12 | 0.13 / 0.22 | 0.00 / 0.11 | 0.35 / 0.41 |
| 10–50% | 63 | 2038 | 86 | 1.68 / 9.66 | 0.00 / 0.82 | 0.52 / 1.01 | 0.00 / 0.19 | 0.16 / 0.21 | 0.00 / 0.00 | 0.46 / 0.76 |
| miss<10% | 169 | 13886 | 128 | 9.36 / 41.38 | 0.77 / 2.62 | 1.30 / 4.46 | 0.00 / 3.96 | – | – | 3.31 / 4.17 |
| mixed | 1 | 3100 | 160 | 2.73 / 2.73 | 0.00 / 0.00 | 0.92 / 0.92 | 1.29 / 1.29 | 0.22 / 0.22 | 0.00 / 0.00 | 0.23 / 0.23 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 5.12 | 2.71 [53%] | 0.20 [4%] | 0.92 [18%] | 0.01 [0%] | 0.04 [1%] | 0.37 [7%] | 0.00 [0%] | 0.84 [16%] | 0.00 [0%] | 0.03 [1%] |
| GPU≥50% | 217 | 2.70 | 1.51 [56%] | 0.08 [3%] | 0.43 [16%] | 0.02 [1%] | 0.00 [0%] | 0.07 [3%] | 0.00 [0%] | 0.55 [20%] | 0.00 [0%] | 0.04 [2%] |
| 10–50% | 63 | 2.03 | 1.17 [58%] | 0.01 [0%] | 0.11 [5%] | 0.01 [1%] | 0.00 [0%] | 0.18 [9%] | 0.00 [0%] | 0.54 [27%] | 0.00 [0%] | 0.01 [0%] |
| miss<10% | 169 | 11.04 | 5.50 [50%] | 0.51 [5%] | 2.88 [26%] | 0.02 [0%] | 0.00 [0%] | 1.22 [11%] | 0.00 [0%] | 0.65 [6%] | 0.00 [0%] | 0.25 [2%] |
| mixed | 1 | 2.44 | 0.00 [0%] | 0.03 [1%] | 0.20 [8%] | 0.00 [0%] | 0.00 [0%] | 1.29 [53%] | 0.00 [0%] | 0.92 [38%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 1.31 | 0.03 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 217 | 0.99 | 0.03 | 0.18 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 63 | 0.82 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 1.79 | 0.12 | 0.66 | 0.01 | 0.00 | 0.00 | 0.00 | 0.04 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 0.61 | 0.04 | 0.49 | 0.00 | 0.00 | 0.00 | 0.74 | 0.00 | 0.01 |
| GPU≥50% | 217 | 0.52 | 0.05 | 0.21 | 0.02 | 0.00 | 0.00 | 0.54 | 0.00 | 0.03 |
| 10–50% | 63 | 0.35 | 0.01 | 0.10 | 0.01 | 0.00 | 0.00 | 0.53 | 0.00 | 0.01 |
| miss<10% | 169 | 2.33 | 0.29 | 1.02 | 0.01 | 0.00 | 0.00 | 0.65 | 0.00 | 0.16 |
| mixed | 1 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.89 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 0.00 | 0.00 | 0.13 | 0.00 | 0.34 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 217 | 0.00 | 0.00 | 0.04 | 0.00 | 0.07 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 63 | 0.00 | 0.00 | 0.01 | 0.00 | 0.18 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 1.39 | 0.10 | 1.20 | 0.00 | 1.22 | 0.00 | 0.00 | 0.00 | 0.05 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 1.29 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 0.39 | 0.05 | 0.01 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.02 |
| GPU≥50% | 217 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1282 | 1278 / 0 / 4 | 384 | 387 | 244 (40–1093) | 0 (223) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5915 | 5915 / 0 / 0 | 128 | 1798 | 801 (111–1690) | 0 (0) |
| promotion after a load | 68 | 68 / 0 / 0 | 57 | 57 | 5 (0–14) | 0 (0) |

Requests refused at least once: 147 of 544; preemptions: 5; running requests that could not get their next chunk: 66.
Admitted external loads: 102; reservation passed at admission p50 0 / max 335 blocks; free blocks at admission p50 1236.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.645 |
| time with free blocks < 50% of the pool | 0.711 |
| time with free blocks < 25% of the pool | 0.558 |
| time with free blocks < 10% of the pool | 0.276 |
| time with free blocks < 5% of the pool | 0.149 |
| blocks held by loads in transfer, mean / max | 32 / 1536 |
| in-flight prefill reservation after schedule(), mean / max | 267 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.442 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 2.4 / 19 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 94 | 0.54 | 0.44 | 0.17 / 0.02 | 2.52 [43] | 7.39 [51] | 8.50 [32] | 4.68 [62] |
| GPU≥50% | 217 | 0.47 | 0.36 | 0.21 / 0.01 | 0.43 [114] | 4.51 [103] | 1.24 [104] | 2.67 [113] |
| 10–50% | 63 | 0.44 | 0.33 | 0.20 / 0.03 | 0.75 [35] | 3.82 [28] | 1.43 [29] | 1.89 [34] |
| miss<10% | 169 | 0.54 | 0.43 | 0.30 / 0.03 | 4.75 [78] | 12.46 [91] | 5.97 [90] | 12.12 [79] |
| mixed | 1 | 0.00 | 0.00 | 0.05 / 0.05 | 2.73 [1] | – | – | 2.73 [1] |
