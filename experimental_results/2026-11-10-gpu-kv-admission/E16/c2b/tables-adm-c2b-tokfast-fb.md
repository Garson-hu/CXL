## Admission analysis of `c2b-tokfast-fb` (18 requests, 1800 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 4352 | 256 | 2.69 / 4.54 | 0.00 / 0.49 | 0.59 / 0.48 | 1.61 / 1.23 | 0.22 / 0.32 | 0.00 / 0.00 | 0.16 / 0.20 |
| miss<10% | 6 | 16640 | 128 | 4.63 / 4.65 | 0.00 / 0.00 | 0.05 / 0.04 | 0.00 / 0.00 | – | – | 4.57 / 4.42 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | hol:full | other | own:full | pending | pol:blocks |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 2.52 | 0.16 [6%] | 0.49 [19%] | 0.10 [4%] | 0.57 [22%] | 0.54 [22%] | 0.66 [26%] |
| miss<10% | 6 | 0.05 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.05 [100%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | hol:full | other | pending |
|---|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.49 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | pending | pol:blocks |
|---|---|---|---|
| host≥50% | 12 | 0.48 | 0.00 |
| miss<10% | 6 | 0.04 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending | pol:blocks |
|---|---|---|---|---|
| host≥50% | 12 | 0.57 | 0.00 | 0.66 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 102 | 102 / 0 / 0 | 256 | 272 | 108 (104–135) | 0 (148) |

Requests refused at least once: 6 of 18; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 30; reservation passed at admission p50 16 / max 562 blocks; free blocks at admission p50 3295.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.454 |
| time with free blocks < 50% of the pool | 0.430 |
| time with free blocks < 25% of the pool | 0.429 |
| time with free blocks < 10% of the pool | 0.170 |
| time with free blocks < 5% of the pool | 0.091 |
| blocks held by loads in transfer, mean / max | 27 / 6240 |
| in-flight prefill reservation after schedule(), mean / max | 315 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.466 |
| steps with a shortened token budget (share of time) | 0.086 |
| running requests, mean / max | 3.1 / 8 |
| waiting + kv-holding requests, mean / max | 0.2 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 1.00 | 0.00 | 0.10 / 0.04 | – | 2.69 [12] | – | 2.69 [12] |
| miss<10% | 6 | 0.00 | 0.00 | 0.20 / 0.15 | 4.63 [6] | – | – | 4.63 [6] |
