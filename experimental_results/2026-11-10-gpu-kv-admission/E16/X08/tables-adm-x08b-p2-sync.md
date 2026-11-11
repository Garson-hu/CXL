## Admission analysis of `x08b-p2-sync` (544 requests, 19927 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 6188 | 384 | 15.94 / 42.03 | 0.84 / 5.38 | 0.40 / 1.74 | 1.58 / 8.29 | 0.56 / 0.52 | 0.00 / 0.01 | 0.42 / 0.58 |
| GPU≥50% | 218 | 6201 | 55 | 1.73 / 29.23 | 0.00 / 2.80 | 0.35 / 1.42 | 0.19 / 3.76 | 0.58 / 0.49 | 0.00 / 0.01 | 0.31 / 0.36 |
| 10–50% | 64 | 2103 | 91 | 9.46 / 59.19 | 0.00 / 2.79 | 0.33 / 0.89 | 3.00 / 12.43 | 0.58 / 0.44 | 0.00 / 0.11 | 0.45 / 0.86 |
| miss<10% | 164 | 13883 | 128 | 19.83 / 57.37 | 0.00 / 3.30 | 0.33 / 0.58 | 11.89 / 15.48 | 0.51 / 0.51 | 0.00 / 0.00 | 3.66 / 4.58 |
| mixed | 1 | 4023 | 160 | 24.95 / 24.95 | 10.05 / 10.05 | 0.86 / 0.86 | 11.93 / 11.93 | 0.58 / 0.58 | 0.00 / 0.00 | 1.43 / 1.43 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 15.94 | 0.01 [0%] | 1.02 [6%] | 10.68 [67%] | 0.48 [3%] | 0.13 [1%] | 0.66 [4%] | 0.34 [2%] | 0.71 [4%] | 0.40 [3%] | 0.08 [0%] | 1.43 [9%] | 0.01 [0%] | 0.00 [0%] |
| GPU≥50% | 218 | 8.03 | 0.00 [0%] | 0.54 [7%] | 5.26 [65%] | 0.27 [3%] | 0.01 [0%] | 0.02 [0%] | 0.01 [0%] | 0.38 [5%] | 0.14 [2%] | 0.10 [1%] | 1.28 [16%] | 0.01 [0%] | 0.00 [0%] |
| 10–50% | 64 | 16.14 | 0.00 [0%] | 0.97 [6%] | 9.27 [57%] | 0.70 [4%] | 0.00 [0%] | 0.12 [1%] | 0.03 [0%] | 0.31 [2%] | 0.08 [1%] | 0.01 [0%] | 4.43 [27%] | 0.01 [0%] | 0.19 [1%] |
| miss<10% | 164 | 19.37 | 0.00 [0%] | 1.15 [6%] | 9.02 [47%] | 0.39 [2%] | 0.00 [0%] | 2.52 [13%] | 0.00 [0%] | 0.35 [2%] | 0.05 [0%] | 0.01 [0%] | 5.67 [29%] | 0.01 [0%] | 0.19 [1%] |
| mixed | 1 | 23.40 | 0.00 [0%] | 1.68 [7%] | 16.14 [69%] | 0.00 [0%] | 0.17 [1%] | 0.00 [0%] | 0.00 [0%] | 1.27 [5%] | 2.33 [10%] | 0.00 [0%] | 1.83 [8%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.00 | 0.40 | 4.73 | 0.24 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 218 | 0.00 | 0.24 | 2.47 | 0.08 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.24 | 2.31 | 0.23 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.26 | 2.91 | 0.12 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 1.29 | 8.75 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.15 | 1.10 | 0.02 | 0.47 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 218 | 0.12 | 0.92 | 0.03 | 0.35 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.09 | 0.39 | 0.10 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.04 | 0.17 | 0.02 | 0.35 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.85 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.42 | 4.77 | 0.20 | 0.65 | 0.34 | 0.00 | 0.40 | 0.08 | 1.43 | 0.00 | 0.00 |
| GPU≥50% | 218 | 0.18 | 1.86 | 0.17 | 0.02 | 0.01 | 0.00 | 0.14 | 0.10 | 1.27 | 0.00 | 0.00 |
| 10–50% | 64 | 0.63 | 6.56 | 0.36 | 0.12 | 0.03 | 0.00 | 0.08 | 0.01 | 4.42 | 0.01 | 0.19 |
| miss<10% | 164 | 0.85 | 5.94 | 0.25 | 2.52 | 0.00 | 0.00 | 0.05 | 0.01 | 5.67 | 0.01 | 0.19 |
| mixed | 1 | 0.38 | 7.39 | 0.00 | 0.00 | 0.00 | 0.00 | 2.32 | 0.00 | 1.83 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 218 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1405 | 1310 / 0 / 95 | 384 | 446 | 223 (46–799) | 0 (1726) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6278 | 6278 / 0 / 0 | 128 | 1201 | 741 (147–1590) | 0 (600) |
| promotion after a load | 18 | 18 / 0 / 0 | 39 | 39 | 4 (0–9) | 0 (0) |

Requests refused at least once: 123 of 544; preemptions: 14; running requests that could not get their next chunk: 14.
Admitted external loads: 128; reservation passed at admission p50 580 / max 1858 blocks; free blocks at admission p50 1857.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.653 |
| time with free blocks < 50% of the pool | 0.714 |
| time with free blocks < 25% of the pool | 0.583 |
| time with free blocks < 10% of the pool | 0.291 |
| time with free blocks < 5% of the pool | 0.142 |
| blocks held by loads in transfer, mean / max | 18 / 3408 |
| in-flight prefill reservation after schedule(), mean / max | 336 / 1908 |
| steps whose running requests used the whole token budget (share of time) | 0.039 |
| steps with a shortened token budget (share of time) | 0.172 |
| running requests, mean / max | 7.0 / 16 |
| waiting + kv-holding requests, mean / max | 5.8 / 26 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.76 | 0.00 | 0.15 / 0.03 | 9.03 [23] | 19.56 [74] | 1.84 [22] | 19.64 [75] |
| GPU≥50% | 218 | 0.66 | 0.00 | 0.24 / 0.03 | 0.23 [74] | 3.91 [144] | 0.74 [107] | 9.57 [111] |
| 10–50% | 64 | 0.59 | 0.00 | 0.23 / 0.03 | 0.64 [26] | 23.07 [38] | 0.86 [28] | 23.15 [36] |
| miss<10% | 164 | 0.71 | 0.00 | 0.25 / 0.05 | 6.19 [48] | 25.25 [116] | 12.33 [83] | 29.54 [81] |
| mixed | 1 | 1.00 | 0.00 | 0.10 / 0.10 | – | 24.95 [1] | – | 24.95 [1] |
