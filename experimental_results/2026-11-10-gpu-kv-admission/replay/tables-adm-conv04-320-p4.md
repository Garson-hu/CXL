## Admission analysis of `conv04-320-p4` (599 requests, 87120 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 71 | 9974 | 544 | 0.71 / 4.30 | 0.00 / 0.03 | 0.03 / 0.31 | 0.00 / 0.39 | 0.12 / 0.39 | 0.00 / 0.00 | 0.23 / 0.58 |
| GPU≥50% | 54 | 901 | 25 | 0.17 / 2.21 | 0.00 / 0.00 | 0.03 / 0.32 | 0.00 / 0.07 | – | – | 0.12 / 0.28 |
| 10–50% | 133 | 2350 | 105 | 0.77 / 11.08 | 0.00 / 0.02 | 0.03 / 0.29 | 0.00 / 1.12 | 0.30 / 0.45 | 0.00 / 0.00 | 0.58 / 0.99 |
| miss<10% | 331 | 13689 | 128 | 5.02 / 23.66 | 0.00 / 0.02 | 0.03 / 0.29 | 0.00 / 2.95 | 0.05 / 0.04 | 0.00 / 0.00 | 3.09 / 4.05 |
| mixed | 10 | 1763 | 32 | 1.09 / 3.10 | 0.00 / 0.00 | 0.03 / 0.32 | 0.00 / 0.00 | 0.08 / 0.36 | 0.00 / 0.00 | 0.20 / 0.37 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 71 | 1.12 | 0.11 [10%] | 0.04 [4%] | 0.00 [0%] | 0.20 [18%] | 0.00 [0%] | 0.38 [34%] | 0.39 [35%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 54 | 0.40 | 0.00 [0%] | 0.01 [2%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.32 [79%] | 0.00 [0%] | 0.00 [0%] | 0.07 [19%] | 0.00 [0%] |
| 10–50% | 133 | 1.49 | 0.02 [1%] | 0.09 [6%] | 0.01 [1%] | 0.02 [2%] | 0.00 [0%] | 0.30 [20%] | 0.11 [8%] | 0.00 [0%] | 0.93 [62%] | 0.00 [0%] |
| miss<10% | 331 | 3.27 | 0.00 [0%] | 0.14 [4%] | 0.02 [1%] | 0.00 [0%] | 0.04 [1%] | 0.29 [9%] | 0.66 [20%] | 0.01 [0%] | 2.10 [64%] | 0.00 [0%] |
| mixed | 10 | 0.69 | 0.06 [9%] | 0.02 [3%] | 0.00 [0%] | 0.21 [31%] | 0.00 [0%] | 0.39 [57%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 71 | 0.00 | 0.03 | 0.00 | 0.00 |
| GPU≥50% | 54 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 133 | 0.00 | 0.02 | 0.00 | 0.00 |
| miss<10% | 331 | 0.00 | 0.02 | 0.00 | 0.00 |
| mixed | 10 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|
| host≥50% | 71 | 0.00 | 0.31 | 0.00 | 0.00 |
| GPU≥50% | 54 | 0.00 | 0.32 | 0.00 | 0.00 |
| 10–50% | 133 | 0.01 | 0.28 | 0.00 | 0.00 |
| miss<10% | 331 | 0.00 | 0.29 | 0.00 | 0.00 |
| mixed | 10 | 0.02 | 0.30 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 71 | 0.00 | 0.00 | 0.00 | 0.00 | 0.39 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.07 | 0.00 |
| 10–50% | 133 | 0.07 | 0.01 | 0.00 | 0.00 | 0.11 | 0.00 | 0.93 | 0.00 |
| miss<10% | 331 | 0.12 | 0.02 | 0.04 | 0.00 | 0.66 | 0.01 | 2.10 | 0.00 |
| mixed | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 71 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 54 | 0.00 | 0.00 | 0.00 |
| 10–50% | 133 | 0.00 | 0.00 | 0.00 |
| miss<10% | 331 | 0.00 | 0.00 | 0.00 |
| mixed | 10 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 747 | 747 / 0 / 0 | 128 | 1700 | 619 (37–1975) | 0 (0) |

Requests refused at least once: 10 of 599; preemptions: 4; running requests that could not get their next chunk: 9.
Admitted external loads: 101; reservation passed at admission p50 0 / max 1791 blocks; free blocks at admission p50 5783.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.263 |
| time with free blocks < 50% of the pool | 0.178 |
| time with free blocks < 25% of the pool | 0.096 |
| time with free blocks < 10% of the pool | 0.037 |
| time with free blocks < 5% of the pool | 0.015 |
| blocks held by loads in transfer, mean / max | 5 / 2992 |
| in-flight prefill reservation after schedule(), mean / max | 128 / 1903 |
| steps whose running requests used the whole token budget (share of time) | 0.117 |
| steps with a shortened token budget (share of time) | 0.047 |
| running requests, mean / max | 1.9 / 13 |
| waiting + kv-holding requests, mean / max | 0.3 / 7 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 71 | 0.41 | 0.00 | 0.79 / 0.38 | 0.28 [42] | 3.06 [29] | 0.49 [67] | 3.74 [4] |
| GPU≥50% | 54 | 0.41 | 0.00 | 0.71 / 0.30 | 0.12 [32] | 1.60 [22] | 0.15 [51] | 1.85 [3] |
| 10–50% | 133 | 0.37 | 0.00 | 0.79 / 0.35 | 0.38 [84] | 4.49 [49] | 0.73 [126] | 1.08 [7] |
| miss<10% | 331 | 0.39 | 0.00 | 0.80 / 0.39 | 2.55 [201] | 10.38 [130] | 4.95 [319] | 12.29 [12] |
| mixed | 10 | 0.40 | 0.00 | 0.74 / 0.28 | 0.26 [6] | 2.77 [4] | 0.30 [9] | 1.76 [1] |
