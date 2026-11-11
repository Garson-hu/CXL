| configuration | TTFT p99 / longest (s) | requests with TTFT > 30 s / > 60 s | requests faster / slower than in stock by > 10 % | prompts < 2,048 tokens (n = 60): TTFT p50 / p95 (s) | prompts ≥ 8,192 tokens (n = 144): TTFT p50 / p95 (s) | preemptions | prompt tokens computed / s | cached share: host tier / GPU prefix | GB stored |
|---|---|---|---|---|---|---|---|---|---|
| stock (c61) | 45.6 / 51.9 | 70 / 0 | – | 10.84 / 40.4 | 14.23 / 42.6 | 5 | 2326 | 0.111 / 0.244 | 75.1 |
| shortest-prompt-first priority | 65.0 / 259.3 | 19 / 6 | 54 % / 16 % | 1.56 / 14.4 | 10.66 / 40.0 | 6 | 2340 | 0.109 / 0.239 | 71.4 |
| oracle shortest-compute-first priority | 64.5 / 228.4 | 18 / 6 | 53 % / 12 % | 1.98 / 7.7 | 11.63 / 40.0 | 2 | 2337 | 0.099 / 0.251 | 71.0 |
| shortest-prompt-first with aging; 1 ms per token | 48.6 / 52.1 | 22 / 0 | 40 % / 12 % | 2.58 / 17.5 | 14.05 / 44.8 | 3 | 2339 | 0.095 / 0.256 | 73.0 |
| bypass alone; 3 s | 46.4 / 55.8 | 53 / 0 | 19 % / 10 % | 6.28 / 34.6 | 14.79 / 43.9 | 4 | 2299 | 0.133 / 0.235 | 109.0 |
| v1.2 (P1 without blkfirst) | 57.3 / 65.7 | 58 / 4 | 36 % / 40 % | 1.72 / 51.0 | 16.79 / 53.0 | 6 | 2268 | 0.138 / 0.230 | 108.9 |
| P1 + starvation bound 20 s | 50.5 / 55.4 | 82 / 0 | 22 % / 42 % | 3.15 / 39.0 | 17.33 / 44.3 | 6 | 2277 | 0.133 / 0.235 | 109.0 |
| P2 + synchronous scheduling | 66.0 / 76.8 | 90 / 6 | 26 % / 51 % | 1.23 / 59.4 | 20.18 / 57.5 | 14 | 2241 | 0.123 / 0.244 | 108.9 |
