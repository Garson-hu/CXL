### Table D-1 — run level

| quantity | stock | shortest-prompt-first priority | P1 |
|---|---|---|---|
| requests completed (failed) | 544 (0) | 544 (0) | 543 (1) |
| makespan: first send → last completion (s) | 1275 | 1275 | 1301 |
| completed requests / s | 0.427 | 0.427 | 0.417 |
| prompt tokens served from a cache: total / host (LMCache) / GPU prefix | 0.368 / 0.037 / 0.331 | 0.368 / 0.038 / 0.330 | 0.368 / 0.041 / 0.327 |
| requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 % | 3 / 161 / 64 / 182 / 134 | 3 / 161 / 64 / 182 / 134 | 3 / 160 / 64 / 182 / 134 |
| requests with a load from the host tier; tokens loaded per such request, p50 | 23; 5120 | 25; 2560 | 30; 2560 |
| prompt tokens computed / s | 2287 | 2287 | 2235 |
| output tokens / s | 88.1 | 88.1 | 86.1 |
| TTFT p50 / p95 / p99 (s) | 10.42 / 36.42 / 43.03 | 6.25 / 26.26 / 39.27 | 12.43 / 46.98 / 61.24 |
| TTFT mean / max (s) | 12.72 / 46.10 | 8.77 / 61.81 | 16.44 / 68.48 |
| request time p50 / p95 / mean (s) | 20.91 / 100.50 / 32.41 | 16.16 / 96.00 / 29.10 | 26.17 / 123.48 / 39.43 |
| time per output token after the first, p50 / p95 (ms) | 74 / 443 | 90 / 440 | 123 / 402 |
| preemptions (requests preempted) | 0 (0) | 0 (0) | 0 (0) |
| running requests refused their next chunk | 0 | 0 | 0 |
| refused admission attempts: full-sequence gate / free blocks / in-flight reservation | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| GPU KV pool (blocks); used share, time-weighted mean | 19919; 0.352 | 19919; 0.355 | 19919; 0.398 |
| time with free blocks < 25 % / < 10 % of the pool | 0.036 / 0.000 | 0.037 / 0.001 | 0.064 / 0.008 |
| blocks reserved for in-flight prefills (stock reservation) / held by loads in transfer, time-weighted mean | 276 / 23 | 295 / 44 | 338 / 39 |
| blocks kept free for passed hits (`hitres`), time-weighted mean; share of time with such a reservation | 0.0; 0.000 | 0.0; 0.000 | 0.0; 0.000 |
| time in steps whose running requests use the whole token budget | 0.435 | 0.436 | 0.042 |
| time in steps with a shortened token budget (prototype) | 0.000 | 0.000 | 0.204 |
| time with the mechanisms suspended by the starvation bound (`agecap`) | 0.000 | 0.000 | 0.000 |
| running / waiting requests, time-weighted mean | 9.1 / 4.6 | 9.4 / 2.9 | 10.4 / 6.0 |
| GPU busy share: engine steps with tokens / NVML utilization | 0.867 / 0.866 | 0.867 / 0.865 | 0.897 / 0.895 |
| KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks | 6.3 / 102.8 / 2183 | 6.4 / 102.5 / 2183 | 6.9 / 102.8 / 2183 |
| requests with an LMCache store; GB stored | 477; 109.0 | 477; 109.0 | 476; 108.8 |

### Table D-2 — per category as served in each run: n \| TTFT p50 / p95 / mean (s) \| request time p50 (s) \| time per output token p50 (ms)

| category | stock | shortest-prompt-first priority | P1 |
|---|---|---|---|
| host-dominant hit | 17 \| 15.42 / 44.07 / 16.11 \| 28.97 \| 67 | 17 \| 10.74 / 32.38 / 11.78 \| 23.13 \| 70 | 24 \| 14.26 / 24.27 / 12.09 \| 24.91 \| 114 |
| GPU-prefix hit | 299 \| 9.15 / 36.50 / 11.84 \| 14.96 \| 48 | 299 \| 5.29 / 19.91 / 6.85 \| 9.48 \| 66 | 292 \| 4.37 / 42.88 / 13.72 \| 13.62 \| 154 |
| partial hit | 64 \| 8.41 / 32.71 / 11.34 \| 29.90 \| 86 | 64 \| 3.39 / 16.19 / 5.43 \| 28.65 \| 90 | 64 \| 10.07 / 56.65 / 16.99 \| 47.43 \| 98 |
| miss | 164 \| 12.22 / 36.91 / 14.53 \| 58.74 \| 101 | 164 \| 9.88 / 36.32 / 13.25 \| 56.99 \| 107 | 163 \| 18.52 / 52.09 / 21.74 \| 68.96 \| 119 |
| all requests | 544 \| 10.42 / 36.42 / 12.72 \| 20.91 \| 74 | 544 \| 6.25 / 26.26 / 8.77 \| 16.16 \| 90 | 543 \| 12.43 / 46.98 / 16.44 \| 26.17 \| 123 |

### Table D-3 — paired by the category in `stock`: the same requests in every run; changes against `stock`

