## First admission attempts of `tool08-320-base2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 126 | 45 | 0 / 11 | 0 / 15 | 2 / 34 | 3 / 19 | 22 / 29 | 18 / 18 |
| compute request (miss or GPU-prefix hit) | 418 | 78 | 0 / 165 | 0 / 53 | 10 / 60 | 17 / 49 | 23 / 49 | 28 / 42 |

- external load, refused at the first attempt (45): blocks of the full sequence p10 / p50 / p90 = 210 / 409 / 532; free blocks 29 / 207 / 382; needed / free p50 2.02; used share of the pool p10 / p50 0.949 / 0.972; gate {'full': 43, 'resv': 2}
- external load, admitted at the first attempt (81): blocks of the full sequence p50 / p90 = 275 / 448; free blocks p10 / p50 418 / 1227; smallest free / needed ratio 1.16
- compute request (miss or GPU-prefix hit), refused at the first attempt (78): blocks of the full sequence p10 / p50 / p90 = 63 / 954 / 1981; free blocks 23 / 257 / 843; needed / free p50 2.71; used share of the pool p10 / p50 0.887 / 0.969; gate {'full': 78}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (340): blocks of the full sequence p50 / p90 = 202 / 964; free blocks p10 / p50 304 / 3477; smallest free / needed ratio 1.04
- GPU-cached prefix at the first visit: 994016 tokens over 544 requests; 35 requests had lost part of it by the time they were admitted (123072 tokens, 12.4 %); 35 of them were then admitted as external loads

### External loads of `tool08-320-base2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 5 | 210 | 4 | 28.90 / 28.52 | 1, 39.07 | 4, 28.90 | 29.61 |
| 2k–4k | 49 | 199 | 9 | 13.29 / 13.89 | 19, 16.34 | 30, 13.29 | 16.16 |
| 4k–8k | 55 | 412 | 23 | 21.28 / 21.25 | 23, 12.45 | 32, 25.22 | 22.80 |
| ≥ 8k | 7 | 921 | 4 | 10.47 / 12.41 | 3, 4.82 | 4, 24.12 | 11.36 |
