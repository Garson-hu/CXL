## Admission analysis of `x08-p2-skip100` (544 requests, 20830 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 6178 | 384 | 2.50 / 10.39 | 0.00 / 0.16 | 0.39 / 0.38 | 0.00 / 1.86 | 0.56 / 0.60 | 0.00 / 0.03 | 0.38 / 0.58 |
| GPU≥50% | 229 | 6231 | 62 | 1.30 / 12.75 | 0.00 / 0.11 | 0.33 / 0.33 | 0.17 / 1.87 | 0.75 / 0.79 | 0.00 / 0.00 | 0.43 / 0.47 |
| 10–50% | 64 | 2103 | 89 | 3.64 / 18.09 | 0.00 / 0.06 | 0.40 / 0.35 | 1.96 / 4.16 | 0.86 / 0.77 | 0.00 / 0.95 | 0.65 / 0.97 |
| miss<10% | 164 | 13883 | 128 | 13.86 / 54.46 | 0.00 / 0.03 | 0.35 / 0.36 | 8.65 / 13.33 | 0.79 / 0.79 | 0.00 / 0.00 | 3.70 / 4.54 |
| mixed | 4 | 7125 | 245 | 6.12 / 9.63 | 0.00 / 0.00 | 0.42 / 0.34 | 4.83 / 3.78 | 0.12 / 0.42 | 0.00 / 0.00 | 0.60 / 0.95 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 3.02 | 0.02 [1%] | 0.04 [1%] | 0.15 [5%] | 0.21 [7%] | 0.44 [15%] | 0.02 [1%] | 0.50 [16%] | 1.37 [46%] | 0.03 [1%] | 0.23 [8%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 229 | 2.37 | 0.00 [0%] | 0.09 [4%] | 0.14 [6%] | 0.04 [2%] | 0.03 [1%] | 0.00 [0%] | 0.32 [13%] | 0.68 [28%] | 0.02 [1%] | 1.03 [43%] | 0.00 [0%] | 0.02 [1%] |
| 10–50% | 64 | 4.68 | 0.00 [0%] | 0.19 [4%] | 0.05 [1%] | 0.10 [2%] | 0.03 [1%] | 0.06 [1%] | 0.36 [8%] | 0.79 [17%] | 0.07 [1%] | 3.02 [64%] | 0.01 [0%] | 0.00 [0%] |
| miss<10% | 164 | 13.72 | 0.00 [0%] | 0.54 [4%] | 0.23 [2%] | 0.09 [1%] | 0.00 [0%] | 0.00 [0%] | 0.33 [2%] | 4.00 [29%] | 0.19 [1%] | 8.29 [60%] | 0.00 [0%] | 0.05 [0%] |
| mixed | 4 | 4.54 | 0.00 [0%] | 0.01 [0%] | 0.15 [3%] | 0.00 [0%] | 0.31 [7%] | 0.00 [0%] | 0.46 [10%] | 2.97 [65%] | 0.06 [1%] | 0.58 [13%] | 0.01 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.00 | 0.00 | 0.06 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 229 | 0.00 | 0.01 | 0.06 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.01 | 0.00 | 0.01 | 0.36 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 229 | 0.01 | 0.00 | 0.00 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.34 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.01 | 0.02 | 0.00 | 0.33 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.34 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.04 | 0.07 | 0.10 | 0.00 | 1.37 | 0.03 | 0.23 | 0.00 | 0.00 |
| GPU≥50% | 229 | 0.07 | 0.07 | 0.01 | 0.00 | 0.68 | 0.02 | 1.03 | 0.00 | 0.00 |
| 10–50% | 64 | 0.18 | 0.05 | 0.04 | 0.00 | 0.79 | 0.07 | 3.02 | 0.01 | 0.00 |
| miss<10% | 164 | 0.53 | 0.19 | 0.09 | 0.00 | 4.00 | 0.19 | 8.29 | 0.00 | 0.05 |
| mixed | 4 | 0.01 | 0.15 | 0.00 | 0.00 | 2.97 | 0.06 | 0.58 | 0.01 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.00 | 0.01 | 0.00 | 0.02 | 0.00 | 0.00 |
| GPU≥50% | 229 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.06 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 385 | 221 / 0 / 164 | 678 | 678 | 660 (584–1108) | 600 (600) |
| promotion after a load | 59 | 59 / 0 / 0 | 24 | 24 | 17 (1–803) | 0 (0) |

Requests refused at least once: 10 of 544; preemptions: 8; running requests that could not get their next chunk: 16.
Admitted external loads: 108; reservation passed at admission p50 75 / max 1850 blocks; free blocks at admission p50 968.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.635 |
| time with free blocks < 50% of the pool | 0.690 |
| time with free blocks < 25% of the pool | 0.541 |
| time with free blocks < 10% of the pool | 0.309 |
| time with free blocks < 5% of the pool | 0.156 |
| blocks held by loads in transfer, mean / max | 21 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 291 / 2511 |
| steps whose running requests used the whole token budget (share of time) | 0.075 |
| steps with a shortened token budget (share of time) | 0.160 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 2.6 / 16 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 83 | 0.58 | 0.00 | 0.12 / 0.01 | 1.78 [35] | 2.51 [48] | 2.14 [22] | 2.79 [61] |
| GPU≥50% | 229 | 0.57 | 0.00 | 0.34 / 0.04 | 0.33 [98] | 1.64 [131] | 1.03 [125] | 1.72 [104] |
| 10–50% | 64 | 0.66 | 0.00 | 0.26 / 0.02 | 0.66 [22] | 5.57 [42] | 1.46 [32] | 4.37 [32] |
| miss<10% | 164 | 0.64 | 0.00 | 0.42 / 0.03 | 4.22 [59] | 16.07 [105] | 12.30 [89] | 15.86 [75] |
| mixed | 4 | 0.25 | 0.00 | 0.03 / 0.01 | 3.87 [3] | 6.12 [1] | – | 6.12 [4] |
