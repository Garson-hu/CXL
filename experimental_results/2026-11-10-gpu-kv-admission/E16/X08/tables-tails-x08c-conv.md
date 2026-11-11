| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 62): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 153): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock (c60) | 52.3 / 54.5 | 59 / 0 | – | 11.70 / 40.5 | 15.76 / 44.2 | 5 | 2392 | 0.031 / 0.044 | 76.6 |
| shortest-prompt-first priority | 146.7 / 314.8 | 21 / 7 | 48 % / 14 % | 1.98 / 8.9 | 10.77 / 56.9 | 5 | 2365 | 0.028 / 0.044 | 73.2 |
| bypass alone; 30 s | 55.8 / 60.8 | 34 / 1 | 29 % / 10 % | 3.25 / 18.7 | 13.79 / 49.4 | 6 | 2368 | 0.048 / 0.044 | 114.1 |
| P2 | 62.5 / 67.2 | 69 / 7 | 13 % / 44 % | 1.76 / 52.6 | 16.33 / 52.6 | 8 | 2345 | 0.048 / 0.044 | 114.2 |
| P4 | 63.3 / 64.8 | 49 / 5 | 26 % / 38 % | 1.50 / 52.5 | 15.35 / 53.5 | 11 | 2344 | 0.048 / 0.044 | 114.1 |
