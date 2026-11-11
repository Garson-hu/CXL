| scenario | configuration | pool in use | hits: TTFT p50 / p95 (s) | misses: TTFT p50 / p95 (s) | requests / s | request time, mean (s) |
|---|---|---|---|---|---|---|
| closed loop, 16 in the system | stock | 0.42 | 3.43 / 8.29 | 3.08 / 6.98 | 2.38 | 6.67 |
| closed loop, 16 in the system | synchronous scheduling | 0.41 | 2.47 / 7.12 | 2.26 / 6.77 | 2.34 | 6.79 |
| closed loop, 16 in the system | prefill cap 1,024 | 0.43 | 3.25 / 7.44 | 3.28 / 6.80 | 2.37 | 6.70 |
| closed loop, 16 in the system | hits-first priority (client-labelled) | 0.45 | 3.30 / 4.81 | 3.34 / 6.95 | 2.38 | 6.68 |
| closed loop, 16 in the system | P1 | 0.45 | 1.18 / 1.84 | 3.39 / 7.39 | 2.27 | 6.94 |
| closed loop, 16 in the system | P2 | 0.45 | 1.17 / 1.91 | 3.40 / 7.40 | 2.27 | 6.94 |
| open loop, 2 requests/s | stock | 0.17 | 0.94 / 3.06 | 1.00 / 2.23 | 2.05 | 2.47 |
| open loop, 2 requests/s | synchronous scheduling | 0.18 | 0.94 / 2.77 | 1.05 / 2.30 | 2.05 | 2.70 |
| open loop, 2 requests/s | prefill cap 1,024 | 0.18 | 0.93 / 2.30 | 1.01 / 2.34 | 2.05 | 2.52 |
| open loop, 2 requests/s | hits-first priority (client-labelled) | 0.17 | 0.93 / 2.78 | 0.99 / 2.22 | 2.05 | 2.46 |
| open loop, 2 requests/s | P1 | 0.20 | 0.93 / 1.86 | 1.07 / 2.77 | 2.05 | 2.81 |
| open loop, 2 requests/s | P2 | 0.20 | 0.94 / 1.86 | 1.08 / 2.77 | 2.05 | 2.81 |
| open loop, 4 requests/s | stock | 0.48 | 6.40 / 11.47 | 5.42 / 10.31 | 2.75 | 9.20 |
| open loop, 4 requests/s | synchronous scheduling | 0.47 | 6.21 / 11.54 | 5.73 / 10.80 | 2.71 | 9.51 |
| open loop, 4 requests/s | prefill cap 1,024 | 0.50 | 6.12 / 11.26 | 5.42 / 9.92 | 2.76 | 9.04 |
| open loop, 4 requests/s | hits-first priority (client-labelled) | 0.47 | 2.93 / 4.24 | 5.68 / 10.40 | 2.77 | 7.66 |
| open loop, 4 requests/s | P1 | 0.45 | 1.81 / 4.74 | 7.03 / 11.89 | 2.66 | 8.06 |
| open loop, 4 requests/s | P2 | 0.49 | 2.16 / 4.15 | 7.15 / 11.91 | 2.64 | 8.36 |
| bursts of 16 | stock | 0.31 | 3.57 / 7.56 | 2.77 / 7.30 | 1.52 | 6.12 |
| bursts of 16 | synchronous scheduling | 0.27 | 3.10 / 7.67 | 2.89 / 7.56 | 1.51 | 6.24 |
| bursts of 16 | prefill cap 1,024 | 0.30 | 2.92 / 7.54 | 3.57 / 7.49 | 1.53 | 6.12 |
| bursts of 16 | hits-first priority (client-labelled) | 0.33 | 1.84 / 3.99 | 3.48 / 7.59 | 1.51 | 6.22 |
| bursts of 16 | P1 | 0.29 | 1.45 / 3.35 | 2.96 / 7.79 | 1.50 | 6.27 |
| bursts of 16 | P2 | 0.34 | 1.20 / 3.50 | 2.94 / 7.87 | 1.51 | 6.28 |

Whole run: refused admission attempts / preemptions — stock 0 / 0; synchronous scheduling 0 / 0; prefill cap 1,024 0 / 0; hits-first priority (client-labelled) 0 / 0; P1 0 / 0; P2 0 / 0
