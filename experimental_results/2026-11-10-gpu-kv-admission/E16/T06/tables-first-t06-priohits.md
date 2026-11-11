## First admission attempts of `t06-priohits` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 142 | 17 | 0 / 70 | 0 / 22 | 1 / 21 | 4 / 16 | 10 / 11 | 2 / 2 |
| compute request (miss or GPU-prefix hit) | 711 | 46 | 0 / 421 | 0 / 151 | 8 / 67 | 13 / 30 | 18 / 28 | 7 / 14 |

- external load, refused at the first attempt (17): blocks of the full sequence p10 / p50 / p90 = 252 / 421 / 1505; free blocks 73 / 285 / 416; needed / free p50 1.57; used share of the pool p10 / p50 0.944 / 0.962; gate {'full': 17}
- external load, admitted at the first attempt (125): blocks of the full sequence p50 / p90 = 386 / 534; free blocks p10 / p50 722 / 4162; smallest free / needed ratio 1.08
- compute request (miss or GPU-prefix hit), refused at the first attempt (46): blocks of the full sequence p10 / p50 / p90 = 328 / 1181 / 1989; free blocks 103 / 361 / 1108; needed / free p50 2.54; used share of the pool p10 / p50 0.851 / 0.954; gate {'full': 46}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (665): blocks of the full sequence p50 / p90 = 378 / 1138; free blocks p10 / p50 1354 / 4887; smallest free / needed ratio 1.03
- GPU-cached prefix at the first visit: 1920448 tokens over 853 requests; 10 requests had lost part of it by the time they were admitted (15968 tokens, 0.8 %); 10 of them were then admitted as external loads

### External loads of `t06-priohits` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 13 | 114 | 2 | 1.34 / 2.15 | 8, 0.59 | 5, 4.01 | 2.24 |
| 2k–4k | 56 | 199 | 3 | 2.12 / 3.80 | 20, 0.54 | 36, 4.46 | 3.79 |
| 4k–8k | 60 | 423 | 7 | 2.68 / 3.64 | 19, 0.40 | 41, 4.07 | 4.68 |
| ≥ 8k | 11 | 1306 | 3 | 0.71 / 6.78 | 7, 0.03 | 4, 4.23 | 3.79 |
