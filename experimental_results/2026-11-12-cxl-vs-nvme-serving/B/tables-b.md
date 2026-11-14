# Experiment B — end-to-end cache expansion (trace replays; one run per cell)

## conversation, trace 0–400 s at 0.08× (high load)

| configuration | requests ok / all | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| recompute only (vLLM alone) | 1177 / 1177 | 0.045 | 0.045 | 0.000 | 0.000 | 0.000 | 12.85 | 22.84 | 74.64 | 95.47 | 27.90 | 42.64 | 107.21 | 0.235 | 80 | 2564 | 0.90 | 37 |
| DRAM only 80 GiB | 1177 / 1177 | 0.096 | 0.045 | 0.051 | 0.000 | 0.000 | 12.17 | 16.71 | 61.94 | 82.90 | 22.42 | 33.87 | 92.14 | 0.235 | 80 | 2430 | 0.88 | 34 |
| DRAM + CXL hybrid L1 | 1177 / 1177 | 0.238 | 0.045 | 0.078 | 0.116 | 0.000 | 10.25 | 8.67 | 41.89 | 56.48 | 13.32 | 24.02 | 68.32 | 0.235 | 80 | 2047 | 0.81 | 25 |
| DRAM + CXL L2 adapter | 1177 / 1177 | 0.238 | 0.045 | 0.044 | 0.000 | 0.149 | 10.25 | 8.62 | 41.24 | 55.35 | 13.23 | 23.90 | 67.92 | 0.235 | 80 | 2047 | 0.81 | 25 |
| DRAM + NVMe L2 adapter | 1177 / 1177 | 0.238 | 0.045 | 0.045 | 0.000 | 0.149 | 10.25 | 8.62 | 41.81 | 55.98 | 13.25 | 23.86 | 67.91 | 0.235 | 80 | 2047 | 0.81 | 25 |
| DRAM only 592 GiB (reference) | 1177 / 1177 | 0.238 | 0.045 | 0.194 | 0.000 | 0.000 | 10.25 | 8.65 | 41.79 | 57.06 | 13.34 | 23.80 | 68.76 | 0.235 | 80 | 2047 | 0.81 | 25 |
| DRAM only 20 GiB | 1177 / 1177 | 0.048 | 0.045 | 0.003 | 0.000 | 0.000 | 12.81 | 22.66 | 70.00 | 91.09 | 27.59 | 42.10 | 102.61 | 0.235 | 80 | 2555 | 0.90 | 35 |
| 20 GiB DRAM + CXL hybrid L1 | 1177 / 1177 | 0.238 | 0.045 | 0.021 | 0.173 | 0.000 | 10.25 | 8.69 | 41.93 | 56.52 | 13.35 | 24.01 | 68.39 | 0.235 | 80 | 2047 | 0.81 | 25 |
| 20 GiB DRAM + NVMe L2 adapter | 1177 / 1177 | 0.238 | 0.045 | 0.004 | 0.000 | 0.190 | 10.25 | 8.62 | 41.25 | 56.30 | 13.25 | 23.82 | 67.89 | 0.235 | 80 | 2047 | 0.81 | 25 |

| configuration | L1 max GiB (of) | L2 max GiB (of) | L1 evicted GiB DRAM / CXL | L2 evicted keys | L1 written GiB DRAM / CXL | L2 stored / loaded GiB | LMCache RSS max GiB (anon + shmem) | vLLM RSS max GiB | MemAvailable min GiB | page cache growth GiB | LMCache CPU s (cores) | NVMe device read / written GiB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 64.1 (80) | - (-) | 370.7 / 0.0 | 0 | 425.5 / 0.0 | 0.0 / 0.0 | 81.0 (80.5 + 0.0) | 3.5 | 644 | 0.21 | 51 (0.01) | 0.0 / 0.2 |
| DRAM + CXL hybrid L1 | 359.6 (592) | - (-) | 0.0 / 0.0 | 0 | 80.0 / 279.6 | 0.0 / 0.0 | 81.0 (0.6 + 80.0) | 3.5 | 638 | 0.48 | 56 (0.01) | 0.0 / 0.2 |
| DRAM + CXL L2 adapter | 64.1 (80) | 359.5 (512) | 376.3 / 0.0 | 0 | 359.7 / 0.0 | 359.7 / 69.0 | 81.0 (80.6 + 0.0) | 3.5 | 649 | 0.14 | 123 (0.02) | 0.0 / 0.2 |
| DRAM + NVMe L2 adapter | 64.1 (80) | 359.5 (512) | 375.2 / 0.0 | 0 | 359.6 / 0.0 | 359.5 / 68.7 | 81.0 (80.5 + 0.0) | 3.5 | 644 | 0.18 | 61 (0.01) | 68.7 / 360.4 |
| DRAM only 592 GiB (reference) | 359.5 (592) | - (-) | 0.0 / 0.0 | 0 | 359.5 / 0.0 | 0.0 / 0.0 | 593.1 (592.6 + 0.0) | 3.5 | 125 | 0.65 | 98 (0.02) | 0.0 / 0.2 |
| DRAM only 20 GiB | 16.2 (20) | - (-) | 433.3 / 0.0 | 0 | 447.6 / 0.0 | 0.0 / 0.0 | 20.9 (20.5 + 0.0) | 3.5 | 705 | 0.13 | 47 (0.01) | 0.0 / 0.2 |
| 20 GiB DRAM + CXL hybrid L1 | 359.5 (532) | - (-) | 0.0 / 0.0 | 0 | 20.0 / 339.6 | 0.0 / 0.0 | 21.0 (0.6 + 20.0) | 3.5 | 699 | 0.13 | 55 (0.01) | 0.0 / 0.2 |
| 20 GiB DRAM + NVMe L2 adapter | 17.1 (20) | 359.5 (512) | 434.7 / 0.0 | 0 | 359.6 / 0.0 | 359.5 / 87.7 | 21.0 (20.5 + 0.0) | 3.5 | 705 | 0.14 | 59 (0.01) | 87.7 / 360.4 |

