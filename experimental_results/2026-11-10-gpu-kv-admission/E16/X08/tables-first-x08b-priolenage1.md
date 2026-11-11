## First admission attempts of `x08b-priolenage1` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 113 | 32 | 0 / 16 | 0 / 15 | 1 / 28 | 4 / 18 | 13 / 20 | 14 / 16 |
| compute request (miss or GPU-prefix hit) | 431 | 69 | 0 / 171 | 0 / 57 | 10 / 77 | 19 / 43 | 18 / 52 | 22 / 31 |

- external load, refused at the first attempt (32): blocks of the full sequence p10 / p50 / p90 = 197 / 390 / 457; free blocks 49 / 177 / 445; needed / free p50 1.71; used share of the pool p10 / p50 0.940 / 0.977; gate {'full': 28, 'resv': 4}
- external load, admitted at the first attempt (81): blocks of the full sequence p50 / p90 = 269 / 454; free blocks p10 / p50 309 / 1368; smallest free / needed ratio 1.05
- compute request (miss or GPU-prefix hit), refused at the first attempt (69): blocks of the full sequence p10 / p50 / p90 = 252 / 1030 / 1987; free blocks 33 / 317 / 832; needed / free p50 3.16; used share of the pool p10 / p50 0.888 / 0.957; gate {'full': 69}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (362): blocks of the full sequence p50 / p90 = 198 / 954; free blocks p10 / p50 326 / 3299; smallest free / needed ratio 1.05
- GPU-cached prefix at the first visit: 814896 tokens over 544 requests; 8 requests had lost part of it by the time they were admitted (8128 tokens, 1.0 %); 8 of them were then admitted as external loads

### External loads of `x08b-priolenage1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 10 | 197 | 4 | 14.02 / 11.56 | 2, 0.27 | 8, 14.55 | 15.01 |
| 2k–4k | 46 | 198 | 9 | 8.84 / 9.20 | 20, 14.13 | 26, 7.89 | 11.16 |
| 4k–8k | 42 | 414 | 11 | 11.79 / 10.44 | 20, 6.62 | 22, 13.87 | 14.96 |
| ≥ 8k | 5 | 921 | 1 | 0.69 / 7.23 | 3, 0.69 | 2, 8.76 | 10.16 |
