### Table D-1 — run level

| quantity | stock (c60) | shortest-prompt-first priority | bypass alone; 30 s | P2 | P4 |
|---|---|---|---|---|---|
| requests completed (failed) | 291 (0) | 291 (0) | 291 (0) | 291 (0) | 291 (0) |
| makespan: first send → last completion (s) | 1292 | 1311 | 1281 | 1293 | 1294 |
| completed requests / s | 0.225 | 0.222 | 0.227 | 0.225 | 0.225 |
| prompt tokens served from a cache: total / host (LMCache) / GPU prefix | 0.075 / 0.031 / 0.044 | 0.073 / 0.028 / 0.044 | 0.093 / 0.048 / 0.044 | 0.093 / 0.048 / 0.044 | 0.093 / 0.048 / 0.044 |
| requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 % | 1 / 185 / 66 / 33 / 6 | 1 / 185 / 66 / 33 / 6 | 1 / 181 / 67 / 34 / 8 | 1 / 181 / 67 / 34 / 8 | 1 / 181 / 67 / 34 / 8 |
| requests with a load from the host tier; tokens loaded per such request, p50 | 14; 8704 | 14; 6656 | 19; 6656 | 19; 6656 | 19; 6656 |
| prompt tokens computed / s | 2392 | 2365 | 2368 | 2345 | 2344 |
| output tokens / s | 83.6 | 82.4 | 84.3 | 83.5 | 83.5 |
| TTFT p50 / p95 / p99 (s) | 14.46 / 41.93 / 52.32 | 5.82 / 34.89 / 146.65 | 10.20 / 42.89 / 55.76 | 13.42 / 52.01 / 62.49 | 10.82 / 52.05 / 63.34 |
| TTFT mean / max (s) | 16.96 / 54.48 | 11.60 / 314.82 | 13.26 / 60.84 | 17.98 / 67.23 | 15.83 / 64.83 |
| request time p50 / p95 / mean (s) | 34.96 / 83.53 / 40.02 | 30.89 / 79.87 / 36.79 | 31.78 / 79.59 / 36.39 | 37.45 / 91.59 / 42.39 | 36.25 / 91.23 / 40.68 |
| time per output token after the first, p50 / p95 (ms) | 66 / 132 | 70 / 190 | 65 / 139 | 69 / 163 | 73 / 159 |
| preemptions (requests preempted) | 5 (3) | 5 (3) | 6 (5) | 8 (7) | 11 (8) |
| running requests refused their next chunk | 10 | 14 | 12 | 16 | 22 |
| refused admission attempts: full-sequence gate / free blocks / in-flight reservation | 6376 / 0 / 0 | 7032 / 0 / 0 | 1581 / 0 / 0 | 6878 / 0 / 4 | 3507 / 0 / 0 |
| GPU KV pool (blocks); used share, time-weighted mean | 7456; 0.606 | 7456; 0.622 | 7456; 0.608 | 7456; 0.626 | 7456; 0.629 |
| time with free blocks < 25 % / < 10 % of the pool | 0.511 / 0.246 | 0.519 / 0.235 | 0.508 / 0.276 | 0.546 / 0.246 | 0.548 / 0.270 |
| blocks reserved for in-flight prefills (stock reservation) / held by loads in transfer, time-weighted mean | 265 / 5 | 281 / 8 | 264 / 5 | 297 / 6 | 292 / 7 |
| blocks kept free for passed hits (`hitres`), time-weighted mean; share of time with such a reservation | 0.0; 0.000 | 0.0; 0.000 | 13.6; 0.036 | 11.8; 0.020 | 18.3; 0.031 |
| time in steps whose running requests use the whole token budget | 0.454 | 0.471 | 0.452 | 0.080 | 0.088 |
| time in steps with a shortened token budget (prototype) | 0.000 | 0.000 | 0.000 | 0.114 | 0.113 |
| time with the mechanisms suspended by the starvation bound (`agecap`) | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| running / waiting requests, time-weighted mean | 5.8 / 3.1 | 6.1 / 2.0 | 5.9 / 2.3 | 6.2 / 3.3 | 6.3 / 2.8 |
| GPU busy share: engine steps with tokens / NVML utilization | 0.877 / 0.875 | 0.886 / 0.884 | 0.875 / 0.872 | 0.881 / 0.880 | 0.882 / 0.881 |
| KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks | 3.8 / 76.6 / 0 | 3.5 / 73.2 / 0 | 5.9 / 114.1 / 0 | 5.9 / 114.2 / 0 | 5.9 / 114.1 / 0 |
| requests with an LMCache store; GB stored | 237; 76.6 | 235; 73.2 | 291; 114.1 | 291; 114.2 | 291; 114.1 |

