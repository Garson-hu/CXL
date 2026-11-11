## First admission attempts of `e-tool04-80-p7456-p1` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 108 | 10 | 0 / 70 | 0 / 18 | 5 / 14 | 4 / 5 | 0 / 0 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 1051 | 38 | 0 / 817 | 7 / 162 | 18 / 53 | 6 / 11 | 6 / 7 | 1 / 1 |

- external load, refused at the first attempt (10): blocks of the full sequence p10 / p50 / p90 = 440 / 457 / 587; free blocks 387 / 890 / 1819; needed / free p50 0.73; used share of the pool p10 / p50 0.805 / 0.916; gate {'full': 3, 'resv': 7}
- external load, admitted at the first attempt (98): blocks of the full sequence p50 / p90 = 386 / 921; free blocks p10 / p50 1706 / 5631; smallest free / needed ratio 1.72
- compute request (miss or GPU-prefix hit), refused at the first attempt (38): blocks of the full sequence p10 / p50 / p90 = 282 / 1254 / 1992; free blocks 272 / 1072 / 1970; needed / free p50 1.07; used share of the pool p10 / p50 0.736 / 0.870; gate {'full': 38}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1013): blocks of the full sequence p50 / p90 = 386 / 1081; free blocks p10 / p50 2564 / 5889; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 3228032 tokens over 1159 requests; 20 requests had lost part of it by the time they were admitted (69120 tokens, 2.1 %); 20 of them were then admitted as external loads

### External loads of `e-tool04-80-p7456-p1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 18 | 212 | 1 | 0.57 / 6.47 | 5, 0.02 | 13, 0.77 | 1.99 |
| 2k–4k | 37 | 199 | 1 | 0.33 / 2.15 | 17, 0.02 | 20, 0.67 | 1.62 |
| 4k–8k | 35 | 435 | 7 | 0.61 / 5.66 | 16, 0.02 | 19, 1.08 | 2.00 |
| ≥ 8k | 16 | 1243 | 0 | 0.28 / 0.42 | 9, 0.02 | 7, 0.72 | 1.40 |
