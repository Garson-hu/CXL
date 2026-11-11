## Admission analysis of `ccb-p3728-p2` (816 requests, 28059 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 2048 | 128 | 0.70 / 2.39 | 0.00 / 0.04 | 0.03 / 0.21 | 0.00 / 0.07 | 0.38 / 0.38 | 0.00 / 0.00 | 0.18 / 0.14 |
| GPU≥50% | 34 | 8192 | 256 | 0.31 / 5.85 | 0.00 / 0.14 | 0.03 / 0.33 | 0.00 / 0.11 | 0.22 / 0.34 | 0.00 / 0.01 | 0.03 / 0.11 |
| miss<10% | 418 | 2048 | 128 | 1.47 / 8.09 | 0.00 / 0.05 | 0.02 / 0.20 | 0.00 / 1.00 | – | – | 0.67 / 0.86 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.70 | 0.04 [5%] | 0.12 [17%] | 0.08 [12%] | 0.19 [27%] | 0.00 [0%] | 0.23 [33%] | 0.03 [5%] | 0.00 [0%] | 0.00 [0%] | 0.01 [1%] |
| GPU≥50% | 34 | 0.93 | 0.01 [1%] | 0.17 [19%] | 0.25 [27%] | 0.16 [17%] | 0.00 [0%] | 0.30 [32%] | 0.02 [2%] | 0.00 [0%] | 0.00 [0%] | 0.02 [2%] |
| miss<10% | 418 | 1.25 | 0.00 [0%] | 0.30 [24%] | 0.23 [18%] | 0.00 [0%] | 0.03 [3%] | 0.14 [11%] | 0.03 [3%] | 0.51 [41%] | 0.00 [0%] | 0.01 [1%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.00 | 0.01 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 34 | 0.00 | 0.04 | 0.09 | 0.00 | 0.00 | 0.00 | 0.01 |
| miss<10% | 418 | 0.00 | 0.02 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.03 | 0.02 | 0.15 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 34 | 0.05 | 0.07 | 0.20 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.04 | 0.02 | 0.14 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.01 | 0.02 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 34 | 0.03 | 0.06 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.24 | 0.17 | 0.03 | 0.00 | 0.03 | 0.51 | 0.00 | 0.01 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 34 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 180 | 180 / 0 / 0 | 128 | 512 | 251 (60–438) | 0 (600) |

Requests refused at least once: 23 of 816; preemptions: 3; running requests that could not get their next chunk: 6.
Admitted external loads: 566; reservation passed at admission p50 0 / max 387 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.221 |
| time with free blocks < 50% of the pool | 0.142 |
| time with free blocks < 25% of the pool | 0.090 |
| time with free blocks < 10% of the pool | 0.041 |
| time with free blocks < 5% of the pool | 0.019 |
| blocks held by loads in transfer, mean / max | 72 / 2624 |
| in-flight prefill reservation after schedule(), mean / max | 48 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.131 |
| steps with a shortened token budget (share of time) | 0.094 |
| running requests, mean / max | 2.3 / 16 |
| waiting + kv-holding requests, mean / max | 1.0 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 364 | 0.33 | 0.00 | 0.91 / 0.15 | 0.40 [244] | 1.39 [120] | 0.53 [306] | 1.51 [58] |
| GPU≥50% | 34 | 0.35 | 0.00 | 0.77 / 0.22 | 0.22 [22] | 1.53 [12] | 0.24 [29] | 3.03 [5] |
| miss<10% | 418 | 0.41 | 0.00 | 0.97 / 0.17 | 0.69 [248] | 2.09 [170] | 1.11 [352] | 4.50 [66] |
