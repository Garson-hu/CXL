# 2026-09-23 — KV promotion: how good is the simplest rule, "promote a block to DRAM at its first hit"? (trace analysis, no hardware)

**STATUS: CLOSED 2026-09-23.** Raw: `experimental_results/2026-09-23-kv-first-hit-promotion/` (`first-hit-8B-delay0.txt`,
`variants-8B.txt`). Script: `scripts/kv_first_hit_promotion.py`. Traces: Mooncake FAST'25 conversation / toolagent /
synthetic (`workloads/`), 512-token blocks = 64 MiB for Llama-3.1-8B; spans 59 / 59 / 17 min.

## Question
cxlpath writes every KV block to CXL by default; the advisor asked what serving hits from CXL costs and whether a
better placement is needed. The simplest remedy: mark a block at its first hit, copy it to a DRAM promotion cache
when DRAM is calm, keep the CXL original (so dropping a DRAM copy is free). How many later hits does that move to
DRAM, at what copy cost, and how does it depend on the DRAM cache size? No session prediction, no timed prefetch.

## Model
Three tiers, lookup DRAM copy → CXL (512 GiB, LRU, evictions drained) → NVMe (3.2 TiB, LRU); prefix matching as in
`2026-09-18-kv-selective-drain.md`. Promotion at the k-th hit (k = 1 default, k = 2 variant), the copy landing after a
delay d (0 or 30 s, the calm-time wait); DRAM cache 10 / 20 / 40 / 80 / 160 GiB or unlimited; eviction LRU, LFU (fewest
hits since promotion), or a Belady oracle that also promotes only blocks with a future hit (upper bound).

## Results (share of all hit events served from the DRAM copy; k = 1, LRU unless stated)
| trace | 10 GiB | 20 | 40 | 80 | 160 | unlimited | oracle at 80 | k = 2 at 80 | delay 30 s at 80 |
|---|---|---|---|---|---|---|---|---|---|
| conversation | 0.7% | 12.5% | 14.1% | 19.8% | 29.6% | **59.0%** | 42.2% | 23.5% | 21.2% |
| toolagent | 2.0% | 60.7% | 62.7% | 65.4% | 70.0% | **82.6%** | 75.5% | 67.2% | 65.8% |
| synthetic | 1.8% | 3.2% | 6.3% | 11.0% | 20.3% | **76.6%** | 24.8% | 11.3% | 10.1% |

Copies: 42.6 k / 39.4 k / 18.3 k promotions = 2.7 / 2.5 / 1.1 TiB over the trace = **0.75 / 0.70 / 1.12 GiB/s** of DRAM
copy traffic (about a quarter to a third of the KV write rate; negligible against a 9–40 GiB/s DRAM write budget);
k = 2 halves it. Yield with unlimited DRAM: 1.44 / 4.74 / 3.27 DRAM hits per copy; **57% / 56% / 16% of promoted
blocks are never hit again** even with unlimited DRAM. Gap from a block's first hit to its second: p50 138 / 129 /
111 s, p90 486 / 426 / 331 s. At 11–18 promotions/s an LRU cache of 80 GiB keeps a promoted block for only 70–115 s,
so at ≤ 80 GiB 85–95% of promotions are evicted before their second hit. LFU is worse than LRU everywhere (it protects
old popular blocks and starves fresh conversation chains). A 30 s copy delay costs nothing (calm-time copying is free).
The hit distribution is extreme: one shared system-prompt block takes 12,029 / 10,936 hits; the median promoted block
takes 0.

## Verdict
- **First-hit promotion is enough where reuse is concentrated** (toolagent: 61–65% of hits from DRAM with 20–80 GiB,
  within 6–10 points of the oracle) and **weak for multi-turn conversation workloads** at realistic DRAM sizes
  (14–20% with 40–80 GiB against a 42% oracle at the same size and a 59% unlimited bound; synthetic 6–11% vs 25%).
- The loss has two causes of similar size: admission (57% of first-hit blocks never get a second hit — each
  conversation turn continues with roughly even odds, so past hits predict future ones only weakly) and capacity
  (the second hit comes ~2 min later, the cache holds a block ~1.5 min). A perfect predictor doubles the share
  (to the oracle's 42%); nothing short of ~1 TiB of DRAM reaches 59%.
- Decision for cxlpath: **adopt k = 1, LRU, calm-time copy as the formal mechanism** (cheap, no prediction, free
  demotion, copy traffic ≤ 1 GiB/s), size the DRAM promotion cache at ≥ 80 GiB, and state the ceiling honestly.
  A session-aware admission signal is worth trying only as an optional improvement with a known 2× ceiling on
  conversation traces, and only after the real LMCache experiment shows what a CXL-served hit costs the
  application (on c28's PCIe 4.0 x8 GPU: nothing; on a PCIe 5 GPU: up to 2× per hit load).
