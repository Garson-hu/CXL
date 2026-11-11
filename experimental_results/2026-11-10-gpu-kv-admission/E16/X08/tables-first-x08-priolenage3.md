## First admission attempts of `x08-priolenage3` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 112 | 31 | 0 / 13 | 0 / 13 | 0 / 24 | 5 / 29 | 11 / 18 | 15 / 15 |
| compute request (miss or GPU-prefix hit) | 432 | 78 | 0 / 158 | 0 / 49 | 11 / 74 | 23 / 64 | 23 / 47 | 21 / 40 |

- external load, refused at the first attempt (31): blocks of the full sequence p10 / p50 / p90 = 194 / 388 / 430; free blocks 30 / 161 / 387; needed / free p50 1.98; used share of the pool p10 / p50 0.948 / 0.978; gate {'full': 29, 'resv': 2}
- external load, admitted at the first attempt (81): blocks of the full sequence p50 / p90 = 386 / 461; free blocks p10 / p50 401 / 1014; smallest free / needed ratio 1.00
- compute request (miss or GPU-prefix hit), refused at the first attempt (78): blocks of the full sequence p10 / p50 / p90 = 189 / 1008 / 1983; free blocks 39 / 334 / 827; needed / free p50 2.88; used share of the pool p10 / p50 0.889 / 0.957; gate {'full': 78}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (354): blocks of the full sequence p50 / p90 = 196 / 847; free blocks p10 / p50 262 / 2825; smallest free / needed ratio 1.05
- GPU-cached prefix at the first visit: 1030848 tokens over 544 requests; 16 requests had lost part of it by the time they were admitted (34704 tokens, 3.4 %); 16 of them were then admitted as external loads

### External loads of `x08-priolenage3` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 7 | 120 | 3 | 0.75 / 2.26 | 4, 0.39 | 3, 6.26 | 1.85 |
| 2k–4k | 45 | 198 | 10 | 1.53 / 2.82 | 15, 0.25 | 30, 2.73 | 3.28 |
| 4k–8k | 47 | 414 | 17 | 3.23 / 4.59 | 16, 0.88 | 31, 5.33 | 6.07 |
| ≥ 8k | 5 | 921 | 1 | 0.85 / 9.00 | 2, 34.43 | 3, 0.85 | 10.32 |
