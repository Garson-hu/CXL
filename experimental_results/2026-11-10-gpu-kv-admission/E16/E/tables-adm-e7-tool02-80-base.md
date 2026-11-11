## Admission analysis of `e7-tool02-80-base` (544 requests, 43376 engine steps, pool 8753 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 25 | 3178 | 160 | 14.44 / 56.62 | 1.75 / 4.49 | 1.93 / 7.27 | 0.00 / 0.87 | 1.56 / 1.55 | 0.00 / 1.01 | 0.37 / 0.95 |
| GPU≥50% | 278 | 6221 | 272 | 0.64 / 20.14 | 0.00 / 2.09 | 0.05 / 1.85 | 0.00 / 0.01 | – | – | 0.35 / 0.57 |
| 10–50% | 65 | 2038 | 96 | 1.21 / 19.11 | 0.00 / 2.42 | 0.05 / 1.87 | 0.00 / 0.00 | 0.12 / 0.12 | 0.00 / 0.00 | 0.74 / 0.97 |
| miss<10% | 175 | 13996 | 128 | 9.62 / 46.66 | 0.00 / 2.65 | 0.06 / 3.48 | 0.00 / 0.23 | – | – | 5.88 / 7.37 |
| mixed | 1 | 3331 | 160 | 54.58 / 54.58 | 7.55 / 7.55 | 34.19 / 34.19 | 11.73 / 11.73 | 0.25 / 0.25 | 0.00 / 0.00 | 0.49 / 0.49 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 25 | 15.18 | 10.00 [66%] | 0.91 [6%] | 1.49 [10%] | 0.38 [2%] | 0.72 [5%] | 1.69 [11%] | 0.00 [0%] |
| GPU≥50% | 278 | 3.95 | 2.72 [69%] | 0.19 [5%] | 0.31 [8%] | 0.00 [0%] | 0.00 [0%] | 0.71 [18%] | 0.00 [0%] |
| 10–50% | 65 | 4.30 | 2.92 [68%] | 0.15 [4%] | 0.60 [14%] | 0.00 [0%] | 0.00 [0%] | 0.62 [15%] | 0.00 [0%] |
| miss<10% | 175 | 6.37 | 4.40 [69%] | 0.40 [6%] | 0.57 [9%] | 0.00 [0%] | 0.23 [4%] | 0.76 [12%] | 0.00 [0%] |
| mixed | 1 | 53.73 | 35.52 [66%] | 5.20 [10%] | 0.20 [0%] | 0.00 [0%] | 11.73 [22%] | 1.08 [2%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 25 | 4.22 | 0.27 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 278 | 1.85 | 0.10 | 0.14 | 0.00 | 0.00 | 0.00 |
| 10–50% | 65 | 2.04 | 0.06 | 0.32 | 0.00 | 0.00 | 0.00 |
| miss<10% | 175 | 2.38 | 0.17 | 0.10 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 5.44 | 2.11 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 25 | 4.11 | 0.55 | 1.24 | 0.00 | 1.36 | 0.00 |
| GPU≥50% | 278 | 0.88 | 0.10 | 0.16 | 0.00 | 0.71 | 0.00 |
| 10–50% | 65 | 0.88 | 0.09 | 0.28 | 0.00 | 0.62 | 0.00 |
| miss<10% | 175 | 2.02 | 0.23 | 0.47 | 0.00 | 0.76 | 0.00 |
| mixed | 1 | 30.08 | 3.08 | 0.00 | 0.00 | 1.03 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|
| host≥50% | 25 | 0.23 | 0.64 | 0.00 | 0.00 |
| GPU≥50% | 278 | 0.01 | 0.00 | 0.00 | 0.00 |
| 10–50% | 65 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 175 | 0.00 | 0.23 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 11.73 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 25 | 0.86 | 0.08 | 0.00 | 0.00 | 0.08 | 0.00 | 0.00 |
| GPU≥50% | 278 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 65 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 175 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 384 | 384 / 0 / 0 | 384 | 409 | 54 (11–142) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 859 | 859 / 0 / 0 | 128 | 865 | 319 (66–1971) | 0 (0) |
| promotion after a load | 34 | 34 / 0 / 0 | 24 | 24 | 9 (1–14) | 0 (0) |

Requests refused at least once: 12 of 544; preemptions: 2; running requests that could not get their next chunk: 5.
Admitted external loads: 27; reservation passed at admission p50 0 / max 142 blocks; free blocks at admission p50 6274.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.222 |
| time with free blocks < 50% of the pool | 0.131 |
| time with free blocks < 25% of the pool | 0.064 |
| time with free blocks < 10% of the pool | 0.031 |
| time with free blocks < 5% of the pool | 0.018 |
| blocks held by loads in transfer, mean / max | 3 / 704 |
| in-flight prefill reservation after schedule(), mean / max | 116 / 1908 |
| steps whose running requests used the whole token budget (share of time) | 0.196 |
| running requests, mean / max | 1.8 / 14 |
| waiting + kv-holding requests, mean / max | 0.6 / 10 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 25 | 0.68 | 0.60 | 0.77 / 0.48 | 0.41 [8] | 16.12 [17] | 14.44 [25] | – |
| GPU≥50% | 278 | 0.33 | 0.31 | 0.86 / 0.46 | 0.34 [187] | 8.78 [91] | 0.59 [276] | 20.14 [2] |
| 10–50% | 65 | 0.32 | 0.29 | 0.89 / 0.55 | 0.79 [44] | 9.87 [21] | 1.21 [65] | – |
| miss<10% | 175 | 0.38 | 0.33 | 0.86 / 0.42 | 5.57 [109] | 20.91 [66] | 9.46 [173] | 68.46 [2] |
| mixed | 1 | 1.00 | 1.00 | 0.66 / 0.66 | – | 54.58 [1] | 54.58 [1] | – |
