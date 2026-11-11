## First admission attempts of `conv04-320-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 93 | 6 | 0 / 70 | 0 / 9 | 2 / 6 | 3 / 5 | 0 / 2 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 506 | 30 | 0 / 370 | 1 / 64 | 11 / 38 | 8 / 16 | 7 / 15 | 3 / 3 |

- external load, refused at the first attempt (6): blocks of the full sequence p10 / p50 / p90 = 200 / 1505 / 1992; free blocks 148 / 716 / 1110; needed / free p50 2.29; used share of the pool p10 / p50 0.851 / 0.920; gate {'full': 6}
- external load, admitted at the first attempt (87): blocks of the full sequence p50 / p90 = 568 / 1672; free blocks p10 / p50 2244 / 5644; smallest free / needed ratio 1.28
- compute request (miss or GPU-prefix hit), refused at the first attempt (30): blocks of the full sequence p10 / p50 / p90 = 347 / 1228 / 1999; free blocks 158 / 534 / 1246; needed / free p50 1.81; used share of the pool p10 / p50 0.850 / 0.929; gate {'full': 30}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (476): blocks of the full sequence p50 / p90 = 495 / 1649; free blocks p10 / p50 2036 / 5918; smallest free / needed ratio 1.10
- GPU-cached prefix at the first visit: 306176 tokens over 599 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `conv04-320-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 18 | 97 | 0 | 0.03 / 2.81 | 12, 0.02 | 6, 4.72 | 2.01 |
| 2k–4k | 15 | 248 | 2 | 0.18 / 3.99 | 9, 0.02 | 6, 5.46 | 2.39 |
| 4k–8k | 19 | 418 | 0 | 0.35 / 2.35 | 12, 0.03 | 7, 4.14 | 1.09 |
| ≥ 8k | 41 | 1150 | 6 | 0.03 / 3.89 | 26, 0.02 | 15, 7.87 | 2.65 |
