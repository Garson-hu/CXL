## First admission attempts of `e-tool08-120-big-priolen` (pool 19919 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 25 | 0 | 0 / 10 | 0 / 12 | 0 / 3 | 0 / 0 | 0 / 0 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 519 | 0 | 0 / 314 | 0 / 196 | 0 / 9 | 0 / 0 | 0 / 0 | 0 / 0 |

- external load, admitted at the first attempt (25): blocks of the full sequence p50 / p90 = 441 / 1674; free blocks p10 / p50 4208 / 8769; smallest free / needed ratio 4.94
- compute request (miss or GPU-prefix hit), admitted at the first attempt (519): blocks of the full sequence p50 / p90 = 222 / 1145; free blocks p10 / p50 7184 / 12447; smallest free / needed ratio 1.52
- GPU-cached prefix at the first visit: 1515808 tokens over 544 requests; 3 requests had lost part of it by the time they were admitted (5472 tokens, 0.4 %); 3 of them were then admitted as external loads

### External loads of `e-tool08-120-big-priolen` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 6 | 165 | 0 | 10.25 / 8.99 | 2, 5.62 | 4, 14.16 | 16.19 |
| 2k–4k | 7 | 198 | 0 | 6.37 / 8.37 | 1, 11.30 | 6, 6.37 | 8.47 |
| 4k–8k | 3 | 418 | 0 | 7.71 / 7.27 | 2, 8.41 | 1, 7.71 | 11.23 |
| ≥ 8k | 9 | 1030 | 0 | 4.04 / 7.49 | 6, 2.25 | 3, 19.86 | 10.74 |