TTFT by the dominant source of the prompt (a request is in a class when at least half of its prompt tokens came from that source; p50 s, n):

| configuration | extension tier (CXL L1 or L2) | DRAM tier | GPU prefix | miss (< 10 % cached) | L2 prefetch inside the cache server, all requests that loaded from the L2: p50 / p95 / max ms (n) |
|---|---|---|---|---|---|
| DRAM only 80 GiB | - (0) | 18.42 (53) | 12.78 (116) | 17.95 (708) | – |
| DRAM + CXL hybrid L1 | 6.08 (108) | 8.18 (68) | 5.82 (116) | 10.65 (576) | – |
| DRAM + CXL L2 adapter | 6.28 (130) | 9.43 (50) | 5.83 (116) | 10.58 (576) | 12.3 / 79.5 / 273.9 (191) |
| DRAM + NVMe L2 adapter | 6.27 (131) | 9.62 (49) | 5.82 (116) | 10.59 (576) | 106.0 / 384.1 / 652.4 (193) |
| DRAM only 592 GiB (reference) | - (0) | 7.07 (183) | 5.81 (116) | 10.65 (576) | – |
| DRAM only 20 GiB | - (0) | 48.84 (2) | 16.00 (116) | 23.74 (759) | – |
| 20 GiB DRAM + CXL hybrid L1 | 7.07 (160) | 10.00 (22) | 5.86 (116) | 10.63 (576) | – |
| 20 GiB DRAM + NVMe L2 adapter | 7.07 (180) | 24.06 (3) | 5.81 (116) | 10.60 (576) | 103.5 / 427.8 / 723.1 (262) |

Requests served mainly from the extension tier (at least half of the prompt from CXL L1 objects or from the L2): parts of the TTFT, p50 ms (n). The lookup interval ends at the poll of vLLM's scheduler that finds the prefetch complete, so it contains the wait for that poll; the L2 prefetch is the part inside the cache server.

| configuration | n | TTFT | lookup interval | of which L2 prefetch | GPU transfer | queued → scheduled | KV ready → scheduled | scheduled → first token |
|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | 108 | 6076 | 471 | - | 98 | 5878 | 0 | 239 |
| DRAM + CXL L2 adapter | 130 | 6282 | 529 | 19 | 110 | 5468 | 0 | 245 |
| DRAM + NVMe L2 adapter | 131 | 6265 | 545 | 170 | 108 | 5462 | 0 | 248 |
| 20 GiB DRAM + CXL hybrid L1 | 160 | 7074 | 498 | - | 104 | 6182 | 0 | 241 |
| 20 GiB DRAM + NVMe L2 adapter | 180 | 7070 | 534 | 146 | 105 | 5971 | 0 | 247 |

The same requests by the length of the prefix that came from the extension tier — L2 prefetch p50 / lookup interval p50 / TTFT p50 in ms (n):

| configuration | < 4K | 4K–8K | 8K–16K | ≥ 16K |
|---|---|---|---|---|
| DRAM + CXL hybrid L1 | - / 470 / 7590 (22) | - / 361 / 1516 (25) | - / 530 / 9697 (25) | - / 522 / 11320 (36) |
| DRAM + CXL L2 adapter | 5 / 480 / 5125 (24) | 9 / 614 / 8121 (22) | 16 / 529 / 6961 (37) | 46 / 522 / 5665 (47) |
| DRAM + NVMe L2 adapter | 37 / 523 / 5166 (25) | 72 / 613 / 8120 (23) | 146 / 573 / 6960 (37) | 325 / 465 / 5516 (46) |
| 20 GiB DRAM + CXL hybrid L1 | - / 482 / 7586 (35) | - / 495 / 2814 (34) | - / 498 / 6990 (34) | - / 522 / 7389 (57) |
| 20 GiB DRAM + NVMe L2 adapter | 37 / 569 / 7556 (39) | 76 / 515 / 6004 (37) | 139 / 577 / 6993 (44) | 304 / 521 / 7602 (60) |

Paired comparison, the same request of the trace in two configurations (first minus second; negative = the first is faster):

