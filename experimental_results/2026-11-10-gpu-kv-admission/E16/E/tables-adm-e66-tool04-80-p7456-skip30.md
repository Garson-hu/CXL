## Admission analysis of `e66-tool04-80-p7456-skip30` (1159 requests, 83975 engine steps, pool 7456 blocks, token budget 2048)

### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)

| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 6201 | 384 | 2.30 / 20.38 | 0.00 / 1.98 | 0.69 / 1.84 | 0.00 / 0.63 | 0.16 / 0.50 | 0.00 / 0.32 | 0.20 / 0.36 |
| GPU≥50% | 593 | 6188 | 288 | 0.35 / 11.71 | 0.00 / 1.10 | 0.03 / 1.07 | 0.00 / 0.09 | 0.90 / 0.56 | 0.00 / 0.38 | 0.19 / 0.32 |
| 10–50% | 124 | 2214 | 102 | 0.79 / 13.99 | 0.00 / 1.07 | 0.13 / 1.45 | 0.00 / 0.36 | 0.15 / 0.51 | 0.00 / 0.49 | 0.41 / 0.69 |
| miss<10% | 340 | 13742 | 128 | 5.19 / 23.21 | 0.00 / 1.39 | 0.03 / 1.16 | 0.00 / 1.05 | 0.01 / 0.01 | 0.00 / 0.00 | 2.92 / 3.84 |
| mixed | 5 | 1546 | 32 | 3.20 / 12.65 | 1.53 / 2.76 | 0.98 / 1.00 | 0.00 / 0.02 | 0.16 / 0.45 | 0.00 / 0.82 | 0.17 / 0.27 |

### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)

| category | n | wait mean (s) | budget | budget_adm | hol:full | other | own:full | pending | pol:blocks | preempt | slots |
|---|---|---|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 5.28 | 3.58 [68%] | 0.23 [4%] | 0.00 [0%] | 0.19 [4%] | 0.00 [0%] | 0.73 [14%] | 0.54 [10%] | 0.00 [0%] | 0.00 [0%] |
| GPU≥50% | 593 | 2.28 | 1.61 [70%] | 0.17 [7%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.41 [18%] | 0.09 [4%] | 0.00 [0%] | 0.00 [0%] |
| 10–50% | 124 | 2.91 | 2.04 [70%] | 0.17 [6%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.45 [15%] | 0.25 [8%] | 0.00 [0%] | 0.00 [0%] |
| miss<10% | 340 | 3.60 | 2.23 [62%] | 0.17 [5%] | 0.00 [0%] | 0.00 [0%] | 0.00 [0%] | 0.44 [12%] | 0.75 [21%] | 0.00 [0%] | 0.00 [0%] |
| mixed | 5 | 5.05 | 3.74 [74%] | 0.22 [4%] | 0.00 [0%] | 0.24 [5%] | 0.00 [0%] | 0.83 [16%] | 0.02 [0%] | 0.00 [0%] | 0.00 [0%] |

### Table 3-pre — the `pre` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | pending | slots |
|---|---|---|---|---|---|---|
| host≥50% | 97 | 1.87 | 0.12 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 593 | 1.01 | 0.09 | 0.00 | 0.00 | 0.00 |
| 10–50% | 124 | 0.99 | 0.08 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 1.29 | 0.09 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 2.62 | 0.14 | 0.00 | 0.00 | 0.00 |

### Table 3-lookup — the `lookup` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | pending | pol:blocks | slots |
|---|---|---|---|---|---|---|
| host≥50% | 97 | 1.14 | 0.09 | 0.61 | 0.00 | 0.00 |
| GPU≥50% | 593 | 0.59 | 0.08 | 0.41 | 0.00 | 0.00 |
| 10–50% | 124 | 0.91 | 0.09 | 0.44 | 0.00 | 0.00 |
| miss<10% | 340 | 0.64 | 0.07 | 0.44 | 0.00 | 0.00 |
| mixed | 5 | 0.31 | 0.00 | 0.69 | 0.00 | 0.00 |

### Table 3-admit — the `admit` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | hol:full | own:full | pending | pol:blocks | preempt |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.09 | 0.00 | 0.00 | 0.00 | 0.00 | 0.54 | 0.00 |
| GPU≥50% | 593 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.09 | 0.00 |
| 10–50% | 124 | 0.11 | 0.00 | 0.00 | 0.00 | 0.00 | 0.25 | 0.00 |
| miss<10% | 340 | 0.29 | 0.00 | 0.00 | 0.00 | 0.00 | 0.75 | 0.00 |
| mixed | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 |

### Table 3-promote — the `promote` phase by reason (mean seconds per request)

| category | n | budget | budget_adm | other | own:full | pending |
|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.30 | 0.02 | 0.00 | 0.00 | 0.00 |
| GPU≥50% | 593 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10–50% | 124 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 |
| miss<10% | 340 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| mixed | 5 | 0.82 | 0.00 | 0.00 | 0.00 | 0.00 |

### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)

| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |
|---|---|---|---|---|---|---|
| compute, no computed tokens (miss / GPU-prefix hit) | 304 | 304 / 0 / 0 | 645 | 645 | 631 (580–1995) | 0 (0) |
| promotion after a load | 7 | 7 / 0 / 0 | 59 | 59 | 49 (3–49) | 0 (0) |

Requests refused at least once: 6 of 1159; preemptions: 3; running requests that could not get their next chunk: 6.
Admitted external loads: 114; reservation passed at admission p50 0 / max 158 blocks; free blocks at admission p50 5408.

### Table 5 — GPU KV occupancy over the run (time-weighted)

| quantity | value |
|---|---|
| used share of the pool, mean | 0.265 |
| time with free blocks < 50% of the pool | 0.175 |
| time with free blocks < 25% of the pool | 0.096 |
| time with free blocks < 10% of the pool | 0.044 |
| time with free blocks < 5% of the pool | 0.020 |
| blocks held by loads in transfer, mean / max | 7 / 2016 |
| in-flight prefill reservation after schedule(), mean / max | 117 / 1990 |
| steps whose running requests used the whole token budget (share of time) | 0.201 |
| running requests, mean / max | 1.9 / 16 |
| waiting + kv-holding requests, mean / max | 0.7 / 18 |

### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])

| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |
|---|---|---|---|---|---|---|---|---|
| host≥50% | 97 | 0.52 | 0.45 | 0.81 / 0.46 | 0.27 [47] | 9.05 [50] | 2.02 [95] | 5.84 [2] |
| GPU≥50% | 593 | 0.34 | 0.30 | 0.80 / 0.38 | 0.18 [394] | 5.78 [199] | 0.31 [564] | 4.35 [29] |
| 10–50% | 124 | 0.35 | 0.31 | 0.80 / 0.40 | 0.44 [80] | 7.08 [44] | 0.77 [121] | 8.69 [3] |
| miss<10% | 340 | 0.36 | 0.32 | 0.83 / 0.45 | 2.83 [216] | 10.59 [124] | 5.12 [329] | 17.71 [11] |
| mixed | 5 | 0.60 | 0.60 | 0.78 / 0.41 | 0.27 [2] | 11.12 [3] | 3.20 [5] | – |
