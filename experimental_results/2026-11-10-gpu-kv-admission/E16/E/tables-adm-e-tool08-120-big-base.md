## Admission analysis of `e-tool08-120-big-base` (544 requests, 18626 engine steps, pool 19919 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 17 | 7190 | 384 | 15.42 / 44.07 | 2.18 / 4.84 | 4.00 / 7.32 | 0.00 / 0.00 | 1.07 / 1.04 | 0.61 / 2.07 | 0.34 / 0.55 |
| GPU≥50% | 299 | 6192 | 112 | 9.15 / 36.50 | 2.44 / 5.15 | 1.37 / 5.98 | 0.00 / 0.00 | 0.18 / 0.18 | 0.00 / 0.00 | 0.35 / 0.48 |
| 10–50% | 64 | 2103 | 87 | 8.41 / 32.71 | 0.68 / 3.67 | 1.58 / 6.42 | 0.00 / 0.00 | 1.99 / 1.32 | 1.14 / 0.69 | 0.58 / 0.92 |
| miss<10% | 164 | 13883 | 128 | 12.22 / 36.91 | 1.19 / 4.12 | 1.52 / 5.69 | 0.00 / 0.00 | 1.48 / 1.48 | 4.07 / 4.07 | 3.62 / 4.46 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 17 | 15.27 | 8.77 [57%] | 0.62 [4%] | 0.17 [1%] | 0.67 [4%] | 5.04 [33%] |
| GPU≥50% | 299 | 11.13 | 6.49 [58%] | 0.60 [5%] | 0.00 [0%] | 0.54 [5%] | 3.50 [31%] |
| 10–50% | 64 | 10.21 | 5.86 [57%] | 0.49 [5%] | 0.00 [0%] | 0.52 [5%] | 3.33 [33%] |
| miss<10% | 164 | 9.85 | 6.38 [65%] | 0.69 [7%] | 0.00 [0%] | 0.54 [5%] | 2.25 [23%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 17 | 2.81 | 0.21 | 0.00 | 0.00 | 1.82 |
| GPU≥50% | 299 | 3.44 | 0.27 | 0.00 | 0.00 | 1.44 |
| 10–50% | 64 | 2.69 | 0.26 | 0.00 | 0.00 | 0.72 |
| miss<10% | 164 | 2.95 | 0.24 | 0.00 | 0.00 | 0.94 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 17 | 4.13 | 0.39 | 0.53 | 2.27 |
| GPU≥50% | 299 | 3.05 | 0.33 | 0.54 | 2.06 |
| 10–50% | 64 | 3.11 | 0.23 | 0.51 | 2.57 |
| miss<10% | 164 | 3.40 | 0.45 | 0.53 | 1.31 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 17 | 0.00 |
| GPU≥50% | 299 | 0.00 |
| 10–50% | 64 | 0.00 |
| miss<10% | 164 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 17 | 1.36 | 0.00 | 0.00 | 0.00 | 0.71 |
| GPU≥50% | 299 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.02 | 0.00 | 0.00 | 0.00 | 0.02 |
| miss<10% | 164 | 0.02 | 0.00 | 0.00 | 0.00 | 0.01 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 544; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 23; reservation passed at admission p50 0 / max 88 blocks; free blocks at admission p50 8950.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.352 |
| time with free blocks < 50% of the pool | 0.385 |
| time with free blocks < 25% of the pool | 0.036 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 23 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 276 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.435 |
| running requests, mean / max | 9.1 / 16 |
| waiting + kv-holding requests, mean / max | 4.6 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 17 | 0.65 | 0.53 | 0.47 / 0.28 | 8.26 [6] | 19.34 [11] | 18.05 [16] | 15.42 [1] |
| GPU≥50% | 299 | 0.55 | 0.49 | 0.58 / 0.34 | 1.02 [136] | 13.10 [163] | 8.84 [294] | 19.64 [5] |
| 10–50% | 64 | 0.53 | 0.48 | 0.73 / 0.33 | 1.36 [30] | 11.72 [34] | 5.94 [59] | 13.18 [5] |
| miss<10% | 164 | 0.51 | 0.44 | 0.81 / 0.37 | 3.79 [81] | 18.40 [83] | 11.68 [161] | 16.73 [3] |
