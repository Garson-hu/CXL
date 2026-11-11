## Admission analysis of `c5-skip3-res300` (93 requests, 1001 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 16640 | 1024 | 3.33 / 3.36 | 0.00 / 0.00 | 0.06 / 0.06 | 2.89 / 2.89 | 0.17 / 0.17 | 0.00 / 0.00 | 0.17 / 0.17 |
| miss<10% | 90 | 2304 | 111 | 7.18 / 11.23 | 0.00 / 0.24 | 0.67 / 2.31 | 2.71 / 3.13 | – | – | 1.16 / 1.04 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget_adm | other | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 3.12 | 0.00 [0%] | 0.15 [5%] | 0.08 [3%] | 2.89 [93%] | 0.00 [0%] |
| miss<10% | 90 | 5.69 | 3.33 [58%] | 0.00 [0%] | 0.41 [7%] | 0.66 [12%] | 1.29 [23%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget_adm | other | pending |
|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 0.24 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | slots |
|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.06 | 0.00 | 0.00 |
| miss<10% | 90 | 1.21 | 0.41 | 0.00 | 0.69 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | slots |
|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 2.89 | 0.00 |
| miss<10% | 90 | 1.88 | 0.00 | 0.66 | 0.60 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 |
| miss<10% | 90 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 93; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 19; reservation passed at admission p50 5 / max 40 blocks; free blocks at admission p50 2485.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.392 |
| time with free blocks < 50% of the pool | 0.325 |
| time with free blocks < 25% of the pool | 0.310 |
| time with free blocks < 10% of the pool | 0.155 |
| time with free blocks < 5% of the pool | 0.106 |
| blocks held by loads in transfer, mean / max | 23 / 6336 |
| in-flight prefill reservation after schedule(), mean / max | 346 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.530 |
| running requests, mean / max | 5.0 / 16 |
| waiting + kv-holding requests, mean / max | 3.1 / 22 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.04 / 0.04 | 3.33 [3] | – | – | 3.33 [3] |
| miss<10% | 90 | 0.43 | 0.00 | 0.04 / 0.02 | 6.95 [51] | 8.53 [39] | – | 7.18 [90] |
