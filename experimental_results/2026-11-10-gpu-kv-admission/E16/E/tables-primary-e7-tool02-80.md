| configuration | host-dominant hits (n = 25): TTFT p50 / mean (s) | GPU-prefix hits (n = 278): TTFT p50 / mean (s) | all requests: TTFT p50 / p95 / mean (s) | misses (n = 175): TTFT p50 / mean (s) | requests / s; output tokens / s | request time mean / p95 (s) | admission delay, mean (s): hits / misses | pool in use; time with < 25 % free; refused attempts | GPU busy: steps / NVML |
|---|---|---|---|---|---|---|---|---|---|
| stock | 14.44 / 16.49 | 0.64 / 4.74 | 3.69 / 32.6 / 8.44 | 9.62 / 14.00 | 0.108; 22.3 | 22.7 / 80.0 | 15.18 / 6.37 | 0.22; 0.06; 1277 | 0.47 / 0.47 |
| P1 | 3.70 / 5.76 (-65 %) | 0.70 / 2.34 (-51 %) | 2.64 / 29.8 / 6.97 (-17 %) | 10.39 / 14.80 (+6 %) | 0.108; 22.3 | 21.8 (-4 %) / 80.1 | 4.41 / 6.78 | 0.22; 0.06; 1245 | 0.47 / 0.47 |
