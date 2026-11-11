## Admission analysis of `tool08-320-priohits-p1` (544 requests, 21308 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 85 | 6178 | 377 | 2.50 / 13.01 | 0.00 / 0.68 | 0.36 / 0.54 | 0.00 / 1.58 | 0.73 / 0.64 | 0.00 / 0.00 | 0.47 / 0.61 |
| GPU≥50% | 231 | 6251 | 70 | 1.16 / 8.42 | 0.00 / 0.34 | 0.32 / 0.44 | 0.11 / 0.82 | 0.31 / 0.45 | 0.00 / 0.00 | 0.39 / 0.44 |
| 10–50% | 64 | 2103 | 92 | 8.21 / 46.34 | 0.00 / 2.53 | 0.49 / 0.80 | 2.32 / 9.88 | 0.82 / 0.60 | 0.00 / 0.00 | 0.74 / 1.01 |
| miss<10% | 164 | 13883 | 128 | 17.76 / 50.89 | 0.00 / 2.15 | 0.43 / 1.38 | 9.86 / 13.11 | 0.73 / 0.73 | 0.00 / 0.00 | 3.56 / 4.60 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 85 | 3.44 | 0.01 [0%] | 0.04 [1%] | 1.32 [39%] | 0.32 [9%] | 0.18 [5%] | 0.50 [15%] | 0.20 [6%] | 0.47 [14%] | 0.04 [1%] | 0.35 [10%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 231 | 1.61 | 0.00 [0%] | 0.01 [1%] | 0.36 [22%] | 0.14 [9%] | 0.01 [1%] | 0.03 [2%] | 0.01 [1%] | 0.31 [19%] | 0.05 [3%] | 0.67 [41%] | 0.00 [0%] | 0.02 [1%] |
| 10–50% | 64 | 13.24 | 0.00 [0%] | 0.40 [3%] | 6.41 [48%] | 0.56 [4%] | 0.03 [0%] | 0.52 [4%] | 0.01 [0%] | 0.46 [3%] | 0.00 [0%] | 4.72 [36%] | 0.00 [0%] | 0.13 [1%] |
| miss<10% | 164 | 16.65 | 0.00 [0%] | 0.63 [4%] | 6.92 [42%] | 0.43 [3%] | 0.00 [0%] | 2.43 [15%] | 0.00 [0%] | 0.44 [3%] | 0.00 [0%] | 5.62 [34%] | 0.00 [0%] | 0.16 [1%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 85 | 0.00 | 0.00 | 0.53 | 0.14 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 231 | 0.00 | 0.00 | 0.25 | 0.08 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.09 | 2.22 | 0.13 | 0.00 | 0.00 | 0.00 | 0.08 |
| miss<10% | 164 | 0.00 | 0.04 | 1.88 | 0.17 | 0.00 | 0.00 | 0.00 | 0.05 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 85 | 0.00 | 0.11 | 0.07 | 0.00 | 0.00 | 0.35 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 231 | 0.01 | 0.05 | 0.06 | 0.00 | 0.00 | 0.30 | 0.00 | 0.00 | 0.00 | 0.02 |
| 10–50% | 64 | 0.01 | 0.32 | 0.01 | 0.00 | 0.00 | 0.45 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.01 | 0.89 | 0.00 | 0.00 | 0.00 | 0.44 | 0.00 | 0.00 | 0.00 | 0.03 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 85 | 0.01 | 0.46 | 0.03 | 0.50 | 0.20 | 0.00 | 0.04 | 0.35 | 0.00 | 0.00 |
| GPU≥50% | 231 | 0.00 | 0.05 | 0.00 | 0.03 | 0.01 | 0.00 | 0.05 | 0.67 | 0.00 | 0.00 |
| 10–50% | 64 | 0.31 | 3.86 | 0.41 | 0.52 | 0.01 | 0.00 | 0.00 | 4.72 | 0.00 | 0.04 |
| miss<10% | 164 | 0.58 | 4.15 | 0.26 | 2.43 | 0.00 | 0.00 | 0.00 | 5.62 | 0.00 | 0.08 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 85 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 231 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1356 | 1267 / 0 / 89 | 384 | 405 | 206 (36–680) | 0 (1757) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5987 | 5987 / 0 / 0 | 128 | 1252 | 716 (97–1638) | 0 (0) |
| promotion after a load | 4 | 4 / 0 / 0 | 25 | 25 | 6 (5–7) | 0 (0) |

Requests refused at least once: 122 of 544; preemptions: 4; running requests that could not get their next chunk: 45.
Admitted external loads: 101; reservation passed at admission p50 150 / max 1826 blocks; free blocks at admission p50 1353.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.623 |
| time with free blocks < 50% of the pool | 0.685 |
| time with free blocks < 25% of the pool | 0.522 |
| time with free blocks < 10% of the pool | 0.265 |
| time with free blocks < 5% of the pool | 0.144 |
| blocks held by loads in transfer, mean / max | 16 / 2080 |
| in-flight prefill reservation after schedule(), mean / max | 288 / 2342 |
| steps whose running requests used the whole token budget (share of time) | 0.055 |
| steps with a shortened token budget (share of time) | 0.170 |
| running requests, mean / max | 6.6 / 16 |
| waiting + kv-holding requests, mean / max | 3.3 / 22 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 85 | 0.72 | 0.00 | 0.17 / 0.03 | 0.50 [24] | 2.64 [61] | 1.83 [27] | 3.13 [58] |
| GPU≥50% | 231 | 0.56 | 0.00 | 0.38 / 0.03 | 0.27 [101] | 1.58 [130] | 0.98 [128] | 1.62 [103] |
| 10–50% | 64 | 0.67 | 0.00 | 0.42 / 0.05 | 0.52 [21] | 17.20 [43] | 1.52 [36] | 22.14 [28] |
| miss<10% | 164 | 0.63 | 0.00 | 0.43 / 0.03 | 6.53 [60] | 22.62 [104] | 12.67 [97] | 25.77 [67] |
