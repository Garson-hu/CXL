## Admission analysis of `x08-p2-skip30-r2` (544 requests, 21064 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 103 | 6178 | 384 | 4.46 / 26.92 | 0.00 / 1.84 | 0.57 / 0.67 | 0.00 / 5.49 | 0.69 / 0.75 | 0.00 / 0.02 | 0.51 / 0.60 |
| GPU≥50% | 210 | 6214 | 80 | 1.16 / 18.50 | 0.00 / 0.51 | 0.34 / 0.46 | 0.15 / 2.08 | 0.71 / 0.73 | 0.00 / 0.00 | 0.43 / 0.45 |
| 10–50% | 64 | 2103 | 96 | 3.79 / 46.72 | 0.00 / 1.69 | 0.46 / 0.68 | 1.96 / 7.52 | 0.80 / 0.74 | 0.00 / 0.00 | 0.67 / 0.97 |
| miss<10% | 164 | 13883 | 128 | 15.82 / 51.70 | 0.00 / 0.48 | 0.39 / 0.55 | 11.37 / 13.89 | 0.58 / 0.58 | 0.00 / 0.00 | 3.87 / 4.62 |
| mixed | 3 | 7294 | 195 | 19.94 / 20.15 | 4.17 / 3.87 | 0.79 / 0.79 | 11.84 / 11.84 | 0.98 / 0.98 | 0.00 / 0.00 | 1.45 / 1.53 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 103 | 8.77 | 0.01 [0%] | 0.13 [1%] | 3.73 [43%] | 0.26 [3%] | 0.42 [5%] | 0.11 [1%] | 0.71 [8%] | 2.79 [32%] | 0.03 [0%] | 0.57 [6%] | 0.01 [0%] | 0.00 [0%] |
| GPU≥50% | 210 | 3.10 | 0.00 [0%] | 0.10 [3%] | 0.94 [30%] | 0.00 [0%] | 0.02 [1%] | 0.00 [0%] | 0.35 [11%] | 0.73 [23%] | 0.03 [1%] | 0.94 [30%] | 0.00 [0%] | 0.00 [0%] |
| 10–50% | 64 | 9.93 | 0.00 [0%] | 0.25 [3%] | 3.47 [35%] | 0.08 [1%] | 0.04 [0%] | 0.02 [0%] | 0.44 [4%] | 1.00 [10%] | 0.12 [1%] | 4.50 [45%] | 0.01 [0%] | 0.00 [0%] |
| miss<10% | 164 | 14.92 | 0.00 [0%] | 0.55 [4%] | 2.62 [18%] | 0.11 [1%] | 0.00 [0%] | 0.81 [5%] | 0.38 [3%] | 2.50 [17%] | 0.10 [1%] | 7.84 [53%] | 0.01 [0%] | 0.01 [0%] |
| mixed | 3 | 17.49 | 0.00 [0%] | 0.43 [2%] | 3.85 [22%] | 0.00 [0%] | 0.59 [3%] | 0.00 [0%] | 1.19 [7%] | 11.43 [65%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 103 | 0.00 | 0.02 | 1.66 | 0.15 | 0.00 | 0.00 |
| GPU≥50% | 210 | 0.00 | 0.02 | 0.49 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.04 | 1.58 | 0.06 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.01 | 0.46 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.02 | 3.85 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 103 | 0.01 | 0.14 | 0.52 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 210 | 0.01 | 0.12 | 0.34 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.02 | 0.24 | 0.42 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.01 | 0.17 | 0.37 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.79 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 103 | 0.08 | 1.81 | 0.11 | 0.10 | 0.00 | 2.79 | 0.03 | 0.57 | 0.01 | 0.00 |
| GPU≥50% | 210 | 0.07 | 0.32 | 0.00 | 0.00 | 0.00 | 0.73 | 0.03 | 0.93 | 0.00 | 0.00 |
| 10–50% | 64 | 0.19 | 1.65 | 0.02 | 0.02 | 0.00 | 1.00 | 0.12 | 4.50 | 0.01 | 0.00 |
| miss<10% | 164 | 0.53 | 1.99 | 0.10 | 0.81 | 0.00 | 2.50 | 0.10 | 7.84 | 0.01 | 0.01 |
| mixed | 3 | 0.41 | 0.00 | 0.00 | 0.00 | 0.00 | 11.43 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 103 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 210 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 227 | 227 / 0 / 0 | 896 | 1030 | 626 (202–665) | 0 (445) |
| compute, no computed tokens (miss / GPU-prefix hit) | 2599 | 2415 / 0 / 184 | 128 | 1201 | 611 (139–1321) | 0 (600) |
| promotion after a load | 20 | 20 / 0 / 0 | 9 | 9 | 7 (2–15) | 0 (0) |

Requests refused at least once: 36 of 544; preemptions: 10; running requests that could not get their next chunk: 20.
Admitted external loads: 124; reservation passed at admission p50 321 / max 1856 blocks; free blocks at admission p50 1340.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.636 |
| time with free blocks < 50% of the pool | 0.683 |
| time with free blocks < 25% of the pool | 0.563 |
| time with free blocks < 10% of the pool | 0.318 |
| time with free blocks < 5% of the pool | 0.167 |
| blocks held by loads in transfer, mean / max | 26 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 298 / 2303 |
| steps whose running requests used the whole token budget (share of time) | 0.061 |
| steps with a shortened token budget (share of time) | 0.171 |
| running requests, mean / max | 6.8 / 16 |
| waiting + kv-holding requests, mean / max | 3.7 / 23 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 103 | 0.53 | 0.00 | 0.12 / 0.02 | 7.78 [48] | 2.35 [55] | 1.94 [26] | 7.78 [77] |
| GPU≥50% | 210 | 0.60 | 0.00 | 0.50 / 0.07 | 0.23 [84] | 1.61 [126] | 1.00 [124] | 1.88 [86] |
| 10–50% | 64 | 0.50 | 0.00 | 0.26 / 0.03 | 1.10 [32] | 7.43 [32] | 1.33 [32] | 19.15 [32] |
| miss<10% | 164 | 0.62 | 0.00 | 0.43 / 0.04 | 4.47 [63] | 19.16 [101] | 12.41 [94] | 24.41 [70] |
| mixed | 3 | 0.00 | 0.00 | 0.08 / 0.08 | 19.94 [3] | – | – | 19.94 [3] |
