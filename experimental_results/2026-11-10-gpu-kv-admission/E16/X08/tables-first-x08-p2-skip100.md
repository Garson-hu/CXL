## First admission attempts of `x08-p2-skip100` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 108 | 0 | 0 / 18 | 0 / 8 | 0 / 33 | 0 / 43 | 0 / 5 | 0 / 1 |
| compute request (miss or GPU-prefix hit) | 436 | 0 | 0 / 155 | 0 / 86 | 0 / 91 | 0 / 64 | 0 / 29 | 0 / 11 |

- external load, admitted at the first attempt (108): blocks of the full sequence p50 / p90 = 387 / 565; free blocks p10 / p50 420 / 968; smallest free / needed ratio 1.06
- compute request (miss or GPU-prefix hit), admitted at the first attempt (436): blocks of the full sequence p50 / p90 = 274 / 1287; free blocks p10 / p50 403 / 2154; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 1089600 tokens over 544 requests; 27 requests had lost part of it by the time they were admitted (44976 tokens, 4.1 %); 27 of them were then admitted as external loads

### External loads of `x08-p2-skip100` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 21 | 386 | 0 | 3.05 / 5.14 | 11, 2.36 | 10, 4.63 | 3.34 |
| 2k–4k | 40 | 201 | 2 | 0.53 / 1.55 | 19, 0.18 | 21, 0.54 | 1.94 |
| 4k–8k | 38 | 413 | 1 | 0.86 / 3.25 | 13, 1.99 | 25, 0.73 | 2.79 |
| ≥ 8k | 9 | 1030 | 2 | 0.70 / 3.15 | 5, 2.17 | 4, 0.70 | 4.64 |
