## Admission analysis of `c1-tokfast` (45 requests, 2296 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 4352 | 256 | 2.17 / 2.80 | 0.00 / 0.00 | 0.49 / 0.44 | 0.00 / 0.00 | 1.15 / 0.87 | 0.00 / 0.00 | 0.27 / 0.28 |
| miss<10% | 18 | 8448 | 128 | 2.78 / 8.65 | 0.00 / 0.00 | 0.10 / 0.22 | 0.00 / 0.00 | – | – | 2.17 / 3.31 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 27 | 1.31 | 0.00 [0%] | 0.00 [0%] | 0.59 [45%] | 0.72 [55%] |
| miss<10% | 18 | 0.23 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.23 [100%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 27 | 0.00 | 0.00 | 0.00 |
| miss<10% | 18 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 27 | 0.44 |
| miss<10% | 18 | 0.22 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 27 | 0.00 |
| miss<10% | 18 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 27 | 0.00 | 0.00 |
| miss<10% | 18 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 45; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 33; reservation passed at admission p50 60 / max 1096 blocks; free blocks at admission p50 4835.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.261 |
| time with free blocks < 50% of the pool | 0.155 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 49 / 1824 |
| in-flight prefill reservation after schedule(), mean / max | 240 / 1638 |
| steps whose running requests used the whole token budget (share of time) | 0.264 |
| running requests, mean / max | 4.5 / 11 |
| waiting + kv-holding requests, mean / max | 0.3 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 0.67 | 0.00 | 0.59 / 0.48 | 0.24 [9] | 2.67 [18] | 2.17 [27] | – |
| miss<10% | 18 | 0.50 | 0.00 | 0.74 / 0.65 | 4.57 [9] | 2.77 [9] | 2.78 [18] | – |
