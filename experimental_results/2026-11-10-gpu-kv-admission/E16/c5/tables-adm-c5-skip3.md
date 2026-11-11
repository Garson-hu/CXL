## Admission analysis of `c5-skip3` (93 requests, 912 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 16640 | 1024 | 5.93 / 6.33 | 0.00 / 0.00 | 0.06 / 0.06 | 3.87 / 3.88 | 1.18 / 1.17 | 0.00 / 0.00 | 0.78 / 0.78 |
| miss<10% | 90 | 2304 | 95 | 6.20 / 10.60 | 0.31 / 0.68 | 4.96 / 3.82 | 0.00 / 0.20 | – | – | 1.15 / 1.04 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 5.11 | 0.00 [0%] | 1.15 [23%] | 0.00 [0%] | 0.00 [0%] | 0.61 [12%] | 0.08 [2%] | 3.26 [64%] | 0.00 [0%] |
| miss<10% | 90 | 4.70 | 0.30 [6%] | 2.97 [63%] | 0.34 [7%] | 0.00 [0%] | 0.00 [0%] | 0.40 [9%] | 0.11 [2%] | 0.58 [12%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 0.05 | 0.47 | 0.08 | 0.00 | 0.00 | 0.09 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.06 | 0.00 | 0.00 |
| miss<10% | 90 | 0.25 | 2.43 | 0.24 | 0.40 | 0.00 | 0.49 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks |
|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.61 | 0.00 | 3.26 |
| miss<10% | 90 | 0.07 | 0.02 | 0.00 | 0.00 | 0.11 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | pending |
|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 |
| miss<10% | 90 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 42 | 42 / 0 / 0 | 1024 | 1040 | 872 (728–1015) | 0 (0) |

Requests refused at least once: 3 of 93; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 19; reservation passed at admission p50 5 / max 40 blocks; free blocks at admission p50 2490.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.385 |
| time with free blocks < 50% of the pool | 0.314 |
| time with free blocks < 25% of the pool | 0.298 |
| time with free blocks < 10% of the pool | 0.181 |
| time with free blocks < 5% of the pool | 0.140 |
| blocks held by loads in transfer, mean / max | 44 / 6336 |
| in-flight prefill reservation after schedule(), mean / max | 354 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.553 |
| running requests, mean / max | 4.8 / 16 |
| waiting + kv-holding requests, mean / max | 2.6 / 21 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.04 / 0.04 | 5.93 [3] | – | – | 5.93 [3] |
| miss<10% | 90 | 0.40 | 0.00 | 0.04 / 0.00 | 7.05 [54] | 6.20 [36] | – | 6.20 [90] |
