## Admission analysis of `e-tool08-120-big-priolen` (544 requests, 18722 engine steps, pool 19919 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 17 | 7190 | 384 | 10.74 / 32.38 | 1.27 / 2.00 | 5.16 / 5.30 | 0.00 / 0.00 | 1.51 / 1.32 | 0.69 / 2.21 | 0.34 / 0.69 |
| GPU≥50% | 299 | 6192 | 68 | 5.29 / 19.91 | 0.92 / 2.15 | 1.30 / 3.97 | 0.00 / 0.00 | 2.30 / 1.60 | 6.59 / 4.67 | 0.35 / 0.46 |
| 10–50% | 64 | 2103 | 96 | 3.39 / 16.19 | 0.53 / 1.52 | 0.90 / 2.57 | 0.00 / 0.00 | 2.45 / 1.65 | 4.03 / 3.65 | 0.58 / 0.82 |
| miss<10% | 164 | 13883 | 128 | 9.88 / 36.32 | 0.76 / 2.64 | 1.91 / 5.91 | 0.00 / 0.00 | 0.43 / 0.43 | 0.39 / 0.39 | 3.58 / 4.48 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 17 | 10.83 | 5.62 [52%] | 0.15 [1%] | 0.16 [1%] | 0.83 [8%] | 4.07 [38%] |
| GPU≥50% | 299 | 6.19 | 3.05 [49%] | 0.10 [2%] | 0.00 [0%] | 0.57 [9%] | 2.47 [40%] |
| 10–50% | 64 | 4.41 | 2.42 [55%] | 0.04 [1%] | 0.00 [0%] | 0.62 [14%] | 1.33 [30%] |
| miss<10% | 164 | 8.56 | 4.90 [57%] | 0.47 [5%] | 0.00 [0%] | 0.58 [7%] | 2.61 [31%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 17 | 1.39 | 0.05 | 0.00 | 0.00 | 0.56 |
| GPU≥50% | 299 | 1.54 | 0.03 | 0.00 | 0.00 | 0.58 |
| 10–50% | 64 | 1.21 | 0.02 | 0.00 | 0.00 | 0.29 |
| miss<10% | 164 | 1.74 | 0.06 | 0.00 | 0.00 | 0.84 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 17 | 2.16 | 0.05 | 0.61 | 2.48 |
| GPU≥50% | 299 | 1.50 | 0.07 | 0.56 | 1.83 |
| 10–50% | 64 | 0.93 | 0.02 | 0.60 | 1.02 |
| miss<10% | 164 | 3.16 | 0.41 | 0.58 | 1.77 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 17 | 0.00 |
| GPU≥50% | 299 | 0.00 |
| 10–50% | 64 | 0.00 |
| miss<10% | 164 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 17 | 1.40 | 0.00 | 0.00 | 0.81 |
| GPU≥50% | 299 | 0.00 | 0.00 | 0.00 | 0.05 |
| 10–50% | 64 | 0.20 | 0.00 | 0.00 | 0.02 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 544; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 25; reservation passed at admission p50 0 / max 96 blocks; free blocks at admission p50 8769.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.355 |
| time with free blocks < 50% of the pool | 0.387 |
| time with free blocks < 25% of the pool | 0.037 |
| time with free blocks < 10% of the pool | 0.001 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 44 / 2864 |
| in-flight prefill reservation after schedule(), mean / max | 295 / 2818 |
| steps whose running requests used the whole token budget (share of time) | 0.436 |
| running requests, mean / max | 9.4 / 16 |
| waiting + kv-holding requests, mean / max | 2.9 / 19 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 17 | 0.59 | 0.47 | 0.39 / 0.32 | 8.27 [7] | 15.72 [10] | 10.74 [16] | 21.60 [1] |
| GPU≥50% | 299 | 0.53 | 0.46 | 0.59 / 0.34 | 1.02 [140] | 7.91 [159] | 5.28 [294] | 20.26 [5] |
| 10–50% | 64 | 0.56 | 0.50 | 0.78 / 0.34 | 1.33 [28] | 5.11 [36] | 2.52 [59] | 6.95 [5] |
| miss<10% | 164 | 0.49 | 0.44 | 0.80 / 0.34 | 3.71 [83] | 15.80 [81] | 9.30 [161] | 23.29 [3] |
