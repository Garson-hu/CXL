## Admission analysis of `c2b-tokfast-out512` (18 requests, 4527 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 4352 | 256 | 5.98 / 7.83 | 0.00 / 1.32 | 0.59 / 0.48 | 0.00 / 1.65 | 0.76 / 0.48 | 0.00 / 0.00 | 0.16 / 0.19 |
| miss<10% | 6 | 16640 | 128 | 4.48 / 4.49 | 0.00 / 0.00 | 0.05 / 0.04 | 0.00 / 0.00 | – | – | 4.41 / 4.34 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | hol:full | hol:resv | other | own:full | own:resv | pending |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 3.92 | 0.20 [5%] | 1.32 [34%] | 0.00 [0%] | 0.18 [5%] | 1.32 [34%] | 0.33 [9%] | 0.58 [15%] |
| miss<10% | 6 | 0.05 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.05 [100%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 1.32 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | own:resv | pending |
|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.48 |
| miss<10% | 6 | 0.00 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | own:resv | pending |
|---|---|---|---|---|
| host≥50% | 12 | 1.32 | 0.33 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 474 | 462 / 0 / 12 | 256 | 272 | 80 (52–108) | 0 (562) |

Requests refused at least once: 3 of 18; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 33; reservation passed at admission p50 16 / max 562 blocks; free blocks at admission p50 3295.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.567 |
| time with free blocks < 50% of the pool | 0.605 |
| time with free blocks < 25% of the pool | 0.535 |
| time with free blocks < 10% of the pool | 0.232 |
| time with free blocks < 5% of the pool | 0.082 |
| blocks held by loads in transfer, mean / max | 24 / 6240 |
| in-flight prefill reservation after schedule(), mean / max | 217 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.331 |
| steps with a shortened token budget (share of time) | 0.061 |
| running requests, mean / max | 4.5 / 8 |
| waiting + kv-holding requests, mean / max | 0.2 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 1.00 | 0.00 | 0.17 / 0.04 | – | 5.98 [12] | 1.98 [3] | 5.98 [9] |
| miss<10% | 6 | 0.00 | 0.00 | 0.33 / 0.15 | 4.48 [6] | – | 4.49 [3] | 4.34 [3] |
