### Table D-1 — run level

| quantity | stock (c66) | shortest-prompt-first priority | shortest-prompt-first + P1 | bypass alone; 30 s |
|---|---|---|---|---|
| requests completed (failed) | 1159 (0) | 1159 (0) | 1159 (0) | 1159 (0) |
| makespan: first send → last completion (s) | 4984 | 4984 | 4984 | 4984 |
| completed requests / s | 0.233 | 0.233 | 0.233 | 0.233 |
| prompt tokens served from a cache: total / host (LMCache) / GPU prefix | 0.382 / 0.071 / 0.311 | 0.380 / 0.060 / 0.320 | 0.383 / 0.054 / 0.329 | 0.384 / 0.066 / 0.318 |
| requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 % | 3 / 336 / 123 / 393 / 304 | 3 / 338 / 123 / 393 / 302 | 3 / 337 / 123 / 391 / 305 | 3 / 337 / 124 / 391 / 304 |
| requests with a load from the host tier; tokens loaded per such request, p50 | 126; 5632 | 109; 4608 | 92; 2560 | 114; 5120 |
| prompt tokens computed / s | 1214 | 1218 | 1212 | 1210 |
| output tokens / s | 44.0 | 44.0 | 44.0 | 44.0 |
| TTFT p50 / p95 / p99 (s) | 2.01 / 22.34 / 34.50 | 1.85 / 13.51 / 31.04 | 1.38 / 11.78 / 31.82 | 1.99 / 16.29 / 31.12 |
| TTFT mean / max (s) | 5.37 / 51.73 | 3.88 / 48.01 | 3.19 / 51.17 | 4.53 / 49.13 |
| request time p50 / p95 / mean (s) | 7.07 / 40.93 / 12.13 | 6.07 / 40.47 / 11.26 | 5.16 / 40.96 / 10.87 | 6.58 / 40.40 / 11.47 |
| time per output token after the first, p50 / p95 (ms) | 20 / 252 | 22 / 382 | 23 / 343 | 21 / 319 |
| preemptions (requests preempted) | 1 (1) | 3 (3) | 4 (3) | 3 (3) |
| running requests refused their next chunk | 2 | 8 | 16 | 6 |
| refused admission attempts: full-sequence gate / free blocks / in-flight reservation | 5023 / 0 / 6 | 4203 / 0 / 0 | 4238 / 0 / 46 | 311 / 0 / 0 |
| GPU KV pool (blocks); used share, time-weighted mean | 7456; 0.264 | 7456; 0.270 | 7456; 0.273 | 7456; 0.265 |
| time with free blocks < 25 % / < 10 % of the pool | 0.096 / 0.039 | 0.099 / 0.042 | 0.100 / 0.037 | 0.096 / 0.044 |
| blocks reserved for in-flight prefills (stock reservation) / held by loads in transfer, time-weighted mean | 119 / 8 | 122 / 6 | 138 / 3 | 117 / 7 |
| blocks kept free for passed hits (`hitres`), time-weighted mean; share of time with such a reservation | 0.0; 0.000 | 0.0; 0.000 | 0.0; 0.000 | 7.1; 0.013 |
| time in steps whose running requests use the whole token budget | 0.202 | 0.205 | 0.094 | 0.201 |
| time in steps with a shortened token budget (prototype) | 0.000 | 0.000 | 0.083 | 0.000 |
| time with the mechanisms suspended by the starvation bound (`agecap`) | 0.000 | 0.000 | 0.000 | 0.000 |
| running / waiting requests, time-weighted mean | 1.9 / 0.9 | 2.0 / 0.5 | 2.1 / 0.4 | 1.9 / 0.7 |
| GPU busy share: engine steps with tokens / NVML utilization | 0.498 / 0.499 | 0.500 / 0.500 | 0.505 / 0.506 | 0.497 / 0.498 |
| KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks | 25.5 / 68.8 / 14550 | 21.8 / 68.7 / 16002 | 19.3 / 68.7 / 17467 | 23.7 / 68.8 / 17463 |
| requests with an LMCache store; GB stored | 946; 204.3 | 969; 206.2 | 992; 225.5 | 992; 225.1 |

### Table D-2 — per category as served in each run: n \| TTFT p50 / p95 / mean (s) \| request time p50 (s) \| time per output token p50 (ms)

