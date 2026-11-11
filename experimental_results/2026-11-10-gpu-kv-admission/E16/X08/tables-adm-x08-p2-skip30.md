## Admission analysis of `x08-p2-skip30` (544 requests, 21052 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 104 | 6178 | 384 | 4.45 / 26.82 | 0.00 / 1.79 | 0.57 / 0.66 | 0.03 / 5.48 | 0.69 / 0.73 | 0.00 / 0.02 | 0.51 / 0.60 |
| GPU≥50% | 209 | 6214 | 80 | 1.16 / 17.62 | 0.00 / 0.49 | 0.34 / 0.54 | 0.15 / 2.17 | 0.70 / 0.72 | 0.00 / 0.00 | 0.41 / 0.45 |
| 10–50% | 64 | 2103 | 99 | 3.79 / 46.60 | 0.00 / 1.66 | 0.48 / 0.67 | 1.96 / 7.45 | 0.76 / 0.73 | 0.00 / 0.00 | 0.68 / 0.98 |
| miss<10% | 164 | 13883 | 128 | 15.82 / 51.51 | 0.00 / 0.49 | 0.37 / 0.52 | 11.03 / 13.86 | 0.60 / 0.60 | 0.00 / 0.00 | 3.78 / 4.62 |
| mixed | 3 | 7294 | 195 | 19.95 / 20.16 | 4.17 / 3.87 | 0.79 / 0.79 | 11.84 / 11.84 | 0.98 / 0.98 | 0.00 / 0.00 | 1.45 / 1.53 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 104 | 8.67 | 0.01 [0%] | 0.10 [1%] | 3.65 [42%] | 0.26 [3%] | 0.41 [5%] | 0.11 [1%] | 0.01 [0%] | 0.70 [8%] | 2.85 [33%] | 0.03 [0%] | 0.54 [6%] | 0.01 [0%] |
| GPU≥50% | 209 | 3.25 | 0.00 [0%] | 0.10 [3%] | 1.03 [32%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.00 [0%] | 0.36 [11%] | 0.76 [23%] | 0.03 [1%] | 0.96 [30%] | 0.00 [0%] |
| 10–50% | 64 | 9.83 | 0.00 [0%] | 0.21 [2%] | 3.43 [35%] | 0.08 [1%] | 0.04 [0%] | 0.02 [0%] | 0.00 [0%] | 0.43 [4%] | 1.08 [11%] | 0.12 [1%] | 4.41 [45%] | 0.01 [0%] |
| miss<10% | 164 | 14.88 | 0.00 [0%] | 0.54 [4%] | 2.63 [18%] | 0.12 [1%] | 0.00 [0%] | 0.81 [5%] | 0.00 [0%] | 0.37 [2%] | 2.55 [17%] | 0.11 [1%] | 7.75 [52%] | 0.01 [0%] |
| mixed | 3 | 17.49 | 0.00 [0%] | 0.43 [2%] | 3.85 [22%] | 0.00 [0%] | 0.59 [3%] | 0.00 [0%] | 0.00 [0%] | 1.19 [7%] | 11.43 [65%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 104 | 0.00 | 0.01 | 1.62 | 0.15 | 0.00 | 0.00 |
| GPU≥50% | 209 | 0.00 | 0.02 | 0.47 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.02 | 1.59 | 0.06 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.48 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.02 | 3.85 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 104 | 0.01 | 0.13 | 0.51 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 209 | 0.01 | 0.19 | 0.34 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.24 | 0.42 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.01 | 0.15 | 0.37 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.79 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 104 | 0.07 | 1.77 | 0.11 | 0.09 | 0.01 | 0.00 | 2.85 | 0.03 | 0.54 | 0.01 |
| GPU≥50% | 209 | 0.07 | 0.36 | 0.00 | 0.00 | 0.00 | 0.00 | 0.76 | 0.03 | 0.96 | 0.00 |
| 10–50% | 64 | 0.19 | 1.60 | 0.02 | 0.02 | 0.00 | 0.00 | 1.08 | 0.12 | 4.40 | 0.01 |
| miss<10% | 164 | 0.53 | 2.00 | 0.11 | 0.81 | 0.00 | 0.00 | 2.55 | 0.11 | 7.75 | 0.01 |
| mixed | 3 | 0.41 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 11.43 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 104 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 209 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 230 | 229 / 0 / 1 | 896 | 1030 | 631 (610–669) | 0 (446) |
| compute, no computed tokens (miss / GPU-prefix hit) | 2597 | 2406 / 0 / 191 | 128 | 1201 | 611 (140–1316) | 0 (600) |
| promotion after a load | 29 | 29 / 0 / 0 | 37 | 37 | 13 (1–28) | 0 (0) |

Requests refused at least once: 37 of 544; preemptions: 10; running requests that could not get their next chunk: 20.
Admitted external loads: 124; reservation passed at admission p50 282 / max 1825 blocks; free blocks at admission p50 1217.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.635 |
| time with free blocks < 50% of the pool | 0.684 |
| time with free blocks < 25% of the pool | 0.561 |
| time with free blocks < 10% of the pool | 0.312 |
| time with free blocks < 5% of the pool | 0.161 |
| blocks held by loads in transfer, mean / max | 25 / 2000 |
| in-flight prefill reservation after schedule(), mean / max | 298 / 2175 |
| steps whose running requests used the whole token budget (share of time) | 0.064 |
| steps with a shortened token budget (share of time) | 0.170 |
| running requests, mean / max | 6.8 / 15 |
| waiting + kv-holding requests, mean / max | 3.7 / 23 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 104 | 0.55 | 0.00 | 0.12 / 0.02 | 7.69 [47] | 2.56 [57] | 1.93 [27] | 7.63 [77] |
| GPU≥50% | 209 | 0.60 | 0.00 | 0.50 / 0.07 | 0.23 [84] | 1.69 [125] | 0.97 [123] | 2.17 [86] |
| 10–50% | 64 | 0.53 | 0.00 | 0.32 / 0.06 | 1.05 [30] | 6.72 [34] | 1.28 [33] | 18.37 [31] |
| miss<10% | 164 | 0.61 | 0.00 | 0.42 / 0.04 | 4.37 [64] | 20.84 [100] | 12.42 [94] | 24.42 [70] |
| mixed | 3 | 0.00 | 0.00 | 0.08 / 0.08 | 19.95 [3] | – | – | 19.95 [3] |
