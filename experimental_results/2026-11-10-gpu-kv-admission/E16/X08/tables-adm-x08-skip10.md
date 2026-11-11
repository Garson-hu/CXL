## Admission analysis of `x08-skip10` (544 requests, 21897 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 6178 | 384 | 9.66 / 28.22 | 2.26 / 5.93 | 0.79 / 1.92 | 0.03 / 2.46 | 0.35 / 0.70 | 0.00 / 0.12 | 0.30 / 0.44 |
| GPU≥50% | 216 | 6237 | 56 | 4.78 / 24.93 | 1.18 / 4.10 | 0.70 / 1.26 | 0.00 / 2.29 | 0.62 / 0.55 | 0.00 / 0.00 | 0.38 / 0.46 |
| 10–50% | 64 | 2103 | 87 | 5.62 / 28.12 | 0.98 / 4.56 | 0.75 / 1.17 | 0.00 / 2.63 | 1.30 / 1.03 | 2.06 / 1.81 | 0.73 / 0.85 |
| miss<10% | 164 | 13883 | 128 | 12.74 / 43.15 | 0.87 / 3.51 | 0.81 / 2.13 | 0.00 / 5.99 | 1.28 / 1.28 | 0.00 / 0.00 | 3.31 / 4.17 |
| mixed | 2 | 6648 | 384 | 10.40 / 10.40 | 6.84 / 5.21 | 1.31 / 1.31 | 1.33 / 1.33 | 0.33 / 0.32 | 0.00 / 0.00 | 0.37 / 0.29 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 11.13 | 6.40 [57%] | 0.46 [4%] | 2.00 [18%] | 0.05 [0%] | 0.22 [2%] | 0.02 [0%] | 0.80 [7%] | 1.15 [10%] | 0.00 [0%] | 0.02 [0%] |
| GPU≥50% | 216 | 7.67 | 4.45 [58%] | 0.41 [5%] | 1.15 [15%] | 0.07 [1%] | 0.02 [0%] | 0.02 [0%] | 0.55 [7%] | 0.98 [13%] | 0.00 [0%] | 0.03 [0%] |
| 10–50% | 64 | 8.54 | 4.70 [55%] | 0.39 [5%] | 1.66 [19%] | 0.00 [0%] | 0.00 [0%] | 0.09 [1%] | 0.61 [7%] | 1.03 [12%] | 0.00 [0%] | 0.07 [1%] |
| miss<10% | 164 | 11.65 | 6.45 [55%] | 0.55 [5%] | 1.50 [13%] | 0.06 [1%] | 0.00 [0%] | 0.60 [5%] | 0.60 [5%] | 1.75 [15%] | 0.00 [0%] | 0.13 [1%] |
| mixed | 2 | 8.17 | 5.21 [64%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.29 [4%] | 0.00 [0%] | 1.34 [16%] | 1.33 [16%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 3.96 | 0.23 | 1.73 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 216 | 2.99 | 0.17 | 0.94 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 3.08 | 0.13 | 1.35 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 2.71 | 0.17 | 0.63 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 2 | 5.21 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 1.13 | 0.11 | 0.04 | 0.63 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 216 | 0.63 | 0.09 | 0.00 | 0.55 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.52 | 0.05 | 0.00 | 0.60 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 1.30 | 0.21 | 0.00 | 0.60 | 0.00 | 0.00 | 0.03 |
| mixed | 2 | 0.00 | 0.00 | 0.00 | 1.31 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 0.94 | 0.08 | 0.20 | 0.05 | 0.02 | 0.00 | 1.15 | 0.00 | 0.02 |
| GPU≥50% | 216 | 0.83 | 0.15 | 0.21 | 0.07 | 0.02 | 0.00 | 0.98 | 0.00 | 0.03 |
| 10–50% | 64 | 1.02 | 0.21 | 0.30 | 0.00 | 0.01 | 0.00 | 1.03 | 0.00 | 0.06 |
| miss<10% | 164 | 2.44 | 0.18 | 0.87 | 0.06 | 0.60 | 0.00 | 1.75 | 0.00 | 0.09 |
| mixed | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.33 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 216 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.00 | 0.00 | 0.00 | 0.08 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 57 | 57 / 0 / 0 | 384 | 413 | 292 (227–304) | 0 (59) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3219 | 3015 / 0 / 204 | 128 | 1468 | 637 (120–1198) | 0 (600) |
| promotion after a load | 140 | 140 / 0 / 0 | 128 | 970 | 187 (145–229) | 0 (0) |

Requests refused at least once: 44 of 544; preemptions: 5; running requests that could not get their next chunk: 10.
Admitted external loads: 114; reservation passed at admission p50 0 / max 649 blocks; free blocks at admission p50 947.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.604 |
| time with free blocks < 50% of the pool | 0.652 |
| time with free blocks < 25% of the pool | 0.510 |
| time with free blocks < 10% of the pool | 0.273 |
| time with free blocks < 5% of the pool | 0.136 |
| blocks held by loads in transfer, mean / max | 26 / 2160 |
| in-flight prefill reservation after schedule(), mean / max | 250 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.413 |
| running requests, mean / max | 6.2 / 16 |
| waiting + kv-holding requests, mean / max | 4.1 / 26 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 98 | 0.59 | 0.51 | 0.17 / 0.04 | 3.84 [40] | 12.48 [58] | 8.49 [40] | 10.88 [58] |
| GPU≥50% | 216 | 0.50 | 0.43 | 0.51 / 0.05 | 0.37 [108] | 10.03 [108] | 1.99 [134] | 13.29 [82] |
| 10–50% | 64 | 0.45 | 0.41 | 0.40 / 0.02 | 1.60 [35] | 7.16 [29] | 1.51 [36] | 18.97 [28] |
| miss<10% | 164 | 0.48 | 0.41 | 0.47 / 0.04 | 5.63 [86] | 17.97 [78] | 8.50 [103] | 21.56 [61] |
| mixed | 2 | 1.00 | 1.00 | 0.22 / 0.15 | – | 10.40 [2] | – | 10.40 [2] |
