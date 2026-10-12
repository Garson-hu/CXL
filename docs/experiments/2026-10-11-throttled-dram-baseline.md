# 2026-10-11 — Throttled-DRAM baseline: is the CXL tier's protection placement, or just its lower rate?

**STATUS: CLOSED 2026-10-11** (25 runs, 17:27–20:20). Raw: `experimental_results/2026-10-11-throttled-dram-baseline/`. Tools: `benchmarks/memory/kvemu.c`
(new optional global store cap), `run_layer2.py --store-cap`, `run_throttled_batch.sh`, `analyze_layer2.py`.
Requested by the user 2026-10-11 after `2026-10-10-lmcache-kv-traffic.md`.

## Question
In the host memory traffic emulation the CXL tier protected every neighbour (≤ 1.7%) while the DRAM tier hurt them
(up to +63%). But the CXL tier is capped at ~49 GB/s per 20 ms while the DRAM tier took bursts up to ~150 GB/s — at
8B 8× both moved the same 38.9 GB/s on average. If DRAM writes capped at the CXL ceiling hurt the neighbours no more
than CXL writes, the protection came from the rate limit, not from CXL. If they still hurt, it is placement.

## Setup
Identical to layer 2 of `2026-10-10-lmcache-kv-traffic.md` (conversation trace, cache warmed with trace seconds 0–600,
~245 s of traffic, 9.5 GB/s per transfer, 2048-token pieces, 7,300 tokens/s per request, 200 GiB tier, 64 workers on
CCDs 6–7, the same four neighbours on cpus 0..), with the tier in DRAM and **all stores together capped at 48 GB/s**:
every 2 MiB piece starts no earlier than the previous one + piece / cap. Configs 8B 1×/4×/8×, 70B 1×/4× (70B 8× omitted:
at 70B 4× both capped tiers already run at the cap continuously), each alone and beside each neighbour; compared with
the uncapped DRAM and the CXL runs of 2026-10-10.
Check (2026-10-11, `test-8b-8x-80s-dramcap48.txt`, 8B 8× over 80 trace seconds): capped DRAM stores 20 ms max 48.1,
p99 48.1, mean 30.0 GB/s, backlog max 4.0 GB, lateness max 58 ms — CXL tier on the same window 49.6 / 48.8 / 29.8 GB/s,
4.1 GB, 66 ms; uncapped DRAM 150.9 / 147.8 / 35.7 GB/s, 1.2 GB, 0 ms.

## Results (`summary.txt`, `summary.csv`; llama.cpp drift-corrected as in `2026-10-10-lmcache-kv-traffic.md`)
Traffic without a neighbour — stores mean / 20 ms max (GB/s), backlog max, start lateness max:

| config | DRAM uncapped | DRAM capped 48 | CXL |
|---|---|---|---|
| 8B 1× | 5.1 / 112.1, 0.3 GB, 0 ms | 5.1 / 48.1, 2.3 GB, 0 ms | 5.1 / 49.1, 2.5 GB, 0 ms |
| 8B 4× | 19.8 / 149.2, 1.6 GB, 2 ms | 19.8 / 48.2, 4.4 GB, 66 ms | 19.8 / 49.7, 4.5 GB, 68 ms |
| 8B 8× | 38.9 / 151.3, 3.1 GB, 15 ms | 38.9 / 48.3, 26.7 GB, 497 ms | 38.9 / 49.8, 30.4 GB, 589 ms |
| 70B 1× | 13.0 / 150.1, 1.0 GB, 0 ms | 13.0 / 48.3, 6.5 GB, 68 ms | 13.0 / 48.6, 6.6 GB, 27 ms |
| 70B 4× | 50.7 / 150.5, 5.3 GB, 15 ms | 47.8 / (197.0*), 1.11 TB, 22 s | 46.7 / 51.2, 1.39 TB, 28 s |

(*one 20 ms window while the emulator was 1.1 TB behind; the logger's window that once included two windows' bytes —
the mean, 47.8 GB/s, is at the cap.)

Neighbour slowdown % — DRAM uncapped | DRAM capped 48 | CXL:

| neighbour | 8B 1× | 8B 4× | 8B 8× | 70B 1× | 70B 4× |
|---|---|---|---|---|---|
| reader | +0.9 / +0.8 / +0.1 | +2.9 / +2.0 / +0.7 | +6.2 / +3.8 / +1.2 | +1.9 / +1.4 / +0.6 | +7.3 / +4.7 / +1.4 |
| PageRank | +2.0 / +2.4 / −0.8 | +7.4 / +7.8 / +0.3 | +15.8 / +14.3 / −0.2 | +4.2 / +4.4 / −0.0 | +21.9 / +18.0 / +0.1 |
| Adam step | +1.4 / +1.5 / +0.1 | +8.1 / +8.0 / +0.2 | +17.8 / +17.7 / +0.2 | +3.5 / +3.9 / +0.1 | +22.6 / +21.1 / +0.1 |
| llama.cpp (±5) | +3.8 / −0.2 / −2.3 | +2.7 / +4.7 / −1.7 | +3.5 / +10.8 / +1.5 | +2.1 / +2.4 / −3.0 | +11.2 / +13.5 / −5.4 |

## Verdict
- **The protection is placement, not rate.** Capped at the CXL tier's ceiling, DRAM writes move the same bytes with
  the same burst shape and backlog as the CXL tier, and still cost the busy neighbours as much as uncapped DRAM writes
  (Adam step +17.7% vs +17.8% at 8B 8×; PageRank +18.0% vs +21.9% at 70B 4×); the CXL tier costs them ≤ 0.3%.
- Capping the bursts helps only the reader that has spare bandwidth (+6.2% → +3.8% at 8B 8×): the busy neighbours react
  to the volume of DRAM writes, not to the peaks above 48 GB/s.
- A cap costs the writer what the CXL tier costs it (backlog 27 GB, 0.5 s late at 8B 8×), so throttling DRAM buys
  neither the neighbours' protection nor the writer's speed.
