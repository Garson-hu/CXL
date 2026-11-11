## First admission attempts of `e-tool04-80-p7456-priolen-p1` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 91 | 4 | 0 / 70 | 2 / 11 | 0 / 7 | 1 / 2 | 1 / 1 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 1068 | 34 | 0 / 830 | 9 / 169 | 19 / 56 | 3 / 8 | 2 / 4 | 1 / 1 |

- external load, refused at the first attempt (4): blocks of the full sequence p10 / p50 / p90 = 386 / 1330 / 1505; free blocks 305 / 2124 / 2126; needed / free p50 1.27; used share of the pool p10 / p50 0.715 / 0.931; gate {'full': 2, 'resv': 2}
- external load, admitted at the first attempt (87): blocks of the full sequence p50 / p90 = 386 / 863; free blocks p10 / p50 2972 / 6096; smallest free / needed ratio 2.31
- compute request (miss or GPU-prefix hit), refused at the first attempt (34): blocks of the full sequence p10 / p50 / p90 = 597 / 1650 / 1999; free blocks 384 / 1527 / 1963; needed / free p50 1.05; used share of the pool p10 / p50 0.737 / 0.801; gate {'full': 34}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1034): blocks of the full sequence p50 / p90 = 386 / 1035; free blocks p10 / p50 2485 / 5811; smallest free / needed ratio 1.10
- GPU-cached prefix at the first visit: 3223488 tokens over 1159 requests; 3 requests had lost part of it by the time they were admitted (13024 tokens, 0.4 %); 3 of them were then admitted as external loads

### External loads of `e-tool04-80-p7456-priolen-p1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 12 | 212 | 0 | 0.32 / 0.28 | 5, 0.02 | 7, 0.48 | 1.37 |
| 2k–4k | 35 | 199 | 0 | 0.31 / 0.32 | 18, 0.02 | 17, 0.62 | 1.41 |
| 4k–8k | 29 | 411 | 2 | 0.29 / 0.70 | 15, 0.02 | 14, 0.63 | 0.67 |
| ≥ 8k | 16 | 1243 | 3 | 0.29 / 2.35 | 8, 0.02 | 8, 0.82 | 1.68 |
