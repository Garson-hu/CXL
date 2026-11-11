## First admission attempts of `e-tool04-80-p7456-priolen` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 111 | 8 | 0 / 85 | 0 / 9 | 1 / 7 | 0 / 1 | 3 / 4 | 4 / 5 |
| compute request (miss or GPU-prefix hit) | 1048 | 34 | 0 / 790 | 2 / 135 | 11 / 67 | 5 / 33 | 8 / 11 | 8 / 12 |

- external load, refused at the first attempt (8): blocks of the full sequence p10 / p50 / p90 = 386 / 457 / 1987; free blocks 73 / 297 / 1847; needed / free p50 4.48; used share of the pool p10 / p50 0.752 / 0.980; gate {'full': 8}
- external load, admitted at the first attempt (103): blocks of the full sequence p50 / p90 = 357 / 623; free blocks p10 / p50 2236 / 5521; smallest free / needed ratio 1.82
- compute request (miss or GPU-prefix hit), refused at the first attempt (34): blocks of the full sequence p10 / p50 / p90 = 517 / 1463 / 1992; free blocks 62 / 414 / 1777; needed / free p50 2.76; used share of the pool p10 / p50 0.762 / 0.948; gate {'full': 34}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1014): blocks of the full sequence p50 / p90 = 386 / 1072; free blocks p10 / p50 1992 / 5783; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 3134032 tokens over 1159 requests; 6 requests had lost part of it by the time they were admitted (34544 tokens, 1.1 %); 6 of them were then admitted as external loads

### External loads of `e-tool04-80-p7456-priolen` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 11 | 72 | 1 | 1.41 / 3.78 | 5, 0.02 | 6, 6.29 | 2.10 |
| 2k–4k | 43 | 199 | 0 | 1.17 / 2.09 | 20, 0.03 | 23, 3.53 | 2.30 |
| 4k–8k | 42 | 411 | 3 | 1.35 / 3.13 | 21, 0.02 | 21, 4.55 | 2.70 |
| ≥ 8k | 14 | 1243 | 3 | 0.50 / 7.34 | 8, 0.02 | 6, 18.58 | 5.94 |
