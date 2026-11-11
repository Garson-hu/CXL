## First admission attempts of `t06-priolen` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 144 | 23 | 0 / 74 | 0 / 17 | 0 / 15 | 2 / 14 | 12 / 15 | 9 / 9 |
| compute request (miss or GPU-prefix hit) | 709 | 40 | 0 / 432 | 1 / 143 | 9 / 70 | 11 / 29 | 13 / 24 | 6 / 11 |

- external load, refused at the first attempt (23): blocks of the full sequence p10 / p50 / p90 = 202 / 387 / 447; free blocks 86 / 230 / 372; needed / free p50 1.74; used share of the pool p10 / p50 0.950 / 0.969; gate {'full': 23}
- external load, admitted at the first attempt (121): blocks of the full sequence p50 / p90 = 386 / 566; free blocks p10 / p50 669 / 4468; smallest free / needed ratio 1.11
- compute request (miss or GPU-prefix hit), refused at the first attempt (40): blocks of the full sequence p10 / p50 / p90 = 347 / 1616 / 1993; free blocks 66 / 401 / 1294; needed / free p50 3.02; used share of the pool p10 / p50 0.834 / 0.949; gate {'full': 40}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (669): blocks of the full sequence p50 / p90 = 364 / 1116; free blocks p10 / p50 1241 / 4907; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 1937312 tokens over 853 requests; 18 requests had lost part of it by the time they were admitted (24912 tokens, 1.3 %); 18 of them were then admitted as external loads

### External loads of `t06-priolen` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 13 | 212 | 3 | 3.16 / 5.76 | 5, 0.02 | 8, 13.71 | 4.45 |
| 2k–4k | 55 | 199 | 4 | 2.04 / 3.31 | 19, 0.47 | 36, 3.73 | 3.35 |
| 4k–8k | 59 | 409 | 10 | 2.25 / 2.95 | 24, 0.67 | 35, 3.66 | 4.39 |
| ≥ 8k | 12 | 1306 | 2 | 0.42 / 15.38 | 7, 0.03 | 5, 12.64 | 5.69 |
