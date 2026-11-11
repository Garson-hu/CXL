## First admission attempts of `e-tool08-120-big-p1` (pool 19919 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 30 | 0 | 0 / 14 | 0 / 16 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 513 | 0 | 0 / 288 | 0 / 201 | 0 / 22 | 0 / 1 | 0 / 1 | 0 / 0 |

- external load, admitted at the first attempt (30): blocks of the full sequence p50 / p90 = 281 / 1674; free blocks p10 / p50 5996 / 9678; smallest free / needed ratio 3.88
- compute request (miss or GPU-prefix hit), admitted at the first attempt (513): blocks of the full sequence p50 / p90 = 306 / 1145; free blocks p10 / p50 6661 / 10950; smallest free / needed ratio 1.45
- GPU-cached prefix at the first visit: 1514480 tokens over 543 requests; 4 requests had lost part of it by the time they were admitted (10240 tokens, 0.7 %); 4 of them were then admitted as external loads

### External loads of `e-tool08-120-big-p1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 4 | 100 | 0 | 10.54 / 9.49 | – | 4, 10.54 | 17.71 |
| 2k–4k | 14 | 197 | 0 | 8.77 / 9.74 | 5, 7.64 | 9, 8.77 | 15.04 |
| 4k–8k | 3 | 418 | 0 | 0.88 / 2.05 | – | 3, 0.88 | 3.05 |
| ≥ 8k | 9 | 1030 | 0 | 0.69 / 4.49 | 2, 0.03 | 7, 3.80 | 8.38 |
