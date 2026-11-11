## Admission analysis of `c5-base` (93 requests, 1151 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 16640 | 1024 | 4.50 / 4.57 | 0.00 / 0.00 | 0.06 / 0.06 | 2.49 / 2.49 | 0.91 / 1.01 | 0.00 / 0.00 | 0.80 / 0.77 |
| miss<10% | 90 | 2304 | 111 | 8.25 / 12.63 | 2.07 / 3.67 | 2.85 / 3.34 | 0.00 / 0.04 | – | – | 1.08 / 1.02 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | slots |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 3.55 | 0.00 [0%] | 0.73 [20%] | 0.00 [0%] | 0.26 [7%] | 2.49 [70%] | 0.08 [2%] | 0.00 [0%] |
| miss<10% | 90 | 7.05 | 0.02 [0%] | 3.65 [52%] | 1.52 [22%] | 0.00 [0%] | 0.04 [1%] | 0.28 [4%] | 1.54 [22%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 1.68 | 1.07 | 0.00 | 0.00 | 0.92 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.06 | 0.00 |
| miss<10% | 90 | 0.02 | 1.97 | 0.45 | 0.00 | 0.28 | 0.62 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 3 | 2.49 | 0.00 |
| miss<10% | 90 | 0.04 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | pending |
|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 |
| miss<10% | 90 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 267 | 267 / 0 / 0 | 1024 | 1040 | 995 (313–1016) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 12 | 12 / 0 / 0 | 128 | 144 | 83 (70–85) | 0 (0) |

Requests refused at least once: 9 of 93; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 19; reservation passed at admission p50 10 / max 40 blocks; free blocks at admission p50 2521.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.402 |
| time with free blocks < 50% of the pool | 0.341 |
| time with free blocks < 25% of the pool | 0.325 |
| time with free blocks < 10% of the pool | 0.135 |
| time with free blocks < 5% of the pool | 0.108 |
| blocks held by loads in transfer, mean / max | 37 / 6336 |
| in-flight prefill reservation after schedule(), mean / max | 337 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.520 |
| running requests, mean / max | 5.1 / 16 |
| waiting + kv-holding requests, mean / max | 3.7 / 26 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.04 / 0.04 | 4.50 [3] | – | – | 4.50 [3] |
| miss<10% | 90 | 0.20 | 0.00 | 0.04 / 0.01 | 7.21 [72] | 9.89 [18] | – | 8.25 [90] |
