# 2026-10-21 — Joint benefit analysis: reuse value × DRAM/CXL movement cost (Phase 3, RQ2 hypothesis validation)

**STATUS: CLOSED (2026-10-21).** **Verdict: the core hypothesis (H2, value × cost in one decision) is not supported
at any single-host KV-cache scale the measurements cover.** The RQ1 admission alone removes 88–91% of the host writes
and all of their tail: after it, the write stream never exceeds 25 GB/s (CXL path 46 GB/s measured), the DRAM part
stays at 0.2–2.1 GB/s (safe budget 6–8 GB/s), the CXL backlog never exceeds 1 GB and the estimated neighbour p99 is
0.1–1.9% — at 8B and 70B blocks, 1× to 8× trace speed, beside the most sensitive neighbour measured. A joint
value-and-cost policy with the same information and resources equals the independent combination (reuse-aware
admission, then budget-gated placement) to −0.5 … +0.7 points of usable hit share on all 24 real-trace
configurations, under checkpoint co-writers (+0.1 … +1.2), neighbour phases (+0.2 … +0.3), half capacity (−0.3 …
−0.9); the value oracle gains ≤ 0.02 from removing the costs; and under CONSTRUCTED stress where the filtered
stream exceeds the path (CXL cut to 6 GB/s) a value-blind congestion drop beats the value-ordered one. What the
evidence supports is smaller and different from the hypothesis: value-aware admission makes DRAM/CXL KV caching
interference-free and makes cost-aware placement unnecessary at these scales (an RQ1 + RQ3 result, not RQ2).
Recommendation: do not build the minimal unified manager on this hypothesis; see Task H. Phase 3 of the roadmap (Oracle → Online predictability → **Joint benefit** → Minimal
system). Question: given the same online reuse information (RQ1) and the same DRAM/CXL resources and interference
constraints (RQ3 measurements), does a joint value-and-cost decision give meaningful benefit over a strong independent
combination of reuse-aware admission and cost-aware placement? Evidence types: **SIM** (a new trace-driven joint
simulator whose resource model is built from the HW / EMU measurements listed below — every cost number is an
interpolation of a measured point and is labelled as such), **ORACLE** (future reuse, same resource constraints),
**HW / EMU** (re-used, cited). No new hardware measurement unless a gap is found; no production change.
Raw: `experimental_results/2026-10-21-joint-benefit-analysis/`. Code: `scripts/kv_joint_sim.py`, `kv_joint_tables.py`,
`kv_joint_figs.py`.

