### Table D-1 — run level

| quantity | stock | P2 |
|---|---|---|
| requests completed (failed) | 291 (0) | 291 (0) |
| makespan: first send → last completion (s) | 1292 | 1293 |
| completed requests / s | 0.225 | 0.225 |
| prompt tokens served from a cache: total / host (LMCache) / GPU prefix | 0.075 / 0.031 / 0.044 | 0.093 / 0.048 / 0.044 |
| requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 % | 1 / 185 / 66 / 33 / 6 | 1 / 181 / 67 / 34 / 8 |
| requests with a load from the host tier; tokens loaded per such request, p50 | 14; 8704 | 19; 6656 |
| prompt tokens computed / s | 2393 | 2346 |
| output tokens / s | 83.6 | 83.5 |
| TTFT p50 / p95 / p99 (s) | 14.43 / 41.75 / 52.14 | 13.34 / 51.82 / 62.35 |
| TTFT mean / max (s) | 16.89 / 54.22 | 17.90 / 66.91 |
| request time p50 / p95 / mean (s) | 34.92 / 83.35 / 39.92 | 37.38 / 91.32 / 42.43 |
| time per output token after the first, p50 / p95 (ms) | 66 / 131 | 71 / 165 |
| preemptions (requests preempted) | 5 (3) | 9 (8) |
| running requests refused their next chunk | 10 | 18 |
| refused admission attempts: full-sequence gate / free blocks / in-flight reservation | 6363 / 0 / 0 | 6922 / 0 / 0 |
| GPU KV pool (blocks); used share, time-weighted mean | 7456; 0.605 | 7456; 0.627 |
| time with free blocks < 25 % / < 10 % of the pool | 0.511 / 0.246 | 0.548 / 0.260 |
| blocks reserved for in-flight prefills (stock reservation) / held by loads in transfer, time-weighted mean | 265 / 5 | 298 / 6 |
| blocks kept free for passed hits (`hitres`), time-weighted mean; share of time with such a reservation | 0.0; 0.000 | 22.0; 0.040 |
| time in steps whose running requests use the whole token budget | 0.455 | 0.080 |
| time in steps with a shortened token budget (prototype) | 0.000 | 0.118 |
| time with the mechanisms suspended by the starvation bound (`agecap`) | 0.000 | 0.000 |
| running / waiting requests, time-weighted mean | 5.8 / 3.1 | 6.2 / 3.3 |
| GPU busy share: engine steps with tokens / NVML utilization | 0.877 / 0.875 | 0.881 / 0.880 |
| KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks | 3.8 / 76.7 / 0 | 5.9 / 114.2 / 0 |
| requests with an LMCache store; GB stored | 237; 76.7 | 291; 114.2 |

### Table D-2 — per category as served in each run: n \| TTFT p50 / p95 / mean (s) \| request time p50 (s) \| time per output token p50 (ms)

| category | stock | P2 |
|---|---|---|
| host-dominant hit | 11 \| 25.23 / 31.45 / 19.34 \| 39.79 \| 81 | 14 \| 4.78 / 28.36 / 9.96 \| 34.16 \| 78 |
| GPU-prefix hit | 28 \| 12.88 / 41.20 / 15.33 \| 31.16 \| 52 | 28 \| 1.42 / 39.32 / 7.63 \| 32.14 \| 94 |
| partial hit | 66 \| 10.81 / 40.31 / 13.70 \| 30.02 \| 66 | 67 \| 7.84 / 53.61 / 15.50 \| 32.97 \| 69 |
| miss | 186 \| 15.33 / 42.97 / 18.10 \| 39.19 \| 68 | 182 \| 16.29 / 51.82 / 20.97 \| 45.48 \| 68 |
| all requests | 291 \| 14.43 / 41.75 / 16.89 \| 34.92 \| 66 | 291 \| 13.34 / 51.82 / 17.90 \| 37.38 \| 71 |

### Table D-3 — paired by the category in `stock`: the same requests in every run; changes against `stock`

