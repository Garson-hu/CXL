## First admission attempts of `tool04-320-p4` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 167 | 0 | 0 / 130 | 0 / 22 | 0 / 7 | 0 / 6 | 0 / 2 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 992 | 6 | 0 / 770 | 0 / 147 | 2 / 50 | 4 / 18 | 0 / 6 | 0 / 1 |

- external load, admitted at the first attempt (167): blocks of the full sequence p50 / p90 = 435 / 1505; free blocks p10 / p50 2080 / 5986; smallest free / needed ratio 1.05
- compute request (miss or GPU-prefix hit), refused at the first attempt (6): blocks of the full sequence p10 / p50 / p90 = 843 / 1700 / 1999; free blocks 482 / 654 / 1128; needed / free p50 2.00; used share of the pool p10 / p50 0.849 / 0.919; gate {'full': 6}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (986): blocks of the full sequence p50 / p90 = 386 / 1071; free blocks p10 / p50 2217 / 5898; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 3231248 tokens over 1159 requests; 12 requests had lost part of it by the time they were admitted (30352 tokens, 0.9 %); 12 of them were then admitted as external loads

### External loads of `tool04-320-p4` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 35 | 210 | 1 | 0.44 / 1.80 | 16, 0.02 | 19, 0.60 | 1.74 |
| 2k–4k | 45 | 200 | 0 | 0.06 / 0.98 | 25, 0.02 | 20, 0.68 | 1.03 |
| 4k–8k | 41 | 418 | 0 | 0.03 / 1.07 | 22, 0.02 | 19, 0.61 | 1.10 |
| ≥ 8k | 46 | 1255 | 1 | 0.02 / 1.23 | 29, 0.02 | 17, 0.61 | 1.39 |
