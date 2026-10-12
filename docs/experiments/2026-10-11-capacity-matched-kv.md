# 2026-10-11 — Capacity-matched KV tiers: DRAM-first, CXL-first, static split, and CXL-first with DRAM borrowing

**STATUS: OPEN.** Raw: `experimental_results/2026-10-11-capacity-matched-kv/` (`emulation/` = 2b; `real/` = 2a, later).
Tools: `benchmarks/memory/kvemu2.c` (new online emulator), `run_exp2b.py`, `run_exp2b_batch.sh`. Agreed with the user
2026-10-11 (experiment 2 of the plan after `2026-10-10-lmcache-kv-traffic.md` and `2026-10-11-throttled-dram-baseline.md`).

## Questions (the user's three)
1. Does CXL-first protect the neighbours? 2. Does managing DRAM and CXL capacity and eviction together raise the KV
hit rate? 3. With sensible admission and eviction in place, does active migration add anything? (Not tested here: no
migration is implemented; question 3 is answered by what admission + eviction leave on the table.)

## LMCache 0.5.5 check (2026-10-11, source read in /mnt/local/ghu4/envs/lmcache)
- One L1 tier per server. With `--l1-devdax-path` (multi-process server only) the L1 is either pure Device-DAX or a
  hybrid in which `DevDaxMemoryAllocator.allocate()` / `batched_allocate()` always try the local pinned-DRAM pool first
  and use the DAX arenas as overflow; no option reverses the order. A CXL-first L1 would need a code change (or an
  undocumented runtime arena added from a DRAM-backed file) → by the user's rule, CXL-first and borrowing are emulated
  only; the real comparison (2a) has DRAM-only, LMCache's DRAM-first hybrid and pure DAX.
- Eviction: one LRU over all L1 objects (`eviction_policy/lru.py`), triggered when usage exceeds `--eviction-trigger-
  watermark` (default 0.8) of the total; it does not know the tiers. It never blocks the second tier, but because
  freed slots are refilled DRAM-first, after warm-up the share of new writes into DRAM follows the share of freed DRAM
  slots, i.e. roughly DRAM's share of capacity; the order matters mainly while the cache fills.
- With a DAX L1 the L1 is not "a single registerable memory region" (`l1_exposes_single_memory_region`), which some
  transfer paths answer with a pinned DRAM staging slab: DRAM traffic even for CXL-resident blocks — to check in 2a.

## kvemu2 (online emulator) — what differs from kvemu
Lookups at request arrival; a block is a hit only if its store has completed (present-but-writing and announced
stores count as pending misses and are not stored twice — LMCache refuses a second writer); slot and tier are chosen
when the store starts (LMCache allocates at offload time, the cxlpath writer reserves at copy time), so a loan granted
mid-burst applies to what is written from then on; evictions skip blocks being written or read. Copies are reported to
the cxlpath ledger per 2 MiB piece. Policies: `dram`, `dram` + 48 GB/s store cap, `cxl`, `lmcache` (DRAM-first, global
LRU, 0.8 watermark, 80 + 170 GiB = 200 GiB effective), `split` (DRAM's slot share by hash, per-tier LRU, 64 + 136),
`cxlfirst` (all new blocks to CXL, per-tier LRU: DRAM stays empty), `borrowtier` (CXL unless the running cxlpathd lends
DRAM, per-tier LRU), `borrowglob` (same placement, global-LRU eviction until the target tier has room).

## Finding while testing (2026-10-11): the existing loan rule stops lending in bursty KV traffic
8B 8× and 70B 4× windows (160 trace seconds) with `borrowtier` and the daemon's defaults lent 6 and 27 blocks (mean
loan 0.01 and 0.05 of 16). The daemon saw CXL full (43.4 of 43.9 GiB/s) but its "loan must pay" test of 2026-10-06 —
while DRAM is lent, CXL + DRAM must exceed what CXL alone reached — failed in the tail of a burst, where demand, not
supply, limits the total; two such epochs set the 60 s block (`--loan-block-s`, tuned for the checkpoint loop) and no
loan followed for the rest of the run. With `--loan-block-s 1` (a setting, no code change): 70B 4× lent 2,000 blocks
(16% of the bytes), backlog max 178.8 → 28.9 GB, capacity used 70% → 96%, hit share 14.1 → 14.8%; 8B 8× lent during
bursts only (296 blocks). Experiment 2b runs the daemon with `--loan-block-s 1`; the default's behaviour is reported
as a limit of the existing controller for bursty writers.

## 2b setup
Conversation trace, cache warmed with trace seconds 0–600, then 8B 4× [600, 1320), 8B 8× [600, 2040), 70B 4×
[600, 1320) — about 180 s of traffic each; calibration and workers as in layer 2 (9.5 GB/s per transfer, 2048-token
pieces, 7,300 tokens/s per request, 64 workers on CCDs 6–7). Neighbours: none; the 8-thread reader (spare bandwidth;
daemon probe cpu 16, bound 1.09); the 80-thread Adam step (busy; probe cpu 80, bound 1.04) — the bounds of the policy
campaign for a 7% slowdown target. One run per cell (72 runs, started 2026-10-11 22:36).
