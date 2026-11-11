## First admission attempts of `x08c-conv-skip30` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 19 | 0 | 0 / 4 | 0 / 3 | 0 / 9 | 0 / 2 | 0 / 1 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 272 | 15 | 0 / 88 | 0 / 59 | 2 / 64 | 6 / 30 | 4 / 18 | 3 / 13 |

- external load, admitted at the first attempt (19): blocks of the full sequence p50 / p90 = 681 / 1977; free blocks p10 / p50 542 / 1243; smallest free / needed ratio 1.08
- compute request (miss or GPU-prefix hit), refused at the first attempt (15): blocks of the full sequence p10 / p50 / p90 = 917 / 1542 / 2009; free blocks 55 / 406 / 804; needed / free p50 3.38; used share of the pool p10 / p50 0.892 / 0.946; gate {'full': 15}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (257): blocks of the full sequence p50 / p90 = 464 / 1616; free blocks p10 / p50 402 / 2233; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 148480 tokens over 291 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `x08c-conv-skip30` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 3 | 100 | 0 | 13.95 / 13.03 | – | 3, 13.95 | 14.54 |
| 2k–4k | 4 | 216 | 0 | 21.80 / 14.19 | 1, 21.80 | 3, 6.96 | 23.48 |
| 4k–8k | 3 | 418 | 0 | 7.01 / 9.92 | 1, 3.36 | 2, 19.39 | 9.09 |
| ≥ 8k | 9 | 1030 | 1 | 10.44 / 10.40 | 4, 0.18 | 5, 16.86 | 12.69 |
