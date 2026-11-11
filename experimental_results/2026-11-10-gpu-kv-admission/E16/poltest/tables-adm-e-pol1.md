## Admission analysis of `e-pol1` (24 requests, 1800 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 8 | 4352 | 256 | 1.69 / 2.64 | 0.00 / 0.00 | 0.05 / 0.05 | 0.00 / 0.57 | 0.70 / 0.68 | 0.00 / 0.00 | 0.15 / 0.26 |
| miss<10% | 16 | 8448 | 128 | 1.92 / 3.30 | 0.00 / 0.00 | 0.05 / 0.25 | 0.00 / 0.34 | – | – | 1.85 / 1.56 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | own:resv | pending |
|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 8 | 1.30 | 0.40 [31%] | 0.02 [1%] | 0.03 [2%] | 0.16 [12%] | 0.37 [28%] | 0.20 [15%] | 0.13 [10%] |
| miss<10% | 16 | 0.59 | 0.00 [0%] | 0.01 [1%] | 0.00 [0%] | 0.00 [0%] | 0.34 [57%] | 0.00 [0%] | 0.24 [42%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 8 | 0.00 | 0.00 |
| miss<10% | 16 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | own:full | own:resv | pending |
|---|---|---|---|---|---|
| host≥50% | 8 | 0.01 | 0.00 | 0.00 | 0.04 |
| miss<10% | 16 | 0.01 | 0.00 | 0.00 | 0.24 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | own:full | own:resv | pending |
|---|---|---|---|---|
| host≥50% | 8 | 0.37 | 0.20 | 0.00 |
| miss<10% | 16 | 0.34 | 0.00 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | hol:full | other | pending |
|---|---|---|---|---|---|
| host≥50% | 8 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 16 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| external load (first admission) | 44 | 40 / 0 / 4 | 256 | 272 | 188 (182–206) | 0 (272) |
| compute, no computed tokens (miss / GPU-prefix hit) | 125 | 125 / 0 / 0 | 128 | 528 | 438 (182–445) | 0 (0) |

Requests refused at least once: 8 of 24; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 18; reservation passed at admission p50 15 / max 272 blocks; free blocks at admission p50 5231.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.408 |
| time with free blocks < 50% of the pool | 0.331 |
| time with free blocks < 25% of the pool | 0.331 |
| time with free blocks < 10% of the pool | 0.252 |
| time with free blocks < 5% of the pool | 0.098 |
| blocks held by loads in transfer, mean / max | 37 / 6624 |
| in-flight prefill reservation after schedule(), mean / max | 266 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.471 |
| running requests, mean / max | 2.8 / 8 |
| waiting + kv-holding requests, mean / max | 0.2 / 6 |
