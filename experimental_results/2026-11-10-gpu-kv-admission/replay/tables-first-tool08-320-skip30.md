## First admission attempts of `tool08-320-skip30` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 129 | 0 | 0 / 12 | 0 / 15 | 0 / 40 | 0 / 52 | 0 / 10 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 415 | 10 | 0 / 152 | 0 / 73 | 2 / 99 | 3 / 56 | 2 / 19 | 3 / 16 |

- external load, admitted at the first attempt (129): blocks of the full sequence p50 / p90 = 387 / 460; free blocks p10 / p50 392 / 773; smallest free / needed ratio 1.05
- compute request (miss or GPU-prefix hit), refused at the first attempt (10): blocks of the full sequence p10 / p50 / p90 = 1201 / 1981 / 2009; free blocks 48 / 432 / 1352; needed / free p50 11.76; used share of the pool p10 / p50 0.822 / 0.977; gate {'full': 10}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (405): blocks of the full sequence p50 / p90 = 324 / 1199; free blocks p10 / p50 502 / 2198; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 899520 tokens over 544 requests; 18 requests had lost part of it by the time they were admitted (41680 tokens, 4.6 %); 18 of them were then admitted as external loads

### External loads of `tool08-320-skip30` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 10 | 196 | 0 | 18.48 / 12.40 | 2, 11.82 | 8, 19.25 | 19.96 |
| 2k–4k | 54 | 199 | 2 | 7.60 / 8.58 | 21, 5.95 | 33, 8.55 | 10.91 |
| 4k–8k | 56 | 413 | 1 | 8.66 / 10.68 | 28, 6.38 | 28, 11.21 | 11.74 |
| ≥ 8k | 9 | 1030 | 0 | 3.85 / 8.21 | 6, 3.85 | 3, 20.59 | 7.53 |
