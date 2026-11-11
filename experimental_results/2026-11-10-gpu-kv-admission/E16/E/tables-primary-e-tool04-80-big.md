| configuration | host-dominant hits (n = 30): TTFT p50 / mean (s) | GPU-prefix hits (n = 661): TTFT p50 / mean (s) | all requests: TTFT p50 / p95 / mean (s) | misses (n = 340): TTFT p50 / mean (s) | requests / s; output tokens / s | request time mean / p95 (s) | admission delay, mean (s): hits / misses | pool in use; time with < 25 % free; refused attempts | GPU busy: steps / NVML |
|---|---|---|---|---|---|---|---|---|---|
| stock | 1.96 / 7.39 | 0.42 / 3.48 | 2.03 / 18.1 / 4.80 | 5.34 / 7.27 | 0.233; 44.0 | 12.5 / 43.6 | 6.71 / 3.17 | 0.11; 0.00; 0 | 0.50 / 0.49 |
| P1 | 1.41 / 1.38 (-81 %) | 0.47 / 1.68 (-52 %) | 1.38 / 17.6 / 3.81 (-21 %) | 5.67 / 8.04 (+11 %) | 0.233; 44.0 | 11.9 (-5 %) / 45.0 | 0.82 / 3.68 | 0.11; 0.00; 0 | 0.50 / 0.50 |
| P1 + synchronous scheduling | 1.07 / 1.03 (-86 %) | 0.51 / 1.64 (-53 %) | 1.09 / 18.4 / 3.84 (-20 %) | 6.04 / 8.23 (+13 %) | 0.233; 44.0 | 12.5 (-0 %) / 46.2 | 0.53 / 3.96 | 0.11; 0.00; 0 | 0.51 / 0.50 |
