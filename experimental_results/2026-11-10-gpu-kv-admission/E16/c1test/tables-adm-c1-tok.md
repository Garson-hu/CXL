## Admission analysis of `c1-tok` (45 requests, 2298 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 4352 | 256 | 2.14 / 5.26 | 0.00 / 0.06 | 0.80 / 0.63 | 0.00 / 0.00 | 0.80 / 1.15 | 0.00 / 0.00 | 0.14 / 0.40 |
| miss<10% | 18 | 8448 | 128 | 3.87 / 7.43 | 0.00 / 0.00 | 0.10 / 1.13 | 0.00 / 0.00 | – | – | 1.63 / 2.77 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 27 | 1.84 | 0.08 [4%] | 0.20 [11%] | 0.65 [35%] | 0.91 [50%] |
| miss<10% | 18 | 1.13 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 1.13 [100%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 27 | 0.00 | 0.06 | 0.00 | 0.00 |
| miss<10% | 18 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 27 | 0.63 |
| miss<10% | 18 | 1.13 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 27 | 0.00 |
| miss<10% | 18 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | other | pending |
|---|---|---|---|---|
| host≥50% | 27 | 0.00 | 0.00 | 0.00 |
| miss<10% | 18 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 45; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 33; reservation passed at admission p50 15 / max 1000 blocks; free blocks at admission p50 4739.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.258 |
| time with free blocks < 50% of the pool | 0.123 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 64 / 1824 |
| in-flight prefill reservation after schedule(), mean / max | 199 / 1638 |
| steps whose running requests used the whole token budget (share of time) | 0.275 |
| running requests, mean / max | 4.2 / 11 |
| waiting + kv-holding requests, mean / max | 0.6 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 0.74 | 0.00 | 0.59 / 0.48 | 0.23 [7] | 3.75 [20] | 2.14 [27] | – |
| miss<10% | 18 | 0.50 | 0.00 | 0.74 / 0.65 | 3.87 [9] | 2.93 [9] | 3.87 [18] | – |
