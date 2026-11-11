## Admission analysis of `c5-skip8` (93 requests, 907 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 16640 | 1024 | 5.53 / 5.54 | 0.00 / 0.00 | 0.06 / 0.06 | 4.50 / 4.51 | 0.73 / 0.73 | 0.00 / 0.00 | 0.18 / 0.18 |
| miss<10% | 90 | 2304 | 128 | 6.14 / 10.90 | 0.41 / 0.44 | 1.00 / 1.11 | 2.59 / 3.47 | – | – | 0.88 / 0.88 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget_adm | other | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 5.29 | 0.03 [0%] | 0.18 [3%] | 0.18 [3%] | 3.72 [70%] | 1.19 [22%] |
| miss<10% | 90 | 5.02 | 2.20 [44%] | 0.00 [0%] | 0.31 [6%] | 0.43 [8%] | 2.09 [42%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget_adm | other | pending | slots |
|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 90 | 0.27 | 0.00 | 0.00 | 0.16 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | slots |
|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.06 | 0.00 | 0.00 |
| miss<10% | 90 | 0.37 | 0.31 | 0.00 | 0.44 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | slots |
|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 3.72 | 0.79 |
| miss<10% | 90 | 1.56 | 0.00 | 0.42 | 1.49 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | other | pending |
|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 |
| miss<10% | 90 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 93; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 19; reservation passed at admission p50 5 / max 40 blocks; free blocks at admission p50 2487.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.396 |
| time with free blocks < 50% of the pool | 0.323 |
| time with free blocks < 25% of the pool | 0.306 |
| time with free blocks < 10% of the pool | 0.205 |
| time with free blocks < 5% of the pool | 0.171 |
| blocks held by loads in transfer, mean / max | 35 / 6336 |
| in-flight prefill reservation after schedule(), mean / max | 344 / 1747 |
| steps whose running requests used the whole token budget (share of time) | 0.532 |
| running requests, mean / max | 5.1 / 16 |
| waiting + kv-holding requests, mean / max | 2.8 / 22 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 3 | 0.00 | 0.00 | 0.04 / 0.04 | 5.53 [3] | – | – | 5.53 [3] |
| miss<10% | 90 | 0.50 | 0.00 | 0.05 / 0.00 | 3.10 [45] | 6.56 [45] | – | 6.14 [90] |
