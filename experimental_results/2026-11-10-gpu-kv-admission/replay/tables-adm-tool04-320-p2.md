## Admission analysis of `tool04-320-p2` (1158 requests, 88167 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 125 | 7043 | 384 | 1.45 / 25.25 | 0.00 / 1.14 | 0.29 / 0.33 | 0.00 / 1.98 | 0.18 / 0.45 | 0.00 / 0.00 | 0.28 / 0.51 |
| GPU≥50% | 605 | 6182 | 386 | 0.31 / 4.25 | 0.00 / 0.05 | 0.03 / 0.27 | 0.00 / 0.49 | 0.75 / 0.66 | 0.00 / 0.00 | 0.22 / 0.31 |
| 10–50% | 122 | 2496 | 105 | 0.78 / 21.58 | 0.00 / 0.36 | 0.03 / 0.25 | 0.00 / 2.39 | 0.11 / 0.33 | 0.00 / 0.00 | 0.60 / 1.07 |
| miss<10% | 293 | 13689 | 128 | 5.31 / 29.70 | 0.00 / 0.19 | 0.03 / 0.27 | 0.00 / 3.64 | 0.05 / 0.04 | 0.00 / 0.00 | 3.16 / 4.21 |
| mixed | 13 | 1844 | 32 | 1.75 / 18.56 | 0.00 / 1.24 | 0.30 / 0.34 | 0.00 / 0.15 | 0.48 / 0.53 | 0.00 / 0.00 | 0.49 / 0.52 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 125 | 3.91 | 0.05 [1%] | 0.12 [3%] | 2.02 [52%] | 0.15 [4%] | 0.24 [6%] | 0.24 [6%] | 0.07 [2%] | 0.41 [11%] | 0.08 [2%] | 0.02 [0%] | 0.48 [12%] | 0.00 [0%] |
| GPU≥50% | 605 | 0.82 | 0.00 [0%] | 0.03 [4%] | 0.12 [15%] | 0.00 [0%] | 0.01 [1%] | 0.00 [0%] | 0.00 [0%] | 0.25 [31%] | 0.00 [0%] | 0.00 [0%] | 0.40 [48%] | 0.00 [0%] |
| 10–50% | 122 | 3.04 | 0.00 [0%] | 0.11 [4%] | 1.03 [34%] | 0.02 [1%] | 0.03 [1%] | 0.11 [4%] | 0.00 [0%] | 0.26 [9%] | 0.02 [1%] | 0.00 [0%] | 1.44 [47%] | 0.00 [0%] |
| miss<10% | 293 | 4.10 | 0.00 [0%] | 0.15 [4%] | 0.89 [22%] | 0.01 [0%] | 0.00 [0%] | 0.62 [15%] | 0.00 [0%] | 0.26 [6%] | 0.00 [0%] | 0.00 [0%] | 2.17 [53%] | 0.00 [0%] |
| mixed | 13 | 2.26 | 0.09 [4%] | 0.02 [1%] | 1.23 [55%] | 0.00 [0%] | 0.30 [13%] | 0.00 [0%] | 0.00 [0%] | 0.47 [21%] | 0.00 [0%] | 0.00 [0%] | 0.15 [7%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 125 | 0.00 | 0.03 | 1.06 | 0.05 | 0.00 | 0.00 |
| GPU≥50% | 605 | 0.00 | 0.01 | 0.04 | 0.00 | 0.00 | 0.00 |
| 10–50% | 122 | 0.00 | 0.01 | 0.33 | 0.02 | 0.00 | 0.00 |
| miss<10% | 293 | 0.00 | 0.01 | 0.17 | 0.01 | 0.00 | 0.00 |
| mixed | 13 | 0.00 | 0.00 | 1.23 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:resv | pol:tok |
|---|---|---|---|---|---|---|---|
| host≥50% | 125 | 0.00 | 0.00 | 0.32 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 605 | 0.01 | 0.02 | 0.25 | 0.00 | 0.00 | 0.00 |
| 10–50% | 122 | 0.00 | 0.00 | 0.25 | 0.00 | 0.00 | 0.00 |
| miss<10% | 293 | 0.01 | 0.01 | 0.26 | 0.00 | 0.00 | 0.00 |
| mixed | 13 | 0.01 | 0.00 | 0.33 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 125 | 0.08 | 0.91 | 0.09 | 0.24 | 0.07 | 0.00 | 0.08 | 0.02 | 0.48 | 0.00 |
| GPU≥50% | 605 | 0.02 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.40 | 0.00 |
| 10–50% | 122 | 0.10 | 0.71 | 0.01 | 0.11 | 0.00 | 0.00 | 0.02 | 0.00 | 1.44 | 0.00 |
| miss<10% | 293 | 0.14 | 0.71 | 0.00 | 0.62 | 0.00 | 0.00 | 0.00 | 0.00 | 2.17 | 0.00 |
| mixed | 13 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.15 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 125 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 605 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 122 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 293 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 13 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 765 | 745 / 0 / 20 | 384 | 511 | 362 (203–1495) | 0 (1728) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4129 | 4129 / 0 / 0 | 128 | 1700 | 868 (205–1737) | 0 (600) |

Requests refused at least once: 48 of 1158; preemptions: 3; running requests that could not get their next chunk: 6.
Admitted external loads: 173; reservation passed at admission p50 0 / max 1694 blocks; free blocks at admission p50 5790.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.258 |
| time with free blocks < 50% of the pool | 0.175 |
| time with free blocks < 25% of the pool | 0.092 |
| time with free blocks < 10% of the pool | 0.031 |
| time with free blocks < 5% of the pool | 0.015 |
| blocks held by loads in transfer, mean / max | 7 / 2160 |
| in-flight prefill reservation after schedule(), mean / max | 125 / 1962 |
| steps whose running requests used the whole token budget (share of time) | 0.070 |
| steps with a shortened token budget (share of time) | 0.081 |
| running requests, mean / max | 1.9 / 13 |
| waiting + kv-holding requests, mean / max | 0.5 / 9 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 125 | 0.49 | 0.00 | 0.79 / 0.24 | 0.27 [64] | 2.89 [61] | 0.76 [110] | 19.77 [15] |
| GPU≥50% | 605 | 0.37 | 0.00 | 0.81 / 0.39 | 0.16 [379] | 1.59 [226] | 0.29 [590] | 1.64 [15] |
| 10–50% | 122 | 0.37 | 0.00 | 0.80 / 0.35 | 0.45 [77] | 6.75 [45] | 0.73 [118] | 36.52 [4] |
| miss<10% | 293 | 0.39 | 0.00 | 0.82 / 0.42 | 2.63 [179] | 13.21 [114] | 5.30 [289] | 26.37 [4] |
| mixed | 13 | 0.46 | 0.00 | 0.74 / 0.12 | 0.29 [7] | 1.97 [6] | 1.11 [11] | 18.56 [2] |