| pair | requests | mean TTFT difference s | median difference s | share of requests faster in the first | requests that are extension-tier hits in both | their median TTFT difference ms | their median lookup-interval difference ms |
|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 − DRAM + NVMe L2 adapter | 1177 | +0.07 | +0.01 | 0.31 | 69 | 1 | -7 |
| DRAM + CXL L2 adapter − DRAM + NVMe L2 adapter | 1177 | -0.03 | -0.01 | 0.67 | 129 | -32 | -2 |
| DRAM + CXL hybrid L1 − DRAM + CXL L2 adapter | 1177 | +0.09 | +0.03 | 0.21 | 68 | 12 | -0 |
| DRAM + CXL hybrid L1 − DRAM only 80 GiB | 1177 | -9.10 | -2.47 | 0.76 | 0 | - | - |
| DRAM + NVMe L2 adapter − DRAM only 80 GiB | 1177 | -9.17 | -2.53 | 0.79 | 0 | - | - |
| DRAM only 80 GiB − recompute only (vLLM alone) | 1177 | -5.48 | -1.57 | 0.70 | 0 | - | - |
| DRAM + CXL hybrid L1 − DRAM only 592 GiB (reference) | 1177 | -0.02 | +0.03 | 0.18 | 0 | - | - |
| 20 GiB DRAM + CXL hybrid L1 − 20 GiB DRAM + NVMe L2 adapter | 1177 | +0.10 | +0.02 | 0.22 | 157 | 11 | 0 |
| 20 GiB DRAM + CXL hybrid L1 − DRAM only 20 GiB | 1177 | -14.24 | -7.29 | 0.79 | 0 | - | - |
| 20 GiB DRAM + NVMe L2 adapter − DRAM only 20 GiB | 1177 | -14.34 | -7.54 | 0.87 | 0 | - | - |

## tool-agent, trace 0–400 s at 0.08× (high load)

| configuration | requests ok / all | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| recompute only (vLLM alone) | 2332 / 2332 | 0.274 | 0.274 | 0.000 | 0.000 | 0.000 | 14.10 | 32.86 | 102.58 | 123.20 | 40.70 | 46.31 | 124.88 | 0.465 | 83 | 2815 | 0.93 | 103 |
| DRAM only 80 GiB | 2332 / 2332 | 0.396 | 0.255 | 0.141 | 0.000 | 0.000 | 11.72 | 12.40 | 60.31 | 83.18 | 19.78 | 23.44 | 82.49 | 0.466 | 84 | 2343 | 0.86 | 60 |
| DRAM + CXL hybrid L1 | 2332 / 2332 | 0.495 | 0.276 | 0.140 | 0.079 | 0.000 | 9.81 | 6.30 | 39.64 | 58.66 | 11.60 | 15.13 | 61.99 | 0.466 | 84 | 1961 | 0.79 | 44 |
| DRAM + CXL L2 adapter | 2332 / 2332 | 0.495 | 0.277 | 0.116 | 0.000 | 0.102 | 9.81 | 6.29 | 39.49 | 58.37 | 11.47 | 14.90 | 61.54 | 0.466 | 84 | 1961 | 0.79 | 44 |
| DRAM + NVMe L2 adapter | 2332 / 2332 | 0.495 | 0.278 | 0.115 | 0.000 | 0.102 | 9.81 | 6.31 | 39.36 | 58.38 | 11.47 | 14.93 | 61.39 | 0.466 | 84 | 1961 | 0.79 | 44 |

| configuration | L1 max GiB (of) | L2 max GiB (of) | L1 evicted GiB DRAM / CXL | L2 evicted keys | L1 written GiB DRAM / CXL | L2 stored / loaded GiB | LMCache RSS max GiB (anon + shmem) | vLLM RSS max GiB | MemAvailable min GiB | page cache growth GiB | LMCache CPU s (cores) | NVMe device read / written GiB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 64.1 (80) | - (-) | 345.2 / 0.0 | 0 | 406.4 / 0.0 | 0.0 / 0.0 | 81.0 (80.5 + 0.0) | 3.5 | 644 | 0.14 | 52 (0.01) | 0.0 / 0.2 |
| DRAM + CXL hybrid L1 | 340.9 (592) | - (-) | 0.0 / 0.0 | 0 | 80.0 / 260.9 | 0.0 / 0.0 | 81.0 (0.6 + 80.0) | 3.5 | 638 | 0.14 | 58 (0.01) | 0.0 / 0.2 |
| DRAM + CXL L2 adapter | 64.1 (80) | 340.9 (512) | 349.3 / 0.0 | 0 | 341.0 / 0.0 | 341.0 / 67.9 | 81.0 (80.6 + 0.0) | 3.5 | 650 | 0.15 | 122 (0.02) | 0.0 / 0.2 |
| DRAM + NVMe L2 adapter | 64.0 (80) | 340.9 (512) | 348.8 / 0.0 | 0 | 341.0 / 0.0 | 341.0 / 67.9 | 81.0 (80.5 + 0.0) | 3.5 | 649 | 0.18 | 64 (0.01) | 67.9 / 341.8 |

TTFT by the dominant source of the prompt (a request is in a class when at least half of its prompt tokens came from that source; p50 s, n):

