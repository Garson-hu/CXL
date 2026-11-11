## Admission analysis of `e-pol2` (24 requests, 1887 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 8 | 4352 | 256 | 1.70 / 2.66 | 0.00 / 0.00 | 0.05 / 0.61 | 0.00 / 0.00 | 0.70 / 0.73 | 0.00 / 0.00 | 0.15 / 0.22 |
| miss<10% | 16 | 8448 | 128 | 1.94 / 3.32 | 0.00 / 0.00 | 0.05 / 0.59 | 0.00 / 0.00 | – | – | 1.85 / 1.56 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending |
|---|---|---|---|---|---|---|
| host≥50% | 8 | 1.35 | 0.40 [29%] | 0.02 [1%] | 0.24 [18%] | 0.70 [52%] |
| miss<10% | 16 | 0.59 | 0.00 [0%] | 0.01 [1%] | 0.00 [0%] | 0.58 [99%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 8 | 0.00 | 0.00 |
| miss<10% | 16 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending |
|---|---|---|---|
| host≥50% | 8 | 0.01 | 0.60 |
| miss<10% | 16 | 0.01 | 0.58 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| host≥50% | 8 | 0.00 |
| miss<10% | 16 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | other | pending |
|---|---|---|---|---|
| host≥50% | 8 | 0.00 | 0.00 | 0.00 |
| miss<10% | 16 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 24; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 16; reservation passed at admission p50 15 / max 272 blocks; free blocks at admission p50 4143.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.406 |
| time with free blocks < 50% of the pool | 0.331 |
| time with free blocks < 25% of the pool | 0.331 |
| time with free blocks < 10% of the pool | 0.244 |
| time with free blocks < 5% of the pool | 0.098 |
| blocks held by loads in transfer, mean / max | 34 / 6624 |
| in-flight prefill reservation after schedule(), mean / max | 265 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.470 |
| running requests, mean / max | 2.8 / 8 |
| waiting + kv-holding requests, mean / max | 0.2 / 6 |
