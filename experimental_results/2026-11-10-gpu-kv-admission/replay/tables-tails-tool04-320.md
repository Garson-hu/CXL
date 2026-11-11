| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 112): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 306): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock | 34.0 / 43.9 | 28 / 0 | – | 0.59 / 28.0 | 5.22 / 28.7 | 1 | 1117 | 0.120 / 0.311 | 187.9 |
| oracle hits-first priority | 33.5 / 43.1 | 18 / 0 | 12 % / 1 % | 0.56 / 11.2 | 5.21 / 27.0 | 2 | 1119 | 0.110 / 0.321 | 190.0 |
| prototype v1.1 | 34.3 / 40.4 | 18 / 0 | 22 % / 13 % | 0.65 / 7.6 | 4.67 / 29.5 | 3 | 1088 | 0.119 / 0.327 | 202.5 |
| P2 | 34.6 / 40.4 | 18 / 0 | 21 % / 13 % | 0.64 / 9.8 | 4.73 / 29.8 | 3 | 1088 | 0.122 / 0.324 | 202.7 |
| P4 | 32.1 / 43.1 | 14 / 0 | 24 % / 12 % | 0.65 / 7.6 | 4.67 / 27.1 | 3 | 1088 | 0.118 / 0.328 | 202.4 |