| configuration | extension tier (CXL L1 or L2) | DRAM tier | GPU prefix | miss (< 10 % cached) | L2 prefetch inside the cache server, all requests that loaded from the L2: p50 / p95 / max ms (n) |
|---|---|---|---|---|---|
| DRAM only 80 GiB | - (0) | 23.96 (485) | 6.38 (924) | 15.78 (631) | – |
| DRAM + CXL hybrid L1 | 4.39 (105) | 15.67 (419) | 1.97 (1005) | 9.35 (501) | – |
| DRAM + CXL L2 adapter | 4.54 (127) | 16.17 (397) | 1.91 (1007) | 9.26 (501) | 12.7 / 73.7 / 257.4 (202) |
| DRAM + NVMe L2 adapter | 4.55 (128) | 15.64 (390) | 1.97 (1012) | 9.27 (501) | 103.9 / 382.1 / 663.0 (202) |

Requests served mainly from the extension tier (at least half of the prompt from CXL L1 objects or from the L2): parts of the TTFT, p50 ms (n). The lookup interval ends at the poll of vLLM's scheduler that finds the prefetch complete, so it contains the wait for that poll; the L2 prefetch is the part inside the cache server.

| configuration | n | TTFT | lookup interval | of which L2 prefetch | GPU transfer | queued → scheduled | KV ready → scheduled | scheduled → first token |
|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | 105 | 4389 | 484 | - | 75 | 3448 | 0 | 243 |
| DRAM + CXL L2 adapter | 127 | 4543 | 505 | 20 | 107 | 3365 | 0 | 260 |
| DRAM + NVMe L2 adapter | 128 | 4546 | 514 | 174 | 110 | 3345 | 0 | 269 |

The same requests by the length of the prefix that came from the extension tier — L2 prefetch p50 / lookup interval p50 / TTFT p50 in ms (n):

| configuration | < 4K | 4K–8K | 8K–16K | ≥ 16K |
|---|---|---|---|---|
| DRAM + CXL hybrid L1 | - / 539 / 5024 (22) | - / 22 / 1601 (23) | - / 295 / 9861 (25) | - / 499 / 4644 (35) |
| DRAM + CXL L2 adapter | 5 / 79 / 1799 (26) | 10 / 612 / 6444 (20) | 15 / 447 / 3882 (34) | 39 / 541 / 4617 (47) |
| DRAM + NVMe L2 adapter | 31 / 446 / 2091 (27) | 71 / 613 / 6446 (20) | 148 / 474 / 3883 (34) | 311 / 542 / 4612 (47) |

Paired comparison, the same request of the trace in two configurations (first minus second; negative = the first is faster):

| pair | requests | mean TTFT difference s | median difference s | share of requests faster in the first | requests that are extension-tier hits in both | their median TTFT difference ms | their median lookup-interval difference ms |
|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 − DRAM + NVMe L2 adapter | 2332 | +0.13 | +0.02 | 0.28 | 63 | 10 | -19 |
| DRAM + CXL L2 adapter − DRAM + NVMe L2 adapter | 2332 | -0.00 | +0.00 | 0.49 | 127 | -14 | -3 |
| DRAM + CXL hybrid L1 − DRAM + CXL L2 adapter | 2332 | +0.13 | +0.02 | 0.25 | 62 | 11 | 0 |
| DRAM + CXL hybrid L1 − DRAM only 80 GiB | 2332 | -8.19 | -1.93 | 0.78 | 0 | - | - |
| DRAM + NVMe L2 adapter − DRAM only 80 GiB | 2332 | -8.31 | -1.95 | 0.78 | 0 | - | - |
| DRAM only 80 GiB − recompute only (vLLM alone) | 2332 | -20.92 | -11.86 | 0.89 | 0 | - | - |

## conversation, trace 0–200 s at 0.04× (half that rate)

| configuration | requests ok / all | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 599 / 599 | 0.093 | 0.044 | 0.048 | 0.000 | 0.000 | 6.25 | 3.92 | 27.44 | 37.33 | 7.04 | 16.87 | 44.95 | 0.120 | 42 | 1254 | 0.51 | 15 |
| DRAM + CXL hybrid L1 | 599 / 599 | 0.182 | 0.044 | 0.094 | 0.044 | 0.000 | 5.63 | 3.20 | 26.32 | 35.83 | 6.36 | 14.49 | 43.26 | 0.120 | 42 | 1131 | 0.49 | 15 |
| DRAM + NVMe L2 adapter | 599 / 599 | 0.182 | 0.044 | 0.051 | 0.000 | 0.086 | 5.63 | 3.19 | 26.31 | 35.80 | 6.36 | 14.38 | 43.21 | 0.120 | 42 | 1131 | 0.49 | 15 |

| configuration | L1 max GiB (of) | L2 max GiB (of) | L1 evicted GiB DRAM / CXL | L2 evicted keys | L1 written GiB DRAM / CXL | L2 stored / loaded GiB | LMCache RSS max GiB (anon + shmem) | vLLM RSS max GiB | MemAvailable min GiB | page cache growth GiB | LMCache CPU s (cores) | NVMe device read / written GiB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 64.0 (80) | - (-) | 166.2 / 0.0 | 0 | 218.8 / 0.0 | 0.0 / 0.0 | 80.9 (80.5 + 0.0) | 3.5 | 650 | 0.10 | 37 (0.01) | 0.0 / 0.1 |
| DRAM + CXL hybrid L1 | 197.6 (592) | - (-) | 0.0 / 0.0 | 0 | 80.0 / 117.6 | 0.0 / 0.0 | 81.0 (0.6 + 80.0) | 3.5 | 644 | 0.10 | 39 (0.01) | 0.0 / 0.1 |
| DRAM + NVMe L2 adapter | 64.1 (80) | 197.6 (512) | 160.9 / 0.0 | 0 | 197.6 / 0.0 | 197.6 / 20.4 | 81.0 (80.5 + 0.0) | 3.5 | 650 | 0.13 | 43 (0.01) | 20.4 / 198.1 |

