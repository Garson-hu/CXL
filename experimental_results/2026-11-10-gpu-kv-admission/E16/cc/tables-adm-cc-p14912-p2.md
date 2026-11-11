## Admission analysis of `cc-p14912-p2` (816 requests, 30426 engine steps, pool 14912 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 303 | 2048 | 128 | 0.68 / 2.09 | 0.00 / 0.03 | 0.02 / 0.18 | 0.00 / 0.00 | 0.38 / 0.38 | 0.00 / 0.01 | 0.17 / 0.14 |
| GPU≥50% | 92 | 4096 | 256 | 0.58 / 2.61 | 0.00 / 0.05 | 0.04 / 0.24 | 0.00 / 0.00 | 0.31 / 0.32 | 0.00 / 0.03 | 0.03 / 0.12 |
| miss<10% | 421 | 2048 | 128 | 1.42 / 7.79 | 0.00 / 0.03 | 0.02 / 0.17 | 0.00 / 0.96 | – | – | 0.66 / 0.86 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 303 | 0.60 | 0.04 [6%] | 0.12 [21%] | 0.20 [33%] | 0.21 [34%] | 0.00 [0%] | 0.03 [5%] |
| GPU≥50% | 92 | 0.65 | 0.03 [5%] | 0.10 [15%] | 0.16 [25%] | 0.24 [37%] | 0.00 [0%] | 0.11 [17%] |
| miss<10% | 421 | 1.16 | 0.00 [0%] | 0.31 [27%] | 0.00 [0%] | 0.12 [10%] | 0.54 [46%] | 0.20 [17%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 303 | 0.00 | 0.02 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 92 | 0.00 | 0.02 | 0.00 | 0.00 | 0.03 |
| miss<10% | 421 | 0.00 | 0.02 | 0.00 | 0.00 | 0.01 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok | slots |
|---|---|---|---|---|---|
| host≥50% | 303 | 0.04 | 0.14 | 0.00 | 0.01 |
| GPU≥50% | 92 | 0.04 | 0.17 | 0.00 | 0.03 |
| miss<10% | 421 | 0.04 | 0.12 | 0.00 | 0.01 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok | slots |
|---|---|---|---|---|---|
| host≥50% | 303 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 92 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 421 | 0.25 | 0.00 | 0.53 | 0.17 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 303 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 |
| GPU≥50% | 92 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| miss<10% | 421 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 727; reservation passed at admission p50 0 / max 388 blocks; free blocks at admission p50 14911.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.059 |
| time with free blocks < 50% of the pool | 0.000 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 69 / 2624 |
| in-flight prefill reservation after schedule(), mean / max | 57 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.148 |
| steps with a shortened token budget (share of time) | 0.096 |
| running requests, mean / max | 2.5 / 16 |
| waiting + kv-holding requests, mean / max | 0.9 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 303 | 0.26 | 0.00 | 0.98 / 0.79 | 0.42 [223] | 1.40 [80] | 0.68 [303] | – |
| GPU≥50% | 92 | 0.42 | 0.00 | 0.95 / 0.72 | 0.20 [53] | 1.39 [39] | 0.58 [92] | – |
| miss<10% | 421 | 0.37 | 0.00 | 0.99 / 0.79 | 0.72 [267] | 1.99 [154] | 1.42 [421] | – |
