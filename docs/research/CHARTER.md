# Research Charter — Reuse- and Interference-Aware Unified DRAM/CXL Memory Management

*Written 2026-10-17 from the direction the user fixed after discussion with the advisor. This charter is the reference
for every later experiment: each new experiment names the research question and the assumption it tests. Amend by
appending to the change history at the end; never rewrite a decision in place.*

## 1. Research problem

How can a unified DRAM/CXL memory system manage data placement, retention and movement according to the future value
of the data and the cost of moving it, while it respects capacity, bandwidth and interference constraints — so that
the application gets faster and colocated applications keep their performance?

Plain form: decide, for every block of bulk data (a KV-cache block, a checkpoint chunk), whether to keep it, where to
keep it (DRAM, CXL, nowhere), when to write or move it, and what to evict — using what the system can know about the
block's future use and what each write or move will cost the neighbours.

## 2. Core hypothesis (not yet validated)

Jointly considering future data value and data-movement cost improves application performance beyond what independent
cache management and independent bandwidth control achieve.

- **H1 (value).** Blocks differ in future reuse value, and that value has structure that admission, retention,
  placement and eviction can use.
- **H2 (value × cost).** A block with high future value may still not be worth writing or moving into DRAM now, because
  the write costs interference; value and cost must enter one decision.

Both halves are hypotheses. They become findings only when the gates in section 8 pass.

## 3. Research questions

- **RQ1 — Can future reuse information improve unified memory management?** Reuse probability, reuse distance,
  next-use distance and timing, miss penalty, and online predictability. First an oracle analysis of the value of
  future information; then whether information available at run time (history, request features) predicts it. Past
  observable information and oracle future information are kept strictly apart. No complex ML predictor.
- **RQ2 — How should DRAM and CXL jointly manage placement, retention and movement?** Candidate mechanisms: unified
  metadata and ownership, capacity-aware admission, reuse-aware placement, value-aware eviction, selective
  promotion/demotion, reclamation, predictive prefetch. Only mechanisms whose benefit the experiments show stay in the
  system. Central sub-question: if placement at creation time is good, is later migration still necessary?
- **RQ3 — How can the manager execute data movement under interference constraints?** Inherits the write-interference
  work: when to write or move, how much DRAM write bandwidth is safe beside busy neighbours, how writers share DRAM
  and CXL bandwidth, how CXL reads are protected. Online safe-budget estimation, budget-gated admission and
  cross-writer coordination serve this question; none of them is the paper's core problem on its own.

## 4. System scope

- **Primary application: LLM KV cache** (vLLM + LMCache; Mooncake traces). Validates reuse-aware admission, retention,
  capacity management, selective movement, prefetch if justified; metrics TTFT, throughput, recomputation. Server-scale
  traffic is host-memory traffic emulation on c28 (CPU copies, not GPU DMA) and is labelled as such.
- **Secondary application: checkpoint staging** (PyTorch DCP / VeloC producers). Validates bulk-write interference,
  movement scheduling, DRAM/CXL bandwidth sharing, completion latency, durability. It does not use the KV reuse
  predictor; it shares the manager's resource control and keeps its own lifecycle and correctness rules.
- **Platform:** c28 (EPYC 9745, 8 CCDs, dax0.0 + dax1.0 = two CZ120 cards, RTX 4060 Ti 8 GB); `cxlpath` (built) as the
  write path and store.
- **Out of scope now:** general OS page tiering, complex ML prediction, RL replay buffers, new CPU scheduling, unrelated
  CXL characterization, a generic multi-tier storage system, a large cross-writer controller implementation, full
  promotion/demotion without demonstrated benefit. SSD/remote prefetch: potential extension only.

## 5. Existing evidence, by research question

Evidence types: **HW** hardware measurement · **REAL** real application · **EMU** trace-driven host-memory emulation ·
**SIM** trace simulation · **EST** estimate. Files are in `docs/experiments/` (raw data in `experimental_results/`).

