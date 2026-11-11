## Admission analysis of `tool08-320-lpt1024` (544 requests, 19838 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 6169 | 384 | 23.82 / 43.46 | 4.15 / 7.14 | 10.68 / 11.73 | 0.00 / 1.74 | 0.97 / 1.00 | 0.00 / 0.34 | 0.63 / 0.73 |
| GPU≥50% | 211 | 6251 | 37 | 12.73 / 40.24 | 2.67 / 5.45 | 1.81 / 8.54 | 0.00 / 0.05 | 0.32 / 0.56 | 0.00 / 0.00 | 0.57 / 0.65 |
| 10–50% | 64 | 2103 | 64 | 11.77 / 39.79 | 1.07 / 4.11 | 1.70 / 9.46 | 0.00 / 0.28 | 1.38 / 1.13 | 1.68 / 0.98 | 0.97 / 1.37 |
| miss<10% | 167 | 13886 | 64 | 20.58 / 48.97 | 1.51 / 4.43 | 3.90 / 8.92 | 0.00 / 1.68 | 1.07 / 1.07 | 2.05 / 2.05 | 5.24 / 6.88 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 21.96 | 5.38 [25%] | 1.05 [5%] | 11.16 [51%] | 1.93 [9%] | 0.18 [1%] | 0.66 [3%] | 0.57 [3%] | 0.68 [3%] | 0.09 [0%] | 0.25 [1%] |
| GPU≥50% | 211 | 14.05 | 3.31 [24%] | 0.71 [5%] | 7.42 [53%] | 1.80 [13%] | 0.00 [0%] | 0.02 [0%] | 0.03 [0%] | 0.44 [3%] | 0.06 [0%] | 0.25 [2%] |
| 10–50% | 64 | 13.98 | 3.00 [21%] | 0.87 [6%] | 7.43 [53%] | 1.72 [12%] | 0.01 [0%] | 0.16 [1%] | 0.09 [1%] | 0.45 [3%] | 0.06 [0%] | 0.17 [1%] |
| miss<10% | 167 | 15.05 | 4.01 [27%] | 0.78 [5%] | 6.93 [46%] | 1.31 [9%] | 0.00 [0%] | 1.28 [8%] | 0.00 [0%] | 0.51 [3%] | 0.06 [0%] | 0.17 [1%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 1.95 | 0.39 | 3.93 | 0.65 | 0.00 | 0.00 | 0.01 | 0.21 |
| GPU≥50% | 211 | 1.46 | 0.25 | 3.08 | 0.55 | 0.00 | 0.00 | 0.01 | 0.10 |
| 10–50% | 64 | 1.13 | 0.22 | 2.25 | 0.38 | 0.00 | 0.00 | 0.01 | 0.12 |
| miss<10% | 167 | 1.56 | 0.29 | 2.08 | 0.35 | 0.00 | 0.00 | 0.01 | 0.14 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 2.94 | 0.54 | 6.52 | 1.13 | 0.00 | 0.00 | 0.53 | 0.07 | 0.00 |
| GPU≥50% | 211 | 1.84 | 0.46 | 4.34 | 1.25 | 0.00 | 0.00 | 0.44 | 0.05 | 0.15 |
| 10–50% | 64 | 1.86 | 0.64 | 5.08 | 1.33 | 0.00 | 0.00 | 0.45 | 0.06 | 0.05 |
| miss<10% | 167 | 2.42 | 0.47 | 4.48 | 0.97 | 0.00 | 0.00 | 0.51 | 0.04 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | own:resv | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 0.03 | 0.02 | 0.47 | 0.64 | 0.57 | 0.00 | 0.00 |
| GPU≥50% | 211 | 0.00 | 0.00 | 0.00 | 0.02 | 0.03 | 0.00 | 0.00 |
| 10–50% | 64 | 0.01 | 0.01 | 0.06 | 0.11 | 0.09 | 0.00 | 0.00 |
| miss<10% | 167 | 0.03 | 0.01 | 0.35 | 1.27 | 0.00 | 0.00 | 0.01 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 0.26 | 0.04 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 211 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.05 | 0.00 | 0.00 | 0.00 |
| miss<10% | 167 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1457 | 1209 / 0 / 248 | 384 | 413 | 308 (73–1194) | 0 (2055) |
| compute, no computed tokens (miss / GPU-prefix hit) | 6162 | 6162 / 0 / 0 | 64 | 1067 | 495 (60–1159) | 0 (0) |
| promotion after a load | 105 | 105 / 0 / 0 | 64 | 661 | 615 (184–634) | 0 (0) |

Requests refused at least once: 171 of 544; preemptions: 74; running requests that could not get their next chunk: 148.
Admitted external loads: 110; reservation passed at admission p50 183 / max 1951 blocks; free blocks at admission p50 1600.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.686 |
| time with free blocks < 50% of the pool | 0.734 |
| time with free blocks < 25% of the pool | 0.635 |
| time with free blocks < 10% of the pool | 0.389 |
| time with free blocks < 5% of the pool | 0.241 |
| blocks held by loads in transfer, mean / max | 29 / 1696 |
| in-flight prefill reservation after schedule(), mean / max | 480 / 3785 |
| steps whose running requests used the whole token budget (share of time) | 0.219 |
| running requests, mean / max | 7.5 / 16 |
| waiting + kv-holding requests, mean / max | 6.8 / 26 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 102 | 0.79 | 0.33 | 0.14 / 0.03 | 5.49 [21] | 24.33 [81] | 20.98 [28] | 24.19 [74] |
| GPU≥50% | 211 | 0.57 | 0.18 | 0.16 / 0.02 | 0.77 [90] | 17.66 [121] | 0.81 [94] | 22.51 [117] |
| 10–50% | 64 | 0.58 | 0.17 | 0.19 / 0.01 | 3.89 [27] | 21.11 [37] | 1.00 [27] | 23.55 [37] |
| miss<10% | 167 | 0.66 | 0.28 | 0.24 / 0.02 | 6.46 [57] | 22.93 [110] | 8.98 [80] | 31.11 [87] |
