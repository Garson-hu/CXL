## Admission analysis of `x08-skip30` (544 requests, 21646 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 6182 | 384 | 9.71 / 26.41 | 1.93 / 3.94 | 0.88 / 1.86 | 0.83 / 3.69 | 0.41 / 0.64 | 0.00 / 0.30 | 0.31 / 0.44 |
| GPU≥50% | 201 | 6198 | 59 | 3.83 / 22.18 | 0.39 / 2.65 | 0.72 / 1.35 | 0.00 / 2.07 | 0.16 / 0.64 | 0.00 / 0.39 | 0.34 / 0.41 |
| 10–50% | 64 | 2103 | 89 | 5.60 / 20.91 | 0.00 / 2.77 | 0.75 / 1.33 | 0.00 / 3.07 | 1.30 / 1.27 | 0.12 / 0.55 | 0.70 / 0.89 |
| miss<10% | 164 | 13883 | 128 | 12.54 / 46.70 | 0.58 / 2.43 | 0.77 / 2.16 | 0.00 / 7.11 | 2.19 / 2.19 | 0.00 / 0.00 | 3.22 / 4.15 |
| mixed | 3 | 6580 | 384 | 7.26 / 10.40 | 3.57 / 3.47 | 1.31 / 0.89 | 1.33 / 0.89 | 0.30 / 0.25 | 0.00 / 0.00 | 0.20 / 0.23 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 10.44 | 5.83 [56%] | 0.32 [3%] | 1.45 [14%] | 0.08 [1%] | 0.26 [3%] | 0.02 [0%] | 0.95 [9%] | 1.53 [15%] | 0.00 [0%] | 0.01 [0%] |
| GPU≥50% | 201 | 6.13 | 3.71 [61%] | 0.35 [6%] | 0.28 [4%] | 0.03 [0%] | 0.02 [0%] | 0.00 [0%] | 0.59 [10%] | 1.15 [19%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 64 | 7.28 | 4.24 [58%] | 0.34 [5%] | 1.02 [14%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.63 [9%] | 1.01 [14%] | 0.00 [0%] | 0.03 [0%] |
| miss<10% | 164 | 11.71 | 6.29 [54%] | 0.47 [4%] | 0.69 [6%] | 0.04 [0%] | 0.00 [0%] | 0.21 [2%] | 0.62 [5%] | 3.27 [28%] | 0.00 [0%] | 0.11 [1%] |
| mixed | 3 | 5.50 | 3.47 [63%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.23 [4%] | 0.00 [0%] | 0.92 [17%] | 0.89 [16%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 2.96 | 0.15 | 0.82 | 0.01 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 201 | 2.26 | 0.15 | 0.21 | 0.03 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 2.20 | 0.14 | 0.42 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 2.04 | 0.17 | 0.20 | 0.02 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 3.47 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.99 | 0.08 | 0.03 | 0.76 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.68 | 0.09 | 0.00 | 0.57 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.66 | 0.05 | 0.00 | 0.62 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 1.32 | 0.19 | 0.00 | 0.61 | 0.00 | 0.00 | 0.03 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.89 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 1.45 | 0.05 | 0.59 | 0.07 | 0.00 | 0.00 | 1.53 | 0.00 | 0.00 |
| GPU≥50% | 201 | 0.74 | 0.10 | 0.07 | 0.00 | 0.00 | 0.00 | 1.15 | 0.00 | 0.01 |
| 10–50% | 64 | 1.31 | 0.14 | 0.59 | 0.00 | 0.00 | 0.00 | 1.01 | 0.00 | 0.02 |
| miss<10% | 164 | 2.93 | 0.10 | 0.49 | 0.02 | 0.21 | 0.00 | 3.27 | 0.00 | 0.08 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.89 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.28 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.01 |
| GPU≥50% | 201 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 1668 | 1617 / 0 / 51 | 128 | 1980 | 624 (152–1353) | 0 (600) |
| promotion after a load | 32 | 32 / 0 / 0 | 46 | 46 | 30 (22–60) | 0 (0) |

Requests refused at least once: 19 of 544; preemptions: 9; running requests that could not get their next chunk: 18.
Admitted external loads: 133; reservation passed at admission p50 0 / max 332 blocks; free blocks at admission p50 752.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.612 |
| time with free blocks < 50% of the pool | 0.660 |
| time with free blocks < 25% of the pool | 0.522 |
| time with free blocks < 10% of the pool | 0.296 |
| time with free blocks < 5% of the pool | 0.154 |
| blocks held by loads in transfer, mean / max | 33 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 246 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.412 |
| running requests, mean / max | 6.3 / 16 |
| waiting + kv-holding requests, mean / max | 3.8 / 24 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.51 | 0.45 | 0.14 / 0.02 | 5.46 [55] | 11.93 [57] | 9.71 [37] | 9.55 [75] |
| GPU≥50% | 201 | 0.48 | 0.44 | 0.52 / 0.05 | 0.34 [104] | 8.05 [97] | 1.61 [125] | 7.90 [76] |
| 10–50% | 64 | 0.44 | 0.38 | 0.27 / 0.03 | 2.00 [36] | 7.15 [28] | 1.61 [34] | 15.68 [30] |
| miss<10% | 164 | 0.49 | 0.41 | 0.47 / 0.04 | 5.32 [84] | 17.28 [80] | 8.51 [100] | 20.57 [64] |
| mixed | 3 | 0.67 | 0.67 | 0.22 / 0.15 | 0.29 [1] | 10.40 [2] | – | 7.26 [3] |
