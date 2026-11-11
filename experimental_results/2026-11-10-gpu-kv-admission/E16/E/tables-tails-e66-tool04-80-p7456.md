| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 112): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 306): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock (c66) | 34.5 / 51.7 | 26 / 0 | – | 0.88 / 27.5 | 6.01 / 28.2 | 1 | 1214 | 0.071 / 0.311 | 204.3 |
| shortest-prompt-first priority | 31.0 / 48.0 | 13 / 0 | 17 % / 4 % | 0.87 / 9.2 | 5.97 / 27.8 | 3 | 1218 | 0.060 / 0.320 | 206.2 |
| shortest-prompt-first + P1 | 31.8 / 51.2 | 12 / 0 | 28 % / 12 % | 0.89 / 4.5 | 5.56 / 27.8 | 4 | 1212 | 0.054 / 0.329 | 225.5 |
| bypass alone; 30 s | 31.1 / 49.1 | 12 / 0 | 7 % / 2 % | 0.83 / 12.9 | 5.77 / 27.0 | 3 | 1210 | 0.066 / 0.318 | 225.1 |
