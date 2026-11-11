## Admission analysis of `cc-p2560-p2` (816 requests, 23024 engine steps, pool 2560 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 2048 | 128 | 0.65 / 2.27 | 0.00 / 0.09 | 0.02 / 0.18 | 0.00 / 0.13 | 0.36 / 0.35 | 0.00 / 0.00 | 0.03 / 0.12 |
| GPU≥50% | 23 | 8192 | 256 | 0.67 / 5.46 | 0.00 / 0.19 | 0.21 / 0.22 | 0.00 / 0.29 | 0.17 / 0.30 | 0.00 / 0.00 | 0.03 / 0.11 |
| miss<10% | 418 | 2048 | 128 | 1.42 / 7.97 | 0.00 / 0.10 | 0.02 / 0.17 | 0.00 / 1.10 | – | – | 0.64 / 0.81 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.74 | 0.04 [5%] | 0.11 [15%] | 0.15 [20%] | 0.02 [3%] | 0.18 [24%] | 0.01 [1%] | 0.00 [0%] | 0.20 [27%] | 0.04 [5%] | 0.00 [0%] |
| GPU≥50% | 23 | 0.99 | 0.01 [1%] | 0.09 [9%] | 0.35 [35%] | 0.09 [9%] | 0.16 [16%] | 0.00 [0%] | 0.00 [0%] | 0.26 [27%] | 0.02 [2%] | 0.00 [0%] |
| miss<10% | 418 | 1.37 | 0.00 [0%] | 0.28 [20%] | 0.32 [24%] | 0.03 [2%] | 0.00 [0%] | 0.04 [3%] | 0.00 [0%] | 0.11 [8%] | 0.10 [7%] | 0.49 [36%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.00 | 0.02 | 0.06 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 23 | 0.00 | 0.02 | 0.13 | 0.04 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.02 | 0.07 | 0.02 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.03 | 0.02 | 0.00 | 0.13 | 0.00 | 0.00 |
| GPU≥50% | 23 | 0.02 | 0.00 | 0.00 | 0.19 | 0.00 | 0.00 |
| miss<10% | 418 | 0.04 | 0.02 | 0.00 | 0.11 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.01 | 0.06 | 0.01 | 0.01 | 0.00 | 0.00 | 0.04 | 0.00 |
| GPU≥50% | 23 | 0.03 | 0.19 | 0.04 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 |
| miss<10% | 418 | 0.23 | 0.24 | 0.01 | 0.04 | 0.00 | 0.00 | 0.10 | 0.49 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 23 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 12 | 9 / 0 / 3 | 512 | 512 | 372 (113–502) | 65 (257) |
| compute, no computed tokens (miss / GPU-prefix hit) | 389 | 389 / 0 / 0 | 128 | 256 | 119 (47–440) | 0 (600) |

Requests refused at least once: 37 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 565; reservation passed at admission p50 0 / max 388 blocks; free blocks at admission p50 2559.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.271 |
| time with free blocks < 50% of the pool | 0.186 |
| time with free blocks < 25% of the pool | 0.109 |
| time with free blocks < 10% of the pool | 0.043 |
| time with free blocks < 5% of the pool | 0.028 |
| blocks held by loads in transfer, mean / max | 57 / 1984 |
| in-flight prefill reservation after schedule(), mean / max | 47 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.135 |
| steps with a shortened token budget (share of time) | 0.095 |
| running requests, mean / max | 1.9 / 14 |
| waiting + kv-holding requests, mean / max | 1.1 / 28 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 375 | 0.29 | 0.00 | 0.90 / 0.19 | 0.41 [266] | 1.30 [109] | 0.53 [318] | 1.23 [57] |
| GPU≥50% | 23 | 0.43 | 0.00 | 0.66 / 0.16 | 0.20 [13] | 1.18 [10] | 0.23 [17] | 1.15 [6] |
| miss<10% | 418 | 0.36 | 0.00 | 0.95 / 0.21 | 0.69 [267] | 1.81 [151] | 1.15 [361] | 4.09 [57] |
