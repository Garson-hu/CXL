## Admission analysis of `tool04-320-p4` (1159 requests, 87748 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 118 | 7002 | 384 | 0.66 / 10.55 | 0.00 / 0.01 | 0.03 / 0.28 | 0.00 / 0.60 | 0.12 / 0.38 | 0.00 / 0.00 | 0.22 / 0.48 |
| GPU≥50% | 610 | 6185 | 386 | 0.34 / 4.02 | 0.00 / 0.01 | 0.03 / 0.26 | 0.00 / 0.45 | 0.52 / 0.53 | 0.00 / 0.06 | 0.23 / 0.31 |
| 10–50% | 122 | 2496 | 106 | 0.78 / 13.84 | 0.00 / 0.01 | 0.03 / 0.25 | 0.00 / 1.73 | 0.11 / 0.40 | 0.00 / 0.00 | 0.61 / 1.16 |
| miss<10% | 293 | 13689 | 128 | 5.30 / 27.06 | 0.00 / 0.01 | 0.03 / 0.26 | 0.00 / 3.60 | 0.05 / 0.04 | 0.00 / 0.00 | 3.16 / 4.20 |
| mixed | 16 | 2590 | 64 | 1.75 / 15.51 | 0.00 / 0.00 | 0.47 / 0.33 | 0.00 / 1.50 | 0.54 / 0.58 | 0.00 / 0.00 | 0.57 / 0.61 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | pol:resv | pol:tok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 118 | 1.27 | 0.07 [5%] | 0.06 [5%] | 0.00 [0%] | 0.23 [18%] | 0.00 [0%] | 0.35 [28%] | 0.34 [27%] | 0.01 [1%] | 0.21 [17%] |
| GPU≥50% | 610 | 0.73 | 0.00 [0%] | 0.04 [6%] | 0.00 [0%] | 0.01 [1%] | 0.00 [0%] | 0.26 [35%] | 0.01 [1%] | 0.00 [0%] | 0.41 [56%] |
| 10–50% | 122 | 2.05 | 0.01 [0%] | 0.11 [6%] | 0.00 [0%] | 0.03 [1%] | 0.00 [0%] | 0.26 [13%] | 0.25 [12%] | 0.01 [1%] | 1.37 [67%] |
| miss<10% | 293 | 3.87 | 0.00 [0%] | 0.15 [4%] | 0.01 [0%] | 0.00 [0%] | 0.05 [1%] | 0.26 [7%] | 0.74 [19%] | 0.01 [0%] | 2.65 [69%] |
| mixed | 16 | 2.40 | 0.08 [3%] | 0.03 [1%] | 0.00 [0%] | 0.36 [15%] | 0.00 [0%] | 0.45 [19%] | 0.75 [31%] | 0.00 [0%] | 0.74 [31%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending |
|---|---|---|---|---|---|
| host≥50% | 118 | 0.00 | 0.01 | 0.00 | 0.00 |
| GPU≥50% | 610 | 0.00 | 0.01 | 0.00 | 0.00 |
| 10–50% | 122 | 0.00 | 0.01 | 0.00 | 0.00 |
| miss<10% | 293 | 0.00 | 0.01 | 0.00 | 0.00 |
| mixed | 16 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget_adm | pending | pol:blocks | pol:tok |
|---|---|---|---|---|---|
| host≥50% | 118 | 0.00 | 0.27 | 0.00 | 0.00 |
| GPU≥50% | 610 | 0.01 | 0.25 | 0.00 | 0.00 |
| 10–50% | 122 | 0.00 | 0.25 | 0.00 | 0.00 |
| miss<10% | 293 | 0.01 | 0.26 | 0.00 | 0.00 |
| mixed | 16 | 0.01 | 0.31 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget_adm | hol:full | own:full | pending | pol:blocks | pol:resv | pol:tok |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 118 | 0.04 | 0.00 | 0.00 | 0.00 | 0.34 | 0.01 | 0.21 |
| GPU≥50% | 610 | 0.03 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.41 |
| 10–50% | 122 | 0.10 | 0.00 | 0.00 | 0.00 | 0.25 | 0.01 | 1.37 |
| miss<10% | 293 | 0.14 | 0.01 | 0.05 | 0.00 | 0.74 | 0.01 | 2.65 |
| mixed | 16 | 0.00 | 0.00 | 0.00 | 0.00 | 0.75 | 0.00 | 0.74 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 118 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 610 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 122 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 293 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 16 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 748 | 748 / 0 / 0 | 128 | 1254 | 628 (462–1632) | 0 (0) |
| promotion after a load | 17 | 17 / 0 / 0 | 128 | 203 | 161 (157–165) | 0 (0) |

Requests refused at least once: 10 of 1159; preemptions: 3; running requests that could not get their next chunk: 6.
Admitted external loads: 167; reservation passed at admission p50 0 / max 1728 blocks; free blocks at admission p50 5986.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.261 |
| time with free blocks < 50% of the pool | 0.175 |
| time with free blocks < 25% of the pool | 0.094 |
| time with free blocks < 10% of the pool | 0.039 |
| time with free blocks < 5% of the pool | 0.016 |
| blocks held by loads in transfer, mean / max | 7 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 126 / 2770 |
| steps whose running requests used the whole token budget (share of time) | 0.081 |
| steps with a shortened token budget (share of time) | 0.079 |
| running requests, mean / max | 2.0 / 14 |
| waiting + kv-holding requests, mean / max | 0.4 / 9 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 118 | 0.43 | 0.00 | 0.83 / 0.33 | 0.26 [67] | 2.42 [51] | 0.42 [111] | 2.55 [7] |
| GPU≥50% | 610 | 0.39 | 0.00 | 0.80 / 0.37 | 0.16 [375] | 1.55 [235] | 0.29 [585] | 1.44 [25] |
| 10–50% | 122 | 0.36 | 0.00 | 0.80 / 0.35 | 0.46 [78] | 6.57 [44] | 0.73 [118] | 20.47 [4] |
| miss<10% | 293 | 0.40 | 0.00 | 0.82 / 0.42 | 2.53 [177] | 13.03 [116] | 5.21 [289] | 20.70 [4] |
| mixed | 16 | 0.56 | 0.00 | 0.77 / 0.10 | 0.26 [7] | 2.48 [9] | 1.74 [14] | 9.55 [2] |
