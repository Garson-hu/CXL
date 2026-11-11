## First admission attempts of `tool08-320-p1` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 138 | 49 | 0 / 14 | 3 / 30 | 20 / 61 | 11 / 17 | 13 / 14 | 2 / 2 |
| compute request (miss or GPU-prefix hit) | 406 | 102 | 0 / 160 | 5 / 60 | 35 / 86 | 32 / 51 | 17 / 32 | 13 / 17 |

- external load, refused at the first attempt (49): blocks of the full sequence p10 / p50 / p90 = 196 / 405 / 565; free blocks 217 / 626 / 1760; needed / free p50 0.55; used share of the pool p10 / p50 0.764 / 0.916; gate {'full': 20, 'resv': 29}
- external load, admitted at the first attempt (89): blocks of the full sequence p50 / p90 = 386 / 469; free blocks p10 / p50 773 / 1844; smallest free / needed ratio 1.20
- compute request (miss or GPU-prefix hit), refused at the first attempt (102): blocks of the full sequence p10 / p50 / p90 = 255 / 836 / 1981; free blocks 93 / 607 / 1559; needed / free p50 1.13; used share of the pool p10 / p50 0.791 / 0.923; gate {'full': 102}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (304): blocks of the full sequence p50 / p90 = 198 / 846; free blocks p10 / p50 570 / 3998; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 989072 tokens over 544 requests; 35 requests had lost part of it by the time they were admitted (141680 tokens, 14.3 %); 35 of them were then admitted as external loads

### External loads of `tool08-320-p1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 7 | 386 | 2 | 6.67 / 11.04 | 1, 10.25 | 6, 6.67 | 8.92 |
| 2k–4k | 52 | 201 | 12 | 12.70 / 14.12 | 15, 10.11 | 37, 16.84 | 14.25 |
| 4k–8k | 57 | 414 | 20 | 20.94 / 21.85 | 19, 16.31 | 38, 20.94 | 22.95 |
| ≥ 8k | 9 | 1030 | 5 | 9.99 / 12.15 | 3, 0.03 | 6, 18.14 | 10.54 |
