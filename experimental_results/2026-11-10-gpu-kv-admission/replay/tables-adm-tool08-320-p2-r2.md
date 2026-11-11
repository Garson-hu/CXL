## Admission analysis of `tool08-320-p2-r2` (544 requests, 21248 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 6187 | 384 | 11.63 / 36.31 | 0.30 / 3.66 | 0.77 / 1.56 | 0.00 / 7.05 | 0.98 / 0.90 | 0.00 / 0.01 | 0.63 / 0.74 |
| GPU≥50% | 203 | 6193 | 64 | 1.51 / 31.68 | 0.00 / 2.22 | 0.43 / 1.69 | 0.18 / 3.27 | 0.66 / 0.67 | 0.00 / 0.00 | 0.42 / 0.46 |
| 10–50% | 64 | 2103 | 89 | 8.22 / 47.29 | 0.00 / 2.55 | 0.51 / 1.01 | 3.22 / 9.65 | 0.78 / 0.70 | 0.00 / 0.03 | 0.70 / 1.08 |
| miss<10% | 164 | 13883 | 128 | 18.25 / 51.85 | 0.00 / 2.00 | 0.42 / 1.16 | 10.61 / 13.57 | 1.10 / 1.10 | 0.00 / 0.00 | 3.66 / 4.67 |
| mixed | 5 | 7056 | 193 | 32.63 / 44.51 | 1.54 / 1.50 | 0.82 / 1.20 | 27.13 / 26.49 | 1.06 / 0.78 | 0.00 / 0.00 | 0.68 / 0.76 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 13.18 | 0.02 [0%] | 0.21 [2%] | 8.62 [65%] | 0.50 [4%] | 0.36 [3%] | 0.45 [3%] | 0.34 [3%] | 0.84 [6%] | 0.37 [3%] | 0.19 [1%] | 1.25 [9%] | 0.01 [0%] | 0.04 [0%] |
| GPU≥50% | 203 | 7.20 | 0.00 [0%] | 0.20 [3%] | 4.55 [63%] | 0.41 [6%] | 0.01 [0%] | 0.04 [1%] | 0.01 [0%] | 0.43 [6%] | 0.38 [5%] | 0.07 [1%] | 1.06 [15%] | 0.00 [0%] | 0.03 [0%] |
| 10–50% | 64 | 13.26 | 0.00 [0%] | 0.32 [2%] | 7.45 [56%] | 0.46 [3%] | 0.02 [0%] | 0.10 [1%] | 0.00 [0%] | 0.46 [4%] | 0.08 [1%] | 0.02 [0%] | 4.19 [32%] | 0.00 [0%] | 0.14 [1%] |
| miss<10% | 164 | 16.73 | 0.00 [0%] | 0.55 [3%] | 7.41 [44%] | 0.41 [2%] | 0.00 [0%] | 2.54 [15%] | 0.00 [0%] | 0.43 [3%] | 0.13 [1%] | 0.02 [0%] | 5.17 [31%] | 0.00 [0%] | 0.06 [0%] |
| mixed | 5 | 29.98 | 0.00 [0%] | 1.01 [3%] | 21.96 [73%] | 2.59 [9%] | 0.17 [1%] | 0.55 [2%] | 0.00 [0%] | 0.77 [3%] | 1.26 [4%] | 0.00 [0%] | 1.66 [6%] | 0.01 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.00 | 0.04 | 3.45 | 0.16 | 0.00 | 0.00 | 0.00 | 0.02 |
| GPU≥50% | 203 | 0.00 | 0.05 | 2.02 | 0.14 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.04 | 2.32 | 0.19 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.03 | 1.81 | 0.14 | 0.00 | 0.00 | 0.00 | 0.02 |
| mixed | 5 | 0.00 | 0.01 | 1.49 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.04 | 0.88 | 0.03 | 0.61 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 203 | 0.09 | 1.07 | 0.11 | 0.42 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.04 | 0.48 | 0.00 | 0.45 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| miss<10% | 164 | 0.04 | 0.64 | 0.05 | 0.43 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.01 | 0.62 | 0.00 | 0.57 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.10 | 4.07 | 0.27 | 0.45 | 0.34 | 0.00 | 0.37 | 0.19 | 1.25 | 0.00 | 0.00 |
| GPU≥50% | 203 | 0.06 | 1.46 | 0.16 | 0.04 | 0.01 | 0.00 | 0.37 | 0.07 | 1.06 | 0.00 | 0.03 |
| 10–50% | 64 | 0.24 | 4.65 | 0.25 | 0.10 | 0.00 | 0.00 | 0.08 | 0.02 | 4.19 | 0.00 | 0.11 |
| miss<10% | 164 | 0.48 | 4.96 | 0.22 | 2.54 | 0.00 | 0.00 | 0.13 | 0.02 | 5.17 | 0.00 | 0.04 |
| mixed | 5 | 0.99 | 19.44 | 2.59 | 0.55 | 0.00 | 0.00 | 1.26 | 0.00 | 1.66 | 0.01 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 203 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 937 | 839 / 0 / 98 | 384 | 446 | 231 (140–498) | 0 (1800) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6491 | 6491 / 0 / 0 | 128 | 1085 | 610 (108–1678) | 0 (600) |

Requests refused at least once: 116 of 544; preemptions: 7; running requests that could not get their next chunk: 16.
Admitted external loads: 125; reservation passed at admission p50 302 / max 1954 blocks; free blocks at admission p50 1700.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.636 |
| time with free blocks < 50% of the pool | 0.684 |
| time with free blocks < 25% of the pool | 0.556 |
| time with free blocks < 10% of the pool | 0.304 |
| time with free blocks < 5% of the pool | 0.159 |
| blocks held by loads in transfer, mean / max | 28 / 2688 |
| in-flight prefill reservation after schedule(), mean / max | 306 / 2615 |
| steps whose running requests used the whole token budget (share of time) | 0.044 |
| steps with a shortened token budget (share of time) | 0.189 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 5.2 / 23 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.76 | 0.00 | 0.12 / 0.03 | 9.36 [26] | 15.23 [82] | 2.66 [30] | 14.84 [78] |
| GPU≥50% | 203 | 0.55 | 0.00 | 0.52 / 0.03 | 0.29 [91] | 2.03 [112] | 0.90 [117] | 15.96 [86] |
| 10–50% | 64 | 0.61 | 0.00 | 0.24 / 0.06 | 0.65 [25] | 18.03 [39] | 1.20 [31] | 18.88 [33] |
| miss<10% | 164 | 0.66 | 0.00 | 0.40 / 0.03 | 6.15 [56] | 22.40 [108] | 12.37 [88] | 28.53 [76] |
| mixed | 5 | 0.60 | 0.00 | 0.11 / 0.10 | 32.63 [2] | 42.80 [3] | – | 32.63 [5] |
