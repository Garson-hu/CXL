### Table D-1 — run level

| quantity | stock | oracle hits-first priority | prototype v1.1 | P2 | P4 |
|---|---|---|---|---|---|
| requests completed (failed) | 1159 (0) | 1159 (0) | 1159 (0) | 1158 (1) | 1159 (0) |
| makespan: first send → last completion (s) | 4984 | 4984 | 4984 | 4984 | 4984 |
| completed requests / s | 0.233 | 0.233 | 0.233 | 0.232 | 0.233 |
| prompt tokens served from a cache: total / host (LMCache) / GPU prefix | 0.431 / 0.120 / 0.311 | 0.431 / 0.110 / 0.321 | 0.446 / 0.119 / 0.327 | 0.446 / 0.122 / 0.324 | 0.446 / 0.118 / 0.328 |
| requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 % | 3 / 298 / 121 / 410 / 327 | 3 / 299 / 121 / 409 / 327 | 3 / 290 / 122 / 410 / 334 | 3 / 290 / 122 / 410 / 333 | 3 / 290 / 122 / 410 / 334 |
| requests with a load from the host tier; tokens loaded per such request, p50 | 187; 5120 | 170; 4608 | 169; 4608 | 173; 5120 | 167; 4608 |
| prompt tokens computed / s | 1117 | 1119 | 1088 | 1088 | 1088 |
| output tokens / s | 44.0 | 44.0 | 44.0 | 44.0 | 44.0 |
| TTFT p50 / p95 / p99 (s) | 1.56 / 21.02 / 34.00 | 1.48 / 16.43 / 33.46 | 1.21 / 17.56 / 34.29 | 1.22 / 18.55 / 34.63 | 1.20 / 14.79 / 32.13 |
| TTFT mean / max (s) | 4.93 / 43.94 | 3.94 / 43.14 | 3.64 / 40.42 | 3.74 / 40.44 | 3.25 / 43.13 |
| request time p50 / p95 / mean (s) | 6.30 / 40.29 / 11.39 | 5.51 / 39.83 / 10.64 | 4.93 / 40.17 / 10.51 | 4.99 / 39.86 / 10.62 | 4.85 / 39.98 / 10.24 |
| time per output token after the first, p50 / p95 (ms) | 19 / 225 | 20 / 374 | 20 / 329 | 20 / 329 | 20 / 315 |
| preemptions (requests preempted) | 1 (1) | 2 (2) | 3 (3) | 3 (3) | 3 (3) |
| running requests refused their next chunk | 2 | 4 | 6 | 6 | 6 |
| refused admission attempts: full-sequence gate / free blocks / in-flight reservation | 4907 / 0 / 17 | 4597 / 0 / 7 | 4767 / 0 / 36 | 4874 / 0 / 20 | 765 / 0 / 0 |
| GPU KV pool (blocks); used share, time-weighted mean | 7456; 0.255 | 7456; 0.258 | 7456; 0.258 | 7456; 0.258 | 7456; 0.261 |
| time with free blocks < 25 % / < 10 % of the pool | 0.092 / 0.037 | 0.096 / 0.036 | 0.092 / 0.034 | 0.092 / 0.031 | 0.094 / 0.039 |
| blocks reserved for in-flight prefills (stock reservation) / held by loads in transfer, time-weighted mean | 108 / 12 | 109 / 12 | 124 / 6 | 125 / 7 | 126 / 7 |
| blocks kept free for passed hits (`hitres`), time-weighted mean; share of time with such a reservation | 0.0; 0.000 | 0.0; 0.000 | 0.0; 0.000 | 3.2; 0.006 | 4.6; 0.009 |
| time in steps whose running requests use the whole token budget | 0.186 | 0.187 | 0.070 | 0.070 | 0.081 |
| time in steps with a shortened token budget (prototype) | 0.000 | 0.000 | 0.080 | 0.081 | 0.079 |
| time with the mechanisms suspended by the starvation bound (`agecap`) | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| running / waiting requests, time-weighted mean | 1.8 / 0.8 | 1.9 / 0.6 | 1.9 / 0.5 | 1.9 / 0.5 | 2.0 / 0.4 |
| GPU busy share: engine steps with tokens / NVML utilization | 0.485 / 0.486 | 0.485 / 0.486 | 0.486 / 0.486 | 0.486 / 0.486 | 0.485 / 0.486 |
| KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks | 43.4 / 187.9 / 0 | 39.7 / 190.0 / 0 | 43.0 / 202.5 / 0 | 43.8 / 202.7 / 0 | 42.7 / 202.4 / 0 |
| requests with an LMCache store; GB stored | 943; 187.9 | 961; 190.0 | 990; 202.5 | 990; 202.7 | 990; 202.4 |

