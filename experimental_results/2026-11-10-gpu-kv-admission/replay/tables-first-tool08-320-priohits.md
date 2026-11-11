## First admission attempts of `tool08-320-priohits` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 107 | 38 | 0 / 15 | 0 / 12 | 0 / 17 | 0 / 16 | 16 / 25 | 22 / 22 |
| compute request (miss or GPU-prefix hit) | 437 | 89 | 0 / 163 | 0 / 41 | 13 / 63 | 21 / 65 | 23 / 53 | 32 / 52 |

- external load, refused at the first attempt (38): blocks of the full sequence p10 / p50 / p90 = 192 / 387 / 446; free blocks 24 / 139 / 324; needed / free p50 2.26; used share of the pool p10 / p50 0.957 / 0.981; gate {'full': 37, 'resv': 1}
- external load, admitted at the first attempt (69): blocks of the full sequence p50 / p90 = 386 / 532; free blocks p10 / p50 326 / 1324; smallest free / needed ratio 1.00
- compute request (miss or GPU-prefix hit), refused at the first attempt (89): blocks of the full sequence p10 / p50 / p90 = 77 / 893 / 1982; free blocks 27 / 260 / 824; needed / free p50 2.27; used share of the pool p10 / p50 0.889 / 0.965; gate {'full': 89}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (348): blocks of the full sequence p50 / p90 = 196 / 847; free blocks p10 / p50 239 / 3051; smallest free / needed ratio 1.04
- GPU-cached prefix at the first visit: 1054192 tokens over 544 requests; 15 requests had lost part of it by the time they were admitted (23872 tokens, 2.3 %); 15 of them were then admitted as external loads

### External loads of `tool08-320-priohits` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 5 | 196 | 2 | 5.00 / 6.53 | 2, 13.95 | 3, 5.00 | 6.78 |
| 2k–4k | 42 | 198 | 18 | 4.33 / 3.91 | 15, 0.75 | 27, 4.77 | 5.34 |
| 4k–8k | 42 | 414 | 12 | 4.29 / 4.03 | 19, 0.45 | 23, 5.42 | 5.58 |
| ≥ 8k | 6 | 921 | 2 | 4.20 / 6.46 | 2, 4.20 | 4, 8.85 | 10.12 |
