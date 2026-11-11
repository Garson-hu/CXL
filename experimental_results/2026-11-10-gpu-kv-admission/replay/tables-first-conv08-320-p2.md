## First admission attempts of `conv08-320-p2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 19 | 2 | 0 / 5 | 0 / 9 | 1 / 3 | 0 / 1 | 1 / 1 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 272 | 82 | 0 / 84 | 5 / 50 | 47 / 91 | 17 / 28 | 10 / 15 | 3 / 4 |

- external load, refused at the first attempt (2): blocks of the full sequence p10 / p50 / p90 = 565 / 1977 / 1977; free blocks 281 / 1516 / 1516; needed / free p50 2.01; used share of the pool p10 / p50 0.797 / 0.962; gate {'full': 2}
- external load, admitted at the first attempt (17): blocks of the full sequence p50 / p90 = 681 / 1674; free blocks p10 / p50 955 / 2640; smallest free / needed ratio 1.10
- compute request (miss or GPU-prefix hit), refused at the first attempt (82): blocks of the full sequence p10 / p50 / p90 = 421 / 1013 / 1983; free blocks 323 / 848 / 1614; needed / free p50 1.08; used share of the pool p10 / p50 0.784 / 0.887; gate {'full': 82}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (190): blocks of the full sequence p50 / p90 = 347 / 1321; free blocks p10 / p50 829 / 3031; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 148480 tokens over 291 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `conv08-320-p2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 3 | 100 | 1 | 3.34 / 8.72 | 1, 22.21 | 2, 3.34 | 4.78 |
| 2k–4k | 4 | 216 | 1 | 4.63 / 3.69 | 1, 2.41 | 3, 4.63 | 7.13 |
| 4k–8k | 3 | 418 | 0 | 0.93 / 7.18 | – | 3, 0.93 | 3.01 |
| ≥ 8k | 9 | 1030 | 3 | 1.89 / 9.45 | 3, 0.03 | 6, 19.04 | 11.43 |
