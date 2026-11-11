## Admission analysis of `s4-p7456-p1` (480 requests, 13014 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 2048 | 128 | 0.10 / 2.13 | 0.00 / 0.02 | 0.02 / 0.13 | 0.00 / 0.00 | 0.05 / 0.26 | 0.00 / 0.00 | 0.02 / 0.10 |
| GPU≥50% | 85 | 8192 | 128 | 0.09 / 2.16 | 0.00 / 0.02 | 0.02 / 0.13 | 0.00 / 0.04 | 0.04 / 0.18 | 0.00 / 0.00 | 0.02 / 0.08 |
| miss<10% | 263 | 8192 | 102 | 1.42 / 40.03 | 0.00 / 0.03 | 0.20 / 0.22 | 0.00 / 8.60 | – | – | 1.41 / 1.26 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 0.41 | 0.00 [1%] | 0.06 [15%] | 0.05 [11%] | 0.14 [34%] | 0.00 [0%] | 0.16 [38%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 85 | 0.38 | 0.00 [0%] | 0.06 [17%] | 0.04 [10%] | 0.10 [26%] | 0.00 [0%] | 0.14 [38%] | 0.03 [8%] | 0.00 [1%] |
| miss<10% | 263 | 8.86 | 0.00 [0%] | 2.04 [23%] | 0.08 [1%] | 0.00 [0%] | 0.01 [0%] | 0.19 [2%] | 6.53 [74%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 132 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 85 | 0.00 | 0.01 | 0.01 | 0.00 | 0.00 |
| miss<10% | 263 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:tok | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 0.02 | 0.01 | 0.00 | 0.11 | 0.00 | 0.00 |
| GPU≥50% | 85 | 0.02 | 0.02 | 0.00 | 0.09 | 0.00 | 0.00 |
| miss<10% | 263 | 0.03 | 0.01 | 0.00 | 0.19 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:tok | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 85 | 0.01 | 0.01 | 0.00 | 0.00 | 0.03 | 0.00 |
| miss<10% | 263 | 1.98 | 0.07 | 0.01 | 0.00 | 6.53 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|
| host≥50% | 132 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 85 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 263 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1 | 1 / 0 / 0 | 512 | 512 | 504 (504–504) | 242 (242) |
| compute, no computed tokens (miss / GPU-prefix hit) | 19 | 19 / 0 / 0 | 1 | 512 | 412 (284–497) | 0 (0) |

Requests refused at least once: 7 of 480; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 296; reservation passed at admission p50 0 / max 394 blocks; free blocks at admission p50 7455.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.290 |
| time with free blocks < 50% of the pool | 0.328 |
| time with free blocks < 25% of the pool | 0.053 |
| time with free blocks < 10% of the pool | 0.018 |
| time with free blocks < 5% of the pool | 0.004 |
| blocks held by loads in transfer, mean / max | 60 / 2560 |
| in-flight prefill reservation after schedule(), mean / max | 121 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.109 |
| steps with a shortened token budget (share of time) | 0.123 |
| running requests, mean / max | 4.4 / 16 |
| waiting + kv-holding requests, mean / max | 5.2 / 32 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 0.30 | 0.00 | 0.98 / 0.23 | 0.06 [93] | 1.65 [39] | 0.09 [117] | 2.01 [15] |
| GPU≥50% | 85 | 0.29 | 0.00 | 0.98 / 0.21 | 0.04 [60] | 1.65 [25] | 0.04 [74] | 2.02 [11] |
| miss<10% | 263 | 0.48 | 0.00 | 0.93 / 0.30 | 0.34 [136] | 18.38 [127] | 0.62 [239] | 14.15 [24] |
