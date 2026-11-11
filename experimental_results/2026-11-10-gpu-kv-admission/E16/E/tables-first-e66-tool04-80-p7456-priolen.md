## First admission attempts of `e66-tool04-80-p7456-priolen` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 110 | 9 | 0 / 83 | 0 / 10 | 1 / 6 | 0 / 1 | 4 / 5 | 4 / 5 |
| compute request (miss or GPU-prefix hit) | 1049 | 33 | 0 / 794 | 2 / 132 | 10 / 66 | 6 / 35 | 9 / 12 | 6 / 10 |

- external load, refused at the first attempt (9): blocks of the full sequence p10 / p50 / p90 = 386 / 443 / 1987; free blocks 73 / 297 / 1845; needed / free p50 3.86; used share of the pool p10 / p50 0.753 / 0.960; gate {'full': 9}
- external load, admitted at the first attempt (101): blocks of the full sequence p50 / p90 = 357 / 623; free blocks p10 / p50 2619 / 5546; smallest free / needed ratio 1.49
- compute request (miss or GPU-prefix hit), refused at the first attempt (33): blocks of the full sequence p10 / p50 / p90 = 597 / 1463 / 1992; free blocks 62 / 414 / 1777; needed / free p50 2.42; used share of the pool p10 / p50 0.762 / 0.944; gate {'full': 33}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1016): blocks of the full sequence p50 / p90 = 386 / 1072; free blocks p10 / p50 1964 / 5783; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 3134016 tokens over 1159 requests; 6 requests had lost part of it by the time they were admitted (29200 tokens, 0.9 %); 6 of them were then admitted as external loads

### External loads of `e66-tool04-80-p7456-priolen` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 12 | 100 | 2 | 2.69 / 4.41 | 5, 0.02 | 7, 6.26 | 3.19 |
| 2k–4k | 42 | 199 | 0 | 1.19 / 2.11 | 20, 0.03 | 22, 4.00 | 2.49 |
| 4k–8k | 41 | 411 | 3 | 1.32 / 2.82 | 22, 0.02 | 19, 4.54 | 2.64 |
| ≥ 8k | 14 | 1243 | 3 | 0.50 / 7.33 | 7, 0.02 | 7, 7.93 | 5.87 |