TTFT by the dominant source of the prompt (a request is in a class when at least half of its prompt tokens came from that source; p50 s, n):

| configuration | extension tier (CXL L1 or L2) | DRAM tier | GPU prefix | miss (< 10 % cached) | L2 prefetch inside the cache server, all requests that loaded from the L2: p50 / p95 / max ms (n) |
|---|---|---|---|---|---|
| DRAM only 80 GiB | - (0) | 1.33 (29) | 0.20 (54) | 5.36 (378) | – |
| DRAM + CXL hybrid L1 | 0.85 (24) | 0.72 (47) | 0.16 (54) | 4.79 (331) | – |
| DRAM + NVMe L2 adapter | 0.72 (42) | 1.05 (29) | 0.17 (54) | 4.77 (331) | 77.5 / 373.5 / 378.5 (64) |

Requests served mainly from the extension tier (at least half of the prompt from CXL L1 objects or from the L2): parts of the TTFT, p50 ms (n). The lookup interval ends at the poll of vLLM's scheduler that finds the prefetch complete, so it contains the wait for that poll; the L2 prefetch is the part inside the cache server.

| configuration | n | TTFT | lookup interval | of which L2 prefetch | GPU transfer | queued → scheduled | KV ready → scheduled | scheduled → first token |
|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | 24 | 848 | 330 | - | 60 | 512 | 0 | 155 |
| DRAM + NVMe L2 adapter | 42 | 716 | 307 | 105 | 79 | 426 | 0 | 203 |

The same requests by the length of the prefix that came from the extension tier — L2 prefetch p50 / lookup interval p50 / TTFT p50 in ms (n):

| configuration | < 4K | 4K–8K | 8K–16K | ≥ 16K |
|---|---|---|---|---|
| DRAM + CXL hybrid L1 | - / 14 / 295 (4) | - / 13 / 256 (7) | - / 10 / 347 (7) | - / 782 / 12088 (6) |
| DRAM + NVMe L2 adapter | 25 / 31 / 300 (6) | 65 / 281 / 715 (10) | 136 / 187 / 748 (14) | 305 / 380 / 755 (12) |

Paired comparison, the same request of the trace in two configurations (first minus second; negative = the first is faster):

| pair | requests | mean TTFT difference s | median difference s | share of requests faster in the first | requests that are extension-tier hits in both | their median TTFT difference ms | their median lookup-interval difference ms |
|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 − DRAM + NVMe L2 adapter | 599 | +0.00 | +0.00 | 0.38 | 7 | -20 | -28 |
| DRAM + CXL hybrid L1 − DRAM only 80 GiB | 599 | -0.68 | +0.00 | 0.49 | 0 | - | - |
| DRAM + NVMe L2 adapter − DRAM only 80 GiB | 599 | -0.68 | -0.00 | 0.61 | 0 | - | - |

## tool-agent, trace 0–200 s at 0.04× (half that rate)

| configuration | requests ok / all | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 1159 / 1159 | 0.383 | 0.297 | 0.086 | 0.000 | 0.000 | 6.04 | 2.08 | 25.04 | 37.44 | 5.81 | 7.41 | 41.20 | 0.233 | 44 | 1212 | 0.50 | 26 |
| DRAM + CXL hybrid L1 | 1159 / 1159 | 0.446 | 0.298 | 0.121 | 0.027 | 0.000 | 5.42 | 1.49 | 23.59 | 36.40 | 5.15 | 6.28 | 38.19 | 0.233 | 44 | 1088 | 0.48 | 26 |
| DRAM + NVMe L2 adapter | 1159 / 1159 | 0.446 | 0.298 | 0.091 | 0.000 | 0.057 | 5.42 | 1.50 | 23.56 | 36.33 | 5.15 | 6.29 | 38.09 | 0.233 | 44 | 1088 | 0.48 | 26 |

| configuration | L1 max GiB (of) | L2 max GiB (of) | L1 evicted GiB DRAM / CXL | L2 evicted keys | L1 written GiB DRAM / CXL | L2 stored / loaded GiB | LMCache RSS max GiB (anon + shmem) | vLLM RSS max GiB | MemAvailable min GiB | page cache growth GiB | LMCache CPU s (cores) | NVMe device read / written GiB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 64.0 (80) | - (-) | 153.4 / 0.0 | 0 | 210.0 / 0.0 | 0.0 / 0.0 | 80.9 (80.5 + 0.0) | 3.5 | 645 | 0.76 | 39 (0.01) | 0.0 / 0.1 |
| DRAM + CXL hybrid L1 | 188.7 (592) | - (-) | 0.0 / 0.0 | 0 | 80.0 / 108.7 | 0.0 / 0.0 | 81.0 (0.5 + 80.0) | 3.5 | 638 | 0.39 | 39 (0.01) | 0.0 / 0.1 |
| DRAM + NVMe L2 adapter | 64.0 (80) | 188.7 (512) | 147.2 / 0.0 | 0 | 188.8 / 0.0 | 188.7 / 19.3 | 81.0 (80.5 + 0.0) | 3.5 | 645 | 0.43 | 44 (0.01) | 19.3 / 189.2 |

