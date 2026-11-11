## Admission analysis of `cc-p7456-p2` (816 requests, 21846 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 333 | 2048 | 128 | 0.70 / 2.42 | 0.00 / 0.04 | 0.03 / 0.21 | 0.00 / 0.00 | 0.38 / 0.39 | 0.00 / 0.03 | 0.17 / 0.14 |
| GPU≥50% | 65 | 4096 | 256 | 0.56 / 2.47 | 0.00 / 0.06 | 0.03 / 0.24 | 0.00 / 0.00 | 0.22 / 0.31 | 0.00 / 0.02 | 0.03 / 0.13 |
| miss<10% | 418 | 2048 | 128 | 1.44 / 7.87 | 0.00 / 0.04 | 0.02 / 0.20 | 0.00 / 0.92 | – | – | 0.67 / 0.88 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 333 | 0.67 | 0.04 [5%] | 0.13 [20%] | 0.19 [29%] | 0.22 [33%] | 0.00 [0%] | 0.09 [13%] |
| GPU≥50% | 65 | 0.63 | 0.03 [4%] | 0.09 [15%] | 0.15 [24%] | 0.24 [37%] | 0.00 [0%] | 0.12 [20%] |
| miss<10% | 418 | 1.16 | 0.00 [0%] | 0.31 [27%] | 0.00 [0%] | 0.12 [11%] | 0.48 [41%] | 0.25 [21%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 333 | 0.00 | 0.02 | 0.00 | 0.00 | 0.02 |
| GPU≥50% | 65 | 0.00 | 0.02 | 0.00 | 0.00 | 0.05 |
| miss<10% | 418 | 0.00 | 0.02 | 0.00 | 0.00 | 0.03 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok | slots |
|---|---|---|---|---|---|
| host≥50% | 333 | 0.04 | 0.14 | 0.00 | 0.03 |
| GPU≥50% | 65 | 0.03 | 0.17 | 0.00 | 0.04 |
| miss<10% | 418 | 0.05 | 0.12 | 0.00 | 0.03 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok | slots |
|---|---|---|---|---|---|
| host≥50% | 333 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 65 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.25 | 0.00 | 0.48 | 0.19 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 333 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| GPU≥50% | 65 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 561; reservation passed at admission p50 0 / max 387 blocks; free blocks at admission p50 7390.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.122 |
| time with free blocks < 50% of the pool | 0.052 |
| time with free blocks < 25% of the pool | 0.002 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 63 / 3648 |
| in-flight prefill reservation after schedule(), mean / max | 52 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.136 |
| steps with a shortened token budget (share of time) | 0.102 |
| running requests, mean / max | 2.6 / 16 |
| waiting + kv-holding requests, mean / max | 1.0 / 27 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 333 | 0.26 | 0.00 | 0.97 / 0.54 | 0.43 [245] | 1.50 [88] | 0.70 [332] | 5.14 [1] |
| GPU≥50% | 65 | 0.40 | 0.00 | 0.92 / 0.51 | 0.11 [39] | 1.44 [26] | 0.56 [64] | 4.15 [1] |
| miss<10% | 418 | 0.36 | 0.00 | 0.98 / 0.55 | 0.73 [269] | 1.84 [149] | 1.44 [416] | 12.51 [2] |
