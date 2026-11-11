## First admission attempts of `e-tool04-80-p7456-priohits` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 114 | 4 | 0 / 88 | 0 / 12 | 0 / 6 | 1 / 5 | 2 / 2 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 1045 | 36 | 0 / 773 | 1 / 136 | 10 / 79 | 13 / 34 | 7 / 17 | 5 / 6 |

- external load, refused at the first attempt (4): blocks of the full sequence p10 / p50 / p90 = 196 / 1330 / 1505; free blocks 113 / 360 / 404; needed / free p50 3.29; used share of the pool p10 / p50 0.946 / 0.979; gate {'full': 4}
- external load, admitted at the first attempt (110): blocks of the full sequence p50 / p90 = 386 / 709; free blocks p10 / p50 2022 / 5592; smallest free / needed ratio 1.06
- compute request (miss or GPU-prefix hit), refused at the first attempt (36): blocks of the full sequence p10 / p50 / p90 = 282 / 1254 / 1992; free blocks 111 / 416 / 1336; needed / free p50 1.80; used share of the pool p10 / p50 0.821 / 0.944; gate {'full': 36}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1009): blocks of the full sequence p50 / p90 = 386 / 1099; free blocks p10 / p50 1819 / 5755; smallest free / needed ratio 1.05
- GPU-cached prefix at the first visit: 3131936 tokens over 1159 requests; 6 requests had lost part of it by the time they were admitted (26352 tokens, 0.8 %); 6 of them were then admitted as external loads

### External loads of `e-tool04-80-p7456-priohits` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 12 | 100 | 0 | 2.71 / 3.95 | 5, 0.02 | 7, 4.87 | 3.22 |
| 2k–4k | 44 | 199 | 2 | 1.17 / 2.28 | 20, 0.03 | 24, 4.02 | 1.96 |
| 4k–8k | 42 | 418 | 1 | 1.33 / 2.68 | 22, 0.02 | 20, 2.76 | 2.65 |
| ≥ 8k | 16 | 997 | 2 | 0.02 / 3.80 | 10, 0.02 | 6, 7.94 | 1.38 |
