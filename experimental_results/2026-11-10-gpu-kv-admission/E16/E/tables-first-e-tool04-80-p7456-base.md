## First admission attempts of `e-tool04-80-p7456-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 131 | 21 | 0 / 71 | 0 / 9 | 1 / 21 | 7 / 15 | 10 / 12 | 3 / 3 |
| compute request (miss or GPU-prefix hit) | 1028 | 37 | 0 / 770 | 0 / 129 | 8 / 66 | 13 / 34 | 9 / 22 | 7 / 7 |

- external load, refused at the first attempt (21): blocks of the full sequence p10 / p50 / p90 = 386 / 443 / 1330; free blocks 146 / 315 / 437; needed / free p50 1.58; used share of the pool p10 / p50 0.941 / 0.958; gate {'full': 20, 'resv': 1}
- external load, admitted at the first attempt (110): blocks of the full sequence p50 / p90 = 386 / 685; free blocks p10 / p50 780 / 5172; smallest free / needed ratio 1.00
- compute request (miss or GPU-prefix hit), refused at the first attempt (37): blocks of the full sequence p10 / p50 / p90 = 155 / 1067 / 1992; free blocks 125 / 398 / 1116; needed / free p50 1.75; used share of the pool p10 / p50 0.850 / 0.947; gate {'full': 37}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (991): blocks of the full sequence p50 / p90 = 387 / 1138; free blocks p10 / p50 1955 / 5875; smallest free / needed ratio 1.03
- GPU-cached prefix at the first visit: 3103616 tokens over 1159 requests; 21 requests had lost part of it by the time they were admitted (96080 tokens, 3.1 %); 21 of them were then admitted as external loads

### External loads of `e-tool04-80-p7456-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 13 | 200 | 2 | 1.41 / 5.97 | 6, 0.02 | 7, 6.29 | 2.06 |
| 2k–4k | 45 | 199 | 3 | 3.46 / 7.97 | 19, 0.02 | 26, 7.77 | 7.26 |
| 4k–8k | 53 | 415 | 11 | 5.80 / 10.79 | 17, 0.20 | 36, 16.85 | 10.49 |
| ≥ 8k | 16 | 997 | 3 | 0.03 / 6.69 | 10, 0.02 | 6, 18.81 | 1.37 |
