## Admission analysis of `c1c-tokfast512-sync` (45 requests, 2057 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 4352 | 256 | 0.93 / 1.10 | 0.00 / 0.00 | 0.23 / 0.21 | 0.00 / 0.00 | 0.32 / 0.25 | 0.00 / 0.00 | 0.12 / 0.12 |
| miss<10% | 18 | 8448 | 128 | 4.06 / 8.09 | 0.00 / 0.00 | 0.04 / 0.11 | 0.00 / 1.32 | – | – | 1.72 / 2.71 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 0.46 | 0.08 [16%] | 0.00 [0%] | 0.08 [17%] | 0.31 [67%] | 0.00 [0%] |
| miss<10% | 18 | 1.43 | 0.00 [0%] | 0.07 [5%] | 0.00 [0%] | 0.11 [8%] | 1.24 [87%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 27 | 0.00 | 0.00 | 0.00 |
| miss<10% | 18 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | pending | pol:tok |
|---|---|---|---|
| host≥50% | 27 | 0.21 | 0.00 |
| miss<10% | 18 | 0.11 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok |
|---|---|---|---|---|
| host≥50% | 27 | 0.00 | 0.00 | 0.00 |
| miss<10% | 18 | 0.07 | 0.00 | 1.24 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 27 | 0.00 | 0.00 | 0.00 |
| miss<10% | 18 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 45; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 33; reservation passed at admission p50 166 / max 1416 blocks; free blocks at admission p50 5155.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.250 |
| time with free blocks < 50% of the pool | 0.118 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 15 / 1824 |
| in-flight prefill reservation after schedule(), mean / max | 278 / 1638 |
| steps whose running requests used the whole token budget (share of time) | 0.324 |
| steps with a shortened token budget (share of time) | 0.124 |
| running requests, mean / max | 4.5 / 10 |
| waiting + kv-holding requests, mean / max | 0.3 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 0.67 | 0.00 | 0.60 / 0.49 | 0.26 [9] | 0.94 [18] | 0.93 [27] | – |
| miss<10% | 18 | 0.33 | 0.00 | 0.74 / 0.63 | 4.06 [12] | 7.45 [6] | 4.06 [18] | – |
