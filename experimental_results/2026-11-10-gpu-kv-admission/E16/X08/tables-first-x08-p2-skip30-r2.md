## First admission attempts of `x08-p2-skip30-r2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 124 | 1 | 0 / 17 | 0 / 28 | 0 / 43 | 1 / 30 | 0 / 6 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 420 | 25 | 0 / 162 | 0 / 67 | 15 / 100 | 7 / 53 | 0 / 22 | 3 / 16 |

- external load, refused at the first attempt (1): blocks of the full sequence p10 / p50 / p90 = 1030 / 1030 / 1030; free blocks 663 / 663 / 663; needed / free p50 1.55; used share of the pool p10 / p50 0.911 / 0.911; gate {'full': 1}
- external load, admitted at the first attempt (123): blocks of the full sequence p50 / p90 = 387 / 469; free blocks p10 / p50 453 / 1322; smallest free / needed ratio 1.01
- compute request (miss or GPU-prefix hit), refused at the first attempt (25): blocks of the full sequence p10 / p50 / p90 = 843 / 1201 / 1999; free blocks 139 / 790 / 1524; needed / free p50 1.55; used share of the pool p10 / p50 0.796 / 0.894; gate {'full': 25}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (395): blocks of the full sequence p50 / p90 = 274 / 1138; free blocks p10 / p50 419 / 2404; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 1060528 tokens over 544 requests; 31 requests had lost part of it by the time they were admitted (70240 tokens, 6.6 %); 31 of them were then admitted as external loads

### External loads of `x08-p2-skip30-r2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 14 | 413 | 0 | 0.61 / 3.80 | 5, 0.60 | 9, 0.61 | 3.13 |
| 2k–4k | 49 | 199 | 1 | 1.17 / 6.59 | 25, 5.00 | 24, 0.57 | 3.31 |
| 4k–8k | 52 | 416 | 1 | 7.36 / 10.01 | 25, 7.91 | 27, 0.72 | 8.47 |
| ≥ 8k | 9 | 1030 | 2 | 0.70 / 8.71 | 2, 0.03 | 7, 6.52 | 8.36 |
