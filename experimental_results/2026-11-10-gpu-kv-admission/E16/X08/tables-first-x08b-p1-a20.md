## First admission attempts of `x08b-p1-a20` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 142 | 51 | 0 / 17 | 4 / 19 | 16 / 62 | 8 / 19 | 20 / 22 | 3 / 3 |
| compute request (miss or GPU-prefix hit) | 402 | 93 | 0 / 165 | 1 / 51 | 35 / 96 | 24 / 39 | 26 / 41 | 7 / 10 |

- external load, refused at the first attempt (51): blocks of the full sequence p10 / p50 / p90 = 210 / 405 / 461; free blocks 212 / 475 / 1714; needed / free p50 1.05; used share of the pool p10 / p50 0.770 / 0.936; gate {'full': 27, 'resv': 24}
- external load, admitted at the first attempt (91): blocks of the full sequence p50 / p90 = 353 / 464; free blocks p10 / p50 698 / 1502; smallest free / needed ratio 1.16
- compute request (miss or GPU-prefix hit), refused at the first attempt (93): blocks of the full sequence p10 / p50 / p90 = 262 / 865 / 1981; free blocks 165 / 513 / 1259; needed / free p50 1.19; used share of the pool p10 / p50 0.831 / 0.931; gate {'full': 93}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (309): blocks of the full sequence p50 / p90 = 198 / 847; free blocks p10 / p50 692 / 4150; smallest free / needed ratio 1.03
- GPU-cached prefix at the first visit: 937248 tokens over 544 requests; 38 requests had lost part of it by the time they were admitted (150592 tokens, 16.1 %); 38 of them were then admitted as external loads

### External loads of `x08b-p1-a20` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 13 | 386 | 4 | 18.64 / 16.68 | 3, 28.18 | 10, 18.64 | 21.07 |
| 2k–4k | 53 | 199 | 14 | 12.28 / 12.99 | 12, 10.19 | 41, 17.24 | 13.76 |
| 4k–8k | 55 | 412 | 19 | 14.82 / 18.51 | 11, 21.10 | 44, 14.32 | 16.57 |
| ≥ 8k | 9 | 1030 | 5 | 9.04 / 9.45 | 3, 0.03 | 6, 9.14 | 9.51 |
