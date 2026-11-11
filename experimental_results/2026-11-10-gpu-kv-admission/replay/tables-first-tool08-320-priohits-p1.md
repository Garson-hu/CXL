## First admission attempts of `tool08-320-priohits-p1` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 106 | 25 | 0 / 18 | 0 / 10 | 7 / 41 | 5 / 22 | 8 / 10 | 5 / 5 |
| compute request (miss or GPU-prefix hit) | 438 | 96 | 0 / 164 | 7 / 67 | 33 / 95 | 26 / 52 | 14 / 37 | 16 / 23 |

- external load, refused at the first attempt (25): blocks of the full sequence p10 / p50 / p90 = 197 / 387 / 789; free blocks 47 / 357 / 1300; needed / free p50 1.12; used share of the pool p10 / p50 0.826 / 0.952; gate {'full': 13, 'resv': 12}
- external load, admitted at the first attempt (81): blocks of the full sequence p50 / p90 = 381 / 532; free blocks p10 / p50 514 / 1439; smallest free / needed ratio 1.04
- compute request (miss or GPU-prefix hit), refused at the first attempt (96): blocks of the full sequence p10 / p50 / p90 = 115 / 827 / 1981; free blocks 70 / 602 / 1678; needed / free p50 1.11; used share of the pool p10 / p50 0.775 / 0.923; gate {'full': 96}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (342): blocks of the full sequence p50 / p90 = 197 / 846; free blocks p10 / p50 430 / 3443; smallest free / needed ratio 1.06
- GPU-cached prefix at the first visit: 1169520 tokens over 544 requests; 15 requests had lost part of it by the time they were admitted (39376 tokens, 3.4 %); 15 of them were then admitted as external loads

### External loads of `tool08-320-priohits-p1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 12 | 386 | 2 | 1.29 / 2.30 | 5, 0.70 | 7, 2.41 | 2.95 |
| 2k–4k | 39 | 199 | 7 | 0.54 / 1.68 | 10, 0.10 | 29, 0.60 | 2.32 |
| 4k–8k | 41 | 405 | 10 | 0.94 / 3.69 | 15, 0.06 | 26, 2.71 | 2.66 |
| ≥ 8k | 9 | 1030 | 2 | 0.37 / 5.78 | 2, 0.03 | 7, 0.38 | 2.88 |
