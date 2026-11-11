## First admission attempts of `tool04-320-p2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 175 | 14 | 0 / 125 | 0 / 23 | 7 / 16 | 5 / 8 | 1 / 2 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 983 | 32 | 0 / 775 | 4 / 142 | 15 / 46 | 7 / 12 | 5 / 7 | 1 / 1 |

- external load, refused at the first attempt (14): blocks of the full sequence p10 / p50 / p90 = 387 / 464 / 1992; free blocks 260 / 837 / 1547; needed / free p50 1.09; used share of the pool p10 / p50 0.793 / 0.914; gate {'full': 7, 'resv': 7}
- external load, admitted at the first attempt (161): blocks of the full sequence p50 / p90 = 420 / 1467; free blocks p10 / p50 2125 / 5976; smallest free / needed ratio 1.05
- compute request (miss or GPU-prefix hit), refused at the first attempt (32): blocks of the full sequence p10 / p50 / p90 = 282 / 1080 / 1987; free blocks 262 / 835 / 1887; needed / free p50 1.12; used share of the pool p10 / p50 0.747 / 0.890; gate {'full': 32}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (951): blocks of the full sequence p50 / p90 = 386 / 1008; free blocks p10 / p50 2683 / 5990; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 3242816 tokens over 1158 requests; 22 requests had lost part of it by the time they were admitted (76176 tokens, 2.3 %); 22 of them were then admitted as external loads

### External loads of `tool04-320-p2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 38 | 210 | 2 | 0.46 / 2.94 | 17, 0.02 | 21, 0.65 | 1.79 |
| 2k–4k | 44 | 200 | 2 | 0.35 / 1.94 | 23, 0.02 | 21, 0.62 | 1.68 |
| 4k–8k | 45 | 435 | 6 | 0.49 / 5.54 | 20, 0.02 | 25, 0.99 | 2.17 |
| ≥ 8k | 46 | 1255 | 3 | 0.03 / 2.33 | 28, 0.02 | 18, 0.72 | 1.38 |
