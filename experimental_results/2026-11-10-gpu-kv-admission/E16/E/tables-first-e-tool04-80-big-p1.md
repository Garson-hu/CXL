## First admission attempts of `e-tool04-80-big-p1` (pool 19916 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 42 | 0 | 0 / 42 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 1117 | 0 | 0 / 1104 | 0 / 13 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

- external load, admitted at the first attempt (42): blocks of the full sequence p50 / p90 = 534 / 1530; free blocks p10 / p50 15658 / 18539; smallest free / needed ratio 6.57
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1117): blocks of the full sequence p50 / p90 = 386 / 1158; free blocks p10 / p50 14443 / 18200; smallest free / needed ratio 3.80
- GPU-cached prefix at the first visit: 3414016 tokens over 1159 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `e-tool04-80-big-p1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 9 | 72 | 0 | 0.53 / 0.42 | 3, 0.02 | 6, 0.65 | 1.71 |
| 2k–4k | 7 | 248 | 0 | 0.02 / 0.14 | 5, 0.02 | 2, 0.57 | 0.30 |
| 4k–8k | 9 | 418 | 0 | 0.34 / 0.44 | 4, 0.02 | 5, 0.92 | 2.00 |
| ≥ 8k | 17 | 1243 | 0 | 0.29 / 0.33 | 8, 0.02 | 9, 0.50 | 1.41 |
