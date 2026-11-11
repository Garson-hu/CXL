## First admission attempts of `tool04-320-tokfast11` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 171 | 15 | 0 / 125 | 1 / 22 | 6 / 14 | 5 / 7 | 2 / 2 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 988 | 31 | 0 / 776 | 0 / 141 | 7 / 40 | 8 / 13 | 8 / 10 | 8 / 8 |

- external load, refused at the first attempt (15): blocks of the full sequence p10 / p50 / p90 = 257 / 464 / 1992; free blocks 261 / 720 / 1674; needed / free p50 0.97; used share of the pool p10 / p50 0.775 / 0.903; gate {'full': 7, 'resv': 8}
- external load, admitted at the first attempt (156): blocks of the full sequence p50 / p90 = 422 / 1484; free blocks p10 / p50 2340 / 6094; smallest free / needed ratio 1.05
- compute request (miss or GPU-prefix hit), refused at the first attempt (31): blocks of the full sequence p10 / p50 / p90 = 279 / 1067 / 1987; free blocks 66 / 370 / 1198; needed / free p50 1.96; used share of the pool p10 / p50 0.839 / 0.950; gate {'full': 31}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (957): blocks of the full sequence p50 / p90 = 386 / 1013; free blocks p10 / p50 2608 / 5986; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 3247344 tokens over 1159 requests; 17 requests had lost part of it by the time they were admitted (50864 tokens, 1.6 %); 17 of them were then admitted as external loads

### External loads of `tool04-320-tokfast11` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 37 | 201 | 1 | 0.44 / 2.52 | 16, 0.02 | 21, 0.60 | 1.76 |
| 2k–4k | 44 | 200 | 2 | 0.36 / 2.15 | 23, 0.02 | 21, 0.62 | 1.79 |
| 4k–8k | 42 | 441 | 6 | 0.34 / 4.08 | 19, 0.02 | 23, 0.83 | 1.96 |
| ≥ 8k | 46 | 1255 | 4 | 0.03 / 2.33 | 28, 0.02 | 18, 0.72 | 1.38 |
