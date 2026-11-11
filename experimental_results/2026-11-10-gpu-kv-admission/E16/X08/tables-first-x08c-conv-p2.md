## First admission attempts of `x08c-conv-p2` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 19 | 2 | 0 / 5 | 0 / 7 | 1 / 5 | 0 / 1 | 1 / 1 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 272 | 82 | 0 / 84 | 3 / 48 | 49 / 96 | 16 / 24 | 10 / 15 | 4 / 5 |

- external load, refused at the first attempt (2): blocks of the full sequence p10 / p50 / p90 = 565 / 1977 / 1977; free blocks 284 / 1650 / 1650; needed / free p50 1.99; used share of the pool p10 / p50 0.779 / 0.962; gate {'full': 2}
- external load, admitted at the first attempt (17): blocks of the full sequence p50 / p90 = 681 / 1674; free blocks p10 / p50 967 / 2326; smallest free / needed ratio 1.09
- compute request (miss or GPU-prefix hit), refused at the first attempt (82): blocks of the full sequence p10 / p50 / p90 = 421 / 1013 / 1983; free blocks 300 / 872 / 1615; needed / free p50 1.11; used share of the pool p10 / p50 0.783 / 0.887; gate {'full': 82}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (190): blocks of the full sequence p50 / p90 = 347 / 1321; free blocks p10 / p50 874 / 3031; smallest free / needed ratio 1.01
- GPU-cached prefix at the first visit: 148480 tokens over 291 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `x08c-conv-p2` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 3 | 100 | 1 | 2.89 / 8.60 | 1, 22.31 | 2, 2.89 | 4.61 |
| 2k–4k | 4 | 216 | 1 | 4.46 / 3.84 | 2, 4.46 | 2, 7.42 | 6.72 |
| 4k–8k | 3 | 418 | 0 | 0.97 / 2.89 | – | 3, 0.97 | 3.68 |
| ≥ 8k | 9 | 1030 | 4 | 1.49 / 9.56 | 3, 0.03 | 6, 19.72 | 11.76 |
