## First admission attempts of `x08-skip30-nores` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 106 | 1 | 0 / 13 | 0 / 15 | 0 / 33 | 0 / 33 | 1 / 12 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 438 | 11 | 0 / 153 | 0 / 72 | 2 / 59 | 1 / 47 | 3 / 41 | 5 / 66 |

- external load, refused at the first attempt (1): blocks of the full sequence p10 / p50 / p90 = 445 / 445 / 445; free blocks 168 / 168 / 168; needed / free p50 2.65; used share of the pool p10 / p50 0.977 / 0.977; gate {'full': 1}
- external load, admitted at the first attempt (105): blocks of the full sequence p50 / p90 = 387 / 565; free blocks p10 / p50 368 / 895; smallest free / needed ratio 1.06
- compute request (miss or GPU-prefix hit), refused at the first attempt (11): blocks of the full sequence p10 / p50 / p90 = 1080 / 1700 / 1999; free blocks 37 / 160 / 751; needed / free p50 12.34; used share of the pool p10 / p50 0.899 / 0.979; gate {'full': 11}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (427): blocks of the full sequence p50 / p90 = 253 / 1145; free blocks p10 / p50 97 / 2042; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 818160 tokens over 544 requests; 14 requests had lost part of it by the time they were admitted (31312 tokens, 3.8 %); 14 of them were then admitted as external loads

### External loads of `x08-skip30-nores` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 7 | 413 | 1 | 11.08 / 8.85 | 3, 0.05 | 4, 13.08 | 12.86 |
| 2k–4k | 44 | 199 | 3 | 6.64 / 7.80 | 20, 8.56 | 24, 6.64 | 9.36 |
| 4k–8k | 46 | 414 | 7 | 4.62 / 10.06 | 23, 2.73 | 23, 9.12 | 5.34 |
| ≥ 8k | 9 | 1030 | 1 | 1.34 / 8.41 | 7, 1.34 | 2, 24.72 | 7.53 |
