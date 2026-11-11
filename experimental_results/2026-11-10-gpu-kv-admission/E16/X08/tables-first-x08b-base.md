## First admission attempts of `x08b-base` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 122 | 43 | 0 / 11 | 0 / 15 | 2 / 30 | 4 / 22 | 23 / 30 | 14 / 14 |
| compute request (miss or GPU-prefix hit) | 422 | 73 | 0 / 176 | 0 / 48 | 9 / 67 | 15 / 45 | 23 / 47 | 26 / 39 |

- external load, refused at the first attempt (43): blocks of the full sequence p10 / p50 / p90 = 216 / 408 / 532; free blocks 37 / 235 / 404; needed / free p50 1.76; used share of the pool p10 / p50 0.946 / 0.968; gate {'full': 41, 'resv': 2}
- external load, admitted at the first attempt (79): blocks of the full sequence p50 / p90 = 281 / 448; free blocks p10 / p50 395 / 1222; smallest free / needed ratio 1.16
- compute request (miss or GPU-prefix hit), refused at the first attempt (73): blocks of the full sequence p10 / p50 / p90 = 101 / 954 / 1981; free blocks 21 / 242 / 791; needed / free p50 2.74; used share of the pool p10 / p50 0.894 / 0.968; gate {'full': 73}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (349): blocks of the full sequence p50 / p90 = 207 / 997; free blocks p10 / p50 323 / 3875; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 961664 tokens over 544 requests; 30 requests had lost part of it by the time they were admitted (88976 tokens, 9.3 %); 30 of them were then admitted as external loads

### External loads of `x08b-base` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 8 | 210 | 5 | 17.45 / 21.09 | 3, 17.45 | 5, 10.30 | 18.24 |
| 2k–4k | 45 | 199 | 9 | 15.44 / 13.58 | 16, 16.44 | 29, 9.97 | 16.27 |
| 4k–8k | 52 | 413 | 20 | 22.10 / 21.53 | 25, 16.13 | 27, 23.82 | 23.48 |
| ≥ 8k | 7 | 921 | 4 | 7.84 / 11.69 | 3, 4.77 | 4, 23.87 | 11.19 |
