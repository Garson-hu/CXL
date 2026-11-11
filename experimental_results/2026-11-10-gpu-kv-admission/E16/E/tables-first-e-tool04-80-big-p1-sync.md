## First admission attempts of `e-tool04-80-big-p1-sync` (pool 19916 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 42 | 0 | 0 / 42 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 1117 | 0 | 0 / 1104 | 0 / 13 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

- external load, admitted at the first attempt (42): blocks of the full sequence p50 / p90 = 534 / 1530; free blocks p10 / p50 15818 / 18390; smallest free / needed ratio 6.61
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1117): blocks of the full sequence p50 / p90 = 387 / 1158; free blocks p10 / p50 14449 / 18121; smallest free / needed ratio 3.80
- GPU-cached prefix at the first visit: 3414016 tokens over 1159 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `e-tool04-80-big-p1-sync` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 9 | 72 | 0 | 0.26 / 0.24 | 3, 0.02 | 6, 0.33 | 1.01 |
| 2k–4k | 7 | 248 | 0 | 0.03 / 0.10 | 5, 0.03 | 2, 0.34 | 0.29 |
| 4k–8k | 9 | 418 | 0 | 0.27 / 0.24 | 4, 0.02 | 5, 0.36 | 1.19 |
| ≥ 8k | 17 | 1243 | 0 | 0.22 / 0.20 | 8, 0.03 | 9, 0.35 | 1.17 |
