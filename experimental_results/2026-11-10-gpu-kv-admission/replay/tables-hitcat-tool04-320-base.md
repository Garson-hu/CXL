| run | category | n | prompt tok p50 | uncached tok p50 | TTFT p50 (s) | queue→sched p50 (s) | lookup p50 (s) | lookup end→load start p50 (s) | KV load wait p50 (s) | transfer p50 (s) | prefill p50 (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tool04-320-base | host≥50% | 148 | 6521 | 597 | 3.3 | 2.8 | 0.51 | 0.3 | 0.21 | 0.05 | 0.21 |
| tool04-320-base | GPU≥50% | 576 | 6187 | 542 | 0.3 | 0.0 | 0.01 | 0.0 | 0.08 | 0.02 | 0.17 |
| tool04-320-base | 10–50% | 121 | 2428 | 1916 | 0.8 | 0.1 | 0.01 | 0.0 | 0.11 | 0.04 | 0.45 |
| tool04-320-base | miss<10% | 301 | 13712 | 13200 | 5.1 | 0.0 | 0.01 | 0.0 | 0.05 | 0.03 | 2.98 |

| run | backlog at arrival | host≥50 % TTFT p50 (s) [n] | GPU≥50 % TTFT p50 (s) [n] | miss TTFT p50 (s) [n] |
|---|---|---|---|---|
| tool04-320-base | 0–20 | 3.3 [146] | 0.3 [569] | 5.1 [301] |
| tool04-320-base | 20–35 | 43.2 [2] | 20.3 [7] | – [0] |
| tool04-320-base | 35–max | – [0] | – [0] | – [0] |

| run | host hits with lookup→load gap > 2 s | gap p50 / p90 (s) | requests first scheduled inside such a gap (GPU / miss / partial / host) | of those, arrived after the host hit |
|---|---|---|---|---|
| tool04-320-base | 42 of 148 | 12.7 / 20.6 | 39 / 55 / 20 / 29 | 12 (5 GPU, 2 miss, 5 partial) |