### Table D-2 — per category as served in each run: n \| TTFT p50 / p95 / mean (s) \| request time p50 (s) \| time per output token p50 (ms)

| category | stock (c60) | shortest-prompt-first priority | bypass alone; 30 s | P2 | P4 |
|---|---|---|---|---|---|
| host-dominant hit | 11 \| 25.45 / 31.74 / 19.47 \| 40.10 \| 81 | 11 \| 7.41 / 11.81 / 5.82 \| 26.03 \| 64 | 14 \| 12.69 / 23.48 / 11.79 \| 35.13 \| 77 | 14 \| 4.86 / 28.42 / 9.12 \| 31.78 \| 68 | 14 \| 3.00 / 26.72 / 5.94 \| 29.74 \| 78 |
| GPU-prefix hit | 28 \| 12.90 / 41.40 / 15.40 \| 31.49 \| 52 | 28 \| 2.22 / 10.11 / 3.62 \| 23.32 \| 74 | 28 \| 5.88 / 19.01 / 6.47 \| 25.00 \| 57 | 28 \| 1.47 / 39.76 / 8.34 \| 33.65 \| 94 | 28 \| 1.31 / 37.39 / 5.22 \| 28.67 \| 98 |
| partial hit | 66 \| 10.85 / 40.51 / 13.77 \| 30.24 \| 65 | 66 \| 2.11 / 11.22 / 3.64 \| 24.21 \| 68 | 67 \| 3.55 / 23.15 / 7.26 \| 26.24 \| 64 | 67 \| 7.87 / 52.62 / 15.57 \| 33.08 \| 70 | 67 \| 5.55 / 52.05 / 11.81 \| 27.90 \| 73 |
| miss | 186 \| 15.35 / 43.04 / 18.18 \| 39.35 \| 67 | 186 \| 9.27 / 46.62 / 15.97 \| 34.74 \| 71 | 182 \| 12.51 / 46.40 / 16.63 \| 37.07 \| 67 | 182 \| 16.33 / 52.01 / 21.04 \| 45.12 \| 66 | 182 \| 14.70 / 52.56 / 19.71 \| 43.84 \| 71 |
| all requests | 291 \| 14.46 / 41.93 / 16.96 \| 34.96 \| 66 | 291 \| 5.82 / 34.89 / 11.60 \| 30.89 \| 70 | 291 \| 10.20 / 42.89 / 13.26 \| 31.78 \| 65 | 291 \| 13.42 / 52.01 / 17.98 \| 37.45 \| 69 | 291 \| 10.82 / 52.05 / 15.83 \| 36.25 \| 73 |

### Table D-3 — paired by the category in `stock (c60)`: the same requests in every run; changes against `stock (c60)`

