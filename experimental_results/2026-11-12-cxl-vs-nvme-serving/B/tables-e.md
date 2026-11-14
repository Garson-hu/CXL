# Experiment E — KV read / write traffic per medium during the replays of Experiment B

CXL traffic is the sum of the individually timed chunk copies into and out of the device mapping. For the `fs_native` NVMe L2 the bytes of each load / store task are spread evenly over the task's interval, so its "peak GiB in 1 s" is an estimate that can exceed the device's rate when several tasks end in the same second; its busy seconds and its rate while busy are not affected.

## conversation, trace 0–400 s at 0.08× (high load)

| configuration | medium | read GiB | write GiB | read busy s | write busy s | read GiB/s while busy | write GiB/s while busy | peak read GiB in 1 s | peak write GiB in 1 s | seconds with both | read-write overlap s | H2D GiB | D2H GiB | H2D-D2H overlap s | replay s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | CXL | 53.4 | 279.6 | 4.8 | 71.9 | 11.14 | 3.89 | 1.28 | 0.25 | 149 | 0.00 | 89.5 | 359.6 | 0.00 | 5007 |
| DRAM + CXL L2 adapter | CXL | 69.0 | 359.6 | 3.2 | 16.8 | 21.84 | 21.45 | 1.76 | 0.25 | 152 | 0.22 | 89.5 | 359.7 | 0.00 | 5007 |
| DRAM + NVMe L2 adapter | NVMe | 68.7 | 359.5 | 24.3 | 388.7 | 2.83 | 0.92 | 1.76 | 0.25 | 147 | 14.65 | 89.5 | 359.6 | 0.00 | 5007 |
| 20 GiB DRAM + CXL hybrid L1 | CXL | 79.7 | 339.6 | 6.7 | 87.3 | 11.84 | 3.89 | 1.32 | 0.25 | 205 | 0.00 | 89.5 | 359.6 | 0.00 | 5007 |
| 20 GiB DRAM + NVMe L2 adapter | NVMe | 87.7 | 359.5 | 31.2 | 396.6 | 2.81 | 0.91 | 2.00 | 0.25 | 192 | 19.04 | 89.5 | 359.6 | 0.00 | 5007 |

## tool-agent, trace 0–400 s at 0.08× (high load)

| configuration | medium | read GiB | write GiB | read busy s | write busy s | read GiB/s while busy | write GiB/s while busy | peak read GiB in 1 s | peak write GiB in 1 s | seconds with both | read-write overlap s | H2D GiB | D2H GiB | H2D-D2H overlap s | replay s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | CXL | 52.4 | 260.9 | 4.7 | 67.1 | 11.10 | 3.89 | 2.14 | 0.24 | 155 | 0.00 | 146.0 | 340.9 | 0.00 | 5002 |
| DRAM + CXL L2 adapter | CXL | 67.9 | 340.9 | 3.2 | 15.7 | 21.37 | 21.73 | 2.14 | 0.25 | 166 | 0.22 | 145.3 | 341.0 | 0.00 | 5002 |
| DRAM + NVMe L2 adapter | NVMe | 67.9 | 341.0 | 24.1 | 386.2 | 2.82 | 0.88 | 2.14 | 0.25 | 159 | 14.50 | 144.6 | 341.0 | 0.00 | 5002 |

## conversation, trace 0–200 s at 0.04× (half that rate)

| configuration | medium | read GiB | write GiB | read busy s | write busy s | read GiB/s while busy | write GiB/s while busy | peak read GiB in 1 s | peak write GiB in 1 s | seconds with both | read-write overlap s | H2D GiB | D2H GiB | H2D-D2H overlap s | replay s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | CXL | 10.3 | 117.6 | 0.9 | 30.2 | 11.39 | 3.89 | 1.16 | 0.23 | 31 | 0.00 | 32.5 | 197.6 | 0.00 | 4982 |
| DRAM + NVMe L2 adapter | NVMe | 20.4 | 197.6 | 7.1 | 208.8 | 2.88 | 0.95 | 1.08 | 0.23 | 48 | 2.58 | 32.5 | 197.6 | 0.00 | 4982 |

## tool-agent, trace 0–200 s at 0.04× (half that rate)

| configuration | medium | read GiB | write GiB | read busy s | write busy s | read GiB/s while busy | write GiB/s while busy | peak read GiB in 1 s | peak write GiB in 1 s | seconds with both | read-write overlap s | H2D GiB | D2H GiB | H2D-D2H overlap s | replay s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | CXL | 9.1 | 108.7 | 0.8 | 28.0 | 11.24 | 3.89 | 1.16 | 0.25 | 29 | 0.00 | 49.8 | 188.7 | 0.00 | 4984 |
| DRAM + NVMe L2 adapter | NVMe | 19.3 | 188.7 | 6.9 | 191.9 | 2.81 | 0.98 | 1.08 | 0.25 | 40 | 1.82 | 49.8 | 188.8 | 0.00 | 4984 |

## conversation, LONG window: trace 0–900 s at 0.08× (high load; 735 GiB of distinct KV stored, the extension tiers fill and evict)

| configuration | medium | read GiB | write GiB | read busy s | write busy s | read GiB/s while busy | write GiB/s while busy | peak read GiB in 1 s | peak write GiB in 1 s | seconds with both | read-write overlap s | H2D GiB | D2H GiB | H2D-D2H overlap s | replay s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | CXL | 199.1 | 593.6 | 18.4 | 152.7 | 10.83 | 3.89 | 1.71 | 0.25 | 471 | 0.00 | 275.6 | 742.4 | 0.00 | 11290 |
| DRAM + CXL L2 adapter | CXL | 222.2 | 749.7 | 10.0 | 34.5 | 22.27 | 21.75 | 2.91 | 1.12 | 481 | 0.55 | 267.9 | 750.2 | 0.00 | 11290 |
| DRAM + NVMe L2 adapter | NVMe | 221.9 | 749.8 | 78.3 | 799.6 | 2.83 | 0.94 | 2.91 | 0.25 | 464 | 44.27 | 268.0 | 750.1 | 0.00 | 11290 |

## conversation, trace 0–400 s at 0.16× (sustained overload: the arrivals take 2,500 s; read-lock TTL 7,200 s, kv_load_failure_policy=recompute)

| configuration | medium | read GiB | write GiB | read busy s | write busy s | read GiB/s while busy | write GiB/s while busy | peak read GiB in 1 s | peak write GiB in 1 s | seconds with both | read-write overlap s | H2D GiB | D2H GiB | H2D-D2H overlap s | replay s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM + CXL hybrid L1 | CXL | 39.4 | 279.3 | 3.7 | 71.8 | 10.67 | 3.89 | 2.14 | 0.22 | 118 | 0.00 | 75.3 | 359.3 | 0.00 | 3855 |
| DRAM + NVMe L2 adapter | NVMe | 34.0 | 359.3 | 12.6 | 374.1 | 2.69 | 0.96 | 3.72 | 0.22 | 15 | 7.43 | 75.7 | 366.6 | 0.00 | 3848 |