## Model (written before the implementation, as the brief requires)
**Data flow.** The vLLM/LMCache server produces KV blocks (Mooncake conversation / tool-agent traces; 512-token blocks;
8B = 67.1 MB, 70B = 167.8 MB — the block sizes of the host-memory-traffic emulation of 2026-10-10/12). A block that
is not in the host cache at its lookup is a miss (recomputed; counted in tokens and in the TTFT model of 2026-10-18);
after the request it is offered to the host cache (admission). An admitted block is written to DRAM or to CXL (single
copy; no duplicate copies anywhere); it becomes a hit only after its store has completed (a block still being written
is a *pending miss*, as in kvemu2). Eviction is per-tier LRU or SLRU; no migration by default (2026-10-11/12: migration
never beat admission); movement, where a policy uses it, is a CXL store plus a DRAM read, and counted.
**Time.** Trace time runs at 1× / 4× / 8× speed (time compression, as the emulation: the reuse structure in requests is
unchanged, residence in seconds and write rates in bytes/s scale with the speed; "4×" is a multi-server aggregate, not
one GPU). RQ1 statistics (gaps, residence) run in trace time; bandwidth, queues and interference in wall time.
**Capacity.** DRAM 64 GiB + CXL 136 GiB = 200 GiB effective (the charter's standard; 1,024 + 2,176 blocks at 8B,
409 + 870 at 70B), single copy; both tiers fully usable; the same for every policy; warm-up on the first half of the
requests (both tiers filled by the policy itself), scoring on the second half.
**Write paths (measured).** CXL: the two cards take ~46 GB/s of stores (46.3–46.8 GB/s achieved, 2026-10-10/11; 43.9
GiB/s pair capacity) — modelled as one FIFO server of 46 GB/s; a store completes when its bytes are drained; the
backlog (bytes queued) and the lateness (completion − offer) are reported. DRAM: stores drain at the emulator's ~150
GB/s per-20-ms ceiling (never binding here); every DRAM write costs interference (below). The DRAM write budget is the
token bucket of 2026-10-12 (refill B GB/s, depth d blocks; a block goes to DRAM only if the bucket holds a block of
credit; unused credit beyond the depth is lost). Checkpoint stream (optional): S GiB every T s offered to the same
CXL path (uncoordinated FIFO, KV-priority, or the joint rule); it must complete (never bypassed); its completion time
is the durability metric.
**Interference (measured, interpolated).** The neighbour's p99 slowdown is a function of the mean DRAM write rate over
the scored window, from the 2026-10-12 calibration beside the 80-thread Adam step: hash-placed ("bursty") writes
1.3 / 2.8 / 4.4 / 6.1 / 9.3 / 12.3 / 15.7 / 18.9 / 23.7 GB/s → +1.2 / 2.6 / 4.1 / 5.6 / 7.7 / 9.3 / 13.5 / 14.7 / 21.7%
(pooled from the 8B 4×, 8B 8× and 70B 4× split sweeps; monotone piecewise-linear interpolation; beyond 24 GB/s linear
extrapolation, flagged); budget-smoothed writes 4.6 / 7.5 / 8.9 / 9.8 / 11.2 / 13.1 GB/s → +3.1 / 5.4 / 6.8 / 7.3 / 7.7 /
9.1%. Beside the 8-thread DRAM reader: +0.7–8.3% up to 24 GB/s (≈ +1 + 0.25 × GB/s). CXL writes cost DRAM neighbours
≤ 2% (2026-10-10) → modelled as 0; CXL writes cost a CPU reader of CXL 36–40% of its bandwidth and 2.4× on a dependent
read (2026-10-09/12) → reported as the CXL-busy share, not as a KV cost (the GPU's KV loads are link-bound and equal
from both tiers, 2026-10-07: A3). SLO: p99 ≤ 7% over the scored window (the charter's).
**Value information (RQ1, online only).** Per block at admission: `seen_before`, `touches`, `last_gap`, the cache's
`residence_window` (EWMA of dead-eviction ages), `regime` (first-touch-horizon rule), and the class rate
P̂(re-lookup within residence | touches, gap bucket) from policy-independent labels (the 2026-10-21 tables). No policy
uses the future except the oracles.
**Policies (same capacity, speed, budget mechanism, information, scoring).**
1. `split_lru` / `split_slru` — static split: every miss admitted; DRAM gets a hash share (32%, the best safe split of
   2026-10-12); per-tier LRU / SLRU; the conventional baseline.
2. `value_split` — reuse-aware only: the RQ1 admission (`2nd_int` with the first-touch-horizon regime switch, SLRU
   structure); placement fixed (hash share 32%); no movement.
3. `cost_budget` — cost-aware only: every miss offered; budget-gated DRAM placement (token bucket), CXL otherwise;
   when the CXL backlog exceeds Q_max seconds of work the arriving store is dropped (value-blind congestion control);
   no reuse information.
4. `indep` — the critical baseline: the RQ1 admission decides *whether*, then the budget decides *where*, then the
   congestion rule drops value-blind; the two modules never exchange information.
5. `joint` — one decision per block from value and cost: (a) admission as RQ1, but the regime switch to first-touch
   admission is taken only if the write path can carry the full stream (offered rate ≤ CXL capacity + DRAM budget);
   (b) while the CXL queue is congested (> Q_pri seconds), the DRAM budget goes to high-value blocks only
   (P̂ ≥ v_th); (c) under congestion (> Q_max) low-value blocks are dropped first and high-value blocks still queue;
   (d) with a checkpoint writer, high-value KV stores go ahead of checkpoint pieces and low-value KV stores are
   dropped during the checkpoint burst; no migration unless a variant says so.
6. `oracle_cost` — ORACLE value (Belady admission with bypass) under the same budget, queue and drop rules; and
   `oracle_free` — the RQ1 capacity-only oracle (no bandwidth constraint) for reference.
Variants for the decomposition: `joint_2nd` (plain second touch as the value signal), `joint_novalue` (the joint cost
rules with admit-all = `cost_budget`), `indep` with and without the congestion drop, migration on / off.
**Selection.** The budget (B, d) and the drop bound Q_max are selected per configuration on the FIRST half of the
trace by one rule for every policy that uses them (highest usable hit share with an estimated p99 ≤ 6%, i.e. a 1-point
margin below the SLO, following the 2026-10-13 method lesson); the test half is never used for selection.
**What the model does not do.** No GPU-link or PCIe queueing (loads are link-bound and tier-independent on c28); the
interference curve is applied to the window-mean DRAM rate, as calibrated, not simulated per burst (the calibration's
20-ms peaks are reported for the hash and budget families and are the reason for the two curves); DRAM capacity used
by the neighbour itself is not modelled (DRAM is 64 GiB for KV in every policy); the CXL path is one FIFO server
(no per-card striping effects); checkpoint durability ends at the CXL/DRAM copy (the NVMe drain of cxlpath, 0.9 GiB/s,
is outside the window).

## Correction to the earlier rounds' write volumes (found 2026-10-21 while validating this simulator)
The "TB written (scored half)" columns of `2026-10-20-rq1b-admission-study.md`, `2026-10-21-rq1b-adaptive-admission.md`
and `2026-10-21-rq1b-robust-admission.md` count admissions over the WHOLE trace (both halves: `st["written"]` was not
gated by the scoring window in `kv_agent_replay.py` and `kv_admission_sim.py`), so their absolute volumes are ~2× the
scored-half volumes and the rates derived from them by dividing by the scored half's 1,800 s are ~2× too high (LRU at
8B 1×: 18.0 TB over the whole hour = 5.0 GB/s, which matches the emulation's 5.4 GB/s offered mean, not 10 GB/s). The
relative reductions (−69 … −77%) and every hit-share number are unaffected. This simulator counts the scored half only
(LRU: 126,085 blocks = 8.46 TB in the 1,656 wall-seconds of the scored half at 1× = 5.1 GB/s). The frozen files are
not edited; this note and the decision report carry the correction.

## Validation of the simulator (Task C)
Single tier of 200 GiB, no bandwidth limit, 1×: `split_lru` 0.180, `value_split` 0.387, `oracle_free` 0.801 usable share
vs the RQ1 replay's 0.178 / 0.384–0.395 / 0.797 (`val-single-tier`); the differences come from two modelled details
the RQ1 replay did not have — the j-th block of a request is offered j × 70 ms after the request (prefill at 7,300
tokens/s) and the residence estimate is the unbiased dead-eviction one. The RQ1 oracle is reproduced to 0.004.

## Task A — remaining resource pressure after RQ1 (Deliverable 1; fig-joint-pressure, `kv_joint_pressure.py`)
Scored half, test half of the requests, wall time; "offered" = `split_lru` (every miss admitted: the stream LMCache
produces); "after RQ1" = `indep` (the RQ1 admission); per-second rates of the admitted stream (DRAM + CXL).

| model × speed (conversation) | offered: mean / p99 / max GB/s | seconds above the CXL capacity (46 GB/s) | DRAM part of the 32% split, mean → Adam p99 | after RQ1: mean / p99 / max GB/s | DRAM part, mean / max → Adam p99 | idle seconds (no write) | CXL backlog max |
|---|---|---|---|---|---|---|---|
| 8B 1× | 4.7 / 13.8 / 19.3 | 0 of 1,775 | 1.6 → +1.5% | 0.56 / 3.3 / 6.0 (−88%) | 0.17 / 2.2 → +0.1% | 796 of 1,769 (45%) | 0 GB |
| 8B 4× | 18.6 / 31.8 / 32.6 | 0 of 450 | 6.1 → +5.8% | 2.2 / 6.7 / 8.1 (−88%) | 0.56 / 2.6 → +0.5% | 30 of 445 | 0 GB |
| 8B 8× | 35.9 / 55.2 / 56.8 | 36 of 230 (17 bursts ≤ 4 s) | 11.8 → +10.1% | 4.4 / 10.5 / 11.4 (−88%) | 1.04 / 3.2 → +0.9% | 12 of 224 | 0 GB |
| 70B 1× | 12.2 / 35.7 / 53.0 | 2 of 1,775 | 4.0 → +4.0% | 1.1 / 6.9 / 11.2 (−91%) | 0.32 / 3.5 → +0.3% | 975 of 1,769 (55%) | 1 GB |
| 70B 4× | 47.9 / 81.6 / 90.1 | 281 of 450 (39 bursts, longest 28 s); backlog 58 GB | 15.7 → +13.9% | 4.3 / 14.6 / 18.8 (−91%) | 0.96 / 3.2 → +0.8% | 53 of 443 | 1 GB |
| 70B 8× | 93.0 / 144 / 150 | 207 of 230 (one 207-s burst); backlog 10.5 TB | 30.5 → +36%* | 8.5 / 22.3 / 23.0 (−91%) | 2.1 / 6.9 → +1.9% | 16 of 223 | 1 GB |

The tool-agent trace is within 5% of these numbers (`kv_joint_pressure.py`). (\* extrapolated beyond the measured
24 GB/s.) Speeds: 4× / 8× are multi-server aggregates of the one-hour trace (time compression; the emulation of
2026-10-10 reached 21 / 42 / 53 / 105 GB/s offered at 8B 4× / 8B 8× / 70B 4× / 70B 8×; this replay's offered means are
19 / 36 / 48 / 93 — the same stream, the scored half only).
- **A1.** The RQ1 admission removes 88–91% of the write volume and all of its tail: after filtering the per-second
  rate never exceeds 25 GB/s at any scale (half the CXL path), the DRAM part of a 32% split stays at 0.2–2.1 GB/s
  (one quarter of the safe budget beside Adam) with a worst minute ≤ 2.4 GB/s, the CXL backlog never exceeds 1 GB,
  and at 1× the host writes nothing in 45–55% of the seconds. Without filtering the same stream saturates the CXL
  path for 62% of the time at 70B 4× (backlog 58 GB) and continuously at 70B 8× (backlog 10.5 TB), and its DRAM
  share alone breaks the 7% SLO from 8B 8× on (+10 … +36%).
- **A2 scaling.** 1× is one server's hour of trace (real timestamps); 4× / 8× compress time (same requests, 4× / 8×
  the bytes per second — the per-request prefill rate stays physical); nothing is synthetic except the stress runs
  below. The filtered stream at 70B 8× (8.5 GB/s mean, 23 GB/s max) is what ~8 servers of this trace at 1× would
  offer together after admission.
