## Admission analysis of `t06-base` (853 requests, 46191 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 6338 | 384 | 13.42 / 47.67 | 2.55 / 5.26 | 2.74 / 9.86 | 0.00 / 0.41 | 0.65 / 0.85 | 0.00 / 0.41 | 0.32 / 0.47 |
| GPU≥50% | 374 | 6192 | 196 | 2.12 / 26.70 | 0.00 / 2.02 | 0.76 / 3.52 | 0.00 / 0.04 | 0.15 / 0.21 | 0.00 / 0.00 | 0.29 / 0.42 |
| 10–50% | 88 | 2103 | 87 | 1.77 / 38.41 | 0.00 / 2.52 | 0.61 / 4.16 | 0.00 / 0.01 | 1.21 / 1.01 | 2.00 / 1.14 | 0.51 / 0.71 |
| miss<10% | 262 | 14081 | 128 | 8.55 / 39.95 | 0.00 / 2.92 | 0.85 / 4.56 | 0.00 / 0.47 | 0.01 / 0.01 | 0.00 / 0.00 | 3.23 / 4.16 |
| mixed | 8 | 6168 | 208 | 12.39 / 53.14 | 4.00 / 7.26 | 1.31 / 9.26 | 0.00 / 0.38 | 1.58 / 1.02 | 1.49 / 1.16 | 0.95 / 0.74 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 16.79 | 9.95 [59%] | 0.71 [4%] | 4.44 [26%] | 0.19 [1%] | 0.44 [3%] | 1.06 [6%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 374 | 5.58 | 3.51 [63%] | 0.34 [6%] | 1.11 [20%] | 0.00 [0%] | 0.03 [1%] | 0.58 [10%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 88 | 6.79 | 4.23 [62%] | 0.40 [6%] | 1.60 [24%] | 0.01 [0%] | 0.01 [0%] | 0.54 [8%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 262 | 7.95 | 4.80 [60%] | 0.42 [5%] | 1.66 [21%] | 0.00 [0%] | 0.47 [6%] | 0.60 [8%] | 0.00 [0%] | 0.00 [0%] |
| mixed | 8 | 19.07 | 11.58 [61%] | 0.85 [4%] | 4.86 [25%] | 0.07 [0%] | 0.38 [2%] | 1.33 [7%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 3.93 | 0.19 | 1.14 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 374 | 1.58 | 0.10 | 0.33 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 88 | 2.05 | 0.12 | 0.35 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 262 | 2.20 | 0.13 | 0.59 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 8 | 5.38 | 0.31 | 1.56 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 5.40 | 0.49 | 3.12 | 0.00 | 0.85 | 0.00 | 0.00 |
| GPU≥50% | 374 | 1.92 | 0.23 | 0.78 | 0.00 | 0.58 | 0.00 | 0.01 |
| 10–50% | 88 | 2.11 | 0.26 | 1.25 | 0.00 | 0.54 | 0.00 | 0.00 |
| miss<10% | 262 | 2.60 | 0.29 | 1.07 | 0.00 | 0.60 | 0.00 | 0.00 |
| mixed | 8 | 4.60 | 0.29 | 3.16 | 0.00 | 1.21 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|
| host≥50% | 121 | 0.00 | 0.00 | 0.41 | 0.00 | 0.00 |
| GPU≥50% | 374 | 0.00 | 0.01 | 0.03 | 0.00 | 0.00 |
| 10–50% | 88 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |
| miss<10% | 262 | 0.00 | 0.00 | 0.47 | 0.00 | 0.00 |
| mixed | 8 | 0.00 | 0.00 | 0.38 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 0.33 | 0.01 | 0.04 | 0.00 | 0.03 | 0.00 | 0.00 |
| GPU≥50% | 374 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 88 | 0.05 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 262 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 8 | 1.02 | 0.14 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1483 | 1483 / 0 / 0 | 384 | 443 | 242 (107–1037) | 0 (149) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4246 | 4246 / 0 / 0 | 128 | 1943 | 775 (189–1856) | 0 (0) |
| promotion after a load | 117 | 117 / 0 / 0 | 106 | 106 | 81 (10–99) | 0 (0) |

Requests refused at least once: 87 of 853; preemptions: 3; running requests that could not get their next chunk: 7.
Admitted external loads: 140; reservation passed at admission p50 0 / max 326 blocks; free blocks at admission p50 2755.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.405 |
| time with free blocks < 50% of the pool | 0.381 |
| time with free blocks < 25% of the pool | 0.217 |
| time with free blocks < 10% of the pool | 0.094 |
| time with free blocks < 5% of the pool | 0.047 |
| blocks held by loads in transfer, mean / max | 21 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 196 / 1991 |
| steps whose running requests used the whole token budget (share of time) | 0.322 |
| running requests, mean / max | 3.6 / 16 |
| waiting + kv-holding requests, mean / max | 2.7 / 30 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 0.74 | 0.66 | 0.56 / 0.14 | 1.15 [32] | 16.78 [89] | 9.73 [97] | 41.11 [24] |
| GPU≥50% | 374 | 0.47 | 0.40 | 0.74 / 0.31 | 0.23 [199] | 6.84 [175] | 1.53 [340] | 18.60 [34] |
| 10–50% | 88 | 0.43 | 0.38 | 0.71 / 0.33 | 0.57 [50] | 8.97 [38] | 1.76 [82] | 44.08 [6] |
| miss<10% | 262 | 0.45 | 0.38 | 0.74 / 0.29 | 3.55 [143] | 14.13 [119] | 7.76 [238] | 37.12 [24] |
| mixed | 8 | 0.75 | 0.75 | 0.85 / 0.05 | 53.14 [2] | 12.39 [6] | 9.97 [6] | 53.14 [2] |
