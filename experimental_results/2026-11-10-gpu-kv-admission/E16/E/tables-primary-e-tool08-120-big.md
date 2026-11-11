| configuration | host-dominant hits (n = 17): TTFT p50 / mean (s) | GPU-prefix hits (n = 299): TTFT p50 / mean (s) | all requests: TTFT p50 / p95 / mean (s) | misses (n = 164): TTFT p50 / mean (s) | requests / s; output tokens / s | request time mean / p95 (s) | admission delay, mean (s): hits / misses | pool in use; time with < 25 % free; refused attempts | GPU busy: steps / NVML |
|---|---|---|---|---|---|---|---|---|---|
| stock | 15.42 / 16.11 | 9.15 / 11.84 | 10.42 / 36.4 / 12.72 | 12.22 / 14.53 | 0.427; 88.1 | 32.4 / 100.5 | 15.27 / 9.85 | 0.35; 0.04; 0 | 0.87 / 0.87 |
| shortest-prompt-first priority | 10.74 / 11.78 (-27 %) | 5.29 / 6.85 (-42 %) | 6.25 / 26.3 / 8.77 (-31 %) | 9.88 / 13.25 (-9 %) | 0.427; 88.1 | 29.1 (-10 %) / 96.0 | 10.83 / 8.56 | 0.35; 0.04; 0 | 0.87 / 0.87 |
| P1 | 6.92 / 9.84 (-39 %) | 5.60 / 13.81 (+17 %) | 12.43 / 47.0 / 16.44 (+29 %) | 18.52 / 21.74 (+50 %) | 0.417; 86.1 | 39.4 (+22 %) / 123.5 | 9.06 / 16.41 | 0.40; 0.06; 0 | 0.90 / 0.90 |
