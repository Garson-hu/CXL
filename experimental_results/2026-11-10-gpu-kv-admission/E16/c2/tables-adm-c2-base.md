## Admission analysis of `c2-base` (18 requests, 1875 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 4352 | 256 | 3.78 / 4.22 | 2.41 / 1.48 | 0.73 / 0.84 | 0.42 / 0.24 | 0.12 / 0.13 | 0.00 / 0.00 | 0.16 / 0.17 |
| miss<10% | 6 | 16640 | 128 | 4.03 / 4.04 | 0.00 / 0.00 | 0.05 / 0.05 | 0.00 / 0.00 | – | – | 3.96 / 3.95 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | hol:full | other | own:full | pending |
|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 2.68 | 1.48 [55%] | 0.13 [5%] | 0.08 [3%] | 0.24 [9%] | 0.75 [28%] |
| miss<10% | 6 | 0.05 | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.05 [100%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 12 | 1.48 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | hol:full | own:full | pending |
|---|---|---|---|---|
| host≥50% | 12 | 0.10 | 0.00 | 0.73 |
| miss<10% | 6 | 0.00 | 0.00 | 0.05 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | pending |
|---|---|---|---|
| host≥50% | 12 | 0.24 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | hol:full | other | pending |
|---|---|---|---|---|
| host≥50% | 12 | 0.00 | 0.00 | 0.00 |
| miss<10% | 6 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 102 | 102 / 0 / 0 | 256 | 272 | 133 (107–152) | 0 (16) |

Requests refused at least once: 6 of 18; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 30; reservation passed at admission p50 12 / max 30 blocks; free blocks at admission p50 3295.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.450 |
| time with free blocks < 50% of the pool | 0.429 |
| time with free blocks < 25% of the pool | 0.420 |
| time with free blocks < 10% of the pool | 0.148 |
| time with free blocks < 5% of the pool | 0.057 |
| blocks held by loads in transfer, mean / max | 22 / 6240 |
| in-flight prefill reservation after schedule(), mean / max | 299 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.549 |
| running requests, mean / max | 3.1 / 8 |
| waiting + kv-holding requests, mean / max | 0.2 / 6 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 12 | 1.00 | 1.00 | 0.10 / 0.04 | – | 3.78 [12] | – | 3.78 [12] |
| miss<10% | 6 | 0.00 | 0.00 | 0.20 / 0.15 | 4.03 [6] | – | – | 4.03 [6] |
