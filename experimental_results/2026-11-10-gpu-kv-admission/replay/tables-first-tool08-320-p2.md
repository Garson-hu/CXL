## First admission attempts of `tool08-320-p2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 131 | 27 | 0 / 14 | 1 / 41 | 9 / 47 | 9 / 19 | 7 / 9 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 413 | 88 | 0 / 159 | 3 / 61 | 36 / 98 | 23 / 48 | 17 / 29 | 9 / 18 |

- external load, refused at the first attempt (27): blocks of the full sequence p10 / p50 / p90 = 210 / 416 / 461; free blocks 260 / 520 / 1696; needed / free p50 0.87; used share of the pool p10 / p50 0.773 / 0.930; gate {'full': 10, 'resv': 17}
- external load, admitted at the first attempt (104): blocks of the full sequence p50 / p90 = 386 / 535; free blocks p10 / p50 679 / 1923; smallest free / needed ratio 1.19
- compute request (miss or GPU-prefix hit), refused at the first attempt (88): blocks of the full sequence p10 / p50 / p90 = 306 / 934 / 1982; free blocks 127 / 657 / 1563; needed / free p50 1.13; used share of the pool p10 / p50 0.790 / 0.914; gate {'full': 88}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (325): blocks of the full sequence p50 / p90 = 197 / 827; free blocks p10 / p50 569 / 3263; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 1053152 tokens over 544 requests; 48 requests had lost part of it by the time they were admitted (176576 tokens, 16.8 %); 48 of them were then admitted as external loads

### External loads of `tool08-320-p2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 11 | 386 | 3 | 1.92 / 10.26 | 4, 18.59 | 7, 0.44 | 4.07 |
| 2k–4k | 55 | 203 | 8 | 7.02 / 11.39 | 19, 8.69 | 36, 5.18 | 10.59 |
| 4k–8k | 53 | 414 | 12 | 15.63 / 15.54 | 10, 12.85 | 43, 17.05 | 17.19 |
| ≥ 8k | 9 | 1030 | 2 | 0.65 / 7.14 | 2, 0.03 | 7, 0.67 | 3.56 |
