## Admission analysis of `a3g-base` (172 requests, 15242 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 80 | 2304 | 128 | 1.37 / 3.37 | 0.00 / 0.00 | 0.05 / 0.33 | 0.00 / 0.71 | 0.13 / 0.35 | 0.00 / 0.00 | 0.15 / 0.17 |
| miss<10% | 92 | 4352 | 128 | 1.83 / 4.07 | 0.00 / 0.00 | 0.05 / 0.26 | 0.00 / 0.67 | – | – | 0.96 / 1.03 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 80 | 1.39 | 0.13 [9%] | 0.08 [5%] | 0.22 [16%] | 0.11 [8%] | 0.71 [51%] | 0.15 [11%] |
| miss<10% | 92 | 0.93 | 0.05 [6%] | 0.04 [4%] | 0.10 [11%] | 0.00 [0%] | 0.67 [72%] | 0.06 [7%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 80 | 0.00 | 0.00 |
| miss<10% | 92 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 80 | 0.09 | 0.06 | 0.13 | 0.00 | 0.06 |
| miss<10% | 92 | 0.05 | 0.04 | 0.10 | 0.00 | 0.06 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 80 | 0.71 | 0.00 |
| miss<10% | 92 | 0.67 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 80 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 92 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 2024 | 2024 / 0 / 0 | 256 | 272 | 147 (39–309) | 0 (32) |
| compute, no computed tokens (miss / GPU-prefix hit) | 2164 | 2164 / 0 / 0 | 128 | 272 | 148 (39–322) | 0 (0) |

Requests refused at least once: 66 of 172; preemptions: 2; running requests that could not get their next chunk: 4.
Admitted external loads: 393; reservation passed at admission p50 0 / max 90 blocks; free blocks at admission p50 3800.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.715 |
| time with free blocks < 50% of the pool | 0.729 |
| time with free blocks < 25% of the pool | 0.721 |
| time with free blocks < 10% of the pool | 0.532 |
| time with free blocks < 5% of the pool | 0.385 |
| blocks held by loads in transfer, mean / max | 63 / 7232 |
| in-flight prefill reservation after schedule(), mean / max | 99 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.213 |
| running requests, mean / max | 4.0 / 13 |
| waiting + kv-holding requests, mean / max | 0.4 / 11 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 80 | 0.00 | 0.00 | 0.06 / 0.02 | 1.37 [80] | – | 1.78 [6] | 1.26 [74] |
| miss<10% | 92 | 0.00 | 0.00 | 0.08 / 0.02 | 1.83 [92] | – | 1.64 [6] | 1.87 [86] |
