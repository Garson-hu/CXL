## Admission analysis of `e66-tool04-80-p7456-base` (1159 requests, 84329 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 6214 | 384 | 6.57 / 31.12 | 0.75 / 3.19 | 1.16 / 5.49 | 0.00 / 0.30 | 0.39 / 0.65 | 0.00 / 0.34 | 0.25 / 0.36 |
| GPU≥50% | 578 | 6187 | 386 | 0.32 / 13.37 | 0.00 / 1.17 | 0.03 / 1.24 | 0.00 / 0.01 | 0.15 / 0.09 | 0.00 / 0.00 | 0.19 / 0.31 |
| 10–50% | 123 | 2211 | 103 | 0.78 / 22.52 | 0.00 / 1.20 | 0.05 / 2.64 | 0.00 / 0.01 | 1.16 / 0.76 | 1.93 / 0.97 | 0.41 / 0.62 |
| miss<10% | 339 | 13886 | 128 | 5.45 / 26.54 | 0.00 / 1.65 | 0.05 / 2.05 | 0.00 / 0.32 | 0.01 / 0.01 | 0.00 / 0.00 | 3.06 / 3.89 |
| mixed | 8 | 3341 | 160 | 11.10 / 34.58 | 1.70 / 5.00 | 2.80 / 5.93 | 0.00 / 0.66 | 0.16 / 0.37 | 0.00 / 0.51 | 0.20 / 0.26 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 9.96 | 5.95 [60%] | 0.35 [4%] | 2.25 [23%] | 0.02 [0%] | 0.18 [2%] | 0.31 [3%] | 0.01 [0%] | 0.88 [9%] | 0.00 [0%] |
| GPU≥50% | 578 | 2.42 | 1.65 [68%] | 0.14 [6%] | 0.23 [9%] | 0.00 [0%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.39 [16%] | 0.00 [0%] |
| 10–50% | 123 | 3.91 | 2.51 [64%] | 0.14 [4%] | 0.79 [20%] | 0.01 [0%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.45 [11%] | 0.00 [0%] |
| miss<10% | 339 | 4.02 | 2.53 [63%] | 0.18 [4%] | 0.54 [14%] | 0.00 [0%] | 0.00 [0%] | 0.32 [8%] | 0.00 [0%] | 0.45 [11%] | 0.00 [0%] |
| mixed | 8 | 12.48 | 6.58 [53%] | 0.47 [4%] | 3.81 [30%] | 0.13 [1%] | 0.12 [1%] | 0.66 [5%] | 0.00 [0%] | 0.70 [6%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 2.64 | 0.14 | 0.39 | 0.02 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 578 | 1.00 | 0.07 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 1.07 | 0.05 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 339 | 1.45 | 0.09 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 8 | 3.28 | 0.20 | 1.39 | 0.13 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 2.87 | 0.19 | 1.73 | 0.00 | 0.00 | 0.00 | 0.71 | 0.00 |
| GPU≥50% | 578 | 0.65 | 0.07 | 0.14 | 0.00 | 0.00 | 0.00 | 0.39 | 0.00 |
| 10–50% | 123 | 1.40 | 0.09 | 0.70 | 0.01 | 0.00 | 0.00 | 0.44 | 0.00 |
| miss<10% | 339 | 1.08 | 0.08 | 0.44 | 0.00 | 0.00 | 0.00 | 0.45 | 0.00 |
| mixed | 8 | 2.80 | 0.23 | 2.27 | 0.00 | 0.00 | 0.00 | 0.63 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | own:full | own:resv | pending |
|---|---|---|---|---|---|
| host≥50% | 111 | 0.00 | 0.29 | 0.01 | 0.00 |
| GPU≥50% | 578 | 0.00 | 0.01 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.01 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.32 | 0.00 | 0.00 |
| mixed | 8 | 0.00 | 0.66 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.26 | 0.01 | 0.04 | 0.00 | 0.00 | 0.02 | 0.00 |
| GPU≥50% | 578 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 8 | 0.51 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1113 | 1107 / 0 / 6 | 384 | 456 | 259 (153–1078) | 0 (149) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3814 | 3814 / 0 / 0 | 128 | 1700 | 820 (233–1878) | 0 (0) |
| promotion after a load | 102 | 102 / 0 / 0 | 106 | 106 | 85 (69–99) | 0 (0) |

Requests refused at least once: 60 of 1159; preemptions: 1; running requests that could not get their next chunk: 2.
Admitted external loads: 126; reservation passed at admission p50 0 / max 326 blocks; free blocks at admission p50 4738.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.264 |
| time with free blocks < 50% of the pool | 0.177 |
| time with free blocks < 25% of the pool | 0.096 |
| time with free blocks < 10% of the pool | 0.039 |
| time with free blocks < 5% of the pool | 0.019 |
| blocks held by loads in transfer, mean / max | 8 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 119 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.202 |
| running requests, mean / max | 1.9 / 16 |
| waiting + kv-holding requests, mean / max | 0.9 / 18 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.59 | 0.53 | 0.73 / 0.23 | 0.29 [45] | 14.32 [66] | 3.28 [97] | 18.36 [14] |
| GPU≥50% | 578 | 0.32 | 0.28 | 0.81 / 0.45 | 0.18 [395] | 5.64 [183] | 0.30 [560] | 18.00 [18] |
| 10–50% | 123 | 0.35 | 0.33 | 0.80 / 0.43 | 0.42 [80] | 7.91 [43] | 0.77 [121] | 27.53 [2] |
| miss<10% | 339 | 0.38 | 0.33 | 0.82 / 0.41 | 2.82 [211] | 10.97 [128] | 5.20 [325] | 24.93 [14] |
| mixed | 8 | 0.62 | 0.50 | 0.78 / 0.23 | 0.22 [3] | 20.40 [5] | 3.19 [7] | 33.73 [1] |
