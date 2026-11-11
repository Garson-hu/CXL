## Admission analysis of `tool08-320-p3` (544 requests, 21110 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 6237 | 384 | 13.08 / 43.08 | 0.56 / 5.10 | 0.57 / 1.24 | 0.57 / 7.35 | 0.78 / 0.82 | 0.00 / 0.04 | 0.64 / 0.66 |
| GPU≥50% | 206 | 6198 | 65 | 1.57 / 33.95 | 0.00 / 3.74 | 0.34 / 0.63 | 0.17 / 3.81 | 0.85 / 0.82 | 0.00 / 0.23 | 0.40 / 0.44 |
| 10–50% | 64 | 2103 | 94 | 8.94 / 40.99 | 0.00 / 4.98 | 0.42 / 0.52 | 3.37 / 6.94 | 0.97 / 0.75 | 0.00 / 0.61 | 0.69 / 1.00 |
| miss<10% | 164 | 13883 | 128 | 16.91 / 45.07 | 0.00 / 2.86 | 0.39 / 0.70 | 8.61 / 11.26 | 0.30 / 0.30 | 0.00 / 0.00 | 3.64 / 4.55 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 14.55 | 3.24 [22%] | 0.39 [3%] | 6.85 [47%] | 0.67 [5%] | 0.30 [2%] | 0.51 [4%] | 0.27 [2%] | 0.69 [5%] | 0.70 [5%] | 0.10 [1%] | 0.79 [5%] | 0.00 [0%] | 0.04 [0%] |
| GPU≥50% | 206 | 8.26 | 2.30 [28%] | 0.25 [3%] | 3.33 [40%] | 0.36 [4%] | 0.01 [0%] | 0.08 [1%] | 0.02 [0%] | 0.37 [5%] | 0.33 [4%] | 0.06 [1%] | 1.12 [14%] | 0.00 [0%] | 0.04 [1%] |
| 10–50% | 64 | 12.52 | 3.31 [26%] | 0.35 [3%] | 4.34 [35%] | 0.54 [4%] | 0.02 [0%] | 0.15 [1%] | 0.02 [0%] | 0.38 [3%] | 0.25 [2%] | 0.03 [0%] | 3.07 [24%] | 0.00 [0%] | 0.06 [0%] |
| miss<10% | 164 | 14.83 | 2.58 [17%] | 0.62 [4%] | 4.86 [33%] | 0.36 [2%] | 0.00 [0%] | 1.72 [12%] | 0.00 [0%] | 0.37 [3%] | 0.14 [1%] | 0.03 [0%] | 4.12 [28%] | 0.00 [0%] | 0.03 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | pending | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 1.92 | 0.11 | 2.85 | 0.22 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 206 | 1.57 | 0.11 | 1.95 | 0.11 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 2.37 | 0.04 | 2.33 | 0.23 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 1.09 | 0.09 | 1.53 | 0.14 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.03 | 0.04 | 0.66 | 0.00 | 0.50 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 206 | 0.03 | 0.02 | 0.21 | 0.00 | 0.36 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| 10–50% | 64 | 0.00 | 0.03 | 0.10 | 0.00 | 0.37 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 |
| miss<10% | 164 | 0.02 | 0.02 | 0.25 | 0.03 | 0.37 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | own:resv | pending | pol:blocks | pol:resv | pol:tok | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 1.18 | 0.20 | 3.17 | 0.41 | 0.51 | 0.27 | 0.00 | 0.70 | 0.10 | 0.79 | 0.00 | 0.01 |
| GPU≥50% | 206 | 0.69 | 0.12 | 1.14 | 0.25 | 0.06 | 0.02 | 0.00 | 0.33 | 0.06 | 1.12 | 0.00 | 0.03 |
| 10–50% | 64 | 0.89 | 0.28 | 1.91 | 0.29 | 0.15 | 0.02 | 0.00 | 0.25 | 0.03 | 3.06 | 0.00 | 0.04 |
| miss<10% | 164 | 1.47 | 0.50 | 3.07 | 0.19 | 1.72 | 0.00 | 0.00 | 0.14 | 0.03 | 4.12 | 0.00 | 0.02 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.02 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 206 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1189 | 1105 / 0 / 84 | 384 | 456 | 254 (35–671) | 0 (1726) |
| compute, no computed tokens (miss / GPU-prefix hit) | 5945 | 5857 / 0 / 88 | 128 | 1067 | 528 (108–1357) | 0 (600) |
| promotion after a load | 71 | 71 / 0 / 0 | 42 | 42 | 20 (3–31) | 0 (0) |

Requests refused at least once: 127 of 544; preemptions: 11; running requests that could not get their next chunk: 22.
Admitted external loads: 129; reservation passed at admission p50 151 / max 1852 blocks; free blocks at admission p50 1249.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.639 |
| time with free blocks < 50% of the pool | 0.687 |
| time with free blocks < 25% of the pool | 0.558 |
| time with free blocks < 10% of the pool | 0.317 |
| time with free blocks < 5% of the pool | 0.174 |
| blocks held by loads in transfer, mean / max | 28 / 2160 |
| in-flight prefill reservation after schedule(), mean / max | 290 / 1898 |
| steps whose running requests used the whole token budget (share of time) | 0.142 |
| steps with a shortened token budget (share of time) | 0.160 |
| running requests, mean / max | 6.7 / 16 |
| waiting + kv-holding requests, mean / max | 5.1 / 33 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 110 | 0.75 | 0.15 | 0.14 / 0.04 | 15.28 [27] | 12.12 [83] | 3.00 [30] | 13.39 [80] |
| GPU≥50% | 206 | 0.57 | 0.14 | 0.47 / 0.04 | 0.28 [88] | 3.16 [118] | 0.90 [117] | 15.94 [89] |
| 10–50% | 64 | 0.58 | 0.17 | 0.20 / 0.04 | 1.34 [27] | 13.71 [37] | 1.12 [29] | 20.56 [35] |
| miss<10% | 164 | 0.71 | 0.09 | 0.41 / 0.04 | 4.41 [47] | 20.33 [117] | 13.29 [95] | 24.26 [69] |
