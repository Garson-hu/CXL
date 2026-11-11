## First admission attempts of `conv04-320-priolen` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 92 | 5 | 0 / 69 | 1 / 12 | 2 / 7 | 0 / 1 | 2 / 3 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 507 | 28 | 0 / 375 | 1 / 68 | 10 / 40 | 9 / 15 | 7 / 8 | 1 / 1 |

- external load, refused at the first attempt (5): blocks of the full sequence p10 / p50 / p90 = 1330 / 1505 / 1992; free blocks 248 / 1109 / 1950; needed / free p50 1.32; used share of the pool p10 / p50 0.738 / 0.851; gate {'full': 4, 'resv': 1}
- external load, admitted at the first attempt (87): blocks of the full sequence p50 / p90 = 565 / 1672; free blocks p10 / p50 2105 / 5921; smallest free / needed ratio 1.28
- compute request (miss or GPU-prefix hit), refused at the first attempt (28): blocks of the full sequence p10 / p50 / p90 = 563 / 1255 / 1999; free blocks 166 / 651 / 1302; needed / free p50 1.93; used share of the pool p10 / p50 0.825 / 0.935; gate {'full': 28}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (479): blocks of the full sequence p50 / p90 = 495 / 1649; free blocks p10 / p50 2037 / 5861; smallest free / needed ratio 1.04
- GPU-cached prefix at the first visit: 306176 tokens over 599 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `conv04-320-priolen` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 18 | 97 | 0 | 0.03 / 1.28 | 12, 0.02 | 6, 4.41 | 2.01 |
| 2k–4k | 15 | 248 | 1 | 0.18 / 1.98 | 10, 0.03 | 5, 3.03 | 2.39 |
| 4k–8k | 21 | 418 | 0 | 0.35 / 1.60 | 13, 0.02 | 8, 2.99 | 1.09 |
| ≥ 8k | 38 | 1243 | 6 | 0.03 / 4.28 | 25, 0.02 | 13, 7.80 | 2.63 |
