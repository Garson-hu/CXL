## First admission attempts of `tool08-320-priolen` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 117 | 44 | 0 / 13 | 0 / 14 | 1 / 34 | 7 / 15 | 11 / 16 | 25 / 25 |
| compute request (miss or GPU-prefix hit) | 427 | 98 | 0 / 140 | 1 / 48 | 10 / 57 | 19 / 58 | 20 / 53 | 48 / 71 |

- external load, refused at the first attempt (44): blocks of the full sequence p10 / p50 / p90 = 194 / 386 / 421; free blocks 42 / 106 / 401; needed / free p50 2.30; used share of the pool p10 / p50 0.946 / 0.986; gate {'full': 41, 'resv': 3}
- external load, admitted at the first attempt (73): blocks of the full sequence p50 / p90 = 386 / 456; free blocks p10 / p50 448 / 1411; smallest free / needed ratio 1.05
- compute request (miss or GPU-prefix hit), refused at the first attempt (98): blocks of the full sequence p10 / p50 / p90 = 48 / 865 / 1982; free blocks 11 / 166 / 825; needed / free p50 3.40; used share of the pool p10 / p50 0.889 / 0.979; gate {'full': 98}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (329): blocks of the full sequence p50 / p90 = 195 / 847; free blocks p10 / p50 241 / 2712; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 958912 tokens over 544 requests; 12 requests had lost part of it by the time they were admitted (18704 tokens, 2.0 %); 12 of them were then admitted as external loads

### External loads of `tool08-320-priolen` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 8 | 196 | 5 | 2.21 / 2.90 | 5, 0.97 | 3, 5.15 | 2.73 |
| 2k–4k | 43 | 198 | 13 | 2.02 / 3.20 | 19, 1.00 | 24, 3.94 | 4.61 |
| 4k–8k | 46 | 408 | 12 | 2.89 / 4.36 | 21, 0.97 | 25, 5.82 | 6.05 |
| ≥ 8k | 5 | 921 | 1 | 0.82 / 7.12 | 3, 0.73 | 2, 24.98 | 10.29 |
