| configuration | hit: load admitted at (s) | hit: TTFT (s) | misses admitted before the hit (of 30) | first miss admitted at (s) | misses: TTFT p50 / p95 / max (s) | all 31 probes: mean request time (s) | refused attempts of the hit | preemptions | blocks kept free for the hit while it waits |
|---|---|---|---|---|---|---|---|---|---|
| stock | 2.57 | 4.50 | 0 | 2.59 | 8.39 / 12.84 / 12.91 | 10.94 | 89 | 0 | – |
| skip=3 | 3.95 | 5.93 | 7 | 0.11 | 6.21 / 10.60 / 10.67 | 8.19 | 14 | 0 | – |
| skip=3, hitres=300 | 2.97 | 3.33 | 4 | 1.07 | 7.20 / 11.23 / 11.46 | 9.34 | 0 | 0 | 289 |
| skip=3, hitres=600 | 2.91 | 4.86 | 4 | 1.07 | 7.48 / 11.72 / 12.08 | 9.77 | 0 | 0 | 577 |
| skip=3, hitres=1200 | 2.57 | 4.55 | 0 | 2.57 | 8.29 / 12.57 / 12.68 | 10.66 | 0 | 0 | 980 |
| skip=8 | 4.59 | 5.53 | 9 | 0.11 | 6.14 / 10.90 / 11.27 | 9.16 | 0 | 0 | – |
| P2 (token reserve + skip=3, hitres=600) | 2.91 | 4.86 | 4 | 1.07 | 7.64 / 11.74 / 12.11 | 9.87 | 0 | 0 | 577 |
