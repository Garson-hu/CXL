
### Table A3-3 — two probes 5 ms apart, 700 free blocks targeted (not enough for both); a holder is released 3 s later

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| C4M8, #1: cold 4096 | 2 | 272 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.94 | 1.02 (1.02–1.02) |
| C4M8, #2: cold 8192 | 2 | 528 / 111 | 445 (445–445) | 0 | full:2 | 0.97 | -1.56 | 3.29 (3.29–3.29) |
| H4M8, #1: host 4096 | 2 | 272 / 256 | 717 (716–717) | 0 | ok:2 | 0.00 | -2.93 | 0.37 (0.34–0.37) |
| H4M8, #2: cold 8192 | 2 | 528 / 128 | 461 (460–461) | 0 | full:2 | 0.72 | -2.22 | 2.64 (2.61–2.64) |
| M8C4, #1: cold 8192 | 2 | 528 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.94 | 1.93 (1.92–1.93) |
| M8C4, #2: cold 4096 | 2 | 272 / 110 | 189 (189–189) | 0 | full:2 | 1.03 | -0.66 | 3.30 (3.30–3.30) |
| M8H4, #1: cold 8192 | 2 | 528 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.94 | 1.92 (1.92–1.92) |
| M8H4, #2: host 4096 | 2 | 272 / 256 | 461 (461–461) | 272 | resv:2 | 2.26 | -0.65 | 2.64 (2.64–2.64) |

### Table A3-5 — two probes 5 ms apart, no memory pressure (more than 5,000 free blocks)

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| H4M8, #1: host 4096 | 2 | 272 / 256 | 5505 (5505–5505) | 0 | ok:2 | 0.00 | – | 1.67 (1.53–1.67) |
| H4M8, #2: cold 8192 | 2 | 528 / 128 | 5249 (5249–5249) | 0 | ok:2 | 0.00 | – | 1.66 (1.66–1.66) |
| M8H4, #1: cold 8192 | 2 | 528 / 128 | 5505 (5505–5505) | 0 | ok:2 | 0.00 | – | 1.62 (1.61–1.62) |
| M8H4, #2: host 4096 | 2 | 272 / 256 | 5249 (5249–5249) | 272 | ok:2 | 0.00 | – | 1.70 (1.69–1.70) |

### Table A3-6 — phases of the probes (seconds, median): lookup result → admitted, load, promotion, compute

| group | type | n | queued → first visit | lookup | admit | load | promote | compute | TTFT |
|---|---|---|---|---|---|---|---|---|---|
| part 3 | host | 4 | 0.000 | 0.073 | 2.260 | 0.148 | 0.001 | 0.150 | 2.641 |
| part 3 | cold | 12 | 0.000 | 0.048 | 0.695 | – | – | 1.850 | 2.614 |
| part 5 | host | 4 | 0.000 | 0.049 | 0.000 | 1.546 | 0.001 | 0.544 | 1.692 |
| part 5 | cold | 4 | 0.000 | 0.027 | 0.000 | – | – | 1.611 | 1.662 |
