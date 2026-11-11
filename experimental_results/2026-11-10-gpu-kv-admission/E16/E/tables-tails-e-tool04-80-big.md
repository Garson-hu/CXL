| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 112): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 306): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock | 25.7 / 35.9 | 4 / 0 | – | 0.85 / 18.2 | 5.97 / 22.8 | 0 | 1210 | 0.036 / 0.348 | 225.2 |
| P1 | 27.3 / 41.5 | 6 / 0 | 19 % / 16 % | 1.01 / 9.5 | 5.89 / 23.9 | 0 | 1209 | 0.036 / 0.349 | 225.0 |
| P1 + synchronous scheduling | 27.8 / 42.1 | 7 / 0 | 20 % / 23 % | 0.80 / 9.8 | 6.11 / 24.2 | 0 | 1209 | 0.036 / 0.349 | 225.0 |
