
### Table A3-3 — two probes 5 ms apart, 700 free blocks targeted (not enough for both); a holder is released 3 s later

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| C4M8, #1: cold 4096 | 2 | 272 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.93 | 1.04 (1.02–1.04) |
| C4M8, #2: cold 8192 | 2 | 528 / 128 | 711 (711–711) | 0 | ok:2 | 0.00 | -1.55 | 3.31 (3.29–3.31) |
| H4M8, #1: host 4096 | 2 | 272 / 256 | 717 (716–717) | 0 | ok:2 | 0.00 | -2.94 | 0.36 (0.36–0.36) |
| H4M8, #2: cold 8192 | 2 | 528 / 128 | 708 (707–708) | 0 | ok:2 | 0.00 | -2.22 | 2.64 (2.63–2.64) |
| M8C4, #1: cold 8192 | 2 | 528 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.93 | 1.94 (1.92–1.94) |
| M8C4, #2: cold 4096 | 2 | 272 / 128 | 711 (711–711) | 0 | ok:2 | 0.00 | -0.64 | 3.32 (3.30–3.32) |
| M8H4, #1: cold 8192 | 2 | 528 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.93 | 1.94 (1.94–1.94) |
| M8H4, #2: host 4096 | 2 | 272 / 256 | 711 (711–711) | 0 | ok:2 | 0.00 | -0.64 | 2.66 (2.65–2.66) |

### Table A3-5 — two probes 5 ms apart, no memory pressure (more than 5,000 free blocks)

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| H4M8, #1: host 4096 | 2 | 272 / 256 | 5505 (5505–5505) | 0 | ok:2 | 0.00 | – | 1.69 (1.53–1.69) |
| H4M8, #2: cold 8192 | 2 | 528 / 128 | 5249 (5249–5249) | 0 | ok:2 | 0.00 | – | 1.66 (1.61–1.66) |
| M8H4, #1: cold 8192 | 2 | 528 / 128 | 5505 (5505–5505) | 0 | ok:2 | 0.00 | – | 1.62 (1.62–1.62) |
| M8H4, #2: host 4096 | 2 | 272 / 256 | 5249 (5249–5249) | 272 | ok:2 | 0.00 | – | 1.70 (1.70–1.70) |

### Table A3-6 — phases of the probes (seconds, median): lookup result → admitted, load, promotion, compute

| group | type | n | queued → first visit | lookup | admit | load | promote | compute | TTFT |
|---|---|---|---|---|---|---|---|---|---|
| part 3 | host | 4 | 0.001 | 2.332 | 0.000 | 0.148 | 0.001 | 0.150 | 2.653 |
| part 3 | cold | 12 | 0.000 | 0.766 | 0.000 | – | – | 1.851 | 2.633 |
| part 5 | host | 4 | 0.001 | 0.049 | 0.000 | 1.544 | 0.001 | 0.160 | 1.697 |
| part 5 | cold | 4 | 0.001 | 0.027 | 0.000 | – | – | 1.569 | 1.622 |
