## Admission analysis of `x08-base` (544 requests, 21750 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 6178 | 384 | 19.39 / 43.81 | 5.52 / 6.67 | 8.41 / 10.69 | 0.00 / 0.64 | 0.78 / 0.81 | 0.00 / 0.25 | 0.38 / 0.49 |
| GPU≥50% | 207 | 6198 | 54 | 6.37 / 40.19 | 1.93 / 4.69 | 1.14 / 5.86 | 0.00 / 0.09 | 0.15 / 0.25 | 0.00 / 0.00 | 0.38 / 0.46 |
| 10–50% | 64 | 2103 | 89 | 10.96 / 36.23 | 1.29 / 4.43 | 1.82 / 6.74 | 0.00 / 0.13 | 1.74 / 1.08 | 1.05 / 0.77 | 0.78 / 0.96 |
| miss<10% | 167 | 13883 | 128 | 13.75 / 43.50 | 1.51 / 3.73 | 1.89 / 7.75 | 0.00 / 0.88 | – | – | 3.22 / 4.16 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 19.08 | 10.32 [54%] | 0.89 [5%] | 6.05 [32%] | 0.01 [0%] | 0.12 [1%] | 0.65 [3%] | 0.00 [0%] | 0.98 [5%] | 0.00 [0%] | 0.06 [0%] |
| GPU≥50% | 207 | 10.64 | 6.05 [57%] | 0.48 [4%] | 3.35 [31%] | 0.00 [0%] | 0.00 [0%] | 0.09 [1%] | 0.00 [0%] | 0.63 [6%] | 0.00 [0%] | 0.05 [0%] |
| 10–50% | 64 | 11.42 | 6.70 [59%] | 0.56 [5%] | 3.34 [29%] | 0.00 [0%] | 0.00 [0%] | 0.17 [1%] | 0.00 [0%] | 0.58 [5%] | 0.00 [0%] | 0.07 [1%] |
| miss<10% | 167 | 12.36 | 6.82 [55%] | 0.60 [5%] | 3.39 [27%] | 0.00 [0%] | 0.00 [0%] | 0.88 [7%] | 0.00 [0%] | 0.62 [5%] | 0.00 [0%] | 0.03 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 106 | 4.16 | 0.37 | 2.13 | 0.00 | 0.00 |
| GPU≥50% | 207 | 3.16 | 0.21 | 1.32 | 0.00 | 0.00 |
| 10–50% | 64 | 2.75 | 0.16 | 1.52 | 0.00 | 0.00 |
| miss<10% | 167 | 2.64 | 0.20 | 0.89 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 5.68 | 0.44 | 3.75 | 0.00 | 0.00 | 0.00 | 0.77 | 0.00 | 0.04 |
| GPU≥50% | 207 | 2.89 | 0.27 | 2.02 | 0.00 | 0.00 | 0.00 | 0.63 | 0.00 | 0.05 |
| 10–50% | 64 | 3.92 | 0.38 | 1.81 | 0.00 | 0.00 | 0.00 | 0.57 | 0.00 | 0.06 |
| miss<10% | 167 | 4.19 | 0.40 | 2.50 | 0.00 | 0.00 | 0.00 | 0.62 | 0.00 | 0.03 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 0.00 | 0.02 | 0.62 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 207 | 0.00 | 0.00 | 0.09 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 |
| miss<10% | 167 | 0.00 | 0.00 | 0.88 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 0.21 | 0.01 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.01 |
| GPU≥50% | 207 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.04 | 0.00 | 0.01 |
| miss<10% | 167 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 2037 | 2028 / 0 / 9 | 384 | 425 | 213 (28–550) | 0 (162) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4479 | 4479 / 0 / 0 | 128 | 1080 | 646 (114–1240) | 0 (0) |
| promotion after a load | 65 | 65 / 0 / 0 | 128 | 661 | 94 (15–543) | 0 (0) |

Requests refused at least once: 130 of 544; preemptions: 5; running requests that could not get their next chunk: 10.
Admitted external loads: 114; reservation passed at admission p50 0 / max 326 blocks; free blocks at admission p50 1183.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.609 |
| time with free blocks < 50% of the pool | 0.653 |
| time with free blocks < 25% of the pool | 0.517 |
| time with free blocks < 10% of the pool | 0.287 |
| time with free blocks < 5% of the pool | 0.162 |
| blocks held by loads in transfer, mean / max | 26 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 251 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.417 |
| running requests, mean / max | 6.2 / 16 |
| waiting + kv-holding requests, mean / max | 5.5 / 34 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 0.58 | 0.52 | 0.17 / 0.02 | 14.53 [44] | 21.38 [62] | 13.39 [37] | 20.01 [69] |
| GPU≥50% | 207 | 0.49 | 0.43 | 0.52 / 0.04 | 0.52 [106] | 11.68 [101] | 1.56 [126] | 20.31 [81] |
| 10–50% | 64 | 0.45 | 0.41 | 0.40 / 0.03 | 2.96 [35] | 14.14 [29] | 1.48 [33] | 18.42 [31] |
| miss<10% | 167 | 0.47 | 0.40 | 0.49 / 0.04 | 5.71 [88] | 17.28 [79] | 8.50 [106] | 23.74 [61] |
