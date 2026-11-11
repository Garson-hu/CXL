## Admission analysis of `cc-p7456-lpt1024` (816 requests, 22041 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 328 | 2048 | 128 | 0.75 / 7.17 | 0.00 / 0.13 | 0.02 / 0.74 | 0.00 / 0.00 | 0.35 / 0.56 | 0.00 / 0.12 | 0.17 / 0.24 |
| GPU≥50% | 70 | 4096 | 128 | 0.71 / 7.58 | 0.00 / 0.17 | 0.04 / 0.78 | 0.00 / 0.00 | 0.20 / 0.41 | 0.00 / 0.11 | 0.03 / 0.20 |
| miss<10% | 418 | 2048 | 64 | 1.39 / 6.82 | 0.00 / 0.13 | 0.02 / 0.70 | 0.00 / 0.00 | – | – | 0.73 / 1.03 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 328 | 1.55 | 0.63 [41%] | 0.25 [16%] | 0.19 [13%] | 0.24 [16%] | 0.22 [15%] |
| GPU≥50% | 70 | 1.48 | 0.52 [35%] | 0.24 [16%] | 0.16 [11%] | 0.31 [21%] | 0.26 [17%] |
| miss<10% | 418 | 0.83 | 0.35 [43%] | 0.18 [21%] | 0.00 [0%] | 0.14 [17%] | 0.16 [19%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 328 | 0.07 | 0.02 | 0.00 | 0.00 | 0.04 |
| GPU≥50% | 70 | 0.06 | 0.03 | 0.00 | 0.00 | 0.08 |
| miss<10% | 418 | 0.06 | 0.02 | 0.00 | 0.00 | 0.04 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 328 | 0.31 | 0.16 | 0.15 | 0.13 |
| GPU≥50% | 70 | 0.27 | 0.15 | 0.21 | 0.15 |
| miss<10% | 418 | 0.29 | 0.15 | 0.14 | 0.12 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 328 | 0.00 |
| GPU≥50% | 70 | 0.00 |
| miss<10% | 418 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 328 | 0.09 | 0.00 | 0.00 | 0.00 | 0.02 |
| GPU≥50% | 70 | 0.09 | 0.00 | 0.00 | 0.00 | 0.01 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 562; reservation passed at admission p50 0 / max 448 blocks; free blocks at admission p50 7389.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.117 |
| time with free blocks < 50% of the pool | 0.049 |
| time with free blocks < 25% of the pool | 0.001 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 101 / 1536 |
| in-flight prefill reservation after schedule(), mean / max | 65 / 896 |
| steps whose running requests used the whole token budget (share of time) | 0.156 |
| running requests, mean / max | 2.4 / 16 |
| waiting + kv-holding requests, mean / max | 1.2 / 29 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 328 | 0.31 | 0.04 | 0.97 / 0.54 | 0.39 [227] | 2.37 [101] | 0.72 [327] | 5.73 [1] |
| GPU≥50% | 70 | 0.44 | 0.04 | 0.91 / 0.58 | 0.09 [39] | 1.91 [31] | 0.71 [70] | – |
| miss<10% | 418 | 0.40 | 0.04 | 0.98 / 0.54 | 0.67 [252] | 1.83 [166] | 1.38 [417] | 5.02 [1] |
