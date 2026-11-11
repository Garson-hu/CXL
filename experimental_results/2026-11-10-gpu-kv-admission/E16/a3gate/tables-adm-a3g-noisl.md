## Admission analysis of `a3g-noisl` (172 requests, 14873 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 80 | 2304 | 128 | 1.36 / 3.36 | 0.00 / 0.00 | 0.05 / 0.33 | 0.00 / 0.61 | 0.13 / 0.38 | 0.00 / 0.00 | 0.15 / 0.17 |
| miss<10% | 92 | 4352 | 128 | 1.84 / 3.68 | 0.00 / 0.00 | 0.05 / 0.27 | 0.00 / 0.25 | – | – | 0.97 / 1.38 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:free | other | own:free | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 80 | 1.32 | 0.16 [12%] | 0.07 [5%] | 0.20 [15%] | 0.11 [9%] | 0.61 [46%] | 0.17 [13%] | 0.00 [0%] |
| miss<10% | 92 | 0.52 | 0.05 [10%] | 0.04 [7%] | 0.10 [20%] | 0.00 [0%] | 0.25 [48%] | 0.08 [15%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 80 | 0.00 | 0.00 |
| miss<10% | 92 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:free | own:free | pending |
|---|---|---|---|---|---|---|
| host≥50% | 80 | 0.09 | 0.05 | 0.12 | 0.00 | 0.08 |
| miss<10% | 92 | 0.05 | 0.04 | 0.10 | 0.00 | 0.08 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:free | pending |
|---|---|---|---|
| host≥50% | 80 | 0.61 | 0.00 |
| miss<10% | 92 | 0.25 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:free | other | pending | preempt |
|---|---|---|---|---|---|---|---|
| host≥50% | 80 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 92 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 1676 | 0 / 1676 / 0 | 256 | 272 | 158 (69–315) | 0 (32) |
| compute, no computed tokens (miss / GPU-prefix hit) | 1953 | 0 / 1953 / 0 | 255 | 272 | 150 (38–328) | 0 (0) |

Requests refused at least once: 64 of 172; preemptions: 23; running requests that could not get their next chunk: 46.
Admitted external loads: 390; reservation passed at admission p50 0 / max 90 blocks; free blocks at admission p50 3806.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.714 |
| time with free blocks < 50% of the pool | 0.725 |
| time with free blocks < 25% of the pool | 0.716 |
| time with free blocks < 10% of the pool | 0.539 |
| time with free blocks < 5% of the pool | 0.396 |
| blocks held by loads in transfer, mean / max | 63 / 7232 |
| in-flight prefill reservation after schedule(), mean / max | 103 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.205 |
| running requests, mean / max | 4.0 / 13 |
| waiting + kv-holding requests, mean / max | 0.3 / 11 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 80 | 0.00 | 0.00 | 0.06 / 0.02 | 1.36 [80] | – | 1.78 [6] | 1.26 [74] |
| miss<10% | 92 | 0.00 | 0.00 | 0.08 / 0.02 | 1.84 [92] | – | 1.64 [6] | 1.87 [86] |
