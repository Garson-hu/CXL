## First admission attempts of `x08-p2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 137 | 25 | 0 / 17 | 2 / 39 | 9 / 55 | 8 / 18 | 6 / 8 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 407 | 89 | 0 / 162 | 3 / 58 | 37 / 97 | 23 / 46 | 17 / 29 | 9 / 15 |

- external load, refused at the first attempt (25): blocks of the full sequence p10 / p50 / p90 = 258 / 431 / 456; free blocks 288 / 567 / 1847; needed / free p50 0.73; used share of the pool p10 / p50 0.752 / 0.924; gate {'full': 6, 'resv': 19}
- external load, admitted at the first attempt (112): blocks of the full sequence p50 / p90 = 386 / 532; free blocks p10 / p50 740 / 1863; smallest free / needed ratio 1.07
- compute request (miss or GPU-prefix hit), refused at the first attempt (89): blocks of the full sequence p10 / p50 / p90 = 262 / 917 / 1982; free blocks 145 / 674 / 1563; needed / free p50 1.16; used share of the pool p10 / p50 0.790 / 0.910; gate {'full': 89}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (318): blocks of the full sequence p50 / p90 = 198 / 846; free blocks p10 / p50 612 / 3848; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 1047536 tokens over 544 requests; 45 requests had lost part of it by the time they were admitted (182608 tokens, 17.4 %); 45 of them were then admitted as external loads

### External loads of `x08-p2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 11 | 386 | 2 | 8.24 / 13.54 | 4, 8.24 | 7, 17.47 | 9.70 |
| 2k–4k | 51 | 202 | 5 | 8.16 / 11.21 | 16, 6.99 | 35, 13.05 | 10.75 |
| 4k–8k | 63 | 416 | 15 | 17.21 / 17.85 | 14, 7.70 | 49, 19.60 | 19.58 |
| ≥ 8k | 9 | 1030 | 3 | 0.39 / 7.48 | 3, 0.03 | 6, 0.70 | 3.57 |
