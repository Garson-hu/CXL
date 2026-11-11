## Admission analysis of `ccb-p3728-base` (816 requests, 28114 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 359 | 2048 | 128 | 1.03 / 6.89 | 0.00 / 0.18 | 0.03 / 0.89 | 0.00 / 0.02 | 0.35 / 0.51 | 0.00 / 0.10 | 0.03 / 0.19 |
| GPU≥50% | 39 | 8192 | 256 | 0.61 / 9.59 | 0.00 / 0.25 | 0.03 / 0.97 | 0.00 / 0.00 | 0.22 / 0.42 | 0.00 / 0.08 | 0.03 / 0.17 |
| miss<10% | 418 | 2048 | 128 | 1.38 / 6.79 | 0.00 / 0.20 | 0.02 / 0.80 | 0.00 / 0.02 | – | – | 0.66 / 0.79 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 359 | 1.68 | 0.85 [51%] | 0.20 [12%] | 0.20 [12%] | 0.13 [8%] | 0.01 [1%] | 0.29 [17%] | 0.00 [0%] |
| GPU≥50% | 39 | 1.72 | 0.85 [49%] | 0.19 [11%] | 0.32 [18%] | 0.09 [5%] | 0.00 [0%] | 0.28 [16%] | 0.00 [0%] |
| miss<10% | 418 | 1.01 | 0.50 [49%] | 0.15 [15%] | 0.18 [17%] | 0.00 [0%] | 0.02 [2%] | 0.16 [16%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 359 | 0.12 | 0.02 | 0.04 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 39 | 0.12 | 0.04 | 0.09 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.11 | 0.03 | 0.05 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 359 | 0.43 | 0.13 | 0.13 | 0.00 | 0.19 | 0.00 |
| GPU≥50% | 39 | 0.48 | 0.12 | 0.19 | 0.00 | 0.18 | 0.00 |
| miss<10% | 418 | 0.39 | 0.13 | 0.12 | 0.00 | 0.16 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|
| host≥50% | 359 | 0.00 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 39 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.02 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 359 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 39 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 418 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 71 | 71 / 0 / 0 | 512 | 512 | 190 (3–508) | 0 (128) |
| compute, no computed tokens (miss / GPU-prefix hit) | 185 | 185 / 0 / 0 | 128 | 257 | 118 (3–376) | 0 (0) |

Requests refused at least once: 45 of 816; preemptions: 8; running requests that could not get their next chunk: 19.
Admitted external loads: 565; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.218 |
| time with free blocks < 50% of the pool | 0.130 |
| time with free blocks < 25% of the pool | 0.084 |
| time with free blocks < 10% of the pool | 0.039 |
| time with free blocks < 5% of the pool | 0.021 |
| blocks held by loads in transfer, mean / max | 98 / 1664 |
| in-flight prefill reservation after schedule(), mean / max | 36 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.227 |
| running requests, mean / max | 2.1 / 16 |
| waiting + kv-holding requests, mean / max | 1.4 / 31 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 359 | 0.27 | 0.13 | 0.91 / 0.14 | 0.44 [262] | 2.93 [97] | 0.69 [306] | 4.39 [53] |
| GPU≥50% | 39 | 0.31 | 0.05 | 0.83 / 0.13 | 0.24 [27] | 2.66 [12] | 0.30 [32] | 2.66 [7] |
| miss<10% | 418 | 0.37 | 0.09 | 0.97 / 0.15 | 0.69 [262] | 1.67 [156] | 1.00 [358] | 4.19 [60] |
