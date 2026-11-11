
### Table A3-3 — two probes 5 ms apart, 700 free blocks targeted (not enough for both); a holder is released 3 s later

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| C4M8, #1: cold 4096 | 2 | 272 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.93 | 1.04 (1.03–1.04) |
| C4M8, #2: cold 8192 | 2 | 528 / 111 | 445 (445–445) | 0 | full:2 | 0.97 | -1.55 | 3.30 (3.30–3.30) |
| H4M8, #1: host 4096 | 2 | 272 / 256 | 717 (716–717) | 0 | ok:2 | 0.00 | -2.94 | 0.36 (0.36–0.36) |
| H4M8, #2: cold 8192 | 2 | 528 / 128 | 461 (460–461) | 0 | full:2 | 0.72 | -2.22 | 2.63 (2.63–2.63) |
| M8C4, #1: cold 8192 | 2 | 528 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.93 | 1.93 (1.93–1.93) |
| M8C4, #2: cold 4096 | 2 | 272 / 111 | 189 (189–189) | 0 | full:2 | 1.03 | -0.65 | 3.31 (3.31–3.31) |
| M8H4, #1: cold 8192 | 2 | 528 / 128 | 717 (717–717) | 0 | ok:2 | 0.00 | -2.93 | 1.93 (1.93–1.93) |
| M8H4, #2: host 4096 | 2 | 272 / 256 | 189 (189–189) | 0 | full:2 | 1.03 | -0.65 | 2.65 (2.64–2.65) |

### Table A3-5 — two probes 5 ms apart, no memory pressure (more than 5,000 free blocks)

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| H4M8, #1: host 4096 | 2 | 272 / 256 | 5505 (5505–5505) | 0 | ok:2 | 0.00 | – | 1.67 (1.67–1.67) |
| H4M8, #2: cold 8192 | 2 | 528 / 128 | 5249 (5249–5249) | 0 | ok:2 | 0.00 | – | 1.67 (1.67–1.67) |
| M8H4, #1: cold 8192 | 2 | 528 / 128 | 5505 (5505–5505) | 0 | ok:2 | 0.00 | – | 1.61 (1.61–1.61) |
| M8H4, #2: host 4096 | 2 | 272 / 256 | 4977 (4977–4977) | 0 | ok:2 | 0.00 | – | 1.75 (1.75–1.75) |

### Table A3-6 — phases of the probes (seconds, median): lookup result → admitted, load, promotion, compute

| group | type | n | queued → first visit | lookup | admit | load | promote | compute | TTFT |
|---|---|---|---|---|---|---|---|---|---|
| part 3 | host | 4 | 0.000 | 1.296 | 1.025 | 0.148 | 0.001 | 0.149 | 2.643 |
| part 3 | cold | 12 | 0.000 | 0.048 | 0.718 | – | – | 1.847 | 2.628 |
| part 5 | host | 4 | 0.000 | 1.091 | 0.000 | 1.080 | 0.001 | 0.543 | 1.752 |
| part 5 | cold | 4 | 0.000 | 0.027 | 0.000 | – | – | 1.611 | 1.665 |
