### Table D-1 — run level

| quantity | stock | P1 |
|---|---|---|
| requests completed (failed) | 544 (0) | 544 (0) |
| makespan: first send → last completion (s) | 5031 | 5031 |
| completed requests / s | 0.108 | 0.108 |
| prompt tokens served from a cache: total / host (LMCache) / GPU prefix | 0.335 / 0.021 / 0.314 | 0.334 / 0.016 / 0.318 |
| requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 % | 3 / 172 / 65 / 178 / 126 | 3 / 173 / 64 / 178 / 126 |
| requests with a load from the host tier; tokens loaded per such request, p50 | 27; 2560 | 21; 2560 |
| prompt tokens computed / s | 610 | 610 |
| output tokens / s | 22.3 | 22.3 |
| TTFT p50 / p95 / p99 (s) | 3.69 / 32.56 / 56.68 | 2.64 / 29.77 / 59.23 |
| TTFT mean / max (s) | 8.44 / 68.46 | 6.97 / 69.52 |
| request time p50 / p95 / mean (s) | 12.97 / 79.98 / 22.70 | 11.94 / 80.09 / 21.82 |
| time per output token after the first, p50 / p95 (ms) | 36 / 578 | 42 / 686 |
| preemptions (requests preempted) | 2 (2) | 1 (1) |
| running requests refused their next chunk | 5 | 2 |
| refused admission attempts: full-sequence gate / free blocks / in-flight reservation | 1277 / 0 / 0 | 1245 / 0 / 0 |
| GPU KV pool (blocks); used share, time-weighted mean | 8753; 0.222 | 8753; 0.223 |
| time with free blocks < 25 % / < 10 % of the pool | 0.064 / 0.031 | 0.061 / 0.028 |
| blocks reserved for in-flight prefills (stock reservation) / held by loads in transfer, time-weighted mean | 116 / 3 | 132 / 1 |
| blocks kept free for passed hits (`hitres`), time-weighted mean; share of time with such a reservation | 0.0; 0.000 | 0.0; 0.000 |
| time in steps whose running requests use the whole token budget | 0.196 | 0.082 |
| time in steps with a shortened token budget (prototype) | 0.000 | 0.072 |
| time with the mechanisms suspended by the starvation bound (`agecap`) | 0.000 | 0.000 |
| running / waiting requests, time-weighted mean | 1.8 / 0.6 | 1.9 / 0.4 |
| GPU busy share: engine steps with tokens / NVML utilization | 0.470 / 0.470 | 0.473 / 0.473 |
| KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks | 5.5 / 69.0 / 7473 | 4.3 / 68.7 / 8411 |
| requests with an LMCache store; GB stored | 469; 174.7 | 478; 178.5 |

### Table D-2 — per category as served in each run: n \| TTFT p50 / p95 / mean (s) \| request time p50 (s) \| time per output token p50 (ms)

| category | stock | P1 |
|---|---|---|
| host-dominant hit | 25 \| 14.44 / 56.62 / 16.49 \| 17.24 \| 56 | 20 \| 3.17 / 60.88 / 10.00 \| 6.76 \| 149 |
| GPU-prefix hit | 278 \| 0.64 / 20.14 / 4.74 \| 1.38 \| 24 | 284 \| 0.74 / 9.00 / 2.29 \| 1.75 \| 26 |
| partial hit | 65 \| 1.21 / 19.11 / 5.47 \| 17.86 \| 32 | 64 \| 1.20 / 17.14 / 5.43 \| 18.43 \| 37 |
| miss | 175 \| 9.62 / 46.66 / 14.00 \| 40.52 \| 59 | 176 \| 10.39 / 48.08 / 14.75 \| 40.46 \| 58 |
| all requests | 544 \| 3.69 / 32.56 / 8.44 \| 12.97 \| 36 | 544 \| 2.64 / 29.77 / 6.97 \| 11.94 \| 42 |

### Table D-3 — paired by the category in `stock`: the same requests in every run; changes against `stock`

