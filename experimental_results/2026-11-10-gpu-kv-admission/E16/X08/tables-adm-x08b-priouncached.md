## Admission analysis of `x08b-priouncached` (544 requests, 21405 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 92 | 6171 | 384 | 3.84 / 12.47 | 0.00 / 1.32 | 0.89 / 1.50 | 0.00 / 0.26 | 0.45 / 0.69 | 0.00 / 0.36 | 0.36 / 0.49 |
| GPU≥50% | 219 | 6251 | 57 | 1.38 / 8.77 | 0.00 / 0.99 | 0.55 / 1.04 | 0.00 / 0.09 | 0.49 / 0.49 | 0.00 / 0.00 | 0.32 / 0.36 |
| 10–50% | 63 | 2038 | 87 | 1.90 / 11.68 | 0.00 / 0.85 | 0.56 / 1.24 | 0.00 / 0.25 | 0.16 / 0.17 | 0.00 / 0.00 | 0.51 / 0.76 |
| miss<10% | 169 | 13886 | 128 | 9.41 / 38.57 | 0.77 / 2.53 | 1.36 / 4.45 | 0.00 / 3.35 | – | – | 3.31 / 4.12 |
| mixed | 1 | 8552 | 211 | 6.01 / 6.01 | 1.01 / 1.01 | 0.54 / 0.54 | 1.58 / 1.58 | 1.75 / 1.75 | 0.00 / 0.00 | 0.81 / 0.81 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 92 | 4.12 | 2.30 [56%] | 0.14 [3%] | 0.58 [14%] | 0.00 [0%] | 0.04 [1%] | 0.24 [6%] | 0.00 [0%] | 0.81 [20%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 219 | 2.12 | 1.26 [60%] | 0.03 [1%] | 0.23 [11%] | 0.00 [0%] | 0.00 [0%] | 0.06 [3%] | 0.00 [0%] | 0.51 [24%] | 0.00 [0%] | 0.02 [1%] |
| 10–50% | 63 | 2.34 | 1.17 [50%] | 0.03 [1%] | 0.44 [19%] | 0.00 [0%] | 0.00 [0%] | 0.20 [8%] | 0.00 [0%] | 0.48 [21%] | 0.00 [0%] | 0.01 [1%] |
| miss<10% | 169 | 10.33 | 5.21 [50%] | 0.50 [5%] | 2.61 [25%] | 0.00 [0%] | 0.00 [0%] | 1.22 [12%] | 0.00 [0%] | 0.67 [7%] | 0.00 [0%] | 0.12 [1%] |
| mixed | 1 | 4.89 | 1.22 [25%] | 0.03 [1%] | 3.02 [62%] | 0.00 [0%] | 0.00 [0%] | 0.06 [1%] | 0.00 [0%] | 0.56 [12%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 92 | 1.23 | 0.02 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 219 | 0.92 | 0.01 | 0.04 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 63 | 0.72 | 0.01 | 0.11 | 0.00 | 0.00 | 0.00 | 0.01 |
| miss<10% | 169 | 1.91 | 0.09 | 0.52 | 0.00 | 0.00 | 0.00 | 0.01 |
| mixed | 1 | 0.41 | 0.03 | 0.58 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 92 | 0.53 | 0.01 | 0.24 | 0.00 | 0.00 | 0.00 | 0.72 | 0.00 | 0.00 |
| GPU≥50% | 219 | 0.34 | 0.01 | 0.16 | 0.00 | 0.00 | 0.00 | 0.51 | 0.00 | 0.01 |
| 10–50% | 63 | 0.45 | 0.02 | 0.28 | 0.00 | 0.00 | 0.00 | 0.48 | 0.00 | 0.00 |
| miss<10% | 169 | 2.23 | 0.33 | 1.14 | 0.00 | 0.00 | 0.00 | 0.67 | 0.00 | 0.08 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.54 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 92 | 0.00 | 0.00 | 0.03 | 0.00 | 0.23 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 219 | 0.00 | 0.00 | 0.03 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 63 | 0.00 | 0.00 | 0.05 | 0.00 | 0.20 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 1.08 | 0.08 | 0.95 | 0.00 | 1.22 | 0.00 | 0.00 | 0.00 | 0.03 |
| mixed | 1 | 0.00 | 0.00 | 1.53 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 92 | 0.30 | 0.03 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 219 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 63 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 169 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1187 | 1184 / 0 / 3 | 384 | 395 | 246 (49–1095) | 0 (205) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5594 | 5594 / 0 / 0 | 128 | 1700 | 783 (159–1817) | 0 (0) |
| promotion after a load | 48 | 48 / 0 / 0 | 57 | 57 | 31 (24–47) | 0 (0) |

Requests refused at least once: 133 of 544; preemptions: 2; running requests that could not get their next chunk: 8.
Admitted external loads: 98; reservation passed at admission p50 0 / max 386 blocks; free blocks at admission p50 1230.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.616 |
| time with free blocks < 50% of the pool | 0.679 |
| time with free blocks < 25% of the pool | 0.518 |
| time with free blocks < 10% of the pool | 0.253 |
| time with free blocks < 5% of the pool | 0.136 |
| blocks held by loads in transfer, mean / max | 26 / 1856 |
| in-flight prefill reservation after schedule(), mean / max | 256 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.425 |
| running requests, mean / max | 6.5 / 16 |
| waiting + kv-holding requests, mean / max | 2.2 / 17 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 92 | 0.52 | 0.45 | 0.16 / 0.02 | 1.89 [44] | 5.84 [48] | 7.24 [29] | 3.77 [63] |
| GPU≥50% | 219 | 0.46 | 0.36 | 0.40 / 0.02 | 0.36 [118] | 4.05 [101] | 1.31 [118] | 1.46 [101] |
| 10–50% | 63 | 0.49 | 0.33 | 0.25 / 0.02 | 0.76 [32] | 3.43 [31] | 1.39 [32] | 2.80 [31] |
| miss<10% | 169 | 0.54 | 0.44 | 0.35 / 0.02 | 4.20 [78] | 14.31 [91] | 5.86 [97] | 13.00 [72] |
| mixed | 1 | 0.00 | 0.00 | 0.00 / 0.00 | 6.01 [1] | – | – | 6.01 [1] |
