### Table D-1 — run level

| quantity | stock | shortest-prompt-first priority | P4 |
|---|---|---|---|
| requests completed (failed) | 599 (0) | 599 (0) | 599 (0) |
| makespan: first send → last completion (s) | 4982 | 4982 | 4982 |
| completed requests / s | 0.120 | 0.120 | 0.120 |
| prompt tokens served from a cache: total / host (LMCache) / GPU prefix | 0.164 / 0.120 / 0.044 | 0.159 / 0.115 / 0.044 | 0.182 / 0.137 / 0.044 |
| requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 % | 1 / 338 / 131 / 85 / 44 | 1 / 339 / 131 / 86 / 42 | 1 / 330 / 133 / 87 / 48 |
| requests with a load from the host tier; tokens loaded per such request, p50 | 93; 6144 | 92; 6144 | 101; 6656 |
| prompt tokens computed / s | 1155 | 1162 | 1131 |
| output tokens / s | 42.2 | 42.2 | 42.2 |
| TTFT p50 / p95 / p99 (s) | 3.46 / 26.98 / 34.19 | 3.09 / 17.43 / 36.34 | 2.44 / 16.78 / 36.88 |
| TTFT mean / max (s) | 6.32 / 40.60 | 5.34 / 44.97 | 5.00 / 44.12 |
| request time p50 / p95 / mean (s) | 15.84 / 45.07 / 18.60 | 15.45 / 45.73 / 18.38 | 13.90 / 44.30 / 17.91 |
| time per output token after the first, p50 / p95 (ms) | 25 / 134 | 28 / 151 | 26 / 126 |
| preemptions (requests preempted) | 2 (2) | 3 (3) | 4 (4) |
| running requests refused their next chunk | 4 | 16 | 9 |
| refused admission attempts: full-sequence gate / free blocks / in-flight reservation | 4966 / 0 / 0 | 4399 / 0 / 1 | 747 / 0 / 0 |
| GPU KV pool (blocks); used share, time-weighted mean | 7456; 0.261 | 7456; 0.268 | 7456; 0.263 |
| time with free blocks < 25 % / < 10 % of the pool | 0.095 / 0.033 | 0.096 / 0.038 | 0.096 / 0.037 |
| blocks reserved for in-flight prefills (stock reservation) / held by loads in transfer, time-weighted mean | 119 / 13 | 123 / 10 | 128 / 5 |
| blocks kept free for passed hits (`hitres`), time-weighted mean; share of time with such a reservation | 0.0; 0.000 | 0.0; 0.000 | 2.1; 0.004 |
| time in steps whose running requests use the whole token budget | 0.205 | 0.209 | 0.117 |
| time in steps with a shortened token budget (prototype) | 0.000 | 0.000 | 0.047 |
| time with the mechanisms suspended by the starvation bound (`agecap`) | 0.000 | 0.000 | 0.000 |
| running / waiting requests, time-weighted mean | 1.8 / 0.5 | 1.9 / 0.3 | 1.9 / 0.3 |
| GPU busy share: engine steps with tokens / NVML utilization | 0.493 / 0.494 | 0.497 / 0.497 | 0.493 / 0.493 |
| KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks | 30.4 / 198.4 / 0 | 29.1 / 199.2 / 0 | 34.9 / 212.2 / 0 |
| requests with an LMCache store; GB stored | 567; 198.4 | 572; 199.2 | 594; 212.2 |

### Table D-2 — per category as served in each run: n \| TTFT p50 / p95 / mean (s) \| request time p50 (s) \| time per output token p50 (ms)

| category | stock | shortest-prompt-first priority | P4 |
|---|---|---|---|
| host-dominant hit | 65 \| 0.79 / 20.68 / 5.45 \| 10.32 \| 18 | 64 \| 0.80 / 21.26 / 4.84 \| 10.32 \| 18 | 71 \| 0.71 / 4.30 / 1.86 \| 9.74 \| 20 |
| GPU-prefix hit | 54 \| 0.16 / 29.13 / 4.75 \| 7.88 \| 19 | 54 \| 0.16 / 7.12 / 1.84 \| 6.87 \| 20 | 54 \| 0.17 / 2.21 / 0.81 \| 7.00 \| 21 |
| partial hit | 131 \| 0.77 / 26.53 / 4.35 \| 10.41 \| 19 | 131 \| 0.77 / 10.60 / 2.79 \| 10.41 \| 23 | 133 \| 0.77 / 11.08 / 2.60 \| 9.84 \| 21 |
| miss | 339 \| 5.15 / 27.21 / 7.52 \| 21.04 \| 34 | 340 \| 5.02 / 19.89 / 7.04 \| 20.57 \| 37 | 331 \| 5.02 / 23.66 / 7.45 \| 19.70 \| 31 |
| all requests | 599 \| 3.46 / 26.98 / 6.32 \| 15.84 \| 25 | 599 \| 3.09 / 17.43 / 5.34 \| 15.45 \| 28 | 599 \| 2.44 / 16.78 / 5.00 \| 13.90 \| 26 |

### Table D-3 — paired by the category in `stock`: the same requests in every run; changes against `stock`

