## Admission analysis of `cc-p14912-tokfast` (816 requests, 31449 engine steps, pool 14912 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 4096 | 128 | 0.69 / 2.27 | 0.00 / 0.04 | 0.02 / 0.20 | 0.00 / 0.00 | 0.37 / 0.36 | 0.00 / 0.02 | 0.04 / 0.13 |
| miss<10% | 421 | 2048 | 128 | 1.42 / 7.78 | 0.00 / 0.03 | 0.02 / 0.18 | 0.00 / 0.95 | – | – | 0.66 / 0.86 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | other | pending | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.62 | 0.03 [6%] | 0.13 [21%] | 0.19 [31%] | 0.21 [34%] | 0.00 [0%] | 0.05 [8%] |
| miss<10% | 421 | 1.16 | 0.00 [0%] | 0.33 [28%] | 0.00 [0%] | 0.11 [9%] | 0.52 [45%] | 0.20 [17%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.00 | 0.02 | 0.00 | 0.00 | 0.01 |
| miss<10% | 421 | 0.00 | 0.02 | 0.00 | 0.00 | 0.01 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok | slots |
|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.05 | 0.14 | 0.00 | 0.01 |
| miss<10% | 421 | 0.06 | 0.11 | 0.00 | 0.01 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:tok | slots |
|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 421 | 0.25 | 0.00 | 0.52 | 0.17 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 |
| miss<10% | 421 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|

Requests refused at least once: 0 of 816; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 795; reservation passed at admission p50 0 / max 388 blocks; free blocks at admission p50 14911.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.062 |
| time with free blocks < 50% of the pool | 0.000 |
| time with free blocks < 25% of the pool | 0.000 |
| time with free blocks < 10% of the pool | 0.000 |
| time with free blocks < 5% of the pool | 0.000 |
| blocks held by loads in transfer, mean / max | 78 / 2624 |
| in-flight prefill reservation after schedule(), mean / max | 41 / 448 |
| steps whose running requests used the whole token budget (share of time) | 0.093 |
| steps with a shortened token budget (share of time) | 0.107 |
| running requests, mean / max | 2.6 / 16 |
| waiting + kv-holding requests, mean / max | 1.0 / 25 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| GPU≥50% | 395 | 0.32 | 0.00 | 0.97 / 0.77 | 0.35 [269] | 1.40 [126] | 0.69 [395] | – |
| miss<10% | 421 | 0.39 | 0.00 | 0.99 / 0.77 | 0.68 [255] | 1.91 [166] | 1.42 [421] | – |
