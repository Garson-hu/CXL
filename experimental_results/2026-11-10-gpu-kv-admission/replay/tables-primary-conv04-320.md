| configuration | host-dominant hits (n = 65): TTFT p50 / mean (s) | GPU-prefix hits (n = 54): TTFT p50 / mean (s) | all requests: TTFT p50 / p95 / mean (s) | misses (n = 339): TTFT p50 / mean (s) | requests / s; output tokens / s | request time mean / p95 (s) | admission delay, mean (s): hits / misses | pool in use; time with < 25 % free; refused attempts | GPU busy: steps / NVML |
|---|---|---|---|---|---|---|---|---|---|
| stock | 0.79 / 5.45 | 0.16 / 4.75 | 3.46 / 27.0 / 6.32 | 5.15 / 7.52 | 0.120; 42.2 | 18.6 / 45.1 | 4.82 / 3.53 | 0.26; 0.10; 4966 | 0.49 / 0.49 |
| shortest-prompt-first priority | 0.81 / 5.03 (-8 %) | 0.16 / 1.84 (-61 %) | 3.09 / 17.4 / 5.34 (-15 %) | 4.84 / 7.01 (-7 %) | 0.120; 42.2 | 18.4 (-1 %) / 45.7 | 4.23 / 3.02 | 0.27; 0.10; 4400 | 0.50 / 0.50 |
| P4 | 0.71 / 1.90 (-65 %) | 0.17 / 0.81 (-83 %) | 2.44 / 16.8 / 5.00 (-21 %) | 4.96 / 7.37 (-2 %) | 0.120; 42.2 | 17.9 (-4 %) / 44.3 | 1.15 / 3.25 | 0.26; 0.10; 747 | 0.49 / 0.49 |
