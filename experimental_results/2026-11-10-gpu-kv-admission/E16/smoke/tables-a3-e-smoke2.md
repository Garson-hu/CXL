### Table A3-1 — one probe under K = 6 decoding holders: external hit vs miss of the same length at three levels of free blocks

| probe (L + tail), target free / need, type | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| 4096 tok, 1.5×, host | 1 | 272 / 256 | 8647 (8647–8647) | 0 | ok:1 | 0.00 | – | 0.47 (0.47–0.47) |
| 4096 tok, 0.6×, cold | 1 | 272 / 128 | 8647 (8647–8647) | 0 | ok:1 | 0.00 | -2.91 | 1.26 (1.26–1.26) |

### Table A3-3 — two probes 5 ms apart, 700 free blocks targeted (not enough for both); a holder is released 3 s later

| order, position: probe | n | blocks needed: full sequence / this allocation | free blocks at the first attempt p50 (min–max) | reservation | first attempt: gate | lookup result → admitted p50 (s) | admitted after the release p50 (s) | TTFT p50 (min–max) (s) |
|---|---|---|---|---|---|---|---|---|
| H4M8, #1: host 4096 | 1 | 272 / 256 | 8647 (8647–8647) | 0 | ok:1 | 0.00 | -2.90 | 2.53 (2.53–2.53) |
| H4M8, #2: cold 8192 | 1 | 528 / 128 | 8391 (8391–8391) | 0 | ok:1 | 0.00 | -2.90 | 2.31 (2.31–2.31) |

### Table A3-6 — phases of the probes (seconds, median): lookup result → admitted, load, promotion, compute

| group | type | n | queued → first visit | lookup | admit | load | promote | compute | TTFT |
|---|---|---|---|---|---|---|---|---|---|
| part 1 | host | 1 | 0.001 | 0.069 | 0.000 | 0.174 | 0.001 | 0.212 | 0.475 |
| part 1 | cold | 1 | 0.000 | 0.069 | 0.000 | – | – | 1.171 | 1.263 |
| part 3 | host | 1 | 0.000 | 0.069 | 0.000 | 1.990 | 0.001 | 0.433 | 2.530 |
| part 3 | cold | 1 | 0.000 | 0.069 | 0.000 | – | – | 2.208 | 2.313 |
