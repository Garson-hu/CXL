## Admission analysis of `tool08-320-storefix` (544 requests, 22025 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 6178 | 384 | 18.85 / 43.00 | 4.57 / 6.26 | 7.85 / 10.62 | 0.00 / 0.66 | 0.64 / 0.83 | 0.00 / 0.25 | 0.39 / 0.48 |
| GPU≥50% | 209 | 6214 | 56 | 6.25 / 40.20 | 2.10 / 5.03 | 0.96 / 5.29 | 0.00 / 0.09 | 0.13 / 0.22 | 0.00 / 0.00 | 0.38 / 0.45 |
| 10–50% | 64 | 2103 | 89 | 9.63 / 35.40 | 1.27 / 4.86 | 1.53 / 6.01 | 0.00 / 0.13 | 1.73 / 1.08 | 1.59 / 0.96 | 0.76 / 0.94 |
| miss<10% | 164 | 13883 | 128 | 13.33 / 42.48 | 1.52 / 4.20 | 1.59 / 6.99 | 0.00 / 0.91 | 1.65 / 1.65 | 1.65 / 1.65 | 3.25 / 4.15 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 18.61 | 10.11 [54%] | 0.85 [5%] | 5.99 [32%] | 0.01 [0%] | 0.12 [1%] | 0.65 [3%] | 0.00 [0%] | 0.82 [4%] | 0.00 [0%] | 0.07 [0%] |
| GPU≥50% | 209 | 10.41 | 5.92 [57%] | 0.46 [4%] | 3.35 [32%] | 0.00 [0%] | 0.00 [0%] | 0.09 [1%] | 0.00 [0%] | 0.53 [5%] | 0.00 [0%] | 0.05 [1%] |
| 10–50% | 64 | 11.13 | 6.51 [59%] | 0.55 [5%] | 3.28 [29%] | 0.00 [0%] | 0.00 [0%] | 0.16 [1%] | 0.00 [0%] | 0.53 [5%] | 0.00 [0%] | 0.10 [1%] |
| miss<10% | 164 | 12.11 | 6.72 [56%] | 0.58 [5%] | 3.30 [27%] | 0.00 [0%] | 0.00 [0%] | 0.90 [7%] | 0.00 [0%] | 0.56 [5%] | 0.00 [0%] | 0.05 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 3.98 | 0.35 | 1.93 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 209 | 3.37 | 0.24 | 1.42 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 3.10 | 0.20 | 1.56 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 2.93 | 0.23 | 1.03 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 5.65 | 0.41 | 3.88 | 0.00 | 0.00 | 0.00 | 0.63 | 0.00 | 0.04 |
| GPU≥50% | 209 | 2.55 | 0.22 | 1.93 | 0.00 | 0.00 | 0.00 | 0.53 | 0.00 | 0.05 |
| 10–50% | 64 | 3.38 | 0.32 | 1.72 | 0.00 | 0.00 | 0.00 | 0.51 | 0.00 | 0.07 |
| miss<10% | 164 | 3.78 | 0.35 | 2.24 | 0.00 | 0.00 | 0.00 | 0.56 | 0.00 | 0.05 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 0.00 | 0.00 | 0.02 | 0.63 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 209 | 0.00 | 0.00 | 0.00 | 0.09 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.01 | 0.00 | 0.01 | 0.89 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 0.20 | 0.02 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.01 |
| GPU≥50% | 209 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.03 | 0.00 | 0.02 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 2033 | 2026 / 0 / 7 | 384 | 418 | 213 (27–540) | 0 (162) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4424 | 4424 / 0 / 0 | 128 | 1080 | 670 (124–1277) | 0 (0) |
| promotion after a load | 108 | 108 / 0 / 0 | 128 | 649 | 535 (20–626) | 0 (0) |

Requests refused at least once: 130 of 544; preemptions: 7; running requests that could not get their next chunk: 14.
Admitted external loads: 117; reservation passed at admission p50 0 / max 326 blocks; free blocks at admission p50 1203.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.604 |
| time with free blocks < 50% of the pool | 0.648 |
| time with free blocks < 25% of the pool | 0.514 |
| time with free blocks < 10% of the pool | 0.280 |
| time with free blocks < 5% of the pool | 0.156 |
| blocks held by loads in transfer, mean / max | 29 / 2160 |
| in-flight prefill reservation after schedule(), mean / max | 249 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.412 |
| running requests, mean / max | 6.2 / 16 |
| waiting + kv-holding requests, mean / max | 5.4 / 34 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 0.55 | 0.50 | 0.16 / 0.03 | 17.24 [48] | 20.76 [59] | 12.42 [40] | 19.75 [67] |
| GPU≥50% | 209 | 0.51 | 0.43 | 0.51 / 0.04 | 0.36 [102] | 12.09 [107] | 1.40 [129] | 19.78 [80] |
| 10–50% | 64 | 0.47 | 0.39 | 0.40 / 0.02 | 4.26 [34] | 14.04 [30] | 1.85 [35] | 19.65 [29] |
| miss<10% | 164 | 0.51 | 0.41 | 0.49 / 0.04 | 5.71 [80] | 17.26 [84] | 7.98 [103] | 23.31 [61] |