| category | stock (c66) | shortest-prompt-first priority | shortest-prompt-first + P1 | bypass alone; 30 s |
|---|---|---|---|---|
| host-dominant hit | 111 \| 6.57 / 31.12 / 10.51 \| 10.96 \| 24 | 96 \| 2.04 / 15.88 / 4.72 \| 4.57 \| 22 | 75 \| 1.04 / 3.90 / 1.68 \| 3.59 \| 23 | 97 \| 2.30 / 20.38 / 5.83 \| 5.00 \| 23 |
| GPU-prefix hit | 578 \| 0.32 / 13.37 / 2.86 \| 0.67 \| 14 | 594 \| 0.35 / 8.01 / 2.03 \| 0.79 \| 14 | 615 \| 0.46 / 4.09 / 1.11 \| 0.97 \| 15 | 593 \| 0.35 / 11.71 / 2.73 \| 0.77 \| 14 |
| partial hit | 123 \| 0.78 / 22.52 / 4.65 \| 11.27 \| 21 | 123 \| 0.77 / 9.05 / 2.33 \| 11.23 \| 23 | 123 \| 0.78 / 7.22 / 1.97 \| 11.13 \| 23 | 124 \| 0.79 / 13.99 / 3.72 \| 11.30 \| 22 |
| miss | 339 \| 5.45 / 26.54 / 8.06 \| 21.58 \| 32 | 341 \| 5.14 / 22.27 / 7.41 \| 21.53 \| 34 | 340 \| 5.11 / 27.01 / 7.75 \| 21.80 \| 33 | 340 \| 5.19 / 23.21 / 7.58 \| 21.46 \| 31 |
| all requests | 1159 \| 2.01 / 22.34 / 5.37 \| 7.07 \| 20 | 1159 \| 1.85 / 13.51 / 3.88 \| 6.07 \| 22 | 1159 \| 1.38 / 11.78 / 3.19 \| 5.16 \| 23 | 1159 \| 1.99 / 16.29 / 4.53 \| 6.58 \| 21 |

### Table D-3 — paired by the category in `stock (c66)`: the same requests in every run; changes against `stock (c66)`

