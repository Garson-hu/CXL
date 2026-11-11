## Admission analysis of `x08-p2-skip10` (544 requests, 21286 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 6192 | 376 | 15.62 / 37.31 | 0.01 / 2.11 | 0.60 / 1.76 | 3.61 / 9.83 | 0.98 / 0.81 | 0.00 / 0.04 | 0.57 / 0.64 |
| GPU≥50% | 208 | 6214 | 70 | 1.48 / 26.58 | 0.00 / 1.82 | 0.41 / 1.06 | 0.17 / 3.07 | 0.94 / 0.74 | 0.00 / 0.04 | 0.44 / 0.48 |
| 10–50% | 64 | 2103 | 96 | 5.41 / 47.73 | 0.00 / 2.22 | 0.59 / 1.22 | 2.42 / 8.93 | 0.78 / 0.70 | 0.00 / 0.00 | 0.66 / 1.04 |
| miss<10% | 164 | 13883 | 128 | 17.57 / 52.57 | 0.00 / 1.54 | 0.41 / 0.85 | 11.49 / 14.42 | 1.03 / 1.03 | 0.00 / 0.00 | 3.67 / 4.67 |
| mixed | 1 | 3122 | 160 | 0.67 / 0.67 | 0.00 / 0.00 | 0.18 / 0.18 | 0.11 / 0.11 | 0.14 / 0.14 | 0.00 / 0.00 | 0.23 / 0.23 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 14.55 | 0.01 [0%] | 0.26 [2%] | 7.90 [54%] | 1.27 [9%] | 0.31 [2%] | 0.44 [3%] | 0.28 [2%] | 0.75 [5%] | 1.60 [11%] | 0.20 [1%] | 1.47 [10%] | 0.01 [0%] | 0.05 [0%] |
| GPU≥50% | 208 | 5.99 | 0.00 [0%] | 0.15 [3%] | 3.27 [55%] | 0.23 [4%] | 0.01 [0%] | 0.03 [0%] | 0.00 [0%] | 0.41 [7%] | 0.58 [10%] | 0.08 [1%] | 1.16 [19%] | 0.00 [0%] | 0.06 [1%] |
| 10–50% | 64 | 12.41 | 0.00 [0%] | 0.28 [2%] | 5.99 [48%] | 0.90 [7%] | 0.02 [0%] | 0.11 [1%] | 0.00 [0%] | 0.48 [4%] | 0.12 [1%] | 0.14 [1%] | 4.12 [33%] | 0.01 [0%] | 0.25 [2%] |
| miss<10% | 164 | 16.82 | 0.00 [0%] | 0.56 [3%] | 6.56 [39%] | 0.47 [3%] | 0.00 [0%] | 2.09 [12%] | 0.00 [0%] | 0.41 [2%] | 0.48 [3%] | 0.08 [0%] | 5.98 [36%] | 0.01 [0%] | 0.17 [1%] |
| mixed | 1 | 0.42 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.11 [26%] | 0.00 [0%] | 0.00 [0%] | 0.20 [48%] | 0.11 [26%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 0.00 | 0.01 | 2.04 | 0.04 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 208 | 0.00 | 0.04 | 1.71 | 0.04 | 0.00 | 0.00 | 0.00 | 0.03 |
| 10–50% | 64 | 0.00 | 0.03 | 2.03 | 0.15 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.01 | 1.41 | 0.07 | 0.00 | 0.00 | 0.00 | 0.05 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 0.04 | 1.07 | 0.11 | 0.53 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 208 | 0.06 | 0.58 | 0.03 | 0.39 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.58 | 0.08 | 0.46 | 0.00 | 0.00 | 0.00 | 0.07 |
| miss<10% | 164 | 0.02 | 0.42 | 0.00 | 0.41 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.17 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 0.18 | 4.55 | 1.11 | 0.43 | 0.28 | 0.00 | 1.60 | 0.20 | 1.47 | 0.01 | 0.00 |
| GPU≥50% | 208 | 0.06 | 0.97 | 0.16 | 0.03 | 0.00 | 0.00 | 0.58 | 0.08 | 1.16 | 0.00 | 0.03 |
| 10–50% | 64 | 0.22 | 3.38 | 0.65 | 0.11 | 0.00 | 0.00 | 0.12 | 0.14 | 4.12 | 0.01 | 0.18 |
| miss<10% | 164 | 0.54 | 4.72 | 0.40 | 2.09 | 0.00 | 0.00 | 0.48 | 0.08 | 5.97 | 0.01 | 0.13 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.11 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.02 |
| GPU≥50% | 208 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 966 | 891 / 0 / 75 | 384 | 456 | 219 (46–421) | 0 (1871) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6010 | 5721 / 0 / 289 | 128 | 1085 | 738 (193–1649) | 0 (600) |
| promotion after a load | 14 | 14 / 0 / 0 | 34 | 34 | 29 (0–45) | 0 (0) |

Requests refused at least once: 101 of 544; preemptions: 10; running requests that could not get their next chunk: 20.
Admitted external loads: 126; reservation passed at admission p50 192 / max 1954 blocks; free blocks at admission p50 1468.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.631 |
| time with free blocks < 50% of the pool | 0.683 |
| time with free blocks < 25% of the pool | 0.548 |
| time with free blocks < 10% of the pool | 0.290 |
| time with free blocks < 5% of the pool | 0.150 |
| blocks held by loads in transfer, mean / max | 27 / 2688 |
| in-flight prefill reservation after schedule(), mean / max | 301 / 2615 |
| steps whose running requests used the whole token budget (share of time) | 0.054 |
| steps with a shortened token budget (share of time) | 0.178 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 4.9 / 23 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 107 | 0.66 | 0.00 | 0.14 / 0.05 | 6.28 [36] | 18.34 [71] | 2.56 [31] | 17.84 [76] |
| GPU≥50% | 208 | 0.57 | 0.00 | 0.48 / 0.03 | 0.33 [90] | 2.12 [118] | 0.95 [119] | 6.33 [89] |
| 10–50% | 64 | 0.61 | 0.00 | 0.25 / 0.08 | 0.77 [25] | 6.76 [39] | 1.13 [31] | 19.28 [33] |
| miss<10% | 164 | 0.62 | 0.00 | 0.42 / 0.04 | 6.19 [62] | 22.52 [102] | 12.30 [90] | 28.46 [74] |
| mixed | 1 | 0.00 | 0.00 | 0.01 / 0.01 | 0.67 [1] | – | – | 0.67 [1] |
