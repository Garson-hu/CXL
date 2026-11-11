## First admission attempts of `x08-p2-skip30` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 124 | 1 | 0 / 17 | 0 / 28 | 1 / 43 | 0 / 29 | 0 / 7 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 420 | 25 | 0 / 162 | 0 / 66 | 15 / 98 | 7 / 58 | 0 / 20 | 3 / 16 |

- external load, refused at the first attempt (1): blocks of the full sequence p10 / p50 / p90 = 1030 / 1030 / 1030; free blocks 1082 / 1082 / 1082; needed / free p50 0.95; used share of the pool p10 / p50 0.855 / 0.855; gate {'resv': 1}
- external load, admitted at the first attempt (123): blocks of the full sequence p50 / p90 = 387 / 469; free blocks p10 / p50 449 / 1214; smallest free / needed ratio 1.01
- compute request (miss or GPU-prefix hit), refused at the first attempt (25): blocks of the full sequence p10 / p50 / p90 = 843 / 1201 / 1999; free blocks 140 / 849 / 1523; needed / free p50 1.55; used share of the pool p10 / p50 0.796 / 0.886; gate {'full': 25}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (395): blocks of the full sequence p50 / p90 = 287 / 1138; free blocks p10 / p50 466 / 2404; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 1045456 tokens over 544 requests; 29 requests had lost part of it by the time they were admitted (68832 tokens, 6.6 %); 29 of them were then admitted as external loads

### External loads of `x08-p2-skip30` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 13 | 409 | 0 | 0.63 / 3.63 | 4, 1.11 | 9, 0.61 | 3.13 |
| 2k–4k | 50 | 199 | 2 | 1.87 / 6.48 | 24, 7.23 | 26, 0.60 | 3.62 |
| 4k–8k | 52 | 416 | 1 | 7.15 / 9.96 | 26, 9.43 | 26, 0.72 | 8.41 |
| ≥ 8k | 9 | 1030 | 2 | 0.70 / 8.81 | 2, 0.03 | 7, 7.66 | 8.35 |