| category in the reference (n) | quantity | stock (c66) | shortest-prompt-first priority | shortest-prompt-first + P1 | bypass alone; 30 s |
|---|---|---|---|---|---|
| host-dominant hit (111) | TTFT p50 (s) | 6.57 | 3.11  -3.47 (-53 %) | 1.68  -4.90 (-74 %) | 3.26  -3.32 (-50 %) |
| host-dominant hit (111) | TTFT p95 (s) | 31.12 | 15.88  -15.24 (-49 %) | 7.14  -23.98 (-77 %) | 19.04  -12.08 (-39 %) |
| host-dominant hit (111) | TTFT mean (s) | 10.51 | 5.37  -5.15 (-49 %) | 2.12  -8.39 (-80 %) | 6.54  -3.97 (-38 %) |
| host-dominant hit (111) | request time p50 (s) | 10.96 | 6.34  -4.62 (-42 %) | 4.63  -6.33 (-58 %) | 6.45  -4.51 (-41 %) |
| host-dominant hit (111) | request time mean (s) | 13.20 | 8.91  -4.29 (-32 %) | 6.51  -6.70 (-51 %) | 9.60  -3.60 (-27 %) |
| host-dominant hit (111) | requests with TTFT lower / higher by > 10 % | – | 41 % / 5 % | 63 % / 4 % | 28 % / 5 % |
| GPU-prefix hit (578) | TTFT p50 (s) | 0.32 | 0.32  +0.00 (+1 %) | 0.34  +0.02 (+7 %) | 0.32  +0.00 (+0 %) |
| GPU-prefix hit (578) | TTFT p95 (s) | 13.37 | 7.63  -5.74 (-43 %) | 3.28  -10.09 (-75 %) | 10.55  -2.82 (-21 %) |
| GPU-prefix hit (578) | TTFT mean (s) | 2.86 | 1.82  -1.04 (-36 %) | 0.98  -1.87 (-66 %) | 2.46  -0.39 (-14 %) |
| GPU-prefix hit (578) | request time p50 (s) | 0.67 | 0.67  +0.00 (+0 %) | 0.69  +0.02 (+2 %) | 0.67  +0.00 (+0 %) |
| GPU-prefix hit (578) | request time mean (s) | 4.43 | 3.74  -0.68 (-15 %) | 3.11  -1.32 (-30 %) | 4.15  -0.28 (-6 %) |
| GPU-prefix hit (578) | requests with TTFT lower / higher by > 10 % | – | 15 % / 2 % | 31 % / 7 % | 4 % / 1 % |
| partial hit (123) | TTFT p50 (s) | 0.78 | 0.77  -0.01 (-1 %) | 0.78  -0.00 (-0 %) | 0.78  -0.01 (-1 %) |
| partial hit (123) | TTFT p95 (s) | 22.52 | 9.05  -13.47 (-60 %) | 7.22  -15.30 (-68 %) | 13.39  -9.13 (-41 %) |
| partial hit (123) | TTFT mean (s) | 4.65 | 2.33  -2.32 (-50 %) | 1.97  -2.68 (-58 %) | 3.47  -1.18 (-25 %) |
| partial hit (123) | request time p50 (s) | 11.27 | 11.23  -0.04 (-0 %) | 11.13  -0.14 (-1 %) | 11.27  -0.00 (-0 %) |
| partial hit (123) | request time mean (s) | 15.24 | 14.66  -0.58 (-4 %) | 14.90  -0.34 (-2 %) | 14.64  -0.60 (-4 %) |
| partial hit (123) | requests with TTFT lower / higher by > 10 % | – | 23 % / 1 % | 28 % / 10 % | 10 % / 3 % |
| miss (339) | TTFT p50 (s) | 5.45 | 5.17  -0.28 (-5 %) | 5.11  -0.34 (-6 %) | 5.29  -0.16 (-3 %) |
| miss (339) | TTFT p95 (s) | 26.54 | 23.25  -3.29 (-12 %) | 27.01  +0.48 (+2 %) | 24.14  -2.40 (-9 %) |
| miss (339) | TTFT mean (s) | 8.06 | 7.44  -0.63 (-8 %) | 7.75  -0.31 (-4 %) | 7.73  -0.33 (-4 %) |
| miss (339) | request time p50 (s) | 21.58 | 21.53  -0.05 (-0 %) | 21.80  +0.22 (+1 %) | 21.51  -0.07 (-0 %) |
| miss (339) | request time mean (s) | 23.72 | 23.68  -0.03 (-0 %) | 24.16  +0.44 (+2 %) | 23.47  -0.25 (-1 %) |
| miss (339) | requests with TTFT lower / higher by > 10 % | – | 10 % / 8 % | 13 % / 25 % | 5 % / 4 % |
| all requests (1159) | TTFT p50 (s) | 2.01 | 1.85  -0.15 (-8 %) | 1.38  -0.63 (-31 %) | 1.99  -0.02 (-1 %) |
| all requests (1159) | TTFT p95 (s) | 22.34 | 13.51  -8.84 (-40 %) | 11.78  -10.57 (-47 %) | 16.29  -6.05 (-27 %) |
| all requests (1159) | TTFT mean (s) | 5.37 | 3.88  -1.50 (-28 %) | 3.19  -2.19 (-41 %) | 4.53  -0.84 (-16 %) |
| all requests (1159) | request time p50 (s) | 7.07 | 6.07  -1.00 (-14 %) | 5.16  -1.91 (-27 %) | 6.58  -0.49 (-7 %) |
| all requests (1159) | request time mean (s) | 12.13 | 11.26  -0.87 (-7 %) | 10.87  -1.26 (-10 %) | 11.47  -0.67 (-5 %) |
| all requests (1159) | requests with TTFT lower / higher by > 10 % | – | 17 % / 4 % | 28 % / 12 % | 7 % / 2 % |

### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \| request time p50 (s)

| prompt tokens (n) | stock (c66) | shortest-prompt-first priority | shortest-prompt-first + P1 | bypass alone; 30 s |
|---|---|---|---|---|
| < 2,048 (112) | 0.88 / 27.53 / 35.67 \| 11.66 | 0.87 / 9.21 / 14.12 \| 11.66 | 0.89 / 4.50 / 8.85 \| 11.28 | 0.83 / 12.91 / 17.28 \| 11.66 |
| 2,048–8,191 (741) | 0.79 / 19.48 / 51.03 \| 2.10 | 0.79 / 9.25 / 16.60 \| 1.98 | 0.79 / 5.26 / 12.20 \| 1.88 | 0.80 / 13.35 / 22.05 \| 2.00 |
| ≥ 8,192 (306) | 6.01 / 28.15 / 51.73 \| 21.79 | 5.97 / 27.76 / 48.01 \| 21.94 | 5.56 / 27.85 / 51.17 \| 21.95 | 5.77 / 27.01 / 49.13 \| 21.66 |
| requests with TTFT > 30 s / > 60 s | 26 / 0 | 13 / 0 | 12 / 0 | 12 / 0 |
