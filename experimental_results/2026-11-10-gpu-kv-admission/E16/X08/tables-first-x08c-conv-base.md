## First admission attempts of `x08c-conv-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 14 | 6 | 0 / 3 | 0 / 3 | 0 / 1 | 2 / 2 | 2 / 3 | 2 / 2 |
| compute request (miss or GPU-prefix hit) | 277 | 73 | 0 / 93 | 0 / 37 | 15 / 61 | 18 / 32 | 23 / 36 | 17 / 18 |

- external load, refused at the first attempt (6): blocks of the full sequence p10 / p50 / p90 = 100 / 871 / 1030; free blocks 84 / 277 / 611; needed / free p50 1.89; used share of the pool p10 / p50 0.918 / 0.976; gate {'full': 6}
- external load, admitted at the first attempt (8): blocks of the full sequence p50 / p90 = 565 / 2005; free blocks p10 / p50 253 / 3000; smallest free / needed ratio 1.14
- compute request (miss or GPU-prefix hit), refused at the first attempt (73): blocks of the full sequence p10 / p50 / p90 = 347 / 1013 / 1982; free blocks 76 / 349 / 968; needed / free p50 2.19; used share of the pool p10 / p50 0.870 / 0.953; gate {'full': 73}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (204): blocks of the full sequence p50 / p90 = 378 / 1415; free blocks p10 / p50 561 / 3088; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 148480 tokens over 291 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `x08c-conv-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 2 | 100 | 1 | 22.96 / 18.45 | – | 2, 22.96 | 25.45 |
| 2k–4k | 3 | 165 | 1 | 24.11 / 18.94 | 1, 31.09 | 2, 24.11 | 26.84 |
| 4k–8k | 2 | 458 | 1 | 29.31 / 18.14 | 1, 29.31 | 1, 6.98 | 29.72 |
| ≥ 8k | 7 | 921 | 4 | 20.35 / 14.36 | 3, 0.18 | 4, 24.98 | 21.25 |
