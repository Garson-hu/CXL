## Admission analysis of `c2-tokfast-out512` (18 requests, 4899 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 4352 | 256 | 5.98 / 7.84 | 0.00 / 1.32 | 0.59 / 0.40 | 5.08 / 2.92 | 0.22 / 0.32 | 0.00 / 0.00 | 0.16 / 0.25 |
| miss<10% | 6 | 16640 | 128 | 4.72 / 4.72 | 0.00 / 0.00 | 0.05 / 0.04 | 0.00 / 0.00 | – | – | 4.66 / 4.53 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | hol:full | hol:resv | other | own:full | own:resv | pending |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 4.96 | 0.16 [3%] | 1.32 [27%] | 0.00 [0%] | 0.10 [2%] | 2.49 [50%] | 0.43 [9%] | 0.46 [9%] |
| miss<10% | 6 | 0.04 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.04 [100%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | hol:full | hol:resv | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 1.32 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | own:resv | pending |
|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.40 |
| miss<10% | 6 | 0.00 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | own:resv | pending |
|---|---|---|---|---|
| host≥50% | 12 | 2.49 | 0.43 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 883 | 865 / 0 / 18 | 256 | 272 | 90 (59–127) | 0 (562) |

Requests refused at least once: 6 of 18; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 33; reservation passed at admission p50 12 / max 562 blocks; free blocks at admission p50 2472.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.610 |
| time with free blocks < 50% of the pool | 0.626 |
| time with free blocks < 25% of the pool | 0.555 |
| time with free blocks < 10% of the pool | 0.394 |
| time with free blocks < 5% of the pool | 0.144 |
| blocks held by loads in transfer, mean / max | 22 / 6240 |
| in-flight prefill reservation after schedule(), mean / max | 207 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.305 |
| steps with a shortened token budget (share of time) | 0.059 |
| running requests, mean / max | 4.8 / 8 |
| waiting + kv-holding requests, mean / max | 0.3 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 1.00 | 0.00 | 0.10 / 0.04 | – | 5.98 [12] | – | 5.98 [12] |
| miss<10% | 6 | 0.00 | 0.00 | 0.20 / 0.15 | 4.72 [6] | – | – | 4.72 [6] |
