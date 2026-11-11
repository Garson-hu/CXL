| trial | probe | c2b-base | c2b-tokfast | c2b-tokfast-a0 | c2b-tokfast-a0-out512 | c2b-tokfast-out512 | c2b-tokfast-fb |
|---|---|---|---|---|---|---|---|
| c2-m100 | #1 miss 16384 | 4.04 (ok:3) | 4.34 (ok:3) | 4.73 (ok:3) | 4.74 (ok:3) | 4.34 (ok:3) | 4.34 (ok:3) |
| c2-m100 | #2 hit 4096 | 4.22 (full:3) | 4.52 (resv:3) | 2.16 (ok:3) | 2.17 (ok:3) | 7.83 (resv:3) | 4.52 (full:3) |
| c2-m100 | #3 hit 4096 | 2.35 (ok:3) | 2.68 (ok:3) | 3.50 (full:3) | 6.55 (full:3) | 5.98 (ok:3) | 2.68 (ok:3) |
| c2-m400 | #1 miss 16384 | 4.01 (ok:3) | 4.64 (ok:3) | 4.92 (ok:3) | 4.91 (ok:3) | 4.49 (ok:3) | 4.65 (ok:3) |
| c2-m400 | #2 hit 4096 | 3.80 (ok:3) | 2.11 (ok:3) | 2.13 (ok:3) | 2.11 (ok:3) | 1.98 (ok:3) | 2.12 (ok:3) |
| c2-m400 | #3 hit 4096 | 2.30 (full:3) | 2.69 (resv:3) | 1.99 (ok:3) | 1.97 (ok:3) | 2.16 (ok:3) | 2.70 (full:3) |

| total | c2b-base | c2b-tokfast | c2b-tokfast-a0 | c2b-tokfast-a0-out512 | c2b-tokfast-out512 | c2b-tokfast-fb |
|---|---|---|---|---|---|---|
| probes sent | 18 | 18 | 18 | 18 | 18 | 18 |
| probes failed or timed out | 0 | 0 | 0 | 0 | 0 | 0 |
| refused admission attempts of probes | 102 | 126 | 117 | 800 | 474 | 102 |
| preemptions (all requests) | 0 | 0 | 6 | 6 | 0 | 0 |
| running requests that could not get their next chunk | 0 | 0 | 12 | 12 | 0 | 0 |
