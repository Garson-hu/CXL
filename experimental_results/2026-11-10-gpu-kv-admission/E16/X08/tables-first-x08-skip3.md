## First admission attempts of `x08-skip3` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 126 | 20 | 0 / 10 | 0 / 14 | 1 / 41 | 3 / 37 | 11 / 19 | 5 / 5 |
| compute request (miss or GPU-prefix hit) | 418 | 50 | 0 / 153 | 0 / 59 | 6 / 91 | 15 / 50 | 14 / 33 | 15 / 32 |

- external load, refused at the first attempt (20): blocks of the full sequence p10 / p50 / p90 = 386 / 421 / 921; free blocks 65 / 243 / 725; needed / free p50 1.63; used share of the pool p10 / p50 0.920 / 0.970; gate {'full': 19, 'resv': 1}
- external load, admitted at the first attempt (106): blocks of the full sequence p50 / p90 = 386 / 458; free blocks p10 / p50 395 / 920; smallest free / needed ratio 1.06
- compute request (miss or GPU-prefix hit), refused at the first attempt (50): blocks of the full sequence p10 / p50 / p90 = 325 / 1252 / 1989; free blocks 47 / 242 / 961; needed / free p50 4.28; used share of the pool p10 / p50 0.882 / 0.969; gate {'full': 50}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (368): blocks of the full sequence p50 / p90 = 222 / 959; free blocks p10 / p50 373 / 2354; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 868944 tokens over 544 requests; 15 requests had lost part of it by the time they were admitted (40800 tokens, 4.7 %); 15 of them were then admitted as external loads

### External loads of `x08-skip3` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 7 | 391 | 2 | 18.49 / 15.96 | 5, 8.12 | 2, 20.45 | 20.48 |
| 2k–4k | 57 | 199 | 5 | 9.60 / 12.75 | 12, 8.70 | 45, 10.57 | 12.43 |
| 4k–8k | 48 | 408 | 12 | 17.98 / 18.73 | 24, 13.11 | 24, 21.43 | 19.85 |
| ≥ 8k | 9 | 1030 | 3 | 4.41 / 8.92 | 6, 4.41 | 3, 24.33 | 7.59 |
