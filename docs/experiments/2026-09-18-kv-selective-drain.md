# 2026-09-18 — KV selective drain: hit-rate loss vs NVMe writes saved (trace analysis, no hardware)

**STATUS: CLOSED 2026-09-18. Verdict: the proposed rule ("drain a KV block to NVMe only if
it was read at least once while resident in the memory tier") is REFUTED — it removes
74–97% of NVMe writes but loses most of the storage-tier hits. It is removed from the
design. An oracle shows real headroom (same or better hit rate with 15–41% of the writes),
but no simple predictor we tried reaches it.**

Question (from `DESIGN.md` §10.6): 58–78% of KV blocks are never read again
(`2026-09-09-kv-trace-analysis.md`); can the drain skip them?

## Method
`scripts/kv_selective_drain.py` — two-tier LRU simulation over the three Mooncake traces
(`workloads/mooncake_*_trace.jsonl`, 512-token blocks, prefix matching: the first block
found in neither tier ends the match, the rest is recomputed and rewritten). Memory tier =
64 GiB (a DRAM pool) or 512 GiB (dax0.0 + dax1.0); storage tier = 3200 GiB NVMe. Block =
64 MiB (Llama-3.1-8B) or 160 MiB (70B). Policies at eviction from the memory tier:
`all` (always drain), `none`, `read>=N` (drained only if read ≥ N times while resident),
`ctx*` (read ≥ 1, or the writing request continued an existing context), `oracle` (drained
only if needed again; uses the future). Raw output:
`experimental_results/2026-09-18-kv-selective-drain/`.

## Results (total hit rate % / NVMe writes relative to `all`; memory tier 512 GiB)
| trace, model | all | none | read>=1 | best ctx | oracle |
|---|---|---|---|---|---|
| conversation, 8B | 35.8 / 100% | 18.1 / 0 | 23.7 / 12% | 24.3 / 21% | 36.6 / 17% |
| conversation, 70B | 30.1 / 100% | 7.0 / 0 | 10.3 / 3% | 10.7 / 4% | 36.1 / 21% |
| toolagent, 8B | 55.2 / 100% | 44.0 / 0 | 47.8 / 13% | 48.3 / 34% | 55.3 / 15% |
| toolagent, 70B | 52.3 / 100% | 35.9 / 0 | 38.1 / 3% | 38.5 / 16% | 55.2 / 20% |
| synthetic, 8B | 64.0 / 100% | 37.8 / 0 | 47.1 / 26% | — | 64.0 / 38% |
| synthetic, 70B | 58.8 / 100% | 20.0 / 0 | 32.0 / 18% | — | 64.0 / 36% |

## Why the rule fails
At these write rates (2.7–3.2 GiB/s for 8B) a 512 GiB memory tier holds a block for only
~160 s, while reuse gaps are p50 59–114 s and p90 282–519 s. Most blocks that WILL be read
again have not been read yet when they are evicted, so "not read while resident" does not
predict "never read". Prefix matching amplifies the loss: dropping one early block makes
the whole later chain unusable. The premise written in the design ("the large CXL tier
makes residency long") was wrong for production-rate traces.

## Other findings
- Growing the memory tier from 64 to 512 GiB raises memory-tier hits strongly
  (8B: conversation 4.5→18.1%, toolagent 34.1→44.0%, synthetic 8.4→37.8%) and removes the
  same share of NVMe reads — a capacity benefit of a CXL pool, independent of draining.
- With `all`, a 70B deployment writes 30 TiB/hour to NVMe and pollutes the 3.2 TiB tier
  (oracle beats `all` by 3–6 points of hit rate there). A good predictor would be valuable;
  request-context predictors are not good enough. Left as future work.
