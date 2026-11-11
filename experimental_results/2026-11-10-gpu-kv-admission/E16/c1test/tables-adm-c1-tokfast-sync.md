## Admission analysis of `c1-tokfast-sync` (45 requests, 2118 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 4352 | 256 | 1.76 / 2.71 | 0.00 / 0.00 | 0.81 / 0.61 | 0.00 / 0.00 | 0.47 / 0.49 | 0.00 / 0.00 | 0.16 / 0.17 |
| miss<10% | 18 | 8448 | 128 | 2.79 / 8.57 | 0.00 / 0.00 | 0.10 / 0.12 | 0.00 / 0.00 | – | – | 2.49 / 3.41 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 27 | 1.10 | 0.00 [0%] | 0.04 [3%] | 0.23 [21%] | 0.83 [76%] |
| miss<10% | 18 | 0.12 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.12 [100%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 27 | 0.00 | 0.00 | 0.00 |
| miss<10% | 18 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 27 | 0.61 |
| miss<10% | 18 | 0.12 |

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
Admitted external loads: 33; reservation passed at admission p50 60 / max 1223 blocks; free blocks at admission p50 4962.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.251 |
| time with free blocks < 50% of the pool | 0.134 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 28 / 1824 |
| in-flight prefill reservation after schedule(), mean / max | 300 / 1638 |
| steps whose running requests used the whole token budget (share of time) | 0.304 |
| running requests, mean / max | 4.6 / 11 |
| waiting + kv-holding requests, mean / max | 0.3 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 27 | 0.67 | 0.00 | 0.59 / 0.49 | 0.21 [9] | 2.13 [18] | 1.76 [27] | – |
| miss<10% | 18 | 0.50 | 0.00 | 0.74 / 0.67 | 4.63 [9] | 2.79 [9] | 2.79 [18] | – |
