| scenario | configuration | pool in use | hits: TTFT p50 / p95 (s) | misses: TTFT p50 / p95 (s) | requests / s | request time, mean (s) |
|---|---|---|---|---|---|---|
| closed loop, 16 in the system | stock | 0.82 | 4.49 / 7.19 | 4.43 / 7.07 | 2.31 | 6.71 |
| closed loop, 16 in the system | P2 | 0.77 | 1.19 / 2.18 | 7.47 / 11.07 | 2.27 | 6.58 |
| closed loop, 16 in the system | P4 | 0.85 | 1.23 / 2.33 | 4.15 / 12.72 | 2.27 | 6.30 |
| closed loop, 16 in the system | bypass alone, 30 s | 0.81 | 3.31 / 6.14 | 4.13 / 9.37 | 2.32 | 6.53 |
| open loop, 2 requests/s | stock | 0.46 | 1.02 / 2.85 | 1.08 / 2.51 | 2.05 | 2.48 |
| open loop, 2 requests/s | P2 | 0.48 | 1.00 / 2.06 | 1.16 / 2.70 | 2.05 | 2.46 |
| open loop, 2 requests/s | P4 | 0.47 | 0.92 / 1.95 | 1.14 / 3.05 | 2.05 | 2.44 |
| open loop, 2 requests/s | bypass alone, 30 s | 0.45 | 0.95 / 2.48 | 0.96 / 2.24 | 2.05 | 2.37 |
| open loop, 4 requests/s | stock | 0.77 | 6.12 / 11.81 | 6.18 / 11.19 | 2.70 | 7.48 |
| open loop, 4 requests/s | P2 | 0.75 | 1.69 / 10.98 | 6.75 / 10.96 | 2.65 | 6.70 |
| open loop, 4 requests/s | P4 | 0.75 | 1.24 / 2.22 | 5.54 / 12.23 | 2.67 | 5.43 |
| open loop, 4 requests/s | bypass alone, 30 s | 0.79 | 1.65 / 3.94 | 3.87 / 11.94 | 2.70 | 5.45 |
| bursts of 16 | stock | 0.50 | 3.18 / 8.01 | 3.40 / 8.00 | 1.40 | 5.61 |
| bursts of 16 | P2 | 0.50 | 1.43 / 4.59 | 3.07 / 8.25 | 1.41 | 4.84 |
| bursts of 16 | P4 | 0.49 | 1.28 / 3.63 | 3.42 / 8.32 | 1.40 | 4.82 |
| bursts of 16 | bypass alone, 30 s | 0.49 | 3.53 / 5.63 | 3.39 / 7.67 | 1.42 | 5.32 |

Whole run: refused admission attempts / preemptions — stock 755 / 0; P2 354 / 0; P4 0 / 0; bypass alone, 30 s 0 / 0
