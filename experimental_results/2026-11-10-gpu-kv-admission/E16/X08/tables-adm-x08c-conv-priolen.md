## Admission analysis of `x08c-conv-priolen` (291 requests, 20605 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 7190 | 384 | 7.41 / 11.81 | 0.00 / 0.89 | 0.90 / 1.23 | 0.00 / 0.38 | 0.45 / 0.88 | 0.00 / 1.55 | 0.49 / 0.71 |
| GPU≥50% | 28 | 906 | 25 | 2.22 / 10.11 | 0.86 / 1.96 | 0.82 / 1.09 | 0.00 / 0.00 | – | – | 0.34 / 0.33 |
| 10–50% | 66 | 2103 | 92 | 2.11 / 11.22 | 0.00 / 1.08 | 0.76 / 1.43 | 0.00 / 0.10 | 0.19 / 0.57 | 0.00 / 2.49 | 0.51 / 0.74 |
| miss<10% | 186 | 13886 | 128 | 9.27 / 46.62 | 0.86 / 4.02 | 1.17 / 3.99 | 0.00 / 3.61 | – | – | 3.52 / 4.16 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 4.93 | 3.42 [69%] | 0.14 [3%] | 0.20 [4%] | 0.01 [0%] | 0.46 [9%] | 0.70 [14%] | 0.00 [0%] |
| GPU≥50% | 28 | 3.05 | 2.30 [75%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.76 [25%] | 0.00 [0%] |
| 10–50% | 66 | 2.75 | 1.94 [71%] | 0.03 [1%] | 0.08 [3%] | 0.00 [0%] | 0.10 [4%] | 0.59 [21%] | 0.00 [0%] |
| miss<10% | 186 | 11.61 | 6.47 [56%] | 0.42 [4%] | 2.79 [24%] | 0.00 [0%] | 1.22 [11%] | 0.71 [6%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.82 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 1.96 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 66 | 1.05 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 |
| miss<10% | 186 | 2.89 | 0.09 | 1.04 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.58 | 0.00 | 0.08 | 0.00 | 0.57 | 0.00 |
| GPU≥50% | 28 | 0.34 | 0.00 | 0.00 | 0.00 | 0.76 | 0.00 |
| 10–50% | 66 | 0.76 | 0.03 | 0.05 | 0.00 | 0.59 | 0.00 |
| miss<10% | 186 | 2.22 | 0.29 | 0.77 | 0.00 | 0.71 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.00 | 0.00 | 0.00 | 0.38 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 66 | 0.00 | 0.00 | 0.00 | 0.10 | 0.00 | 0.00 |
| miss<10% | 186 | 1.36 | 0.04 | 0.98 | 1.22 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 1.47 | 0.00 | 0.00 | 0.00 | 0.07 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 66 | 0.11 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 186 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 153 | 153 / 0 / 0 | 704 | 871 | 216 (23–401) | 0 (7) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6878 | 6878 / 0 / 0 | 128 | 1700 | 654 (138–1657) | 0 (0) |
| promotion after a load | 1 | 1 / 0 / 0 | 88 | 88 | 86 (86–86) | 0 (0) |

Requests refused at least once: 79 of 291; preemptions: 5; running requests that could not get their next chunk: 14.
Admitted external loads: 14; reservation passed at admission p50 0 / max 29 blocks; free blocks at admission p50 2600.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.622 |
| time with free blocks < 50% of the pool | 0.693 |
| time with free blocks < 25% of the pool | 0.519 |
| time with free blocks < 10% of the pool | 0.235 |
| time with free blocks < 5% of the pool | 0.101 |
| blocks held by loads in transfer, mean / max | 8 / 992 |
| in-flight prefill reservation after schedule(), mean / max | 281 / 1981 |
| steps whose running requests used the whole token budget (share of time) | 0.471 |
| running requests, mean / max | 6.1 / 14 |
| waiting + kv-holding requests, mean / max | 2.0 / 12 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 11 | 0.36 | 0.36 | 0.40 / 0.02 | 2.86 [7] | 8.38 [4] | 8.38 [6] | 2.86 [5] |
| GPU≥50% | 28 | 0.68 | 0.68 | 0.56 / 0.02 | 0.32 [9] | 5.20 [19] | 5.86 [16] | 2.22 [12] |
| 10–50% | 66 | 0.47 | 0.42 | 0.37 / 0.06 | 0.63 [35] | 5.24 [31] | 1.87 [42] | 2.66 [24] |
| miss<10% | 186 | 0.51 | 0.47 | 0.40 / 0.04 | 4.34 [92] | 11.70 [94] | 7.25 [109] | 11.19 [77] |
