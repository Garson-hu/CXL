## First admission attempts of `x08-skip30` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 133 | 0 | 0 / 12 | 0 / 15 | 0 / 40 | 0 / 54 | 0 / 12 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 411 | 10 | 0 / 152 | 0 / 72 | 2 / 95 | 3 / 55 | 2 / 19 | 3 / 18 |

- external load, admitted at the first attempt (133): blocks of the full sequence p50 / p90 = 387 / 458; free blocks p10 / p50 384 / 752; smallest free / needed ratio 1.02
- compute request (miss or GPU-prefix hit), refused at the first attempt (10): blocks of the full sequence p10 / p50 / p90 = 1201 / 1981 / 2009; free blocks 49 / 435 / 1353; needed / free p50 11.83; used share of the pool p10 / p50 0.875 / 0.977; gate {'full': 10}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (401): blocks of the full sequence p50 / p90 = 339 / 1199; free blocks p10 / p50 479 / 2227; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 882288 tokens over 544 requests; 16 requests had lost part of it by the time they were admitted (35152 tokens, 4.0 %); 16 of them were then admitted as external loads

### External loads of `x08-skip30` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 12 | 186 | 0 | 12.92 / 12.58 | 2, 8.47 | 10, 18.49 | 13.55 |
| 2k–4k | 55 | 199 | 2 | 7.62 / 8.61 | 23, 5.33 | 32, 8.58 | 9.71 |
| 4k–8k | 57 | 414 | 2 | 8.01 / 10.51 | 29, 3.43 | 28, 10.40 | 10.17 |
| ≥ 8k | 9 | 1030 | 0 | 2.54 / 8.11 | 6, 2.54 | 3, 20.85 | 7.70 |