- **A3 headroom.** After RQ1 there is no window in any configuration where the write path saturates (0 seconds above
  46 GB/s), the DRAM budget is exhausted (the token bucket at the selected 2–32 GB/s refuses nothing: 0 DRAM-budget
  refusals in the test runs) or the neighbour's SLO is approached (p99 ≤ 1.9%). The interference problem that
  motivated the cost side (`2026-10-10`, `2026-10-12`: +17 … +63% at 70B beside Adam, backlog > 700 GB) is a
  property of admit-all caching; value-aware admission alone removes it at every scale tested, with no cost-aware
  mechanism at all. **Real conflict windows exist only without the filter** (70B 4× / 8×: the CXL path saturated,
  DRAM over budget) **or under CONSTRUCTED stress** (§E3: the CXL path reduced to one card or less, a 64 GiB
  checkpoint every 5 s).

## Task B — is value coupled to cost? (Deliverable 2)
- **B1 value → placement: no.** Reads cost the same from both tiers for the GPU (A3, measured), so the only effect of
  putting high-value blocks in DRAM is a hot/cold partition of the capacity. With the online value (P̂ of a re-lookup
  within the residence; top 32% by value → DRAM) the joint policy matches the hash split to ±0.007 at every
  configuration (`joint` vs `joint_hash`: 0.384 vs 0.384 at 8B 1×, 0.247 vs 0.240 at 70B 4×, 0.231 vs 0.233 at 70B
  8× on the conversation trace; 0.745 / 0.743, 0.670 / 0.673, 0.671 / 0.673 on the tool-agent trace); with the ORACLE
  value the oracle's own placement gains +0.5 / +1.2 / +3.4 points over its hash placement at 70B 1× / 4× / 8× and
  ±0.5 at 8B. Value does not say *where*; the capacity share does (the 2026-10-12 finding holds: the hit share follows
  DRAM's share of the admitted blocks).
- **B2 cost → admission: not at these loads.** The joint admission rules that depend on cost — the DRAM budget
  reserved for high-value blocks under CXL congestion, value-ordered drops, the cost veto of the normal-admission
  regime — never fire in any test configuration (0 drops, 0 vetoes, backlog ≤ 1 GB), because the admitted stream is
  never congested. A block's admission benefit does change with the path state in principle (a store that completes
  after its next use is useless), but after RQ1 the path state is always "idle".
