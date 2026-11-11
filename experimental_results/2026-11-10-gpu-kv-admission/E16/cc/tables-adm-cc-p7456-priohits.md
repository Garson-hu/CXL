## Admission analysis of `cc-p7456-priohits` (816 requests, 22146 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 2048 | 128 | 1.02 / 3.95 | 0.00 / 0.07 | 0.02 / 0.26 | 0.00 / 0.00 | 0.38 / 0.61 | 0.00 / 0.14 | 0.04 / 0.23 |
| GPU≥50% | 73 | 4096 | 128 | 0.94 / 3.67 | 0.00 / 0.12 | 0.03 / 0.32 | 0.00 / 0.00 | 0.31 / 0.50 | 0.00 / 0.13 | 0.03 / 0.19 |
| miss<10% | 418 | 2048 | 128 | 1.44 / 6.87 | 0.00 / 0.17 | 0.02 / 0.84 | 0.00 / 0.00 | – | – | 0.66 / 0.82 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 1.08 | 0.59 [55%] | 0.10 [10%] | 0.13 [12%] | 0.18 [17%] | 0.07 [7%] |
| GPU≥50% | 73 | 1.07 | 0.58 [54%] | 0.04 [4%] | 0.11 [10%] | 0.23 [21%] | 0.11 [10%] |
| miss<10% | 418 | 1.00 | 0.52 [52%] | 0.22 [22%] | 0.00 [0%] | 0.14 [14%] | 0.13 [13%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.06 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 73 | 0.10 | 0.00 | 0.00 | 0.00 | 0.02 |
| miss<10% | 418 | 0.10 | 0.02 | 0.00 | 0.00 | 0.04 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 325 | 0.11 | 0.00 | 0.11 | 0.03 |
| GPU≥50% | 73 | 0.12 | 0.00 | 0.16 | 0.04 |
| miss<10% | 418 | 0.42 | 0.20 | 0.14 | 0.09 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 325 | 0.00 |
| GPU≥50% | 73 | 0.00 |
| miss<10% | 418 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.12 | 0.00 | 0.00 | 0.00 | 0.02 |
| GPU≥50% | 73 | 0.11 | 0.00 | 0.00 | 0.00 | 0.02 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 564; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 7391.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.119 |
| time with free blocks < 50% of the pool | 0.045 |
| time with free blocks < 25% of the pool | 0.008 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 110 / 2624 |
| in-flight prefill reservation after schedule(), mean / max | 38 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.233 |
| running requests, mean / max | 2.3 / 16 |
| waiting + kv-holding requests, mean / max | 1.1 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.21 | 0.10 | 0.97 / 0.55 | 0.43 [257] | 2.78 [68] | 0.93 [316] | 3.67 [9] |
| GPU≥50% | 73 | 0.32 | 0.19 | 0.90 / 0.42 | 0.57 [50] | 2.68 [23] | 0.91 [70] | 2.03 [3] |
| miss<10% | 418 | 0.32 | 0.10 | 0.98 / 0.52 | 0.71 [286] | 1.86 [132] | 1.31 [407] | 9.67 [11] |
