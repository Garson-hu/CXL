## Admission analysis of `c3b-base` (15 requests, 1193 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 9 | 2304 | 128 | 8.65 / 8.70 | 7.14 / 6.85 | 0.72 / 0.72 | 0.00 / 0.00 | 0.58 / 0.58 | 0.00 / 0.00 | 0.19 / 0.23 |
| miss<10% | 6 | 16640 | 128 | 8.35 / 8.36 | 7.09 / 3.54 | 0.71 / 0.38 | 4.00 / 2.00 | – | – | 3.90 / 2.22 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 9 | 8.16 | 3.16 [39%] | 0.03 [0%] | 3.67 [45%] | 0.44 [5%] | 0.00 [0%] | 0.86 [11%] |
| miss<10% | 6 | 5.93 | 1.58 [27%] | 0.01 [0%] | 1.95 [33%] | 0.00 [0%] | 2.00 [34%] | 0.38 [6%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 9 | 3.16 | 0.02 | 3.67 | 0.00 | 0.00 |
| miss<10% | 6 | 1.58 | 0.01 | 1.95 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | own:full | pending |
|---|---|---|---|---|
| host≥50% | 9 | 0.01 | 0.00 | 0.72 |
| miss<10% | 6 | 0.00 | 0.00 | 0.38 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 9 | 0.00 | 0.00 |
| miss<10% | 6 | 2.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 9 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 492 | 492 / 0 / 0 | 128 | 1040 | 585 (561–609) | 0 (0) |

Requests refused at least once: 3 of 15; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 27; reservation passed at admission p50 0 / max 32 blocks; free blocks at admission p50 2911.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.370 |
| time with free blocks < 50% of the pool | 0.305 |
| time with free blocks < 25% of the pool | 0.305 |
| time with free blocks < 10% of the pool | 0.209 |
| time with free blocks < 5% of the pool | 0.030 |
| blocks held by loads in transfer, mean / max | 30 / 6816 |
| in-flight prefill reservation after schedule(), mean / max | 355 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.594 |
| running requests, mean / max | 2.4 / 10 |
| waiting + kv-holding requests, mean / max | 1.0 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 9 | 0.00 | 0.00 | 0.08 / 0.08 | 8.65 [9] | – | – | 8.65 [9] |
| miss<10% | 6 | 0.00 | 0.00 | 0.08 / 0.08 | 8.35 [6] | – | – | 8.35 [6] |
