## First admission attempts of `tool08-320-p2-r2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 128 | 26 | 0 / 17 | 1 / 35 | 9 / 48 | 8 / 17 | 7 / 10 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 416 | 87 | 0 / 163 | 5 / 60 | 32 / 99 | 24 / 48 | 17 / 29 | 9 / 17 |

- external load, refused at the first attempt (26): blocks of the full sequence p10 / p50 / p90 = 210 / 416 / 461; free blocks 301 / 545 / 1696; needed / free p50 0.87; used share of the pool p10 / p50 0.773 / 0.931; gate {'full': 10, 'resv': 16}
- external load, admitted at the first attempt (102): blocks of the full sequence p50 / p90 = 386 / 535; free blocks p10 / p50 680 / 1872; smallest free / needed ratio 1.06
- compute request (miss or GPU-prefix hit), refused at the first attempt (87): blocks of the full sequence p10 / p50 / p90 = 325 / 954 / 1982; free blocks 138 / 653 / 1624; needed / free p50 1.13; used share of the pool p10 / p50 0.782 / 0.912; gate {'full': 87}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (329): blocks of the full sequence p50 / p90 = 197 / 815; free blocks p10 / p50 571 / 3384; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 1075440 tokens over 544 requests; 47 requests had lost part of it by the time they were admitted (178368 tokens, 16.6 %); 47 of them were then admitted as external loads

### External loads of `tool08-320-p2-r2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 11 | 386 | 3 | 2.21 / 10.30 | 4, 18.76 | 7, 0.44 | 4.48 |
| 2k–4k | 51 | 202 | 7 | 7.05 / 11.95 | 17, 8.73 | 34, 5.19 | 10.64 |
| 4k–8k | 54 | 414 | 12 | 15.38 / 15.24 | 11, 4.54 | 43, 17.01 | 17.09 |
| ≥ 8k | 9 | 1030 | 2 | 0.67 / 7.18 | 2, 0.03 | 7, 0.67 | 3.54 |
