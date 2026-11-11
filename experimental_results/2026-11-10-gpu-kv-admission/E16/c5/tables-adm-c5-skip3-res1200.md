## Admission analysis of `c5-skip3-res1200` (93 requests, 1137 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 16640 | 1024 | 4.55 / 4.57 | 0.00 / 0.00 | 0.06 / 0.06 | 2.49 / 2.49 | 1.56 / 1.56 | 0.00 / 0.00 | 0.40 / 0.40 |
| miss<10% | 90 | 2304 | 95 | 8.28 / 12.57 | 0.00 / 3.16 | 0.06 / 1.04 | 2.51 / 2.73 | – | – | 1.16 / 1.08 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 4.11 | 0.00 [0%] | 1.15 [28%] | 0.39 [10%] | 0.00 [0%] | 0.00 [0%] | 0.08 [2%] | 2.49 [61%] | 0.00 [0%] |
| miss<10% | 90 | 6.92 | 0.06 [1%] | 3.95 [57%] | 0.84 [12%] | 0.00 [0%] | 0.04 [1%] | 0.05 [1%] | 0.71 [10%] | 1.26 [18%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 1.86 | 0.43 | 0.00 | 0.00 | 0.87 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.06 | 0.00 | 0.00 |
| miss<10% | 90 | 0.06 | 0.83 | 0.05 | 0.00 | 0.09 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 2.49 | 0.00 |
| miss<10% | 90 | 1.27 | 0.41 | 0.04 | 0.00 | 0.71 | 0.30 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | hol:full | pending |
|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 |
| miss<10% | 90 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 12 | 12 / 0 / 0 | 112 | 144 | 84 (71–101) | 0 (0) |

Requests refused at least once: 6 of 93; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 19; reservation passed at admission p50 10 / max 40 blocks; free blocks at admission p50 2492.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.401 |
| time with free blocks < 50% of the pool | 0.339 |
| time with free blocks < 25% of the pool | 0.323 |
| time with free blocks < 10% of the pool | 0.145 |
| time with free blocks < 5% of the pool | 0.120 |
| blocks held by loads in transfer, mean / max | 47 / 6336 |
| in-flight prefill reservation after schedule(), mean / max | 340 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.526 |
| running requests, mean / max | 5.1 / 16 |
| waiting + kv-holding requests, mean / max | 3.6 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.04 / 0.04 | 4.55 [3] | – | – | 4.55 [3] |
| miss<10% | 90 | 0.30 | 0.00 | 0.04 / 0.01 | 6.83 [63] | 10.18 [27] | – | 8.28 [90] |
