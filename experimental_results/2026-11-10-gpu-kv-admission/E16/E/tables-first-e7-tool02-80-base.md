## First admission attempts of `e7-tool02-80-base` (pool 8753 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 26 | 2 | 0 / 19 | 0 / 1 | 0 / 3 | 0 / 0 | 0 / 1 | 2 / 2 |
| compute request (miss or GPU-prefix hit) | 518 | 9 | 0 / 415 | 0 / 66 | 2 / 23 | 1 / 7 | 2 / 2 | 4 / 5 |

- external load, refused at the first attempt (2): blocks of the full sequence p10 / p50 / p90 = 408 / 409 / 409; free blocks 52 / 66 / 66; needed / free p50 7.85; used share of the pool p10 / p50 0.992 / 0.994; gate {'full': 2}
- external load, admitted at the first attempt (24): blocks of the full sequence p50 / p90 = 199 / 418; free blocks p10 / p50 1669 / 6583; smallest free / needed ratio 1.48
- compute request (miss or GPU-prefix hit), refused at the first attempt (9): blocks of the full sequence p10 / p50 / p90 = 29 / 677 / 1987; free blocks 21 / 177 / 1685; needed / free p50 1.38; used share of the pool p10 / p50 0.807 / 0.980; gate {'full': 9}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (509): blocks of the full sequence p50 / p90 = 387 / 1217; free blocks p10 / p50 3249 / 7392; smallest free / needed ratio 1.11
- GPU-cached prefix at the first visit: 1436800 tokens over 544 requests; 6 requests had lost part of it by the time they were admitted (17072 tokens, 1.2 %); 6 of them were then admitted as external loads

### External loads of `e7-tool02-80-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 1 | 209 | 1 | 53.47 / 53.47 | – | 1, 53.47 | 54.58 |
| 2k–4k | 18 | 198 | 0 | 6.11 / 9.56 | 5, 0.04 | 13, 9.79 | 12.64 |
| 4k–8k | 8 | 409 | 2 | 7.77 / 17.94 | 4, 5.02 | 4, 23.21 | 16.22 |
