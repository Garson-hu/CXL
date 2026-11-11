## Admission analysis of `s4-p3728-p2` (480 requests, 13491 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 151 | 8192 | 512 | 0.10 / 4.42 | 0.00 / 0.13 | 0.02 / 0.25 | 0.00 / 0.16 | 0.05 / 0.22 | 0.00 / 0.00 | 0.02 / 0.06 |
| GPU≥50% | 67 | 2048 | 128 | 0.08 / 1.60 | 0.00 / 0.05 | 0.02 / 0.07 | 0.00 / 0.02 | 0.04 / 0.10 | 0.00 / 0.00 | 0.02 / 0.05 |
| miss<10% | 262 | 8192 | 128 | 1.42 / 39.59 | 0.00 / 0.13 | 0.04 / 0.29 | 0.00 / 8.28 | – | – | 1.40 / 1.08 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.76 | 0.00 [1%] | 0.05 [6%] | 0.36 [47%] | 0.10 [13%] | 0.00 [0%] | 0.18 [24%] | 0.07 [9%] | 0.00 [0%] |
| GPU≥50% | 67 | 0.24 | 0.00 [0%] | 0.02 [10%] | 0.07 [30%] | 0.05 [20%] | 0.00 [0%] | 0.08 [35%] | 0.01 [6%] | 0.00 [0%] |
| miss<10% | 262 | 8.70 | 0.00 [0%] | 1.14 [13%] | 4.48 [51%] | 0.00 [0%] | 0.39 [4%] | 0.19 [2%] | 0.04 [0%] | 2.47 [28%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.00 | 0.01 | 0.12 | 0.00 | 0.00 |
| GPU≥50% | 67 | 0.00 | 0.01 | 0.04 | 0.00 | 0.00 |
| miss<10% | 262 | 0.00 | 0.02 | 0.11 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.02 | 0.11 | 0.13 | 0.00 | 0.00 |
| GPU≥50% | 67 | 0.00 | 0.01 | 0.06 | 0.00 | 0.00 |
| miss<10% | 262 | 0.02 | 0.08 | 0.19 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.01 | 0.07 | 0.00 | 0.00 | 0.07 | 0.00 |
| GPU≥50% | 67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |
| miss<10% | 262 | 1.10 | 4.29 | 0.39 | 0.00 | 0.04 | 2.47 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|
| host≥50% | 151 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 67 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 262 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 491 | 491 / 0 / 0 | 1 | 512 | 135 (131–390) | 0 (512) |

Requests refused at least once: 82 of 480; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 298; reservation passed at admission p50 0 / max 386 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.428 |
| time with free blocks < 50% of the pool | 0.418 |
| time with free blocks < 25% of the pool | 0.354 |
| time with free blocks < 10% of the pool | 0.191 |
| time with free blocks < 5% of the pool | 0.116 |
| blocks held by loads in transfer, mean / max | 50 / 2048 |
| in-flight prefill reservation after schedule(), mean / max | 91 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.110 |
| steps with a shortened token budget (share of time) | 0.099 |
| running requests, mean / max | 3.2 / 9 |
| waiting + kv-holding requests, mean / max | 5.2 / 32 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 151 | 0.29 | 0.00 | 0.96 / 0.06 | 0.06 [107] | 1.75 [44] | 0.07 [114] | 2.35 [37] |
| GPU≥50% | 67 | 0.21 | 0.00 | 0.97 / 0.17 | 0.04 [53] | 1.26 [14] | 0.04 [58] | 1.41 [9] |
| miss<10% | 262 | 0.45 | 0.00 | 0.86 / 0.11 | 0.35 [145] | 17.05 [117] | 0.46 [206] | 20.15 [56] |
