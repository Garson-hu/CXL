## Admission analysis of `s4-p3728-base` (480 requests, 13405 engine steps, pool 3728 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 147 | 2048 | 128 | 0.11 / 19.45 | 0.00 / 1.30 | 0.02 / 1.77 | 0.00 / 0.06 | 0.05 / 0.22 | 0.00 / 0.05 | 0.02 / 0.08 |
| GPU≥50% | 68 | 2048 | 128 | 0.09 / 7.03 | 0.00 / 0.49 | 0.02 / 0.60 | 0.00 / 0.00 | 0.04 / 0.09 | 0.00 / 0.00 | 0.02 / 0.04 |
| miss<10% | 265 | 8192 | 128 | 1.42 / 38.33 | 0.00 / 2.41 | 0.17 / 5.93 | 0.00 / 0.10 | – | – | 1.40 / 1.01 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 147 | 3.39 | 2.21 [65%] | 0.27 [8%] | 0.59 [17%] | 0.04 [1%] | 0.06 [2%] | 0.22 [7%] |
| GPU≥50% | 68 | 1.19 | 0.73 [61%] | 0.05 [4%] | 0.28 [24%] | 0.02 [1%] | 0.00 [0%] | 0.11 [9%] |
| miss<10% | 265 | 8.44 | 5.76 [68%] | 0.78 [9%] | 1.48 [18%] | 0.00 [0%] | 0.10 [1%] | 0.32 [4%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 147 | 0.89 | 0.12 | 0.29 | 0.00 | 0.00 |
| GPU≥50% | 68 | 0.32 | 0.02 | 0.15 | 0.00 | 0.00 |
| miss<10% | 265 | 1.72 | 0.24 | 0.45 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 147 | 1.16 | 0.15 | 0.28 | 0.00 | 0.18 |
| GPU≥50% | 68 | 0.38 | 0.03 | 0.12 | 0.00 | 0.08 |
| miss<10% | 265 | 4.04 | 0.54 | 1.03 | 0.00 | 0.31 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 147 | 0.06 | 0.00 |
| GPU≥50% | 68 | 0.00 | 0.00 |
| miss<10% | 265 | 0.10 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 147 | 0.04 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 68 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 265 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 160 | 160 / 0 / 0 | 512 | 512 | 133 (131–137) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 304 | 304 / 0 / 0 | 128 | 512 | 133 (130–135) | 0 (0) |

Requests refused at least once: 92 of 480; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 295; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 3727.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.439 |
| time with free blocks < 50% of the pool | 0.418 |
| time with free blocks < 25% of the pool | 0.387 |
| time with free blocks < 10% of the pool | 0.230 |
| time with free blocks < 5% of the pool | 0.160 |
| blocks held by loads in transfer, mean / max | 55 / 1536 |
| in-flight prefill reservation after schedule(), mean / max | 74 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.395 |
| running requests, mean / max | 3.2 / 9 |
| waiting + kv-holding requests, mean / max | 6.1 / 32 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 147 | 0.25 | 0.17 | 0.96 / 0.07 | 0.07 [110] | 7.08 [37] | 0.07 [115] | 8.19 [32] |
| GPU≥50% | 68 | 0.19 | 0.07 | 0.97 / 0.07 | 0.04 [55] | 4.59 [13] | 0.04 [59] | 5.76 [9] |
| miss<10% | 265 | 0.35 | 0.25 | 0.86 / 0.04 | 0.38 [172] | 16.15 [93] | 0.37 [177] | 23.97 [88] |
