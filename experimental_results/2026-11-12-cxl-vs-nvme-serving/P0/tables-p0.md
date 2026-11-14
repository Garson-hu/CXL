# P0 — validation of the real data paths (c28, 2026-11-12)

| run | tier | KV stored GiB | L1 objects written DRAM / DAX (chunks) | L1 reads DRAM / DAX | L2 stored / loaded GiB | DAX arenas (GiB, CUDA-registered) | residency check | LMCache RSS max GiB: anon / shmem | page cache growth GiB | NVMe device read / written GiB | GPU memory max MiB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| p0-dram-s | dram | 2.99 | 340 / 0 | 1172 / 0 | 0.00 / 0.00 | - | - | 8.49 / 0.01 | 0.00 | 0.00 / 0.00 | 4760 |
| p0-dax-v | dax | 2.99 | 0 / 340 | 0 / 1172 | 0.00 / 0.00 | dax1.0 8 yes | 85 of 85 hashes equal through an independent read-only mapping | 0.50 / 0.01 | 0.00 | 0.00 / 0.00 | 4760 |
| p0-hyb2-v | hyb | 7.42 | 227 / 617 | 880 / 2308 | 0.00 / 0.00 | dax1.0 4 yes; dax0.0 4 yes | 155 of 155 hashes equal through an independent read-only mapping | 0.50 / 2.01 | 0.01 | 0.00 / 0.00 | 4764 |
| p0-hyb-full2 | hyb | 5.20 | 455 / 137 | 1792 / 388 | 0.00 / 0.00 | dax1.0 269.5 yes; dax0.0 242.5 yes | 35 of 35 hashes equal through an independent read-only mapping | 0.50 / 4.01 | 0.00 | 0.00 / 0.00 | 7652 |
| p0-hyb-full80 | hyb | 5.20 | 592 / 0 | 2180 / 0 | 0.00 / 0.00 | dax1.0 269.5 yes; dax0.0 242.5 yes | no Device-DAX object in this run | 0.49 / 80.01 | 0.02 | 0.02 / 0.00 | 7804 |
| p0-daxl2-v | daxl2 | 2.99 | 340 / 0 | 340 / 0 | 2.99 / 10.30 | - | 340 of 340 hashes equal through an independent read-only mapping | 8.50 / 0.01 | 0.33 | 0.00 / 0.00 | 4760 |
| p0-daxl2-full2 | daxl2 | 5.20 | 592 / 0 | 592 / 0 | 5.20 / 19.16 | - | 592 of 592 hashes equal through an independent read-only mapping | 80.50 / 0.01 | 0.00 | 0.00 / 0.00 | 6776 |
| p0-ssd-v | ssd | 2.99 | 340 / 0 | 340 / 0 | 2.99 / 10.30 | - | files: 0 of 783360 pages (0.00 %) in the page cache | 8.49 / 0.01 | 0.00 | 10.30 / 2.99 | 4760 |
| p0-ssdn-v | ssdn | 2.99 | 340 / 0 | 340 / 0 | 2.99 / 10.30 | - | files: 0 of 783360 pages (0.00 %) in the page cache | 8.49 / 0.01 | 0.00 | 10.30 / 2.99 | 4760 |
| p0-ssdn-buf | ssdn (buffered I/O: control) | 2.99 | 340 / 0 | 340 / 0 | 2.99 / 10.30 | - | files: 783360 of 783360 pages (100.00 %) in the page cache | 8.49 / 0.01 | 3.32 | 0.00 / 0.00 | 4760 |
