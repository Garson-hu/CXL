## First admission attempts of `e66-tool04-80-p7456-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 130 | 21 | 0 / 70 | 0 / 9 | 1 / 21 | 7 / 15 | 10 / 12 | 3 / 3 |
| compute request (miss or GPU-prefix hit) | 1029 | 37 | 0 / 772 | 0 / 128 | 8 / 66 | 13 / 40 | 9 / 16 | 7 / 7 |

- external load, refused at the first attempt (21): blocks of the full sequence p10 / p50 / p90 = 386 / 443 / 1330; free blocks 145 / 315 / 436; needed / free p50 1.58; used share of the pool p10 / p50 0.942 / 0.958; gate {'full': 20, 'resv': 1}
- external load, admitted at the first attempt (109): blocks of the full sequence p50 / p90 = 386 / 685; free blocks p10 / p50 756 / 5126; smallest free / needed ratio 1.00
- compute request (miss or GPU-prefix hit), refused at the first attempt (37): blocks of the full sequence p10 / p50 / p90 = 155 / 1067 / 1992; free blocks 125 / 399 / 1115; needed / free p50 1.79; used share of the pool p10 / p50 0.850 / 0.946; gate {'full': 37}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (992): blocks of the full sequence p50 / p90 = 387 / 1138; free blocks p10 / p50 1955 / 5884; smallest free / needed ratio 1.03
- GPU-cached prefix at the first visit: 3103600 tokens over 1159 requests; 21 requests had lost part of it by the time they were admitted (96080 tokens, 3.1 %); 21 of them were then admitted as external loads

### External loads of `e66-tool04-80-p7456-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 13 | 200 | 2 | 1.40 / 5.90 | 6, 0.02 | 7, 6.27 | 2.02 |
| 2k–4k | 44 | 199 | 3 | 3.58 / 8.09 | 19, 0.03 | 25, 7.75 | 7.94 |
| 4k–8k | 53 | 415 | 11 | 5.78 / 10.73 | 18, 0.29 | 35, 16.73 | 10.43 |
| ≥ 8k | 16 | 997 | 3 | 0.03 / 6.66 | 9, 0.02 | 7, 13.73 | 1.38 |
