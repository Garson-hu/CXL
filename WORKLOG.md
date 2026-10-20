# Worklog — primary progress tracker

**This is the main place to track the project.** Open this first: the Current
Status below tells you where we are; the Session Log is the reverse-chronological
history. For depth, open only the core docs (see the Doc Map). Keep `docs/` lean —
new findings go here in WORKLOG, not into new scattered files.

---

## Current Status (2026-08-25; hardware/phase lines updated 2026-09-14)

**2026-10-20 addendum — RQ1-B historical learning CLOSED.** New blocks' reuse is not learnable from history; observed
blocks' reuse is (AP 0.75–0.99) but LRU already keeps them. A self-labelling admission filter (class hit-rate feedback,
bypass) is the first online method beating SLRU on both real traces (14–16% of the oracle gain at 200 GiB, −66…−78%
writes); negative on synthetic. Gate 2 stays PARTIAL. dax perms reset by the 2026-10-18 reboot (root 0600).

**2026-10-18 addendum — RQ1 CLOSED (miss-cost feasibility).** Miss cost is prefix-dependent and already exploited by
tail-first eviction in vLLM/LMCache; loading from DRAM or CXL costs ≤ 1/15 of recompute; cost-aware retention adds
nothing over recency/frequency/lifecycle policies (agent traces, Mooncake). The value input to RQ2 is settled and
small; any joint benefit must come from movement cost / interference. Gate 2 PARTIAL unchanged.

**2026-10-17 final-round addendum — RQ1-B CLOSED (reuse horizon vs residence).** Real agent lifecycle signals help only
when the cache turns over within ~2 reuse horizons while still holding the live contexts (90–91% of the oracle gain with
real steady churn, +3–7 pts) or when the cache is below the live set (51–70%); everywhere else 0–4%. A 200 GiB tier with
≤ 64 agents sits in the LRU regime. Gate 2 PARTIAL. RQ1 answered: not a basis for reuse-prediction-driven design.

**2026-10-17 late addendum — RQ1-B AGENT VALIDATION DONE (REAL RUNS).** Real agent runtime events are timely and
block-exact, but at a host cache ≥ the live working set plain LRU already serves 96.5–98.6% of the reuses; the events
clear Gate 2 only under capacity pressure (≤ 0.3 GB with 16 agents) and their robust value is write avoidance (−49%
with deferred stores, simulated) and releasing dead occupancy (74–86% of cache-time). Gate 2 agents: PARTIAL.
Recommendation: lifecycle event as a release + deferred-store interface for RQ3, not hit-rate prediction.

