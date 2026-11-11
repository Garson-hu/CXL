## First admission attempts of `e-tool04-80-p7456-p4` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 96 | 0 | 0 / 73 | 0 / 13 | 0 / 5 | 0 / 4 | 0 / 1 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 1063 | 7 | 0 / 819 | 1 / 166 | 3 / 57 | 3 / 15 | 0 / 6 | 0 / 0 |

- external load, admitted at the first attempt (96): blocks of the full sequence p50 / p90 = 395 / 997; free blocks p10 / p50 1759 / 5935; smallest free / needed ratio 1.08
- compute request (miss or GPU-prefix hit), refused at the first attempt (7): blocks of the full sequence p10 / p50 / p90 = 843 / 1700 / 1999; free blocks 451 / 989 / 1961; needed / free p50 1.99; used share of the pool p10 / p50 0.737 / 0.867; gate {'full': 7}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (1056): blocks of the full sequence p50 / p90 = 387 / 1170; free blocks p10 / p50 2172 / 5740; smallest free / needed ratio 1.02
- GPU-cached prefix at the first visit: 3232192 tokens over 1159 requests; 8 requests had lost part of it by the time they were admitted (20384 tokens, 0.6 %); 8 of them were then admitted as external loads

### External loads of `e-tool04-80-p7456-p4` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 14 | 230 | 1 | 0.34 / 1.68 | 5, 0.02 | 9, 0.53 | 1.68 |
| 2k–4k | 37 | 199 | 0 | 0.32 / 1.32 | 18, 0.02 | 19, 0.62 | 1.53 |
| 4k–8k | 28 | 422 | 0 | 0.29 / 1.22 | 15, 0.02 | 13, 0.78 | 0.67 |
| ≥ 8k | 17 | 1243 | 0 | 0.28 / 1.59 | 8, 0.02 | 9, 0.72 | 1.41 |
