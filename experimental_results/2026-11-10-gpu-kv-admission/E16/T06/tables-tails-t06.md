| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 86): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 236): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock (c73) | 52.5 / 61.2 | 78 / 2 | – | 3.28 / 39.8 | 8.57 / 41.6 | 3 | 1837 | 0.096 / 0.264 | 148.3 |
| oracle hits-first priority | 46.0 / 65.7 | 40 / 1 | 20 % / 4 % | 2.24 / 14.5 | 8.39 / 39.7 | 3 | 1835 | 0.094 / 0.267 | 147.3 |
| shortest-prompt-first priority | 39.1 / 151.0 | 17 / 2 | 30 % / 7 % | 1.65 / 9.9 | 7.42 / 35.1 | 4 | 1828 | 0.096 / 0.268 | 148.9 |
| bypass alone; 30 s | 43.8 / 64.3 | 21 / 1 | 16 % / 7 % | 3.29 / 15.2 | 8.58 / 39.9 | 7 | 1851 | 0.083 / 0.273 | 177.6 |
| P2 | 54.5 / 62.7 | 61 / 3 | 30 % / 25 % | 1.22 / 23.7 | 9.48 / 45.4 | 7 | 1846 | 0.065 / 0.290 | 177.7 |
| P4 | 47.1 / 64.5 | 44 / 5 | 33 % / 25 % | 1.19 / 11.9 | 9.39 / 43.1 | 9 | 1844 | 0.057 / 0.298 | 177.3 |
