## First admission attempts of `e7-tool02-80-p1` (pool 8753 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 20 | 0 | 0 / 16 | 0 / 2 | 0 / 2 | 0 / 0 | 0 / 0 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 524 | 11 | 0 / 433 | 0 / 64 | 1 / 12 | 6 / 11 | 2 / 2 | 2 / 2 |

- external load, admitted at the first attempt (20): blocks of the full sequence p50 / p90 = 210 / 457; free blocks p10 / p50 2573 / 7232; smallest free / needed ratio 2.40
- compute request (miss or GPU-prefix hit), refused at the first attempt (11): blocks of the full sequence p10 / p50 / p90 = 76 / 677 / 917; free blocks 58 / 672 / 826; needed / free p50 1.15; used share of the pool p10 / p50 0.906 / 0.923; gate {'full': 11}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (513): blocks of the full sequence p50 / p90 = 390 / 1217; free blocks p10 / p50 3653 / 7446; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 1473024 tokens over 544 requests; 4 requests had lost part of it by the time they were admitted (10416 tokens, 0.7 %); 4 of them were then admitted as external loads

### External loads of `e7-tool02-80-p1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 3 | 210 | 1 | 54.87 / 37.66 | – | 3, 54.87 | 55.90 |
| 2k–4k | 11 | 198 | 0 | 1.08 / 0.77 | 5, 0.04 | 6, 1.23 | 3.07 |
| 4k–8k | 7 | 413 | 0 | 0.95 / 5.87 | 3, 0.04 | 4, 2.28 | 2.87 |
