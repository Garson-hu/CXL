## Admission analysis of `c5-p2` (93 requests, 1032 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 16640 | 1024 | 4.86 / 4.98 | 0.00 / 0.00 | 0.06 / 0.06 | 2.82 / 2.95 | 1.49 / 1.37 | 0.00 / 0.00 | 0.17 / 0.25 |
| miss<10% | 90 | 2304 | 111 | 7.64 / 11.74 | 0.00 / 0.80 | 0.57 / 3.11 | 2.08 / 2.24 | – | – | 0.96 / 0.94 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:resv | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 4.38 | 0.23 [5%] | 0.18 [4%] | 0.65 [15%] | 0.00 [0%] | 0.36 [8%] | 2.95 [67%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 90 | 6.15 | 2.94 [48%] | 0.66 [11%] | 0.00 [0%] | 0.04 [1%] | 0.41 [7%] | 0.45 [7%] | 0.14 [2%] | 0.15 [2%] | 1.35 [22%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 0.46 | 0.09 | 0.00 | 0.00 | 0.24 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:resv | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 1.50 | 0.36 | 0.41 | 0.00 | 0.00 | 0.00 | 0.84 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:resv | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 2.95 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 0.98 | 0.22 | 0.04 | 0.00 | 0.45 | 0.14 | 0.15 | 0.26 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | hol:full | pending |
|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 |
| miss<10% | 90 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 13 | 13 / 0 / 0 | 111 | 144 | 89 (84–118) | 0 (0) |

Requests refused at least once: 10 of 93; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 19; reservation passed at admission p50 5 / max 40 blocks; free blocks at admission p50 2486.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.395 |
| time with free blocks < 50% of the pool | 0.326 |
| time with free blocks < 25% of the pool | 0.317 |
| time with free blocks < 10% of the pool | 0.171 |
| time with free blocks < 5% of the pool | 0.129 |
| blocks held by loads in transfer, mean / max | 46 / 6336 |
| in-flight prefill reservation after schedule(), mean / max | 338 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.524 |
| steps with a shortened token budget (share of time) | 0.007 |
| running requests, mean / max | 5.1 / 16 |
| waiting + kv-holding requests, mean / max | 3.3 / 24 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.04 / 0.04 | 4.86 [3] | – | – | 4.86 [3] |
| miss<10% | 90 | 0.38 | 0.00 | 0.04 / 0.02 | 5.08 [56] | 10.27 [34] | – | 7.64 [90] |
