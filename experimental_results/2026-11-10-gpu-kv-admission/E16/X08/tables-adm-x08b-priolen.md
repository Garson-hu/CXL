## Admission analysis of `x08b-priolen` (544 requests, 20488 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 6171 | 384 | 4.40 / 12.55 | 0.00 / 1.28 | 0.90 / 1.74 | 0.00 / 0.44 | 0.43 / 0.72 | 0.00 / 0.38 | 0.43 / 0.55 |
| GPU≥50% | 209 | 6253 | 43 | 1.85 / 11.82 | 0.00 / 1.22 | 0.59 / 1.27 | 0.00 / 0.11 | 0.13 / 0.13 | 0.00 / 0.00 | 0.34 / 0.40 |
| 10–50% | 63 | 2038 | 87 | 1.86 / 9.06 | 0.00 / 0.90 | 0.56 / 0.78 | 0.00 / 0.08 | 0.20 / 0.52 | 0.00 / 1.89 | 0.51 / 0.71 |
| miss<10% | 169 | 13996 | 128 | 8.76 / 38.60 | 0.76 / 2.28 | 1.43 / 4.66 | 0.00 / 3.56 | – | – | 3.20 / 4.15 |
| mixed | 1 | 3158 | 160 | 2.54 / 2.54 | 0.99 / 0.99 | 0.84 / 0.84 | 0.11 / 0.11 | 0.13 / 0.13 | 0.00 / 0.00 | 0.24 / 0.24 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 4.55 | 2.53 [56%] | 0.22 [5%] | 0.60 [13%] | 0.00 [0%] | 0.04 [1%] | 0.29 [6%] | 0.00 [0%] | 0.83 [18%] | 0.00 [0%] | 0.04 [1%] |
| GPU≥50% | 209 | 2.59 | 1.52 [59%] | 0.08 [3%] | 0.38 [14%] | 0.00 [0%] | 0.00 [0%] | 0.07 [3%] | 0.00 [0%] | 0.52 [20%] | 0.00 [0%] | 0.03 [1%] |
| 10–50% | 63 | 1.87 | 1.09 [59%] | 0.01 [1%] | 0.10 [5%] | 0.00 [0%] | 0.00 [0%] | 0.10 [6%] | 0.00 [0%] | 0.54 [29%] | 0.00 [0%] | 0.02 [1%] |
| miss<10% | 169 | 10.49 | 5.28 [50%] | 0.46 [4%] | 2.59 [25%] | 0.00 [0%] | 0.00 [0%] | 1.32 [13%] | 0.00 [0%] | 0.66 [6%] | 0.00 [0%] | 0.19 [2%] |
| mixed | 1 | 2.07 | 0.99 [48%] | 0.00 [0%] | 0.11 [5%] | 0.00 [0%] | 0.00 [0%] | 0.11 [5%] | 0.00 [0%] | 0.87 [42%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 1.24 | 0.03 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 209 | 1.02 | 0.03 | 0.15 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 63 | 0.78 | 0.01 | 0.09 | 0.00 | 0.00 | 0.00 | 0.02 |
| miss<10% | 169 | 1.80 | 0.08 | 0.38 | 0.00 | 0.00 | 0.00 | 0.02 |
| mixed | 1 | 0.99 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 0.63 | 0.06 | 0.28 | 0.00 | 0.00 | 0.00 | 0.74 | 0.00 | 0.03 |
| GPU≥50% | 209 | 0.50 | 0.05 | 0.19 | 0.00 | 0.00 | 0.00 | 0.52 | 0.00 | 0.01 |
| 10–50% | 63 | 0.24 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.53 | 0.00 | 0.00 |
| miss<10% | 169 | 2.27 | 0.31 | 1.28 | 0.00 | 0.00 | 0.00 | 0.66 | 0.00 | 0.14 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.84 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 0.00 | 0.00 | 0.14 | 0.00 | 0.29 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 209 | 0.00 | 0.00 | 0.03 | 0.00 | 0.07 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 63 | 0.00 | 0.00 | 0.00 | 0.00 | 0.08 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 1.21 | 0.08 | 0.92 | 0.00 | 1.32 | 0.00 | 0.00 | 0.00 | 0.03 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.11 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 0.32 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 209 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 |
| miss<10% | 169 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 949 | 945 / 0 / 4 | 384 | 387 | 200 (47–354) | 0 (223) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6590 | 6590 / 0 / 0 | 128 | 1976 | 755 (155–1651) | 0 (0) |
| promotion after a load | 17 | 17 / 0 / 0 | 128 | 661 | 359 (355–365) | 0 (0) |

Requests refused at least once: 139 of 544; preemptions: 6; running requests that could not get their next chunk: 17.
Admitted external loads: 109; reservation passed at admission p50 0 / max 238 blocks; free blocks at admission p50 1174.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.639 |
| time with free blocks < 50% of the pool | 0.711 |
| time with free blocks < 25% of the pool | 0.532 |
| time with free blocks < 10% of the pool | 0.267 |
| time with free blocks < 5% of the pool | 0.145 |
| blocks held by loads in transfer, mean / max | 29 / 1536 |
| in-flight prefill reservation after schedule(), mean / max | 273 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.444 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 2.3 / 17 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 0.51 | 0.45 | 0.16 / 0.03 | 2.42 [50] | 7.18 [52] | 7.67 [33] | 3.31 [69] |
| GPU≥50% | 209 | 0.46 | 0.35 | 0.38 / 0.02 | 0.42 [113] | 4.81 [96] | 1.46 [110] | 2.04 [99] |
| 10–50% | 63 | 0.52 | 0.35 | 0.23 / 0.01 | 0.62 [30] | 2.89 [33] | 1.97 [30] | 1.79 [33] |
| miss<10% | 169 | 0.50 | 0.43 | 0.32 / 0.02 | 5.92 [84] | 12.47 [85] | 6.92 [93] | 10.82 [76] |
| mixed | 1 | 1.00 | 1.00 | 0.06 / 0.06 | – | 2.54 [1] | – | 2.54 [1] |
