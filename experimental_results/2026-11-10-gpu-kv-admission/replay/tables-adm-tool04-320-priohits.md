## Admission analysis of `tool04-320-priohits` (1159 requests, 87125 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 130 | 6472 | 384 | 1.78 / 16.80 | 0.00 / 1.09 | 0.41 / 1.17 | 0.00 / 0.24 | 0.15 / 0.47 | 0.00 / 0.31 | 0.20 / 0.43 |
| GPU≥50% | 594 | 6193 | 386 | 0.29 / 7.39 | 0.00 / 0.71 | 0.03 / 0.64 | 0.00 / 0.00 | 0.05 / 0.31 | 0.00 / 0.77 | 0.18 / 0.28 |
| 10–50% | 121 | 2428 | 103 | 0.77 / 19.62 | 0.00 / 1.19 | 0.03 / 1.97 | 0.00 / 0.04 | 0.11 / 0.42 | 0.00 / 0.39 | 0.47 / 0.85 |
| miss<10% | 302 | 13712 | 128 | 5.12 / 27.66 | 0.00 / 1.64 | 0.03 / 2.03 | 0.00 / 0.35 | 0.05 / 0.04 | 0.00 / 0.00 | 3.00 / 3.90 |
| mixed | 12 | 1844 | 32 | 3.09 / 17.80 | 1.30 / 1.27 | 0.82 / 1.67 | 0.00 / 0.40 | 0.30 / 0.65 | 0.00 / 0.70 | 0.20 / 0.54 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 130 | 3.27 | 1.86 [57%] | 0.07 [2%] | 0.38 [12%] | 0.00 [0%] | 0.16 [5%] | 0.22 [7%] | 0.00 [0%] | 0.58 [18%] | 0.00 [0%] |
| GPU≥50% | 594 | 1.37 | 0.94 [69%] | 0.02 [2%] | 0.01 [1%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.38 [28%] | 0.00 [0%] |
| 10–50% | 121 | 3.31 | 2.08 [63%] | 0.11 [3%] | 0.63 [19%] | 0.00 [0%] | 0.02 [0%] | 0.04 [1%] | 0.00 [0%] | 0.43 [13%] | 0.00 [0%] |
| miss<10% | 302 | 4.03 | 2.39 [59%] | 0.18 [5%] | 0.67 [17%] | 0.00 [0%] | 0.00 [0%] | 0.33 [8%] | 0.00 [0%] | 0.44 [11%] | 0.01 [0%] |
| mixed | 12 | 4.69 | 2.85 [61%] | 0.06 [1%] | 0.72 [15%] | 0.00 [0%] | 0.10 [2%] | 0.40 [9%] | 0.00 [0%] | 0.57 [12%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 130 | 0.97 | 0.02 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 594 | 0.70 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 121 | 1.03 | 0.03 | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 302 | 1.33 | 0.09 | 0.22 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 12 | 1.22 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 130 | 0.38 | 0.02 | 0.24 | 0.00 | 0.00 | 0.00 | 0.53 | 0.00 |
| GPU≥50% | 594 | 0.23 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.38 | 0.00 |
| 10–50% | 121 | 0.98 | 0.07 | 0.51 | 0.00 | 0.00 | 0.00 | 0.41 | 0.00 |
| miss<10% | 302 | 1.06 | 0.09 | 0.44 | 0.00 | 0.00 | 0.00 | 0.43 | 0.00 |
| mixed | 12 | 0.46 | 0.00 | 0.69 | 0.00 | 0.00 | 0.00 | 0.52 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | own:resv | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 130 | 0.03 | 0.00 | 0.00 | 0.21 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 594 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 121 | 0.00 | 0.00 | 0.00 | 0.04 | 0.00 | 0.00 | 0.00 |
| miss<10% | 302 | 0.00 | 0.00 | 0.02 | 0.33 | 0.00 | 0.00 | 0.00 |
| mixed | 12 | 0.00 | 0.00 | 0.00 | 0.40 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 130 | 0.28 | 0.01 | 0.01 | 0.00 | 0.01 | 0.00 |
| GPU≥50% | 594 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 121 | 0.05 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 302 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 12 | 0.70 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1117 | 1110 / 0 / 7 | 1504 | 1505 | 832 (150–1153) | 0 (1087) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3445 | 3445 / 0 / 0 | 128 | 1616 | 718 (193–1730) | 0 (0) |
| promotion after a load | 42 | 42 / 0 / 0 | 128 | 311 | 68 (60–75) | 0 (0) |

Requests refused at least once: 43 of 1159; preemptions: 2; running requests that could not get their next chunk: 4.
Admitted external loads: 170; reservation passed at admission p50 0 / max 1030 blocks; free blocks at admission p50 5636.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.258 |
| time with free blocks < 50% of the pool | 0.172 |
| time with free blocks < 25% of the pool | 0.096 |
| time with free blocks < 10% of the pool | 0.036 |
| time with free blocks < 5% of the pool | 0.016 |
| blocks held by loads in transfer, mean / max | 12 / 2240 |
| in-flight prefill reservation after schedule(), mean / max | 109 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.187 |
| running requests, mean / max | 1.9 / 16 |
| waiting + kv-holding requests, mean / max | 0.6 / 12 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 130 | 0.45 | 0.38 | 0.82 / 0.36 | 0.29 [72] | 5.69 [58] | 1.08 [121] | 9.68 [9] |
| GPU≥50% | 594 | 0.30 | 0.26 | 0.82 / 0.37 | 0.17 [418] | 4.40 [176] | 0.27 [565] | 1.99 [29] |
| 10–50% | 121 | 0.32 | 0.31 | 0.80 / 0.32 | 0.48 [82] | 6.72 [39] | 0.73 [114] | 20.84 [7] |
| miss<10% | 302 | 0.35 | 0.32 | 0.83 / 0.39 | 2.84 [196] | 12.07 [106] | 4.66 [287] | 26.81 [15] |
| mixed | 12 | 0.50 | 0.50 | 0.80 / 0.39 | 0.30 [6] | 9.96 [6] | 2.22 [11] | 14.45 [1] |
