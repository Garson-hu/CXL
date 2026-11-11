## First admission attempts of `x08b-p2-sync` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 130 | 26 | 0 / 15 | 0 / 41 | 15 / 57 | 4 / 10 | 6 / 6 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 414 | 92 | 0 / 141 | 4 / 65 | 37 / 110 | 28 / 56 | 11 / 22 | 12 / 20 |

- external load, refused at the first attempt (26): blocks of the full sequence p10 / p50 / p90 = 258 / 416 / 456; free blocks 264 / 938 / 1473; needed / free p50 0.67; used share of the pool p10 / p50 0.802 / 0.875; gate {'full': 8, 'resv': 18}
- external load, admitted at the first attempt (104): blocks of the full sequence p50 / p90 = 386 / 535; free blocks p10 / p50 807 / 1943; smallest free / needed ratio 1.02
- compute request (miss or GPU-prefix hit), refused at the first attempt (92): blocks of the full sequence p10 / p50 / p90 = 291 / 917 / 1983; free blocks 97 / 704 / 1359; needed / free p50 1.15; used share of the pool p10 / p50 0.818 / 0.906; gate {'full': 92}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (322): blocks of the full sequence p50 / p90 = 196 / 796; free blocks p10 / p50 580 / 2620; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 993920 tokens over 544 requests; 43 requests had lost part of it by the time they were admitted (148784 tokens, 15.0 %); 43 of them were then admitted as external loads

### External loads of `x08b-p2-sync` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 28 | 210 | 3 | 15.03 / 14.76 | 6, 25.79 | 22, 15.03 | 16.38 |
| 2k–4k | 39 | 199 | 7 | 4.52 / 9.88 | 10, 1.57 | 29, 6.02 | 5.68 |
| 4k–8k | 52 | 418 | 16 | 19.37 / 20.65 | 12, 8.94 | 40, 24.86 | 21.17 |
| ≥ 8k | 9 | 1030 | 2 | 0.62 / 7.38 | 3, 0.21 | 6, 1.19 | 2.96 |
