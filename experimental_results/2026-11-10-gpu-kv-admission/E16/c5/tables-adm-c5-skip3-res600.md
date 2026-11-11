## Admission analysis of `c5-skip3-res600` (93 requests, 1036 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 16640 | 1024 | 4.86 / 5.19 | 0.00 / 0.00 | 0.06 / 0.06 | 2.82 / 2.95 | 1.44 / 1.34 | 0.00 / 0.00 | 0.42 / 0.42 |
| miss<10% | 90 | 2304 | 112 | 7.48 / 11.72 | 0.00 / 0.97 | 0.57 / 3.20 | 0.96 / 1.88 | – | – | 0.95 / 0.92 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget_adm | hol:full | other | own:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 4.35 | 0.39 [9%] | 0.25 [6%] | 0.40 [9%] | 0.00 [0%] | 0.36 [8%] | 2.95 [68%] | 0.00 [0%] |
| miss<10% | 90 | 6.05 | 2.94 [49%] | 0.67 [11%] | 0.00 [0%] | 0.04 [1%] | 0.42 [7%] | 0.59 [10%] | 1.40 [23%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 0.56 | 0.16 | 0.00 | 0.00 | 0.25 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.06 | 0.00 | 0.00 |
| miss<10% | 90 | 1.49 | 0.35 | 0.42 | 0.00 | 0.94 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 2.95 | 0.00 |
| miss<10% | 90 | 0.89 | 0.15 | 0.04 | 0.00 | 0.59 | 0.21 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | hol:full | pending |
|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 |
| miss<10% | 90 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 13 | 13 / 0 / 0 | 111 | 144 | 89 (84–118) | 0 (0) |

Requests refused at least once: 10 of 93; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 19; reservation passed at admission p50 5 / max 40 blocks; free blocks at admission p50 2485.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.394 |
| time with free blocks < 50% of the pool | 0.325 |
| time with free blocks < 25% of the pool | 0.316 |
| time with free blocks < 10% of the pool | 0.169 |
| time with free blocks < 5% of the pool | 0.129 |
| blocks held by loads in transfer, mean / max | 45 / 6336 |
| in-flight prefill reservation after schedule(), mean / max | 339 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.525 |
| running requests, mean / max | 5.0 / 16 |
| waiting + kv-holding requests, mean / max | 3.2 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.04 / 0.04 | 4.86 [3] | – | – | 4.86 [3] |
| miss<10% | 90 | 0.40 | 0.00 | 0.04 / 0.02 | 4.92 [54] | 10.31 [36] | – | 7.48 [90] |
