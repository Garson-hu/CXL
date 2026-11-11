## Admission analysis of `tool08-320-skip30` (544 requests, 21713 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 6178 | 384 | 10.03 / 25.64 | 2.21 / 3.99 | 0.86 / 1.80 | 0.97 / 3.67 | 0.44 / 0.67 | 0.00 / 0.27 | 0.30 / 0.42 |
| GPU≥50% | 205 | 6221 | 62 | 3.82 / 22.15 | 0.41 / 2.63 | 0.71 / 1.30 | 0.00 / 2.06 | 0.30 / 0.71 | 0.00 / 0.35 | 0.33 / 0.41 |
| 10–50% | 64 | 2103 | 87 | 5.77 / 21.00 | 0.43 / 2.94 | 0.73 / 1.43 | 0.00 / 2.95 | 1.26 / 1.00 | 0.12 / 0.55 | 0.72 / 0.88 |
| miss<10% | 164 | 13883 | 128 | 12.35 / 46.38 | 0.00 / 2.26 | 0.76 / 2.19 | 0.00 / 7.06 | 1.98 / 1.98 | 0.00 / 0.00 | 3.21 / 4.14 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | hol:resv | other | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 10.41 | 5.80 [56%] | 0.32 [3%] | 1.51 [15%] | 0.00 [0%] | 0.28 [3%] | 0.00 [0%] | 0.93 [9%] | 1.55 [15%] | 0.00 [0%] | 0.01 [0%] |
| GPU≥50% | 205 | 6.06 | 3.71 [61%] | 0.32 [5%] | 0.23 [4%] | 0.00 [0%] | 0.02 [0%] | 0.00 [0%] | 0.59 [10%] | 1.18 [19%] | 0.00 [0%] | 0.01 [0%] |
| 10–50% | 64 | 7.42 | 4.30 [58%] | 0.35 [5%] | 0.97 [13%] | 0.00 [0%] | 0.01 [0%] | 0.00 [0%] | 0.64 [9%] | 1.11 [15%] | 0.00 [0%] | 0.03 [0%] |
| miss<10% | 164 | 11.53 | 6.23 [54%] | 0.45 [4%] | 0.64 [6%] | 0.01 [0%] | 0.00 [0%] | 0.20 [2%] | 0.60 [5%] | 3.30 [29%] | 0.00 [0%] | 0.09 [1%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 2.91 | 0.16 | 0.93 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 205 | 2.30 | 0.15 | 0.17 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 2.32 | 0.16 | 0.46 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 1.93 | 0.16 | 0.18 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.97 | 0.08 | 0.00 | 0.75 | 0.00 | 0.00 |
| GPU≥50% | 205 | 0.64 | 0.09 | 0.00 | 0.57 | 0.00 | 0.00 |
| 10–50% | 64 | 0.74 | 0.06 | 0.00 | 0.63 | 0.00 | 0.00 |
| miss<10% | 164 | 1.37 | 0.20 | 0.00 | 0.59 | 0.00 | 0.02 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | hol:resv | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 1.49 | 0.04 | 0.58 | 0.00 | 0.00 | 0.00 | 1.55 | 0.00 | 0.00 |
| GPU≥50% | 205 | 0.74 | 0.07 | 0.06 | 0.00 | 0.00 | 0.00 | 1.18 | 0.00 | 0.01 |
| 10–50% | 64 | 1.20 | 0.11 | 0.50 | 0.00 | 0.00 | 0.00 | 1.11 | 0.00 | 0.02 |
| miss<10% | 164 | 2.93 | 0.09 | 0.46 | 0.01 | 0.20 | 0.00 | 3.30 | 0.00 | 0.07 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.26 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 205 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 64 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 164 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 1636 | 1625 / 0 / 11 | 128 | 1980 | 620 (149–1485) | 0 (600) |
| promotion after a load | 2 | 2 / 0 / 0 | 128 | 661 | 635 (634–635) | 0 (0) |

Requests refused at least once: 18 of 544; preemptions: 10; running requests that could not get their next chunk: 20.
Admitted external loads: 129; reservation passed at admission p50 0 / max 332 blocks; free blocks at admission p50 773.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.609 |
| time with free blocks < 50% of the pool | 0.660 |
| time with free blocks < 25% of the pool | 0.513 |
| time with free blocks < 10% of the pool | 0.291 |
| time with free blocks < 5% of the pool | 0.148 |
| blocks held by loads in transfer, mean / max | 32 / 2080 |
| in-flight prefill reservation after schedule(), mean / max | 245 / 2182 |
| steps whose running requests used the whole token budget (share of time) | 0.413 |
| running requests, mean / max | 6.3 / 16 |
| waiting + kv-holding requests, mean / max | 3.8 / 24 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 111 | 0.51 | 0.44 | 0.15 / 0.02 | 7.53 [54] | 11.74 [57] | 11.32 [34] | 9.48 [77] |
| GPU≥50% | 205 | 0.48 | 0.44 | 0.51 / 0.06 | 0.32 [107] | 7.83 [98] | 1.62 [128] | 7.52 [77] |
| 10–50% | 64 | 0.48 | 0.42 | 0.27 / 0.04 | 1.50 [33] | 6.63 [31] | 1.93 [36] | 15.36 [28] |
| miss<10% | 164 | 0.48 | 0.39 | 0.47 / 0.04 | 5.63 [86] | 17.25 [78] | 8.48 [100] | 19.82 [64] |
