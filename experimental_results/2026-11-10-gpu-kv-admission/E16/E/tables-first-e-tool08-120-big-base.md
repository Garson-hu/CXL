## First admission attempts of `e-tool08-120-big-base` (pool 19919 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 23 | 0 | 0 / 7 | 0 / 15 | 0 / 1 | 0 / 0 | 0 / 0 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 521 | 0 | 0 / 293 | 0 / 212 | 0 / 16 | 0 / 0 | 0 / 0 | 0 / 0 |

- external load, admitted at the first attempt (23): blocks of the full sequence p50 / p90 = 458 / 1674; free blocks p10 / p50 6732 / 8950; smallest free / needed ratio 3.85
- compute request (miss or GPU-prefix hit), admitted at the first attempt (521): blocks of the full sequence p50 / p90 = 275 / 1138; free blocks p10 / p50 6912 / 11626; smallest free / needed ratio 1.36
- GPU-cached prefix at the first visit: 1521664 tokens over 544 requests; 2 requests had lost part of it by the time they were admitted (5120 tokens, 0.3 %); 2 of them were then admitted as external loads

### External loads of `e-tool08-120-big-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 4 | 100 | 0 | 16.08 / 11.51 | 2, 16.08 | 2, 18.93 | 18.16 |
| 2k–4k | 7 | 198 | 0 | 13.18 / 13.20 | 1, 16.68 | 6, 13.18 | 18.05 |
| 4k–8k | 3 | 418 | 0 | 22.69 / 20.69 | 1, 6.30 | 2, 33.09 | 32.16 |
| ≥ 8k | 9 | 1030 | 0 | 3.34 / 7.81 | 5, 2.57 | 4, 16.81 | 8.91 |
