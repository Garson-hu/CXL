## Admission analysis of `s4-p7456-base` (480 requests, 12831 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 2048 | 128 | 0.10 / 21.00 | 0.00 / 1.15 | 0.02 / 2.07 | 0.00 / 0.01 | 0.05 / 0.44 | 0.00 / 0.12 | 0.02 / 0.14 |
| GPU≥50% | 83 | 8192 | 128 | 0.09 / 10.77 | 0.00 / 0.32 | 0.02 / 1.09 | 0.00 / 0.00 | 0.05 / 0.25 | 0.00 / 0.10 | 0.02 / 0.12 |
| miss<10% | 265 | 8192 | 124 | 1.42 / 39.42 | 0.00 / 2.29 | 0.18 / 6.03 | 0.00 / 0.01 | – | – | 1.40 / 1.21 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 3.80 | 2.65 [70%] | 0.63 [17%] | 0.11 [3%] | 0.05 [1%] | 0.01 [0%] | 0.32 [8%] | 0.03 [1%] |
| GPU≥50% | 83 | 1.76 | 1.20 [68%] | 0.18 [10%] | 0.05 [3%] | 0.03 [1%] | 0.00 [0%] | 0.20 [11%] | 0.11 [6%] |
| miss<10% | 265 | 8.34 | 5.98 [72%] | 1.88 [23%] | 0.09 [1%] | 0.00 [0%] | 0.01 [0%] | 0.35 [4%] | 0.03 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 0.87 | 0.27 | 0.01 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 83 | 0.23 | 0.02 | 0.01 | 0.00 | 0.00 | 0.05 |
| miss<10% | 265 | 1.72 | 0.55 | 0.00 | 0.00 | 0.00 | 0.01 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 1.42 | 0.32 | 0.09 | 0.00 | 0.22 | 0.02 |
| GPU≥50% | 83 | 0.74 | 0.13 | 0.03 | 0.00 | 0.14 | 0.05 |
| miss<10% | 265 | 4.26 | 1.33 | 0.08 | 0.00 | 0.35 | 0.02 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending | slots |
|---|---|---|---|---|
| host≥50% | 132 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 83 | 0.00 | 0.00 | 0.00 |
| miss<10% | 265 | 0.01 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 83 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| miss<10% | 265 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 13 | 13 / 0 / 0 | 512 | 512 | 269 (266–271) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 28 | 28 / 0 / 0 | 128 | 512 | 267 (255–269) | 0 (0) |

Requests refused at least once: 13 of 480; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 294; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 7455.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.329 |
| time with free blocks < 50% of the pool | 0.384 |
| time with free blocks < 25% of the pool | 0.178 |
| time with free blocks < 10% of the pool | 0.042 |
| time with free blocks < 5% of the pool | 0.017 |
| blocks held by loads in transfer, mean / max | 119 / 2560 |
| in-flight prefill reservation after schedule(), mean / max | 99 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.409 |
| running requests, mean / max | 4.8 / 16 |
| waiting + kv-holding requests, mean / max | 6.1 / 31 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 132 | 0.27 | 0.21 | 0.98 / 0.28 | 0.06 [96] | 9.66 [36] | 0.09 [119] | 13.35 [13] |
| GPU≥50% | 83 | 0.20 | 0.12 | 0.98 / 0.10 | 0.04 [66] | 6.92 [17] | 0.04 [72] | 10.70 [11] |
| miss<10% | 265 | 0.43 | 0.30 | 0.93 / 0.31 | 0.35 [151] | 18.16 [114] | 0.63 [240] | 12.40 [25] |