- **B3 value → movement: no.** Promoting a block to DRAM on its first CXL hit (`--migrate`, counted as a DRAM write
  and a CXL read) changes `indep` by +0.002 / +0.002 / +0.003 (70B 4× / 70B 8× / 8B 8×) and `joint` by −0.018 /
  −0.012 / −0.006; the previous rounds' result that migration adds nothing over admission stands, and value does not
  change it.
- **B4 are the decisions coupled?** Value-aware admission followed by an independent cost-aware placement is
  sufficient on every real-trace configuration up to 70B 8× beside the most sensitive neighbour measured: the two
  modules never need to exchange information because the first one empties the queue the second one would manage.
  Coupling appears only when the *filtered* stream exceeds the path (§E3) — a load this hardware has not been
  measured under (CONSTRUCTED).

## Task D — fair baselines (Deliverable 4; fig-joint-grid)
Test half (requests 50–100%), 200 GiB = 64 DRAM + 136 CXL, the (budget, depth) pair selected on the first half for
every budget policy (`selection.md`: 2–32 GB/s, depth 1 except 8B 1× conversation depth 4), beside the Adam step;
usable-prefix hit share; p99 = estimated Adam p99 slowdown (interpolated calibration; * extrapolated).

| config | split + LRU | split + SLRU | reuse-aware only | cost-aware only | **independent** | **joint** | joint, hash placement | joint, plain 2nd touch | ORACLE value, same costs | ORACLE value + placement | ORACLE free || p99: split / cost / indep / joint |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| conv 8B 1× | 0.177 | 0.209 | 0.381 | 0.210 | **0.384** | **0.384** | 0.384 | 0.338 | 0.784 | 0.779 | 0.784 || 1.5 / 1.0 / 0.1 / 0.2 |
| conv 8B 4× | 0.180 | 0.198 | 0.380 | 0.198 | **0.387** | 0.382 | 0.387 | 0.334 | 0.782 | 0.781 | 0.784 || 5.8 / 1.8 / 0.5 / 0.5 |
| conv 8B 8× | 0.177 | 0.193 | 0.381 | 0.207 | 0.381 | **0.385** | 0.381 | 0.338 | 0.751 | 0.760 | 0.758 || 10.1 / 2.8 / 0.9 / 0.9 |
| conv 70B 1× | 0.123 | 0.127 | 0.235 | 0.130 | **0.240** | 0.235 | 0.240 | 0.170 | 0.529 | 0.534 | 0.523 || 4.0 / 1.6 / 0.3 / 0.2 |
| conv 70B 4× | 0.122 | 0.124 | 0.236 | 0.122 | 0.240 | **0.247** | 0.240 | 0.167 | 0.520 | 0.532 | 0.519 || 13.9 / 2.4 / 0.8 / 0.7 |
| conv 70B 8× | 0.116 | 0.120 | 0.234 | 0.115 | **0.233** | 0.231 | 0.233 | 0.167 | 0.439 | 0.473 | 0.452 || 36\* / 5.1 / 1.9 / 1.8 |
| tool 8B 1× | 0.647 | 0.657 | 0.742 | 0.655 | 0.743 | **0.745** | 0.743 | 0.732 | 0.930 | 0.930 | 0.932 || 1.5 / 0.5 / 0.1 / 0.1 |
| tool 8B 4× | 0.647 | 0.654 | 0.745 | 0.651 | 0.742 | **0.744** | 0.742 | 0.737 | 0.932 | 0.933 | 0.933 || 5.7 / 2.3 / 0.5 / 0.5 |
| tool 8B 8× | 0.647 | 0.650 | 0.746 | 0.651 | **0.743** | 0.742 | 0.743 | 0.739 | 0.920 | 0.924 | 0.924 || 9.3 / 3.9 / 1.0 / 1.0 |
| tool 70B 1× | 0.619 | 0.620 | 0.672 | 0.621 | **0.673** | 0.672 | 0.673 | 0.646 | 0.812 | 0.812 | 0.813 || 3.8 / 1.4 / 0.2 / 0.2 |
| tool 70B 4× | 0.620 | 0.621 | 0.671 | 0.619 | **0.673** | 0.670 | 0.673 | 0.642 | 0.809 | 0.815 | 0.813 || 13.7 / 3.4 / 1.0 / 0.8 |
| tool 70B 8× | 0.616 | 0.619 | 0.670 | 0.616 | **0.673** | 0.671 | 0.673 | 0.640 | 0.753 | 0.781 | 0.772 || 33.7\* / 5.5 / 1.8 / 1.2 |

