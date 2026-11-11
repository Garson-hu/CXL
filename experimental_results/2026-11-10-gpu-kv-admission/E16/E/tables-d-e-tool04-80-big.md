### Table D-1 — run level

| quantity | stock | P1 | P1 + synchronous scheduling |
|---|---|---|---|
| requests completed (failed) | 1159 (0) | 1159 (0) | 1159 (0) |
| makespan: first send → last completion (s) | 4984 | 4984 | 4984 |
| completed requests / s | 0.233 | 0.233 | 0.233 |
| prompt tokens served from a cache: total / host (LMCache) / GPU prefix | 0.384 / 0.036 / 0.348 | 0.385 / 0.036 / 0.349 | 0.385 / 0.036 / 0.349 |
| requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 % | 3 / 337 / 124 / 391 / 304 | 3 / 336 / 124 / 391 / 305 | 3 / 336 / 124 / 391 / 305 |
| requests with a load from the host tier; tokens loaded per such request, p50 | 42; 6144 | 42; 6144 | 42; 6144 |
| prompt tokens computed / s | 1210 | 1209 | 1209 |
| output tokens / s | 44.0 | 44.0 | 44.0 |
| TTFT p50 / p95 / p99 (s) | 2.03 / 18.07 / 25.74 | 1.38 / 17.61 / 27.32 | 1.09 / 18.41 / 27.77 |
| TTFT mean / max (s) | 4.80 / 35.86 | 3.81 / 41.54 | 3.84 / 42.14 |
| request time p50 / p95 / mean (s) | 7.24 / 43.61 / 12.48 | 5.75 / 45.04 / 11.88 | 6.27 / 46.19 / 12.45 |
| time per output token after the first, p50 / p95 (ms) | 22 / 399 | 24 / 385 | 28 / 403 |
| preemptions (requests preempted) | 0 (0) | 0 (0) | 0 (0) |
| running requests refused their next chunk | 0 | 0 | 0 |
| refused admission attempts: full-sequence gate / free blocks / in-flight reservation | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| GPU KV pool (blocks); used share, time-weighted mean | 19916; 0.108 | 19916; 0.110 | 19916; 0.111 |
| time with free blocks < 25 % / < 10 % of the pool | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| blocks reserved for in-flight prefills (stock reservation) / held by loads in transfer, time-weighted mean | 123 / 9 | 141 / 3 | 155 / 2 |
| blocks kept free for passed hits (`hitres`), time-weighted mean; share of time with such a reservation | 0.0; 0.000 | 0.0; 0.000 | 0.0; 0.000 |
| time in steps whose running requests use the whole token budget | 0.205 | 0.069 | 0.070 |
| time in steps with a shortened token budget (prototype) | 0.000 | 0.084 | 0.063 |
| time with the mechanisms suspended by the starvation bound (`agecap`) | 0.000 | 0.000 | 0.000 |
| running / waiting requests, time-weighted mean | 2.1 / 0.7 | 2.2 / 0.5 | 2.3 / 0.5 |
| GPU busy share: engine steps with tokens / NVML utilization | 0.495 / 0.495 | 0.502 / 0.502 | 0.512 / 0.499 |
| KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks | 12.9 / 68.8 / 17457 | 13.0 / 68.8 / 17457 | 13.0 / 68.7 / 17472 |
| requests with an LMCache store; GB stored | 992; 225.2 | 992; 225.0 | 992; 225.0 |

### Table D-2 — per category as served in each run: n \| TTFT p50 / p95 / mean (s) \| request time p50 (s) \| time per output token p50 (ms)

| category | stock | P1 | P1 + synchronous scheduling |
|---|---|---|---|
| host-dominant hit | 30 \| 1.96 / 31.10 / 7.39 \| 8.62 \| 25 | 30 \| 1.38 / 2.98 / 1.32 \| 6.46 \| 34 | 30 \| 1.00 / 2.26 / 0.99 \| 7.18 \| 44 |
| GPU-prefix hit | 661 \| 0.42 / 14.69 / 3.48 \| 0.90 \| 15 | 662 \| 0.50 / 7.65 / 1.68 \| 0.97 \| 15 | 662 \| 0.52 / 8.32 / 1.64 \| 1.05 \| 17 |
| partial hit | 124 \| 0.79 / 18.22 / 4.32 \| 11.48 \| 22 | 124 \| 0.80 / 19.46 / 4.18 \| 11.48 \| 23 | 124 \| 0.79 / 19.76 / 4.24 \| 12.53 \| 25 |
| miss | 340 \| 5.34 / 21.34 / 7.27 \| 21.77 \| 33 | 339 \| 5.67 / 23.94 / 8.06 \| 22.15 \| 33 | 339 \| 6.04 / 24.19 / 8.25 \| 23.65 \| 35 |
| all requests | 1159 \| 2.03 / 18.07 / 4.80 \| 7.24 \| 22 | 1159 \| 1.38 / 17.61 / 3.81 \| 5.75 \| 24 | 1159 \| 1.09 / 18.41 / 3.84 \| 6.27 \| 28 |

### Table D-3 — paired by the category in `stock`: the same requests in every run; changes against `stock`

