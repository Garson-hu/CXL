**Budget selection on the FIRST half (requests 25–50%)** — rule: the (B, depth) pair with the highest usable hit share of the independent combination among the pairs whose estimated neighbour p99 is ≤ 6% for the independent, the cost-only and the joint policy; the same pair is used by all three on the test half.

| trace | model | speed | neighbour | chosen B (GB/s) / depth | indep hit (sel) | indep p99 | cost_budget hit / p99 | joint hit / p99 | feasible pairs |
|---|---|---|---|---|---|---|---|---|---|
| conversation | 70b | 1× | adam | 8 / 1 | 0.253 | 0.3% | 0.140 / 1.6% | 0.243 / 0.3% | 20 of 20 |
| conversation | 70b | 1× | reader | 8 / 1 | 0.253 | 0.2% | 0.140 / 1.0% | 0.243 / 0.2% | 20 of 20 |
| conversation | 70b | 4× | adam | 4 / 1 | 0.251 | 0.8% | 0.114 / 2.3% | 0.237 / 0.8% | 15 of 20 |
| conversation | 70b | 4× | reader | 32 / 1 | 0.253 | 0.7% | 0.138 / 2.6% | 0.243 / 0.7% | 20 of 20 |
| conversation | 70b | 8× | adam | 12 / 1 | 0.248 | 1.8% | 0.111 / 5.0% | 0.245 / 1.5% | 13 of 20 |
| conversation | 70b | 8× | reader | 32 / 1 | 0.250 | 1.2% | 0.112 / 2.7% | 0.255 / 1.1% | 19 of 20 |
| conversation | 8b | 1× | adam | 2 / 4 | 0.386 | 0.1% | 0.249 / 0.9% | 0.373 / 0.1% | 20 of 20 |
| conversation | 8b | 1× | reader | 2 / 4 | 0.386 | 0.1% | 0.249 / 0.6% | 0.373 / 0.1% | 20 of 20 |
| conversation | 8b | 4× | adam | 4 / 1 | 0.385 | 0.5% | 0.218 / 1.8% | 0.384 / 0.4% | 20 of 20 |
| conversation | 8b | 4× | reader | 4 / 1 | 0.385 | 0.3% | 0.218 / 1.1% | 0.384 / 0.3% | 20 of 20 |
| conversation | 8b | 8× | adam | 8 / 1 | 0.381 | 0.8% | 0.213 / 2.8% | 0.373 / 0.7% | 16 of 20 |
| conversation | 8b | 8× | reader | 8 / 1 | 0.381 | 0.5% | 0.213 / 1.7% | 0.373 / 0.5% | 20 of 20 |
| toolagent | 70b | 1× | adam | 8 / 1 | 0.677 | 0.2% | 0.619 / 1.5% | 0.670 / 0.3% | 20 of 20 |
| toolagent | 70b | 1× | reader | 8 / 1 | 0.677 | 0.2% | 0.619 / 0.9% | 0.670 / 0.2% | 20 of 20 |
| toolagent | 70b | 4× | adam | 8 / 1 | 0.676 | 1.0% | 0.615 / 3.4% | 0.675 / 1.0% | 15 of 20 |
| toolagent | 70b | 4× | reader | 8 / 1 | 0.676 | 0.6% | 0.615 / 2.2% | 0.675 / 0.6% | 20 of 20 |
| toolagent | 70b | 8× | adam | 16 / 1 | 0.676 | 1.9% | 0.612 / 5.8% | 0.665 / 1.5% | 14 of 20 |
| toolagent | 70b | 8× | reader | 32 / 1 | 0.678 | 1.2% | 0.613 / 2.5% | 0.677 / 1.1% | 19 of 20 |
| toolagent | 8b | 1× | adam | 2 / 1 | 0.737 | 0.1% | 0.665 / 0.5% | 0.735 / 0.1% | 20 of 20 |
| toolagent | 8b | 1× | reader | 2 / 1 | 0.737 | 0.1% | 0.665 / 0.3% | 0.735 / 0.1% | 20 of 20 |
| toolagent | 8b | 4× | adam | 12 / 1 | 0.735 | 0.5% | 0.652 / 2.4% | 0.737 / 0.4% | 20 of 20 |
| toolagent | 8b | 4× | reader | 12 / 1 | 0.735 | 0.3% | 0.652 / 1.5% | 0.737 / 0.3% | 20 of 20 |
| toolagent | 8b | 8× | adam | 32 / 1 | 0.731 | 1.0% | 0.653 / 4.1% | 0.729 / 0.9% | 16 of 20 |
| toolagent | 8b | 8× | reader | 32 / 4 | 0.732 | 0.8% | 0.652 / 2.0% | 0.711 / 0.8% | 20 of 20 |