Beside the DRAM reader and with no neighbour the hit shares are the same to ±0.008 (the budget binds nowhere).
- **Joint vs independent: −0.005 … +0.007** over the twelve configurations (mean +0.0004); the sign flips with the
  configuration, i.e. noise of the quantile placement, not a mechanism. **Reuse-aware only** (RQ1 admission, static
  split, no cost module) is within 0.001–0.007 of both. **Cost-aware only** (admit all, budget-gated split) buys SLO
  safety (p99 0.5–5.5% vs the split's 1.5–36%) at the hit share of the split (+0.00 … +0.03), as in 2026-10-12.
- **The oracles:** the value oracle under the same costs loses ≤ 0.02 to the unconstrained oracle (0.439 vs 0.452 at
  70B 8×; identical elsewhere): the measured costs do not bind even for a policy that admits 3× more than the RQ1
  rule. Gate 3's premise (a joint policy vs the best independent combination at the same SLO) is therefore tested
  under conditions where the independent combination already pays no cost.

## Task E — regimes (Deliverable 5; `reg-*`, fig-joint-regimes)
| regime | condition | split + SLRU | reuse-aware only | cost-aware only | independent | joint | ORACLE value, costs | what differs |
|---|---|---|---|---|---|---|---|---|
| E1 low pressure | 8B 1× / 4×, 70B 1× (real) | 0.13–0.21 | 0.24–0.38 | 0.13–0.21 | 0.24–0.39 | 0.24–0.38 | 0.52–0.78 | nothing: no module ever refuses or drops |
| E2 DRAM interference | 8B 8×, 70B 4× beside Adam (real stream, measured curve) | p99 +10 / +14% (fails) | +1.4 / +1.6% | +2.8 / +2.4% | +0.9 / +0.8% | +0.9 / +0.7% | +1.2 / +1.4% | the RQ1 admission alone brings the DRAM writes under the budget; the cost module adds safety only to admit-all |
| E3 CXL saturation | 70B 4× / 8× admit-all: backlog 58 GB / 10.5 TB; after RQ1: 1 GB | — | — | drops 10–60k blocks (value-blind) | 0 drops | 0 drops | — | after filtering no saturation; see the CONSTRUCTED stress below |
| E4 capacity pressure | 100 GiB (32 + 68) at 70B 4× / 8B 8×, Adam | 0.114 / 0.136 (p99 14 / 10%) | 0.175 / 0.265 | 0.114 / 0.127 | **0.177 / 0.275** | 0.174 / 0.266 | 0.357 / 0.530 | the joint value placement is −0.3 / −0.9 points: a hot/cold partition hurts under capacity pressure |
| E5 checkpoint co-writer | 64 GiB every 60 s / 15 s on the CXL path, 70B 4× and 8B 8×, Adam; FIFO / KV-priority / joint rule | 0.124 / 0.193; checkpoint 1.5 s (FIFO), 15.3–15.6 s (KV priority: the admit-all stream starves it) | 0.236 / 0.381; 1.5–1.8 s | 0.122 / 0.204 | 0.240–0.241 / 0.374–0.381; 1.5–1.8 s | **0.242–0.252 / 0.384–0.388**; 1.5–1.8 s | 0.49–0.52 / 0.71–0.75 | +0.1 … +1.2 points for the joint rule (low-value KV dropped during the burst, high-value ahead of checkpoint pieces); every value-aware policy completes a 64 GiB checkpoint in 1.5 s (46 GB/s) because the KV stream leaves the path free |
| E6 phase changes | Adam 30 s on / 30 s off (budget 32 while off), 70B 4× / 8B 8× | 0.124 / 0.193 | 0.236 / 0.381 | 0.130 / 0.197 | 0.238 / 0.383 | 0.240 / 0.386 | 0.520 / 0.754 | +0.2 / +0.3 points; the budget's on/off swing has nothing to redistribute (DRAM 0.9–1.1 GB/s) |
The tool-agent trace gives the same picture (E4 half capacity: independent 0.639 / 0.688 vs joint 0.643 / 0.687 at
70B 4× / 8B 8×; E5 checkpoints at 15 s / 60 s: 0.672–0.673 / 0.740–0.743 vs 0.671–0.673 / 0.736–0.743, completion
1.5–1.9 s; E6 phases: 0.673 / 0.743 vs 0.670 / 0.742), and so does the no-neighbour run of the saturating load (70B 8×:
admit-all backlog 9.6–10.4 TB, every value-aware policy 1 GB; independent 0.233 / 0.673, joint 0.231 / 0.671).
The CONSTRUCTED mixed traces of the 2026-10-20 admission study at 70B 4× beside Adam (`reg-mixphase`: a phase change
from one workload to the other; `reg-mixinter`: the two interleaved) are denser than either real trace: admit-all
offers 34 / 69 GB/s to the CXL path (backlog 34 GB / 20.9 TB, Adam p99 13.6 / 35.2%, SLO fails) and the cost-only
policy holds the path only by dropping 7.8k / 132k blocks. After the RQ1 admission the same streams are 3.6 / 5.1 GB/s
with a 1–2 GB backlog and p99 0.5–1.0%, and joint vs independent is +0.5 / −0.4 points (0.671 vs 0.666 on the phase
change, 0.491 vs 0.495 interleaved; joint with hash placement equals the independent policy exactly; 0 drops, 0
vetoes; value oracle 0.80–0.81 / 0.60–0.62). The regime rule stays in the filtering state throughout both.

**Where would value and cost couple? (CONSTRUCTED stress, 70B 8× beside Adam, `stress-*`; conversation / tool agent)**
| stress | independent | independent, no drop | joint | joint, hash placement | joint, no drop | ORACLE value, costs | reading |
|---|---|---|---|---|---|---|---|
| CXL path cut to one card (23 GB/s) | 0.232 / 0.673 (backlog 1 GB) | same | 0.231 / 0.672 | 0.232 / 0.673 | 0.231 / 0.672 | 0.394 / 0.744 | the filtered stream (8.5 GB/s) still fits: nothing couples |
| CXL 12 GB/s (a quarter) | 0.232 / 0.673 (14 GB) | same | 0.233 / 0.671 | 0.231 / 0.671 | 0.232 / 0.671 | 0.264 / 0.672 (drops 9k) | still fits; only the oracle's 3× larger stream queues |
| CXL 6 GB/s (below the filtered mean) | **0.207 / 0.663** (backlog 12 GB, 3.0–3.5k value-blind drops) | 0.167 / 0.633 (backlog 707–714 GB, 2.7k pending misses) | 0.178 / 0.647 (6.1–6.4k value-ordered drops) | 0.191 / 0.652 | 0.162 / 0.634 | 0.207 / 0.661 | the path is overloaded: congestion control is worth +4 / +3 points, and the value-blind drop beats the value-ordered one by 3 / 2 points — keeping "high-value" stores queued (up to 4 × Q_max) makes them late and useless; the oracle with value-blind drops equals the online policy |
| CXL 23 GB/s and the DRAM budget cut to 1 GB/s | 0.205 / 0.658 | same | **0.213 / 0.660** | 0.205 / 0.658 | 0.213 / 0.660 | 0.153 / 0.617 | DRAM starved: giving the few DRAM slots to the top-value blocks is worth +0.8 / +0.2 points — the only place value placement shows, and it is small |
| checkpoint 64 GiB every 5 s (FIFO) | 0.231 / 0.672 (completion 1.5 s) | same | 0.230 / 0.670 | 0.223 / 0.667 | 0.230 / 0.670 | 0.403 / 0.736 | nothing couples: the 46 GB/s path absorbs a 30% checkpoint duty beside the filtered stream |
| checkpoint every 5 s, KV priority | 0.233 / 0.673 (2.1–2.2 s) | same | 0.234 / 0.671 | 0.228 / 0.665 | 0.234 / 0.671 | 0.437 / 0.753 | KV priority (value-blind) costs the checkpoint 0.6 s and nothing else |
| checkpoint every 5 s, the joint rule (low-value KV dropped during bursts) | 0.214 / 0.663 (3.2k drops) | 0.233 / 0.673 | 0.211 / 0.660 (4.1–4.2k drops) | 0.212 / 0.663 | 0.234 / 0.671 | 0.368 / 0.727 | the joint checkpoint rule is harmful: it drops 3–4k useful stores for a path that was never short |

Even where the path is overloaded (a load ~8× beyond the 70B 8× aggregate on this hardware, or a path ~8× slower),
the independent, value-blind congestion control is the better mechanism, and the only positive joint effect (DRAM
budget starved to 1 GB/s: +0.2 … +0.8 points) is below the noise of the quantile placement elsewhere.

## Task F — application-level meaning
Replay quantities (not measured end to end): with the RQ1 admission the recomputed tokens of the scored half fall
from 62–66 M (split) to 58–63 M (−5 … −9%; oracle 47–56 M, −16 … −27%), the TTFT model (2026-10-18 measured
per-token costs) by 8–9% (oracle 23–26%), host writes by 88–91%, DRAM writes by 83–95%, and the estimated Adam p99
from 1.5–36% to 0.1–1.9%; joint vs independent: 0.0 ± 0.3% in every one of these. Neighbour interference: the
measured curves (2026-10-12) apply within 0–24 GB/s of DRAM writes; every value-aware policy sits at 0.1–2.4 GB/s,
where the curve is nearly linear and the p99 ≤ 2%; the CXL-busy share, the cost to a CPU reader of CXL (2026-10-09/12,
2.4× on a dependent read inside bursts), falls with the write volume (CXL busy ≤ 10% after RQ1 at 70B 8× vs ≥ 90%
without). Checkpoint: a 64 GiB copy completes in 1.5 s beside the filtered KV stream in every mode; beside the
admit-all stream KV priority starves it (15.6 s at 70B 4×, 74.6 s for the cost-only policy at 60-s period) — the
2026-10-12 finding that two writers need coordinated admission applies to the unfiltered stream only. No checkpoint
trace suitable for joint replay exists (the real producers of 2026-09-22 were periodic 64–96 GiB copies, used here as
the stream model); durability is the copy's completion, the NVMe drain is outside the window.

## Task G — decomposition (Deliverable 6)
| component | evidence | contribution |
|---|---|---|
| value signal only (RQ1 admission, static split) | `value_split` | 97–100% of the independent combination's gain; all of the write and interference reduction |
| cost signal only (budget-gated split + drops, admit all) | `cost_budget` | hits of the split (+0.00 … +0.03); SLO safety; drops 10–60k blocks at 70B |
| both, independent decisions | `indep` | = value only + SLO safety; 0 drops |
| joint decisions | `joint` | −0.005 … +0.007 vs independent (test half, 12 configurations); +0.1 … +1.2 under checkpoint bursts; −0.3 … −0.9 under capacity pressure |
| oracle value + measured cost | `oracle_cost` vs `oracle_free` | −0.02 … 0.00: the costs do not bind |
| plain second touch instead of the adaptive admission (`joint_2nd`) | 70B: −7 … −9 points; 8B: −0.5 … −4.6 points | the gap rule carries the value; the joint rules do not compensate for a weaker signal |
| without the value signal (`cost_budget` = the joint cost rules with admit-all) | 0.115–0.210 | = split: the joint rules have nothing to work with |
| without real contention | 0 drops, 0 vetoes, 0 budget refusals in every test run | the joint policy degenerates to the independent one by construction |
Benefits from avoided low-value writes: all of the write / interference reduction, from RQ1 (not joint). Better tier
placement: none online (±0.007), ≤ +3.4 points with oracle value at 70B 8×. Reduced interference: from the volume
reduction, not from placement. Preserved capacity: the oracle's remaining gain (0.23 → 0.45–0.52, the first-touch
cost of RQ1), untouched by either combination. Migration cost: −0.006 … −0.018 for the joint variant. Bad value
predictions: the 49–52% dead second-touch admissions (RQ1) occupy capacity in every policy alike.

