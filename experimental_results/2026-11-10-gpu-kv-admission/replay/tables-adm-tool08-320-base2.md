## Admission analysis of `tool08-320-base2` (544 requests, 21733 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 6177 | 384 | 18.81 / 43.75 | 5.51 / 6.62 | 7.76 / 10.38 | 0.00 / 0.62 | 0.63 / 0.83 | 0.00 / 0.27 | 0.39 / 0.48 |
| GPU≥50% | 205 | 6221 | 55 | 6.28 / 40.16 | 1.63 / 4.76 | 1.14 / 5.81 | 0.00 / 0.09 | 0.15 / 0.25 | 0.00 / 0.00 | 0.39 / 0.45 |
| 10–50% | 64 | 2103 | 87 | 10.87 / 36.11 | 1.77 / 4.50 | 1.66 / 6.65 | 0.00 / 0.13 | 1.73 / 1.08 | 1.05 / 0.83 | 0.76 / 0.95 |
| miss<10% | 167 | 13883 | 128 | 13.71 / 43.47 | 1.51 / 3.70 | 1.89 / 7.74 | 0.00 / 0.89 | – | – | 3.22 / 4.16 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 18.73 | 10.18 [54%] | 0.83 [4%] | 5.92 [32%] | 0.01 [0%] | 0.12 [1%] | 0.63 [3%] | 0.00 [0%] | 0.97 [5%] | 0.00 [0%] | 0.07 [0%] |
| GPU≥50% | 205 | 10.67 | 6.04 [57%] | 0.47 [4%] | 3.39 [32%] | 0.00 [0%] | 0.00 [0%] | 0.09 [1%] | 0.00 [0%] | 0.62 [6%] | 0.00 [0%] | 0.05 [0%] |
| 10–50% | 64 | 11.41 | 6.71 [59%] | 0.56 [5%] | 3.29 [29%] | 0.00 [0%] | 0.00 [0%] | 0.15 [1%] | 0.00 [0%] | 0.60 [5%] | 0.00 [0%] | 0.10 [1%] |
| miss<10% | 167 | 12.33 | 6.82 [55%] | 0.59 [5%] | 3.36 [27%] | 0.00 [0%] | 0.00 [0%] | 0.89 [7%] | 0.00 [0%] | 0.63 [5%] | 0.00 [0%] | 0.04 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 4.21 | 0.33 | 2.08 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 205 | 3.20 | 0.21 | 1.36 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 2.86 | 0.15 | 1.49 | 0.00 | 0.00 | 0.00 |
| miss<10% | 167 | 2.61 | 0.19 | 0.89 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 5.49 | 0.41 | 3.67 | 0.00 | 0.00 | 0.00 | 0.77 | 0.00 | 0.04 |
| GPU≥50% | 205 | 2.84 | 0.26 | 2.03 | 0.00 | 0.00 | 0.00 | 0.62 | 0.00 | 0.05 |
| 10–50% | 64 | 3.82 | 0.39 | 1.78 | 0.00 | 0.00 | 0.00 | 0.59 | 0.00 | 0.07 |
| miss<10% | 167 | 4.20 | 0.40 | 2.46 | 0.00 | 0.00 | 0.00 | 0.63 | 0.00 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.00 | 0.02 | 0.60 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 205 | 0.00 | 0.00 | 0.09 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 |
| miss<10% | 167 | 0.00 | 0.00 | 0.89 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.20 | 0.01 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.02 |
| GPU≥50% | 205 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.02 | 0.00 | 0.02 |
| miss<10% | 167 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 2005 | 1996 / 0 / 9 | 384 | 425 | 212 (27–549) | 0 (162) |
| compute, no computed tokens (miss / GPU-prefix hit) | 4492 | 4492 / 0 / 0 | 128 | 1080 | 663 (113–1282) | 0 (0) |
| promotion after a load | 47 | 47 / 0 / 0 | 128 | 151 | 60 (14–541) | 0 (0) |

Requests refused at least once: 130 of 544; preemptions: 6; running requests that could not get their next chunk: 12.
Admitted external loads: 116; reservation passed at admission p50 0 / max 326 blocks; free blocks at admission p50 1203.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.609 |
| time with free blocks < 50% of the pool | 0.653 |
| time with free blocks < 25% of the pool | 0.517 |
| time with free blocks < 10% of the pool | 0.289 |
| time with free blocks < 5% of the pool | 0.164 |
| blocks held by loads in transfer, mean / max | 27 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 251 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.417 |
| running requests, mean / max | 6.2 / 16 |
| waiting + kv-holding requests, mean / max | 5.5 / 34 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 108 | 0.59 | 0.53 | 0.17 / 0.02 | 13.76 [44] | 21.35 [64] | 12.70 [39] | 19.73 [69] |
| GPU≥50% | 205 | 0.49 | 0.43 | 0.53 / 0.04 | 0.46 [104] | 11.22 [101] | 1.56 [124] | 20.39 [81] |
| 10–50% | 64 | 0.50 | 0.42 | 0.40 / 0.03 | 2.94 [32] | 14.57 [32] | 1.61 [33] | 18.28 [31] |
| miss<10% | 167 | 0.49 | 0.40 | 0.49 / 0.03 | 6.26 [86] | 17.13 [81] | 8.47 [106] | 23.51 [61] |
