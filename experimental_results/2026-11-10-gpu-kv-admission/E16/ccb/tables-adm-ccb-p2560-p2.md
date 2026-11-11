## Admission analysis of `ccb-p2560-p2` (816 requests, 28457 engine steps, pool 2560 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 2048 | 128 | 0.66 / 2.23 | 0.00 / 0.13 | 0.03 / 0.18 | 0.00 / 0.17 | 0.36 / 0.36 | 0.00 / 0.00 | 0.03 / 0.13 |
| GPU≥50% | 23 | 8192 | 256 | 0.78 / 8.18 | 0.00 / 0.39 | 0.20 / 0.26 | 0.00 / 0.34 | 0.18 / 0.23 | 0.00 / 0.00 | 0.03 / 0.10 |
| miss<10% | 418 | 2048 | 128 | 1.47 / 8.20 | 0.00 / 0.12 | 0.02 / 0.20 | 0.00 / 1.13 | – | – | 0.66 / 0.83 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.83 | 0.03 [4%] | 0.13 [15%] | 0.20 [24%] | 0.01 [2%] | 0.19 [23%] | 0.01 [1%] | 0.00 [0%] | 0.22 [26%] | 0.04 [5%] | 0.00 [0%] |
| GPU≥50% | 23 | 1.21 | 0.00 [0%] | 0.16 [14%] | 0.49 [41%] | 0.06 [5%] | 0.14 [11%] | 0.00 [0%] | 0.00 [0%] | 0.29 [24%] | 0.06 [5%] | 0.00 [0%] |
| miss<10% | 418 | 1.45 | 0.00 [0%] | 0.30 [21%] | 0.37 [26%] | 0.02 [1%] | 0.00 [0%] | 0.04 [3%] | 0.00 [0%] | 0.13 [9%] | 0.10 [7%] | 0.48 [33%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.00 | 0.03 | 0.09 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 23 | 0.00 | 0.08 | 0.28 | 0.03 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.03 | 0.09 | 0.01 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.03 | 0.01 | 0.00 | 0.14 | 0.00 | 0.00 |
| GPU≥50% | 23 | 0.04 | 0.00 | 0.00 | 0.22 | 0.00 | 0.00 |
| miss<10% | 418 | 0.04 | 0.03 | 0.00 | 0.13 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.02 | 0.09 | 0.01 | 0.01 | 0.00 | 0.00 | 0.04 | 0.00 |
| GPU≥50% | 23 | 0.04 | 0.20 | 0.03 | 0.00 | 0.00 | 0.00 | 0.06 | 0.00 |
| miss<10% | 418 | 0.24 | 0.25 | 0.01 | 0.04 | 0.00 | 0.00 | 0.10 | 0.48 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 23 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 21 | 19 / 0 / 2 | 512 | 512 | 239 (52–376) | 3 (352) |
| compute, no computed tokens (miss / GPU-prefix hit) | 333 | 333 / 0 / 0 | 128 | 256 | 117 (46–493) | 0 (600) |

Requests refused at least once: 38 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 565; reservation passed at admission p50 0 / max 388 blocks; free blocks at admission p50 2559.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.277 |
| time with free blocks < 50% of the pool | 0.188 |
| time with free blocks < 25% of the pool | 0.113 |
| time with free blocks < 10% of the pool | 0.047 |
| time with free blocks < 5% of the pool | 0.028 |
| blocks held by loads in transfer, mean / max | 67 / 1984 |
| in-flight prefill reservation after schedule(), mean / max | 47 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.131 |
| steps with a shortened token budget (share of time) | 0.097 |
| running requests, mean / max | 1.9 / 14 |
| waiting + kv-holding requests, mean / max | 1.2 / 29 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.34 | 0.00 | 0.87 / 0.17 | 0.37 [248] | 1.34 [127] | 0.55 [316] | 1.33 [59] |
| GPU≥50% | 23 | 0.48 | 0.00 | 0.66 / 0.14 | 0.19 [12] | 1.37 [11] | 0.24 [17] | 1.28 [6] |
| miss<10% | 418 | 0.41 | 0.00 | 0.95 / 0.17 | 0.70 [245] | 2.21 [173] | 1.20 [354] | 4.75 [64] |