| category in the reference (n) | quantity | stock | shortest-prompt-first priority | P1 |
|---|---|---|---|---|
| host-dominant hit (17) | TTFT p50 (s) | 15.42 | 10.74  -4.68 (-30 %) | 6.92  -8.50 (-55 %) |
| host-dominant hit (17) | TTFT p95 (s) | 44.07 | 32.38  -11.69 (-27 %) | 31.42  -12.65 (-29 %) |
| host-dominant hit (17) | TTFT mean (s) | 16.11 | 11.78  -4.33 (-27 %) | 9.84  -6.27 (-39 %) |
| host-dominant hit (17) | request time p50 (s) | 28.97 | 23.13  -5.84 (-20 %) | 33.92  +4.95 (+17 %) |
| host-dominant hit (17) | request time mean (s) | 41.63 | 38.76  -2.87 (-7 %) | 42.92  +1.29 (+3 %) |
| host-dominant hit (17) | requests with TTFT lower / higher by > 10 % | – | 35 % / 18 % | 76 % / 18 % |
| GPU-prefix hit (299) | TTFT p50 (s) | 9.15 | 5.29  -3.85 (-42 %) | 5.60  -3.54 (-39 %) |
| GPU-prefix hit (299) | TTFT p95 (s) | 36.50 | 19.91  -16.59 (-45 %) | 42.88  +6.38 (+17 %) |
| GPU-prefix hit (299) | TTFT mean (s) | 11.84 | 6.85  -4.99 (-42 %) | 13.81  +1.97 (+17 %) |
| GPU-prefix hit (299) | request time p50 (s) | 14.96 | 9.48  -5.47 (-37 %) | 13.85  -1.10 (-7 %) |
| GPU-prefix hit (299) | request time mean (s) | 16.26 | 11.88  -4.38 (-27 %) | 19.25  +2.99 (+18 %) |
| GPU-prefix hit (299) | requests with TTFT lower / higher by > 10 % | – | 41 % / 8 % | 29 % / 47 % |
| partial hit (64) | TTFT p50 (s) | 8.41 | 3.39  -5.02 (-60 %) | 10.07  +1.66 (+20 %) |
| partial hit (64) | TTFT p95 (s) | 32.71 | 16.19  -16.52 (-51 %) | 56.65  +23.93 (+73 %) |
| partial hit (64) | TTFT mean (s) | 11.34 | 5.43  -5.92 (-52 %) | 16.99  +5.65 (+50 %) |
| partial hit (64) | request time p50 (s) | 29.90 | 28.65  -1.25 (-4 %) | 47.43  +17.53 (+59 %) |
| partial hit (64) | request time mean (s) | 43.90 | 38.19  -5.71 (-13 %) | 54.33  +10.43 (+24 %) |
| partial hit (64) | requests with TTFT lower / higher by > 10 % | – | 48 % / 5 % | 12 % / 67 % |
| miss (163) | TTFT p50 (s) | 11.83 | 9.88  -1.95 (-16 %) | 18.52  +6.69 (+57 %) |
| miss (163) | TTFT p95 (s) | 36.91 | 36.32  -0.59 (-2 %) | 52.09  +15.18 (+41 %) |
| miss (163) | TTFT mean (s) | 14.48 | 13.28  -1.20 (-8 %) | 21.74  +7.26 (+50 %) |
| miss (163) | request time p50 (s) | 58.74 | 56.99  -1.75 (-3 %) | 68.96  +10.22 (+17 %) |
| miss (163) | request time mean (s) | 56.54 | 56.18  -0.36 (-1 %) | 70.25  +13.71 (+24 %) |
| miss (163) | requests with TTFT lower / higher by > 10 % | – | 25 % / 20 % | 1 % / 67 % |
| all requests (543) | TTFT p50 (s) | 10.26 | 6.24  -4.02 (-39 %) | 12.43  +2.17 (+21 %) |
| all requests (543) | TTFT p95 (s) | 36.42 | 26.26  -10.16 (-28 %) | 46.98  +10.55 (+29 %) |
| all requests (543) | TTFT mean (s) | 12.71 | 8.77  -3.94 (-31 %) | 16.44  +3.73 (+29 %) |
| all requests (543) | request time p50 (s) | 20.87 | 16.14  -4.73 (-23 %) | 26.17  +5.30 (+25 %) |
| all requests (543) | request time mean (s) | 32.40 | 29.12  -3.28 (-10 %) | 39.43  +7.03 (+22 %) |
| all requests (543) | requests with TTFT lower / higher by > 10 % | – | 37 % / 11 % | 20 % / 54 % |

### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \| request time p50 (s)

| prompt tokens (n) | stock | shortest-prompt-first priority | P1 |
|---|---|---|---|
| < 2,048 (60) | 10.42 / 37.52 / 38.19 \| 30.24 | 3.44 / 15.00 / 20.04 \| 25.55 | 2.99 / 56.65 / 62.03 \| 37.20 |
| 2,048–8,191 (339) | 8.84 / 36.42 / 44.52 \| 16.31 | 5.28 / 19.76 / 26.62 \| 10.91 | 8.29 / 46.19 / 61.47 \| 16.20 |
| ≥ 8,192 (144) | 13.62 / 36.91 / 46.10 \| 57.41 | 12.85 / 38.13 / 61.81 \| 55.19 | 18.64 / 52.97 / 68.48 \| 67.83 |
| requests with TTFT > 30 s / > 60 s | 57 / 0 | 20 / 1 | 127 / 8 |
