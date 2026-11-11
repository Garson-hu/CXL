## Admission analysis of `c2-tokfast-a0-out512` (18 requests, 4828 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 4352 | 256 | 6.27 / 6.54 | 0.00 / 0.00 | 0.59 / 0.48 | 0.00 / 1.26 | 0.85 / 0.86 | 0.00 / 0.00 | 0.54 / 1.51 |
| miss<10% | 6 | 16640 | 128 | 5.11 / 5.12 | 0.00 / 0.00 | 0.05 / 0.04 | 0.00 / 0.00 | – | – | 5.04 / 4.90 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | preempt |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 2.60 | 0.53 [20%] | 0.01 [0%] | 1.01 [39%] | 0.10 [4%] | 0.23 [9%] | 0.71 [27%] | 0.01 [0%] |
| miss<10% | 6 | 0.04 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.04 [100%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.48 |
| miss<10% | 6 | 0.00 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | preempt |
|---|---|---|---|---|---|---|
| host≥50% | 12 | 0.01 | 1.01 | 0.23 | 0.00 | 0.01 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 9 | 9 / 0 / 0 | 256 | 272 | 3 (2–130) | 0 (0) |
| compute, no computed tokens (miss / GPU-prefix hit) | 758 | 758 / 0 / 0 | 218 | 273 | 90 (61–120) | 0 (0) |

Requests refused at least once: 9 of 18; preemptions: 6; running requests that could not get their next chunk: 12.
Admitted external loads: 33; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 2475.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.616 |
| time with free blocks < 50% of the pool | 0.631 |
| time with free blocks < 25% of the pool | 0.567 |
| time with free blocks < 10% of the pool | 0.402 |
| time with free blocks < 5% of the pool | 0.151 |
| blocks held by loads in transfer, mean / max | 27 / 6240 |
| in-flight prefill reservation after schedule(), mean / max | 212 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.323 |
| steps with a shortened token budget (share of time) | 0.078 |
| running requests, mean / max | 4.8 / 9 |
| waiting + kv-holding requests, mean / max | 0.3 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 1.00 | 0.00 | 0.10 / 0.03 | – | 6.27 [12] | – | 6.27 [12] |
| miss<10% | 6 | 0.00 | 0.00 | 0.20 / 0.15 | 5.11 [6] | – | – | 5.11 [6] |
