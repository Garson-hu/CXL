## Admission analysis of `t06-skip30` (853 requests, 46317 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 109 | 6180 | 384 | 6.05 / 20.28 | 1.41 / 3.64 | 1.01 / 1.72 | 0.00 / 0.59 | 0.40 / 0.62 | 0.00 / 0.43 | 0.30 / 0.43 |
| GPU≥50% | 386 | 6193 | 128 | 2.70 / 16.50 | 0.37 / 2.05 | 0.76 / 2.13 | 0.00 / 0.34 | 0.91 / 0.52 | 0.00 / 0.00 | 0.37 / 0.46 |
| 10–50% | 89 | 2103 | 86 | 2.76 / 16.00 | 0.00 / 2.25 | 0.71 / 1.42 | 0.00 / 0.36 | 0.89 / 0.82 | 0.00 / 0.79 | 0.51 / 0.78 |
| miss<10% | 264 | 14041 | 128 | 8.55 / 36.84 | 0.00 / 2.36 | 0.79 / 2.19 | 0.00 / 2.66 | 0.01 / 0.01 | 0.00 / 0.00 | 3.34 / 4.15 |
| mixed | 5 | 1661 | 32 | 8.27 / 12.41 | 1.75 / 1.89 | 1.31 / 1.48 | 0.00 / 0.08 | 1.58 / 1.17 | 1.48 / 1.61 | 1.10 / 0.84 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 109 | 7.01 | 4.60 [66%] | 0.21 [3%] | 0.55 [8%] | 0.26 [4%] | 0.01 [0%] | 0.94 [13%] | 0.44 [6%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 386 | 4.52 | 3.07 [68%] | 0.38 [8%] | 0.16 [4%] | 0.00 [0%] | 0.00 [0%] | 0.63 [14%] | 0.26 [6%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 89 | 4.12 | 2.79 [68%] | 0.30 [7%] | 0.14 [3%] | 0.01 [0%] | 0.00 [0%] | 0.61 [15%] | 0.27 [7%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 264 | 7.20 | 4.28 [59%] | 0.37 [5%] | 0.37 [5%] | 0.00 [0%] | 0.10 [1%] | 0.63 [9%] | 1.45 [20%] | 0.00 [0%] | 0.01 [0%] |
| mixed | 5 | 6.23 | 4.14 [67%] | 0.28 [4%] | 0.00 [0%] | 0.23 [4%] | 0.16 [3%] | 1.33 [21%] | 0.08 [1%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 109 | 3.09 | 0.04 | 0.51 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 386 | 1.77 | 0.13 | 0.14 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 2.00 | 0.13 | 0.12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 264 | 2.00 | 0.11 | 0.24 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 1.88 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | pol:blocks |
|---|---|---|---|---|---|
| host≥50% | 109 | 0.77 | 0.12 | 0.83 | 0.00 |
| GPU≥50% | 386 | 1.27 | 0.23 | 0.62 | 0.00 |
| 10–50% | 89 | 0.67 | 0.14 | 0.60 | 0.00 |
| miss<10% | 264 | 1.36 | 0.20 | 0.63 | 0.00 |
| mixed | 5 | 0.31 | 0.01 | 1.17 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 109 | 0.10 | 0.01 | 0.04 | 0.00 | 0.00 | 0.44 | 0.00 | 0.00 |
| GPU≥50% | 386 | 0.04 | 0.02 | 0.02 | 0.00 | 0.00 | 0.26 | 0.00 | 0.01 |
| 10–50% | 89 | 0.05 | 0.02 | 0.02 | 0.00 | 0.00 | 0.27 | 0.00 | 0.00 |
| miss<10% | 264 | 0.92 | 0.06 | 0.13 | 0.10 | 0.00 | 1.45 | 0.00 | 0.01 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.08 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 109 | 0.41 | 0.01 | 0.00 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 386 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 89 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 264 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 1.33 | 0.11 | 0.00 | 0.16 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 1195 | 1195 / 0 / 0 | 128 | 1158 | 596 (83–1908) | 0 (0) |
| promotion after a load | 29 | 29 / 0 / 0 | 33 | 33 | 7 (0–69) | 0 (0) |

Requests refused at least once: 15 of 853; preemptions: 7; running requests that could not get their next chunk: 14.
Admitted external loads: 126; reservation passed at admission p50 0 / max 307 blocks; free blocks at admission p50 3836.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.412 |
| time with free blocks < 50% of the pool | 0.384 |
| time with free blocks < 25% of the pool | 0.233 |
| time with free blocks < 10% of the pool | 0.119 |
| time with free blocks < 5% of the pool | 0.060 |
| blocks held by loads in transfer, mean / max | 16 / 2400 |
| in-flight prefill reservation after schedule(), mean / max | 197 / 1991 |
| steps whose running requests used the whole token budget (share of time) | 0.325 |
| running requests, mean / max | 3.8 / 16 |
| waiting + kv-holding requests, mean / max | 1.9 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 109 | 0.66 | 0.60 | 0.70 / 0.08 | 1.02 [37] | 9.67 [72] | 3.53 [82] | 10.65 [27] |
| GPU≥50% | 386 | 0.50 | 0.43 | 0.69 / 0.27 | 0.24 [194] | 7.46 [192] | 1.99 [349] | 6.39 [37] |
| 10–50% | 89 | 0.45 | 0.39 | 0.71 / 0.28 | 0.54 [49] | 8.55 [40] | 2.55 [82] | 14.01 [7] |
| miss<10% | 264 | 0.46 | 0.40 | 0.74 / 0.24 | 3.62 [143] | 12.50 [121] | 7.76 [236] | 26.74 [28] |
| mixed | 5 | 0.80 | 0.80 | 0.85 / 0.10 | 2.25 [1] | 9.32 [4] | 9.32 [4] | 5.17 [1] |
