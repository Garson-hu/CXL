## Admission analysis of `s4-p3728-p1` (480 requests, 13528 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 151 | 8192 | 512 | 0.10 / 10.99 | 0.00 / 0.64 | 0.02 / 0.79 | 0.00 / 0.20 | 0.05 / 0.26 | 0.00 / 0.00 | 0.02 / 0.07 |
| GPU≥50% | 66 | 2048 | 128 | 0.08 / 6.09 | 0.00 / 0.13 | 0.02 / 0.32 | 0.00 / 0.02 | 0.04 / 0.12 | 0.00 / 0.00 | 0.01 / 0.05 |
| miss<10% | 263 | 8192 | 128 | 1.42 / 39.60 | 0.00 / 0.49 | 0.20 / 0.88 | 0.00 / 7.40 | – | – | 1.40 / 1.06 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:tok |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 151 | 1.89 | 0.00 [0%] | 0.13 [7%] | 1.43 [76%] | 0.06 [3%] | 0.08 [4%] | 0.19 [10%] | 0.00 [0%] |
| GPU≥50% | 66 | 0.59 | 0.00 [0%] | 0.06 [11%] | 0.37 [62%] | 0.04 [7%] | 0.01 [2%] | 0.11 [19%] | 0.00 [0%] |
| miss<10% | 263 | 8.77 | 0.00 [0%] | 1.04 [12%] | 4.95 [56%] | 0.00 [0%] | 0.43 [5%] | 0.21 [2%] | 2.14 [24%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.00 | 0.03 | 0.60 | 0.00 | 0.00 |
| GPU≥50% | 66 | 0.00 | 0.02 | 0.11 | 0.00 | 0.00 |
| miss<10% | 263 | 0.00 | 0.04 | 0.45 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:tok |
|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.07 | 0.61 | 0.00 | 0.12 | 0.00 |
| GPU≥50% | 66 | 0.03 | 0.22 | 0.00 | 0.08 | 0.00 |
| miss<10% | 263 | 0.07 | 0.60 | 0.00 | 0.20 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:tok |
|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.01 | 0.11 | 0.08 | 0.00 | 0.00 |
| GPU≥50% | 66 | 0.01 | 0.01 | 0.01 | 0.00 | 0.00 |
| miss<10% | 263 | 0.94 | 3.90 | 0.43 | 0.00 | 2.14 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|
| host≥50% | 151 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 66 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 263 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 72 | 72 / 0 / 0 | 512 | 512 | 262 (132–392) | 129 (352) |
| compute, no computed tokens (miss / GPU-prefix hit) | 590 | 590 / 0 / 0 | 1 | 512 | 135 (131–391) | 0 (0) |

Requests refused at least once: 113 of 480; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 297; reservation passed at admission p50 0 / max 387 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.436 |
| time with free blocks < 50% of the pool | 0.422 |
| time with free blocks < 25% of the pool | 0.365 |
| time with free blocks < 10% of the pool | 0.219 |
| time with free blocks < 5% of the pool | 0.130 |
| blocks held by loads in transfer, mean / max | 58 / 2048 |
| in-flight prefill reservation after schedule(), mean / max | 90 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.107 |
| steps with a shortened token budget (share of time) | 0.115 |
| running requests, mean / max | 3.2 / 9 |
| waiting + kv-holding requests, mean / max | 5.7 / 32 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.27 | 0.00 | 0.96 / 0.06 | 0.06 [110] | 3.67 [41] | 0.07 [116] | 6.48 [35] |
| GPU≥50% | 66 | 0.21 | 0.00 | 0.97 / 0.28 | 0.04 [52] | 2.03 [14] | 0.04 [60] | 6.09 [6] |
| miss<10% | 263 | 0.46 | 0.00 | 0.86 / 0.14 | 0.34 [141] | 18.38 [122] | 0.46 [208] | 20.42 [55] |
