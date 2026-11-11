## First admission attempts of `tool08-320-storefix` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 127 | 46 | 0 / 11 | 0 / 17 | 2 / 33 | 3 / 19 | 23 / 29 | 18 / 18 |
| compute request (miss or GPU-prefix hit) | 417 | 77 | 0 / 165 | 0 / 50 | 9 / 64 | 18 / 47 | 24 / 49 | 26 / 42 |

- external load, refused at the first attempt (46): blocks of the full sequence p10 / p50 / p90 = 210 / 408 / 532; free blocks 11 / 207 / 382; needed / free p50 1.93; used share of the pool p10 / p50 0.949 / 0.974; gate {'full': 44, 'resv': 2}
- external load, admitted at the first attempt (81): blocks of the full sequence p50 / p90 = 357 / 460; free blocks p10 / p50 505 / 1240; smallest free / needed ratio 1.06
- compute request (miss or GPU-prefix hit), refused at the first attempt (77): blocks of the full sequence p10 / p50 / p90 = 63 / 893 / 1981; free blocks 24 / 272 / 797; needed / free p50 2.51; used share of the pool p10 / p50 0.893 / 0.964; gate {'full': 77}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (340): blocks of the full sequence p50 / p90 = 200 / 959; free blocks p10 / p50 295 / 3473; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 959152 tokens over 544 requests; 29 requests had lost part of it by the time they were admitted (103680 tokens, 10.8 %); 29 of them were then admitted as external loads

### External loads of `tool08-320-storefix` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 7 | 389 | 5 | 22.49 / 23.43 | 4, 22.49 | 3, 28.42 | 28.66 |
| 2k–4k | 47 | 199 | 10 | 15.71 / 13.64 | 18, 17.27 | 29, 13.12 | 16.78 |
| 4k–8k | 54 | 412 | 22 | 22.75 / 22.03 | 24, 17.30 | 30, 25.23 | 23.92 |
| ≥ 8k | 9 | 1030 | 4 | 1.35 / 8.52 | 6, 1.35 | 3, 24.12 | 6.90 |
