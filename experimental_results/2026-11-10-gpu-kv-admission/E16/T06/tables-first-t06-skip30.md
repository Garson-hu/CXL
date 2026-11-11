## First admission attempts of `t06-skip30` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 126 | 0 | 0 / 64 | 0 / 17 | 0 / 17 | 0 / 19 | 0 / 8 | 0 / 1 |
| compute request (miss or GPU-prefix hit) | 727 | 7 | 0 / 407 | 1 / 158 | 1 / 84 | 1 / 58 | 1 / 14 | 3 / 6 |

- external load, admitted at the first attempt (126): blocks of the full sequence p50 / p90 = 387 / 566; free blocks p10 / p50 436 / 3836; smallest free / needed ratio 1.07
- compute request (miss or GPU-prefix hit), refused at the first attempt (7): blocks of the full sequence p10 / p50 / p90 = 1080 / 1759 / 1999; free blocks 37 / 367 / 1920; needed / free p50 4.79; used share of the pool p10 / p50 0.742 / 0.951; gate {'full': 7}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (720): blocks of the full sequence p50 / p90 = 386 / 1252; free blocks p10 / p50 743 / 4381; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 1809808 tokens over 853 requests; 10 requests had lost part of it by the time they were admitted (18384 tokens, 1.0 %); 10 of them were then admitted as external loads

### External loads of `t06-skip30` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 11 | 100 | 1 | 7.83 / 8.78 | 3, 0.29 | 8, 14.94 | 12.42 |
| 2k–4k | 49 | 199 | 1 | 2.31 / 4.73 | 16, 0.63 | 33, 4.82 | 3.77 |
| 4k–8k | 57 | 418 | 1 | 5.29 / 6.56 | 17, 0.57 | 40, 6.29 | 6.87 |
| ≥ 8k | 9 | 1243 | 0 | 4.00 / 8.14 | 5, 0.03 | 4, 18.80 | 6.53 |
