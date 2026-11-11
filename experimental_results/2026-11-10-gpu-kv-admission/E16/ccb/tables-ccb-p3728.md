| scenario | configuration | pool in use | hits: TTFT p50 / p95 (s) | misses: TTFT p50 / p95 (s) | requests / s | request time, mean (s) |
|---|---|---|---|---|---|---|
| closed loop, 16 in the system | stock | 0.80 | 3.04 / 7.55 | 2.49 / 7.15 | 2.33 | 6.79 |
| closed loop, 16 in the system | P2 | 0.75 | 1.16 / 2.40 | 3.72 / 8.86 | 2.28 | 6.83 |
| closed loop, 16 in the system | P4 | 0.80 | 1.28 / 2.35 | 4.17 / 9.54 | 2.25 | 7.02 |
| closed loop, 16 in the system | bypass alone, 30 s | 0.79 | 3.34 / 8.71 | 2.74 / 7.33 | 2.34 | 6.76 |
| open loop, 2 requests/s | stock | 0.37 | 1.03 / 2.92 | 1.07 / 2.35 | 2.05 | 2.76 |
| open loop, 2 requests/s | P2 | 0.41 | 1.02 / 1.93 | 1.06 / 2.85 | 2.05 | 2.89 |
| open loop, 2 requests/s | P4 | 0.40 | 1.01 / 1.85 | 0.97 / 2.76 | 2.05 | 2.80 |
| open loop, 2 requests/s | bypass alone, 30 s | 0.36 | 1.02 / 2.89 | 0.88 / 2.25 | 2.05 | 2.63 |
| open loop, 4 requests/s | stock | 0.75 | 6.01 / 11.65 | 5.74 / 10.69 | 2.73 | 8.31 |
| open loop, 4 requests/s | P2 | 0.78 | 2.19 / 7.02 | 7.15 / 11.63 | 2.66 | 7.49 |
| open loop, 4 requests/s | P4 | 0.77 | 1.50 / 2.98 | 4.78 / 12.14 | 2.66 | 6.75 |
| open loop, 4 requests/s | bypass alone, 30 s | 0.74 | 3.00 / 6.41 | 4.35 / 11.84 | 2.72 | 7.03 |
| bursts of 16 | stock | 0.54 | 3.52 / 8.08 | 2.89 / 7.81 | 1.45 | 6.12 |
| bursts of 16 | P2 | 0.49 | 1.32 / 3.28 | 3.02 / 8.08 | 1.42 | 5.58 |
| bursts of 16 | P4 | 0.49 | 1.58 / 3.23 | 3.03 / 8.22 | 1.42 | 5.67 |
| bursts of 16 | bypass alone, 30 s | 0.55 | 3.21 / 6.92 | 2.88 / 7.38 | 1.44 | 6.05 |

Whole run: refused admission attempts / preemptions — stock 256 / 8; P2 180 / 3; P4 6 / 2; bypass alone, 30 s 47 / 7
