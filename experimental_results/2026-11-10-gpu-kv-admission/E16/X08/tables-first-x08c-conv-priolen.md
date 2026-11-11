## First admission attempts of `x08c-conv-priolen` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 14 | 3 | 0 / 4 | 0 / 4 | 0 / 2 | 0 / 0 | 2 / 2 | 1 / 2 |
| compute request (miss or GPU-prefix hit) | 277 | 75 | 0 / 90 | 0 / 43 | 18 / 52 | 16 / 37 | 15 / 23 | 26 / 32 |

- external load, refused at the first attempt (3): blocks of the full sequence p10 / p50 / p90 = 216 / 871 / 1674; free blocks 145 / 228 / 341; needed / free p50 3.82; used share of the pool p10 / p50 0.954 / 0.969; gate {'full': 3}
- external load, admitted at the first attempt (11): blocks of the full sequence p50 / p90 = 418 / 921; free blocks p10 / p50 767 / 2952; smallest free / needed ratio 1.38
- compute request (miss or GPU-prefix hit), refused at the first attempt (75): blocks of the full sequence p10 / p50 / p90 = 421 / 1067 / 1983; free blocks 43 / 323 / 1059; needed / free p50 3.23; used share of the pool p10 / p50 0.858 / 0.957; gate {'full': 75}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (202): blocks of the full sequence p50 / p90 = 364 / 1287; free blocks p10 / p50 459 / 3031; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 148480 tokens over 291 requests; 0 requests had lost part of it by the time they were admitted (0 tokens, 0.0 %); 0 of them were then admitted as external loads

### External loads of `x08c-conv-priolen` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 2 | 100 | 0 | 2.61 / 1.34 | 1, 0.06 | 1, 2.61 | 12.71 |
| 2k–4k | 3 | 165 | 1 | 1.61 / 1.64 | 2, 2.43 | 1, 1.61 | 2.86 |
| 4k–8k | 3 | 418 | 0 | 3.87 / 3.58 | 1, 3.87 | 2, 4.22 | 8.38 |
| ≥ 8k | 6 | 921 | 2 | 3.19 / 5.46 | 4, 2.06 | 2, 20.77 | 7.41 |
