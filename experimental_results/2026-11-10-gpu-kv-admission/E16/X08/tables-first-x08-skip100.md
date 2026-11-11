## First admission attempts of `x08-skip100` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 134 | 0 | 0 / 12 | 0 / 9 | 0 / 45 | 0 / 56 | 0 / 12 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 410 | 0 | 0 / 153 | 0 / 71 | 0 / 93 | 0 / 67 | 0 / 18 | 0 / 8 |

- external load, admitted at the first attempt (134): blocks of the full sequence p50 / p90 = 387 / 469; free blocks p10 / p50 389 / 745; smallest free / needed ratio 1.01
- compute request (miss or GPU-prefix hit), admitted at the first attempt (410): blocks of the full sequence p50 / p90 = 362 / 1348; free blocks p10 / p50 507 / 2142; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 873152 tokens over 544 requests; 22 requests had lost part of it by the time they were admitted (51632 tokens, 5.9 %); 22 of them were then admitted as external loads

### External loads of `x08-skip100` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 14 | 196 | 1 | 5.60 / 8.28 | 6, 0.20 | 8, 18.49 | 7.70 |
| 2k–4k | 55 | 199 | 0 | 5.01 / 5.02 | 22, 0.86 | 33, 6.96 | 5.50 |
| 4k–8k | 56 | 413 | 2 | 6.03 / 7.27 | 25, 2.52 | 31, 9.39 | 7.37 |
| ≥ 8k | 9 | 1030 | 1 | 5.19 / 9.16 | 5, 0.73 | 4, 24.71 | 7.70 |
