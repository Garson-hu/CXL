| scenario | quantity (stock → P2 / P4 / bypass alone, 30 s) | pool 3,728 blocks | pool 2,560 blocks |
|---|---|---|---|
| closed loop, 16 in the system | external hits: TTFT p50 (s) | 3.04 → 1.16 / 1.28 / 3.34 | 4.49 → 1.19 / 1.23 / 3.31 |
| closed loop, 16 in the system | misses: TTFT p50 (s) | 2.49 → 3.72 / 4.17 / 2.74 | 4.43 → 7.47 / 4.15 / 4.13 |
| closed loop, 16 in the system | completed requests / s | 2.33 → 2.28 / 2.25 / 2.34 | 2.31 → 2.27 / 2.27 / 2.32 |
| closed loop, 16 in the system | request time, mean (s) | 6.79 → 6.83 / 7.02 / 6.76 | 6.71 → 6.58 / 6.30 / 6.53 |
| closed loop, 16 in the system | pool in use, measured: stock / P2 / P4 / bypass alone, 30 s | 0.80 / 0.75 / 0.80 / 0.79 | 0.82 / 0.77 / 0.85 / 0.81 |
| open loop, 2 requests/s | external hits: TTFT p50 (s) | 1.03 → 1.02 / 1.01 / 1.02 | 1.02 → 1.00 / 0.92 / 0.95 |
| open loop, 2 requests/s | misses: TTFT p50 (s) | 1.07 → 1.06 / 0.97 / 0.88 | 1.08 → 1.16 / 1.14 / 0.96 |
| open loop, 2 requests/s | completed requests / s | 2.05 → 2.05 / 2.05 / 2.05 | 2.05 → 2.05 / 2.05 / 2.05 |
| open loop, 2 requests/s | request time, mean (s) | 2.76 → 2.89 / 2.80 / 2.63 | 2.48 → 2.46 / 2.44 / 2.37 |
| open loop, 2 requests/s | pool in use, measured: stock / P2 / P4 / bypass alone, 30 s | 0.37 / 0.41 / 0.40 / 0.36 | 0.46 / 0.48 / 0.47 / 0.45 |
| open loop, 4 requests/s | external hits: TTFT p50 (s) | 6.01 → 2.19 / 1.50 / 3.00 | 6.12 → 1.69 / 1.24 / 1.65 |
| open loop, 4 requests/s | misses: TTFT p50 (s) | 5.74 → 7.15 / 4.78 / 4.35 | 6.18 → 6.75 / 5.54 / 3.87 |
| open loop, 4 requests/s | completed requests / s | 2.73 → 2.66 / 2.66 / 2.72 | 2.70 → 2.65 / 2.67 / 2.70 |
| open loop, 4 requests/s | request time, mean (s) | 8.31 → 7.49 / 6.75 / 7.03 | 7.48 → 6.70 / 5.43 / 5.45 |
| open loop, 4 requests/s | pool in use, measured: stock / P2 / P4 / bypass alone, 30 s | 0.75 / 0.78 / 0.77 / 0.74 | 0.77 / 0.75 / 0.75 / 0.79 |
| bursts of 16 | external hits: TTFT p50 (s) | 3.52 → 1.32 / 1.58 / 3.21 | 3.18 → 1.43 / 1.28 / 3.53 |
| bursts of 16 | misses: TTFT p50 (s) | 2.89 → 3.02 / 3.03 / 2.88 | 3.40 → 3.07 / 3.42 / 3.39 |
| bursts of 16 | completed requests / s | 1.45 → 1.42 / 1.42 / 1.44 | 1.40 → 1.41 / 1.40 / 1.42 |
| bursts of 16 | request time, mean (s) | 6.12 → 5.58 / 5.67 / 6.05 | 5.61 → 4.84 / 4.82 / 5.32 |
| bursts of 16 | pool in use, measured: stock / P2 / P4 / bypass alone, 30 s | 0.54 / 0.49 / 0.49 / 0.55 | 0.50 / 0.50 / 0.49 / 0.49 |
| whole run | refused admission attempts: stock / P2 / P4 / bypass alone, 30 s | 256 / 180 / 6 / 47 | 755 / 354 / 0 / 0 |
| whole run | preemptions: stock / P2 / P4 / bypass alone, 30 s | 8 / 3 / 2 / 7 | 0 / 0 / 0 / 0 |
