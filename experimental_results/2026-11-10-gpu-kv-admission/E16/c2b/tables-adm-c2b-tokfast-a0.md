## Admission analysis of `c2b-tokfast-a0` (18 requests, 1642 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 4352 | 256 | 2.16 / 3.51 | 0.00 / 0.00 | 0.70 / 0.65 | 0.00 / 0.45 | 0.82 / 0.79 | 0.00 / 0.00 | 0.35 / 0.30 |
| miss<10% | 6 | 16640 | 128 | 4.91 / 4.92 | 0.00 / 0.00 | 0.05 / 0.04 | 0.00 / 0.00 | – | – | 4.84 / 4.76 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 1.89 | 0.43 [23%] | 0.01 [0%] | 0.33 [18%] | 0.12 [6%] | 0.10 [5%] | 0.88 [47%] | 0.02 [1%] |
| miss<10% | 6 | 0.05 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.05 [100%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.65 |
| miss<10% | 6 | 0.00 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|
| host≥50% | 12 | 0.01 | 0.33 | 0.10 | 0.00 | 0.01 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending | preempt |
|---|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 6 | 6 / 0 / 0 | 256 | 272 | 33 (32–33) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 111 | 111 / 0 / 0 | 236 | 273 | 109 (102–135) | 0 (0) |

Requests refused at least once: 9 of 18; preemptions: 6; running requests that could not get their next chunk: 12.
Admitted external loads: 30; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 3295.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.457 |
| time with free blocks < 50% of the pool | 0.430 |
| time with free blocks < 25% of the pool | 0.420 |
| time with free blocks < 10% of the pool | 0.190 |
| time with free blocks < 5% of the pool | 0.114 |
| blocks held by loads in transfer, mean / max | 36 / 6240 |
| in-flight prefill reservation after schedule(), mean / max | 323 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.492 |
| steps with a shortened token budget (share of time) | 0.119 |
| running requests, mean / max | 3.2 / 8 |
| waiting + kv-holding requests, mean / max | 0.2 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 1.00 | 0.00 | 0.10 / 0.02 | – | 2.16 [12] | – | 2.16 [12] |
| miss<10% | 6 | 0.00 | 0.00 | 0.20 / 0.15 | 4.91 [6] | – | – | 4.91 [6] |
