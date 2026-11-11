## Admission analysis of `x08b-tokfast12` (544 requests, 21599 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 6311 | 384 | 8.27 / 28.64 | 0.01 / 1.85 | 0.74 / 1.84 | 0.00 / 5.78 | 0.88 / 0.87 | 0.00 / 0.01 | 0.58 / 0.67 |
| GPU≥50% | 200 | 6182 | 65 | 1.48 / 18.50 | 0.00 / 0.64 | 0.40 / 0.79 | 0.15 / 2.55 | 1.05 / 1.01 | 0.00 / 0.00 | 0.45 / 0.50 |
| 10–50% | 64 | 2103 | 92 | 5.96 / 50.98 | 0.00 / 0.40 | 0.45 / 1.02 | 1.93 / 10.20 | 0.96 / 0.75 | 0.00 / 0.58 | 0.75 / 1.05 |
| miss<10% | 164 | 13883 | 128 | 16.79 / 52.32 | 0.00 / 0.70 | 0.41 / 1.06 | 10.31 / 14.54 | 0.93 / 0.93 | 0.00 / 0.00 | 3.63 / 4.64 |
| mixed | 4 | 4186 | 160 | 14.71 / 19.71 | 0.44 / 1.26 | 0.79 / 2.53 | 11.44 / 6.70 | 1.23 / 1.00 | 0.00 / 0.00 | 1.27 / 1.10 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 10.34 | 0.02 [0%] | 0.16 [2%] | 4.37 [42%] | 1.63 [16%] | 0.33 [3%] | 0.71 [7%] | 0.68 [7%] | 0.74 [7%] | 0.19 [2%] | 1.50 [14%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 200 | 4.07 | 0.00 [0%] | 0.11 [3%] | 1.32 [33%] | 0.55 [14%] | 0.05 [1%] | 0.04 [1%] | 0.03 [1%] | 0.42 [10%] | 0.09 [2%] | 1.44 [35%] | 0.00 [0%] | 0.00 [0%] |
| 10–50% | 64 | 11.71 | 0.00 [0%] | 0.31 [3%] | 3.13 [27%] | 0.70 [6%] | 0.03 [0%] | 0.21 [2%] | 0.00 [0%] | 0.41 [3%] | 0.10 [1%] | 6.82 [58%] | 0.00 [0%] | 0.01 [0%] |
| miss<10% | 164 | 16.30 | 0.00 [0%] | 0.54 [3%] | 4.11 [25%] | 0.63 [4%] | 0.00 [0%] | 1.12 [7%] | 0.00 [0%] | 0.41 [3%] | 0.13 [1%] | 9.31 [57%] | 0.00 [0%] | 0.03 [0%] |
| mixed | 4 | 11.49 | 0.00 [0%] | 0.20 [2%] | 5.05 [44%] | 0.83 [7%] | 0.48 [4%] | 0.14 [1%] | 0.04 [0%] | 0.94 [8%] | 0.00 [0%] | 3.79 [33%] | 0.01 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.00 | 0.03 | 1.62 | 0.19 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 200 | 0.00 | 0.02 | 0.52 | 0.11 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.01 | 0.39 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.01 | 0.67 | 0.02 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.01 | 1.24 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.01 | 0.76 | 0.54 | 0.00 | 0.00 | 0.52 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 200 | 0.01 | 0.18 | 0.21 | 0.00 | 0.00 | 0.38 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.01 | 0.39 | 0.22 | 0.00 | 0.00 | 0.40 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.01 | 0.35 | 0.29 | 0.00 | 0.00 | 0.41 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.04 | 1.23 | 0.63 | 0.00 | 0.00 | 0.62 | 0.00 | 0.00 | 0.01 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.10 | 1.86 | 0.74 | 0.71 | 0.68 | 0.00 | 0.19 | 1.50 | 0.00 | 0.00 |
| GPU≥50% | 200 | 0.08 | 0.63 | 0.23 | 0.04 | 0.03 | 0.00 | 0.09 | 1.44 | 0.00 | 0.00 |
| 10–50% | 64 | 0.28 | 2.35 | 0.47 | 0.17 | 0.00 | 0.00 | 0.10 | 6.82 | 0.00 | 0.01 |
| miss<10% | 164 | 0.52 | 3.09 | 0.33 | 1.12 | 0.00 | 0.00 | 0.13 | 9.31 | 0.00 | 0.03 |
| mixed | 4 | 0.15 | 2.58 | 0.00 | 0.14 | 0.04 | 0.00 | 0.00 | 3.79 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 200 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.04 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1441 | 1215 / 0 / 226 | 384 | 440 | 240 (136–1079) | 0 (1734) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5686 | 5686 / 0 / 0 | 128 | 1252 | 753 (81–1654) | 0 (0) |
| promotion after a load | 35 | 35 / 0 / 0 | 128 | 970 | 675 (667–868) | 0 (0) |

Requests refused at least once: 131 of 544; preemptions: 6; running requests that could not get their next chunk: 14.
Admitted external loads: 139; reservation passed at admission p50 304 / max 1945 blocks; free blocks at admission p50 1608.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.626 |
| time with free blocks < 50% of the pool | 0.680 |
| time with free blocks < 25% of the pool | 0.543 |
| time with free blocks < 10% of the pool | 0.281 |
| time with free blocks < 5% of the pool | 0.151 |
| blocks held by loads in transfer, mean / max | 32 / 2544 |
| in-flight prefill reservation after schedule(), mean / max | 302 / 2414 |
| steps whose running requests used the whole token budget (share of time) | 0.044 |
| steps with a shortened token budget (share of time) | 0.191 |
| running requests, mean / max | 6.6 / 16 |
| waiting + kv-holding requests, mean / max | 4.2 / 20 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.69 | 0.00 | 0.11 / 0.01 | 6.98 [35] | 8.80 [77] | 2.40 [34] | 11.54 [78] |
| GPU≥50% | 200 | 0.61 | 0.00 | 0.53 / 0.04 | 0.26 [78] | 1.79 [122] | 0.91 [116] | 4.56 [84] |
| 10–50% | 64 | 0.62 | 0.00 | 0.27 / 0.04 | 0.76 [24] | 13.06 [40] | 1.33 [33] | 17.00 [31] |
| miss<10% | 164 | 0.66 | 0.00 | 0.43 / 0.05 | 4.33 [55] | 22.15 [109] | 12.20 [90] | 26.20 [74] |
| mixed | 4 | 0.50 | 0.00 | 0.21 / 0.03 | 19.71 [2] | 14.52 [2] | 1.52 [1] | 14.71 [3] |