| RQ | finding | type | file |
|---|---|---|---|
| RQ1 | 76 / 79 / 58% of 8B KV blocks are never reused (conversation / tool agent / synthetic); the agent trace puts two thirds of its reuses on 0.5% of the blocks; one hour of chat creates ~11 TiB of distinct 8B KV | SIM | 2026-10-09-kv-capacity-characterization |
| RQ1 | 57% of blocks promoted on their first hit never re-hit; the second reuse comes p50 ~130 s after the first (80 GiB of DRAM catches ~40% of second reuses, 320 GiB ~90%) | SIM | 2026-09-23-kv-first-hit-promotion, 2026-10-07-read-cost |
| RQ1/RQ2 | LRU at 200 GiB: every policy that fills both tiers reaches reuse-hit share 0.190 (8B 4×); CXL-first leaves DRAM idle and loses a fifth (0.150); a global LRU does not help; reactive migration (move on first CXL hit while DRAM is calm) recovers half, and nothing beside a busy neighbour | EMU | 2026-10-11-capacity-matched-kv |
| RQ2 | The hit share follows DRAM's share of new blocks and peaks when it equals DRAM's 32% share of capacity; a bandwidth budget with the right bucket depth equals the best static split | EMU | 2026-10-12-budget-gated-admission |
| RQ2 | Real LMCache 0.5.5 on the 4060 Ti: DRAM, DRAM-first hybrid and CXL L1 give the same hits and TTFT; the hybrid is hard-wired DRAM-first; the 80% watermark's slack lands in CXL | REAL | 2026-10-11-capacity-matched-kv (2a) |
| RQ3 | Non-temporal writers on 4 of 8 CCDs cut a DRAM reader to 8% of idle (write-drain cliff); 1–2 CCDs cost 18–22% | HW | 2026-09-08-dram-write-drain |
| RQ3 | CXL writes from an unrelated CCD cost a DRAM reader 0–2%; from the reader's own CCD 64% (MIKU effect), from the paired CCD like DRAM writes | HW | 2026-10-09-cxl-topology-interference |
| RQ3 | DRAM writes capped at the CXL rate still harm busy neighbours (Adam +17.7% vs +17.8% uncapped; CXL tier +0.2%); Optane writes harm same-socket DRAM readers more per byte than DRAM writes | EMU, HW | 2026-10-11-throttled-dram-baseline, 2026-10-06-optane-control |
| RQ3 | The two CXL cards take ~46 GB/s of writes; 70B 4× (52 GB/s offered) falls behind without bound; CXL readers lose 36–40% to CXL writes and a dependent read takes 2.4× longer | EMU, HW | 2026-10-10-lmcache-kv-traffic, 2026-10-07-read-cost |
| RQ3 | Real KV traffic from one 4060 Ti is ~0.1 GB/s in 58 MB bursts and disturbs nobody; emulated server-scale KV writes into DRAM cost neighbours up to +63%, into CXL ≤ 2% | REAL, EMU | 2026-10-10-lmcache-kv-traffic |
| RQ3 | Beside a DRAM-heavy neighbour the probe-based guard lends nothing although 6–8 GB/s of DRAM writes fit a 7% p99 SLO; budget-gated admission equals the best safe split; an oracle budget that rises while the neighbour pauses cuts the 70B backlog 137–145 → 60 GB; 70B 4× beside Adam is marginal (CXL + safe DRAM < 54 GB/s offered) | EMU | 2026-10-12-budget-gated-admission |
| RQ3 | Checkpoint writes into the cards that hold the KV cache: KV loads on the GPU unaffected, a CPU reader of CXL 2.4× slower; at 8B 8× any checkpoint pushes KV load queueing from 53 ms to ~8 s and KV priority cannot help (shared write pipe) | REAL, EMU | 2026-10-12-checkpoint-kv-mixed |
| RQ3 | cxlpath's DRAM loan beside moderate victims: copies 1.3–1.5× faster than all-CXL at 6–8% harm, 4–10× less harm than DRAM staging; beside saturated victims = all-CXL | REAL | 2026-09-22-three-policies-realdata |

What the evidence does **not** say: the static-split result shows only that the current *reactive* migration (promotion
after an access has happened) adds little; it says nothing about management that uses *future* reuse information
(H1), which no experiment has tested yet.

## 6. Unvalidated assumptions (each must be tested or stated as a limit)

- **A1.** Future reuse of KV blocks has structure beyond recency (reuse count, next-use time, position in the prompt,
  conversation continuation) that an oracle can exploit at 200 GiB. → Phase 1, Steps 1–3.
- **A2.** That structure is visible at run time from history and request features, on a trace segment never used for
  calibration. → Phase 1, Step 4.
- **A3.** Hits from DRAM and from CXL are worth the same to the GPU reader (measured on c28: 12.5 GiB/s both; external
  H100 figure: ~10% difference). Promotion therefore adds no read benefit for KV; its only possible value is capacity
  or write-cost placement. → treated as a measured fact on c28 and a stated limit elsewhere.
- **A4.** A miss costs recomputation of the block (estimate: ~15–25 ms per 512-token 8B block on one H100) and the
  benefit of a hit is that recomputation minus the load (~1.3 ms at 50 GB/s). → EST; application metrics in
  emulation use tokens recomputed.
- **A5.** Beside busy neighbours the safe DRAM write budget is small (6–8 GB/s at a 7% p99 SLO) and can be estimated
  online. → RQ3; the online estimator is not built.
- **A6.** Host-memory traffic emulation (CPU non-temporal copies) represents the traffic shape of server-scale GPU DMA
  closely enough for placement and interference conclusions. → stated limit; real checkpoint path carries the real
  system claims.
- **A7.** A joint value–cost policy gains more than the sum of a value-only policy and a cost-only policy. → Phase 2,
  Gate 3.

