| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 121): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 321): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock | 34.2 / 40.6 | 15 / 0 | – | 0.23 / 27.6 | 5.36 / 27.2 | 2 | 1155 | 0.120 / 0.044 | 198.4 |
| shortest-prompt-first priority | 36.3 / 45.0 | 12 / 0 | 12 % / 4 % | 0.23 / 8.4 | 5.42 / 24.8 | 3 | 1162 | 0.115 / 0.044 | 199.2 |
| P4 | 36.9 / 44.1 | 12 / 0 | 16 % / 9 % | 0.24 / 4.3 | 4.95 / 23.7 | 4 | 1131 | 0.137 / 0.044 | 212.2 |
