## First admission attempts of `e66-tool04-80-p7456-priolen-p1` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 92 | 4 | 0 / 70 | 2 / 12 | 1 / 9 | 0 / 0 | 1 / 1 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 1067 | 32 | 0 / 830 | 9 / 165 | 19 / 62 | 2 / 6 | 1 / 3 | 1 / 1 |

- external load, refused at the first attempt (4): blocks of the full sequence p10 / p50 / p90 = 389 / 1330 / 1505; free blocks 350 / 2122 / 2125; needed / free p50 1.11; used share of the pool p10 / p50 0.715 / 0.828; gate {'full': 2, 'resv': 2}
- external load, admitted at the first attempt (88): blocks of the full sequence p50 / p90 = 386 / 863; free blocks p10 / p50 2320 / 6096; smallest free / needed ratio 2.32
- compute request (miss or GPU-prefix hit), refused at the first attempt (32): blocks of the full sequence p10 / p50 / p90 = 852 / 1700 / 1999; free blocks 692 / 1527 / 1931; needed / free p50 1.06; used share of the pool p10 / p50 0.741 / 0.801; gate {'full': 32}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1035): blocks of the full sequence p50 / p90 = 386 / 1035; free blocks p10 / p50 2507 / 5811; smallest free / needed ratio 1.09
- GPU-cached prefix at the first visit: 3225808 tokens over 1159 requests; 3 requests had lost part of it by the time they were admitted (8144 tokens, 0.3 %); 3 of them were then admitted as external loads

### External loads of `e66-tool04-80-p7456-priolen-p1` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 14 | 212 | 0 | 0.35 / 0.41 | 6, 0.02 | 8, 0.52 | 1.61 |
| 2k–4k | 35 | 199 | 0 | 0.32 / 0.33 | 18, 0.02 | 17, 0.62 | 1.39 |
| 4k–8k | 27 | 413 | 1 | 0.05 / 0.46 | 15, 0.02 | 12, 0.62 | 0.36 |
| ≥ 8k | 16 | 1243 | 3 | 0.29 / 2.09 | 8, 0.02 | 8, 1.26 | 2.08 |
