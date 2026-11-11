## Admission analysis of `cc-p7456-base` (816 requests, 22013 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 2048 | 128 | 1.02 / 7.26 | 0.00 / 0.16 | 0.02 / 0.85 | 0.00 / 0.00 | 0.36 / 0.57 | 0.00 / 0.10 | 0.03 / 0.21 |
| GPU≥50% | 73 | 4096 | 128 | 0.91 / 7.58 | 0.00 / 0.25 | 0.04 / 0.97 | 0.00 / 0.00 | 0.27 / 0.42 | 0.00 / 0.09 | 0.03 / 0.20 |
| miss<10% | 418 | 2048 | 128 | 1.38 / 6.64 | 0.00 / 0.15 | 0.02 / 0.80 | 0.00 / 0.00 | – | – | 0.66 / 0.80 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 1.68 | 0.88 [52%] | 0.27 [16%] | 0.13 [8%] | 0.25 [15%] | 0.15 [9%] |
| GPU≥50% | 73 | 1.74 | 0.91 [52%] | 0.22 [13%] | 0.09 [5%] | 0.27 [16%] | 0.25 [14%] |
| miss<10% | 418 | 0.95 | 0.49 [51%] | 0.20 [21%] | 0.00 [0%] | 0.13 [14%] | 0.13 [14%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.10 | 0.03 | 0.00 | 0.00 | 0.03 |
| GPU≥50% | 73 | 0.15 | 0.03 | 0.00 | 0.00 | 0.07 |
| miss<10% | 418 | 0.10 | 0.02 | 0.00 | 0.00 | 0.03 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 325 | 0.42 | 0.18 | 0.15 | 0.10 |
| GPU≥50% | 73 | 0.45 | 0.16 | 0.21 | 0.15 |
| miss<10% | 418 | 0.39 | 0.17 | 0.13 | 0.10 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 325 | 0.00 |
| GPU≥50% | 73 | 0.00 |
| miss<10% | 418 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.09 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 73 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 563; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 7389.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.115 |
| time with free blocks < 50% of the pool | 0.048 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 97 / 1600 |
| in-flight prefill reservation after schedule(), mean / max | 37 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.233 |
| running requests, mean / max | 2.2 / 16 |
| waiting + kv-holding requests, mean / max | 1.4 / 31 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.24 | 0.10 | 0.97 / 0.56 | 0.43 [247] | 2.89 [78] | 1.02 [325] | – |
| GPU≥50% | 73 | 0.30 | 0.18 | 0.90 / 0.46 | 0.35 [51] | 3.74 [22] | 0.91 [73] | – |
| miss<10% | 418 | 0.33 | 0.10 | 0.98 / 0.57 | 0.70 [282] | 1.57 [136] | 1.38 [418] | – |
