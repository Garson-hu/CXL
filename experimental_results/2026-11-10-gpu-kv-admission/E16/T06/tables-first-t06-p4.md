## First admission attempts of `t06-p4` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 95 | 1 | 0 / 54 | 1 / 13 | 0 / 18 | 0 / 7 | 0 / 3 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 758 | 14 | 0 / 488 | 2 / 161 | 6 / 67 | 2 / 30 | 3 / 9 | 1 / 3 |

- external load, refused at the first attempt (1): blocks of the full sequence p10 / p50 / p90 = 1505 / 1505 / 1505; free blocks 2333 / 2333 / 2333; needed / free p50 0.65; used share of the pool p10 / p50 0.687 / 0.687; gate {'resv': 1}
- external load, admitted at the first attempt (94): blocks of the full sequence p50 / p90 = 281 / 623; free blocks p10 / p50 722 / 4204; smallest free / needed ratio 1.08
- compute request (miss or GPU-prefix hit), refused at the first attempt (14): blocks of the full sequence p10 / p50 / p90 = 843 / 1714 / 1992; free blocks 296 / 779 / 1904; needed / free p50 1.28; used share of the pool p10 / p50 0.745 / 0.898; gate {'full': 14}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (744): blocks of the full sequence p50 / p90 = 383 / 1201; free blocks p10 / p50 1341 / 4737; smallest free / needed ratio 1.00
- GPU-cached prefix at the first visit: 2083744 tokens over 853 requests; 6 requests had lost part of it by the time they were admitted (16816 tokens, 0.8 %); 6 of them were then admitted as external loads

### External loads of `t06-p4` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 21 | 153 | 0 | 7.20 / 12.91 | 5, 9.80 | 16, 7.20 | 8.12 |
| 2k–4k | 37 | 199 | 1 | 0.53 / 2.00 | 8, 0.25 | 29, 0.55 | 1.86 |
| 4k–8k | 28 | 423 | 1 | 0.61 / 3.66 | 11, 0.02 | 17, 0.66 | 2.20 |
| ≥ 8k | 9 | 1243 | 2 | 0.37 / 8.07 | 4, 0.03 | 5, 0.62 | 2.50 |