| category in the reference (n) | quantity | stock | P1 |
|---|---|---|---|
| host-dominant hit (25) | TTFT p50 (s) | 14.44 | 3.70  -10.74 (-74 %) |
| host-dominant hit (25) | TTFT p95 (s) | 56.62 | 12.42  -44.20 (-78 %) |
| host-dominant hit (25) | TTFT mean (s) | 16.49 | 5.76  -10.73 (-65 %) |
| host-dominant hit (25) | request time p50 (s) | 17.24 | 8.48  -8.76 (-51 %) |
| host-dominant hit (25) | request time mean (s) | 21.04 | 11.88  -9.16 (-44 %) |
| host-dominant hit (25) | requests with TTFT lower / higher by > 10 % | – | 64 % / 4 % |
| GPU-prefix hit (278) | TTFT p50 (s) | 0.64 | 0.70  +0.06 (+9 %) |
| GPU-prefix hit (278) | TTFT p95 (s) | 20.14 | 9.18  -10.96 (-54 %) |
| GPU-prefix hit (278) | TTFT mean (s) | 4.74 | 2.34  -2.40 (-51 %) |
| GPU-prefix hit (278) | request time p50 (s) | 1.38 | 1.55  +0.17 (+12 %) |
| GPU-prefix hit (278) | request time mean (s) | 8.30 | 6.90  -1.41 (-17 %) |
| GPU-prefix hit (278) | requests with TTFT lower / higher by > 10 % | – | 26 % / 9 % |
| partial hit (65) | TTFT p50 (s) | 1.21 | 1.20  -0.01 (-0 %) |
| partial hit (65) | TTFT p95 (s) | 19.11 | 17.14  -1.97 (-10 %) |
| partial hit (65) | TTFT mean (s) | 5.47 | 5.43  -0.04 (-1 %) |
| partial hit (65) | request time p50 (s) | 17.86 | 17.85  -0.01 (-0 %) |
| partial hit (65) | request time mean (s) | 24.89 | 25.40  +0.51 (+2 %) |
| partial hit (65) | requests with TTFT lower / higher by > 10 % | – | 5 % / 8 % |
| miss (175) | TTFT p50 (s) | 9.62 | 10.39  +0.77 (+8 %) |
| miss (175) | TTFT p95 (s) | 46.66 | 48.08  +1.42 (+3 %) |
| miss (175) | TTFT mean (s) | 14.00 | 14.80  +0.80 (+6 %) |
| miss (175) | request time p50 (s) | 40.52 | 40.46  -0.06 (-0 %) |
| miss (175) | request time mean (s) | 44.80 | 45.41  +0.62 (+1 %) |
| miss (175) | requests with TTFT lower / higher by > 10 % | – | 0 % / 17 % |
| all requests (544) | TTFT p50 (s) | 3.69 | 2.64  -1.05 (-28 %) |
| all requests (544) | TTFT p95 (s) | 32.56 | 29.77  -2.79 (-9 %) |
| all requests (544) | TTFT mean (s) | 8.44 | 6.97  -1.46 (-17 %) |
| all requests (544) | request time p50 (s) | 12.97 | 11.94  -1.02 (-8 %) |
| all requests (544) | request time mean (s) | 22.70 | 21.82  -0.88 (-4 %) |
| all requests (544) | requests with TTFT lower / higher by > 10 % | – | 17 % / 11 % |

### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \| request time p50 (s)

| prompt tokens (n) | stock | P1 |
|---|---|---|
| < 2,048 (60) | 1.12 / 51.66 / 56.28 \| 22.31 | 1.20 / 16.19 / 46.89 \| 22.27 |
| 2,048–8,191 (340) | 1.40 / 22.87 / 67.18 \| 3.62 | 1.49 / 17.14 / 60.88 \| 3.67 |
| ≥ 8,192 (144) | 11.00 / 46.66 / 68.46 \| 41.94 | 11.63 / 48.08 / 69.52 \| 42.22 |
| requests with TTFT > 30 s / > 60 s | 31 / 3 | 27 / 5 |
