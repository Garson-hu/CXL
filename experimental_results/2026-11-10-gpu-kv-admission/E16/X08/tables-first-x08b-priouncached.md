## First admission attempts of `x08b-priouncached` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 116 | 42 | 0 / 13 | 0 / 12 | 1 / 29 | 0 / 14 | 22 / 29 | 19 / 19 |
| compute request (miss or GPU-prefix hit) | 428 | 86 | 0 / 159 | 1 / 54 | 12 / 60 | 14 / 47 | 27 / 54 | 32 / 54 |

- external load, refused at the first attempt (42): blocks of the full sequence p10 / p50 / p90 = 202 / 392 / 440; free blocks 7 / 160 / 303; needed / free p50 2.67; used share of the pool p10 / p50 0.959 / 0.979; gate {'full': 41, 'resv': 1}
- external load, admitted at the first attempt (74): blocks of the full sequence p50 / p90 = 378 / 456; free blocks p10 / p50 391 / 1174; smallest free / needed ratio 1.01
- compute request (miss or GPU-prefix hit), refused at the first attempt (86): blocks of the full sequence p10 / p50 / p90 = 102 / 893 / 1983; free blocks 31 / 243 / 1016; needed / free p50 2.59; used share of the pool p10 / p50 0.864 / 0.969; gate {'full': 86}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (342): blocks of the full sequence p50 / p90 = 198 / 954; free blocks p10 / p50 269 / 3083; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 1000208 tokens over 544 requests; 15 requests had lost part of it by the time they were admitted (15088 tokens, 1.5 %); 15 of them were then admitted as external loads

### External loads of `x08b-priouncached` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 6 | 160 | 2 | 5.19 / 3.96 | 1, 0.06 | 5, 5.19 | 6.24 |
| 2k–4k | 39 | 198 | 8 | 2.68 / 3.31 | 18, 0.93 | 21, 4.03 | 4.07 |
| 4k–8k | 48 | 406 | 16 | 1.93 / 2.79 | 25, 0.51 | 23, 3.36 | 3.20 |
| ≥ 8k | 5 | 921 | 1 | 0.67 / 6.65 | 2, 0.67 | 3, 8.76 | 10.15 |