**2026-10-17 night addendum — RQ1-B ANSWERED: NO FOR CHAT, PARTLY FOR AGENTS.** The scheduler queue knows exact next
reads 0.2 s ahead (worthless against 2-minute reuse gaps); the agent loop's continue/end decision is the one realistic
early signal (41–48% of the oracle's gain on the agent trace, +12 points). Recommended next: a small real agent run to
verify the loop signal, then the lifecycle channel as a mechanism. No predictor, no RQ2/RQ3 work started.

**2026-10-17 evening addendum — SESSION-HINT STUDY: NO-GO FOR PREDICTION-AWARE MANAGEMENT.** Perfect session hints
recover ~half of the block oracle (74% with a 300 s bound on chat); realistic chat signals recover nothing; prompt
task-end events in agent workloads 28–41%. Decision: stop reuse prediction as a contribution; keep an explicit
lifetime-release interface as a mechanism; refocus on placement, admission, lifecycle, cross-application coordination
(design discussion next, nothing implemented).

**2026-10-17 addendum — CHARTER WRITTEN, PHASE 1 DONE: GATE 1 PASS, GATE 2 FAIL.** Future reuse information is worth > 5×
the capacity (oracle 80 / 94 / 70% of reuses vs 17 / 65 / 34%, writes −70–83%) but is not predictable from anything in
the traces (online rules ≤ 6% of the ceiling). Migration adds no hits at equal capacity. Phase 2 blocked by the charter's
rule; proposed next: session-hint oracle study (offline), then hint-driven admission in emulation; RQ3 budget estimator
independent. Files: `docs/research/CHARTER.md`, `docs/research/decision-2026-10-17.md`, `docs/DESIGN.md` §11.

**2026-10-13 20:45 addendum — c28 RELEASED; RESEARCH RE-FOCUS PROPOSED.** All progress saved and pushed; the deck is
tracked in git. Proposal to the user: one core problem (SLO-safe DRAM write budget + joint DRAM/CXL bandwidth
arbitration for bulk writers), RQ1 as motivation, RQ4 demoted to a supporting mechanism; decisive next experiments =
online estimator vs oracle (gate), cross-writer arbitration, ablations. No new design or experiment started.

**2026-10-13 18:45 addendum — BUDGET-GATED ADMISSION CLOSED; DECK DELIVERED.** 196 runs: budget-gated admission equals the
best safe static split inside the SLO (smoother writes, no extra hits); both beat the controller next to Adam; an
adaptive (oracle) budget halves the 70B backlog; 70B 4× next to Adam is marginal. Deck: `docs/slides/SLIDES_2026-10-13-
progress-report.pptx`. Next: user decides on online budget estimation / cross-writer admission. No controller or
manager changes made.

**2026-10-12 19:30 addendum — BUDGET-GATED ADMISSION EXPERIMENT PAUSED, c28 RELEASED.** Open file
`docs/experiments/2026-10-12-budget-gated-admission.md`: calibration and evaluation rep 1 done, 76 runs (≈ 8.5 h) remain;
resume = re-launch `benchmarks/memory/run_bga_chain.sh 60` detached in a new c28 allocation (≥ 12 h) after the checks
listed in the file's "Progress" section (dax permissions, no leftovers, binaries). No controller / manager changes.

**2026-10-12 addendum — DIRECTION 2 EXPERIMENTS 1–3 CLOSED.** Topology, LMCache KV traffic, throttled DRAM, capacity-matched
KV tiers and checkpoint + KV mixed are closed (INDEX). CXL-first is the protection; its costs are idle DRAM capacity and,
above ~46 GB/s or with a second CXL writer, write bandwidth. No unified manager built; next steps to be agreed with the
user. c28 allocation 302913 ends 2026-10-13 18:51.

**2026-09-14 addendum.** Healthy NPS1 DRAM since the 2026-09-09 reboot; CXL devdax-only
(dax0.0/dax1.0 usable, dax2.0 root-only). Campaign: 1a/1b/2/3c/4a/B1 done, crippled-DRAM data
(3b, A1.4) discarded. Key new fact: DRAM write saturation (4 CCDs of NT writers, ~273 GiB/s)
puts the socket in drain mode — reads 12×, plain writes 8×, NT writes −20%; CXL-resident work
immune. Next: Phase 4 real apps framed as co-runner protection (see session 21).

**2026-10-06 addendum — ADVISOR REVIEW ANSWERED, PLAN APPROVED, EXECUTION STARTED.** The advisor (2026-10-04) asked why
the work exists, what only CXL can do, why not persistent memory, and about multi-tenancy. Line of argument adopted by
the user: memory-bandwidth interference from bulk writers has only ever been remedied by throttling (MBA, MemGuard,
PARTIES, MT²); CXL is the first independent, write-capable memory pipe, so the traffic can be redirected instead; DRAM is
granted to that data only on evidence (bandwidth headroom → loan; observed reuse → promotion) and everything it holds is
revocable at zero cost. Approved plan (five weeks): why-evidence experiments, four code changes, LMCache + vLLM, read-
while-write, multi-tenancy, sensitivity. Done today: read path v2 (shadow copies, free demotion, groups, k per class,
prefetch), measured CXL capacity + loan-must-pay rule, drain no longer yields, CPU tensors as objects in the PyTorch
plugin (gate written), multi-tenant arbitration designed (DESIGN §10.12), tail-latency and checkpoint-frequency
analyses, SSD arithmetic, literature check; running: fixed-split baseline (c28), Optane control (queued on cascade),
LMCache environment install. Files: `docs/experiments/2026-10-06-why-evidence.md`, DESIGN §10.11 items 18–21, §10.12.

**2026-09-23 addendum — PHASE 2 RE-RUN DONE (real data), KV PROMOTION ANALYSED.** 117 runs: beside moderate victims
(reader, PageRank-32) cxlpath lends 23–34% and is 1.3–1.5× faster than all-CXL inside the bound, 3× faster than
throttling, 4–10× less harm than DRAM staging; beside saturated victims cxlpath = all-CXL with 2.4–3.4× less harm.
llama.cpp-32: real-data DRAM copies run at 22 GiB/s < CXL 30; the constant-capacity fullness rule never fires (flaw to
fix: measure fullness under the co-runner). Advisor's read-path questions answered with a trace analysis
(`2026-09-23-kv-first-hit-promotion.md`): first-hit promotion moves 59 / 83 / 77% of hits to DRAM with unlimited DRAM,
20 / 65 / 11% with 80 GiB LRU (oracle 42 / 76 / 25%); 57% of promoted blocks never re-hit; copy traffic ≤ 1.1 GiB/s.
Decisions pending with the user: implement k-per-stream promotion + calm-time copy + free demotion; set up the real
LMCache + vLLM experiment. Status deck 2026-09-22 published (25 slides, generators in `scripts/`).

**2026-09-22 (evening) addendum — PHASE 2 NUMBERS SUPERSEDED; RE-RUN IN PROGRESS.** While replacing the
synthetic checkpoint copy with the real PyTorch producer, a machine fact surfaced: beside llama.cpp on 32 threads,
c28 writes an all-zero 64 B line at near-full speed and any data-carrying line at 66% (CXL) / 20% (DRAM) of that
rate, while alone the two are identical (`docs/experiments/2026-09-22-zero-line-writes.md`). The phase-2 C producer
copied a 98%-zero snapshot, so every copy rate and harm in `2026-09-22-three-policies.md` (core figure, four
victims) and in the 32-thread / pacing extension is for zero-line writes. Phase 1, the 2026-09-08 cliff and the
PyTorch producer wrote data and stand. The producer now fills a pseudo-random snapshot; the whole phase-2
protocol is re-running (`2026-09-22-three-policies-realdata.md`, ~8 h from 20:05 EDT). **Valid and new: the
headline with the real producer** (`2026-09-22-moderate-pacing-dcp.md` item 3): beside the saturated Adam step,
`dcp.async_save` through cxlpath blocks the training thread 0.8 s vs 1.6 s with DCP's stock DRAM stager, 7.2% vs
12% slowdown, no tail vs 0.4–1.5% for 30 s, durable after 19 s vs 31–33 s. Producer pacing is BUILT (DESIGN
§10.11 item 15); the daemon's default guard is 1.3.

**2026-09-22 addendum — EVALUATION PHASES 1–2 DONE (branch `evaluation`).** Five victims screened for the
DRAM write budget under a reader-protection bound; the core figure (three simple policies vs cxlpath) measured
beside four victims; the Observation-2 headline timeline measured. Two regimes: a moderate victim gets a DRAM
loan (cxlpath 1.3–1.5× faster than all-CXL inside the bound, 3× faster than throttling at equal harm, 5× less
harm than DRAM staging); saturated victims get none (copies are source-bound; cxlpath = all-CXL, 2.4–3.5× less
harm than DRAM staging at the same completion). The headroom guard on the ABSOLUTE probe level (1.3× a
calibrated unloaded level) decides the regime — the old 2.0× guard over-lent. Gap: no producer pacing. Files:
`docs/experiments/2026-09-21-dram-write-budget.md`, `2026-09-22-budget-more-victims.md`,
`2026-09-22-three-policies.md`. Next: phase 3 order and the pacing decision, with the user.

**2026-09-21 addendum — PAPER OUTLINE REVISED.** Motivation = one table, three observations (moving is
nearly free / keeping is harmful / CXL is a safe destination), three strawmen ⇒ "CXL by default, borrow
DRAM only when it does not hurt readers". Gain hypothesis: about twice either simple policy under an
equal reader-protection bound (unmeasured). See `docs/PAPER.md` top section.

**2026-09-19 addendum — SYSTEM BUILT.** The write-path runtime `cxlpath` (Thesis v3) is implemented on
git branch `cxlpath` (`system/cxlpath/`, README there): every step of the build plan passed its gate,
including a 10-minute run of all three clients (VeloC/LULESH, PyTorch async checkpoint, KV stand-in).
Build record: `docs/experiments/2026-09-08-write-tier-campaign.md` "Phase 5 v2"; as-built design and the
list of changes versus the agreed design: `docs/DESIGN.md` §10.10–10.11. **No evaluation experiment has
been run; the evaluation plan is the next thing to agree with the user.**

**2026-09-18 addendum — DESIGN PHASE.** Framing agreed with the user: Thesis v3, the
horizontal write path (PolyStore-inspired; `docs/PAPER.md` top section, `docs/DESIGN.md` §10).
User ruling: finish the design first; NO experiments until the design is agreed. First
experiment afterwards = the O2 motivation figure (all-core LULESH + large checkpoint, staging
on DRAM vs CXL).

**Project.** CXL + LLM systems research for a top systems venue (OSDI/ASPLOS'27,
SOSP'27, FAST'28). On `c28` directly.

**Direction — v2 PIVOT (2026-08-25, advisor-aligned):** *Direction-aware memory
placement* — CXL's full-duplex link + asynchronous stores make it a
**write-preferred tier**; place objects by memory-traffic *direction*
(read-stream / write-stream / RMW), with per-direction bandwidth budgets in the
ObjPlace planner. Zero admin dependency (runs on node 4 as-is). Two GATE
experiments decide go/no-go (duplex matrix; cross-interference asymmetry) — specs
in `docs/experiments/2026-08-25-direction-gates.md`. LLM support = reserved
interfaces only for now
(KV-evict / prefix-insert / optimizer-RMW classes; see `docs/PAPER.md`). Prior
per-card direction (Ideas 1–3, confirmed 2026-07-08) is PARKED: BIOS
de-interleave remains gated; twins +34% and quadrant affinity become supporting
characterization. First evidence for v2: DRAM writes pay exactly the 2× RFO tax
(34.3 = 68.8/2); CXL plain-writes beat the shared-pipe model by +22%.

**Hardware (REBOOT #3 ~2026-08-27, verified 2026-08-28 — log
`hardware/results/2026-08-28-post-reboot-fused-node.log`).** AMD EPYC 9745
Turin, back to **NPS1** (node 0 = all 256 CPUs + 773 GB DRAM, now 151.9 ns —
faster than every prior config, older DRAM baselines stale). **ALL CXL fused
into node 1 (~1018 GiB, all three dax regions system-ram): 238.6 ns, 46.9 @8T /
48.7 @32T GiB/s** (matches Pair-A striped ceiling — allocator placement across
pairs not controllable from userspace). **famfs GONE** (DeepTier off the box —
constraint lifted). **2026-09-01: dax2.0 = DEVDAX, root:kmem 0660, mmap-able by ghu4; node 1 = Pair A only
(508 GiB). Pair B = plain 256 B stripe, card=(off>>8)&1 — PER-CARD TARGETING WORKS via
dax offsets** (`docs/experiments/2026-09-01-pairb-address-map.md`). Pair A still 2-way
root-hashed (unsplittable). Gate results (08-25, NPS4 node 4 = Pair A
alone) remain valid device physics; W3 baselines must be re-measured. GPU 1×
RTX 4060 Ti 8 GB. No MLC — custom `membench` + `cxlprobe`.

**What is built.** `system/placement/`: ObjPlace runtime (`objplace.{h,c}`,
`libobjplace.so`), benchmarks `bwbench` / `gnnbench` / `sensbench` / `mixbench`,
overhead `obench`, `test_objplace`. `benchmarks/`: `membench` (C) + Python
orchestrators (`phase21/22`, `confirm`, `integ`, `eval_objplace`, `eval_block2`) +
`embbench.py` (ctypes bridge to ObjPlace).

**Headline results** (full tables: `docs/RESULTS.md`). CXL latency 1.53× DRAM, BW
35.5 GiB/s. Bandwidth-bound CXL victim 2.0–2.13× under co-runner (latency-bound
≤1.23×, DRAM ~1.0×). ObjPlace = manual ±<1%, +14.3% vs interleave (skewed
embedding), +315% bandwidth recovery, +118% vs hotness-only, pressure-aware
(+67%→+116%), overhead ~0%. GNN skewed +8.3% / uniform −11.6%.

**GATES PASSED (2026-08-25).** G1 duplex: CXL joint 59.4 GiB/s vs 45.8 single
(+30%); DRAM pinned/degrading — write direction is real added capacity. G2b
(CCD-separated): write stream moved DRAM→CXL costs the DRAM reader NOTHING
(68.6 GiB/s = idle; 10.9 under DRAM writers = 6.3× collapse), latency idle-equal,
writers keep 80%. CXL co-located readers pay (−41% bw; chase 2.2×). Bonus: same-CCD
victim/aggressor threads share a fabric port that dominates cross-node interference
— now a methodology invariant. Full tables:
`docs/experiments/2026-08-25-direction-gates.md`.

**Open issues / honest gaps.** Novelty double-check pending (Clove, VLDB'25 line).
Multi-tenant evidence still synthetic. No established-baseline comparison yet
(TPP/MEMTIS/Colloid/Nomad). NPS4 invalidated all NPS1 DRAM baselines. Old parked
gaps unchanged (INTERLEAVE candidate, per-card access, KV claim).

**Per-card unlocked (2026-09-02).** Pair B addressable per card via /dev/dax2.0 offsets; cards
measured as isolation domains (`docs/experiments/2026-09-02-pairb-card-interference.md`).
The parked per-card direction is no longer blocked — it merges into the direction-aware
thesis as "place write streams on their own card".

**Next step (critical path) — CAMPAIGN PLAN 2026-09-08:** the four-phase plan +
PolyStore integration lives in `docs/experiments/2026-09-08-write-tier-campaign.md`
(ACTIVE umbrella; per-phase TODO with statuses — READ IT FIRST). Order: 1a mechanism
write-up → 2b CXL 1/2/4-card scaling → 3a/3b stencil (all DRAM-independent) →
[BIOS: Memory Interleaving back to Auto] → 1b DRAM write-drain matrix → 3c → 4 LULESH/
VeloC → 5 PolyStore. Blockers: DRAM interleave disabled (2026-09-08 log); PolyStore PDF;
LULESH version. Each step needs explicit user approval before execution.

**Doc Map (reorganized 2026-08-25 — rules in `docs/README.md`).**
- `WORKLOG.md` (this file) — status + history. **Start here.**
- `docs/PAPER.md` — thesis, claims, positioning (living; append-only Change history).
- `docs/DESIGN.md` — CURRENT system design + API (living; append-only Change history).
- `docs/experiments/INDEX.md` — one row per experiment: date, question, verdict, link.
- `docs/experiments/YYYY-MM-DD-<content>.md` — one file per experiment; ONE active,
  frozen once closed. `METHODOLOGY.md` holds the shared invariants.
- `docs/guides/STUDY_GUIDE_OBJPLACE_DETAILED.md` — code-level onboarding walkthrough.
- `docs/slides/` — dated decks.
- `Related.md` (repo root) — literature scan (2026-05-20; superseded for coverage by the 2026-07-08 review).
- `DEEP_RESEARCH_2026-07-08-cxl-landscape.html` (repo root) — 97-paper verified map + gap analysis (Part I) + ranked research directions + 8-week plan (Part II). **The reference document for related work and claims.**
- `benchmarks/results/2026-07-08-cxl-lit-review.json` — machine-readable records for all 97 papers (evidence quotes, corrections).
- `docs/archive/` — superseded per-phase notes (kept for reference, not maintained).

---

## Session Log

### 2026-10-18 → 2026-10-20 (session 34, RQ1-B historical learning; cluster power loss on 2026-10-18)

- Characterization `scripts/kv_history_characterize.py` (prefix groups by depth, sharing, concentration, inter-reuse
  intervals, popularity persistence, conditional new-block reuse, LRU premature evictions at 100/200/400 GiB) on the
  Mooncake conversation / tool-agent / synthetic traces and two real agent traces → `*-history.json`, fig-history-*.
- Online predictors `scripts/kv_online_predict.py` (prequential, lazy labels, NEW vs OBSERVED blocks, H = 60/300 s,
  tables + online logistic; AP / P@R50 / calibration per time fifth; next-interval error) → `*-predict.json`, fig-predict-*.
- Replay `scripts/kv_agent_replay.py` extended with learned policies (pop / lhd / olr / cond, feedback labels from the
  cache's own hits and evictions, `--admit-th` bypass, `--dump-hits`); `scripts/kv_hits_compare.py`, `kv_hits_explain.py`,
  `kv_history_figs.py`. Mooncake replays at 100/200/400 GiB (tail order, prefix-aware) and agent traces.
- Power loss on 2026-10-18 killed the tool-agent replays before their CSVs were written; c28 rebooted (dax perms reset to
  root 0600 again), /mnt/local intact, uncommitted work intact; checkpoint commit ce62460; tool-agent replays rerun
  split by capacity on 2026-10-20.
- Result: history predicts observed-block reuse (AP 0.75 / 0.99) but not new-block reuse (≤ 1.3× base); retention
  learning = LRU; learned admission bypass beats SLRU on both real traces (14–16% of the oracle gain at 200 GiB, writes
  −66…−78%), negative on synthetic. Gate 2 stays PARTIAL. Report CLOSED, decision report + INDEX updated.

### 2026-10-18 (session 34, RQ1 miss-cost feasibility)

- Microbenchmark `benchmarks/lmcache/misscost_bench.py` + `misscost_run.py` (3B-AWQ, LMCache L1 4 GB in DRAM and on
  /dev/dax1.0, GPU cache 16k tokens; cold / GPU hit / L1 hit / hole / clean prefix / 4-at-once; L = 1k–7.7k, 3 reps):
  recompute 0.134 ms/token (+7%/1k position), load from either tier ≤ 1/15 of recompute, hole at f·L = prefix of f·L,
  contention 3.1×; one store/evict stall (2.6 s) at a full L1. Fit + figure `scripts/kv_misscost_figs.py`.
- Replay extended (`--order tail` = LMCache's reversed-touch order, prefix-aware usable hits, TTFT model, `cost`,
  `slru+cost`, `event_cont+cost`, `--cost-noise`, `--mooncake` loader); first cost-only version evicted shared heads →
  0 hits (kept as a finding); tables `scripts/kv_misscost_tables.py`. Agent traces and Mooncake 100/200/400 GiB.
- Result: cost-aware retention never beats recency-based policies (−50…+2% of the oracle's TTFT gain; 0% Mooncake),
  no complement to SLRU or the continue signal, insensitive to ±50% cost error. RQ1 closed; Gate 2 unchanged PARTIAL.
  Experiment file CLOSED; decision report and INDEX updated. Node idle (no servers left running).

### 2026-10-17 (session 34, final RQ1-B round) — reuse horizon vs cache residence

- Public trace with real timestamps: Exgentic/agent-llm-traces (HF, CDLA-2.0; 39 parquet shards, kept outside the repo;
  `scripts/agent_trace_public_stats.py` → `experimental_results/2026-10-17-rq1b-reuse-horizon/public/`): horizons
  6–11 s p50 / 20–36 s p90, prompts 20k–60k tokens, 7–35 calls per session; spans end at submission, so tool and model
  time are not separable. SWE-bench trajectory datasets have no timing.
- Real long-tool workload `benchmarks/agent/agent_tasks_lt.py` (24 CSV datasets 1.5M–6M rows under
  /mnt/local/ghu4/agent-data, pandas / pytest / python_exec tools executed as subprocesses; measured 2.5–15 s), runner
  and launcher extended (workload selection, client CPU set, background replay with optional de-quantization).
  Runs: lt-k8-l1g, lt-k16-l1g, lt-k8-l1g-bg / lt-k16-l1g-bg (bursty Mooncake background), lt-k8-l1g-bg2 / lt-k16-l1g-bg2
  (steady background). Replay extended (`--churn`, `event_cont`, evictions-before-reuse, live/dead occupancy, coverage,
  residence, W_live / P / H); regime analysis `scripts/kv_agent_regime.py`; tables `scripts/kv_horizon_tables.py`.
- Result: continue signal ≥ 50% of the oracle gain only in the band W_live ≲ C ≲ P·H (90–91% with real steady churn,
  +3–7 pts) or below the live set (51–70%); 0–4% in every no-/moderate-pressure setting; end signal never the useful one;
  bursty churn favours SLRU. Gate 2 PARTIAL; RQ1 closed. Experiment file CLOSED, decision report, INDEX updated.

### 2026-10-17 late (session 34, continued) — RQ1-B real agent runtime validation

- Built a minimal real agent workflow: OpenAI Agents SDK 0.24 (separate venv `/mnt/local/ghu4/envs/agent`, loop unmodified)
  with three local tools over a seeded report corpus (`benchmarks/agent/agent_tasks.py`), 400 tasks; vLLM 0.31 + LMCache
  0.5.5 MP with Qwen2.5-3B-Instruct-AWQ (1.5B fp16 collapsed to one-shot tool calls); logging-only instrumentation:
  SDK RunHooks + per-call X-Request-Id, and LMCache's event bus mirrored to JSONL through a `sitecustomize.py`
  (`benchmarks/agent/kvevt/`). Runs k8-l1g / k16-l1g / k8-l4g (5.2 / 2.9 / 5.2 min serving); lazy-offload run crashed
  LMCache's FIFO policy (ValueError in `mark_req_finished`), kept as a limit.
- Analysis `scripts/kv_agent_events.py` (join, timing, semantics, figures) and replay `scripts/kv_agent_replay.py`
  (capacity sweep with the real events, deferred-store variants); tables `scripts/kv_agent_tables.py`.
- Results: continue/end known with no delay; continue → 100% context re-read 1.3 s later; end → 84–85% private chunks
  dead, 92% shared chunks live, event 0.4 s after the last write; real reuse-hit 0.965–0.986 under plain LRU; events
  ≥ 50% of the oracle gain only below the live working set; writes −49% only with deferred stores (simulated).
  Gate 2 agents PARTIAL. Experiment file CLOSED, decision report and INDEX updated. Node: allocation 313660 idle.

### 2026-10-17 night (session 34, continued) — RQ1-B: application-level reuse signals

- Inventory from source (vLLM 0.31: `Request.block_hashes` at creation, `on_new_request` at arrival, `request_finished`,
  per-request `cache_salt` / `kv_transfer_params`; LMCache 0.5.5: eager-prefetch lookup at arrival, `end_session`, pin/unpin,
  lazy offload buffering stores past request end, per-salt isolated LRU; OpenAI Agents SDK / LangGraph loops: tool calls →
  call again, final → end). Lead times measured on the c28 runs: queue wait p50 0.19–0.26 s, p90 2.6–6 s.
- Replay (`kv_session_hint_study.py` queue policies): queued-request protection ≤ 0.3% of the oracle's gain at W ≤ 10 s,
  2–5% at 30–60 s; the agent task-end event 41% (+12 points), 48% with a 60 s queue; chat has no realistic early signal.
  `docs/experiments/2026-10-17-rq1b-application-reuse-signals.md` (CLOSED); decision report updated; Gate 2 FAIL chat /
  PARTIAL agents. Recommended: an agent-runtime lifecycle channel, verified by one small real agent run; no predictor,
  no queue-pin project. Nothing implemented; node idle.

### 2026-10-17 evening (session 34, continued) — session-level hint study (the last predictability experiment)

- `scripts/kv_session_hint_study.py` + `kv_session_hint_figs.py`; `docs/experiments/2026-10-17-kv-session-hint-study.md`
  (CLOSED). Sessions reconstructed from prefix chains; reuse is within-session (89–100%); the next turn re-reads ~80% of
  a turn's blocks. A perfect "session continues" hint (oracle) recovers 40–54% of the block oracle's gain (74 / 51 / 41%
  with a 300 s bound), from retention (eviction-only = admission + eviction); writes −45–66% with admission. Realistic
  signals: recency / idle TTL = LRU (0%); termination events 60 s late = 0%; within ~10 s = 28–41% (agent frameworks).
  False positives cost most (30% halves the benefit); false negatives are cheap; delay > 10 s kills it.
- Decision (decision report updated, Gate 2: FAIL for chat, borderline for agents): NO-GO for a prediction-aware unified
  manager; stop the reuse-prediction direction; keep an immediate "lifetime release" event as an optional interface;
  refocus the unified manager on capacity-aware placement, interference-aware admission, lifecycle management and
  cross-application coordination — to be discussed with the user, not implemented.

### 2026-10-17 (session 34) — research charter, Phase 1 oracle study (offline), decision report

- The user fixed the research direction (reuse- and interference-aware unified DRAM/CXL memory management; core hypothesis
  H1 future value / H2 value × cost; RQ1 future information, RQ2 joint placement/retention/movement, RQ3 movement under
  interference; gates before experiments). Written as `docs/research/CHARTER.md` (evidence classified by RQ, assumptions
  A1–A7, Gates 1–4 with criteria and rationale) BEFORE the analysis, as required.
- Phase 1 (trace simulation, no node time): `scripts/kv_reuse_characterization.py`, `scripts/kv_oracle_study.py`,
  `scripts/kv_oracle_figs.py`; `docs/experiments/2026-10-17-kv-reuse-oracle-study.md` (CLOSED). Gate 1 PASS: the oracle
  (Belady MIN with bypass) at 200 GiB serves 80 / 94 / 70% of reuses vs 17 / 65 / 34% for the best baseline; recompute
  −26–43%; host writes −70–83%; the gain is "do not store the 58–79% never-reused blocks" (worth > 5× capacity; 300 s of
  foresight gives 94%). Gate 2 FAIL: no creation-time or reconstructed-session feature separates dead from live blocks in
  the two real traces; online rules (segmented LRU, reactive promotion, admission filters, frequency eviction) recover
  ≤ 6% of the ceiling. Migration adds no hits at equal capacity (oracle + ideal tiers = oracle; reactive migration's +3
  points = a logical SLRU with zero movement).
- Decision report `docs/research/decision-2026-10-17.md`; design sketch `docs/DESIGN.md` §11 (keep cxlpath store,
  CXL-first path, exclusive tiers + static admission share; add logical segmented retention and the RQ3 write scheduler;
  a block-lifetime hint interface only if a session-hint oracle study passes; drop promotion/demotion for hits, prefetch,
  ML prediction). Phase 2 not started (charter rule). Next, pending the user: session-hint oracle (offline), hint-driven
  admission in emulation, the online safe-budget estimator (RQ3).
- Node: on c28 under allocation 313660, idle; nothing queued; no cxlpathd or manager code touched.

### 2026-10-13 evening (session 33, closing) — progress saved, c28 released, research re-focus proposed

- Saved: every raw file of the budget-gated campaign (quiet, calibration, evaluation ×3, varying, longrun, depth,
  depth-eval; large files gzipped), the checkpoint + KV runs, the node-local chain/install logs copied into the repo
  (`/mnt/local/ghu4` is node-local and not durable), the deck and its figures now TRACKED in git by the user's request
  (`docs/slides/SLIDES_2026-10-13-progress-report.pptx` + `docs/slides/2026-10-13-progress-report/`; the three
  older decks in `docs/slides/` stay local-only). Nothing was running when the allocation was released.
- Research re-focus (proposal, to be decided by the user; details in the chat of 2026-10-13 and
  `memory/project_direction.md`): one core problem — how much DRAM write bandwidth bulk writers may use beside
  latency-sensitive readers, estimated online under a p99 SLO, and how one host shares it with CXL's write capacity
  among writers and readers; RQ1 (characterization) = motivation; RQ2 + RQ3 = one mechanism (budget estimator +
  budgeted admission + cross-writer arbitration); RQ4 (unified capacity management) = supporting mechanism +
  negative-result ablation, not a contribution. Decisive experiments: the online estimator vs oracle / static splits
  (go/no-go gate), cross-writer arbitration (checkpoint + KV), SLO/neighbour/depth ablations.
- Open problems carried forward: online safe-budget estimation (the probe-based guard finds none beside Adam);
  cross-writer admission (8B 8× + checkpoint collapse); evaluation realism for KV (emulation, small GPU);
  single machine / two CXL cards; the selection rule's SLO margin.

**Resume notes (2026-10-13).** Allocation 311690 released 2026-10-13 ~20:45 (the user's queued job 311691 "cxl" is a
re-request). c28: `/dev/dax0.0`, `/dev/dax1.0` = `root:kmem 0660` by a manual admin fix — a reboot resets them (ask the
admin; no udev rule); `dax2.0` reserved. Node-local (`/mnt/local/ghu4`, lost on reimage): `envs/lmcache` (vLLM 0.31.0 +
LMCache 0.5.5, python 3.12), `hf/` (HF_HOME; Qwen/Qwen2.5-1.5B-Instruct), `cache/`; rebuild from
`hardware/results/2026-10-06-lmcache-install*.log`. Untracked binaries to rebuild from source if missing:
`benchmarks/memory/{kvemu,kvemu2,kvemu3,topo,readcost,gpuread}` (gcc lines in the experiment files),
`benchmarks/policy/{reader_victim,ckpt_producer}` (`make -C benchmarks/policy`), `benchmarks/lmcache/ckpt_cxl`,
`system/cxlpath/build/*` (see `memory/project_cxlpath_build.md`). Start: `salloc -p turin128 -w c28 -t 3-00:00:00`,
then `ls -l /dev/dax0.0 /dev/dax1.0`, `pgrep -fa "kvemu|cxlpathd|opt_step|reader_victim"`,
`system/cxlpath/build/cxlp_admin kvemu view` (expect "no such store"). No experiment is queued: the next one follows
the user's decision on the re-focus.

### 2026-10-13 (session 33) — budget-gated admission campaign finished and closed; progress deck for Dr. Mueller

- Resumed on allocation 311690 at 10:22 (dax permissions intact, binaries unchanged, HEAD = pushed state); the chain
  skipped the 101 finished runs. Done today: 49 evaluation repeats, 24 varying-load runs (Adam 30 s on / off, oracle
  budget), 3 long runs (70B 4× × 720 s), 18 bucket-depth runs + 3 depth-evaluation repeats; 196 runs in all, none failed.
- Verdict (`2026-10-12-budget-gated-admission.md`, CLOSED): under the same 7% SLO budget-gated admission equals the best
  safe static split (hits and backlog), with smoother DRAM writes; a deeper bucket raises utilization (0.3 → 0.9) but
  not the evaluation hit share; both beat the existing controller next to Adam (0.180–0.190 vs 0.157–0.161; it lends
  nothing there, 70B backlog > 700 GB); the oracle budget that rises while Adam pauses cuts the 70B 4× backlog peak
  137–145 → 60 GB; the long run shows 70B 4× next to Adam is marginal (CXL + 6–8 GB/s safe DRAM < 54 GB/s offered);
  migration matches the split next to the reader for 5–30× fewer DRAM writes but breaks the SLO at 70B 4×. Method
  notes: chosen settings straddle the SLO (rule 2 takes the largest feasible value; p99 noise ±0.5 points) — a
  selection margin is needed next time; calibration-segment optima (depth 4 / 16 GB/s: 0.201) did not transfer.
- Research-progress deck for Dr. Mueller: `docs/slides/SLIDES_2026-10-13-progress-report.pptx` (26 slides, STE style,
  every data figure from the raw results; sources in `docs/slides/2026-10-13-progress-report/`; generators tracked as
  `scripts/figs_deck_2026-10-13.py` and `scripts/deck_2026-10-13.py`). First built in a top-level `presentation/` dir
  by mistake, moved to `docs/slides/` (local-only by the 2026-09 rule) at the user's reminder.
- Pending user decisions: online estimation of the safe DRAM budget (the probe guard finds none beside Adam);
  cross-writer admission for checkpoint + KV; whether to track the deck in git (`git add -f`).

### 2026-10-12 (session 32) — budget-gated admission: tools, calibration, evaluation rep 1; PAUSED (node released)

- Experiments 2 and 3 of the plan closed and the contribution assessed (session 31 entry, INDEX). User's next step
  (option 1): budget-gated admission vs the best safe static split, the existing controller and CXL-first + migration,
  under a 7% p99 neighbour-slowdown SLO; no change to cxlpathd, no cross-writer admission, no unified manager.
- Tools (2026-10-12): kvemu2 `budget` policy (one-block token bucket, budget fixed or read from a file = oracle),
  `KV2_SPLIT_SHARE`, common warm-up; run_exp2b phases (neighbour SIGSTOP/SIGCONT) + oracle phase budgets; the reader
  victim counts progress every 64 MiB (1 GiB counting quantized 100 ms samples to ~10% steps — all earlier reader p99
  figures are not measurable); `quiet_baseline.py`, `analyze_bga.py`, `select_settings.py`, `run_bga_chain.sh`.
- Quiet baselines: Adam and reader p99 stable to ≤ 1.3% across 60 s windows. Calibration (72 runs, trace from 2040 s):
  the budget's smoother writes buy SLO room (8B 8×: 8.9 GB/s at +6.8% p99 vs the split's 9.0 at +7.0%; 20 ms peaks 20
  vs 40–50 GB/s at 8B 4×) but the one-block bucket caps DRAM's share of writes at ~25% (chunks of 4 blocks fall due
  together), and the hit share peaks when DRAM's share of new blocks equals its 32% share of capacity. Selection rule
  fixed (rule 2: best hit inside the SLO; largest feasible when overloaded; oracle off-budget = largest swept) before
  any affected run. Evaluation rep 1 (29 runs): next to Adam the controller lends nothing (hit .157–.161, 70B 4×
  backlog > 700 GB); budget .180 vs best safe split .164 at 8B 8×, equal elsewhere; migration recovers hits cheaply
  next to the reader but never beats admission and breaks the SLO at 70B 4× (+7.5%).
- 19:25: chain stopped between runs at the user's request (node to be released); the run in flight finished; nothing
  interrupted. Remaining: 49 evaluation runs, 24 varying-load, 3 long runs ≈ 8.5 h; resume steps in the experiment
  file (`2026-10-12-budget-gated-admission.md`, "Progress"). Pending user decision: a one-chunk-bucket sweep (~1.5 h).

### 2026-10-11/12 (session 31) — throttled DRAM baseline, capacity-matched KV tiers, checkpoint + KV mixed

- Throttled DRAM baseline closed (`2026-10-11-throttled-dram-baseline.md`): capping the DRAM tier at CXL's rate does
  not protect neighbours — the protection is placement.
- Capacity-matched KV closed (`2026-10-11-capacity-matched-kv.md`). LMCache 0.5.5's hybrid L1 is hard-wired DRAM-first,
  so CXL-first and borrowing were emulated (new online emulator `kvemu2`: a block is a hit only after its store
  completes; tier chosen at store start; the cxlpath ledger sees every 2 MiB piece). 81 runs + 2: CXL-first keeps Adam
  at +0.1% everywhere but idles DRAM capacity (hit share 0.150 vs 0.190); global LRU does not help; a minimal
  calm-time migration (`borrowmig`) recovers half for ~0.3 GB/s of DRAM writes, nothing next to Adam. Above CXL's
  ~46 GB/s (70B 4×) loans bound the backlog next to the reader; next to Adam ~6 GB/s of DRAM fits a 7% p99 target (the
  mean deficit only) and cxlpathd lends none (its guard). Finding: cxlpathd's 60 s loan block stops loans for bursty KV
  writers; 1 s used. Real LMCache (2a, 4060 Ti): DRAM / hybrid / DAX L1 indistinguishable; the hybrid's watermark
  slack sits in the CXL part.
- Checkpoint + KV mixed closed (`2026-10-12-checkpoint-kv-mixed.md`): real KV path unaffected (GPU link-bound), a CPU
  CXL reader 2.4× slower inside checkpoint bursts; emulated 8B 4× KV priority removes the KV load slowdown, a fixed
  rate does not; 8B 8× any checkpoint overloads CXL writes (load queueing 53 ms → ~8 s) in every mode.
- Incidents: the first hybrid run failed (`slot_bytes` required by the DAX adapter; kept in
  `real/failed-hybrid-no-slot-bytes/`). Launch chains now copied into the repo (`run_chain_2026-10-12.sh`,
  `run_exp2b_slo_split.sh`).

### 2026-10-10/11 (session 30) — topology, LMCache KV traffic in two layers, Optane

- Topology closed: CXL writes cost a DRAM reader 0–2% from an unrelated CCD, ≈ DRAM writes per byte from the paired
  CCD (4+5), and are worse than DRAM writes from the same CCD (MIKU's effect). Earlier campaigns were in the safe
  placement. User: keep it a characterization result, no automatic placement mechanism for now.
- LMCache KV traffic closed (`2026-10-10-lmcache-kv-traffic.md`). Layer 1 (real vLLM + LMCache, 1.5B on the 4060 Ti):
  the card carries ~0.08–0.2× of the trace; stores are 2048-token bursts of 0.058 GB at ~9–10 GB/s (LMCache's figure
  confirmed once the PCIe sampler read NVML's cumulative counters every ~1.4 ms); 0.065–0.14 GB/s on average; no
  neighbour moves (llama.cpp's raw 17% was its own context-growth drift; corrected +0.1%). Layer 2 (host memory
  traffic emulation, kvemu, 8B/70B × 1/4/8×): DRAM tier costs neighbours +1–4% up to +17–63% (tails +83%); CXL tier
  ≤ 1.7% but cannot keep up from 70B 4× and queues bursts — the case for the DRAM loan.
- Optane control (fixed: PM node detection, PM's socket) closed: PM writes hurt same-socket DRAM readers more per byte
  than DRAM writes; plain stores to PM cut a reader from 39.9 to 1.9 GiB/s.
- Incidents: the session restart killed background jobs (now detached with setsid); the c28 Slurm allocation's 3-day
  limit (2026-10-10 18:51) killed the overnight chain — the current allocation 302913 ends 2026-10-13 18:51. Raw files
  > 500 kB are stored gzip-compressed.

### 2026-10-07/09 (session 29) — read cost, group-meeting deck, the advisor's unified-pool proposal, topology pilot

- 2026-10-07: read cost of CXL vs DRAM measured (`2026-10-07-read-cost.md`); 27-slide group-meeting deck in plain
  English, figures from `scripts/figs_deck_2026-10-07.py`, matplotlib default colours by the user's request.
- 2026-10-09: the user brought a long proposal for a unified DRAM/CXL memory pool (the advisor's idea: promotion with
  invalidation of the CXL copy, demotion, reclamation). After a critical review (related work checked; one cited
  INFOCOM paper could not be found; NOMAD already proposed keeping slow-tier copies; LMCache 0.5.5 already has a
  DRAM-first DRAM+Device-DAX tier) the user chose: one budget for every DRAM write, DRAM capacity as a separate
  resource, admission-only placement compared against migration before any unified manager is built, topology
  experiment first, capacity-matched LMCache DRAM-first vs CXL-first, a mixed checkpoint + KV workload.
- KV capacity characterization closed (`2026-10-09-kv-capacity-characterization.md`): host KV is capacity-bound;
  DRAM holding other blocks instead of copies adds +3 to +15 points of reuse hits next to the 512 GiB CXL pair.
- Topology experiment opened (`2026-10-09-cxl-topology-interference.md`, tool `benchmarks/memory/topo.c`): the CXL
  part is blocked because the 2026-10-07 reboot made /dev/dax* root-only again. DRAM-only pilot: same CCD −71%,
  paired CCD 5 −21%, any other CCD −10% for 8 DRAM-writing threads beside a CCD-4 reader.
- Admin requests drafted (device permissions + udev rule, memory-controller counters, dax1.0 system-ram feasibility);
  nothing changed on the devices.

### 2026-10-04/06 (session 28) — the advisor's review, the "why", the plan, and the first week of execution
- 2026-09-30/10-04: the user's duplex question (answered: used only implicitly; the drain's yield rule contradicted it),
  the advisor's KV read-path questions (first-hit promotion trace analysis, `2026-09-23-kv-first-hit-promotion.md`),
  the status deck, the English Word pitch (`docs/slides/PITCH_2026-10-04-problem-why-cxl-design.docx`), ChatGPT's
  "evidence-based DRAM admission" reframing (adopted with two additions: a probation tier must be cheap to leave;
  the design's invariant is zero-cost revocation), and the advisor's four points. Decided line: redirect instead of
  throttle; DRAM on evidence; everything revocable.
- Code (all unit tests pass): promotion copies instead of relocating (DRAM shadows on extents, `cxlp_shadow_trim`,
  group eviction, read counts reset on drop, `--shadow-cap-gib`, daemon trims when the pool runs low); k per class
  (`CXLP_OBJ_LATENCY`, `--k-latency`, GPU never while DRAM is not faster); `cxlp_obj_prefetch`; measured CXL capacity
  (10 s max of active epochs) and the loan-must-pay rule (two epochs of slower DRAM chunks hand the loan back); drain
  never yields; `cxlp_put_par` + the plugin's CPU tensors as objects (one drain file per checkpoint, reader pins or
  falls back to the file); producer `split` policy (fixed-ratio baseline).
- Analyses: llama.cpp per-token p99 1.6× during a DRAM-staged burst vs 1.1× CXL; checkpoint frequency at a 3% budget
  every 60 s (stock) vs 27 s (cxlpath) for 16 GiB; KV churn 110–340× a QLC drive's daily write budget; MT² confirms
  "NVM and DRAM share the same memory bus" and throttling as the remedy.
- Running / queued: fixed-split baseline (24 runs), Optane control (Slurm 304547, cascade nodes busy), LMCache env.
- Evening: fixed-split baseline done (24 runs: a fixed 25% / 50% share costs the saturated victims 1.5–3.5× cxlpath's harm
  or under-uses the headroom; `2026-10-06-why-evidence.md` §6). Controller gates (`2026-10-06-controller-v2-gates.md`):
  the per-chunk-rate loan test misfired (withdrew a paying loan beside the reader), replaced by an aggregate rule
  (total rate with the loan must exceed CXL alone) with a 60 s block after a failed trial; reader unchanged (1.06 s,
  6.4%, share 0.30), llama.cpp-32 one short trial per minute (2.23–2.27 s vs 2.16 all-CXL, 0% harm). E2b plugin gate
  passes after fixing a back-pressure deadlock for CPU-only state dicts. Per-tenant probe threads added to the daemon.
  KV replay tool extended (timed replay, forced device, latency/group hints, fast fill). LMCache + vLLM environment:
  `/mnt/local/ghu4/envs/lmcache` (vllm 0.31.0, lmcache 0.5.5, HF_HOME `/mnt/local/ghu4/hf`); smoke test on the 4060 Ti
  stores a 1792-token prefix in LMCache's CPU memory and reuses it (`benchmarks/lmcache/smoke_vllm_lmcache.py`).
- The home directory hit its 40 GB quota three times today (a Rust toolchain pulled by a pip build; old VS Code server
  builds). Everything new (conda env, pip and HF caches) now lives on `/mnt/local/ghu4`; five old VS Code server builds
  were removed; ~2.7 GB free at the end of the day. Raw results in the repo are small, but the quota needs watching.
- Feedback recorded: no invented shorthand as if it were a term; plain sentences a reader can follow without context.

### 2026-09-23 (session 27) — re-run closed, status deck, advisor's read-path questions, first-hit promotion analysis
- Real-data re-run closed (`2026-09-22-three-policies-realdata.md`): numbers within a few points of the zero-line
  campaign except beside llama.cpp (DRAM copies 22 GiB/s instead of 86; all policies ≤ 4% harm; no loan because
  fullness is judged against the constant 43.9 GiB/s while 29 is achievable) and Adam-32 (DRAM harm 93 → 56%).
- Status deck (English, 25 slides, all data figures matplotlib from raw results) published; generators kept in
  `scripts/figs_status_2026-09-22.py`, `scripts/deck_status_2026-09-22.py`.
- User's duplex question: answered that the design uses it only implicitly and that the drain's yield-to-writers rule
  contradicts it; proposed an observation + drain rule change + read-while-write experiments (user to decide).
- Advisor's two questions (hits served from CXL; PolyStore-style split at ingest by predicted reuse): the k = 3 rule
  never promotes KV blocks (0.37–0.64 reads per written block); GPU hits from CXL cost nothing on c28 (12.5 vs 12.3
  GiB/s), up to 2× on a PCIe-5 GPU, CPU 1.7×. Proposed: CXL as probation tier, promote at first hit when DRAM is
  calm, free demotion, no value split at ingest (timing argument), optional session prefetch.
- Trace simulation of first-hit promotion (`scripts/kv_first_hit_promotion.py`): unlimited DRAM 59 / 83 / 77% of hits
  from DRAM at 0.7–1.1 GiB/s of copies; 80 GiB LRU 20 / 65 / 11% (oracle 42 / 76 / 25%); second hit p50 ~130 s after
  the first vs ~100 s residency; 57% of first-hit blocks never re-hit; k = 2 halves copies, LFU worse, 30 s copy delay
  free. Judgement: enough for prompt-dominated workloads, weak for multi-turn chat; predictor ceiling 2×.
- Feedback recorded: never prescribe how the paper must be written; report results, do the work.

### 2026-09-22 (session 26) — three follow-ups to phase 2, the real PyTorch producer, and the zero-line finding
- The user asked for three things: real applications on 32 threads as moderate victims, producer pacing as a
  last resort with a check that the bound holds, and the headline with the real `torch.distributed.checkpoint`
  producer instead of the synthetic copy. Items 1–2 ran overnight (`benchmarks/policy/run_policy.py
  --vthreads/--scale`; pacing = token bucket in the policy page + daemon controller, commit 95e4a54).
- Item 3: `benchmarks/policy/torch_ckpt_producer.py`. Two library facts: stock `async_save` does not copy a
  CPU-resident state dict at all (it hands the live tensors to the serialisation thread), so "today's
  practice" is DCP's own `BlockingAsyncStager` with a cached pinned copy (`tensor.copy_`, 66 GiB/s alone);
  and the plugin needed a parallel NT copy (`cxlp_copy_in_par`, 8 pinned threads) to fill CXL from Python.
  Result beside the saturated Adam step (3 reps, all within 0.3 points): blocked 0.8 vs 1.6 s, 7.2% vs 12%
  during the stage, 0.0% vs 0.4–1.5% tail during the 30 s of serialisation, durable after 19 vs 31–33 s.
- The stage into CXL ran at 29 GiB/s beside llama.cpp-32 where the C producer's all-CXL copy ran at 43.
  Bisected in C (same cpus, same kernel, same destination): only the DATA differed — the C producer's
  snapshot was touched one word per 4 KiB (98% zero lines). Pattern test: zeros, and one-word-per-4 KiB,
  copy at 43.7 → CXL / 83 → DRAM beside llama.cpp; ones, random, one-non-zero-byte-per-line copy at 29 / 19;
  half zero lines land half-way; alone all identical (43.9 / 94.5); reads unaffected; THP irrelevant.
  Beside the 8-thread reader, random data copies at 92.8 = zeros (93.7): the trigger in llama.cpp is open.
- Consequence: the phase-2 numbers (three-policies core figure, four victims, 32-thread campaign, pacing) are
  for zero-line writes and are superseded; `ckpt_producer.c` fills a random snapshot now; the whole protocol
  is re-running into `experimental_results/2026-09-22-three-policies-realdata/`. Invariant appended to
  METHODOLOGY.md. Phase 1 (`writer.h`: 0x5a / memset(1)), the 2026-09-08 cliff (`membench`, non-zero) and the
  PyTorch producer (non-zero tensors; now `torch.rand`) are unaffected.
- Also: the daemon's default guard is now 1.3 (the documented decision; the campaigns had passed it
  explicitly); the DCP plugin's buffer sets are outside the DRAM loan (phase-3 item); llama.cpp's token rate
  drifts with its context over a long run (local reference windows handle it; fixed-length decodes later).
- Docs: `2026-09-22-moderate-pacing-dcp.md` (item 3 valid, items 1–2 superseded), `2026-09-22-zero-line-writes.md`,
  `2026-09-22-three-policies-realdata.md` (active), INDEX, METHODOLOGY, DESIGN §10.11 items 15 and 17.
  Raw item-1–3 files moved from the frozen three-policies directory to `2026-09-22-moderate-pacing-dcp/`
  (they were untracked; the frozen directory is byte-identical to its commit).

### 2026-09-21/22 (session 25) — evaluation phases 1 and 2: budgets, the core figure, the guard
- User decisions: start experiments; OSDI quality regardless of venue; paper in `/home/ghu4/papers/cxlpath`
  (skeleton created after `checkpoint/dpu-relay-paper`, git initialised, not committed); integrate the real
  LMCache after surveying benchmarks (survey saved to `benchmarks/results/2026-09-21-benchmark-survey.md`);
  `cxlpath` merged into `main`; evaluation work on branch `evaluation`.
- Phase 1 (`benchmarks/budget/`): DRAM write budget under a 5/7/10% bound beside a synthetic reader, the CPU
  Adam step, LULESH, GAPBS PageRank and llama.cpp decoding; pure writes vs copies; CXL as control. Under 7%:
  40/28 GiB/s beside the reader, 18–21/9–12 beside the saturated applications — same order as or below the
  CXL pair's 43.9. Copies hurt ~2× more than pure writes; copies to CXL still cost 3–5% (source reads).
  LULESH's first sweep was void (library path; the driver now aborts on a silent victim) and LULESH was
  dropped as a victim (≤ 9% effect, 6% noise). Headline victim: the CPU Adam step (340 GB/s of traffic).
- Phase 2 (`benchmarks/policy/`): a periodic 64 GiB (PageRank: 192 GiB) checkpoint copy beside each victim
  under all-DRAM (NT / plain stores), all-CXL, throttled DRAM and cxlpath, on two axes (victim slowdown
  during the copy; completion). Preparing it fixed three daemon issues (populated DRAM pool — first-touch
  faults had made a spilled chunk 5× slower than a CXL chunk; burst-tail decrements; polluted active
  reference). Results: two regimes as in the status addendum; O2 headline timeline (Adam step 15–17% slower
  for 3.5 s with DRAM staging, 6.5% with CXL staging).
- The guard finding: a probe bound maps to victim slowdown by a victim-dependent factor (0.7× reader, 2×
  Adam, 3× PageRank) and beside a saturated victim the probe's scatter exceeds a 7% signal; the absolute
  probe level (135 ns idle and beside the reader; 200 beside llama/PageRank; 262 beside Adam) separates the
  regimes, so the headroom guard is now 1.3× a 2 s calibration of the unloaded level (the lowest windowed
  reference had denied the loan to the reader once). With it cxlpath lends only where lending is safe.
- Gap recorded (DESIGN §10.11 item 15): cxlpath never paces the producer, so even all-CXL exceeds 7% beside
  read-saturated victims (source reads); producer pacing as a last resort is proposed, not built.
- Lessons: never `pkill -f` with a pattern that matches the shell (twice); a 1 s-step victim needs copy
  windows of several steps; llama.cpp on this machine must be built without AVX512-BF16/VNNI (binutils 2.30).

### 2026-09-21 (session 24) — paper outline reviewed with the user; motivation restructured, gain repositioned
- `cxlpath` branch and the pending docs commit on `main` were pushed to GitHub (no merge, user's wish).
- The user reviewed the paper outline and asked for a considered answer, not agreement. Outcome, now in
  `docs/PAPER.md`: (1) the three observations split the work — moving low-reuse data off DRAM is nearly
  free, keeping it there is harmful, CXL is a safe destination — and the first one no longer concludes
  "DRAM is for reads only", which contradicted the controller that lends DRAM to writers; (2) the
  motivation ends with three simple policies (all-DRAM, all-CXL, rate-limited all-DRAM) on two axes and
  the sentence that is design principle P2; "raw devdax has no allocator" moves to the opening of the
  design section as a challenge; (3) Background keeps hardware facts only, and the Thesis-v2 sentence
  "CXL directions are independent" is dropped as overstated.
- Thinking through the rate-limiting strawman changed the positioning of the gain: once DRAM readers
  must be protected, the usable DRAM write bandwidth is only tens of GiB/s (interpolated from the probe
  calibration and the live controller run), the same order as the CXL pair's 43.9 GiB/s. Hypothesis:
  under an equal protection bound, "CXL by default + DRAM on loan" delivers about twice either simple
  policy. It replaces "only +15% from adding bandwidth" and is the first thing to measure.
- Second round of the review: the user asked for the design section to say HOW only, with "what we
  want to build, for which existing problem" placed before it, and told me to study PolyStore's writing
  technique. Re-read: its introduction goes limitations → insight → challenges → contributions one to
  one; its motivation is pure analysis; goals and principles (requirements) and the overview precede
  the mechanisms; each component subsection is a short lead-in plus mechanism. `docs/PAPER.md` outline
  and `docs/DESIGN.md` §10.1 now follow that; the "challenges" block moved from the design opening to
  the introduction; build-time rationale goes to evaluation ablations or the discussion.
- Next: agree the first experiments (the application for the headline figure of the second observation,
  the three-policies figure, the DRAM write budget under a protection bound).

### 2026-09-19 (session 23) — cxlpath built end to end: feasibility checks, four components, three clients, all-clients run
- The user approved the build plan (campaign file, "Phase 5 v2": checks V → components A–D → clients E →
  system complete F; evaluation excluded), named the system `cxlpath`, asked for one commit per step on
  branch `cxlpath` without Claude attribution, and later said to keep going without asking unless a
  decision is really theirs. The plan table with a results entry per step is the resume point.
- Feasibility checks, all positive: O_DIRECT to NVMe straight from a devdax mapping; scattered 32 MB
  segments stitch into one virtually contiguous buffer that CUDA registers (~20 ms/GiB, 200 GiB fine);
  PyTorch 2.5.1 `async_save` accepts our staging (AsyncStager); the DRAM latency probe tracks a reader's
  slowdown monotonically (1.18× at −13% … 6.5× at −92%); the 3.9 GiB/s GPU→CXL write cap does not react
  to anything visible without root (cause open).
- Component A (segment store on raw devdax): shared CAS segment table, reserve/commit/release on
  per-thread log segments, shared object index that survives a SIGKILLed writer, buffer sets with the
  overwrite rule. 82 ns of library work per 32 MiB write, no system call on the data path.
- Component B (placement): shared policy page + `cxlpathd`; probe costs 1.26% of one core; spill settles
  at 6/16 for a 60 GiB/s demand and halves 16 ms after an injected DRAM aggressor; GPU sources switch
  between the direct (3.9 GiB/s) and staged (12.2 GiB/s) path with DRAM pressure. The live runs forced
  the probe reference to become a median with separate idle/active trackers, a loose idle bound, a
  headroom guard, and capacity-based full/slack rules.
- Component C (read path): pin/unpin, per-extent read counts, break-even k — calibrated k = 3 for a CPU
  consumer on c28 (CXL streaming read 1.77× DRAM), "never" for the GPU (12.45 vs 12.46 GiB/s).
- Component D (drain and recovery): DRAM-free O_DIRECT drain, byte-identical files for awkward sizes,
  back-pressure holds a producer at the NVMe's 0.9 GiB/s, recovery from CXL after a killed writer and
  from NVMe after the store is gone. Checkpoint versions are reclaimed by the runtime.
- Clients: VeloC (patch on the project's copy `~/apps/veloc-src`; drained files byte-identical to stock
  VeloC's; LULESH restarts from CXL), PyTorch DCP plugin (`async_save` → CUDA-registered CXL buffer set,
  reload byte-exact from CXL and from NVMe), KV stand-in driven by the Mooncake traces (971 GiB stored,
  213 GiB read back, 0 verification errors; LMCache itself still ⏳ user).
- The 10-minute all-clients run earned its keep: run 1 exposed drain starvation and (on inspection) a
  silent fall-back of a VeloC client that carried a stale static library; run 2 failed because
  re-written checkpoint versions piled up until the store was full (a key now names ONE object; pins
  name the pinned object); run 3 passed — 3.07 TiB through CXL, 0 errors, no leak.
- Machine facts learned: the Solidigm NVMe sustains 0.90–0.92 GiB/s whatever the parallelism; one core
  pushes 41 GiB/s = 94% of the dax0.0/dax1.0 pair's write capacity; an idle machine's probe scatters
  100–160 ns; writers' own source reads lift the probe ~20%; logs on the NFS home must be buffered.
- Docs: `docs/DESIGN.md` §10 as built (+ §10.11: thirteen differences from the agreed design, with the
  evidence), `docs/PAPER.md` "Facts from building the system", `system/cxlpath/README.md`.
- Next (with the user): review the build; plan the evaluation; names; real LMCache integration or not.

### 2026-09-18 (session 22) — Thesis v3 framing: the horizontal write path (design only, nothing run)
- Read PolyStore (FAST'25) in full and mapped it onto our data. Its three complaints about
  vertical stacking (all writes crowd the fastest device, constant migration, one cache policy
  for all devices) all hold for today's memory tiering, and are worse in memory because DRAM
  reads and writes share one pipe, CXL directions are independent, and promotion is itself a
  DRAM write stream — none of which PolyStore's sum-of-bandwidth model can express.
- The ten reviewer questions were re-answered and then split: MOTIVATION = three observations
  (most written data is never read; heavy DRAM writes slow DRAM readers; the same writes on CXL
  do not), with reviewer question 5 answered by how the second figure is designed (a real
  bandwidth-bound application plus a realistic checkpoint, synthetic 12× beside it as worst
  case). EVALUATION = writer cost, read-back cost, rate-limit baseline, same-card constraint.
  Questions 8 and 10 go to Discussion (user: 10 not needed, 8 not for now).
- User decisions: scope widened to the whole write path ending on NVMe — agreed; PM nodes
  c35/c36 supplementary only — agreed; do NOT run experiments yet, design first.
- Machine facts checked: c28 has DRAM + CXL + NVMe (3.5 TB Solidigm, `/mnt/local`) but no PM;
  PM is on c35/c36 (idle, `-p cascade`), which have no CXL. No machine has both.
- Docs updated in place (no new files): `docs/PAPER.md` Thesis v3 section + PolyStore
  positioning + history; `docs/DESIGN.md` §10 with OPEN points per component + history.
- Housekeeping: /home quota was over the soft limit (40688 MB used, soft 39936, hard 40960);
  a PDF read failed because of it.
- User correction (same day): PolyStore is a paper to LEARN from and borrow ideas from, not a
  comparison method or baseline; PAPER/DESIGN reworded accordingly (saved as a feedback memory).
- /home cleaned by the user: 40.7 GB → 29.6 GB (old VS Code servers, conda package cache,
  gdb-15.2 build tree); quota grace cleared.
- Design discussion (recorded in `docs/DESIGN.md` §10.2, §10.3, §10.3a): reserve→commit write
  primitive, 32–64 MB segments, shared table without a middleman, no compaction; three no-root
  signals with a DRAM latency probe, slow-increase/fast-decrease spill ratio; LLM-scale
  checkpoints (tens of GB) required by the user → virtually contiguous multi-segment buffers;
  PyTorch async checkpoint chosen as the LLM client.
- Feasibility check (the only thing run today, user-approved): the GPU CAN register and write
  directly into devdax CXL with correct data, but at 3.9 GiB/s vs 12.3 GiB/s into pinned DRAM;
  GPU reads from CXL are full speed (12.5). Log `hardware/results/2026-09-18-gpu-devdax-dma.log`.
- End-to-end walkthrough (LLM checkpoint; KV block) forced seven adjustments; `docs/DESIGN.md`
  §10 was then rewritten as one consistent text with all user decisions (32 MB segments, one
  machine-wide bound, initial policy constants, 10-minute read window, selective KV drain,
  emulated multi-GPU stream + CPU-optimizer victim). User: LULESH + VeloC is exploratory only.
- `docs/DESIGN.md` §10 and the paper outline in `docs/PAPER.md` regrouped in PolyStore's shape
  (observations → goals G1–G3 → principles P1–P4 → components A–D → per-component evaluation
  questions); Recovery paragraph added to Component D.
- Trace analysis (no hardware): selective KV drain REFUTED — hit rate falls 35.8→23.7%
  (conversation, 8B) because memory-tier residency (~160 s) is shorter than reuse gaps; removed
  from the design. `docs/experiments/2026-09-18-kv-selective-drain.md`.
- Next: user picks system/component names; then the machine checks listed in DESIGN §10.8 once
  experiments are allowed.

### 2026-09-14 (session 21) — 1b and 3c on healthy DRAM: the write-drain cliff, and CXL as an isolation domain
Crippled-DRAM results (3b, A1.4) discarded per user ruling. **1b** (`2026-09-08-dram-write-drain.md`,
CLOSED): on NPS1 the reader collapse is a cliff at the socket's ~290 GiB/s write ceiling — writers on
≤2 CCDs (≤138 GiB/s NT) cost a CCD0 reader 18–22%, writers on 4 CCDs (273 GiB/s) cost it 12×
(96→8 GiB/s, chase p50 130→610–1359 ns); sum conserved (~290–300, one pipe). Direction decides the
victim: reads 11–12×, plain-store writes 8×, mixed 6–7×, NT writes only −13–23%. Neighbour-CCD
writers −20% (fabric, separate). **Method bug caught and fixed:** the first multi-CCD pass showed
"no collapse" because the 32–96 GiB aggressor pre-touch overlapped the victim window; membench now
prints `measure_start/end_epoch`, `summarize-1b2.py` rejects any victim window not inside a live
aggressor window (3 of 102 rejected). **3c** (`2026-09-14-stencil-3c.md`, CLOSED): idle, all-DRAM
wins (0.261 s/step; `new` on CXL +19% rotate … 2.2× copyback/pingpong). Under 280 GiB/s DRAM NT-write
pressure every DRAM-reading variant is 10× slower regardless of where `new` lives; all-on-CXL is
immune (0.60 = 0.60, 4.3× faster than DRAM in that state); with the aggressor writing to CXL
(pair-saturated 44 GiB/s) the all-DRAM stencil keeps 95–100%. **Thesis consequence:** the write tier
must take the *aggressor's* write streams off DRAM (keeps the controller out of drain mode for
everyone), not the victim's buffers — gate 2b at app scale. Phase 4 to be reframed as co-runner
protection. `pond` takes `--daxA/--daxB`; drivers `stencil-3c*.sh`, `dram-write-drain-1b*.sh`.

### 2026-09-10 (session 20) — Environment changed: DRAM restored, CXL is devdax-only
Reboot 2026-09-09 12:46. DRAM back and better: 141 GiB/s @32T (May 94.6), 309 @128T, 152 ns.
No CXL NUMA node any more — dax0.0/dax1.0 (cards c1+e1) devdax + mmap-able (root:kmem),
dax2.0 (cards 01+02) devdax but root-only 0600 (no udev rule). 1b/3c/4b unblocked; the
tmpfs-on-CXL checkpoint trick and every `--node=1` path are gone — CXL only through devdax
mmap from now on. Log: `hardware/results/2026-09-10-post-reboot-dram-restored.log`.

### 2026-09-09 (session 19) — Phase 4 started: LULESH+VeloC checkpointing on CXL; KV-trace analysis
**A1:** user's VeloC-instrumented LULESH built (`~/apps/lulesh-veloc`, `-DWITH_VELOC`), VeloC rebuilt
(`~/apps/veloc-inst`) with a pread/pwrite fallback for cross-fs drains (stock build lost every
drain, EXDEV). **No-root CXL scratch placement**: tmpfs pages follow the writer's mempolicy →
`LULESH_CKPT_NODE=1` hook. 3 reps at `-s 160`: compute penalty +4.8%→+2.9% (ckpt/10) and
+9.0%→+6.2% (ckpt/5) when scratch moves DRAM→CXL; ckpt call 0.079→0.072 s per 348 MB
(`2026-09-09-lulesh-veloc-ckpt.md`). Small stream — scale-up next. **B1:** Mooncake ×3 +
ShareGPT traces downloaded (gitignored); 58–78% of written KV blocks are never read again,
reuse gaps p50 ≤2 min, 3–8 GiB/s KV writes at 3–7 req/s → anchor B justified
(`2026-09-09-kv-trace-analysis.md`). LULESH 2.0 upstream also built (`~/apps/lulesh`).
Tools: `hardware/scripts/`-style run scripts live with the apps (`run-a1.sh`).

### 2026-09-08 (session 18) — Campaign phases 1a/2/3b executed
**1a** mechanism write-up (`2026-09-08-dram-write-drain.md`). **2** closed: five per-card answers
+ 1/2/4-card scaling (read 24→46→90, NT-write 22→44→85 GiB/s, HB −6%, cross-pair −1%,
duplex +53/+36/+42%, four cards 128 GiB/s) — `2026-09-08-cxl-card-scaling.md`; first run was
killed by a session restart (background jobs die with the process), reps 2–3 re-run. **3a/3b**:
`benchmarks/stencil/pond.c` (rotate/copyback/migrate/pingpong) built and run on crippled
DRAM: every CXL policy ~2× faster than all-DRAM, NT stores −30% — a high-DRAM-pressure
preview, real ranking needs 3c after the BIOS revert (`2026-09-08-stencil-write-tier.md`).
**PolyStore** (FAST'25) read in full; gap list in `Related.md`. PDF kept local. Next: 4a.

### 2026-09-08 (session 17) — Pair A hash confirmed; DRAM interleave regression; campaign plan
**Advisor's request answered experimentally:** `/dev/dax0.0` (Pair A) is interleaved and
HASHED — bit sweep 8–16 and XOR(8,9) all negative, same-class co-run 41.6 = different-
class 41.7; Pair B control finds its stripe at bit 8 (23.9). Per-card stays Pair-B-only.
(`docs/experiments/2026-09-08-paira-interleave-hash.md`, tool `hardware/scripts/bitprobe.sh`.)
**BIOS screenshots decoded:** no CXL-interleave knob exists on this Supermicro/AMI BIOS;
`CXL Memory Attribute=Enabled` is what makes CXL Soft-Reserved/dax (must stay);
`Memory Interleaving=Disabled` + `Chipselect Interleaving=Disabled` are DRAM knobs —
**DRAM regression found:** 25–41 GiB/s @32T (May: 94.6), lowest-ever latency 145.8 ns,
CXL now faster than DRAM (`hardware/results/2026-09-08-dram-interleave-regression.log`).
Recommendation: revert both to Auto; drop the Supermicro ask (two independent pairs +
Pair-B card instrument already cover the thesis). **Campaign plan** (user's 4 phases +
PolyStore FAST'25) recorded as ACTIVE umbrella `docs/experiments/2026-09-08-write-tier-
campaign.md` with TODO statuses; cluster facts: PM only on c35/c36 (Optane, `-p cascade`),
c28 NVMe 3.84 TB at /mnt/local (world-writable). Awaiting: approval to start 1a+2b,
PolyStore PDF, LULESH version, BIOS revert email.

### 2026-09-02 (session 16) — Card-vs-card interference: cards ARE isolation domains
**Experiment** `docs/experiments/2026-09-02-pairb-card-interference.md` (cxlprobe gained
`--class` for chase + `daxstridewr` NT-write mode). Victim on card A (even class) vs 8T
aggressors on card B (odd) or card A, separate CCDs, 3 reps. **Cross-card: latency
victim unchanged (225→225 ns mean, p50 219 under reads AND NT writes); bandwidth victim
−6% under reads, 0% under writes. Same-card: latency 1.93× (reads) / 2.06× (writes);
bandwidth −51% (read+read fair share) but only −5% under writes (card-level duplex ≈
+55% joint).** Symmetric arm (victim on B, writes on A): +2%. Cross-card asymmetry: readers
protected, NT writers yield ~30% (overlap-estimated). **Meaning:** "writer gets its own
card" gives Gate-2b-grade isolation inside the CXL tier; planner can treat cards as
independent budgets (read ~23.9, write ~21.9, joint ~37; co-located-write latency ×2).
First real-hardware CXL-to-CXL card-granularity interference measurement.

### 2026-09-01 (session 15) — dax2.0 is ours; Pair B card map PROVEN (plain 256 B stripe)
**Machine:** admin switched dax2.0 to devdax (17:45, no reboot) and granted group kmem
(0660, ghu4 in kmem ~20:00); node 1 = Pair A only (508 GiB). open+mmap verified across
the device (devdax enforces bounds at fault time — never touch past 512 GiB).
**Experiment** `docs/experiments/2026-09-01-pairb-address-map.md`: P1 halves identical
(46.0 GiB/s, 219 ns) → not concatenated; P2 every co-run 24+24 → one shared pair;
P3 256-B classes: each alone 23.9 (one card), even+odd 44.3, even+even 24.3 → **plain
modulo stripe `card=(off>>8)&1`**; P3b parity uniform across the whole window. My
Aug-28 "linear layout" hypothesis refuted; E1's Pair-A hash stands (root-level XOR),
Pair B's host-bridge-level interleave uses plain bits. **First single-CZ120 number:
23.9 GiB/s read @8T per card.** Tools: `cxlprobe --mode=daxstride` (new),
`hardware/scripts/pairb-address-map.sh`. **Consequence:** per-card experiments
(card-vs-card interference, per-card write streams) are possible NOW via dax offsets,
no further admin change. Label assignment (which class = 01:00.0 vs 02:00.0) still an
assumption from decoder3.0 target order.

### 2026-08-25 (session 14) — Direction pivot: write-preferred CXL + gate experiments
**Context:** advisor lukewarm on the interleaving/per-card ask (system changes are
troublesome); interested in read/write path separation on CXL. Discussed and
sharpened his idea: NOT "CXL write BW > read BW" (false: 27.9 vs 45.6) but three
real mechanisms — duplex link (separate wires per direction), the 2× DRAM write
tax (RFO+writeback on a shared bus; measured exact: 34.3 = 68.8/2), and
asynchronous stores hiding CXL latency. Quick-look W0 numbers: CXL plain-write
27.9 GiB/s = +22% over the shared-pipe prediction (partial duplex, first
evidence). **Decisions:** (1) pivot the paper thesis to direction-aware placement
(`docs/PAPER.md` Thesis v2); (2) LLM support = reserved interfaces only
(KV-evict/prefix-insert/optimizer-RMW classes, `obj_stage_out/in` staging API,
promote-on-hit hook) — implementation later, trap documented (active-decode KV on
CXL = read-latency loss); (3) two GATES before any system code: duplex matrix +
cross-interference asymmetry (full specs + pass/fail in `docs/EXPERIMENT_PLAN.md`);
(4) per-card direction parked. **Docs reorganized (user-approved scheme):**
`docs/experiments/` with dated per-experiment files + INDEX + METHODOLOGY;
`DESIGN.md` + `PAPER.md` as living docs with append-only Change-history
sections; guides/ + slides/ folders; RESULTS.md / EXPERIMENT_PLAN.md /
DESIGN_OBJPLACE.md dissolved into the new files (originals preserved in
`docs/archive/`); rules in `docs/README.md`; CLAUDE.md policy updated. User
feedback captured: present multi-step plans and get explicit agreement BEFORE
executing (memory: feedback_confirm_before_do). Gate specs + eventual results:
`docs/experiments/2026-08-25-direction-gates.md`. **Later same day (user-approved):**
data migrated to `experimental_results/<md-name>/` layout (user's convention;
user renamed old `experiments/` → `experimental_results/` themselves); repo pushed
to private GitHub `Garson-hu/CXL` (main, SSH); membench extended (NT-write kernel,
`duplex` mode, cross-node write aggressors — ~130 lines) and BOTH GATES RUN AND
PASSED (results above + in the gates file). Gate-2 v1 same-CCD confound caught and
fixed with the CCD-separated re-run (both datasets kept). Tools:
`hardware/scripts/duplex-gates.sh` + `duplex-gate2b.sh`.

### 2026-08-14 (session 13) — Post-reboot: NPS4 discovered; E4 hypothesis CONFIRMED
**What happened:** admin BIOS visit + reboot (~08-12) after the Thursday meeting.
Result is NPS1→**NPS4** (4 CPU quadrants + CXL = node 4), NOT CXL de-interleave
(decoders unchanged: 3 windows, all ways=2 gran=256). His "3 regions vs 4 devices"
email observation = firmware window carving (Pair A in 2 windows + Pair B in 1),
not a kernel flaw. **Gold:** NPS4 exposes per-card quadrant affinity — mem0→n3,
mem1→n0 (Pair A spans two quadrants), mem2+mem3→n1 (Pair B one quadrant) —
independently confirming the E4 "farther but wider" topology hypothesis. Speeds
re-verified: CXL 287 ns / 45.4 GiB/s @8T (unchanged); DRAM node 0 improved to
174.8 ns (quadrant-local). famfs FUSE restarted, still holds dax2.0.
**Files:** `hardware/results/2026-08-14-post-reboot-nps4-check.log`; memory
project_hardware updated.

### 2026-08-11..12 (session 12) — Four pre-BIOS experiments + research-update deck
**Experiments** (log: `hardware/results/2026-08-11-prelim-fourexp.log`; new tool
`benchmarks/memory/cxlprobe.c`): **E1** stripe-trick NEGATIVE — offset classes
exceed one card's ceiling (37.8 > ~24 GiB/s); AMD hashes way-selection above page
bits; software cannot split a firmware pair (THP also never engaged on CXL node:
AnonHugePages=0, MADV_COLLAPSE rc=-1). **E2** cross-pair BLOCKED — famfs FUSE
holds dax2.0 exclusively (SIGBUS on first read); needs a world-readable famfs file
or 1-hour unmount. **E3** tails benign — p99.9 < 1 µs at all loads (no
Melody-style spikes on CZ120); real signal = CXL median +15% / p90 +40–54% under
own load while DRAM flat ⇒ congestion, not spikes, is the design signal. **E4**
twins — Pair A 47.7 GiB/s @32T vs Pair B 35.5 flat (May) = +34% ceiling gap;
DRAM drift control 4–11%; hypothesis: Pair A spans two fabric quadrants
(confirmed next session). **Deliverable:** 12-slide research-update deck
`docs/SLIDES_2026-08-12-cxl-research-update.pptx` (landscape → paper pitch →
May+August evidence → asks); May slide framed as Idea 1 prototype.

### 2026-07-06..08 (session 11) — Deep literature review (97 papers) + research directions
**What we did:** Ran a 7-stage multi-agent deep literature review of CXL systems research
2022–2026 (10 discovery sweeps incl. 2026 accepted lists + adversarial multi-device hunt →
97 per-paper deep-reads against primary sources with verbatim evidence quotes → 39
skeptical re-verifications → map-audit intuition checks). Survived 5 session-limit
interruptions via journal-harvest + continuation-script relaunches (nothing re-run).
Then synthesized research directions in-context (user asked to stop agents to save tokens).
**Key verified findings:** (1) Of 97 records: 26 single-device, 10 multi-device-pooled
(always fused), only 7 multi-device-independent — none manages commodity ASIC expanders
independently on one host. (2) CXL-to-CXL cross-device interference never measured
(CXL-Interplay DAC'25 = 1 device/testbed, says so verbatim; Melody ASPLOS'25 = 4 devices
on different hosts, punts mitigation). (3) All multi-tenant CXL QoS regulates above one
fused pool (Memstrata, MTTM, Equilibria, Mercury). (4) Near-miss ring to cite: CSFQ
transport (NSDI'26), Weisgut (VLDB'25), CXL-CCL, Liaw&Chen. (5) Corrections from
verification: ArtMem = Optane not CXL; Beluga = 32 devices; SupMario ≥5 devices,
arXiv-only (ASPLOS'25 version = Melody); ATC discontinued after '25.
**Decisions:** Direction confirmed — device-granular CXL management as umbrella (Idea 1),
device-isolation multi-tenancy (Idea 2) and adaptive interleaving (Idea 3) as
emphasis/mechanism; famfs/FAST as pivot if the decoder gate fails. Week-2 interference
data picks Idea 1 vs Idea 2 emphasis. Avoid: object-tiering headline (SoarAlto/OBASE/
Clove), KV substrates, switch pools, kernel patches, pure characterization.
**Files added/changed:** `DEEP_RESEARCH_2026-07-08-cxl-landscape.html` (Part I map +
Part II directions), `benchmarks/results/2026-07-08-cxl-lit-review.json`, WORKLOG,
memory (project_direction, project_hardware, project_litreview, feedback_token_budget,
MEMORY.md).
**Next steps:** (1) Admin ticket (de-interleave dax2.0 + sysctl access) — critical path;
(2) 8-week plan Weeks 1–2: per-device baselines, interference matrix, tail sweeps;
(3) decision gate per plan.

### 2026-06-12 (session 9) — Deep-research scan for the next direction
**What we did:** Ran a multi-agent deep-research pass (103 agents, claims verified
3-vote against primary PDFs) on "what real-CXL direction could make a FAST/OSDI
paper from c28." Full report: `benchmarks/results/2026-06-12-deep-research-directions.json`.
**Ranked findings:**
1. **Device-granular CXL placement/QoS across 4 devices (top, verifiably open).**
   CXL-Interplay (DAC'25) — "first real-HW CXL interference study" — has only ONE
   device per testbed and never measures CXL-to-CXL; Micron/Intel's 8-device study
   fuses all devices into one NUMA node; Melody (ASPLOS'25) documents unstable µs
   tail latencies on real CXL and explicitly punts mitigation. Treating each device
   as a schedulable resource (cross-device interference + tail-aware placement)
   extends ObjPlace directly. Needs ≥2 system-ram CXL nodes (free a FAMFS device).
2. **FAST angle: three-tier DRAM/CXL/SSD storage/buffer-pool on real ASIC CXL +
   famfs.** Only prior real-HW validation is a workshop paper on an FPGA prototype
   whose authors leave exactly our questions open; famfs itself disclaims storage
   semantics ("not a data storage tool") and is unmerged/in transition — building
   storage semantics above it is unclaimed. Caveat: CZ120 is volatile (no
   persistence story; scope crash-consistency out or log to SSD).
3. **R/W-mix-aware dynamic DRAM:CXL bandwidth steering.** DRAM loses ~20% at 1R:1W
   while CXL *improves* (bidirectional PCIe); optimal split is workload-dependent
   and static kernel interleave can't track it. Best as a mechanism inside idea 1.
4. **AVOID: GPF/crash-consistency** — real spec gap but CZ120s are volatile; cannot
   exercise end-to-end on our hardware.
**Leverage (verified):** NUMA emulation is documented as misleading (MICRO'23: up to
26% latency / 3–66% BW error; Melody: emulation misses µs tails entirely) and
top-venue CXL papers are dominated by hyperscaler-affiliated groups → our 4 real
ASIC devices + famfs deployment is a rare position. **Closest competitor:** MTTM
(EuroSys'26) partitions the *DRAM* tier for multi-tenant bandwidth — adjacent, not
occupying device-side CXL contention. Must cite.
**Decision (2026-06-12): Idea 1 agreed**, combined with the original kickoff idea
(LLM cold-data offload + promotion/demotion) — the original idea returns as (a) the
LLM-era workload/evaluation domain and (b) a *device-aware, sensitivity-driven*
object promotion/demotion mechanism (not page-hotness migration, which is the
crowded lane). Combined thesis: *sensitivity- and device-aware placement AND
movement of memory objects across DRAM and multiple real CXL devices for LLM-era
workloads.* Staged plan + full findings written to `DEEP_RESEARCH_2026-06-12.html`
(repo root). Go/no-go = stage-2 cross-device interference characterization (needs
admin to free one FAMFS device; keep one on famfs as Idea-2 fallback).
**Process rule (2026-06-12):** max 10 concurrent subagents, strict, all
conversations (saved to memory).

### 2026-06-12 (session 10) — 4-vs-2 device decision + critical de-interleave finding
**Question:** for a strong first FAST/ObjPlace paper, take all 4 CXL devices (push the
DeepTier ASPLOS project off its 2 famfs devices) or stay on 2? Ran a bounded workflow
(10 agents, ≤4 concurrent; verified vs primary PDFs). Raw:
`benchmarks/results/2026-06-12-four-vs-two-devices-analysis.json`.
**Verdict (unanimous across 3 judge lenses + internal delta): 4 devices helps only
MODESTLY and QUANTITATIVELY — do NOT push DeepTier.** The first-of-kind headline
("first real-HW CXL-to-CXL cross-device interference + per-device QoS") is fully
established at **2 de-interleaved NUMA nodes**; the decisive never-published experiment
(victim on CXL-node-A degrading under aggressor on disjoint-core CXL-node-B) needs
exactly two. 4 devices only adds saturation *curves*, a same-vendor device-population
heterogeneity figure, and a bin-packing scheduler search space — strengthening, not
new claim classes — and risks the "gains from more hardware, not mechanism" critique.
Competitive proof count is not the currency: Micron used 8 devices (fused) and bought
zero interference novelty; Weisgut (VLDB'25) used 4 separate nodes but placement-only.
**THE REAL GATE (bigger than 2-vs-4): can c28 even expose per-device CXL NUMA nodes?**
Live sysfs (verified this session): the 512 GiB system-ram region (dax2.0) is produced
by root `decoder0.2` with **interleave_ways=2** (2 devices fused); host-bridge
`decoder3.0` reads **locked=1**; root decoders 0.0/0.1/0.2 read locked=0. So per-device
granularity needs root-level CXL **region teardown + recreate at interleave_ways=1** —
unverified on Zen5/Turin, and we lack passwordless sudo. This gate is IDENTICAL effort/
risk for the 2-node and 4-node paths, so 4 buys zero de-risking. **It blocks the entire
device-granular direction (Idea 1) at any device count until resolved.**
**Decision:** (1) FIRST verify de-interleave feasibility on the 2 devices we already
control (dax2.0) — the true go/no-go — via an admin request; (2) if it works,
de-interleave dax2.0 ONLY, keep DeepTier on dax0.0/dax1.0 famfs, ship the cross-device
interference + per-device-placement contribution at 2 nodes with a REAL co-located
tenant + established baselines (TPP/MEMTIS/Colloid/SoarAlto — the paper's actual #1
weakness, orthogonal to device count); (3) hold 4-device scaling as an optional
post-DeepTier camera-ready robustness pass. Earlier (session 9) "4 devices is the
strength" framing is now qualified: the strength is ≥2 *de-interleaved* devices, not raw count.

### 2026-05-20 (session 8) — Doc consolidation; WORKLOG is now the tracker
**What we did:** Collapsed `docs/` from 21 scattered files to **5 core docs** +
`docs/archive/`. Created `docs/RESULTS.md` (all results in one place), `docs/PAPER.md`
(org + claims + positioning), `docs/EXPERIMENT_PLAN.md` (done + next + reproduce);
folded the API reference into `docs/DESIGN_OBJPLACE.md`; kept
`docs/STUDY_GUIDE_OBJPLACE.md`. Archived the per-phase result/plan/direction notes
(SMOKE/PHASE1-3/2.1/2.2/INTEGRATION/EVAL_*/FINAL_STATUS/DIRECTION_DECISION/
NOVELTY_GAP/RELATED_WORK/MEASUREMENT_PLAN/PLAN_LLM_ERA/EVALUATION_PLAN/API) into
`docs/archive/` (raw CSVs remain under `benchmarks/results/`). Rewrote this Current
Status to be the single up-to-date status, with a Doc Map.
**Decisions:** WORKLOG is the primary progress tracker from now on; `docs/` keeps
only paper-org / claims / plan / results / design; no new scattered docs (summarize
into WORKLOG, archive temporaries).
**Files changed:** `docs/{RESULTS,PAPER,EXPERIMENT_PLAN}.md` (new),
`docs/DESIGN_OBJPLACE.md` (API folded in), `docs/archive/*` (19 files moved),
`WORKLOG.md`, `CLAUDE.md` (docs policy).
**Next:** real two-tenant workload + INTERLEAVE planner candidate (not started).

### 2026-05-20 (session 7) — Block-2 evaluation (pressure / budget / GNN / overhead)
Pressure-aware (+67%→+116% vs hotness-only), DRAM-budget +18–22% at 40–60%, GNN
skewed +8.3% / uniform −11.6% (no INTERLEAVE candidate), overhead ~0%. Fixed GNN
gather to be memory-bound (memcpy). Results in `docs/RESULTS.md` §5.

### 2026-05-20 (session 6) — ObjPlace runtime + Block-1 evaluation
Refactored `obj_alloc_hint` prototype into the **ObjPlace** object-placement runtime
(registry + benefit-per-byte planner + CXL-pressure model). All 5 eval targets met
(`docs/RESULTS.md` §4). Integrated into embbench/bwbench/gnnbench/sensbench.

### 2026-05-20 (session 5) — Direction locked + minimal prototype
Confirmation runs (median-5) held: CXL bandwidth victim 2.01×/2.13×, embedding skew
~15%. Locked direction; built minimal `obj_alloc_hint` prototype.

### 2026-05-19 (session 4) — Phase 2.1/2.2 + integration
Disjoint-core retest overturned Phase 2 (CPU-contention artifact). Bandwidth-bound
multi-thread victim 2.0–2.13× on CXL; latency-bound ≤1.23×; DRAM ~1.0%. See
`docs/RESULTS.md` §2.

### 2026-05-19 (session 3) — Deep-research pass, benchmark harness, first real CXL numbers
**What we did:**
- Wrote four research docs in `docs/`:
  - `RELATED_WORK_CXL_LLM.md` — survey of CXL tiering, CXL+LLM, embedding/GNN-on-heterogeneous-memory, and CXL QoS prior art with per-paper analysis.
  - `NOVELTY_GAP_TABLE.md` — 17-row comparison table and answers to the seven framing questions.
  - `DIRECTION_DECISION.md` — five candidate sub-directions (A LLM KV, B umbrella interference+placement, C embedding/GNN, D multi-CXL aggregation, E pivot), each with thesis, mechanism, experiments, hardware feasibility, four risk vectors, and an explicit go/no-go signal tied to Phase 1–2 measurements.
  - `PLAN_LLM_ERA_CXL.md` — 1–2 week plan with status, hypotheses, deep-research tasks, measurement plan summary, prototype plan, risks, and go/no-go matrix.
  - `MEASUREMENT_PLAN.md` — three-phase measurement plan (baseline / interference matrix / workload smoke).
- Built `benchmarks/memory/membench.c` (custom C, libnuma-based, no MLC required). Modes: latency, stream-read, stream-write, random-read, mixed, loaded-latency. CSV output. Refuses to allocate on a node with 0 MB online and prints the exact unblock command.
- Built `benchmarks/kvcache/kvbench.py` (KV-cache-shape memory benchmark; configurable layers/heads/seq/batch; placement modes dram/cxl/interleave/split).
- Built `benchmarks/embedding/embbench.py` (row-gather; uniform + Zipfian; placement modes dram/cxl/interleave/skew).
- Added five helper scripts under `scripts/`: `check-cxl-memory.sh`, `run-dram-cxl-baseline.sh`, `run-interference-matrix.sh`, `run-kv-cache-bench.sh`, `run-embedding-gather-bench.sh`.
- Discovered between sessions: **admin onlined `dax2.0` → NUMA node 1 has 522 GB CXL online.** Ran first real DRAM-vs-CXL smoke. Results in `benchmarks/results/<TS>-smoke/` and summarized in `docs/SMOKE_RESULTS_2026-05-19.md`.

**Decisions:**
- Direction remains **not locked**. Hypothesis stage. Lock only after Phase 1 + Phase 2 produce go/no-go signals on (a) CXL latency budget, (b) per-device bandwidth saturation, (c) asymmetric multi-process interference.
- LLM treated as motivation + one workload class — not the only target. Embedding and GNN gather are first-class evaluation workloads so the paper survives the small (4060 Ti 8 GB) local GPU.
- Avoid: MoE-on-CXL (closed), switch-pool (no switch), basic Memstrata port (incremental).

**Measurements (smoke, single thread, 512 MiB / thread, 3 s):**

| Metric | DRAM | CXL (dax2.0) | CXL/DRAM |
|---|---:|---:|---:|
| Pointer-chase latency | 184.9 ns | 276.5 ns | **1.50×** |
| Sequential read BW | 32.2 GiB/s | 19.5 GiB/s | 0.60× |
| Sequential write BW | 31.1 GiB/s | 18.5 GiB/s | 0.59× |
| Random read BW | 2.30 GiB/s | 1.58 GiB/s | 0.69× |
| Stream-read 4-thread BW | 69.2 GiB/s | **35.6 GiB/s** (saturated) | 0.51× |
| Stream-read 32-thread BW | 94.6 GiB/s | 35.5 GiB/s (still flat) | 0.37× |

Hypothesis 1 (CXL latency closer to DRAM than 2×) **supported**.
Hypothesis 2 (per-device BW saturates early, BW pressure dominates) **strongly supported** — saturation by 4 threads at ~99% of theoretical 36 GB/s.

**Files added/changed:**
- `docs/RELATED_WORK_CXL_LLM.md` (new)
- `docs/NOVELTY_GAP_TABLE.md` (new)
- `docs/DIRECTION_DECISION.md` (new)
- `docs/PLAN_LLM_ERA_CXL.md` (new)
- `docs/MEASUREMENT_PLAN.md` (new)
- `docs/SMOKE_RESULTS_2026-05-19.md` (new)
- `benchmarks/memory/{membench.c,Makefile,README.md}` (new)
- `benchmarks/kvcache/kvbench.py` (new)
- `benchmarks/embedding/embbench.py` (new)
- `scripts/{check-cxl-memory.sh,run-dram-cxl-baseline.sh,run-interference-matrix.sh,run-kv-cache-bench.sh,run-embedding-gather-bench.sh}` (new)
- `benchmarks/results/2026-05-19-<TS>-smoke/{smoke.csv,scaling.csv,notes.log}` (new)
- `WORKLOG.md` (this file)

**Next steps:**
- Run full Phase 1: `./scripts/run-dram-cxl-baseline.sh` (~15 min) — produces latency, BW, scaling, loaded-latency CSVs in a timestamped dir.
- Run Phase 2: `./scripts/run-interference-matrix.sh` — produces interference matrices on DRAM and CXL.
- Run Phase 3 smoke: `./scripts/run-kv-cache-bench.sh` and `./scripts/run-embedding-gather-bench.sh`.
- Decide direction using the matrix in `docs/PLAN_LLM_ERA_CXL.md` § "Go / no-go criteria".
- Open ask to admin if Phase 2 shows interesting interference: free `dax0.0` or `dax1.0` (whichever is least load-bearing) to enable multi-CZ120 NUMA experiments (Direction D).

### 2026-04-18 (session 2) — Hardware inspection on c28; MLC blocked
**What we did:**
- Discovered Claude Code's environment *is* c28 (`hostname=c28`) — no ssh/salloc needed. Corrected CLAUDE.md accordingly.
- Ran `hardware/scripts/inspect-system.sh` and appended cxl/daxctl/tools/sudo probes to the log.
- Attempted to run MLC; found two blockers: MLC not installed, and CXL not online as a NUMA node.
- Added `hardware/scripts/setup-mlc.sh` (checks common install paths, prints Intel fetch instructions).

**Decisions:**
- Hold MLC sweep until CXL is brought online as system-ram and MLC is fetched. No attempt to brute-force via custom user-space benchmark (dax chardevs are `root:600`, user has no passwordless sudo).
- GPU on c28 is too small (4060 Ti 8 GB) for anything beyond small quantized 7B — plan to use c29 (H100) or c30–31 (A6000) for model-scale experiments once direction is locked.

**Measurements (inspection only):**

| Thing | Observed |
|---|---|
| CPU | EPYC 9745 Turin, 256 logical / 128 physical, single NUMA node |
| DRAM | 773 GB, one node |
| GPU | 1× RTX 4060 Ti 8 GB (driver 580.65.06, CUDA 13.0) |
| CXL devices (lspci) | 4× Micron 6400 @ 01:00.0, 02:00.0, c1:00.0, e1:00.0 |
| CXL bus endpoints (`cxl list`) | 2 committed — mem1 (port3/endpoint5), mem3 (port3/endpoint6) |
| CXL sysfs | mem0–mem3 all present, each `ram_size=0x4000000000` (256 GB) |
| CXL exposed as | devdax only — `dax0.0` 242 GiB, `dax1.0` 269 GiB, `dax2.0` 512 GiB, all target_node 1 |
| NUMA nodes | only node 0 — CXL not online |
| Kernel | 6.14.11+ with `memhp_default_state=offline` |
| Tools installed | `cxl`, `daxctl`, `ndctl`, gcc 12.4.0 |
| MLC | missing |
| sudo | needs password |

**Files added/changed:**
- `hardware/results/2026-04-18-inspect.log` — raw inspection output (never edit)
- `hardware/scripts/setup-mlc.sh` — MLC presence check / install hints
- `CLAUDE.md` — corrected access section (dev env = c28), added CXL-bring-online + MLC-fetch sections
- Memory: `project_hardware.md` rewritten with measured state (GPU, CXL offline, sudo, MLC)

**Next steps:**
- Open a ticket with ARC admins (or request sudo for the session) to run:
  ```
  sudo daxctl reconfigure-device --mode=system-ram --no-online dax0.0 dax1.0 dax2.0
  sudo daxctl online-memory dax0.0 dax1.0 dax2.0
  ```
  Confirm `numactl --hardware` shows new node(s) for CXL.
- Fetch Intel MLC (EULA form → tar → `~/mlc/Linux`, add to PATH).
- Re-run `hardware/scripts/mlc-sweep.sh <DRAM_NODE> <CXL_NODE(s)>`.
- Separately, decide whether we want all 4 CZ120 devices exposed (need to commit mem0 + mem2 as endpoints first) or whether the current 3-region devdax layout is acceptable for first experiments.

### 2026-04-18 (session 1) — Project scaffolding + doc/memory scheme
**What we did:**
- Created initial directory scaffold (notes/, hardware/, experiments/, workloads/, papers/, writing/, scripts/) with planning docs covering field landscape, options A–E, Week 1 plan, reading list, decisions log, open questions.
- User trimmed the scaffold to a lean layout: removed `notes/`, `papers/`, `writing/`; added `system/` for the future built system.
- Updated `README.md` to match the lean layout.
- Adopted the three-layer doc/memory scheme (per-project memory, WORKLOG.md, CLAUDE.md) and created `WORKLOG.md`, `CLAUDE.md`, and `.claude/skills/update-mem/SKILL.md`.
- User initialized the repo as git (`.git`, `.gitignore`).

**Decisions:**
- Direction lock deferred until Week 1 hardware data.
- Planning context lives in conversation + per-project memory, not in the repo.
- System paper target, not characterization paper.
- Doc/memory layers: CLAUDE.md for codebase rules, WORKLOG.md for session narrative, per-project memory for indexed facts across sessions.

**Measurements:** None — hardware not yet accessed.

**Files added/changed:**
- `README.md`
- `hardware/scripts/{inspect-system.sh,mlc-sweep.sh,llm-baselines.sh}`
- `WORKLOG.md` (this file)
- `CLAUDE.md`
- `.claude/skills/update-mem/SKILL.md`
- `.gitignore` (user-added)
- Memory: `user_role.md`, `project_hardware.md`, `project_direction.md`, `project_layout.md`, `reference_arc_cluster.md`, `MEMORY.md`

**Next steps:**
- Run Week 1 hardware verification on c28: `ssh arc.csc.ncsu.edu`, `salloc -p turin128 -w c28`, then `hardware/scripts/inspect-system.sh` → `mlc-sweep.sh` → `llm-baselines.sh`. Dump output into `hardware/results/` as dated files.
- Confirm GPU presence on c28.
- Compare measured CXL latency against Micron's "remote socket DRAM" claim and Memstrata's 2× assumption.
