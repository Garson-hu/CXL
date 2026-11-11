## Admission analysis of `x08c-conv-p2-skip30` (291 requests, 20710 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 9550 | 544 | 3.00 / 26.72 | 0.00 / 0.29 | 0.77 / 0.59 | 0.00 / 3.41 | 0.96 / 0.82 | 0.00 / 0.00 | 0.69 / 0.70 |
| GPU≥50% | 28 | 906 | 16 | 1.31 / 37.39 | 0.00 / 0.26 | 0.58 / 0.48 | 0.15 / 3.88 | – | – | 0.42 / 0.43 |
| 10–50% | 67 | 2103 | 96 | 5.55 / 52.05 | 0.00 / 0.74 | 0.57 / 0.85 | 1.37 / 8.96 | 0.89 / 0.69 | 0.00 / 0.80 | 0.77 / 1.00 |
| miss<10% | 182 | 13883 | 128 | 14.70 / 52.56 | 0.00 / 1.01 | 0.57 / 0.63 | 10.72 / 13.48 | 0.61 / 0.61 | 0.00 / 0.00 | 3.42 / 4.40 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 5.11 | 0.03 [1%] | 0.02 [0%] | 1.84 [36%] | 0.55 [11%] | 0.00 [0%] | 0.80 [16%] | 1.88 [37%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 28 | 4.62 | 0.00 [0%] | 0.08 [2%] | 2.60 [56%] | 0.00 [0%] | 0.00 [0%] | 0.48 [10%] | 0.00 [0%] | 0.03 [1%] | 1.43 [31%] | 0.01 [0%] |
| 10–50% | 67 | 10.63 | 0.00 [0%] | 0.39 [4%] | 4.48 [42%] | 0.02 [0%] | 0.05 [0%] | 0.47 [4%] | 0.10 [1%] | 0.01 [0%] | 5.10 [48%] | 0.01 [0%] |
| miss<10% | 182 | 15.13 | 0.00 [0%] | 0.50 [3%] | 3.60 [24%] | 0.00 [0%] | 0.81 [5%] | 0.48 [3%] | 1.88 [12%] | 0.01 [0%] | 7.83 [52%] | 0.01 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.00 | 0.01 | 0.28 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.01 | 0.25 | 0.00 | 0.00 | 0.01 |
| 10–50% | 67 | 0.00 | 0.01 | 0.73 | 0.00 | 0.00 | 0.00 |
| miss<10% | 182 | 0.00 | 0.02 | 0.99 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.00 | 0.00 | 0.59 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.48 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 67 | 0.01 | 0.38 | 0.46 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 182 | 0.01 | 0.15 | 0.48 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.01 | 1.52 | 0.00 | 0.00 | 1.88 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.07 | 2.35 | 0.00 | 0.00 | 0.00 | 0.03 | 1.43 | 0.01 |
| 10–50% | 67 | 0.37 | 3.36 | 0.00 | 0.00 | 0.10 | 0.01 | 5.10 | 0.01 |
| miss<10% | 182 | 0.47 | 2.46 | 0.81 | 0.00 | 1.88 | 0.01 | 7.83 | 0.01 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 28 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 67 | 0.00 | 0.00 | 0.00 | 0.05 | 0.00 |
| miss<10% | 182 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 3456 | 3456 / 0 / 0 | 128 | 1542 | 651 (281–1707) | 0 (600) |
| promotion after a load | 51 | 51 / 0 / 0 | 128 | 970 | 603 (593–620) | 0 (0) |

Requests refused at least once: 34 of 291; preemptions: 11; running requests that could not get their next chunk: 22.
Admitted external loads: 19; reservation passed at admission p50 462 / max 1221 blocks; free blocks at admission p50 2094.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.629 |
| time with free blocks < 50% of the pool | 0.689 |
| time with free blocks < 25% of the pool | 0.548 |
| time with free blocks < 10% of the pool | 0.270 |
| time with free blocks < 5% of the pool | 0.117 |
| blocks held by loads in transfer, mean / max | 7 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 292 / 1911 |
| steps whose running requests used the whole token budget (share of time) | 0.088 |
| steps with a shortened token budget (share of time) | 0.113 |
| running requests, mean / max | 6.3 / 14 |
| waiting + kv-holding requests, mean / max | 2.8 / 17 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 14 | 0.57 | 0.00 | 0.25 / 0.07 | 3.15 [6] | 3.00 [8] | 2.91 [7] | 3.15 [7] |
| GPU≥50% | 28 | 0.61 | 0.00 | 0.48 / 0.03 | 0.25 [11] | 1.36 [17] | 1.16 [15] | 1.34 [13] |
| 10–50% | 67 | 0.67 | 0.00 | 0.28 / 0.08 | 0.42 [22] | 10.62 [45] | 2.13 [39] | 19.85 [28] |
| miss<10% | 182 | 0.62 | 0.00 | 0.34 / 0.06 | 4.41 [70] | 20.85 [112] | 10.82 [99] | 24.82 [83] |
