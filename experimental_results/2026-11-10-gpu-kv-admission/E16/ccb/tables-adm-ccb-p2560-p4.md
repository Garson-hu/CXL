## Admission analysis of `ccb-p2560-p4` (816 requests, 28445 engine steps, pool 2560 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 374 | 2048 | 128 | 0.64 / 1.88 | 0.00 / 0.01 | 0.03 / 0.15 | 0.00 / 0.06 | 0.34 / 0.34 | 0.00 / 0.00 | 0.03 / 0.12 |
| GPU≥50% | 24 | 8192 | 256 | 0.81 / 1.62 | 0.00 / 0.01 | 0.23 / 0.26 | 0.00 / 0.11 | 0.21 / 0.26 | 0.00 / 0.00 | 0.03 / 0.10 |
| miss<10% | 418 | 2048 | 128 | 1.42 / 8.25 | 0.00 / 0.01 | 0.02 / 0.15 | 0.00 / 1.12 | – | – | 0.67 / 0.83 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 374 | 0.57 | 0.03 [6%] | 0.10 [17%] | 0.19 [34%] | 0.20 [35%] | 0.05 [9%] | 0.00 [0%] |
| GPU≥50% | 24 | 0.64 | 0.00 [0%] | 0.12 [19%] | 0.16 [24%] | 0.28 [44%] | 0.08 [12%] | 0.00 [0%] |
| miss<10% | 418 | 1.27 | 0.00 [0%] | 0.28 [22%] | 0.00 [0%] | 0.12 [9%] | 0.31 [24%] | 0.57 [44%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 374 | 0.00 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 24 | 0.00 | 0.01 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.01 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|
| host≥50% | 374 | 0.02 | 0.13 | 0.00 | 0.00 |
| GPU≥50% | 24 | 0.04 | 0.21 | 0.00 | 0.00 |
| miss<10% | 418 | 0.03 | 0.12 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|
| host≥50% | 374 | 0.01 | 0.00 | 0.05 | 0.00 |
| GPU≥50% | 24 | 0.03 | 0.00 | 0.08 | 0.00 |
| miss<10% | 418 | 0.24 | 0.00 | 0.31 | 0.56 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 374 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 24 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 566; reservation passed at admission p50 0 / max 389 blocks; free blocks at admission p50 2559.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.280 |
| time with free blocks < 50% of the pool | 0.188 |
| time with free blocks < 25% of the pool | 0.117 |
| time with free blocks < 10% of the pool | 0.055 |
| time with free blocks < 5% of the pool | 0.033 |
| blocks held by loads in transfer, mean / max | 66 / 1856 |
| in-flight prefill reservation after schedule(), mean / max | 47 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.132 |
| steps with a shortened token budget (share of time) | 0.092 |
| running requests, mean / max | 2.0 / 14 |
| waiting + kv-holding requests, mean / max | 1.0 / 22 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 374 | 0.35 | 0.00 | 0.87 / 0.15 | 0.37 [244] | 1.32 [130] | 0.55 [313] | 1.06 [61] |
| GPU≥50% | 24 | 0.46 | 0.00 | 0.66 / 0.11 | 0.19 [13] | 1.37 [11] | 0.24 [16] | 1.23 [8] |
| miss<10% | 418 | 0.41 | 0.00 | 0.95 / 0.17 | 0.69 [245] | 2.02 [173] | 1.16 [361] | 3.05 [57] |
