## Admission analysis of `c1c-chunk512` (45 requests, 2693 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 4352 | 256 | 2.99 / 9.30 | 1.33 / 2.59 | 0.31 / 0.61 | 0.00 / 0.00 | 0.30 / 0.29 | 0.00 / 0.12 | 0.10 / 0.17 |
| miss<10% | 18 | 8448 | 32 | 4.19 / 8.52 | 0.12 / 1.51 | 0.22 / 0.17 | 0.00 / 0.00 | – | – | 1.83 / 2.95 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 27 | 3.62 | 3.13 [87%] | 0.08 [2%] | 0.08 [2%] | 0.33 [9%] |
| miss<10% | 18 | 1.68 | 1.51 [90%] | 0.00 [0%] | 0.00 [0%] | 0.17 [10%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 27 | 2.56 | 0.03 | 0.00 | 0.00 |
| miss<10% | 18 | 1.51 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending |
|---|---|---|---|---|
| host≥50% | 27 | 0.29 | 0.05 | 0.27 |
| miss<10% | 18 | 0.00 | 0.00 | 0.17 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 27 | 0.00 |
| miss<10% | 18 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 27 | 0.12 | 0.00 | 0.00 |
| miss<10% | 18 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 45; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 33; reservation passed at admission p50 0 / max 75 blocks; free blocks at admission p50 4418.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.240 |
| time with free blocks < 50% of the pool | 0.051 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 23 / 1824 |
| in-flight prefill reservation after schedule(), mean / max | 286 / 1734 |
| steps whose running requests used the whole token budget (share of time) | 0.677 |
| steps with a shortened token budget (share of time) | 1.000 |
| running requests, mean / max | 4.2 / 10 |
| waiting + kv-holding requests, mean / max | 0.9 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 0.89 | 0.89 | 0.64 / 0.55 | 0.20 [3] | 4.82 [24] | 2.99 [27] | – |
| miss<10% | 18 | 0.50 | 0.50 | 0.74 / 0.67 | 4.19 [9] | 3.77 [9] | 4.19 [18] | – |
