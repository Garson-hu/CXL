## Admission analysis of `x08b-skip` (544 requests, 22173 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 6176 | 384 | 11.19 / 35.57 | 3.26 / 4.62 | 0.76 / 2.38 | 0.05 / 5.90 | 0.43 / 0.67 | 0.00 / 0.17 | 0.33 / 0.43 |
| GPU≥50% | 202 | 6231 | 62 | 4.13 / 34.57 | 0.73 / 4.13 | 0.75 / 1.98 | 0.00 / 2.10 | 0.90 / 0.77 | 0.00 / 0.51 | 0.39 / 0.49 |
| 10–50% | 64 | 2103 | 78 | 4.52 / 28.12 | 0.68 / 4.19 | 0.86 / 2.33 | 0.00 / 1.83 | 1.83 / 1.26 | 0.43 / 0.52 | 0.75 / 0.90 |
| miss<10% | 164 | 13883 | 128 | 12.79 / 42.75 | 1.19 / 3.89 | 0.76 / 3.17 | 0.00 / 4.53 | 1.27 / 1.27 | 1.68 / 1.68 | 3.19 / 4.11 |
| mixed | 6 | 6686 | 190 | 44.12 / 44.75 | 2.89 / 8.58 | 0.69 / 0.69 | 41.41 / 21.16 | 0.89 / 0.77 | 0.38 / 0.26 | 0.49 / 0.57 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 13.73 | 7.54 [55%] | 0.71 [5%] | 3.16 [23%] | 0.15 [1%] | 0.21 [2%] | 0.40 [3%] | 0.00 [0%] | 0.83 [6%] | 0.65 [5%] | 0.00 [0%] | 0.08 [1%] |
| GPU≥50% | 202 | 8.26 | 4.79 [58%] | 0.51 [6%] | 1.91 [23%] | 0.08 [1%] | 0.01 [0%] | 0.01 [0%] | 0.00 [0%] | 0.49 [6%] | 0.38 [5%] | 0.00 [0%] | 0.08 [1%] |
| 10–50% | 64 | 8.45 | 4.77 [56%] | 0.54 [6%] | 1.92 [23%] | 0.06 [1%] | 0.01 [0%] | 0.03 [0%] | 0.00 [0%] | 0.52 [6%] | 0.45 [5%] | 0.00 [0%] | 0.16 [2%] |
| miss<10% | 164 | 11.61 | 6.37 [55%] | 0.59 [5%] | 2.30 [20%] | 0.09 [1%] | 0.00 [0%] | 0.76 [7%] | 0.00 [0%] | 0.57 [5%] | 0.77 [7%] | 0.00 [0%] | 0.16 [1%] |
| mixed | 6 | 31.48 | 14.81 [47%] | 0.76 [2%] | 12.92 [41%] | 0.99 [3%] | 0.11 [0%] | 0.68 [2%] | 0.00 [0%] | 0.72 [2%] | 0.47 [1%] | 0.02 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 3.26 | 0.27 | 1.08 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 202 | 2.77 | 0.15 | 1.16 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 2.72 | 0.11 | 1.29 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 2.78 | 0.19 | 0.88 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 4.84 | 0.21 | 3.28 | 0.25 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 1.24 | 0.17 | 0.23 | 0.68 | 0.00 | 0.05 |
| GPU≥50% | 202 | 0.98 | 0.21 | 0.25 | 0.48 | 0.00 | 0.06 |
| 10–50% | 64 | 1.19 | 0.28 | 0.25 | 0.49 | 0.00 | 0.11 |
| miss<10% | 164 | 1.86 | 0.28 | 0.41 | 0.56 | 0.00 | 0.06 |
| mixed | 6 | 0.00 | 0.00 | 0.00 | 0.69 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 2.71 | 0.23 | 1.77 | 0.13 | 0.39 | 0.00 | 0.00 | 0.65 | 0.00 | 0.01 |
| GPU≥50% | 202 | 1.02 | 0.14 | 0.49 | 0.04 | 0.01 | 0.00 | 0.00 | 0.38 | 0.00 | 0.02 |
| 10–50% | 64 | 0.84 | 0.13 | 0.37 | 0.00 | 0.00 | 0.00 | 0.00 | 0.45 | 0.00 | 0.03 |
| miss<10% | 164 | 1.74 | 0.12 | 1.02 | 0.05 | 0.75 | 0.00 | 0.00 | 0.76 | 0.00 | 0.09 |
| mixed | 6 | 9.70 | 0.33 | 9.36 | 0.74 | 0.54 | 0.00 | 0.00 | 0.47 | 0.01 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.15 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 202 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| mixed | 6 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.14 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1103 | 1098 / 0 / 5 | 384 | 424 | 259 (114–551) | 0 (970) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4025 | 3925 / 0 / 100 | 128 | 1287 | 616 (155–1187) | 0 (600) |
| promotion after a load | 143 | 143 / 0 / 0 | 128 | 649 | 501 (7–623) | 0 (0) |

Requests refused at least once: 75 of 544; preemptions: 4; running requests that could not get their next chunk: 8.
Admitted external loads: 126; reservation passed at admission p50 0 / max 231 blocks; free blocks at admission p50 955.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.596 |
| time with free blocks < 50% of the pool | 0.641 |
| time with free blocks < 25% of the pool | 0.494 |
| time with free blocks < 10% of the pool | 0.271 |
| time with free blocks < 5% of the pool | 0.122 |
| blocks held by loads in transfer, mean / max | 29 / 2080 |
| in-flight prefill reservation after schedule(), mean / max | 245 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.408 |
| running requests, mean / max | 6.2 / 16 |
| waiting + kv-holding requests, mean / max | 4.6 / 33 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.53 | 0.44 | 0.18 / 0.05 | 7.97 [51] | 16.11 [57] | 9.45 [42] | 12.69 [66] |
| GPU≥50% | 202 | 0.47 | 0.40 | 0.60 / 0.06 | 0.34 [107] | 7.95 [95] | 1.62 [134] | 17.85 [68] |
| 10–50% | 64 | 0.44 | 0.36 | 0.50 / 0.04 | 1.92 [36] | 6.58 [28] | 1.48 [37] | 19.72 [27] |
| miss<10% | 164 | 0.53 | 0.44 | 0.49 / 0.07 | 3.76 [77] | 19.53 [87] | 9.27 [112] | 21.92 [52] |
| mixed | 6 | 1.00 | 0.33 | 0.07 / 0.00 | – | 44.12 [6] | – | 44.12 [6] |
