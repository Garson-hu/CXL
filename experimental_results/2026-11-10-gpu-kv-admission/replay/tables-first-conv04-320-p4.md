## First admission attempts of `conv04-320-p4` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 101 | 0 | 0 / 80 | 0 / 13 | 0 / 7 | 0 / 1 | 0 / 0 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 498 | 6 | 0 / 368 | 0 / 81 | 1 / 35 | 4 / 10 | 0 / 2 | 1 / 2 |

- external load, admitted at the first attempt (101): blocks of the full sequence p50 / p90 = 612 / 1759; free blocks p10 / p50 2451 / 5783; smallest free / needed ratio 1.11
- compute request (miss or GPU-prefix hit), refused at the first attempt (6): blocks of the full sequence p10 / p50 / p90 = 843 / 1714 / 1999; free blocks 41 / 620 / 989; needed / free p50 3.51; used share of the pool p10 / p50 0.867 / 0.934; gate {'full': 6}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (492): blocks of the full sequence p50 / p90 = 499 / 1649; free blocks p10 / p50 2023 / 5771; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 306176 tokens over 599 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `conv04-320-p4` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 19 | 97 | 0 | 0.03 / 0.28 | 12, 0.02 | 7, 0.74 | 1.76 |
| 2k–4k | 15 | 248 | 0 | 0.03 / 0.35 | 9, 0.02 | 6, 0.87 | 1.76 |
| 4k–8k | 21 | 418 | 0 | 0.46 / 0.38 | 12, 0.02 | 9, 0.65 | 1.09 |
| ≥ 8k | 46 | 1255 | 0 | 0.03 / 1.21 | 27, 0.02 | 19, 0.86 | 1.89 |