TTFT by the dominant source of the prompt (a request is in a class when at least half of its prompt tokens came from that source; p50 s, n):

| configuration | extension tier (CXL L1 or L2) | DRAM tier | GPU prefix | miss (< 10 % cached) | L2 prefetch inside the cache server, all requests that loaded from the L2: p50 / p95 / max ms (n) |
|---|---|---|---|---|---|
| DRAM only 80 GiB | - (0) | 9.05 (139) | 0.31 (549) | 5.44 (340) | – |
| DRAM + CXL hybrid L1 | 0.88 (22) | 5.36 (160) | 0.26 (550) | 4.63 (293) | – |
| DRAM + NVMe L2 adapter | 0.71 (38) | 6.75 (143) | 0.26 (550) | 4.68 (293) | 80.1 / 328.3 / 376.0 (64) |

Requests served mainly from the extension tier (at least half of the prompt from CXL L1 objects or from the L2): parts of the TTFT, p50 ms (n). The lookup interval ends at the poll of vLLM's scheduler that finds the prefetch complete, so it contains the wait for that poll; the L2 prefetch is the part inside the cache server.

| configuration | n | TTFT | lookup interval | of which L2 prefetch | GPU transfer | queued → scheduled | KV ready → scheduled | scheduled → first token |
|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | 22 | 879 | 17 | - | 69 | 539 | 0 | 137 |
| DRAM + NVMe L2 adapter | 38 | 705 | 307 | 160 | 79 | 438 | 0 | 212 |

The same requests by the length of the prefix that came from the extension tier — L2 prefetch p50 / lookup interval p50 / TTFT p50 in ms (n):

| configuration | < 4K | 4K–8K | 8K–16K | ≥ 16K |
|---|---|---|---|---|
| DRAM + CXL hybrid L1 | - / 436 / 2133 (4) | - / 12 / 260 (6) | - / 16 / 676 (7) | - / 394 / 15786 (5) |
| DRAM + NVMe L2 adapter | 26 / 43 / 361 (7) | 70 / 336 / 1695 (7) | 160 / 206 / 3069 (11) | 266 / 330 / 705 (13) |

Paired comparison, the same request of the trace in two configurations (first minus second; negative = the first is faster):

| pair | requests | mean TTFT difference s | median difference s | share of requests faster in the first | requests that are extension-tier hits in both | their median TTFT difference ms | their median lookup-interval difference ms |
|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 − DRAM + NVMe L2 adapter | 1159 | +0.00 | +0.00 | 0.38 | 4 | 22 | 1 |
| DRAM + CXL hybrid L1 − DRAM only 80 GiB | 1159 | -0.66 | -0.00 | 0.55 | 0 | - | - |
| DRAM + NVMe L2 adapter − DRAM only 80 GiB | 1159 | -0.66 | -0.00 | 0.56 | 0 | - | - |

## conversation, LONG window: trace 0–900 s at 0.08× (high load; 735 GiB of distinct KV stored, the extension tiers fill and evict)

| configuration | requests ok / all | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 2728 / 2728 | 0.097 | 0.047 | 0.051 | 0.000 | 0.000 | 27.57 | 14.46 | 63.07 | 85.06 | 21.42 | 32.76 | 91.57 | 0.241 | 83 | 2438 | 0.88 | 39 |
| DRAM + CXL hybrid L1 | 2728 / 2728 | 0.309 | 0.047 | 0.073 | 0.190 | 0.000 | 21.09 | 6.15 | 33.38 | 49.40 | 9.72 | 20.77 | 58.76 | 0.242 | 83 | 1868 | 0.78 | 25 |
| DRAM + CXL L2 adapter | 2728 / 2728 | 0.302 | 0.047 | 0.044 | 0.000 | 0.211 | 21.31 | 6.32 | 33.27 | 49.38 | 9.88 | 20.86 | 59.72 | 0.242 | 83 | 1888 | 0.78 | 25 |
| DRAM + NVMe L2 adapter | 2728 / 2728 | 0.302 | 0.047 | 0.045 | 0.000 | 0.211 | 21.31 | 6.24 | 33.29 | 49.42 | 9.85 | 20.93 | 59.19 | 0.242 | 83 | 1887 | 0.78 | 25 |

