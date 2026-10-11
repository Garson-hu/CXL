# 2026-10-11 — Throttled-DRAM baseline: is the CXL tier's protection placement, or just its lower rate?

**STATUS: OPEN.** Raw: `experimental_results/2026-10-11-throttled-dram-baseline/`. Tools: `benchmarks/memory/kvemu.c`
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
