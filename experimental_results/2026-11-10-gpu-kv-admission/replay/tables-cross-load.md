| configuration | sustainable, 320 GB (c28) | sustainable, 80 GB (c61) | sustainable, 80 GB (c66) | intermediate, 80 GB (c73) | overload, 320 GB (c28) | overload, 150 GB (c60) | overload, 150 GB (c61) | overload, large pool (c66) |
|---|---|---|---|---|---|---|---|---|
| stock: mean TTFT / mean request time / misses' mean TTFT / longest TTFT (s) | 4.93 / 11.4 / 7.89 / 44 | 5.41 / 12.2 / 8.12 / 52 | 5.37 / 12.1 / 8.06 / 52 | 9.93 / 19.3 / 12.30 / 61 | 14.67 / 27.6 / 16.64 / 53 | 14.75 / 27.7 / 16.71 / 53 | 14.15 / 26.8 / 16.13 / 52 | 12.72 / 32.4 / 14.53 / 46 |
| oracle hits-first priority | -20 % / -7 % / +2 % / 43 | -19 % / -7 % / +2 % / 49 | – | -32 % / -15 % / +2 % / 66 | -33 % / -16 % / +15 % / 56 | – | – | – |
| shortest-prompt-first priority | – | -28 % / -7 % / -8 % / 48 | -28 % / -7 % / -8 % / 48 | -43 % / -18 % / -15 % / 151 | -49 % / -21 % / -7 % / 249 | – | -49 % / -20 % / -8 % / 259 | -31 % / -10 % / -9 % / 62 |
| oracle shortest-compute-first priority | – | – | – | – | – | – | -52 % / -24 % / -9 % / 228 | – |
| shortest-prompt-first with aging (1 ms per token on c61; 3 ms on c60) | – | – | – | – | – | -50 % / -24 % / -8 % / 96 | -30 % / -14 % / -9 % / 52 | – |
| shortest-prompt-first + token mechanisms (P1) | – | -41 % / -10 % / -4 % / 51 | -41 % / -10 % / -4 % / 51 | – | – | – | – | – |
| token mechanisms (P1; with the 3 s bypass, P2, on c28 at the sustainable load and on c73) | -24 % / -7 % / +6 % / 40 | -23 % / -6 % / +8 % / 52 | – | -23 % / -7 % / +11 % / 63 | +9 % / +9 % / +28 % / 63 | – | – | +29 % / +22 % / +50 % / 68 |
| token mechanisms + bypass, 3 s (P2) | – | – | – | – | -4 % / +2 % / +29 % / 63 | -2 % / +3 % / +28 % / 63 | – | – |
| bypass alone, 3 s | – | – | – | – | – | -10 % / -6 % / -2 % / 56 | -12 % / -6 % / -1 % / 56 | – |
| bypass alone, 10 s | – | – | – | – | – | -23 % / -13 % / -5 % / 54 | – | – |
| bypass alone, 30 s | – | – | -16 % / -5 % / -4 % / 49 | -25 % / -10 % / -6 % / 64 | -28 % / -15 % / -6 % / 58 | -28 % / -15 % / -5 % / 58 | – | – |
| bypass alone, 100 s | – | – | – | – | – | -39 % / -20 % / -4 % / 75 | – | – |
| token mechanisms + bypass, 30 s (P4) | -34 % / -10 % / +3 % / 43 | -33 % / -9 % / +4 % / 52 | – | -32 % / -11 % / +8 % / 65 | – | -28 % / -10 % / +16 % / 61 | – | – |
| token mechanisms + bypass, 100 s | – | – | – | – | – | -45 % / -20 % / +9 % / 109 | – | – |
