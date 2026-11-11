## Admission analysis of `e-tool08-120-big-p1` (543 requests, 16358 engine steps, pool 19919 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 24 | 3954 | 160 | 14.26 / 24.27 | 4.36 / 3.66 | 0.60 / 3.84 | 0.00 / 0.00 | 1.31 / 1.20 | 2.66 / 2.71 | 0.40 / 0.53 |
| GPU≥50% | 292 | 6214 | 176 | 4.36 / 42.88 | 0.00 / 3.00 | 0.58 / 2.05 | 0.26 / 7.96 | 1.12 / 1.12 | 6.73 / 6.73 | 0.48 / 0.55 |
| 10–50% | 64 | 2103 | 96 | 10.07 / 56.65 | 0.00 / 1.45 | 0.59 / 1.28 | 1.84 / 12.91 | 1.18 / 0.91 | 0.52 / 0.88 | 0.70 / 1.09 |
| miss<10% | 163 | 13883 | 128 | 18.52 / 52.08 | 0.00 / 2.22 | 0.51 / 1.22 | 9.46 / 12.95 | 1.10 / 1.10 | 3.10 / 3.10 | 4.46 / 5.18 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 24 | 11.41 | 0.02 [0%] | 0.29 [3%] | 0.17 [1%] | 0.75 [7%] | 0.00 [0%] | 10.18 [89%] |
| GPU≥50% | 292 | 13.04 | 0.00 [0%] | 0.25 [2%] | 0.00 [0%] | 0.43 [3%] | 2.29 [18%] | 10.06 [77%] |
| 10–50% | 64 | 15.74 | 0.00 [0%] | 0.42 [3%] | 0.01 [0%] | 0.47 [3%] | 4.83 [31%] | 10.01 [64%] |
| miss<10% | 163 | 16.41 | 0.00 [0%] | 0.75 [5%] | 0.00 [0%] | 0.42 [3%] | 6.53 [40%] | 8.71 [53%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 24 | 0.00 | 0.04 | 0.00 | 0.00 | 3.62 |
| GPU≥50% | 292 | 0.00 | 0.03 | 0.00 | 0.00 | 2.97 |
| 10–50% | 64 | 0.00 | 0.04 | 0.00 | 0.00 | 1.41 |
| miss<10% | 163 | 0.00 | 0.03 | 0.00 | 0.00 | 2.18 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok | slots |
|---|---|---|---|---|---|
| host≥50% | 24 | 0.16 | 0.47 | 0.00 | 3.21 |
| GPU≥50% | 292 | 0.04 | 0.43 | 0.00 | 1.58 |
| 10–50% | 64 | 0.04 | 0.46 | 0.00 | 0.78 |
| miss<10% | 163 | 0.02 | 0.41 | 0.00 | 0.78 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok | slots |
|---|---|---|---|---|---|
| host≥50% | 24 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 292 | 0.18 | 0.00 | 2.29 | 5.49 |
| 10–50% | 64 | 0.33 | 0.00 | 4.83 | 7.74 |
| miss<10% | 163 | 0.69 | 0.00 | 6.53 | 5.73 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | other | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 24 | 0.00 | 0.00 | 0.00 | 2.71 |
| GPU≥50% | 292 | 0.00 | 0.00 | 0.00 | 0.02 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.05 |
| miss<10% | 163 | 0.00 | 0.00 | 0.00 | 0.02 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 543; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 30; reservation passed at admission p50 452 / max 1769 blocks; free blocks at admission p50 9678.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.398 |
| time with free blocks < 50% of the pool | 0.430 |
| time with free blocks < 25% of the pool | 0.064 |
| time with free blocks < 10% of the pool | 0.008 |
| time with free blocks < 5% of the pool | 0.004 |
| blocks held by loads in transfer, mean / max | 39 / 3312 |
| in-flight prefill reservation after schedule(), mean / max | 338 / 1909 |
| steps whose running requests used the whole token budget (share of time) | 0.042 |
| steps with a shortened token budget (share of time) | 0.204 |
| running requests, mean / max | 10.4 / 16 |
| waiting + kv-holding requests, mean / max | 6.0 / 30 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 24 | 0.75 | 0.00 | 0.46 / 0.18 | 15.04 [6] | 14.26 [18] | 10.00 [20] | 15.02 [4] |
| GPU≥50% | 292 | 0.71 | 0.00 | 0.55 / 0.36 | 0.27 [84] | 10.73 [208] | 3.31 [282] | 30.29 [10] |
| 10–50% | 64 | 0.62 | 0.00 | 0.60 / 0.18 | 0.79 [24] | 14.01 [40] | 8.38 [57] | 30.50 [7] |
| miss<10% | 163 | 0.72 | 0.00 | 0.74 / 0.36 | 3.84 [46] | 21.01 [117] | 17.71 [154] | 31.96 [9] |
