# 2026-09-09 — B1: how much KV-cache traffic is "written, rarely read"? (trace analysis)

**STATUS: FIRST PASS DONE 2026-09-09 (Mooncake ×3 + ShareGPT). Verdict: LLM serving
produces a large write-mostly KV stream — 58–78% of written KV blocks are never read
again; the rest are read back after seconds–minutes; write rates of 3–8 GiB/s at only
3–7 req/s.** Campaign Phase 4, anchor B, item B1.2. Raw:
`experimental_results/2026-09-09-kv-trace-analysis/`. Traces (gitignored, re-downloadable):
`workloads/mooncake_{conversation,toolagent,synthetic}_trace.jsonl` (Mooncake FAST'25
release; fields timestamp/input_length/output_length/hash_ids, 512-token blocks) and
`workloads/ShareGPT_V3_unfiltered_cleaned_split.json`. LMSys-Chat-1M skipped for now
(needs an HF token) — noted.

## Method
A block hash seen for the first time = KV **written** at prefill; seen again later =
KV **read back** (prefix hit). Reuse gap = time between a block's write and its next
read. KV bytes/token = layers × 2 × kv_heads × head_dim × 2 B: Llama-3.1-8B 128 KiB,
Llama-3.1-70B 320 KiB, Qwen2.5-7B 56 KiB. Rates scale linearly with request rate.

## Results
| trace | req/s | input p50/p90 tok | written blocks | read-back | **never read again** | reuse gap p50 / p90 / p99 | KV write GiB/s (8B / 70B) | read-back GiB/s (8B / 70B) |
|---|---:|---:|---:|---:|---:|---|---|---|
| conversation | 3.40 | 6909 / 27367 | 182,790 | 105,710 (ratio 0.37) | **76%** | 114 s / 519 s / 1578 s | 3.23 / 8.07 | 1.87 / 4.67 |
| toolagent | 6.67 | 6346 / 16810 | 183,300 | 226,316 (0.55) | **78%** | 0 s / 243 s / 609 s | 3.24 / 8.10 | 4.00 / 10.00 |
| synthetic | 3.91 | 11587 / 38615 | 43,924 | 77,953 (0.64) | **58%** | 59 s / 282 s / 583 s | 2.69 / 6.72 | 4.77 / 11.92 |
Peak minute (conversation, 8B): 4,417 new blocks = 4.6 GiB/s of KV writes.
ShareGPT (no timestamps): 92,837 conversations, user turns p50 3 / p90 7, 75% multi-turn
→ every later turn re-reads the prior context's KV; **25% single-turn = written, never read**;
~1.8 K tokens/conversation p50.

## What this says for anchor B
1. The write side is big and mostly dead: at production-like rates a serving node writes
   several GiB/s of KV, and 3 of every 4 blocks are never touched again — the ideal
   write-tier object (Gate 2b shape: park it, never pay the read-back).
2. The reads that do happen come **seconds to minutes** later (toolagent's p50 of 0 s is
   the same-request shared-system-prompt block; its p90 is 4 min) — long enough that a
   read-back is a bulk re-load into DRAM/GPU staging, not a latency-critical access.
3. Read-back volume (2–12 GiB/s) is comparable to or larger than the write volume on the
   agent/synthetic traces → a pool on one CXL pair (45 GiB/s read) has headroom; splitting
   writes and read-backs across the two pairs (write to dax2.0, serve hits from dax0.0)
   is the card-isolation result applied.
4. **Decision: B is worth a real system experiment (B2 → B3).** The KV stream is
   larger than any single application write stream we have measured.

## Next (B2)
Trace-driven KV-pool microbenchmark: replay a Mooncake trace at 1× / 4× / 8× rate;
"prefill" = NT-write of input_length × KV bytes/token into the pool {DRAM, dax2.0, dax0.0,
DRAM+CXL split}; "hit" = read-back of reused blocks into a DRAM staging buffer; a
concurrent DRAM reader (4T stream) stands in for decode attention. Metrics: pool write
throughput, hit read-back latency/throughput, decode-reader slowdown, pool occupancy
under a written-never-read eviction policy (LRU vs "never-read → CXL first").
