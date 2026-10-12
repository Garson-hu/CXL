# 2026-10-11 — Capacity-matched KV tiers: DRAM-first, CXL-first, static split, and CXL-first with DRAM borrowing

**STATUS: CLOSED 2026-10-12.** Raw: `experimental_results/2026-10-11-capacity-matched-kv/` (`emulation/` = 2b; `real/` = 2a; `tests/` = trials of 2026-10-11).
Tools: `benchmarks/memory/kvemu2.c` (new online emulator), `run_exp2b.py`, `run_exp2b_batch.sh`, `run_exp2b_slo_split.sh`,
`analyze_exp2b.py`; `benchmarks/lmcache/run_2a.py`, `analyze_mp.py`. Agreed with the user
2026-10-11 (experiment 2 of the plan after `2026-10-10-lmcache-kv-traffic.md` and `2026-10-11-throttled-dram-baseline.md`).

## Questions (the user's three)
1. Does CXL-first protect the neighbours? 2. Does managing DRAM and CXL capacity and eviction together raise the KV
hit rate? 3. With sensible admission and eviction in place, does active migration add anything? (Question 3 is tested
with one minimal migration policy, `borrowmig`, added 2026-10-11 — not a memory manager.)

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
DRAM, per-tier LRU), `borrowglob` (same placement, global-LRU eviction until the target tier has room), `borrowmig`
(`borrowtier` + when a block is hit in CXL and the daemon reports DRAM calm, copy it to a DRAM slot freed from DRAM's LRU
end, switch the mapping and free the CXL slot; at most 8 moves in flight; no demotion).

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
campaign for a 7% slowdown target. One run per cell (81 runs, 2026-10-11 22:36 – 2026-10-12 04:41; two static splits
next to Adam added 2026-10-12 09:00 for the bandwidth-SLO question).

## 2b results (emulation, 81 runs, 2026-10-11/12)
GB/s = mean over the window; backlog = largest amount offered but not yet stored; hit = share of reuse accesses served
from host memory (a block still being written is a miss); used = mean occupancy / capacity (LMCache-like: of 250 GiB
raw); DRAM held = mean GiB of KV in DRAM. Writes, backlog, hit and used are from the run without a neighbour, except
where a cell says otherwise. Reader = bandwidth lost by the 8-thread DRAM reader; Adam = median / p99 step slowdown of
the 80-thread Adam step, both against their own BEFORE window. Borrow policies run cxlpathd (`--loan-block-s 1`).

**8B 4× (offered 20.9 GB/s)**
| policy | DRAM / CXL writes GB/s | backlog GB | hit | used | DRAM held GiB | reader | Adam p50 / p99 |
|---|---|---|---|---|---|---|---|
| dram | 19.4 / 0 | 2.2 | 0.190 | 1.00 | 200 | +2.7% | +7.8 / +17.2% |
| dram, 48 GB/s cap | 19.4 / 0 | 4.4 | 0.190 | 1.00 | 200 | +2.1% | +7.8 / +15.5% |
| cxl | 0 / 19.4 | 4.4 | 0.190 | 1.00 | 0 | +0.4% | +0.1 / +1.0% |
| lmcache (DRAM-first) | 7.7 / 11.8 | 4.3 | 0.190 | 0.80 | 80 | +1.4% | +2.2 / +13.2% |
| split (hash, 32% DRAM) | 6.2 / 13.2 | 4.4 | 0.190 | 1.00 | 64 | +1.0% | +2.4 / +5.5% |
| cxlfirst | 0 / 19.8 | 4.4 | 0.150 | 0.68 | 0 | +0.6% | +0.1 / +0.4% |
| borrowtier | 0.1 / 19.7 | 4.4 | 0.150 | 0.71 | 6.0 | +0.6% | +0.1 / +0.5% |
| borrowglob | 0.1 / 19.7 | 4.4 | 0.150 | 0.68 | 0.4 | +0.6% | +0.1 / +0.3% |
| borrowmig | 0.2 / 19.5, moved 21 GB | 2.0 | 0.172 | 0.76 | 16.1 | +0.5% (hit 0.173) | +0.1 / +0.3% (no moves, hit 0.150) |

