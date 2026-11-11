## Admission analysis of `x08-skip3` (544 requests, 21910 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 6168 | 384 | 13.44 / 37.16 | 3.14 / 5.03 | 0.92 / 3.46 | 0.71 / 5.60 | 0.52 / 0.78 | 0.00 / 0.25 | 0.36 / 0.43 |
| GPU≥50% | 204 | 6251 | 62 | 4.78 / 35.85 | 0.93 / 4.21 | 0.75 / 2.15 | 0.00 / 2.61 | 0.91 / 0.54 | 0.00 / 0.00 | 0.43 / 0.51 |
| 10–50% | 64 | 2103 | 87 | 5.45 / 28.88 | 1.42 / 4.77 | 0.91 / 2.32 | 0.00 / 2.19 | 1.50 / 1.38 | 1.64 / 0.97 | 0.84 / 0.97 |
| miss<10% | 164 | 13883 | 128 | 12.63 / 43.03 | 1.20 / 4.24 | 0.85 / 3.30 | 0.00 / 4.55 | 1.28 / 1.28 | 1.67 / 1.67 | 3.31 / 4.16 |
| mixed | 6 | 6686 | 191 | 44.66 / 45.28 | 1.15 / 2.03 | 1.32 / 7.73 | 41.70 / 21.29 | 0.90 / 0.79 | 0.38 / 0.27 | 0.50 / 0.57 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 15.12 | 8.62 [57%] | 0.75 [5%] | 3.31 [22%] | 0.18 [1%] | 0.21 [1%] | 0.31 [2%] | 0.00 [0%] | 0.96 [6%] | 0.69 [5%] | 0.00 [0%] | 0.09 [1%] |
| GPU≥50% | 204 | 8.99 | 5.19 [58%] | 0.54 [6%] | 2.09 [23%] | 0.18 [2%] | 0.00 [0%] | 0.03 [0%] | 0.00 [0%] | 0.48 [5%] | 0.39 [4%] | 0.00 [0%] | 0.08 [1%] |
| 10–50% | 64 | 9.42 | 5.21 [55%] | 0.54 [6%] | 2.23 [24%] | 0.22 [2%] | 0.00 [0%] | 0.06 [1%] | 0.00 [0%] | 0.53 [6%] | 0.48 [5%] | 0.00 [0%] | 0.16 [2%] |
| miss<10% | 164 | 12.10 | 6.69 [55%] | 0.61 [5%] | 2.39 [20%] | 0.15 [1%] | 0.00 [0%] | 0.83 [7%] | 0.00 [0%] | 0.59 [5%] | 0.69 [6%] | 0.00 [0%] | 0.15 [1%] |
| mixed | 6 | 32.11 | 15.15 [47%] | 0.88 [3%] | 12.98 [40%] | 0.99 [3%] | 0.11 [0%] | 0.68 [2%] | 0.00 [0%] | 0.82 [3%] | 0.47 [1%] | 0.02 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 3.64 | 0.28 | 1.09 | 0.02 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 204 | 2.80 | 0.14 | 1.22 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 3.01 | 0.10 | 1.59 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 3.05 | 0.18 | 0.96 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 1.83 | 0.20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 2.00 | 0.23 | 0.43 | 0.00 | 0.74 | 0.00 | 0.00 | 0.05 |
| GPU≥50% | 204 | 1.12 | 0.24 | 0.26 | 0.00 | 0.47 | 0.00 | 0.00 | 0.06 |
| 10–50% | 64 | 1.15 | 0.30 | 0.25 | 0.00 | 0.50 | 0.00 | 0.00 | 0.11 |
| miss<10% | 164 | 1.92 | 0.31 | 0.42 | 0.00 | 0.58 | 0.00 | 0.00 | 0.07 |
| mixed | 6 | 3.26 | 0.11 | 3.31 | 0.25 | 0.79 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 2.60 | 0.19 | 1.65 | 0.16 | 0.28 | 0.00 | 0.00 | 0.69 | 0.00 | 0.01 |
| GPU≥50% | 204 | 1.27 | 0.16 | 0.60 | 0.13 | 0.03 | 0.00 | 0.00 | 0.39 | 0.00 | 0.03 |
| 10–50% | 64 | 0.98 | 0.13 | 0.39 | 0.16 | 0.03 | 0.00 | 0.00 | 0.48 | 0.00 | 0.03 |
| miss<10% | 164 | 1.71 | 0.12 | 1.01 | 0.11 | 0.82 | 0.00 | 0.00 | 0.69 | 0.00 | 0.09 |
| mixed | 6 | 9.79 | 0.34 | 9.39 | 0.74 | 0.54 | 0.00 | 0.00 | 0.47 | 0.01 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 0.14 | 0.00 | 0.07 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 204 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.14 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 795 | 794 / 0 / 1 | 384 | 418 | 314 (124–569) | 0 (970) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4730 | 4316 / 0 / 414 | 128 | 1394 | 663 (173–1479) | 0 (600) |
| promotion after a load | 173 | 173 / 0 / 0 | 128 | 649 | 193 (8–622) | 0 (0) |

Requests refused at least once: 78 of 544; preemptions: 6; running requests that could not get their next chunk: 12.
Admitted external loads: 121; reservation passed at admission p50 0 / max 231 blocks; free blocks at admission p50 920.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.602 |
| time with free blocks < 50% of the pool | 0.661 |
| time with free blocks < 25% of the pool | 0.504 |
| time with free blocks < 10% of the pool | 0.245 |
| time with free blocks < 5% of the pool | 0.109 |
| blocks held by loads in transfer, mean / max | 31 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 248 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.412 |
| running requests, mean / max | 6.2 / 16 |
| waiting + kv-holding requests, mean / max | 4.9 / 34 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 0.60 | 0.50 | 0.20 / 0.06 | 9.65 [42] | 16.26 [64] | 11.87 [43] | 17.40 [63] |
| GPU≥50% | 204 | 0.47 | 0.43 | 0.52 / 0.07 | 0.38 [108] | 9.46 [96] | 1.61 [130] | 18.39 [74] |
| 10–50% | 64 | 0.45 | 0.39 | 0.27 / 0.03 | 3.95 [35] | 7.04 [29] | 1.48 [34] | 19.57 [30] |
| miss<10% | 164 | 0.52 | 0.43 | 0.47 / 0.05 | 4.16 [78] | 17.77 [86] | 9.77 [107] | 22.42 [57] |
| mixed | 6 | 1.00 | 0.50 | 0.09 / 0.00 | – | 44.66 [6] | – | 44.66 [6] |
