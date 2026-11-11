## First admission attempts of `t06-p2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 105 | 13 | 0 / 46 | 1 / 31 | 6 / 17 | 2 / 7 | 2 / 2 | 2 / 2 |
| compute request (miss or GPU-prefix hit) | 748 | 55 | 0 / 484 | 6 / 156 | 23 / 66 | 13 / 23 | 11 / 13 | 2 / 6 |

- external load, refused at the first attempt (13): blocks of the full sequence p10 / p50 / p90 = 312 / 438 / 1505; free blocks 112 / 746 / 1841; needed / free p50 0.42; used share of the pool p10 / p50 0.753 / 0.900; gate {'full': 4, 'resv': 9}
- external load, admitted at the first attempt (92): blocks of the full sequence p50 / p90 = 384 / 605; free blocks p10 / p50 1111 / 3788; smallest free / needed ratio 1.41
- compute request (miss or GPU-prefix hit), refused at the first attempt (55): blocks of the full sequence p10 / p50 / p90 = 282 / 852 / 1987; free blocks 249 / 806 / 1916; needed / free p50 1.07; used share of the pool p10 / p50 0.743 / 0.892; gate {'full': 55}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (693): blocks of the full sequence p50 / p90 = 362 / 1145; free blocks p10 / p50 1952 / 4968; smallest free / needed ratio 1.03
- GPU-cached prefix at the first visit: 2124960 tokens over 853 requests; 24 requests had lost part of it by the time they were admitted (79856 tokens, 3.8 %); 24 of them were then admitted as external loads

### External loads of `t06-p2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 16 | 271 | 2 | 14.17 / 9.47 | 1, 0.03 | 15, 14.17 | 17.45 |
| 2k–4k | 40 | 199 | 2 | 0.57 / 6.76 | 10, 0.47 | 30, 0.58 | 2.30 |
| 4k–8k | 38 | 438 | 8 | 9.92 / 14.75 | 10, 7.22 | 28, 21.43 | 11.48 |
| ≥ 8k | 9 | 1243 | 2 | 0.46 / 15.93 | 5, 0.03 | 4, 27.05 | 2.69 |
