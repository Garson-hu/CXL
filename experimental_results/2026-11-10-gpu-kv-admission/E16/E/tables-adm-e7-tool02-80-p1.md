## Admission analysis of `e7-tool02-80-p1` (544 requests, 43645 engine steps, pool 8753 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 20 | 3331 | 160 | 3.17 / 60.88 | 0.00 / 0.07 | 1.07 / 0.82 | 0.00 / 7.19 | 1.08 / 0.92 | 0.00 / 0.00 | 0.50 / 0.70 |
| GPU≥50% | 284 | 6201 | 386 | 0.74 / 9.00 | 0.00 / 0.02 | 0.06 / 0.55 | 0.00 / 0.90 | 1.07 / 1.07 | 0.00 / 0.00 | 0.47 / 0.60 |
| 10–50% | 64 | 2038 | 96 | 1.20 / 17.14 | 0.00 / 0.03 | 0.05 / 0.46 | 0.00 / 3.70 | – | – | 1.02 / 1.07 |
| miss<10% | 176 | 13996 | 128 | 10.39 / 48.08 | 0.00 / 0.02 | 0.05 / 0.52 | 0.00 / 6.19 | – | – | 6.20 / 7.75 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 20 | 8.99 | 0.14 [2%] | 0.53 [6%] | 2.04 [23%] | 0.45 [5%] | 0.63 [7%] | 1.01 [11%] | 4.18 [47%] | 0.00 [0%] |
| GPU≥50% | 284 | 1.48 | 0.00 [0%] | 0.09 [6%] | 0.00 [0%] | 0.00 [0%] | 0.01 [0%] | 0.54 [37%] | 0.84 [57%] | 0.00 [0%] |
| 10–50% | 64 | 4.19 | 0.00 [0%] | 0.18 [4%] | 0.49 [12%] | 0.00 [0%] | 0.13 [3%] | 0.45 [11%] | 2.94 [70%] | 0.00 [0%] |
| miss<10% | 176 | 6.74 | 0.00 [0%] | 0.37 [6%] | 0.80 [12%] | 0.00 [0%] | 0.47 [7%] | 0.52 [8%] | 4.58 [68%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 20 | 0.00 | 0.07 | 0.00 | 0.00 |
| GPU≥50% | 284 | 0.00 | 0.02 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.03 | 0.00 | 0.00 |
| miss<10% | 176 | 0.00 | 0.02 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok |
|---|---|---|---|---|
| host≥50% | 20 | 0.02 | 0.80 | 0.00 |
| GPU≥50% | 284 | 0.01 | 0.54 | 0.00 |
| 10–50% | 64 | 0.01 | 0.45 | 0.00 |
| miss<10% | 176 | 0.00 | 0.52 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:tok | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 20 | 0.44 | 1.94 | 0.63 | 0.00 | 4.18 | 0.00 |
| GPU≥50% | 284 | 0.06 | 0.00 | 0.01 | 0.00 | 0.84 | 0.00 |
| 10–50% | 64 | 0.14 | 0.49 | 0.13 | 0.00 | 2.94 | 0.00 |
| miss<10% | 176 | 0.35 | 0.80 | 0.47 | 0.00 | 4.58 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 20 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 284 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 176 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 187 | 187 / 0 / 0 | 160 | 209 | 99 (60–136) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 1058 | 1058 / 0 / 0 | 128 | 865 | 340 (29–1969) | 0 (0) |

Requests refused at least once: 12 of 544; preemptions: 1; running requests that could not get their next chunk: 2.
Admitted external loads: 21; reservation passed at admission p50 140 / max 1241 blocks; free blocks at admission p50 7120.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.223 |
| time with free blocks < 50% of the pool | 0.133 |
| time with free blocks < 25% of the pool | 0.061 |
| time with free blocks < 10% of the pool | 0.028 |
| time with free blocks < 5% of the pool | 0.017 |
| blocks held by loads in transfer, mean / max | 1 / 416 |
| in-flight prefill reservation after schedule(), mean / max | 132 / 1908 |
| steps whose running requests used the whole token budget (share of time) | 0.082 |
| steps with a shortened token budget (share of time) | 0.072 |
| running requests, mean / max | 1.9 / 13 |
| waiting + kv-holding requests, mean / max | 0.4 / 8 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 20 | 0.60 | 0.00 | 0.84 / 0.48 | 0.41 [8] | 4.76 [12] | 3.17 [20] | – |
| GPU≥50% | 284 | 0.42 | 0.00 | 0.86 / 0.46 | 0.30 [164] | 3.01 [120] | 0.74 [284] | – |
| 10–50% | 64 | 0.34 | 0.00 | 0.90 / 0.57 | 0.75 [42] | 11.35 [22] | 1.20 [64] | – |
| miss<10% | 176 | 0.41 | 0.00 | 0.86 / 0.48 | 5.42 [103] | 20.78 [73] | 10.39 [176] | – |