| category in the reference (n) | quantity | stock | P2 |
|---|---|---|---|
| host-dominant hit (11) | TTFT p50 (s) | 25.23 | 4.78  -20.45 (-81 %) |
| host-dominant hit (11) | TTFT p95 (s) | 31.45 | 24.51  -6.94 (-22 %) |
| host-dominant hit (11) | TTFT mean (s) | 19.34 | 9.80  -9.54 (-49 %) |
| host-dominant hit (11) | request time p50 (s) | 39.79 | 31.22  -8.57 (-22 %) |
| host-dominant hit (11) | request time mean (s) | 43.47 | 37.66  -5.81 (-13 %) |
| host-dominant hit (11) | requests with TTFT lower / higher by > 10 % | – | 82 % / 9 % |
| GPU-prefix hit (28) | TTFT p50 (s) | 12.88 | 1.42  -11.46 (-89 %) |
| GPU-prefix hit (28) | TTFT p95 (s) | 41.20 | 39.32  -1.89 (-5 %) |
| GPU-prefix hit (28) | TTFT mean (s) | 15.33 | 7.63  -7.69 (-50 %) |
| GPU-prefix hit (28) | request time p50 (s) | 31.16 | 32.14  +0.97 (+3 %) |
| GPU-prefix hit (28) | request time mean (s) | 33.06 | 30.81  -2.25 (-7 %) |
| GPU-prefix hit (28) | requests with TTFT lower / higher by > 10 % | – | 57 % / 14 % |
| partial hit (66) | TTFT p50 (s) | 10.81 | 7.84  -2.96 (-27 %) |
| partial hit (66) | TTFT p95 (s) | 40.31 | 53.61  +13.30 (+33 %) |
| partial hit (66) | TTFT mean (s) | 13.70 | 15.52  +1.82 (+13 %) |
| partial hit (66) | request time p50 (s) | 30.02 | 32.97  +2.94 (+10 %) |
| partial hit (66) | request time mean (s) | 35.62 | 39.06  +3.44 (+10 %) |
| partial hit (66) | requests with TTFT lower / higher by > 10 % | – | 15 % / 47 % |
| miss (186) | TTFT p50 (s) | 15.33 | 16.20  +0.87 (+6 %) |
| miss (186) | TTFT p95 (s) | 42.97 | 51.82  +8.85 (+21 %) |
| miss (186) | TTFT mean (s) | 18.10 | 20.76  +2.66 (+15 %) |
| miss (186) | request time p50 (s) | 39.19 | 45.20  +6.01 (+15 %) |
| miss (186) | request time mean (s) | 42.27 | 45.65  +3.38 (+8 %) |
| miss (186) | requests with TTFT lower / higher by > 10 % | – | 4 % / 48 % |
| all requests (291) | TTFT p50 (s) | 14.43 | 13.34  -1.09 (-8 %) |
| all requests (291) | TTFT p95 (s) | 41.75 | 51.82  +10.07 (+24 %) |
| all requests (291) | TTFT mean (s) | 16.89 | 17.90  +1.01 (+6 %) |
| all requests (291) | request time p50 (s) | 34.92 | 37.38  +2.47 (+7 %) |
| all requests (291) | request time mean (s) | 39.92 | 42.43  +2.50 (+6 %) |
| all requests (291) | requests with TTFT lower / higher by > 10 % | – | 15 % / 43 % |

### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \| request time p50 (s)

| prompt tokens (n) | stock | P2 |
|---|---|---|
| < 2,048 (62) | 11.68 / 40.31 / 47.75 \| 30.02 | 1.68 / 53.61 / 60.69 \| 32.14 |
| 2,048–8,191 (76) | 11.67 / 40.82 / 45.13 \| 35.79 | 12.63 / 43.62 / 58.29 \| 37.27 |
| ≥ 8,192 (153) | 15.70 / 44.06 / 54.22 \| 39.79 | 16.29 / 52.86 / 66.91 \| 45.48 |
| requests with TTFT > 30 s / > 60 s | 58 / 0 | 68 / 7 |