### Table D-2 — per category as served in each run: n \| TTFT p50 / p95 / mean (s) \| request time p50 (s) \| time per output token p50 (ms)

| category | stock | oracle hits-first priority | prototype v1.1 | P2 | P4 |
|---|---|---|---|---|---|
| host-dominant hit | 148 \| 3.34 / 30.11 / 8.19 \| 10.75 \| 24 | 130 \| 1.78 / 16.80 / 3.87 \| 7.61 \| 23 | 122 \| 1.38 / 23.18 / 4.00 \| 8.14 \| 24 | 125 \| 1.45 / 25.25 / 4.54 \| 8.42 \| 25 | 118 \| 0.66 / 10.55 / 1.86 \| 6.84 \| 20 |
| GPU-prefix hit | 576 \| 0.27 / 13.24 / 2.56 \| 0.59 \| 13 | 594 \| 0.29 / 7.39 / 1.77 \| 0.64 \| 13 | 610 \| 0.32 / 4.24 / 1.20 \| 0.67 \| 13 | 605 \| 0.31 / 4.25 / 1.23 \| 0.64 \| 13 | 610 \| 0.34 / 4.02 / 1.14 \| 0.70 \| 14 |
| partial hit | 121 \| 0.78 / 20.12 / 4.29 \| 9.93 \| 21 | 121 \| 0.77 / 19.62 / 4.28 \| 9.93 \| 21 | 122 \| 0.78 / 21.91 / 4.20 \| 9.93 \| 21 | 122 \| 0.78 / 21.58 / 4.22 \| 9.93 \| 21 | 122 \| 0.78 / 13.84 / 3.31 \| 9.92 \| 22 |
| miss | 301 \| 5.05 / 26.55 / 7.89 \| 21.73 \| 32 | 302 \| 5.12 / 27.66 / 8.06 \| 21.71 \| 31 | 293 \| 5.31 / 29.38 / 8.42 \| 21.87 \| 30 | 293 \| 5.31 / 29.70 / 8.42 \| 21.85 \| 30 | 293 \| 5.30 / 27.06 / 8.18 \| 21.88 \| 30 |
| all requests | 1159 \| 1.56 / 21.02 / 4.93 \| 6.30 \| 19 | 1159 \| 1.48 / 16.43 / 3.94 \| 5.51 \| 20 | 1159 \| 1.21 / 17.56 / 3.64 \| 4.93 \| 20 | 1158 \| 1.22 / 18.55 / 3.74 \| 4.99 \| 20 | 1159 \| 1.20 / 14.79 / 3.25 \| 4.85 \| 20 |

### Table D-3 — paired by the category in `stock`: the same requests in every run; changes against `stock`

