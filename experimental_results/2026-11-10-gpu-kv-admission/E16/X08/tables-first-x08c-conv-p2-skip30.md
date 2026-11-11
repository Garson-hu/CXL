## First admission attempts of `x08c-conv-p2-skip30` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 19 | 0 | 0 / 5 | 0 / 7 | 0 / 5 | 0 / 1 | 0 / 1 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 272 | 26 | 0 / 81 | 2 / 62 | 12 / 83 | 11 / 34 | 1 / 8 | 0 / 4 |

- external load, admitted at the first attempt (19): blocks of the full sequence p50 / p90 = 681 / 1977; free blocks p10 / p50 598 / 2094; smallest free / needed ratio 1.09
- compute request (miss or GPU-prefix hit), refused at the first attempt (26): blocks of the full sequence p10 / p50 / p90 = 599 / 1348 / 2001; free blocks 463 / 811 / 1795; needed / free p50 1.21; used share of the pool p10 / p50 0.759 / 0.897; gate {'full': 26}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (246): blocks of the full sequence p50 / p90 = 440 / 1596; free blocks p10 / p50 622 / 2175; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 148480 tokens over 291 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `x08c-conv-p2-skip30` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 3 | 100 | 1 | 1.62 / 1.82 | 2, 3.23 | 1, 0.61 | 3.15 |
| 2k–4k | 4 | 216 | 0 | 0.91 / 1.26 | 1, 0.53 | 3, 0.91 | 5.22 |
| 4k–8k | 3 | 418 | 0 | 0.88 / 0.87 | – | 3, 0.88 | 3.00 |
| ≥ 8k | 9 | 1030 | 1 | 0.70 / 5.85 | 4, 17.57 | 5, 0.70 | 7.63 |
