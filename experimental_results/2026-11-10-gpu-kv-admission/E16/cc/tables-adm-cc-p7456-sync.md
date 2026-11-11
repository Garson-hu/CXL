## Admission analysis of `cc-p7456-sync` (815 requests, 20559 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 2048 | 128 | 0.97 / 7.01 | 0.00 / 0.31 | 0.02 / 0.79 | 0.00 / 0.00 | 0.34 / 0.39 | 0.00 / 0.20 | 0.02 / 0.08 |
| GPU≥50% | 73 | 4096 | 128 | 0.89 / 7.67 | 0.00 / 0.39 | 0.02 / 0.86 | 0.00 / 0.00 | 0.17 / 0.27 | 0.00 / 0.19 | 0.02 / 0.08 |
| miss<10% | 417 | 2048 | 128 | 1.45 / 6.70 | 0.00 / 0.31 | 0.02 / 0.74 | 0.00 / 0.00 | – | – | 0.65 / 0.74 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 1.70 | 0.96 [57%] | 0.46 [27%] | 0.02 [1%] | 0.18 [11%] | 0.07 [4%] |
| GPU≥50% | 73 | 1.71 | 0.99 [58%] | 0.41 [24%] | 0.02 [1%] | 0.17 [10%] | 0.11 [7%] |
| miss<10% | 417 | 1.05 | 0.60 [57%] | 0.36 [34%] | 0.00 [0%] | 0.03 [3%] | 0.06 [6%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.21 | 0.09 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 73 | 0.29 | 0.08 | 0.00 | 0.00 | 0.02 |
| miss<10% | 417 | 0.20 | 0.09 | 0.00 | 0.00 | 0.02 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 325 | 0.43 | 0.29 | 0.03 | 0.05 |
| GPU≥50% | 73 | 0.44 | 0.30 | 0.03 | 0.09 |
| miss<10% | 417 | 0.40 | 0.26 | 0.03 | 0.05 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 325 | 0.00 |
| GPU≥50% | 73 | 0.00 |
| miss<10% | 417 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.20 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 73 | 0.19 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 417 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 815; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 562; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 7455.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.110 |
| time with free blocks < 50% of the pool | 0.044 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 85 / 1088 |
| in-flight prefill reservation after schedule(), mean / max | 62 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.256 |
| running requests, mean / max | 2.3 / 16 |
| waiting + kv-holding requests, mean / max | 1.4 / 31 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 325 | 0.24 | 0.18 | 0.98 / 0.59 | 0.41 [246] | 2.71 [79] | 0.97 [325] | – |
| GPU≥50% | 73 | 0.32 | 0.27 | 0.95 / 0.50 | 0.22 [50] | 2.46 [23] | 0.89 [73] | – |
| miss<10% | 417 | 0.31 | 0.13 | 0.99 / 0.59 | 0.70 [286] | 1.71 [131] | 1.45 [417] | – |