## Task H — critical assessment (Deliverable 7)
1. **Remaining write pressure after RQ1:** not significant on this hardware at any scale tested: 0.6–8.5 GB/s mean,
   ≤ 25 GB/s peak, ≤ 1 GB of backlog, DRAM ≤ 2.1 GB/s — below every measured threshold (CXL 46 GB/s, safe DRAM 6–8
   GB/s). The pressure that the write-interference work measured belongs to admit-all caching.
2. **Workloads that need value and cost together:** none of the real ones tested (two Mooncake traces × 8B / 70B ×
   1–8×, two neighbours, checkpoints at 60 / 15 s, phases, half capacity, mixes). The joint rules fire only under
   CONSTRUCTED stress (the CXL path cut to ≤ half a card, or a checkpoint every 5 s).
3. **Where the independent combination suffices:** everywhere above — and the independent cost module is itself
   idle; the RQ1 admission alone (static split) is within 0.007 of the best policy at every configuration.
4. **Joint gain at equal information and resources:** −0.5 … +0.7 points of usable hit share on the grid, +0.1 … +1.2
   under checkpoint bursts, −0.3 … −0.9 under capacity pressure; 0.0 ± 0.3% in recompute and TTFT.
5. **Does it pay for its complexity:** no. The joint policy adds four rules, an online value quantile and a cost veto
   for no measurable gain.
