## First admission attempts of `tool04-320-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 191 | 24 | 0 / 118 | 0 / 16 | 3 / 25 | 7 / 16 | 11 / 13 | 3 / 3 |
| compute request (miss or GPU-prefix hit) | 968 | 33 | 0 / 738 | 0 / 117 | 8 / 61 | 13 / 31 | 6 / 15 | 6 / 6 |

- external load, refused at the first attempt (24): blocks of the full sequence p10 / p50 / p90 = 312 / 450 / 1505; free blocks 139 / 353 / 906; needed / free p50 1.58; used share of the pool p10 / p50 0.878 / 0.953; gate {'full': 21, 'resv': 3}
- external load, admitted at the first attempt (167): blocks of the full sequence p50 / p90 = 387 / 1243; free blocks p10 / p50 881 / 5542; smallest free / needed ratio 1.00
- compute request (miss or GPU-prefix hit), refused at the first attempt (33): blocks of the full sequence p10 / p50 / p90 = 155 / 1067 / 1989; free blocks 130 / 420 / 1115; needed / free p50 1.91; used share of the pool p10 / p50 0.850 / 0.944; gate {'full': 33}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (935): blocks of the full sequence p50 / p90 = 386 / 1071; free blocks p10 / p50 1994 / 6058; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 3079696 tokens over 1159 requests; 20 requests had lost part of it by the time they were admitted (100960 tokens, 3.3 %); 20 of them were then admitted as external loads

### External loads of `tool04-320-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 30 | 200 | 2 | 0.26 / 3.96 | 18, 0.02 | 12, 6.33 | 2.09 |
| 2k–4k | 56 | 199 | 4 | 1.98 / 6.40 | 25, 0.02 | 31, 6.02 | 6.03 |
| 4k–8k | 61 | 417 | 11 | 4.48 / 8.80 | 28, 0.03 | 33, 13.46 | 5.98 |
| ≥ 8k | 40 | 1150 | 5 | 0.03 / 4.22 | 25, 0.02 | 15, 8.02 | 2.88 |
