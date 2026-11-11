## First admission attempts of `x08b-priolen` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 128 | 43 | 0 / 12 | 0 / 15 | 0 / 34 | 6 / 20 | 20 / 30 | 17 / 17 |
| compute request (miss or GPU-prefix hit) | 416 | 92 | 0 / 136 | 1 / 60 | 12 / 57 | 19 / 59 | 22 / 56 | 38 / 48 |

- external load, refused at the first attempt (43): blocks of the full sequence p10 / p50 / p90 = 202 / 393 / 450; free blocks 22 / 209 / 384; needed / free p50 1.92; used share of the pool p10 / p50 0.948 / 0.972; gate {'full': 41, 'resv': 2}
- external load, admitted at the first attempt (85): blocks of the full sequence p50 / p90 = 386 / 448; free blocks p10 / p50 265 / 1165; smallest free / needed ratio 1.05
- compute request (miss or GPU-prefix hit), refused at the first attempt (92): blocks of the full sequence p10 / p50 / p90 = 118 / 929 / 1981; free blocks 37 / 244 / 915; needed / free p50 2.88; used share of the pool p10 / p50 0.877 / 0.968; gate {'full': 92}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (324): blocks of the full sequence p50 / p90 = 195 / 847; free blocks p10 / p50 310 / 2740; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 885280 tokens over 544 requests; 14 requests had lost part of it by the time they were admitted (29568 tokens, 3.3 %); 14 of them were then admitted as external loads

### External loads of `x08b-priolen` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 6 | 198 | 2 | 6.61 / 6.56 | 2, 0.27 | 4, 14.37 | 7.22 |
| 2k–4k | 43 | 198 | 8 | 1.43 / 2.80 | 24, 0.55 | 19, 4.35 | 3.99 |
| 4k–8k | 56 | 413 | 15 | 2.96 / 3.96 | 24, 0.87 | 32, 4.86 | 5.66 |
| ≥ 8k | 4 | 921 | 0 | 0.69 / 2.49 | 2, 0.69 | 2, 8.80 | 10.19 |