**8B 8× (offered 39.2 GB/s)**
| policy | DRAM / CXL writes GB/s | backlog GB | hit | used | DRAM held GiB | reader | Adam p50 / p99 |
|---|---|---|---|---|---|---|---|
| dram | 36.3 / 0 | 5.5 | 0.192 | 1.00 | 200 | +5.9% | +16.8 / +29.3% |
| dram, 48 GB/s cap | 36.3 / 0 | 20.9 | 0.192 | 1.00 | 200 | +3.7% | +16.6 / +24.6% |
| cxl | 0 / 36.3 | 26.0 | 0.192 | 1.00 | 0 | +1.1% | +0.1 / +0.3% |
| lmcache | 14.5 / 21.8 | 8.2 | 0.192 | 0.80 | 80 | +2.2% | +5.3 / +20.9% |
| split | 11.7 / 24.7 | 8.4 | 0.191 | 1.00 | 64 | +1.9% | +5.0 / +9.3% |
| cxlfirst | 0 / 37.1 | 29.5 | 0.151 | 0.68 | 0 | +1.0% | +0.1 / +0.3% |
| borrowtier | 1.9 / 34.5 | 10.4 | 0.156 | 0.96 | 56.4 | +1.7%, lends 1.8 GB/s | +0.1 / +0.3%, lends 0 |
| borrowglob | 2.0 / 35.0 | 16.4 | 0.153 | 0.72 | 7.2 | +1.6% | +0.1 / +0.3% |
| borrowmig | 1.9 / 34.6, moved 43 GB | 3.3 | 0.168 | 0.96 | 56.9 | +1.2% (hit 0.171) | +0.1 / +0.3% (no moves, hit 0.151) |

**70B 4× (offered 52.4 GB/s, above CXL's ~46; a multi-server aggregate stress point, see below)**
| policy | DRAM / CXL writes GB/s | backlog GB (late s) | hit | used | DRAM held GiB | reader | Adam p50 / p99 |
|---|---|---|---|---|---|---|---|
| dram | 50.1 / 0 | 6.9 (0.003) | 0.122 | 1.00 | 200 | +6.9% | +22.3 / +47.1% |
| dram, 48 GB/s cap | 47.7 / 0 | 559 (10.7) | 0.143* | 1.00 | 200 | +4.9% | +21.1 / +27.5% |
| cxl | 0 / 46.3 | 714 (14.2) | 0.147* | 1.00 | 0 | +1.4% | +0.1 / +0.4% |
| lmcache | 19.9 / 30.1 | 57.5 (0.7) | 0.125 | 0.80 | 80 | +3.4% | +3.3 / +43.6% |
| split | 16.1 / 34.0 | 32.2 (0.4) | 0.121 | 1.00 | 64 | +2.4% | +6.4 / +12.7% |
| cxlfirst | 0 / 46.1 | 774 (15.6) | 0.132* | 0.68 | 0 | +1.5% | +0.1 / +0.3% |
| borrowtier | 9.7 / 40.3 | 37.6 (0.4) | 0.119 | 0.99 | 61.6 | +2.1%, lends 9.7 GB/s, backlog 38.9 | +0.1 / +0.4%, lends 0, backlog 777 (15.7 s) |
| borrowglob | 9.9 / 40.3 | 145 (1.9) | 0.119 | 0.82 | 31.2 | +2.1%, lends 9.8 GB/s | +0.1 / +0.3%, lends 0, backlog 777 |
| borrowmig | 9.7 / 40.4, moved 13 GB | 24.1 (0.4) | 0.118 | 0.99 | 61.6 | +2.0%, lends 9.6 GB/s | +0.1 / +0.3%, lends 0, backlog 773 |

\* overloaded runs: not comparable (see the visibility check).

## Backlog and visibility check (the user's question)
A block whose store has not completed is never a hit: it counts as a "pending miss". Pending misses: 12–19 at 8B 4×;
729–854 at 8B 8× in every policy, DRAM included (a request reusing blocks its predecessor is still writing, inside one
burst); 19–27 at 70B 4× when DRAM takes part, 1,221–1,421 when CXL alone falls behind (backlog 714–777 GB, stores 14–16 s
late). The emulator therefore does not serve unwritten data. The backlog still changes the hit share the other way:
stores that wait do not evict, so older blocks live longer, and the overloaded runs show *higher* hit shares (cxl 0.147,
DRAM capped at 48 GB/s 0.143) than the runs that keep up (DRAM 0.122). The backlog grows without bound (a real system
would drop the stores or stall the GPU), so those hit shares are an artifact of overload, not a capacity effect.

## 2a results (real vLLM 0.31 + LMCache 0.5.5 multi-process, 2026-10-12)
Qwen2.5-1.5B on the RTX 4060 Ti; conversation trace 0–180 s at 0.08× (556 requests, 2,272 s, 0.245 requests/s, 2,805
prompt tokens/s); LMCache L1 40 GiB, LRU, watermark 0.8, 256-token chunks; same requests in every run. Command
(`benchmarks/lmcache/run_chain_2026-10-12.sh`, hybrid re-run alone after the `slot_bytes` fix):
`run_2a.py experimental_results/2026-10-11-capacity-matched-kv/real <cfg> workloads/mooncake_conversation_trace.jsonl 0
180 0.08 <dram|hybrid|dax> 40`; summary `real/summary.txt` (`analyze_mp.py`).
| L1 | chunks found | TTFT p50 / p90 / p99 | TTFT vs DRAM, same request (median) | L1 used mean / max | KV on the GPU link, stores / loads |
|---|---|---|---|---|---|
| DRAM 40 GiB | 1,904 of 24,188 = 0.079 | 4.33 / 14.33 / 34.62 s | — | 25.9 / 32.1 GiB | 0.091 / 0.050 GB/s |
| LMCache hybrid, DRAM 20 + DAX 20 GiB | 1,947 = 0.080 | 4.15 / 14.43 / 33.76 s | −0.003 s | 26.0 / 31.9 GiB | 0.091 / 0.050 GB/s |
| DAX 40 GiB (dax1.0) | 1,939 = 0.080 | 4.27 / 15.54 / 34.85 s | +0.04 s | 25.8 / 32.1 GiB | 0.090 / 0.049 GB/s |

- At the rate this GPU sustains, where the L1 lives changes nothing measurable: same hits, TTFT within run noise
  (paired per-request differences scatter ±4 s, from queueing order). KV traffic is ~0.1 GB/s, far below what disturbs
  anyone (`2026-10-10-lmcache-kv-traffic.md`).
- **Where the watermark's loss lands in the hybrid** (the allocator's two pools, logged every 5 s, 447 checks): the DRAM
  pool fills first (DAX first used 6 min in), then holds 18.2 GiB on average (max 20.0) while the DAX pool holds 10.8 GiB
  (max 12.2 of 20). The global LRU stops at 80% of the total, and because freed DRAM is refilled first the unused 20% sits
  entirely in the CXL part; DRAM stays ~91% full and keeps taking a matching share of the writes.
