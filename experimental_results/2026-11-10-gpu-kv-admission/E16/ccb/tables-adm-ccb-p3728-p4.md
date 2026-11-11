## Admission analysis of `ccb-p3728-p4` (816 requests, 28218 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 2048 | 128 | 0.70 / 2.04 | 0.00 / 0.02 | 0.03 / 0.17 | 0.00 / 0.04 | 0.36 / 0.37 | 0.00 / 0.00 | 0.17 / 0.14 |
| GPU≥50% | 34 | 8192 | 256 | 0.58 / 1.96 | 0.00 / 0.02 | 0.03 / 0.22 | 0.00 / 0.04 | 0.18 / 0.26 | 0.00 / 0.00 | 0.03 / 0.10 |
| miss<10% | 418 | 2048 | 128 | 1.47 / 7.65 | 0.00 / 0.02 | 0.02 / 0.16 | 0.00 / 0.95 | – | – | 0.67 / 0.86 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.60 | 0.04 [6%] | 0.10 [16%] | 0.00 [0%] | 0.21 [34%] | 0.23 [37%] | 0.04 [6%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 34 | 0.54 | 0.01 [2%] | 0.07 [13%] | 0.00 [0%] | 0.18 [33%] | 0.25 [46%] | 0.03 [6%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 418 | 1.13 | 0.00 [0%] | 0.24 [21%] | 0.00 [0%] | 0.00 [0%] | 0.13 [12%] | 0.17 [15%] | 0.00 [0%] | 0.59 [52%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 34 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:tok | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.03 | 0.00 | 0.14 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 34 | 0.04 | 0.00 | 0.18 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.03 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.00 | 0.00 | 0.00 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 34 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.20 | 0.00 | 0.00 | 0.17 | 0.00 | 0.59 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 364 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 34 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 6 | 6 / 0 / 0 | 256 | 256 | 253 (252–253) | 0 (0) |

Requests refused at least once: 1 of 816; preemptions: 2; running requests that could not get their next chunk: 5.
Admitted external loads: 566; reservation passed at admission p50 0 / max 392 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.224 |
| time with free blocks < 50% of the pool | 0.143 |
| time with free blocks < 25% of the pool | 0.095 |
| time with free blocks < 10% of the pool | 0.040 |
| time with free blocks < 5% of the pool | 0.018 |
| blocks held by loads in transfer, mean / max | 70 / 2624 |
| in-flight prefill reservation after schedule(), mean / max | 48 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.131 |
| steps with a shortened token budget (share of time) | 0.096 |
| running requests, mean / max | 2.4 / 16 |
| waiting + kv-holding requests, mean / max | 0.9 / 21 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.33 | 0.00 | 0.91 / 0.15 | 0.39 [244] | 1.45 [120] | 0.54 [310] | 1.56 [54] |
| GPU≥50% | 34 | 0.41 | 0.00 | 0.81 / 0.09 | 0.20 [20] | 1.35 [14] | 0.23 [27] | 1.31 [7] |
| miss<10% | 418 | 0.40 | 0.00 | 0.97 / 0.15 | 0.69 [250] | 2.02 [168] | 1.08 [355] | 4.01 [63] |