6. **Difference from a classic admission + bandwidth controller:** none that the data can see; our admission signal
   is better than the classic ones (RQ1), and the budget controller is the 2026-10-12 one; their combination is the
   strongest policy here.
7. **Strongest evidence:** the write-pressure table (Task A) and the grid (Task D): one admission rule removes the
   problem the cost side was built for, on both real traces, at every scale, beside the most sensitive neighbour.
8. **Strongest negative evidence for the hypothesis:** `oracle_cost` = `oracle_free` to ≤ 0.02 — even perfect value
   information gains nothing from cost awareness at these loads; and `joint` = `indep` at 0 drops / 0 vetoes.
9. **Unverified assumptions that could change the picture:** the interference curve beyond 24 GB/s of DRAM writes
   (extrapolated); CPU-copy emulation vs GPU DMA (A6); DRAM capacity contention with the neighbour (DRAM is 64 GiB
   for KV in every policy here); loads whose filtered stream exceeds ~46 GB/s (≥ 40 servers of this trace at 70B, or
   much larger blocks); a workload whose reuse is not dominated by dead blocks (the RQ1 filter removes 88–91% here);
   checkpoint producers co-located at a higher duty cycle than measured; multi-tenant KV caches where the admission
   signal is shared.
10. **Minimal system implementation:** not on the current core hypothesis. The evidence supports a different and
    smaller claim — value-aware admission makes DRAM/CXL KV caching interference-free and makes cost-aware placement
    unnecessary at single-host scale — which is an RQ1 + RQ3 result, not the joint RQ2 one.

