## Admission analysis of `x08b-base` (544 requests, 22048 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 6178 | 384 | 18.72 / 43.07 | 5.44 / 7.14 | 7.70 / 9.89 | 0.00 / 0.61 | 0.77 / 0.83 | 0.00 / 0.27 | 0.38 / 0.49 |
| GPU≥50% | 212 | 6198 | 57 | 6.20 / 39.87 | 1.91 / 4.87 | 0.95 / 5.14 | 0.00 / 0.09 | 0.30 / 0.27 | 0.00 / 0.00 | 0.38 / 0.44 |
| 10–50% | 64 | 2103 | 87 | 10.84 / 34.59 | 0.97 / 4.45 | 1.29 / 6.15 | 0.00 / 0.14 | 1.72 / 1.07 | 1.04 / 0.76 | 0.76 / 0.92 |
| miss<10% | 167 | 13883 | 128 | 12.79 / 43.04 | 1.02 / 3.94 | 1.59 / 7.03 | 0.00 / 0.86 | – | – | 3.25 / 4.12 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 18.74 | 10.19 [54%] | 0.79 [4%] | 6.04 [32%] | 0.01 [0%] | 0.11 [1%] | 0.63 [3%] | 0.00 [0%] | 0.90 [5%] | 0.00 [0%] | 0.06 [0%] |
| GPU≥50% | 212 | 10.11 | 5.80 [57%] | 0.43 [4%] | 3.15 [31%] | 0.00 [0%] | 0.00 [0%] | 0.09 [1%] | 0.00 [0%] | 0.60 [6%] | 0.00 [0%] | 0.03 [0%] |
| 10–50% | 64 | 10.85 | 6.41 [59%] | 0.53 [5%] | 3.15 [29%] | 0.00 [0%] | 0.00 [0%] | 0.17 [2%] | 0.00 [0%] | 0.52 [5%] | 0.00 [0%] | 0.07 [1%] |
| miss<10% | 167 | 11.83 | 6.59 [56%] | 0.55 [5%] | 3.23 [27%] | 0.00 [0%] | 0.00 [0%] | 0.86 [7%] | 0.00 [0%] | 0.57 [5%] | 0.00 [0%] | 0.03 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 4.50 | 0.36 | 2.28 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 212 | 3.37 | 0.24 | 1.26 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 2.92 | 0.17 | 1.35 | 0.00 | 0.00 | 0.00 |
| miss<10% | 167 | 2.80 | 0.22 | 0.92 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 5.21 | 0.36 | 3.58 | 0.00 | 0.00 | 0.00 | 0.69 | 0.00 | 0.04 |
| GPU≥50% | 212 | 2.43 | 0.19 | 1.88 | 0.00 | 0.00 | 0.00 | 0.59 | 0.00 | 0.03 |
| 10–50% | 64 | 3.46 | 0.34 | 1.79 | 0.00 | 0.00 | 0.00 | 0.50 | 0.00 | 0.06 |
| miss<10% | 167 | 3.79 | 0.33 | 2.31 | 0.00 | 0.00 | 0.00 | 0.57 | 0.00 | 0.03 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 0.00 | 0.02 | 0.60 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 212 | 0.00 | 0.00 | 0.09 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.14 | 0.00 | 0.00 | 0.00 |
| miss<10% | 167 | 0.00 | 0.00 | 0.86 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 0.21 | 0.01 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.01 |
| GPU≥50% | 212 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.04 | 0.00 | 0.01 |
| miss<10% | 167 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1873 | 1865 / 0 / 8 | 384 | 425 | 216 (29–548) | 0 (162) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4383 | 4383 / 0 / 0 | 128 | 1080 | 642 (120–1233) | 0 (0) |
| promotion after a load | 85 | 85 / 0 / 0 | 128 | 151 | 61 (3–541) | 0 (0) |

Requests refused at least once: 123 of 544; preemptions: 5; running requests that could not get their next chunk: 11.
Admitted external loads: 112; reservation passed at admission p50 0 / max 326 blocks; free blocks at admission p50 1185.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.598 |
| time with free blocks < 50% of the pool | 0.639 |
| time with free blocks < 25% of the pool | 0.498 |
| time with free blocks < 10% of the pool | 0.272 |
| time with free blocks < 5% of the pool | 0.158 |
| blocks held by loads in transfer, mean / max | 26 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 250 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.414 |
| running requests, mean / max | 6.1 / 16 |
| waiting + kv-holding requests, mean / max | 5.3 / 34 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 101 | 0.56 | 0.49 | 0.14 / 0.03 | 17.76 [44] | 20.71 [57] | 11.75 [36] | 20.24 [65] |
| GPU≥50% | 212 | 0.47 | 0.42 | 0.56 / 0.03 | 0.58 [112] | 10.60 [100] | 1.61 [135] | 20.10 [77] |
| 10–50% | 64 | 0.47 | 0.36 | 0.52 / 0.03 | 3.77 [34] | 13.70 [30] | 1.46 [36] | 18.88 [28] |
| miss<10% | 167 | 0.49 | 0.42 | 0.56 / 0.04 | 4.33 [85] | 19.13 [82] | 9.27 [112] | 22.46 [55] |
