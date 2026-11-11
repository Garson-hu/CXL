| check | tool08-320-base | tool08-320-base2 | tool08-320-storefix | tool08-320-p1 | tool08-320-p2 | tool08-320-p2-r2 | tool08-320-p3 | tool08-320-priohits |
|---|---|---|---|---|---|---|---|---|
| requests sent | 544 | 544 | 544 | 544 | 544 | 544 | 544 | 544 |
| HTTP 200 without error | 544 | 544 | 544 | 544 | 544 | 544 | 544 | 544 |
| output tokens generated | 112233 | 112233 | 112233 | 112233 | 112233 | 112233 | 112233 | 112233 |
| text identical to the reference, all requests | – | 543 / 544 (99.8 %) | 538 / 544 (98.9 %) | 528 / 544 (97.1 %) | 529 / 544 (97.2 %) | 526 / 544 (96.7 %) | 526 / 544 (96.7 %) | 533 / 544 (98.0 %) |
| … served the same way in both runs | – | 540 / 541 (99.8 %) | 530 / 534 (99.3 %) | 468 / 483 (96.9 %) | 458 / 470 (97.4 %) | 457 / 472 (96.8 %) | 471 / 487 (96.7 %) | 470 / 480 (97.9 %) |
| … served differently (tier differs) | – | 3 / 3 (100.0 %) | 8 / 10 (80.0 %) | 60 / 61 (98.4 %) | 71 / 74 (95.9 %) | 69 / 72 (95.8 %) | 55 / 57 (96.5 %) | 63 / 64 (98.4 %) |
| … loaded from LMCache in one run only | – | 3 / 3 (100.0 %) | 8 / 10 (80.0 %) | 60 / 61 (98.4 %) | 71 / 74 (95.9 %) | 69 / 72 (95.8 %) | 55 / 57 (96.5 %) | 63 / 64 (98.4 %) |
| LMCache retrieves (requests with one) | 117 (117) | 116 (116) | 117 (117) | 125 (125) | 128 (128) | 125 (125) | 129 (129) | 95 (95) |
| requests with more than one retrieve | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| preemptions | 5 | 6 | 7 | 9 | 8 | 7 | 11 | 5 |
| running requests refused their next chunk | 10 | 12 | 14 | 18 | 16 | 16 | 22 | 11 |
| GPU KV pool (blocks) | 7456 | 7456 | 7456 | 7456 | 7456 | 7456 | 7456 | 7456 |
| free blocks, min / max over the run | 0 / 7455 | 0 / 7455 | 0 / 7455 | 0 / 7455 | 0 / 7455 | 0 / 7455 | 0 / 7455 | 0 / 7455 |
| steps with no block holder (≥ 50 ms after the last one): free = pool − 1 | 61 / 61 | 61 / 61 | 65 / 65 | 58 / 58 | 60 / 60 | 62 / 62 | 57 / 57 | 57 / 57 |
| requests with a store | 396 | 393 | 477 | 477 | 477 | 477 | 477 | 400 |
| bytes stored (GB) | 73.8 | 73.7 | 108.9 | 108.7 | 108.8 | 108.8 | 108.9 | 71.9 |
