## Admission analysis of `conv04-320-priolen` (599 requests, 85650 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 64 | 9586 | 544 | 0.80 / 21.26 | 0.00 / 0.69 | 0.03 / 1.58 | 0.00 / 0.81 | 0.11 / 0.43 | 0.00 / 0.69 | 0.19 / 0.50 |
| GPU≥50% | 54 | 901 | 26 | 0.16 / 7.12 | 0.00 / 0.90 | 0.04 / 0.55 | 0.00 / 0.00 | – | – | 0.11 / 0.24 |
| 10–50% | 131 | 2293 | 103 | 0.77 / 10.60 | 0.00 / 0.80 | 0.03 / 0.91 | 0.00 / 0.01 | 0.10 / 0.51 | 0.00 / 1.39 | 0.40 / 0.74 |
| miss<10% | 340 | 13883 | 128 | 5.02 / 19.89 | 0.00 / 1.09 | 0.03 / 1.49 | 0.00 / 0.44 | 0.05 / 0.04 | 0.00 / 0.00 | 3.07 / 3.87 |
| mixed | 10 | 1763 | 32 | 1.87 / 8.71 | 0.00 / 0.85 | 0.76 / 0.62 | 0.00 / 0.00 | 0.08 / 0.50 | 0.00 / 0.53 | 0.20 / 0.48 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 64 | 4.20 | 2.60 [62%] | 0.09 [2%] | 0.51 [12%] | 0.00 [0%] | 0.11 [3%] | 0.38 [9%] | 0.00 [0%] | 0.51 [12%] | 0.00 [0%] |
| GPU≥50% | 54 | 1.45 | 0.83 [57%] | 0.02 [1%] | 0.17 [12%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.43 [30%] | 0.00 [0%] |
| 10–50% | 131 | 1.94 | 1.26 [65%] | 0.04 [2%] | 0.14 [7%] | 0.00 [0%] | 0.01 [0%] | 0.09 [5%] | 0.00 [0%] | 0.40 [21%] | 0.00 [0%] |
| miss<10% | 340 | 3.03 | 1.88 [62%] | 0.11 [4%] | 0.31 [10%] | 0.00 [0%] | 0.00 [0%] | 0.28 [9%] | 0.00 [0%] | 0.46 [15%] | 0.00 [0%] |
| mixed | 10 | 2.50 | 1.86 [74%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.12 [5%] | 0.00 [0%] | 0.00 [0%] | 0.52 [21%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 64 | 0.66 | 0.03 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 54 | 0.71 | 0.02 | 0.17 | 0.00 | 0.00 |
| 10–50% | 131 | 0.71 | 0.02 | 0.07 | 0.00 | 0.00 |
| miss<10% | 340 | 1.04 | 0.04 | 0.01 | 0.00 | 0.00 |
| mixed | 10 | 0.85 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | own:resv | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 64 | 0.91 | 0.04 | 0.20 | 0.00 | 0.00 | 0.44 |
| GPU≥50% | 54 | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.43 |
| 10–50% | 131 | 0.45 | 0.01 | 0.07 | 0.00 | 0.00 | 0.39 |
| miss<10% | 340 | 0.77 | 0.06 | 0.21 | 0.00 | 0.00 | 0.46 |
| mixed | 10 | 0.16 | 0.00 | 0.00 | 0.00 | 0.00 | 0.47 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 64 | 0.27 | 0.02 | 0.14 | 0.38 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 131 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.06 | 0.01 | 0.10 | 0.28 | 0.00 | 0.00 | 0.00 |
| mixed | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 64 | 0.54 | 0.00 | 0.14 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 131 | 0.07 | 0.00 | 0.00 | 0.00 | 0.08 | 0.00 |
| miss<10% | 340 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 10 | 0.53 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 723 | 722 / 0 / 1 | 1504 | 1505 | 241 (100–1845) | 0 (1140) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3293 | 3293 / 0 / 0 | 128 | 1980 | 919 (347–1885) | 0 (0) |
| promotion after a load | 384 | 384 / 0 / 0 | 128 | 495 | 99 (42–588) | 0 (0) |

Requests refused at least once: 37 of 599; preemptions: 3; running requests that could not get their next chunk: 16.
Admitted external loads: 92; reservation passed at admission p50 0 / max 1140 blocks; free blocks at admission p50 5630.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.268 |
| time with free blocks < 50% of the pool | 0.181 |
| time with free blocks < 25% of the pool | 0.096 |
| time with free blocks < 10% of the pool | 0.038 |
| time with free blocks < 5% of the pool | 0.017 |
| blocks held by loads in transfer, mean / max | 10 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 123 / 2009 |
| steps whose running requests used the whole token budget (share of time) | 0.209 |
| running requests, mean / max | 1.9 / 13 |
| waiting + kv-holding requests, mean / max | 0.3 / 7 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 64 | 0.36 | 0.28 | 0.75 / 0.35 | 0.29 [41] | 9.63 [23] | 0.60 [61] | 10.33 [3] |
| GPU≥50% | 54 | 0.33 | 0.31 | 0.73 / 0.32 | 0.13 [36] | 3.78 [18] | 0.16 [52] | 15.76 [2] |
| 10–50% | 131 | 0.32 | 0.27 | 0.80 / 0.36 | 0.41 [89] | 4.56 [42] | 0.72 [125] | 8.18 [6] |
| miss<10% | 340 | 0.36 | 0.34 | 0.80 / 0.39 | 2.80 [216] | 9.57 [124] | 4.81 [332] | 24.24 [8] |
| mixed | 10 | 0.40 | 0.40 | 0.78 / 0.52 | 0.30 [6] | 8.61 [4] | 1.87 [10] | – |
