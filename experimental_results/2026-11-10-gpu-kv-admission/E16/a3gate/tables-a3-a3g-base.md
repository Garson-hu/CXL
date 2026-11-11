### Table A3-1 — one probe under K = 6 decoding holders: external hit vs miss of the same length at three levels of free blocks

| probe (L + tail), target free / need, type | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| 1024 tok, 3×, host | 3 | 80 / 64 | 256 (256–258) | 0 | ok:3 | 0.00 | – | 0.33 (0.33–0.34) |
| 1024 tok, 3×, cold | 3 | 80 / 80 | 260 (260–260) | 0 | ok:3 | 0.00 | – | 0.35 (0.34–0.35) |
| 1024 tok, 1.5×, host | 3 | 80 / 64 | 140 (139–140) | 0 | ok:3 | 0.00 | – | 0.32 (0.32–0.34) |
| 1024 tok, 1.5×, cold | 3 | 80 / 80 | 139 (138–139) | 0 | ok:3 | 0.00 | – | 0.37 (0.35–0.37) |
| 1024 tok, 0.6×, host | 3 | 80 / 64 | 68 (68–68) | 0 | full:3 | 2.99 | 0.06 | 3.32 (3.32–3.32) |
| 1024 tok, 0.6×, cold | 3 | 80 / 80 | 64 (64–64) | 0 | full:3 | 3.01 | 0.08 | 3.36 (3.36–3.36) |
| 2048 tok, 3×, host | 3 | 144 / 128 | 447 (447–447) | 0 | ok:3 | 0.00 | – | 0.33 (0.33–0.33) |
| 2048 tok, 3×, cold | 3 | 144 / 128 | 447 (447–447) | 0 | ok:3 | 0.00 | – | 0.60 (0.60–0.61) |
| 2048 tok, 1.5×, host | 3 | 144 / 128 | 235 (235–235) | 0 | ok:3 | 0.00 | – | 0.33 (0.33–0.33) |
| 2048 tok, 1.5×, cold | 3 | 144 / 128 | 234 (233–235) | 0 | ok:3 | 0.00 | – | 0.61 (0.61–0.62) |
| 2048 tok, 0.6×, host | 3 | 144 / 128 | 104 (103–104) | 0 | full:3 | 3.01 | 0.07 | 3.33 (3.33–3.34) |
| 2048 tok, 0.6×, cold | 3 | 144 / 128 | 100 (100–100) | 0 | full:3 | 3.01 | 0.07 | 3.59 (3.59–3.59) |
| 4096 tok, 3×, host | 3 | 272 / 256 | 831 (831–831) | 0 | ok:3 | 0.00 | – | 0.35 (0.35–0.35) |
| 4096 tok, 3×, cold | 3 | 272 / 128 | 831 (831–831) | 0 | ok:3 | 0.00 | – | 1.04 (1.04–1.04) |
| 4096 tok, 1.5×, host | 3 | 272 / 256 | 424 (424–424) | 0 | ok:3 | 0.00 | – | 0.36 (0.36–0.36) |
| 4096 tok, 1.5×, cold | 3 | 272 / 128 | 424 (424–425) | 0 | ok:3 | 0.00 | – | 1.07 (1.06–1.07) |
| 4096 tok, 0.6×, host | 3 | 272 / 256 | 181 (180–181) | 0 | full:3 | 3.01 | 0.07 | 3.35 (3.34–3.36) |
| 4096 tok, 0.6×, cold | 3 | 272 / 128 | 178 (178–178) | 0 | full:3 | 2.99 | 0.06 | 4.00 (4.00–4.00) |
| 8192 tok, 3×, host | 3 | 528 / 512 | 1599 (1599–1599) | 0 | ok:3 | 0.00 | – | 0.33 (0.33–0.33) |
| 8192 tok, 3×, cold | 3 | 528 / 128 | 1599 (1599–1599) | 0 | ok:3 | 0.00 | – | 1.87 (1.87–1.87) |
| 8192 tok, 1.5×, host | 3 | 528 / 512 | 807 (807–807) | 0 | ok:3 | 0.00 | – | 0.36 (0.36–0.36) |
| 8192 tok, 1.5×, cold | 3 | 528 / 128 | 807 (807–807) | 0 | ok:3 | 0.00 | – | 1.95 (1.93–1.95) |
| 8192 tok, 0.6×, host | 3 | 528 / 512 | 335 (335–336) | 0 | full:3 | 3.00 | 0.07 | 3.37 (3.36–3.38) |
| 8192 tok, 0.6×, cold | 3 | 528 / 128 | 334 (334–334) | 0 | full:3 | 3.00 | 0.06 | 4.89 (4.89–4.90) |

### Table A3-2 — the same probe (4,096 + tail tokens) with 4 and 12 holders: the number of running requests at equal free blocks

| holders K, target free / need, type | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| K = 4, 1.5×, host | 2 | 272 / 256 | 419 (419–419) | 0 | ok:2 | 0.00 | – | 0.34 (0.34–0.34) |
| K = 4, 1.5×, cold | 2 | 272 / 128 | 419 (419–419) | 0 | ok:2 | 0.00 | – | 1.03 (1.03–1.03) |
| K = 4, 0.6×, host | 2 | 272 / 256 | 172 (171–172) | 0 | full:2 | 3.00 | 0.07 | 3.32 (3.31–3.32) |
| K = 4, 0.6×, cold | 2 | 272 / 128 | 172 (172–172) | 0 | full:2 | 3.00 | 0.07 | 3.98 (3.98–3.98) |
| K = 12, 1.5×, host | 2 | 272 / 256 | 435 (434–435) | 0 | ok:2 | 0.00 | – | 0.37 (0.37–0.37) |
| K = 12, 1.5×, cold | 2 | 272 / 128 | 435 (435–435) | 0 | ok:2 | 0.00 | – | 1.09 (1.09–1.09) |
| K = 12, 0.6×, host | 2 | 272 / 256 | 203 (203–203) | 0 | full:2 | 3.01 | 0.07 | 3.37 (3.37–3.37) |
| K = 12, 0.6×, cold | 2 | 272 / 128 | 196 (196–196) | 0 | full:2 | 3.01 | 0.07 | 4.07 (4.07–4.07) |

