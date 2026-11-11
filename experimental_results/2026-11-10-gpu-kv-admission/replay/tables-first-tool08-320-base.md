## First admission attempts of `tool08-320-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 126 | 44 | 0 / 10 | 0 / 15 | 2 / 34 | 4 / 20 | 21 / 30 | 17 / 17 |
| compute request (miss or GPU-prefix hit) | 418 | 76 | 0 / 166 | 0 / 53 | 11 / 63 | 16 / 46 | 23 / 49 | 26 / 41 |

- external load, refused at the first attempt (44): blocks of the full sequence p10 / p50 / p90 = 210 / 409 / 532; free blocks 34 / 217 / 382; needed / free p50 2.02; used share of the pool p10 / p50 0.949 / 0.972; gate {'full': 42, 'resv': 2}
- external load, admitted at the first attempt (82): blocks of the full sequence p50 / p90 = 274 / 448; free blocks p10 / p50 352 / 1222; smallest free / needed ratio 1.16
- compute request (miss or GPU-prefix hit), refused at the first attempt (76): blocks of the full sequence p10 / p50 / p90 = 101 / 1003 / 1981; free blocks 23 / 258 / 859; needed / free p50 2.74; used share of the pool p10 / p50 0.885 / 0.966; gate {'full': 76}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (342): blocks of the full sequence p50 / p90 = 206 / 959; free blocks p10 / p50 294 / 3476; smallest free / needed ratio 1.03
- GPU-cached prefix at the first visit: 998976 tokens over 544 requests; 36 requests had lost part of it by the time they were admitted (116720 tokens, 11.7 %); 36 of them were then admitted as external loads

### External loads of `tool08-320-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 11 | 163 | 6 | 13.26 / 18.90 | 2, 39.07 | 9, 11.89 | 13.92 |
| 2k–4k | 46 | 199 | 8 | 16.34 / 13.99 | 19, 16.34 | 27, 15.97 | 17.13 |
| 4k–8k | 53 | 412 | 22 | 22.68 / 21.86 | 22, 13.64 | 31, 25.21 | 23.69 |
| ≥ 8k | 7 | 921 | 4 | 10.47 / 12.36 | 3, 4.82 | 4, 24.11 | 11.36 |