| category in the reference (n) | quantity | stock | P1 | P1 + synchronous scheduling |
|---|---|---|---|---|
| host-dominant hit (30) | TTFT p50 (s) | 1.96 | 1.41  -0.55 (-28 %) | 1.07  -0.89 (-45 %) |
| host-dominant hit (30) | TTFT p95 (s) | 31.10 | 2.98  -28.12 (-90 %) | 2.26  -28.85 (-93 %) |
| host-dominant hit (30) | TTFT mean (s) | 7.39 | 1.38  -6.01 (-81 %) | 1.03  -6.36 (-86 %) |
| host-dominant hit (30) | request time p50 (s) | 8.62 | 7.61  -1.01 (-12 %) | 8.38  -0.24 (-3 %) |
| host-dominant hit (30) | request time mean (s) | 14.64 | 12.61  -2.02 (-14 %) | 13.16  -1.48 (-10 %) |
| host-dominant hit (30) | requests with TTFT lower / higher by > 10 % | – | 47 % / 0 % | 50 % / 3 % |
| GPU-prefix hit (661) | TTFT p50 (s) | 0.42 | 0.47  +0.05 (+12 %) | 0.51  +0.09 (+22 %) |
| GPU-prefix hit (661) | TTFT p95 (s) | 14.69 | 7.65  -7.04 (-48 %) | 8.32  -6.36 (-43 %) |
| GPU-prefix hit (661) | TTFT mean (s) | 3.48 | 1.68  -1.80 (-52 %) | 1.64  -1.83 (-53 %) |
| GPU-prefix hit (661) | request time p50 (s) | 0.90 | 0.96  +0.07 (+7 %) | 1.03  +0.13 (+15 %) |
| GPU-prefix hit (661) | request time mean (s) | 5.38 | 4.03  -1.34 (-25 %) | 4.14  -1.24 (-23 %) |
| GPU-prefix hit (661) | requests with TTFT lower / higher by > 10 % | – | 30 % / 9 % | 31 % / 11 % |
| partial hit (124) | TTFT p50 (s) | 0.79 | 0.80  +0.01 (+1 %) | 0.79  +0.00 (+0 %) |
| partial hit (124) | TTFT p95 (s) | 18.22 | 19.46  +1.24 (+7 %) | 19.76  +1.54 (+8 %) |
| partial hit (124) | TTFT mean (s) | 4.32 | 4.18  -0.14 (-3 %) | 4.24  -0.07 (-2 %) |
| partial hit (124) | request time p50 (s) | 11.48 | 11.48  -0.00 (-0 %) | 12.53  +1.06 (+9 %) |
| partial hit (124) | request time mean (s) | 15.98 | 16.20  +0.22 (+1 %) | 17.42  +1.44 (+9 %) |
| partial hit (124) | requests with TTFT lower / higher by > 10 % | – | 6 % / 23 % | 7 % / 28 % |
| miss (340) | TTFT p50 (s) | 5.34 | 5.67  +0.33 (+6 %) | 6.04  +0.70 (+13 %) |
| miss (340) | TTFT p95 (s) | 21.34 | 23.94  +2.60 (+12 %) | 24.19  +2.84 (+13 %) |
| miss (340) | TTFT mean (s) | 7.27 | 8.04  +0.77 (+11 %) | 8.23  +0.96 (+13 %) |
| miss (340) | request time p50 (s) | 21.77 | 22.15  +0.38 (+2 %) | 23.65  +1.88 (+9 %) |
| miss (340) | request time mean (s) | 24.82 | 25.50  +0.67 (+3 %) | 26.74  +1.91 (+8 %) |
| miss (340) | requests with TTFT lower / higher by > 10 % | – | 0 % / 28 % | 0 % / 45 % |
| all requests (1159) | TTFT p50 (s) | 2.03 | 1.38  -0.65 (-32 %) | 1.09  -0.94 (-46 %) |
| all requests (1159) | TTFT p95 (s) | 18.07 | 17.61  -0.46 (-3 %) | 18.41  +0.35 (+2 %) |
| all requests (1159) | TTFT mean (s) | 4.80 | 3.81  -0.99 (-21 %) | 3.84  -0.96 (-20 %) |
| all requests (1159) | request time p50 (s) | 7.24 | 5.75  -1.48 (-20 %) | 6.27  -0.97 (-13 %) |
| all requests (1159) | request time mean (s) | 12.48 | 11.88  -0.60 (-5 %) | 12.45  -0.03 (-0 %) |
| all requests (1159) | requests with TTFT lower / higher by > 10 % | – | 19 % / 16 % | 20 % / 23 % |

### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \| request time p50 (s)

| prompt tokens (n) | stock | P1 | P1 + synchronous scheduling |
|---|---|---|---|
| < 2,048 (112) | 0.85 / 18.22 / 25.89 \| 12.18 | 1.01 / 9.54 / 28.34 \| 11.48 | 0.80 / 9.82 / 28.69 \| 12.80 |
| 2,048–8,191 (741) | 0.81 / 14.99 / 34.90 \| 2.07 | 0.79 / 12.63 / 40.04 \| 1.91 | 0.74 / 13.29 / 40.64 \| 1.70 |
| ≥ 8,192 (306) | 5.97 / 22.83 / 35.86 \| 22.40 | 5.89 / 23.94 / 41.54 \| 22.95 | 6.11 / 24.19 / 42.14 \| 24.11 |
| requests with TTFT > 30 s / > 60 s | 4 / 0 | 6 / 0 | 7 / 0 |
