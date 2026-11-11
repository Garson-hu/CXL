| configuration | host-dominant hits (n = 11): TTFT p50 / mean (s) | GPU-prefix hits (n = 28): TTFT p50 / mean (s) | all requests: TTFT p50 / p95 / mean (s) | misses (n = 186): TTFT p50 / mean (s) | requests / s; output tokens / s | request time mean / p95 (s) | admission delay, mean (s): hits / misses | pool in use; time with < 25 % free; refused attempts | GPU busy: steps / NVML |
|---|---|---|---|---|---|---|---|---|---|
| stock | 25.23 / 19.34 | 12.88 / 15.33 | 14.43 / 41.8 / 16.89 | 15.33 / 18.10 | 0.225; 83.6 | 39.9 / 83.4 | 18.77 / 13.75 | 0.61; 0.51; 6363 | 0.88 / 0.88 |
| P2 | 4.78 / 9.80 (-49 %) | 1.42 / 7.63 (-50 %) | 13.34 / 51.8 / 17.90 (+6 %) | 16.20 / 20.76 (+15 %) | 0.225; 83.5 | 42.4 (+6 %) / 91.3 | 8.83 / 16.24 | 0.63; 0.55; 6922 | 0.88 / 0.88 |