| configuration | L1 max GiB (of) | L2 max GiB (of) | L1 evicted GiB DRAM / CXL | L2 evicted keys | L1 written GiB DRAM / CXL | L2 stored / loaded GiB | LMCache RSS max GiB (anon + shmem) | vLLM RSS max GiB | MemAvailable min GiB | page cache growth GiB | LMCache CPU s (cores) | NVMe device read / written GiB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 64.1 (80) | - (-) | 907.6 / 0.0 | 0 | 964.8 / 0.0 | 0.0 / 0.0 | 81.0 (80.5 + 0.0) | 3.5 | 644 | 0.30 | 115 (0.01) | 0.0 / 0.4 |
| DRAM + CXL hybrid L1 | 473.6 (592) | - (-) | 68.7 / 215.4 | 0 | 148.7 / 593.6 | 0.0 / 0.0 | 81.1 (0.6 + 80.0) | 3.5 | 638 | 0.29 | 149 (0.01) | 0.0 / 0.4 |
| DRAM + CXL L2 adapter | 64.1 (80) | 409.5 (512) | 913.2 / 0.0 | 46608 | 750.2 / 0.0 | 750.2 / 222.2 | 81.0 (80.6 + 0.0) | 3.5 | 644 | 0.33 | 401 (0.04) | 0.0 / 0.4 |
| DRAM + NVMe L2 adapter | 64.8 (80) | 409.6 (512) | 912.6 / 0.0 | 46612 | 750.1 / 0.0 | 749.8 / 221.9 | 81.0 (80.6 + 0.0) | 3.5 | 644 | 0.39 | 142 (0.01) | 221.9 / 751.9 |

TTFT by the dominant source of the prompt (a request is in a class when at least half of its prompt tokens came from that source; p50 s, n):

| configuration | extension tier (CXL L1 or L2) | DRAM tier | GPU prefix | miss (< 10 % cached) | L2 prefetch inside the cache server, all requests that loaded from the L2: p50 / p95 / max ms (n) |
|---|---|---|---|---|---|
| DRAM only 80 GiB | - (0) | 12.49 (117) | 13.19 (292) | 15.42 (1625) | – |
| DRAM + CXL hybrid L1 | 4.46 (408) | 6.80 (136) | 4.59 (292) | 8.52 (1140) | – |
| DRAM + CXL L2 adapter | 4.86 (423) | 5.98 (111) | 4.75 (292) | 8.60 (1161) | 12.5 / 93.9 / 9222.8 (620) |
| DRAM + NVMe L2 adapter | 4.81 (423) | 6.66 (115) | 4.68 (292) | 8.56 (1161) | 104.0 / 405.9 / 1044.3 (620) |

Requests served mainly from the extension tier (at least half of the prompt from CXL L1 objects or from the L2): parts of the TTFT, p50 ms (n). The lookup interval ends at the poll of vLLM's scheduler that finds the prefetch complete, so it contains the wait for that poll; the L2 prefetch is the part inside the cache server.

| configuration | n | TTFT | lookup interval | of which L2 prefetch | GPU transfer | queued → scheduled | KV ready → scheduled | scheduled → first token |
|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | 408 | 4461 | 449 | - | 95 | 3524 | 0 | 255 |
| DRAM + CXL L2 adapter | 423 | 4855 | 474 | 17 | 106 | 3824 | 0 | 258 |
| DRAM + NVMe L2 adapter | 423 | 4808 | 486 | 160 | 105 | 3639 | 0 | 261 |

The same requests by the length of the prefix that came from the extension tier — L2 prefetch p50 / lookup interval p50 / TTFT p50 in ms (n):

| configuration | < 4K | 4K–8K | 8K–16K | ≥ 16K |
|---|---|---|---|---|
| DRAM + CXL hybrid L1 | - / 413 / 5112 (78) | - / 495 / 2908 (103) | - / 416 / 4942 (97) | - / 414 / 4720 (130) |
| DRAM + CXL L2 adapter | 5 / 390 / 2323 (71) | 9 / 604 / 6115 (86) | 15 / 447 / 4427 (110) | 47 / 479 / 5223 (156) |
| DRAM + NVMe L2 adapter | 31 / 417 / 2323 (69) | 76 / 610 / 5949 (88) | 137 / 456 / 4347 (110) | 315 / 486 / 5246 (156) |

Paired comparison, the same request of the trace in two configurations (first minus second; negative = the first is faster):

| pair | requests | mean TTFT difference s | median difference s | share of requests faster in the first | requests that are extension-tier hits in both | their median TTFT difference ms | their median lookup-interval difference ms |
|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 − DRAM + NVMe L2 adapter | 2728 | -0.12 | +0.01 | 0.38 | 295 | -26 | -2 |
| DRAM + CXL L2 adapter − DRAM + NVMe L2 adapter | 2728 | +0.03 | -0.00 | 0.64 | 422 | -27 | -3 |
| DRAM + CXL hybrid L1 − DRAM + CXL L2 adapter | 2728 | -0.15 | +0.01 | 0.31 | 295 | 3 | -0 |
| DRAM + CXL hybrid L1 − DRAM only 80 GiB | 2728 | -11.70 | -4.87 | 0.86 | 0 | - | - |
| DRAM + NVMe L2 adapter − DRAM only 80 GiB | 2728 | -11.57 | -4.78 | 0.87 | 0 | - | - |

## conversation, trace 0–400 s at 0.16× (sustained overload: the arrivals take 2,500 s; read-lock TTL 7,200 s, kv_load_failure_policy=recompute)