| category in the reference (n) | quantity | stock | oracle hits-first priority | prototype v1.1 | P2 | P4 |
|---|---|---|---|---|---|---|
| host-dominant hit (148) | TTFT p50 (s) | 3.34 | 2.61  -0.72 (-22 %) | 1.52  -1.81 (-54 %) | 1.61  -1.73 (-52 %) | 1.45  -1.89 (-57 %) |
| host-dominant hit (148) | TTFT p95 (s) | 30.11 | 16.17  -13.94 (-46 %) | 22.40  -7.71 (-26 %) | 22.39  -7.72 (-26 %) | 10.55  -19.56 (-65 %) |
| host-dominant hit (148) | TTFT mean (s) | 8.19 | 4.32  -3.87 (-47 %) | 3.58  -4.61 (-56 %) | 3.86  -4.33 (-53 %) | 2.27  -5.92 (-72 %) |
| host-dominant hit (148) | request time p50 (s) | 10.75 | 7.91  -2.84 (-26 %) | 6.79  -3.95 (-37 %) | 6.92  -3.82 (-36 %) | 6.02  -4.73 (-44 %) |
| host-dominant hit (148) | request time mean (s) | 13.14 | 10.00  -3.14 (-24 %) | 10.10  -3.04 (-23 %) | 10.39  -2.75 (-21 %) | 8.82  -4.33 (-33 %) |
| host-dominant hit (148) | requests with TTFT lower / higher by > 10 % | – | 34 % / 1 % | 47 % / 5 % | 47 % / 4 % | 53 % / 2 % |
| GPU-prefix hit (575) | TTFT p50 (s) | 0.27 | 0.27  +0.00 (+0 %) | 0.28  +0.01 (+4 %) | 0.27  +0.01 (+2 %) | 0.28  +0.01 (+3 %) |
| GPU-prefix hit (575) | TTFT p95 (s) | 13.24 | 6.98  -6.25 (-47 %) | 4.02  -9.22 (-70 %) | 4.25  -8.99 (-68 %) | 3.25  -9.99 (-75 %) |
| GPU-prefix hit (575) | TTFT mean (s) | 2.56 | 1.61  -0.96 (-37 %) | 1.11  -1.45 (-57 %) | 1.20  -1.37 (-53 %) | 1.01  -1.55 (-60 %) |
| GPU-prefix hit (575) | request time p50 (s) | 0.59 | 0.59  +0.00 (+0 %) | 0.59  +0.01 (+1 %) | 0.59  +0.00 (+1 %) | 0.59  +0.00 (+0 %) |
| GPU-prefix hit (575) | request time mean (s) | 3.93 | 3.29  -0.64 (-16 %) | 2.98  -0.95 (-24 %) | 3.04  -0.88 (-23 %) | 2.88  -1.05 (-27 %) |
| GPU-prefix hit (575) | requests with TTFT lower / higher by > 10 % | – | 13 % / 1 % | 25 % / 7 % | 24 % / 8 % | 25 % / 7 % |
| partial hit (121) | TTFT p50 (s) | 0.78 | 0.77  -0.00 (-0 %) | 0.77  -0.00 (-0 %) | 0.78  +0.00 (+1 %) | 0.78  +0.01 (+1 %) |
| partial hit (121) | TTFT p95 (s) | 20.12 | 19.62  -0.50 (-2 %) | 15.58  -4.54 (-23 %) | 15.88  -4.24 (-21 %) | 13.43  -6.69 (-33 %) |
| partial hit (121) | TTFT mean (s) | 4.29 | 4.28  -0.01 (-0 %) | 3.92  -0.37 (-9 %) | 3.93  -0.36 (-8 %) | 3.04  -1.25 (-29 %) |
| partial hit (121) | request time p50 (s) | 9.93 | 9.93  -0.00 (-0 %) | 9.85  -0.07 (-1 %) | 9.85  -0.07 (-1 %) | 9.85  -0.07 (-1 %) |
| partial hit (121) | request time mean (s) | 14.69 | 14.69  +0.00 (+0 %) | 14.61  -0.08 (-1 %) | 14.62  -0.07 (-0 %) | 14.27  -0.43 (-3 %) |
| partial hit (121) | requests with TTFT lower / higher by > 10 % | – | 2 % / 1 % | 12 % / 12 % | 11 % / 13 % | 17 % / 12 % |
| miss (301) | TTFT p50 (s) | 5.05 | 5.05  -0.00 (-0 %) | 5.22  +0.16 (+3 %) | 5.22  +0.16 (+3 %) | 5.21  +0.16 (+3 %) |
| miss (301) | TTFT p95 (s) | 26.55 | 27.66  +1.11 (+4 %) | 29.38  +2.83 (+11 %) | 29.70  +3.14 (+12 %) | 27.06  +0.51 (+2 %) |
| miss (301) | TTFT mean (s) | 7.89 | 8.07  +0.17 (+2 %) | 8.35  +0.45 (+6 %) | 8.35  +0.45 (+6 %) | 8.11  +0.21 (+3 %) |
| miss (301) | request time p50 (s) | 21.73 | 21.71  -0.02 (-0 %) | 21.84  +0.10 (+0 %) | 21.85  +0.12 (+1 %) | 21.82  +0.09 (+0 %) |
| miss (301) | request time mean (s) | 23.19 | 23.23  +0.04 (+0 %) | 23.31  +0.12 (+1 %) | 23.29  +0.11 (+0 %) | 23.27  +0.08 (+0 %) |
| miss (301) | requests with TTFT lower / higher by > 10 % | – | 0 % / 3 % | 6 % / 27 % | 6 % / 28 % | 9 % / 28 % |
| all requests (1158) | TTFT p50 (s) | 1.56 | 1.49  -0.07 (-5 %) | 1.21  -0.35 (-22 %) | 1.22  -0.34 (-22 %) | 1.20  -0.36 (-23 %) |
| all requests (1158) | TTFT p95 (s) | 21.02 | 16.43  -4.59 (-22 %) | 17.56  -3.46 (-16 %) | 18.55  -2.47 (-12 %) | 14.79  -6.23 (-30 %) |
| all requests (1158) | TTFT mean (s) | 4.94 | 3.95  -0.99 (-20 %) | 3.64  -1.30 (-26 %) | 3.74  -1.20 (-24 %) | 3.26  -1.68 (-34 %) |
| all requests (1158) | request time p50 (s) | 6.35 | 5.52  -0.83 (-13 %) | 4.95  -1.40 (-22 %) | 4.99  -1.36 (-21 %) | 4.85  -1.50 (-24 %) |
| all requests (1158) | request time mean (s) | 11.40 | 10.65  -0.75 (-7 %) | 10.52  -0.88 (-8 %) | 10.62  -0.79 (-7 %) | 10.25  -1.16 (-10 %) |
| all requests (1158) | requests with TTFT lower / higher by > 10 % | – | 12 % / 1 % | 22 % / 13 % | 21 % / 13 % | 24 % / 12 % |

### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \| request time p50 (s)

| prompt tokens (n) | stock | oracle hits-first priority | prototype v1.1 | P2 | P4 |
|---|---|---|---|---|---|
| < 2,048 (112) | 0.59 / 27.97 / 35.52 \| 11.06 | 0.56 / 11.18 / 35.37 \| 10.07 | 0.65 / 7.57 / 36.31 \| 9.48 | 0.64 / 9.84 / 36.52 \| 9.85 | 0.65 / 7.57 / 20.47 \| 9.75 |
| 2,048–8,191 (740) | 0.60 / 18.73 / 43.23 \| 1.47 | 0.55 / 9.93 / 35.18 \| 1.41 | 0.61 / 12.00 / 35.01 \| 1.48 | 0.61 / 13.28 / 35.09 \| 1.44 | 0.59 / 8.12 / 18.59 \| 1.42 |
| ≥ 8,192 (306) | 5.22 / 28.71 / 43.94 \| 21.01 | 5.21 / 26.97 / 43.14 \| 21.17 | 4.67 / 29.49 / 40.42 \| 21.09 | 4.73 / 29.83 / 40.44 \| 21.10 | 4.67 / 27.06 / 43.13 \| 21.04 |
| requests with TTFT > 30 s / > 60 s | 28 / 0 | 18 / 0 | 18 / 0 | 18 / 0 | 14 / 0 |
