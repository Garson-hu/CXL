## Admission analysis of `s4-p7456-p2` (480 requests, 13013 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 131 | 2048 | 128 | 0.10 / 2.06 | 0.00 / 0.02 | 0.02 / 0.14 | 0.00 / 0.00 | 0.05 / 0.25 | 0.00 / 0.00 | 0.02 / 0.10 |
| GPU≥50% | 86 | 8192 | 128 | 0.09 / 2.26 | 0.00 / 0.04 | 0.02 / 0.13 | 0.00 / 0.04 | 0.05 / 0.19 | 0.00 / 0.00 | 0.02 / 0.09 |
| miss<10% | 263 | 8192 | 97 | 1.42 / 39.82 | 0.00 / 0.03 | 0.20 / 0.23 | 0.00 / 8.57 | – | – | 1.40 / 1.26 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 131 | 0.41 | 0.00 [1%] | 0.05 [12%] | 0.04 [9%] | 0.14 [34%] | 0.00 [0%] | 0.17 [42%] | 0.00 [0%] | 0.00 [0%] | 0.01 [1%] |
| GPU≥50% | 86 | 0.41 | 0.00 [0%] | 0.06 [16%] | 0.04 [10%] | 0.11 [27%] | 0.00 [0%] | 0.15 [37%] | 0.00 [0%] | 0.03 [6%] | 0.02 [4%] |
| miss<10% | 263 | 8.83 | 0.00 [0%] | 2.02 [23%] | 0.07 [1%] | 0.00 [0%] | 0.01 [0%] | 0.19 [2%] | 0.00 [0%] | 6.51 [74%] | 0.02 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 131 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 86 | 0.00 | 0.02 | 0.01 | 0.00 | 0.00 | 0.01 |
| miss<10% | 263 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | pending | pol:blocks | pol:tok | slots |
|---|---|---|---|---|---|---|---|
| host≥50% | 131 | 0.02 | 0.00 | 0.12 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 86 | 0.01 | 0.01 | 0.11 | 0.00 | 0.00 | 0.00 |
| miss<10% | 263 | 0.03 | 0.01 | 0.19 | 0.00 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:tok | slots |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 131 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 86 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 |
| miss<10% | 263 | 1.97 | 0.06 | 0.01 | 0.00 | 0.00 | 6.51 | 0.02 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 131 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 86 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 263 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 20 | 20 / 0 / 0 | 1 | 512 | 346 (264–475) | 0 (0) |

Requests refused at least once: 5 of 480; preemptions: 0; running requests that could not get their next chunk: 0.
Admitted external loads: 296; reservation passed at admission p50 0 / max 392 blocks; free blocks at admission p50 7455.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.290 |
| time with free blocks < 50% of the pool | 0.328 |
| time with free blocks < 25% of the pool | 0.048 |
| time with free blocks < 10% of the pool | 0.022 |
| time with free blocks < 5% of the pool | 0.007 |
| blocks held by loads in transfer, mean / max | 59 / 2560 |
| in-flight prefill reservation after schedule(), mean / max | 121 / 892 |
| steps whose running requests used the whole token budget (share of time) | 0.109 |
| steps with a shortened token budget (share of time) | 0.120 |
| running requests, mean / max | 4.4 / 16 |
| waiting + kv-holding requests, mean / max | 5.2 / 32 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 131 | 0.30 | 0.00 | 0.98 / 0.23 | 0.06 [92] | 1.59 [39] | 0.09 [117] | 1.85 [14] |
| GPU≥50% | 86 | 0.30 | 0.00 | 0.98 / 0.20 | 0.04 [60] | 1.61 [26] | 0.04 [74] | 2.16 [12] |
| miss<10% | 263 | 0.48 | 0.00 | 0.93 / 0.32 | 0.34 [137] | 18.71 [126] | 0.62 [240] | 14.08 [23] |
