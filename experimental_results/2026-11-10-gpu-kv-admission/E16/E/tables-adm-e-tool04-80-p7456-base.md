## Admission analysis of `e-tool04-80-p7456-base` (1159 requests, 84089 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 6214 | 384 | 6.60 / 31.30 | 0.75 / 3.15 | 1.17 / 5.49 | 0.00 / 0.30 | 0.40 / 0.65 | 0.00 / 0.34 | 0.25 / 0.36 |
| GPU≥50% | 577 | 6187 | 386 | 0.32 / 13.46 | 0.00 / 1.18 | 0.03 / 1.26 | 0.00 / 0.01 | 0.15 / 0.09 | 0.00 / 0.00 | 0.19 / 0.31 |
| 10–50% | 123 | 2211 | 103 | 0.78 / 22.70 | 0.00 / 1.23 | 0.05 / 2.65 | 0.00 / 0.01 | 1.16 / 0.76 | 1.93 / 0.98 | 0.41 / 0.63 |
| miss<10% | 339 | 13886 | 128 | 5.49 / 26.66 | 0.00 / 1.67 | 0.05 / 2.06 | 0.00 / 0.32 | 0.01 / 0.01 | 0.00 / 0.00 | 3.08 / 3.91 |
| mixed | 8 | 3341 | 160 | 11.18 / 34.78 | 1.71 / 5.02 | 2.81 / 5.95 | 0.00 / 0.67 | 0.17 / 0.37 | 0.00 / 0.52 | 0.20 / 0.26 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 9.94 | 5.93 [60%] | 0.35 [4%] | 2.24 [23%] | 0.02 [0%] | 0.18 [2%] | 0.31 [3%] | 0.01 [0%] | 0.88 [9%] | 0.00 [0%] |
| GPU≥50% | 577 | 2.45 | 1.68 [68%] | 0.14 [6%] | 0.23 [9%] | 0.00 [0%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.39 [16%] | 0.00 [0%] |
| 10–50% | 123 | 3.94 | 2.54 [64%] | 0.14 [4%] | 0.79 [20%] | 0.01 [0%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.45 [11%] | 0.00 [0%] |
| miss<10% | 339 | 4.06 | 2.55 [63%] | 0.18 [4%] | 0.55 [13%] | 0.00 [0%] | 0.00 [0%] | 0.32 [8%] | 0.00 [0%] | 0.46 [11%] | 0.00 [0%] |
| mixed | 8 | 12.53 | 6.61 [53%] | 0.48 [4%] | 3.82 [30%] | 0.13 [1%] | 0.12 [1%] | 0.67 [5%] | 0.00 [0%] | 0.70 [6%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 2.60 | 0.14 | 0.39 | 0.02 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 577 | 1.01 | 0.07 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 1.09 | 0.05 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 339 | 1.47 | 0.10 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 8 | 3.29 | 0.20 | 1.40 | 0.13 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 2.88 | 0.19 | 1.72 | 0.00 | 0.00 | 0.00 | 0.70 | 0.00 |
| GPU≥50% | 577 | 0.67 | 0.07 | 0.14 | 0.00 | 0.00 | 0.00 | 0.39 | 0.00 |
| 10–50% | 123 | 1.40 | 0.09 | 0.71 | 0.01 | 0.00 | 0.00 | 0.44 | 0.00 |
| miss<10% | 339 | 1.08 | 0.08 | 0.44 | 0.00 | 0.00 | 0.00 | 0.46 | 0.00 |
| mixed | 8 | 2.81 | 0.23 | 2.28 | 0.00 | 0.00 | 0.00 | 0.63 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | own:full | own:resv | pending |
|---|---|---|---|---|---|
| host≥50% | 112 | 0.00 | 0.29 | 0.01 | 0.00 |
| GPU≥50% | 577 | 0.00 | 0.01 | 0.00 | 0.00 |
| 10–50% | 123 | 0.00 | 0.01 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.32 | 0.00 | 0.00 |
| mixed | 8 | 0.00 | 0.67 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.26 | 0.01 | 0.04 | 0.00 | 0.00 | 0.02 | 0.00 |
| GPU≥50% | 577 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 123 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 8 | 0.52 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1113 | 1107 / 0 / 6 | 384 | 456 | 262 (153–1076) | 0 (149) |
| compute, no computed tokens (miss / GPU-prefix hit) | 3832 | 3832 / 0 / 0 | 128 | 1700 | 820 (234–1877) | 0 (0) |
| promotion after a load | 102 | 102 / 0 / 0 | 106 | 106 | 85 (69–99) | 0 (0) |

Requests refused at least once: 60 of 1159; preemptions: 1; running requests that could not get their next chunk: 2.
Admitted external loads: 127; reservation passed at admission p50 0 / max 326 blocks; free blocks at admission p50 4678.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.265 |
| time with free blocks < 50% of the pool | 0.178 |
| time with free blocks < 25% of the pool | 0.096 |
| time with free blocks < 10% of the pool | 0.040 |
| time with free blocks < 5% of the pool | 0.019 |
| blocks held by loads in transfer, mean / max | 8 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 120 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.203 |
| running requests, mean / max | 1.9 / 16 |
| waiting + kv-holding requests, mean / max | 0.9 / 18 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 112 | 0.60 | 0.54 | 0.73 / 0.23 | 0.29 [45] | 14.38 [67] | 3.30 [98] | 18.53 [14] |
| GPU≥50% | 577 | 0.32 | 0.28 | 0.81 / 0.43 | 0.18 [394] | 5.67 [183] | 0.30 [558] | 15.54 [19] |
| 10–50% | 123 | 0.36 | 0.33 | 0.80 / 0.42 | 0.41 [79] | 8.01 [44] | 0.78 [121] | 27.66 [2] |
| miss<10% | 339 | 0.38 | 0.33 | 0.82 / 0.42 | 2.84 [210] | 11.09 [129] | 5.25 [325] | 25.11 [14] |
| mixed | 8 | 0.62 | 0.50 | 0.78 / 0.23 | 0.21 [3] | 20.49 [5] | 3.21 [7] | 33.94 [1] |
