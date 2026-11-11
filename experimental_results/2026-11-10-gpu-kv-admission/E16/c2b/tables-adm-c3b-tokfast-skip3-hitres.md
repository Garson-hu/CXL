## Admission analysis of `c3b-tokfast-skip3-hitres` (15 requests, 1079 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 9 | 2304 | 128 | 0.75 / 0.82 | 0.00 / 0.00 | 0.05 / 0.05 | 0.00 / 0.00 | 0.13 / 0.24 | 0.00 / 0.00 | 0.29 / 0.33 |
| miss<10% | 6 | 16640 | 128 | 7.96 / 7.97 | 0.00 / 0.00 | 3.06 / 1.55 | 0.97 / 0.49 | – | – | 3.90 / 2.24 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget_adm | other | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 9 | 0.29 | 0.02 [6%] | 0.20 [68%] | 0.00 [0%] | 0.07 [26%] |
| miss<10% | 6 | 2.04 | 0.00 [0%] | 0.00 [0%] | 0.49 [24%] | 1.55 [76%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 9 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 9 | 0.00 | 0.05 |
| miss<10% | 6 | 0.00 | 1.55 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 9 | 0.00 | 0.00 |
| miss<10% | 6 | 0.49 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | other | pending |
|---|---|---|---|---|
| host≥50% | 9 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 120 | 120 / 0 / 0 | 128 | 1040 | 573 (567–579) | 0 (0) |

Requests refused at least once: 3 of 15; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 27; reservation passed at admission p50 0 / max 16 blocks; free blocks at admission p50 2910.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.356 |
| time with free blocks < 50% of the pool | 0.287 |
| time with free blocks < 25% of the pool | 0.287 |
| time with free blocks < 10% of the pool | 0.192 |
| time with free blocks < 5% of the pool | 0.035 |
| blocks held by loads in transfer, mean / max | 28 / 6816 |
| in-flight prefill reservation after schedule(), mean / max | 364 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.610 |
| running requests, mean / max | 2.4 / 10 |
| waiting + kv-holding requests, mean / max | 0.2 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 9 | 0.33 | 0.00 | 0.08 / 0.02 | 0.75 [6] | 0.82 [3] | – | 0.75 [9] |
| miss<10% | 6 | 0.50 | 0.00 | 0.08 / 0.06 | 7.97 [3] | 0.65 [3] | – | 7.96 [6] |
