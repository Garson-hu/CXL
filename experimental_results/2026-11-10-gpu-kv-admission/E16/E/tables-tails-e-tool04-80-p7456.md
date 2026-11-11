| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 112): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 306): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock (c61) | 34.7 / 52.0 | 26 / 0 | – | 0.90 / 27.7 | 6.06 / 28.3 | 1 | 1214 | 0.071 / 0.311 | 204.3 |
| oracle hits-first priority | 33.7 / 48.5 | 18 / 0 | 12 % / 1 % | 0.90 / 20.1 | 6.05 / 27.8 | 2 | 1214 | 0.063 / 0.319 | 205.5 |
| shortest-prompt-first priority | 31.2 / 48.2 | 13 / 0 | 17 % / 3 % | 0.89 / 9.3 | 6.03 / 27.9 | 3 | 1218 | 0.061 / 0.319 | 206.0 |
| shortest-prompt-first + P1 | 32.0 / 51.2 | 12 / 0 | 29 % / 12 % | 0.92 / 4.5 | 5.60 / 28.1 | 4 | 1212 | 0.055 / 0.328 | 225.5 |
| P1 | 35.2 / 51.7 | 22 / 0 | 21 % / 15 % | 1.00 / 9.8 | 5.74 / 29.9 | 3 | 1212 | 0.060 / 0.323 | 225.5 |
| P4 | 32.0 / 51.8 | 14 / 0 | 24 % / 14 % | 0.92 / 8.9 | 5.73 / 28.6 | 4 | 1209 | 0.056 / 0.329 | 224.9 |
