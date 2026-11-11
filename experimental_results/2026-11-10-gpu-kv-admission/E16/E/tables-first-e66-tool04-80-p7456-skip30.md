## First admission attempts of `e66-tool04-80-p7456-skip30` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 114 | 0 | 0 / 78 | 0 / 13 | 0 / 9 | 0 / 10 | 0 / 4 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 1045 | 1 | 0 / 771 | 0 / 135 | 1 / 77 | 0 / 37 | 0 / 21 | 0 / 4 |

- external load, admitted at the first attempt (114): blocks of the full sequence p50 / p90 = 387 / 863; free blocks p10 / p50 645 / 5408; smallest free / needed ratio 1.14
- compute request (miss or GPU-prefix hit), refused at the first attempt (1): blocks of the full sequence p10 / p50 / p90 = 1992 / 1992 / 1992; free blocks 1479 / 1479 / 1479; needed / free p50 1.35; used share of the pool p10 / p50 0.802 / 0.802; gate {'full': 1}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1044): blocks of the full sequence p50 / p90 = 386 / 1201; free blocks p10 / p50 1343 / 5700; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 3111136 tokens over 1159 requests; 12 requests had lost part of it by the time they were admitted (44400 tokens, 1.4 %); 12 of them were then admitted as external loads

### External loads of `e66-tool04-80-p7456-skip30` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 15 | 200 | 0 | 2.69 / 4.85 | 6, 0.02 | 9, 8.99 | 3.20 |
| 2k–4k | 41 | 199 | 1 | 1.23 / 3.71 | 19, 0.02 | 22, 5.22 | 1.95 |
| 4k–8k | 41 | 418 | 1 | 2.00 / 4.31 | 21, 0.02 | 20, 4.82 | 2.88 |
| ≥ 8k | 17 | 1243 | 0 | 0.50 / 7.84 | 8, 0.02 | 9, 16.40 | 5.84 |
