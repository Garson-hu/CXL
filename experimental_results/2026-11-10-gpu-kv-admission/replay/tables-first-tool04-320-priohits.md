## First admission attempts of `tool04-320-priohits` (pool 7456 blocks)

| kind | attempts | refused | refused / attempts by used share of the pool: < 50 % | 50–75 % | 75–90 % | 90–95 % | 95–98 % | ≥ 98 % |
|---|---|---|---|---|---|---|---|---|
| external load | 170 | 11 | 0 / 129 | 0 / 20 | 3 / 11 | 3 / 5 | 5 / 5 | 0 / 0 |
| compute request (miss or GPU-prefix hit) | 989 | 32 | 0 / 741 | 0 / 128 | 11 / 73 | 10 / 27 | 7 / 16 | 4 / 4 |

- external load, refused at the first attempt (11): blocks of the full sequence p10 / p50 / p90 = 257 / 443 / 1505; free blocks 159 / 404 / 1153; needed / free p50 1.32; used share of the pool p10 / p50 0.845 / 0.946; gate {'full': 10, 'resv': 1}
- external load, admitted at the first attempt (159): blocks of the full sequence p50 / p90 = 388 / 1275; free blocks p10 / p50 2204 / 5689; smallest free / needed ratio 1.17
- compute request (miss or GPU-prefix hit), refused at the first attempt (32): blocks of the full sequence p10 / p50 / p90 = 347 / 1254 / 1989; free blocks 102 / 420 / 1328; needed / free p50 1.80; used share of the pool p10 / p50 0.822 / 0.944; gate {'full': 32}
- compute request (miss or GPU-prefix hit), admitted at the first attempt (957): blocks of the full sequence p50 / p90 = 386 / 1024; free blocks p10 / p50 1940 / 5931; smallest free / needed ratio 1.05
- GPU-cached prefix at the first visit: 3167504 tokens over 1159 requests; 9 requests had lost part of it by the time they were admitted (34384 tokens, 1.1 %); 9 of them were then admitted as external loads

### External loads of `tool04-320-priohits` by length of the loaded prefix: wait from queueing to the admission of the load (s)

| loaded prefix (tokens) | n | blocks of the full sequence p50 | refused at least once | wait p50 / mean | no prefill in flight at arrival: n, wait p50 | prefill in flight at arrival: n, wait p50 | TTFT p50 |
|---|---|---|---|---|---|---|---|
| < 2k | 31 | 130 | 1 | 0.03 / 1.87 | 20, 0.02 | 11, 3.44 | 2.01 |
| 2k–4k | 52 | 199 | 4 | 1.18 / 2.25 | 25, 0.02 | 27, 3.65 | 2.39 |
| 4k–8k | 47 | 413 | 2 | 0.41 / 2.52 | 27, 0.02 | 20, 4.46 | 1.99 |
| ≥ 8k | 40 | 1150 | 4 | 0.03 / 2.91 | 25, 0.02 | 15, 4.77 | 2.89 |
