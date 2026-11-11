## First admission attempts of `x08-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 125 | 47 | 0 / 10 | 0 / 15 | 2 / 31 | 4 / 21 | 24 / 31 | 17 / 17 |
| compute request (miss or GPU-prefix hit) | 419 | 77 | 0 / 165 | 0 / 53 | 10 / 62 | 17 / 49 | 24 / 48 | 26 / 42 |

- external load, refused at the first attempt (47): blocks of the full sequence p10 / p50 / p90 = 210 / 408 / 532; free blocks 34 / 217 / 382; needed / free p50 1.81; used share of the pool p10 / p50 0.949 / 0.971; gate {'full': 45, 'resv': 2}
- external load, admitted at the first attempt (78): blocks of the full sequence p50 / p90 = 281 / 456; free blocks p10 / p50 395 / 1226; smallest free / needed ratio 1.16
- compute request (miss or GPU-prefix hit), refused at the first attempt (77): blocks of the full sequence p10 / p50 / p90 = 101 / 954 / 1981; free blocks 24 / 272 / 857; needed / free p50 2.71; used share of the pool p10 / p50 0.885 / 0.964; gate {'full': 77}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (342): blocks of the full sequence p50 / p90 = 200 / 959; free blocks p10 / p50 294 / 3329; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 999136 tokens over 544 requests; 33 requests had lost part of it by the time they were admitted (125680 tokens, 12.6 %); 33 of them were then admitted as external loads

### External loads of `x08-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 5 | 210 | 4 | 28.92 / 28.55 | 1, 39.09 | 4, 28.92 | 29.66 |
| 2k–4k | 47 | 199 | 9 | 15.99 / 14.09 | 19, 16.36 | 28, 15.99 | 16.79 |
| 4k–8k | 55 | 413 | 24 | 21.30 / 21.67 | 23, 13.64 | 32, 25.24 | 22.88 |
| ≥ 8k | 7 | 921 | 4 | 11.27 / 12.55 | 3, 4.82 | 4, 24.16 | 11.76 |
