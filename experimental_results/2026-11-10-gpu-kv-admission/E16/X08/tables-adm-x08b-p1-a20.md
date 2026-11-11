## Admission analysis of `x08b-p1-a20` (544 requests, 21525 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 6176 | 384 | 15.21 / 42.74 | 3.67 / 5.67 | 0.83 / 5.08 | 0.00 / 4.39 | 0.79 / 0.77 | 0.00 / 0.02 | 0.48 / 0.60 |
| GPU≥50% | 201 | 6214 | 70 | 1.83 / 39.09 | 0.00 / 3.17 | 0.50 / 2.66 | 0.16 / 2.44 | 0.63 / 0.59 | 0.00 / 0.00 | 0.44 / 0.48 |
| 10–50% | 64 | 2103 | 93 | 8.39 / 36.85 | 0.00 / 4.38 | 0.62 / 2.49 | 1.01 / 4.98 | 0.79 / 0.58 | 0.00 / 0.37 | 0.75 / 1.05 |
| miss<10% | 164 | 13883 | 128 | 16.53 / 44.12 | 0.00 / 2.90 | 0.51 / 2.03 | 5.72 / 9.26 | 0.22 / 0.22 | 0.00 / 0.00 | 3.65 / 4.46 |
| mixed | 4 | 7023 | 384 | 30.73 / 32.45 | 8.90 / 7.17 | 7.76 / 6.02 | 13.52 / 10.10 | 0.17 / 0.44 | 0.00 / 0.00 | 0.57 / 0.50 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 15.93 | 3.17 [20%] | 0.36 [2%] | 8.50 [53%] | 1.01 [6%] | 0.16 [1%] | 0.70 [4%] | 0.37 [2%] | 0.75 [5%] | 0.08 [1%] | 0.84 [5%] | 0.00 [0%] | 0.01 [0%] |
| GPU≥50% | 201 | 8.31 | 1.94 [23%] | 0.22 [3%] | 3.87 [47%] | 0.56 [7%] | 0.01 [0%] | 0.11 [1%] | 0.02 [0%] | 0.36 [4%] | 0.04 [0%] | 1.18 [14%] | 0.00 [0%] | 0.00 [0%] |
| 10–50% | 64 | 11.91 | 3.11 [26%] | 0.36 [3%] | 5.32 [45%] | 0.39 [3%] | 0.00 [0%] | 0.15 [1%] | 0.00 [0%] | 0.41 [3%] | 0.00 [0%] | 2.07 [17%] | 0.00 [0%] | 0.10 [1%] |
| miss<10% | 164 | 14.19 | 2.06 [15%] | 0.54 [4%] | 5.48 [39%] | 0.34 [2%] | 0.00 [0%] | 1.92 [14%] | 0.00 [0%] | 0.41 [3%] | 0.00 [0%] | 3.36 [24%] | 0.00 [0%] | 0.06 [0%] |
| mixed | 4 | 23.74 | 0.62 [3%] | 0.99 [4%] | 13.63 [57%] | 2.07 [9%] | 0.03 [0%] | 1.08 [5%] | 0.00 [0%] | 0.78 [3%] | 0.09 [0%] | 4.42 [19%] | 0.03 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 1.91 | 0.16 | 3.51 | 0.08 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 201 | 1.22 | 0.12 | 1.81 | 0.03 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 1.81 | 0.07 | 2.43 | 0.06 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.94 | 0.09 | 1.84 | 0.04 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.62 | 0.87 | 5.68 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.36 | 0.09 | 3.32 | 0.77 | 0.00 | 0.00 | 0.53 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.16 | 0.05 | 1.58 | 0.52 | 0.00 | 0.00 | 0.35 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.25 | 0.09 | 1.46 | 0.30 | 0.00 | 0.00 | 0.40 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.05 | 0.04 | 1.26 | 0.27 | 0.00 | 0.00 | 0.41 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 3.28 | 2.07 | 0.00 | 0.00 | 0.63 | 0.00 | 0.00 | 0.03 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.88 | 0.10 | 1.36 | 0.06 | 0.69 | 0.37 | 0.00 | 0.08 | 0.84 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.56 | 0.05 | 0.49 | 0.00 | 0.11 | 0.02 | 0.00 | 0.04 | 1.18 | 0.00 | 0.00 |
| 10–50% | 64 | 1.06 | 0.19 | 1.43 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 | 2.07 | 0.00 | 0.10 |
| miss<10% | 164 | 1.08 | 0.42 | 2.38 | 0.03 | 1.92 | 0.00 | 0.00 | 0.00 | 3.36 | 0.00 | 0.06 |
| mixed | 4 | 0.00 | 0.11 | 4.40 | 0.00 | 1.08 | 0.00 | 0.00 | 0.09 | 4.42 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 |
| GPU≥50% | 201 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1852 | 1704 / 0 / 148 | 384 | 446 | 231 (28–973) | 0 (1866) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5661 | 5661 / 0 / 0 | 128 | 1085 | 702 (136–1256) | 0 (0) |
| promotion after a load | 24 | 24 / 0 / 0 | 36 | 36 | 12 (8–470) | 0 (0) |

Requests refused at least once: 148 of 544; preemptions: 6; running requests that could not get their next chunk: 13.
Admitted external loads: 130; reservation passed at admission p50 115 / max 1863 blocks; free blocks at admission p50 1394.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.631 |
| time with free blocks < 50% of the pool | 0.677 |
| time with free blocks < 25% of the pool | 0.560 |
| time with free blocks < 10% of the pool | 0.297 |
| time with free blocks < 5% of the pool | 0.172 |
| blocks held by loads in transfer, mean / max | 23 / 2160 |
| in-flight prefill reservation after schedule(), mean / max | 284 / 1898 |
| steps whose running requests used the whole token budget (share of time) | 0.133 |
| steps with a shortened token budget (share of time) | 0.158 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 5.2 / 34 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.77 | 0.21 | 0.13 / 0.03 | 15.94 [25] | 15.21 [86] | 2.78 [30] | 15.94 [81] |
| GPU≥50% | 201 | 0.57 | 0.11 | 0.54 / 0.03 | 0.27 [86] | 3.43 [115] | 0.91 [120] | 18.72 [81] |
| 10–50% | 64 | 0.58 | 0.14 | 0.23 / 0.05 | 1.33 [27] | 12.79 [37] | 1.08 [29] | 21.17 [35] |
| miss<10% | 164 | 0.65 | 0.07 | 0.41 / 0.04 | 5.61 [58] | 20.77 [106] | 12.34 [93] | 23.32 [71] |
| mixed | 4 | 1.00 | 0.50 | 0.16 / 0.14 | – | 30.73 [4] | – | 30.73 [4] |
