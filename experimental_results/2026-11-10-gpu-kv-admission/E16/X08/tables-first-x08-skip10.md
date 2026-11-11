## First admission attempts of `x08-skip10` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 115 | 4 | 0 / 15 | 0 / 12 | 0 / 37 | 0 / 37 | 3 / 13 | 1 / 1 |
| compute request (miss or GPU-prefix hit) | 429 | 34 | 0 / 158 | 0 / 59 | 6 / 94 | 9 / 74 | 13 / 31 | 6 / 13 |

- external load, refused at the first attempt (4): blocks of the full sequence p10 / p50 / p90 = 386 / 413 / 457; free blocks 66 / 256 / 306; needed / free p50 2.00; used share of the pool p10 / p50 0.959 / 0.969; gate {'full': 4}
- external load, admitted at the first attempt (111): blocks of the full sequence p50 / p90 = 386 / 532; free blocks p10 / p50 388 / 947; smallest free / needed ratio 1.01
- compute request (miss or GPU-prefix hit), refused at the first attempt (34): blocks of the full sequence p10 / p50 / p90 = 501 / 1201 / 1987; free blocks 78 / 338 / 800; needed / free p50 4.13; used share of the pool p10 / p50 0.893 / 0.956; gate {'full': 34}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (395): blocks of the full sequence p50 / p90 = 248 / 1080; free blocks p10 / p50 513 / 2354; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 845040 tokens over 544 requests; 13 requests had lost part of it by the time they were admitted (29168 tokens, 3.5 %); 13 of them were then admitted as external loads

### External loads of `x08-skip10` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 12 | 168 | 1 | 18.49 / 16.41 | 3, 14.52 | 9, 18.49 | 20.02 |
| 2k–4k | 47 | 199 | 2 | 6.64 / 8.60 | 15, 0.08 | 32, 9.02 | 8.08 |
| 4k–8k | 46 | 408 | 2 | 10.23 / 12.25 | 20, 6.39 | 26, 11.28 | 10.88 |
| ≥ 8k | 9 | 1030 | 1 | 1.32 / 8.83 | 6, 1.32 | 3, 24.71 | 7.70 |