## 7. Expected contributions (if the gates pass)

- **C1.** A measured account of future-value structure in KV reuse and of its online predictability, with the ceiling
  (oracle) and the realizable share (simple predictor) of reuse-aware admission, retention and eviction at DRAM+CXL scale.
- **C2.** A unified DRAM/CXL manager that takes one decision per block from its predicted value and the measured cost
  of writing or moving it (DRAM write budget under a neighbour SLO, CXL write capacity, CXL read protection), keeping
  only the mechanisms the gates justify, built on the existing `cxlpath` write path.
- **C3.** The interference characterization and movement scheduler that make C2 safe: write-drain cliff, topology
  condition, why throttling and PM do not substitute, SLO-bounded DRAM write budget shared across writers, evaluated
  on the KV cache (emulation + real LMCache) and on real checkpoint staging.

## 8. Go / No-Go gates (quantitative; set before Phase 1 ran)

All comparisons at equal effective capacity (200 GiB: DRAM 64 + CXL 136 GiB), same trace, same warm-up, same
accounting; the test segment is never used to fit anything. Metrics: *reuse-hit share* = hits / reuse accesses;
*overall hit rate* = hits / all block accesses; *recomputed tokens* = misses × 512; *host writes* = bytes stored.

- **Gate 1 — future information has value.** Oracle E (future-aware admission + eviction) vs the best capacity-matched
  baseline (A–D), per trace, on the test segment. PASS if at least one holds: reuse-hit share +5 points absolute;
  recomputed tokens −20%; host writes −50% at equal or better hits. *Why:* the spread between our existing policies
  is 0.005–0.04 in hit share and the emulation noise ±0.001, and a realizable predictor usually reaches at most half
  of an oracle gap — a ceiling under 5 points is within a static-tuning change. −20% recompute is the application-level
  counterpart. −50% writes halves neighbour harm (8B 8× +16.8% → 8B 4× +7.8%) and brings 70B 4× (52 GB/s) under the
  CXL ceiling (46). A fail is reported as a negative result with its cause; no predictor is built on a failed gate.
- **Gate 2 — the information is predictable online.** A predictor that uses only past-observable and creation-time
  features, fitted on segment 1 and evaluated on segment 2, must capture ≥ 50% of the oracle's gain in the metric that
  passed Gate 1, and the cost of its errors (extra recompute from wrong bypass or eviction) must stay ≤ 25% of that
  gain. *Why:* below half of the ceiling the benefit is comparable to the spread between simple heuristics and would
  not survive implementation overheads. If it fails, the report names which information is missing; no ML by default.
- **Gate 3 — joint management adds value.** The joint value-and-interference policy vs the best *independent*
  combination (value-aware placement + interference-aware write control, each tuned alone) at the same neighbour p99
  (≤ 7%): recomputed tokens −10% relative, or DRAM writes −30% at equal hits, and the gain must be traceable to
  blocks decided differently, not to a different budget. *Why:* an additive combination is the null hypothesis; 10% is
  twice the budget-vs-split spread we measured.
- **Gate 4 — application-level benefit.** In emulation and, for checkpoints, on the real path: recomputed tokens or
  TTFT proxy −10% at neighbour p99 ≤ 7%; per-minute backlog not trending up over ≥ 12 minutes; checkpoint completion
  ≤ 1.2× all-CXL; buffer requirement bounded. Hit rate, bandwidth and backlog are intermediate metrics only.

Gates are not re-tuned after a result. If Phase 1 fails Gate 1 or 2, work stops at the report and the problem is
explained; no new topic is started in its place.

## 9. Major rejection risks

- The oracle gap at 200 GiB is small, or it exists but is not predictable online → no C1/C2 (the gates exist for this).
- "Value" rests on an estimated miss cost; reviewers ask for measured TTFT on a server-class GPU with CXL, which we do
  not have (the 4060 Ti is link-bound; H100 nodes have no CXL).
- Realism: KV results are CPU emulation; one machine, two cards; the checkpoint path must carry the real claims.
- Novelty: learned/oracle-guided caching exists (Belady-guided policies, LRB, frequency-based KV eviction in serving
  systems); the claim must be the *joint* value–cost decision across DRAM and CXL under interference, not a better
  cache replacement policy.
- Absolute gains inside the SLO are modest; the paper must show where joint decisions change outcomes, not only
  that a mechanism exists.

## 10. Method rules

Prefer existing code, traces and results; Phase 1 is offline (trace simulation) and does not need the node; no
change to `cxlpathd`, no full manager, no new large KV/checkpoint campaigns before the gates; keep negative results;
all figures matplotlib (default colours, white background); every result carries its evidence type; every experiment
file records method, inputs, accounting and the exact commands; predictors never see test-segment future accesses.

## Change history
- 2026-10-17 — charter created (direction fixed by the user after the advisor discussion; gates set before Phase 1).