- LMCache's `/status` reports no per-tier counters; the per-tier write split and its effect on neighbours come from the
  emulated LMCache-like policy (2b).

## Answers (emulation unless stated)
**1. Does CXL-first protect the neighbours? Yes, in every configuration.** CXL-first, the three borrow policies and
all-CXL cost Adam +0.1% median (p99 ≤ +1.0%) at 8B 4×, 8B 8× and 70B 4×. Writing the KV into DRAM costs it +7.8 /
+16.8 / +22.3% (capping DRAM at 48 GB/s changes nothing, as in `2026-10-11-throttled-dram-baseline.md`); LMCache's
DRAM-first share (39–40% of the writes) +2.2 / +5.3 / +3.3% median, p99 +13 / +21 / +44%; the static 32% split +2.4 /
+5.0 / +6.4% (p99 +5.5 / +9.3 / +12.7%). For about the same DRAM write rate, LMCache's DRAM-first placement has 2.2–3.4× the
split's p99, because it fills freed DRAM with whole bursts. Next to the reader (spare bandwidth) the borrow policies
cost +0.5 to +2.1% against +2.7 to +6.9% for all-DRAM.

**2. Does managing DRAM and CXL capacity together raise the hit share? Only if the DRAM part ends up holding reused
blocks; eviction alone does not put them there.** At 200 GiB effective, every policy that fills both tiers as blocks
arrive reaches the same hit share (0.190 / 0.191–0.192 / 0.121–0.125); per-tier LRU costs nothing by itself (split: used
1.00). CXL-first admission leaves the 64 GiB DRAM part empty (used 0.68) and loses a fifth of the hits (0.150 / 0.151).
Borrowing fills DRAM only when CXL is full and DRAM is calm: at 8B 4× it hardly lends (0.150–0.152); at 8B 8× it fills
DRAM to 56 GiB (used 0.96), but with whatever was written during bursts, which per-tier LRU then keeps (0.156); at 70B
4× its loans fill DRAM and it matches the DRAM policies (0.118–0.119). One LRU over both tiers (`borrowglob`) is no
better (0.150 / 0.153 / 0.119) and empties DRAM: evicting the globally oldest block to make room in CXL frees DRAM
slots that CXL-first admission never refills (DRAM held 0.4 / 7.2 / 31 GiB vs 6 / 56 / 62 with per-tier LRU).
LMCache's 0.8 watermark costs 20% of the raw capacity (matched here with 250 GiB raw); in the real hybrid that unused
20% sits entirely in the CXL part.

