## First admission attempts of `tool08-320-p3` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 132 | 31 | 0 / 15 | 2 / 22 | 9 / 51 | 10 / 25 | 7 / 16 | 3 / 3 |
| compute request (miss or GPU-prefix hit) | 412 | 87 | 0 / 160 | 0 / 45 | 25 / 81 | 21 / 48 | 22 / 45 | 19 / 33 |

- external load, refused at the first attempt (31): blocks of the full sequence p10 / p50 / p90 = 200 / 431 / 789; free blocks 223 / 560 / 1587; needed / free p50 0.76; used share of the pool p10 / p50 0.787 / 0.925; gate {'full': 13, 'resv': 18}
- external load, admitted at the first attempt (101): blocks of the full sequence p50 / p90 = 281 / 464; free blocks p10 / p50 477 / 1337; smallest free / needed ratio 1.03
- compute request (miss or GPU-prefix hit), refused at the first attempt (87): blocks of the full sequence p10 / p50 / p90 = 112 / 849 / 1982; free blocks 38 / 411 / 1166; needed / free p50 1.54; used share of the pool p10 / p50 0.844 / 0.945; gate {'full': 87}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (325): blocks of the full sequence p50 / p90 = 200 / 917; free blocks p10 / p50 322 / 3328; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 1018800 tokens over 544 requests; 40 requests had lost part of it by the time they were admitted (140848 tokens, 13.8 %); 40 of them were then admitted as external loads

### External loads of `tool08-320-p3` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 17 | 202 | 5 | 18.67 / 17.21 | 3, 33.35 | 14, 17.35 | 20.49 |
| 2k–4k | 51 | 199 | 9 | 9.56 / 10.90 | 17, 13.53 | 34, 8.42 | 12.01 |
| 4k–8k | 52 | 417 | 15 | 14.63 / 17.32 | 9, 27.23 | 43, 11.60 | 16.60 |
| ≥ 8k | 9 | 1030 | 3 | 0.70 / 9.02 | 3, 0.03 | 6, 12.02 | 8.22 |