| category in the reference (n) | quantity | stock (c60) | shortest-prompt-first priority | bypass alone; 30 s | P2 | P4 |
|---|---|---|---|---|---|---|
| host-dominant hit (11) | TTFT p50 (s) | 25.45 | 5.49  -19.95 (-78 %) | 9.46  -15.98 (-63 %) | 4.86  -20.58 (-81 %) | 2.91  -22.53 (-89 %) |
| host-dominant hit (11) | TTFT p95 (s) | 31.74 | 11.81  -19.93 (-63 %) | 23.48  -8.25 (-26 %) | 24.57  -7.17 (-23 %) | 19.82  -11.91 (-38 %) |
| host-dominant hit (11) | TTFT mean (s) | 19.47 | 5.38  -14.08 (-72 %) | 11.53  -7.93 (-41 %) | 8.67  -10.80 (-55 %) | 4.83  -14.63 (-75 %) |
| host-dominant hit (11) | request time p50 (s) | 40.10 | 26.03  -14.07 (-35 %) | 29.47  -10.63 (-27 %) | 29.75  -10.34 (-26 %) | 29.03  -11.07 (-28 %) |
| host-dominant hit (11) | request time mean (s) | 43.63 | 29.45  -14.18 (-32 %) | 35.79  -7.83 (-18 %) | 35.10  -8.53 (-20 %) | 30.94  -12.68 (-29 %) |
| host-dominant hit (11) | requests with TTFT lower / higher by > 10 % | – | 64 % / 0 % | 55 % / 0 % | 82 % / 9 % | 91 % / 0 % |
| GPU-prefix hit (28) | TTFT p50 (s) | 12.90 | 2.22  -10.68 (-83 %) | 5.88  -7.02 (-54 %) | 1.47  -11.43 (-89 %) | 1.31  -11.59 (-90 %) |
| GPU-prefix hit (28) | TTFT p95 (s) | 41.40 | 10.11  -31.29 (-76 %) | 19.01  -22.39 (-54 %) | 39.76  -1.64 (-4 %) | 37.39  -4.02 (-10 %) |
| GPU-prefix hit (28) | TTFT mean (s) | 15.40 | 3.62  -11.79 (-77 %) | 6.47  -8.93 (-58 %) | 8.34  -7.06 (-46 %) | 5.22  -10.19 (-66 %) |
| GPU-prefix hit (28) | request time p50 (s) | 31.49 | 23.32  -8.17 (-26 %) | 25.00  -6.49 (-21 %) | 33.65  +2.16 (+7 %) | 28.67  -2.82 (-9 %) |
| GPU-prefix hit (28) | request time mean (s) | 33.19 | 23.32  -9.87 (-30 %) | 24.35  -8.84 (-27 %) | 31.36  -1.83 (-6 %) | 28.53  -4.66 (-14 %) |
| GPU-prefix hit (28) | requests with TTFT lower / higher by > 10 % | – | 61 % / 7 % | 46 % / 4 % | 54 % / 18 % | 68 % / 14 % |
| partial hit (66) | TTFT p50 (s) | 10.85 | 2.11  -8.74 (-81 %) | 3.55  -7.30 (-67 %) | 7.87  -2.98 (-27 %) | 5.55  -5.30 (-49 %) |
| partial hit (66) | TTFT p95 (s) | 40.51 | 11.22  -29.29 (-72 %) | 22.03  -18.48 (-46 %) | 52.62  +12.10 (+30 %) | 52.05  +11.54 (+28 %) |
| partial hit (66) | TTFT mean (s) | 13.77 | 3.64  -10.13 (-74 %) | 6.91  -6.86 (-50 %) | 15.59  +1.82 (+13 %) | 11.86  -1.91 (-14 %) |
| partial hit (66) | request time p50 (s) | 30.24 | 24.21  -6.02 (-20 %) | 26.24  -4.00 (-13 %) | 33.08  +2.84 (+9 %) | 29.59  -0.65 (-2 %) |
| partial hit (66) | request time mean (s) | 35.70 | 27.41  -8.29 (-23 %) | 28.77  -6.93 (-19 %) | 39.17  +3.47 (+10 %) | 35.61  -0.09 (-0 %) |
| partial hit (66) | requests with TTFT lower / higher by > 10 % | – | 56 % / 3 % | 38 % / 3 % | 14 % / 47 % | 33 % / 30 % |
| miss (186) | TTFT p50 (s) | 15.35 | 9.30  -6.05 (-39 %) | 12.67  -2.68 (-17 %) | 16.31  +0.96 (+6 %) | 14.32  -1.03 (-7 %) |
| miss (186) | TTFT p95 (s) | 43.04 | 46.62  +3.59 (+8 %) | 46.40  +3.36 (+8 %) | 52.01  +8.97 (+21 %) | 52.56  +9.52 (+22 %) |
| miss (186) | TTFT mean (s) | 18.18 | 16.00  -2.18 (-12 %) | 16.64  -1.54 (-8 %) | 20.83  +2.65 (+15 %) | 19.49  +1.31 (+7 %) |
| miss (186) | request time p50 (s) | 39.35 | 34.74  -4.61 (-12 %) | 37.07  -2.28 (-6 %) | 45.07  +5.73 (+15 %) | 43.74  +4.40 (+11 %) |
| miss (186) | request time mean (s) | 42.36 | 42.58  +0.22 (+1 %) | 40.95  -1.42 (-3 %) | 45.62  +3.26 (+8 %) | 44.89  +2.52 (+6 %) |
| miss (186) | requests with TTFT lower / higher by > 10 % | – | 42 % / 20 % | 21 % / 13 % | 3 % / 49 % | 14 % / 46 % |
| all requests (291) | TTFT p50 (s) | 14.46 | 5.82  -8.64 (-60 %) | 10.20  -4.26 (-29 %) | 13.42  -1.05 (-7 %) | 10.82  -3.65 (-25 %) |
| all requests (291) | TTFT p95 (s) | 41.93 | 34.89  -7.04 (-17 %) | 42.89  +0.96 (+2 %) | 52.01  +10.08 (+24 %) | 52.05  +10.12 (+24 %) |
| all requests (291) | TTFT mean (s) | 16.96 | 11.60  -5.36 (-32 %) | 13.26  -3.70 (-22 %) | 17.98  +1.02 (+6 %) | 15.83  -1.13 (-7 %) |
| all requests (291) | request time p50 (s) | 34.96 | 30.89  -4.08 (-12 %) | 31.78  -3.18 (-9 %) | 37.45  +2.49 (+7 %) | 36.25  +1.29 (+4 %) |
| all requests (291) | request time mean (s) | 40.02 | 36.79  -3.23 (-8 %) | 36.39  -3.63 (-9 %) | 42.39  +2.37 (+6 %) | 40.68  +0.66 (+2 %) |
| all requests (291) | requests with TTFT lower / higher by > 10 % | – | 48 % / 14 % | 29 % / 10 % | 13 % / 44 % | 26 % / 38 % |

### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \| request time p50 (s)

| prompt tokens (n) | stock (c60) | shortest-prompt-first priority | bypass alone; 30 s | P2 | P4 |
|---|---|---|---|---|---|
| < 2,048 (62) | 11.70 / 40.51 / 47.86 \| 30.24 | 1.98 / 8.90 / 10.39 \| 23.32 | 3.25 / 18.70 / 22.21 \| 24.17 | 1.76 / 52.62 / 60.70 \| 33.08 | 1.50 / 52.54 / 60.42 \| 29.59 |
| 2,048–8,191 (76) | 11.72 / 40.91 / 45.23 \| 35.72 | 4.04 / 11.81 / 12.87 \| 26.28 | 8.30 / 23.15 / 25.73 \| 30.10 | 11.24 / 43.86 / 58.27 \| 37.29 | 7.21 / 34.98 / 52.05 \| 33.85 |
| ≥ 8,192 (153) | 15.76 / 44.18 / 54.48 \| 40.10 | 10.77 / 56.88 / 314.82 \| 35.84 | 13.79 / 49.39 / 60.84 \| 39.40 | 16.33 / 52.62 / 67.23 \| 46.02 | 15.35 / 53.54 / 64.83 \| 44.57 |
| requests with TTFT > 30 s / > 60 s | 59 / 0 | 21 / 7 | 34 / 1 | 69 / 7 | 49 / 5 |
