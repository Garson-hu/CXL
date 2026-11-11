## Admission analysis of `t06-priolen` (853 requests, 46345 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 6179 | 384 | 3.42 / 12.28 | 0.69 / 1.61 | 1.01 / 1.26 | 0.00 / 0.21 | 0.46 / 0.71 | 0.00 / 0.54 | 0.33 / 0.51 |
| GPU≥50% | 378 | 6247 | 195 | 1.67 / 11.28 | 0.00 / 1.03 | 0.71 / 1.39 | 0.00 / 0.01 | 0.13 / 0.22 | 0.00 / 0.00 | 0.30 / 0.42 |
| 10–50% | 89 | 2103 | 87 | 1.33 / 13.01 | 0.00 / 1.48 | 0.41 / 2.35 | 0.00 / 0.11 | 0.89 / 0.84 | 0.00 / 0.49 | 0.39 / 0.71 |
| miss<10% | 261 | 13996 | 128 | 7.25 / 31.98 | 0.00 / 1.62 | 0.75 / 2.84 | 0.00 / 1.15 | 0.01 / 0.01 | 0.00 / 0.00 | 3.25 / 4.16 |
| mixed | 4 | 1661 | 32 | 7.75 / 14.53 | 2.92 / 3.23 | 1.27 / 1.83 | 0.00 / 0.35 | 0.89 / 0.69 | 0.00 / 0.31 | 0.39 / 0.47 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 4.33 | 2.71 [63%] | 0.14 [3%] | 0.34 [8%] | 0.00 [0%] | 0.12 [3%] | 0.16 [4%] | 0.00 [0%] | 0.85 [20%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 378 | 2.44 | 1.72 [71%] | 0.11 [5%] | 0.03 [1%] | 0.00 [0%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.56 [23%] | 0.00 [0%] | 0.00 [0%] |
| 10–50% | 89 | 4.02 | 2.61 [65%] | 0.09 [2%] | 0.66 [16%] | 0.00 [0%] | 0.01 [0%] | 0.11 [3%] | 0.00 [0%] | 0.54 [13%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 261 | 5.62 | 3.39 [60%] | 0.39 [7%] | 0.73 [13%] | 0.00 [0%] | 0.00 [0%] | 0.56 [10%] | 0.00 [0%] | 0.55 [10%] | 0.00 [0%] | 0.00 [0%] |
| mixed | 4 | 6.41 | 4.47 [70%] | 0.08 [1%] | 0.24 [4%] | 0.00 [0%] | 0.10 [2%] | 0.35 [6%] | 0.00 [0%] | 1.16 [18%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 1.55 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 378 | 0.98 | 0.03 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 1.31 | 0.02 | 0.15 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 261 | 1.39 | 0.09 | 0.14 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 3.23 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 0.33 | 0.01 | 0.14 | 0.00 | 0.00 | 0.77 | 0.00 | 0.00 |
| GPU≥50% | 378 | 0.74 | 0.08 | 0.01 | 0.00 | 0.00 | 0.56 | 0.00 | 0.00 |
| 10–50% | 89 | 1.26 | 0.06 | 0.51 | 0.00 | 0.00 | 0.53 | 0.00 | 0.00 |
| miss<10% | 261 | 1.66 | 0.28 | 0.36 | 0.00 | 0.00 | 0.55 | 0.00 | 0.00 |
| mixed | 4 | 0.75 | 0.00 | 0.00 | 0.00 | 0.00 | 1.08 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 0.00 | 0.00 | 0.05 | 0.16 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 378 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.00 | 0.00 | 0.00 | 0.11 | 0.00 | 0.00 | 0.00 |
| miss<10% | 261 | 0.35 | 0.02 | 0.23 | 0.56 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.35 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 0.48 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 378 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 261 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.31 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1071 | 1070 / 0 / 1 | 960 | 1330 | 241 (18–1947) | 0 (246) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4568 | 4568 / 0 / 0 | 128 | 1980 | 889 (306–1849) | 0 (0) |
| promotion after a load | 3 | 3 / 0 / 0 | 102 | 102 | 0 (0–2) | 0 (0) |

Requests refused at least once: 66 of 853; preemptions: 4; running requests that could not get their next chunk: 26.
Admitted external loads: 139; reservation passed at admission p50 0 / max 307 blocks; free blocks at admission p50 4162.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.412 |
| time with free blocks < 50% of the pool | 0.392 |
| time with free blocks < 25% of the pool | 0.229 |
| time with free blocks < 10% of the pool | 0.096 |
| time with free blocks < 5% of the pool | 0.045 |
| blocks held by loads in transfer, mean / max | 24 / 2400 |
| in-flight prefill reservation after schedule(), mean / max | 201 / 1992 |
| steps whose running requests used the whole token budget (share of time) | 0.328 |
| running requests, mean / max | 3.9 / 16 |
| waiting + kv-holding requests, mean / max | 1.3 / 14 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 121 | 0.60 | 0.53 | 0.69 / 0.08 | 1.01 [48] | 6.21 [73] | 3.35 [89] | 5.23 [32] |
| GPU≥50% | 378 | 0.50 | 0.43 | 0.69 / 0.31 | 0.22 [190] | 4.59 [188] | 1.63 [346] | 1.75 [32] |
| 10–50% | 89 | 0.43 | 0.38 | 0.71 / 0.28 | 0.46 [51] | 5.91 [38] | 1.39 [81] | 0.98 [8] |
| miss<10% | 261 | 0.44 | 0.37 | 0.74 / 0.27 | 3.17 [147] | 11.17 [114] | 6.98 [235] | 10.20 [26] |
| mixed | 4 | 0.75 | 0.75 | 0.75 / 0.13 | 1.99 [1] | 7.75 [3] | 7.75 [3] | 4.45 [1] |
