| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 60): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 144): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock | 43.0 / 46.1 | 57 / 0 | – | 10.42 / 37.5 | 13.62 / 36.9 | 0 | 2287 | 0.037 / 0.331 | 109.0 |
| shortest-prompt-first priority | 39.3 / 61.8 | 20 / 1 | 37 % / 11 % | 3.44 / 15.0 | 12.85 / 38.1 | 0 | 2287 | 0.038 / 0.330 | 109.0 |
| P1 | 61.2 / 68.5 | 127 / 8 | 20 % / 54 % | 2.99 / 56.6 | 18.64 / 53.0 | 0 | 2235 | 0.041 / 0.327 | 108.8 |
