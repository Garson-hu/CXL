## Admission analysis of `cc-p2560-p1` (816 requests, 23016 engine steps, pool 2560 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 2048 | 128 | 0.72 / 5.60 | 0.00 / 0.19 | 0.02 / 0.39 | 0.00 / 0.06 | 0.36 / 0.37 | 0.00 / 0.00 | 0.12 / 0.13 |
| GPU≥50% | 25 | 8192 | 256 | 0.67 / 8.00 | 0.00 / 0.22 | 0.21 / 0.68 | 0.00 / 0.00 | 0.18 / 0.33 | 0.00 / 0.00 | 0.02 / 0.12 |
| miss<10% | 418 | 2048 | 128 | 1.42 / 7.98 | 0.00 / 0.17 | 0.02 / 0.42 | 0.00 / 0.82 | – | – | 0.64 / 0.81 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:tok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 1.01 | 0.03 [3%] | 0.17 [17%] | 0.36 [36%] | 0.04 [4%] | 0.14 [14%] | 0.03 [3%] | 0.01 [1%] | 0.22 [22%] | 0.00 [0%] |
| GPU≥50% | 25 | 1.24 | 0.01 [1%] | 0.18 [14%] | 0.59 [47%] | 0.04 [4%] | 0.14 [12%] | 0.00 [0%] | 0.00 [0%] | 0.28 [22%] | 0.00 [0%] |
| miss<10% | 418 | 1.41 | 0.00 [0%] | 0.29 [21%] | 0.48 [34%] | 0.04 [3%] | 0.00 [0%] | 0.08 [6%] | 0.00 [0%] | 0.12 [8%] | 0.40 [28%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.00 | 0.05 | 0.11 | 0.02 | 0.00 | 0.00 |
| GPU≥50% | 25 | 0.00 | 0.06 | 0.14 | 0.02 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.05 | 0.11 | 0.02 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:tok |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.06 | 0.19 | 0.01 | 0.00 | 0.00 | 0.14 | 0.00 |
| GPU≥50% | 25 | 0.08 | 0.39 | 0.02 | 0.00 | 0.00 | 0.19 | 0.00 |
| miss<10% | 418 | 0.07 | 0.21 | 0.02 | 0.00 | 0.00 | 0.12 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.01 | 0.02 | 0.03 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 25 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.18 | 0.17 | 0.08 | 0.00 | 0.00 | 0.40 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 25 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 141 | 117 / 0 / 24 | 512 | 512 | 246 (112–506) | 0 (352) |
| compute, no computed tokens (miss / GPU-prefix hit) | 636 | 636 / 0 / 0 | 128 | 512 | 185 (52–434) | 0 (0) |

Requests refused at least once: 74 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 565; reservation passed at admission p50 0 / max 387 blocks; free blocks at admission p50 2559.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.273 |
| time with free blocks < 50% of the pool | 0.187 |
| time with free blocks < 25% of the pool | 0.112 |
| time with free blocks < 10% of the pool | 0.046 |
| time with free blocks < 5% of the pool | 0.025 |
| blocks held by loads in transfer, mean / max | 58 / 1856 |
| in-flight prefill reservation after schedule(), mean / max | 47 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.131 |
| steps with a shortened token budget (share of time) | 0.097 |
| running requests, mean / max | 1.9 / 14 |
| waiting + kv-holding requests, mean / max | 1.3 / 30 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.30 | 0.00 | 0.87 / 0.17 | 0.41 [260] | 1.45 [113] | 0.54 [315] | 2.08 [58] |
| GPU≥50% | 25 | 0.48 | 0.00 | 0.66 / 0.17 | 0.19 [13] | 1.29 [12] | 0.56 [18] | 1.04 [7] |
| miss<10% | 418 | 0.40 | 0.00 | 0.90 / 0.17 | 0.68 [252] | 2.15 [166] | 1.26 [359] | 5.43 [59] |
