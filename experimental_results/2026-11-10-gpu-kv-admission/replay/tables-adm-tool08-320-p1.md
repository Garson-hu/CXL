## Admission analysis of `tool08-320-p1` (544 requests, 20983 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 113 | 6178 | 384 | 19.12 / 42.74 | 2.08 / 6.20 | 0.81 / 5.93 | 0.00 / 5.71 | 0.88 / 0.86 | 0.00 / 0.01 | 0.60 / 0.66 |
| GPU≥50% | 200 | 6221 | 71 | 1.73 / 38.69 | 0.00 / 3.07 | 0.47 / 3.55 | 0.17 / 2.26 | 0.64 / 0.48 | 0.00 / 0.00 | 0.45 / 0.48 |
| 10–50% | 64 | 2103 | 94 | 10.61 / 47.43 | 0.00 / 4.73 | 0.63 / 2.85 | 2.47 / 7.04 | 1.28 / 0.89 | 0.00 / 0.00 | 0.76 / 1.08 |
| miss<10% | 164 | 13883 | 128 | 18.79 / 51.54 | 0.00 / 3.50 | 0.50 / 3.03 | 6.33 / 10.33 | 0.23 / 0.23 | 0.64 / 0.64 | 3.75 / 4.63 |
| mixed | 3 | 6188 | 384 | 2.08 / 39.95 | 0.00 / 1.30 | 0.40 / 11.34 | 0.00 / 0.00 | 1.06 / 1.11 | 0.00 / 0.00 | 0.45 / 0.61 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 113 | 18.71 | 0.01 [0%] | 0.37 [2%] | 12.70 [68%] | 2.11 [11%] | 0.13 [1%] | 0.68 [4%] | 0.65 [3%] | 0.80 [4%] | 0.13 [1%] | 1.12 [6%] | 0.01 [0%] |
| GPU≥50% | 200 | 8.89 | 0.00 [0%] | 0.24 [3%] | 5.60 [63%] | 1.25 [14%] | 0.00 [0%] | 0.09 [1%] | 0.04 [0%] | 0.41 [5%] | 0.06 [1%] | 1.17 [13%] | 0.01 [0%] |
| 10–50% | 64 | 14.68 | 0.00 [0%] | 0.35 [2%] | 8.41 [57%] | 1.95 [13%] | 0.01 [0%] | 0.16 [1%] | 0.00 [0%] | 0.46 [3%] | 0.00 [0%] | 3.33 [23%] | 0.00 [0%] |
| miss<10% | 164 | 16.86 | 0.00 [0%] | 0.50 [3%] | 7.96 [47%] | 1.02 [6%] | 0.00 [0%] | 2.56 [15%] | 0.00 [0%] | 0.43 [3%] | 0.00 [0%] | 4.37 [26%] | 0.01 [0%] |
| mixed | 3 | 13.75 | 0.00 [0%] | 0.05 [0%] | 10.69 [78%] | 1.94 [14%] | 0.24 [2%] | 0.00 [0%] | 0.00 [0%] | 0.72 [5%] | 0.00 [0%] | 0.00 [0%] | 0.10 [1%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 113 | 0.00 | 0.11 | 5.15 | 0.94 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 200 | 0.00 | 0.06 | 2.59 | 0.42 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.07 | 3.41 | 1.24 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.07 | 2.82 | 0.61 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.01 | 1.10 | 0.19 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 113 | 0.12 | 4.32 | 0.91 | 0.00 | 0.00 | 0.57 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 200 | 0.12 | 2.26 | 0.75 | 0.00 | 0.00 | 0.41 | 0.00 | 0.00 | 0.01 |
| 10–50% | 64 | 0.10 | 1.92 | 0.39 | 0.00 | 0.00 | 0.44 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.07 | 2.12 | 0.41 | 0.00 | 0.00 | 0.43 | 0.00 | 0.00 | 0.01 |
| mixed | 3 | 0.04 | 9.31 | 1.43 | 0.00 | 0.00 | 0.46 | 0.00 | 0.00 | 0.10 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 113 | 0.13 | 2.90 | 0.11 | 0.68 | 0.65 | 0.00 | 0.13 | 1.12 | 0.01 |
| GPU≥50% | 200 | 0.07 | 0.74 | 0.08 | 0.09 | 0.04 | 0.00 | 0.06 | 1.17 | 0.00 |
| 10–50% | 64 | 0.18 | 3.08 | 0.30 | 0.16 | 0.00 | 0.00 | 0.00 | 3.33 | 0.00 |
| miss<10% | 164 | 0.37 | 3.02 | 0.01 | 2.55 | 0.00 | 0.00 | 0.00 | 4.37 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 113 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |
| GPU≥50% | 200 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1803 | 1566 / 0 / 237 | 384 | 451 | 256 (78–992) | 0 (1800) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6108 | 6108 / 0 / 0 | 128 | 1067 | 535 (118–1525) | 0 (0) |
| promotion after a load | 28 | 28 / 0 / 0 | 36 | 36 | 16 (10–647) | 0 (0) |

Requests refused at least once: 155 of 544; preemptions: 9; running requests that could not get their next chunk: 18.
Admitted external loads: 125; reservation passed at admission p50 223 / max 1852 blocks; free blocks at admission p50 1616.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.641 |
| time with free blocks < 50% of the pool | 0.690 |
| time with free blocks < 25% of the pool | 0.569 |
| time with free blocks < 10% of the pool | 0.318 |
| time with free blocks < 5% of the pool | 0.166 |
| blocks held by loads in transfer, mean / max | 25 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 301 / 2401 |
| steps whose running requests used the whole token budget (share of time) | 0.044 |
| steps with a shortened token budget (share of time) | 0.195 |
| running requests, mean / max | 6.8 / 15 |
| waiting + kv-holding requests, mean / max | 5.9 / 29 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 113 | 0.69 | 0.00 | 0.12 / 0.02 | 14.96 [35] | 19.82 [78] | 2.56 [25] | 20.52 [88] |
| GPU≥50% | 200 | 0.56 | 0.00 | 0.47 / 0.04 | 0.27 [87] | 4.32 [113] | 0.90 [116] | 17.79 [84] |
| 10–50% | 64 | 0.58 | 0.00 | 0.24 / 0.05 | 1.34 [27] | 16.27 [37] | 1.11 [28] | 23.87 [36] |
| miss<10% | 164 | 0.68 | 0.00 | 0.40 / 0.04 | 7.19 [53] | 22.06 [111] | 12.68 [90] | 28.16 [74] |
| mixed | 3 | 1.00 | 0.00 | 0.11 / 0.06 | – | 2.08 [3] | 1.41 [1] | 39.95 [2] |