**3. With admission and eviction in place, does migration add anything? Yes, where DRAM has calm bandwidth and free
capacity; nothing elsewhere.** `borrowmig`: 8B 4× 0.150 → 0.172 (0.173 next to the reader), 8B 8× 0.156 → 0.168
(0.171), moving 21–44 GB in ~180 s (0.1–0.25 GB/s of DRAM writes); at 8B 4× the 16 GiB it keeps in DRAM serve 2,806 of
3,619 hits. That recovers about half of what CXL-first lost (8B 4×: 0.022 of 0.040) with ~5% of the DRAM writes the
split spends to recover all of it (0.2 GB/s of loans + 0.11 GB/s of moves vs 6.2 GB/s), at no measurable cost to the reader (+0.5%). No gain at 70B 4× (the
loans already fill DRAM; 13 GB moved; 0.118) and none next to Adam: DRAM is never calm there, nothing moves, hit share
stays 0.150. The gain is capacity only — the GPU loads from DRAM and CXL at the same speed (`2026-10-07-read-cost.md`).

**Above the CXL limit: how much DRAM write bandwidth the slowdown target allows.** 70B 4× (a multi-server aggregate:
~5–15 8×H100 servers by the estimate in `2026-10-10-lmcache-kv-traffic.md`) offers 52.4 GB/s; CXL takes 46.3; the mean
deficit is 6.1 GB/s.
- Next to the reader the controller lends 9.6–9.8 GB/s: the backlog stays bounded at 39–50 GB (stores ≤ 0.8 s late)
  instead of growing to 719–777 GB (14–16 s late), for +2.1% reader loss (bound 9%). Enough.
- Next to Adam the controller lends nothing — Adam alone keeps the probe at 275 ns against 127 ns idle, above the guard,
  in every epoch — and the backlog grows to 773–777 GB (15.7 s) as with CXL alone. What Adam would tolerate, measured
  with static splits (DRAM writes spread evenly over blocks; `opt-70b-4x-split24`, `-split40`, `-split`):

  | DRAM writes | Adam median / p99 | backlog peak (stores late) | backlog |
  |---|---|---|---|
  | 0 (CXL-first) | +0.1 / +0.3% | 775 GB (15.7 s) | grows all run |
  | 6.0 GB/s | +2.6 / +6.1% | 176 GB (3.1 s) | bounded, drains between bursts |
  | 10.0 GB/s | +4.3 / +8.2% | 103 GB (1.6 s) | bounded |
  | 16.1 GB/s | +6.4 / +12.7% | 32 GB (0.4 s) | bounded |

  Against a 7% target on p99, about 6 GB/s of DRAM is safe: just the mean deficit, so the backlog stays bounded, but not
  enough for the bursts, which wait seconds. Keeping stores within half a second needs ~16 GB/s, which breaks the p99
  target (within it only for a median target). **So next to a DRAM-heavy neighbour the total safe write bandwidth
  (~46 + 6 GB/s) only just covers the mean demand, and the existing controller does not find even the 6 GB/s** — its
  guard treats "DRAM busy" as "no loan". The reader tail column of `summary.txt` (worst 1% of 100 ms slices) is ~0
  everywhere and is not used.

## Verdict
- CXL-first placement is what protects the neighbours (+0.1% vs up to +22% median, +47% p99), in every configuration.
- It costs capacity unless the DRAM part is refilled with reused data: CXL-first loses a fifth of the hit share against
  every full-capacity policy; global LRU does not help; moving hit blocks to DRAM while DRAM is calm recovers about half
  of it for ~0.3 GB/s of DRAM writes. Where DRAM is never calm (next to Adam) nothing recovers it, and the full hit
  share is only reached by writing into DRAM at a cost to the neighbour (split: +2.4–6.4%).
- Write throughput: CXL alone carries up to ~46 GB/s; above it, DRAM loans keep the backlog bounded next to a neighbour
  with spare bandwidth; next to a DRAM-heavy one the safe DRAM bandwidth (~6 GB/s at 70B 4×) only covers the mean, and
  the existing controller lends none of it.
- Real LMCache (2a): at what one 4060 Ti sustains, DRAM, DRAM-first hybrid and pure CXL L1 are indistinguishable (hits
  0.079–0.080, paired TTFT within ±0.04 s); in the hybrid, the watermark's unused 20% lands in the CXL part.
- Limits: host memory traffic emulation (CPU non-temporal copies by 64 workers on CCDs 6–7, not GPU DMA; ~150 GB/s DRAM
  write peak); one run per cell, ~180 s of traffic each; effective capacity fixed at 200 GiB; 70B 4× is a multi-server
  aggregate stress point and its H100 rates are estimates; borrowing results depend on cxlpathd's `--loan-block-s 1` (the
  60 s default lends almost nothing to bursty writers) and on its guard; `borrowmig` is a minimal migration rule (no
  demotion, 8 moves in flight), not a tuned manager.
