## Admission analysis of `e-tool04-80-p7456-p4` (1159 requests, 84050 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 76 | 6311 | 384 | 1.36 / 3.41 | 0.00 / 0.04 | 0.29 / 0.30 | 0.00 / 0.49 | 0.13 / 0.37 | 0.00 / 0.00 | 0.26 / 0.39 |
| GPU≥50% | 612 | 6185 | 386 | 0.47 / 5.94 | 0.00 / 0.02 | 0.04 / 0.29 | 0.00 / 0.57 | 0.60 / 0.51 | 0.00 / 0.11 | 0.25 / 0.34 |
| 10–50% | 124 | 2214 | 101 | 0.81 / 11.95 | 0.00 / 0.01 | 0.19 / 0.29 | 0.00 / 2.09 | 0.15 / 0.26 | 0.00 / 0.00 | 0.59 / 0.76 |
| miss<10% | 339 | 13742 | 128 | 5.67 / 25.78 | 0.00 / 0.01 | 0.04 / 0.29 | 0.00 / 3.81 | 0.01 / 0.01 | 0.00 / 0.00 | 3.22 / 4.15 |
| mixed | 8 | 3377 | 160 | 1.87 / 18.31 | 0.00 / 0.00 | 0.43 / 0.35 | 0.00 / 3.08 | 0.66 / 0.57 | 0.00 / 0.00 | 0.60 / 0.58 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 76 | 1.21 | 0.07 [6%] | 0.09 [7%] | 0.00 [0%] | 0.21 [17%] | 0.00 [0%] | 0.38 [32%] | 0.11 [9%] | 0.00 [0%] | 0.34 [28%] | 0.00 [0%] |
| GPU≥50% | 612 | 0.88 | 0.00 [0%] | 0.06 [7%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.28 [32%] | 0.01 [1%] | 0.00 [0%] | 0.53 [60%] | 0.00 [0%] |
| 10–50% | 124 | 2.40 | 0.00 [0%] | 0.14 [6%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.29 [12%] | 0.18 [7%] | 0.00 [0%] | 1.78 [74%] | 0.00 [0%] |
| miss<10% | 339 | 4.11 | 0.00 [0%] | 0.19 [5%] | 0.08 [2%] | 0.00 [0%] | 0.09 [2%] | 0.28 [7%] | 0.60 [15%] | 0.00 [0%] | 2.85 [69%] | 0.00 [0%] |
| mixed | 8 | 4.00 | 0.05 [1%] | 0.01 [0%] | 0.00 [0%] | 0.36 [9%] | 0.00 [0%] | 0.51 [13%] | 1.40 [35%] | 0.00 [0%] | 1.67 [42%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 76 | 0.00 | 0.04 | 0.00 | 0.00 |
| GPU≥50% | 612 | 0.00 | 0.02 | 0.00 | 0.00 |
| 10–50% | 124 | 0.00 | 0.01 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.01 | 0.00 | 0.00 |
| mixed | 8 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|
| host≥50% | 76 | 0.00 | 0.30 | 0.00 | 0.00 |
| GPU≥50% | 612 | 0.01 | 0.28 | 0.00 | 0.00 |
| 10–50% | 124 | 0.01 | 0.29 | 0.00 | 0.00 |
| miss<10% | 339 | 0.01 | 0.28 | 0.00 | 0.00 |
| mixed | 8 | 0.00 | 0.35 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:resv | pol:tok | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 76 | 0.04 | 0.00 | 0.00 | 0.00 | 0.11 | 0.00 | 0.34 | 0.00 |
| GPU≥50% | 612 | 0.04 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.52 | 0.00 |
| 10–50% | 124 | 0.13 | 0.00 | 0.00 | 0.00 | 0.18 | 0.00 | 1.78 | 0.00 |
| miss<10% | 339 | 0.18 | 0.08 | 0.09 | 0.00 | 0.60 | 0.00 | 2.85 | 0.00 |
| mixed | 8 | 0.01 | 0.00 | 0.00 | 0.00 | 1.40 | 0.00 | 1.67 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 76 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 612 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 124 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 339 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 8 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 1032 | 1032 / 0 / 0 | 128 | 1067 | 619 (164–1627) | 0 (0) |
| promotion after a load | 18 | 18 / 0 / 0 | 128 | 203 | 162 (158–166) | 0 (0) |

Requests refused at least once: 12 of 1159; preemptions: 4; running requests that could not get their next chunk: 8.
Admitted external loads: 96; reservation passed at admission p50 0 / max 1770 blocks; free blocks at admission p50 5935.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.270 |
| time with free blocks < 50% of the pool | 0.186 |
| time with free blocks < 25% of the pool | 0.098 |
| time with free blocks < 10% of the pool | 0.041 |
| time with free blocks < 5% of the pool | 0.016 |
| blocks held by loads in transfer, mean / max | 3 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 136 / 1921 |
| steps whose running requests used the whole token budget (share of time) | 0.082 |
| steps with a shortened token budget (share of time) | 0.084 |
| running requests, mean / max | 2.1 / 13 |
| waiting + kv-holding requests, mean / max | 0.5 / 9 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 76 | 0.50 | 0.00 | 0.82 / 0.44 | 0.25 [38] | 2.37 [38] | 1.04 [74] | 12.92 [2] |
| GPU≥50% | 612 | 0.43 | 0.00 | 0.79 / 0.39 | 0.16 [346] | 1.58 [266] | 0.41 [597] | 2.21 [15] |
| 10–50% | 124 | 0.42 | 0.00 | 0.79 / 0.37 | 0.41 [72] | 6.14 [52] | 0.78 [120] | 6.14 [4] |
| miss<10% | 339 | 0.43 | 0.00 | 0.82 / 0.43 | 2.72 [192] | 11.65 [147] | 5.62 [334] | 19.26 [5] |
| mixed | 8 | 0.62 | 0.00 | 0.78 / 0.13 | 0.25 [3] | 2.58 [5] | 1.70 [6] | 12.74 [2] |
