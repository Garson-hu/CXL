## First admission attempts of `t06-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 150 | 31 | 0 / 57 | 0 / 17 | 0 / 24 | 8 / 23 | 15 / 21 | 8 / 8 |
| compute request (miss or GPU-prefix hit) | 703 | 52 | 0 / 420 | 0 / 140 | 14 / 66 | 16 / 40 | 11 / 22 | 11 / 15 |

- external load, refused at the first attempt (31): blocks of the full sequence p10 / p50 / p90 = 262 / 418 / 532; free blocks 98 / 232 / 406; needed / free p50 1.78; used share of the pool p10 / p50 0.946 / 0.969; gate {'full': 31}
- external load, admitted at the first attempt (119): blocks of the full sequence p50 / p90 = 386 / 565; free blocks p10 / p50 582 / 3640; smallest free / needed ratio 1.02
- compute request (miss or GPU-prefix hit), refused at the first attempt (52): blocks of the full sequence p10 / p50 / p90 = 299 / 1080 / 1989; free blocks 95 / 438 / 1072; needed / free p50 2.19; used share of the pool p10 / p50 0.856 / 0.942; gate {'full': 52}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (651): blocks of the full sequence p50 / p90 = 386 / 1145; free blocks p10 / p50 1305 / 4924; smallest free / needed ratio 1.03
- GPU-cached prefix at the first visit: 1914176 tokens over 853 requests; 35 requests had lost part of it by the time they were admitted (144208 tokens, 7.5 %); 35 of them were then admitted as external loads

### External loads of `t06-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 11 | 210 | 3 | 5.76 / 12.93 | 6, 0.99 | 5, 7.83 | 12.39 |
| 2k–4k | 52 | 200 | 5 | 5.31 / 12.04 | 15, 0.47 | 37, 7.67 | 9.97 |
| 4k–8k | 67 | 418 | 13 | 15.40 / 16.97 | 12, 3.08 | 55, 21.61 | 16.19 |
| ≥ 8k | 10 | 1306 | 3 | 3.78 / 16.14 | 7, 0.03 | 3, 20.59 | 6.52 |
