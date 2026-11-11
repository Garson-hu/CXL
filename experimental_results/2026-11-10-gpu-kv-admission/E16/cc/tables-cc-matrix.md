| scenario | quantity (stock → P1 / P2) | pool 14,912 blocks | pool 7,456 blocks | pool 3,728 blocks | pool 2,560 blocks |
|---|---|---|---|---|---|
| closed loop, 16 in the system | external hits: TTFT p50 (s) | 3.37 → 1.17 / 1.17 | 3.43 → 1.18 / 1.17 | 3.27 → 1.19 / 1.14 | 4.37 → 1.23 / 1.15 |
| closed loop, 16 in the system | misses: TTFT p50 (s) | 3.03 → 3.34 / 3.34 | 3.08 → 3.39 / 3.40 | 2.34 → 3.06 / 3.50 | 4.30 → 7.19 / 7.23 |
| closed loop, 16 in the system | completed requests / s | 2.42 → 2.31 / 2.31 | 2.38 → 2.27 / 2.27 | 2.36 → 2.31 / 2.31 | 2.38 → 2.34 / 2.34 |
| closed loop, 16 in the system | request time, mean (s) | 6.57 → 6.85 / 6.85 | 6.67 → 6.94 / 6.94 | 6.70 → 6.75 / 6.76 | 6.52 → 6.37 / 6.39 |
| closed loop, 16 in the system | pool in use, measured: stock / P1 / P2 | 0.21 / 0.22 / 0.22 | 0.42 / 0.45 / 0.45 | 0.80 / 0.77 / 0.77 | 0.82 / 0.75 / 0.77 |
| open loop, 2 requests/s | external hits: TTFT p50 (s) | 0.90 → 0.89 / 0.89 | 0.94 → 0.93 / 0.94 | 0.99 → 0.94 / 0.93 | 0.92 → 0.92 / 0.72 |
| open loop, 2 requests/s | misses: TTFT p50 (s) | 0.92 → 1.03 / 1.02 | 1.00 → 1.07 / 1.08 | 1.01 → 1.06 / 1.06 | 1.00 → 1.00 / 0.97 |
| open loop, 2 requests/s | completed requests / s | 2.06 → 2.06 / 2.06 | 2.05 → 2.05 / 2.05 | 2.05 → 2.05 / 2.05 | 2.06 → 2.05 / 2.05 |
| open loop, 2 requests/s | request time, mean (s) | 2.37 → 2.54 / 2.55 | 2.47 → 2.81 / 2.81 | 2.55 → 2.72 / 2.68 | 2.20 → 2.28 / 2.23 |
| open loop, 2 requests/s | pool in use, measured: stock / P1 / P2 | 0.08 / 0.09 / 0.09 | 0.17 / 0.20 / 0.20 | 0.35 / 0.39 / 0.38 | 0.41 / 0.45 / 0.45 |
| open loop, 4 requests/s | external hits: TTFT p50 (s) | 5.91 → 1.73 / 1.84 | 6.40 → 1.81 / 2.16 | 5.73 → 5.44 / 2.15 | 5.66 → 5.44 / 1.40 |
| open loop, 4 requests/s | misses: TTFT p50 (s) | 5.39 → 6.96 / 6.94 | 5.42 → 7.03 / 7.15 | 5.55 → 6.30 / 6.47 | 5.63 → 5.95 / 6.31 |
| open loop, 4 requests/s | completed requests / s | 2.79 → 2.67 / 2.67 | 2.75 → 2.66 / 2.64 | 2.76 → 2.68 / 2.67 | 2.76 → 2.72 / 2.72 |
| open loop, 4 requests/s | request time, mean (s) | 8.85 → 8.07 / 8.13 | 9.20 → 8.06 / 8.36 | 8.09 → 8.26 / 7.77 | 6.99 → 7.21 / 6.02 |
| open loop, 4 requests/s | pool in use, measured: stock / P1 / P2 | 0.24 / 0.23 / 0.23 | 0.48 / 0.45 / 0.49 | 0.75 / 0.76 / 0.76 | 0.77 / 0.79 / 0.73 |
| bursts of 16 | external hits: TTFT p50 (s) | 3.03 → 1.21 / 1.30 | 3.57 → 1.45 / 1.20 | 3.45 → 1.18 / 1.16 | 3.40 → 1.26 / 1.34 |
| bursts of 16 | misses: TTFT p50 (s) | 2.78 → 3.00 / 3.01 | 2.77 → 2.96 / 2.94 | 2.85 → 2.95 / 2.95 | 3.28 → 3.24 / 2.99 |
| bursts of 16 | completed requests / s | 1.40 → 1.38 / 1.38 | 1.52 → 1.50 / 1.51 | 1.52 → 1.50 / 1.50 | 1.50 → 1.49 / 1.49 |
| bursts of 16 | request time, mean (s) | 6.15 → 6.31 / 6.32 | 6.12 → 6.27 / 6.28 | 6.05 → 5.47 / 5.50 | 5.29 → 4.61 / 4.62 |
| bursts of 16 | pool in use, measured: stock / P1 / P2 | 0.14 / 0.16 / 0.17 | 0.31 / 0.29 / 0.34 | 0.52 / 0.51 / 0.52 | 0.50 / 0.51 / 0.50 |
| whole run | refused admission attempts: stock / P1 / P2 | 0 / 0 / 0 | 0 / 0 / 0 | 256 / 300 / 175 | 747 / 777 / 401 |
| whole run | preemptions: stock / P1 / P2 | 0 / 0 / 0 | 0 / 0 / 0 | 7 / 3 / 3 | 0 / 0 / 0 |
