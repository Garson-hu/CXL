## First admission attempts of `x08b-tokfast12` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 151 | 49 | 0 / 19 | 0 / 27 | 21 / 64 | 12 / 23 | 13 / 15 | 3 / 3 |
| compute request (miss or GPU-prefix hit) | 393 | 80 | 0 / 161 | 0 / 48 | 10 / 65 | 14 / 37 | 16 / 35 | 40 / 47 |

- external load, refused at the first attempt (49): blocks of the full sequence p10 / p50 / p90 = 198 / 405 / 469; free blocks 155 / 626 / 1577; needed / free p50 0.56; used share of the pool p10 / p50 0.788 / 0.916; gate {'full': 20, 'resv': 29}
- external load, admitted at the first attempt (102): blocks of the full sequence p50 / p90 = 386 / 458; free blocks p10 / p50 695 / 1769; smallest free / needed ratio 1.32
- compute request (miss or GPU-prefix hit), refused at the first attempt (80): blocks of the full sequence p10 / p50 / p90 = 255 / 954 / 1983; free blocks 9 / 155 / 846; needed / free p50 3.98; used share of the pool p10 / p50 0.892 / 0.980; gate {'full': 80}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (313): blocks of the full sequence p50 / p90 = 209 / 959; free blocks p10 / p50 450 / 3939; smallest free / needed ratio 1.03
- GPU-cached prefix at the first visit: 1085584 tokens over 544 requests; 43 requests had lost part of it by the time they were admitted (168064 tokens, 15.5 %); 43 of them were then admitted as external loads

### External loads of `x08b-tokfast12` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 24 | 186 | 3 | 8.57 / 9.52 | 9, 6.24 | 15, 8.57 | 11.61 |
| 2k–4k | 49 | 202 | 12 | 4.43 / 8.45 | 17, 5.94 | 32, 1.14 | 6.68 |
| 4k–8k | 57 | 418 | 19 | 9.28 / 11.00 | 18, 5.77 | 39, 10.89 | 10.81 |
| ≥ 8k | 9 | 1030 | 3 | 0.39 / 4.81 | 2, 0.03 | 7, 0.48 | 3.52 |