| configuration | requests ok / all | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 1177 / 1177 | 0.130 | 0.045 | 0.086 | 0.000 | 0.000 | 11.70 | 856.58 | 1546.47 | 1565.46 | 835.57 | 871.26 | 1562.97 | 0.287 | 98 | 2857 | 1.00 | 460 |
| DRAM + CXL hybrid L1 | 1177 / 1177 | 0.208 | 0.045 | 0.078 | 0.085 | 0.000 | 10.66 | 792.93 | 1328.17 | 1343.59 | 755.46 | 807.97 | 1344.55 | 0.305 | 104 | 2765 | 1.00 | 437 |
| DRAM + NVMe L2 adapter | 1177 / 1177 | 0.209 | 0.045 | 0.094 | 0.000 | 0.070 | 10.65 | 790.72 | 1321.17 | 1336.66 | 753.02 | 805.80 | 1337.57 | 0.306 | 104 | 2767 | 1.00 | 437 |

| configuration | L1 max GiB (of) | L2 max GiB (of) | L1 evicted GiB DRAM / CXL | L2 evicted keys | L1 written GiB DRAM / CXL | L2 stored / loaded GiB | LMCache RSS max GiB (anon + shmem) | vLLM RSS max GiB | MemAvailable min GiB | page cache growth GiB | LMCache CPU s (cores) | NVMe device read / written GiB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only 80 GiB | 64.1 (80) | - (-) | 345.2 / 0.0 | 0 | 400.1 / 0.0 | 0.0 / 0.0 | 81.1 (80.7 + 0.0) | 4.0 | 644 | 0.11 | 44 (0.01) | 0.0 / 0.1 |
| DRAM + CXL hybrid L1 | 359.3 (592) | - (-) | 0.0 / 0.0 | 0 | 80.0 / 279.3 | 0.0 / 0.0 | 81.2 (0.7 + 80.0) | 4.0 | 638 | 0.11 | 48 (0.01) | 0.0 / 0.1 |
| DRAM + NVMe L2 adapter | 64.6 (80) | 359.3 (512) | 341.6 / 0.0 | 0 | 366.6 / 0.0 | 359.3 / 34.0 | 81.1 (80.7 + 0.0) | 4.0 | 644 | 0.37 | 54 (0.01) | 34.0 / 360.1 |

TTFT by the dominant source of the prompt (a request is in a class when at least half of its prompt tokens came from that source; p50 s, n):

| configuration | extension tier (CXL L1 or L2) | DRAM tier | GPU prefix | miss (< 10 % cached) | L2 prefetch inside the cache server, all requests that loaded from the L2: p50 / p95 / max ms (n) |
|---|---|---|---|---|---|
| DRAM only 80 GiB | - (0) | 812.28 (84) | 863.35 (116) | 813.01 (674) | – |
| DRAM + CXL hybrid L1 | 1055.34 (72) | 555.18 (67) | 799.85 (116) | 730.76 (607) | – |
| DRAM + NVMe L2 adapter | 1072.56 (53) | 788.48 (94) | 797.68 (116) | 719.81 (606) | 301.4 / 712.3 / 917.8 (81) |

Requests served mainly from the extension tier (at least half of the prompt from CXL L1 objects or from the L2): parts of the TTFT, p50 ms (n). The lookup interval ends at the poll of vLLM's scheduler that finds the prefetch complete, so it contains the wait for that poll; the L2 prefetch is the part inside the cache server.

| configuration | n | TTFT | lookup interval | of which L2 prefetch | GPU transfer | queued → scheduled | KV ready → scheduled | scheduled → first token |
|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | 72 | 1055339 | 65201 | - | 311 | 1054118 | 0 | 313 |
| DRAM + NVMe L2 adapter | 53 | 1072563 | 65080 | 387 | 182 | 1072236 | 0 | 304 |

The same requests by the length of the prefix that came from the extension tier — L2 prefetch p50 / lookup interval p50 / TTFT p50 in ms (n):

| configuration | < 4K | 4K–8K | 8K–16K | ≥ 16K |
|---|---|---|---|---|
| DRAM + CXL hybrid L1 | - / 40615 / 934444 (9) | - / 40624 / 921010 (19) | - / 40600 / 921310 (18) | - / 65206 / 1140613 (26) |
| DRAM + NVMe L2 adapter | 90 / 65147 / 1112913 (5) | 276 / 65080 / 1072563 (10) | 312 / 65102 / 1143241 (16) | 447 / 40426 / 988048 (22) |

Paired comparison, the same request of the trace in two configurations (first minus second; negative = the first is faster):

| pair | requests | mean TTFT difference s | median difference s | share of requests faster in the first | requests that are extension-tier hits in both | their median TTFT difference ms | their median lookup-interval difference ms |
|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 − DRAM + NVMe L2 adapter | 1177 | +2.43 | +2.13 | 0.19 | 21 | 4569 | 112 |
| DRAM + CXL hybrid L1 − DRAM only 80 GiB | 1177 | -80.11 | -62.55 | 0.76 | 0 | - | - |
| DRAM + NVMe L2 adapter − DRAM only 80 GiB | 1177 | -82.55 | -64.68 | 0.76 | 0 | - | - |

