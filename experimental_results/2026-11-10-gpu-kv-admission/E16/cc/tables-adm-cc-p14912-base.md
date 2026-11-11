## Admission analysis of `cc-p14912-base` (816 requests, 30567 engine steps, pool 14912 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 4096 | 128 | 0.93 / 7.36 | 0.00 / 0.24 | 0.03 / 0.78 | 0.00 / 0.00 | 0.35 / 0.54 | 0.00 / 0.11 | 0.03 / 0.19 |
| miss<10% | 421 | 2048 | 128 | 1.35 / 6.47 | 0.00 / 0.24 | 0.02 / 0.71 | 0.00 / 0.00 | – | – | 0.65 / 0.79 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 1.66 | 0.86 [52%] | 0.26 [16%] | 0.13 [8%] | 0.24 [15%] | 0.16 [10%] |
| miss<10% | 421 | 0.95 | 0.49 [51%] | 0.20 [22%] | 0.00 [0%] | 0.13 [14%] | 0.12 [13%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.11 | 0.04 | 0.00 | 0.00 | 0.08 |
| miss<10% | 421 | 0.11 | 0.05 | 0.00 | 0.00 | 0.09 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | slots |
|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.41 | 0.16 | 0.15 | 0.05 |
| miss<10% | 421 | 0.38 | 0.16 | 0.13 | 0.04 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | pending |
|---|---|---|
| GPU≥50% | 395 | 0.00 |
| miss<10% | 421 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.10 | 0.00 | 0.00 | 0.00 | 0.01 |
| miss<10% | 421 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 728; reservation passed at admission p50 0 / max 0 blocks; free blocks at admission p50 14911.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.057 |
| time with free blocks < 50% of the pool | 0.000 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 103 / 1856 |
| in-flight prefill reservation after schedule(), mean / max | 43 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.238 |
| running requests, mean / max | 2.1 / 16 |
| waiting + kv-holding requests, mean / max | 1.3 / 29 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.26 | 0.11 | 0.98 / 0.78 | 0.41 [294] | 3.08 [101] | 0.93 [395] | – |
| miss<10% | 421 | 0.32 | 0.09 | 0.99 / 0.78 | 0.71 [288] | 1.70 [133] | 1.35 [421] | – |
