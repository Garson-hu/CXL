## Admission analysis of `tool08-320-base` (544 requests, 21791 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 6176 | 384 | 19.17 / 43.75 | 6.65 / 6.79 | 7.76 / 10.44 | 0.00 / 0.62 | 0.77 / 0.85 | 0.00 / 0.25 | 0.38 / 0.47 |
| GPU≥50% | 207 | 6221 | 57 | 6.28 / 40.17 | 1.63 / 4.72 | 1.14 / 5.78 | 0.00 / 0.09 | 0.30 / 0.28 | 0.00 / 0.00 | 0.41 / 0.46 |
| 10–50% | 64 | 2103 | 87 | 10.92 / 36.12 | 1.01 / 4.42 | 1.69 / 6.70 | 0.00 / 0.13 | 1.73 / 1.08 | 1.05 / 0.83 | 0.76 / 0.94 |
| miss<10% | 167 | 13883 | 128 | 13.67 / 43.48 | 1.31 / 3.68 | 2.01 / 7.75 | 0.00 / 0.89 | – | – | 3.22 / 4.15 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 18.95 | 10.28 [54%] | 0.84 [4%] | 6.04 [32%] | 0.01 [0%] | 0.13 [1%] | 0.62 [3%] | 0.00 [0%] | 0.96 [5%] | 0.00 [0%] | 0.07 [0%] |
| GPU≥50% | 207 | 10.60 | 6.01 [57%] | 0.48 [5%] | 3.33 [31%] | 0.00 [0%] | 0.00 [0%] | 0.09 [1%] | 0.00 [0%] | 0.62 [6%] | 0.00 [0%] | 0.05 [0%] |
| 10–50% | 64 | 11.37 | 6.68 [59%] | 0.56 [5%] | 3.28 [29%] | 0.00 [0%] | 0.00 [0%] | 0.15 [1%] | 0.00 [0%] | 0.59 [5%] | 0.00 [0%] | 0.10 [1%] |
| miss<10% | 167 | 12.31 | 6.81 [55%] | 0.59 [5%] | 3.35 [27%] | 0.00 [0%] | 0.00 [0%] | 0.89 [7%] | 0.00 [0%] | 0.62 [5%] | 0.00 [0%] | 0.04 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 106 | 4.30 | 0.34 | 2.15 | 0.00 | 0.00 |
| GPU≥50% | 207 | 3.18 | 0.21 | 1.33 | 0.00 | 0.00 |
| 10–50% | 64 | 2.80 | 0.13 | 1.48 | 0.00 | 0.00 |
| miss<10% | 167 | 2.60 | 0.19 | 0.89 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 5.51 | 0.41 | 3.71 | 0.00 | 0.00 | 0.00 | 0.76 | 0.00 | 0.04 |
| GPU≥50% | 207 | 2.83 | 0.28 | 2.00 | 0.00 | 0.00 | 0.00 | 0.62 | 0.00 | 0.05 |
| 10–50% | 64 | 3.85 | 0.40 | 1.79 | 0.00 | 0.00 | 0.00 | 0.58 | 0.00 | 0.07 |
| miss<10% | 167 | 4.21 | 0.40 | 2.46 | 0.00 | 0.00 | 0.00 | 0.62 | 0.00 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 0.00 | 0.02 | 0.60 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 207 | 0.00 | 0.00 | 0.09 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 |
| miss<10% | 167 | 0.00 | 0.00 | 0.89 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 0.19 | 0.02 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.02 |
| GPU≥50% | 207 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.02 | 0.00 | 0.02 |
| miss<10% | 167 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 2000 | 1991 / 0 / 9 | 384 | 425 | 212 (27–549) | 0 (162) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4480 | 4480 / 0 / 0 | 128 | 1080 | 656 (117–1238) | 0 (0) |
| promotion after a load | 47 | 47 / 0 / 0 | 128 | 151 | 60 (14–541) | 0 (0) |

Requests refused at least once: 126 of 544; preemptions: 5; running requests that could not get their next chunk: 10.
Admitted external loads: 117; reservation passed at admission p50 0 / max 326 blocks; free blocks at admission p50 1181.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.608 |
| time with free blocks < 50% of the pool | 0.652 |
| time with free blocks < 25% of the pool | 0.516 |
| time with free blocks < 10% of the pool | 0.287 |
| time with free blocks < 5% of the pool | 0.162 |
| blocks held by loads in transfer, mean / max | 27 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 251 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.417 |
| running requests, mean / max | 6.2 / 16 |
| waiting + kv-holding requests, mean / max | 5.5 / 34 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 106 | 0.59 | 0.53 | 0.16 / 0.02 | 13.76 [43] | 21.35 [63] | 13.21 [37] | 19.74 [69] |
| GPU≥50% | 207 | 0.49 | 0.43 | 0.52 / 0.04 | 0.51 [106] | 10.87 [101] | 1.51 [126] | 20.17 [81] |
| 10–50% | 64 | 0.48 | 0.42 | 0.40 / 0.03 | 2.91 [33] | 14.11 [31] | 1.43 [33] | 18.27 [31] |
| miss<10% | 167 | 0.47 | 0.39 | 0.49 / 0.03 | 5.70 [89] | 17.49 [78] | 7.97 [107] | 23.69 [60] |
