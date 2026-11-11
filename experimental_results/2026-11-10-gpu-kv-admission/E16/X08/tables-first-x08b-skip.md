## First admission attempts of `x08b-skip` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 130 | 22 | 0 / 16 | 0 / 14 | 1 / 39 | 4 / 35 | 12 / 21 | 5 / 5 |
| compute request (miss or GPU-prefix hit) | 414 | 47 | 0 / 166 | 0 / 57 | 3 / 76 | 16 / 56 | 14 / 33 | 14 / 26 |

- external load, refused at the first attempt (22): blocks of the full sequence p10 / p50 / p90 = 386 / 424 / 587; free blocks 65 / 225 / 527; needed / free p50 1.86; used share of the pool p10 / p50 0.929 / 0.974; gate {'full': 20, 'resv': 2}
- external load, admitted at the first attempt (108): blocks of the full sequence p50 / p90 = 386 / 460; free blocks p10 / p50 404 / 955; smallest free / needed ratio 1.06
- compute request (miss or GPU-prefix hit), refused at the first attempt (47): blocks of the full sequence p10 / p50 / p90 = 542 / 1201 / 1987; free blocks 46 / 233 / 651; needed / free p50 4.56; used share of the pool p10 / p50 0.913 / 0.969; gate {'full': 47}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (367): blocks of the full sequence p50 / p90 = 253 / 1008; free blocks p10 / p50 430 / 3022; smallest free / needed ratio 1.06
- GPU-cached prefix at the first visit: 848672 tokens over 544 requests; 12 requests had lost part of it by the time they were admitted (21296 tokens, 2.5 %); 12 of them were then admitted as external loads

### External loads of `x08b-skip` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 10 | 388 | 2 | 11.85 / 12.65 | 6, 11.85 | 4, 18.38 | 12.87 |
| 2k–4k | 52 | 199 | 4 | 7.54 / 10.83 | 13, 0.08 | 39, 9.13 | 9.22 |
| 4k–8k | 55 | 408 | 14 | 17.43 / 17.50 | 32, 10.03 | 23, 22.56 | 18.72 |
| ≥ 8k | 9 | 1030 | 3 | 1.31 / 8.23 | 6, 1.31 | 3, 24.04 | 6.81 |