**Verdict.** The core hypothesis — that deciding value and movement cost together improves on deciding them
independently — is **not supported** by anything this study could measure or replay. Every real-trace configuration
(two traces × 8B / 70B × 1 / 4 / 8× × two neighbours, 200 GiB and 100 GiB, with and without checkpoint co-writers and
neighbour phases) ends with the joint policy within −0.9 … +1.2 points of the independent combination, and the sign
is not systematic. The reason is structural, not a tuning accident: the RQ1 admission removes 88–91% of the write
stream and all of its tail, so after it the measured path has 5–11× headroom, the DRAM write rate is 3–40× below the
safe budget, and the cost module's decisions (budget refusals, congestion drops, regime vetoes, migrations) never
fire — there is nothing left for a joint decision to trade off. Where the stream is made to exceed the path
(CONSTRUCTED: CXL cut to 6 GB/s, ~8× beyond the hardest real configuration), the value-blind congestion drop beats the
value-ordered one, because holding a "valuable" store in a long queue makes it arrive too late to be used. The value
oracle under the same costs loses ≤ 0.02 to the unconstrained oracle, which bounds what any cost-aware mechanism could
add at these scales. What the evidence does support: (i) the write-interference problem measured on 2026-10-10/12 is a
property of admit-all KV caching; (ii) online reuse-aware admission alone makes DRAM/CXL KV caching interference-free
beside the most sensitive neighbour measured and keeps checkpoint co-writers at their uncontended completion time;
(iii) a budget-gated split is a sufficient (and idle) safety mechanism. These are RQ1 + RQ3 results. The study does
not proceed to a minimal unified manager; the next step is the user's / advisor's decision on how to reposition the
contribution (see the decision report, Update 2026-10-21 Phase 3).