### Table A3-3 — two probes 5 ms apart, 700 free blocks targeted (not enough for both); a holder is released 3 s later

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| C4M8, #1: cold 4096 | 3 | 272 / 128 | 717 (717–717) | 0 | ok:3 | 0.00 | -2.94 | 1.04 (1.03–1.05) |
| C4M8, #2: cold 8192 | 3 | 528 / 111 | 445 (444–445) | 0 | full:3 | 0.98 | -1.55 | 3.33 (3.33–3.35) |
| H4M8, #1: host 4096 | 3 | 272 / 256 | 717 (717–717) | 0 | ok:3 | 0.00 | -2.93 | 0.35 (0.33–0.35) |
| H4M8, #2: cold 8192 | 3 | 528 / 128 | 461 (461–461) | 0 | full:3 | 0.70 | -2.23 | 2.65 (2.63–2.65) |
| M8C4, #1: cold 8192 | 3 | 528 / 128 | 717 (717–717) | 0 | ok:3 | 0.00 | -2.93 | 1.95 (1.94–1.96) |
| M8C4, #2: cold 4096 | 3 | 272 / 111 | 189 (188–189) | 0 | full:3 | 1.04 | -0.63 | 3.34 (3.33–3.35) |
| M8H4, #1: cold 8192 | 3 | 528 / 128 | 717 (717–717) | 0 | ok:3 | 0.00 | -2.94 | 1.95 (1.94–1.95) |
| M8H4, #2: host 4096 | 3 | 272 / 256 | 189 (189–189) | 0 | full:3 | 1.04 | -0.63 | 2.64 (2.64–2.65) |

### Table A3-5 — two probes 5 ms apart, no memory pressure (more than 5,000 free blocks)

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| H4M8, #1: host 4096 | 3 | 272 / 256 | 5505 (5505–5505) | 0 | ok:3 | 0.00 | – | 1.71 (1.69–1.72) |
| H4M8, #2: cold 8192 | 3 | 528 / 128 | 5249 (5249–5249) | 0 | ok:3 | 0.00 | – | 1.64 (1.63–1.69) |
| M8H4, #1: cold 8192 | 3 | 528 / 128 | 5505 (5505–5505) | 0 | ok:3 | 0.00 | – | 1.64 (1.63–1.64) |
| M8H4, #2: host 4096 | 3 | 272 / 256 | 4977 (4977–4977) | 0 | ok:3 | 0.00 | – | 1.78 (1.78–1.79) |

### Table A3-4 — bursts of 4 and 8 probes of 2,048 + tail tokens, alternating external hit / miss, free blocks for half of the burst

| burst | type | n | admitted at the first attempt | admitted before the release | refused first: gate full / free / resv | TTFT p50 (s) | admitted after the release p50 (s) |
|---|---|---|---|---|---|---|---|
| n4-coldfirst | host | 4 | 2 | 4 | 2 / 0 / 0 | 2.03 | – |
| n4-coldfirst | cold | 4 | 2 | 4 | 2 / 0 / 0 | 1.70 | – |
| n4-hostfirst | host | 4 | 2 | 4 | 2 / 0 / 0 | 1.83 | – |
| n4-hostfirst | cold | 4 | 2 | 4 | 2 / 0 / 0 | 1.75 | – |
| n8-coldfirst | host | 8 | 8 | 8 | 0 / 0 / 0 | 2.86 | – |
| n8-coldfirst | cold | 8 | 4 | 8 | 4 / 0 / 0 | 2.21 | – |
| n8-hostfirst | host | 8 | 4 | 8 | 4 / 0 / 0 | 2.37 | – |
| n8-hostfirst | cold | 8 | 4 | 8 | 4 / 0 / 0 | 2.22 | – |

### Table A3-6 — phases of the probes (seconds, median): lookup result → admitted, load, promotion, compute

| group | type | n | queued → first visit | lookup | admit | load | promote | compute | TTFT |
|---|---|---|---|---|---|---|---|---|---|
| part 1 | host | 36 | 0.000 | 0.050 | 0.000 | 0.127 | 0.001 | 0.142 | 0.362 |
| part 1 | cold | 36 | 0.000 | 0.050 | 0.000 | – | – | 0.936 | 1.870 |
| part 2 | host | 8 | 0.000 | 0.050 | 3.000 | 0.127 | 0.001 | 0.163 | 3.314 |
| part 2 | cold | 8 | 0.000 | 0.050 | 2.999 | – | – | 0.997 | 3.977 |
| part 3 | host | 6 | 0.000 | 1.316 | 1.036 | 0.124 | 0.001 | 0.152 | 2.642 |
| part 3 | cold | 18 | 0.000 | 0.049 | 0.565 | – | – | 1.877 | 2.632 |
| part 4 | host | 24 | 0.001 | 0.466 | 0.000 | 0.607 | 0.001 | 0.154 | 1.831 |
| part 4 | cold | 24 | 0.001 | 0.076 | 0.024 | – | – | 0.598 | 1.703 |
| part 5 | host | 6 | 0.000 | 1.107 | 0.000 | 1.097 | 0.001 | 0.162 | 1.778 |
| part 5 | cold | 6 | 0.000 | 0.027 | 0.000 | – | – | 1.590 | 1.639 |
