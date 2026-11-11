## Admission analysis of `cc-p2560-base` (816 requests, 22866 engine steps, pool 2560 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 2048 | 128 | 1.30 / 6.92 | 0.00 / 0.24 | 0.03 / 0.93 | 0.00 / 0.03 | 0.31 / 0.45 | 0.00 / 0.08 | 0.03 / 0.15 |
| GPU≥50% | 25 | 8192 | 256 | 0.56 / 9.17 | 0.00 / 0.23 | 0.19 / 1.02 | 0.00 / 0.00 | 0.18 / 0.38 | 0.00 / 0.00 | 0.02 / 0.05 |
| miss<10% | 418 | 2048 | 128 | 1.42 / 6.68 | 0.00 / 0.21 | 0.02 / 0.88 | 0.00 / 0.03 | – | – | 0.65 / 0.76 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 1.73 | 0.85 [49%] | 0.21 [12%] | 0.28 [16%] | 0.10 [6%] | 0.03 [2%] | 0.27 [16%] |
| GPU≥50% | 25 | 1.63 | 0.65 [40%] | 0.26 [16%] | 0.32 [20%] | 0.12 [7%] | 0.00 [0%] | 0.27 [17%] |
| miss<10% | 418 | 1.12 | 0.54 [48%] | 0.17 [15%] | 0.23 [21%] | 0.00 [0%] | 0.03 [3%] | 0.15 [13%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.16 | 0.03 | 0.06 | 0.00 | 0.00 |
| GPU≥50% | 25 | 0.11 | 0.05 | 0.07 | 0.00 | 0.00 |
| miss<10% | 418 | 0.12 | 0.03 | 0.06 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.44 | 0.14 | 0.17 | 0.00 | 0.18 |
| GPU≥50% | 25 | 0.48 | 0.17 | 0.20 | 0.00 | 0.17 |
| miss<10% | 418 | 0.42 | 0.14 | 0.17 | 0.00 | 0.15 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 373 | 0.03 | 0.00 |
| GPU≥50% | 25 | 0.00 | 0.00 |
| miss<10% | 418 | 0.03 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.08 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 25 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 259 | 259 / 0 / 0 | 512 | 512 | 117 (50–436) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 488 | 488 / 0 / 0 | 128 | 512 | 118 (47–499) | 0 (0) |

Requests refused at least once: 72 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 563; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 2494.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.272 |
| time with free blocks < 50% of the pool | 0.180 |
| time with free blocks < 25% of the pool | 0.114 |
| time with free blocks < 10% of the pool | 0.049 |
| time with free blocks < 5% of the pool | 0.033 |
| blocks held by loads in transfer, mean / max | 75 / 1536 |
| in-flight prefill reservation after schedule(), mean / max | 33 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.228 |
| running requests, mean / max | 1.7 / 14 |
| waiting + kv-holding requests, mean / max | 1.5 / 31 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 373 | 0.24 | 0.11 | 0.87 / 0.17 | 0.50 [284] | 2.98 [89] | 0.62 [306] | 4.32 [67] |
| GPU≥50% | 25 | 0.24 | 0.04 | 0.75 / 0.17 | 0.24 [19] | 4.42 [6] | 0.24 [18] | 0.89 [7] |
| miss<10% | 418 | 0.31 | 0.07 | 0.95 / 0.15 | 0.86 [287] | 1.50 [131] | 1.00 [350] | 4.14 [68] |