| category in the reference (n) | quantity | stock | shortest-prompt-first priority | P4 |
|---|---|---|---|---|
| host-dominant hit (65) | TTFT p50 (s) | 0.79 | 0.81  +0.01 (+2 %) | 0.71  -0.08 (-10 %) |
| host-dominant hit (65) | TTFT p95 (s) | 20.68 | 21.26  +0.58 (+3 %) | 4.30  -16.38 (-79 %) |
| host-dominant hit (65) | TTFT mean (s) | 5.45 | 5.03  -0.42 (-8 %) | 1.90  -3.55 (-65 %) |
| host-dominant hit (65) | request time p50 (s) | 10.32 | 10.32  -0.00 (-0 %) | 9.58  -0.75 (-7 %) |
| host-dominant hit (65) | request time mean (s) | 15.24 | 15.32  +0.08 (+1 %) | 14.04  -1.20 (-8 %) |
| host-dominant hit (65) | requests with TTFT lower / higher by > 10 % | – | 12 % / 5 % | 34 % / 3 % |
| GPU-prefix hit (54) | TTFT p50 (s) | 0.16 | 0.16  +0.00 (+0 %) | 0.17  +0.01 (+6 %) |
| GPU-prefix hit (54) | TTFT p95 (s) | 29.13 | 7.12  -22.00 (-76 %) | 2.21  -26.91 (-92 %) |
| GPU-prefix hit (54) | TTFT mean (s) | 4.75 | 1.84  -2.92 (-61 %) | 0.81  -3.94 (-83 %) |
| GPU-prefix hit (54) | request time p50 (s) | 7.88 | 6.87  -1.01 (-13 %) | 7.00  -0.88 (-11 %) |
| GPU-prefix hit (54) | request time mean (s) | 13.00 | 11.83  -1.17 (-9 %) | 11.34  -1.66 (-13 %) |
| GPU-prefix hit (54) | requests with TTFT lower / higher by > 10 % | – | 24 % / 0 % | 37 % / 0 % |
| partial hit (131) | TTFT p50 (s) | 0.77 | 0.77  +0.00 (+0 %) | 0.77  -0.00 (-0 %) |
| partial hit (131) | TTFT p95 (s) | 26.53 | 10.60  -15.92 (-60 %) | 10.43  -16.09 (-61 %) |
| partial hit (131) | TTFT mean (s) | 4.35 | 2.79  -1.56 (-36 %) | 2.46  -1.89 (-44 %) |
| partial hit (131) | request time p50 (s) | 10.41 | 10.41  +0.00 (+0 %) | 9.71  -0.70 (-7 %) |
| partial hit (131) | request time mean (s) | 14.15 | 13.41  -0.74 (-5 %) | 13.23  -0.92 (-7 %) |
| partial hit (131) | requests with TTFT lower / higher by > 10 % | – | 11 % / 1 % | 17 % / 5 % |
| miss (339) | TTFT p50 (s) | 5.15 | 4.84  -0.30 (-6 %) | 4.96  -0.19 (-4 %) |
| miss (339) | TTFT p95 (s) | 27.21 | 19.89  -7.33 (-27 %) | 23.66  -3.56 (-13 %) |
| miss (339) | TTFT mean (s) | 7.52 | 7.01  -0.51 (-7 %) | 7.37  -0.15 (-2 %) |
| miss (339) | request time p50 (s) | 21.04 | 20.48  -0.56 (-3 %) | 19.70  -1.34 (-6 %) |
| miss (339) | request time mean (s) | 21.96 | 22.04  +0.08 (+0 %) | 21.64  -0.33 (-1 %) |
| miss (339) | requests with TTFT lower / higher by > 10 % | – | 9 % / 6 % | 9 % / 14 % |
| all requests (599) | TTFT p50 (s) | 3.46 | 3.09  -0.37 (-11 %) | 2.44  -1.02 (-30 %) |
| all requests (599) | TTFT p95 (s) | 26.98 | 17.43  -9.55 (-35 %) | 16.78  -10.20 (-38 %) |
| all requests (599) | TTFT mean (s) | 6.32 | 5.34  -0.98 (-15 %) | 5.00  -1.31 (-21 %) |
| all requests (599) | request time p50 (s) | 15.84 | 15.45  -0.38 (-2 %) | 13.90  -1.94 (-12 %) |
| all requests (599) | request time mean (s) | 18.60 | 18.38  -0.23 (-1 %) | 17.91  -0.69 (-4 %) |
| all requests (599) | requests with TTFT lower / higher by > 10 % | – | 12 % / 4 % | 16 % / 9 % |

### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \| request time p50 (s)

| prompt tokens (n) | stock | shortest-prompt-first priority | P4 |
|---|---|---|---|
| < 2,048 (121) | 0.23 / 27.56 / 33.89 \| 9.18 | 0.23 / 8.41 / 17.43 \| 8.44 | 0.24 / 4.35 / 9.82 \| 7.79 |
| 2,048–8,191 (157) | 1.23 / 19.37 / 34.69 \| 10.77 | 1.23 / 11.55 / 14.62 \| 10.69 | 1.20 / 11.51 / 18.69 \| 10.44 |
| ≥ 8,192 (321) | 5.36 / 27.21 / 40.60 \| 21.04 | 5.42 / 24.75 / 44.97 \| 20.53 | 4.95 / 23.66 / 44.12 \| 19.70 |
| requests with TTFT > 30 s / > 60 s | 15 / 0 | 12 / 0 | 12 / 0 |
