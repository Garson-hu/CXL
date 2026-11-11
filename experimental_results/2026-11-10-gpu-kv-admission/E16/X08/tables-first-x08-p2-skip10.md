## First admission attempts of `x08-p2-skip10` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 128 | 19 | 0 / 17 | 0 / 33 | 8 / 45 | 3 / 22 | 5 / 8 | 3 / 3 |
| compute request (miss or GPU-prefix hit) | 416 | 73 | 0 / 163 | 2 / 62 | 32 / 98 | 23 / 44 | 9 / 31 | 7 / 18 |

- external load, refused at the first attempt (19): blocks of the full sequence p10 / p50 / p90 = 196 / 440 / 871; free blocks 93 / 480 / 1695; needed / free p50 1.01; used share of the pool p10 / p50 0.773 / 0.936; gate {'full': 10, 'resv': 9}
- external load, admitted at the first attempt (109): blocks of the full sequence p50 / p90 = 378 / 532; free blocks p10 / p50 531 / 1674; smallest free / needed ratio 1.09
- compute request (miss or GPU-prefix hit), refused at the first attempt (73): blocks of the full sequence p10 / p50 / p90 = 296 / 1003 / 1981; free blocks 177 / 694 / 1496; needed / free p50 1.16; used share of the pool p10 / p50 0.799 / 0.907; gate {'full': 73}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (343): blocks of the full sequence p50 / p90 = 200 / 929; free blocks p10 / p50 420 / 3134; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 1103456 tokens over 544 requests; 51 requests had lost part of it by the time they were admitted (173872 tokens, 15.8 %); 51 of them were then admitted as external loads

### External loads of `x08-p2-skip10` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 16 | 425 | 3 | 13.35 / 9.48 | 6, 17.37 | 10, 2.36 | 15.68 |
| 2k–4k | 46 | 203 | 6 | 2.78 / 9.38 | 16, 2.24 | 30, 3.28 | 5.26 |
| 4k–8k | 55 | 406 | 11 | 17.37 / 18.14 | 20, 14.91 | 35, 18.34 | 19.12 |
| ≥ 8k | 9 | 1030 | 2 | 0.39 / 7.36 | 2, 0.03 | 7, 0.70 | 3.65 |
