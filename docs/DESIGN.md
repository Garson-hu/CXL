# System Design (current)

*The one document that always describes the system as it exists now.
History: `## Change history` at the bottom (append-only). Predecessor file:
`archive/DESIGN_OBJPLACE.md` (2026-05-20 original, verbatim).*

**Status 2026-08-25:** ObjPlace v1 (below) is built and evaluated
(`experiments/2026-05-19-baseline-objplace.md`). The per-direction extension
(§7) is DESIGNED-ONLY, gated on the experiments in
`experiments/2026-08-25-direction-gates.md`.

**Status 2026-09-18:** §10 (write-path runtime, PolyStore-inspired) is the
CURRENT design direction — DESIGN-ONLY, under discussion with the user, nothing
built, no experiments until it is agreed. §1–§9 describe the existing ObjPlace
v1 code; §7's per-direction accounting is reused inside §10.3.

## 1. What ObjPlace is
Object-level semantic placement, not a `numa_alloc_onnode` wrapper: the
application registers each memory object with its *type, access pattern,
sensitivity, hot fraction, skew, phase*; a benefit-guided planner decides
DRAM / CXL / SPLIT under a model of CXL bandwidth pressure. Rationale: the two
signals that decide CXL placement value — **bandwidth-sensitivity** and **access
skew** — are known to the application and invisible to page-grain hotness
tracking (a bandwidth-bound object loses 2.0–2.13× under a CXL co-tenant; a
latency-bound one ≤1.23×; same hotness, different placement value).

## 2. Object registry
Per-object metadata (in-process array, no kernel involvement):
`id` · `size` · `type` {generic, embedding, feature, kv, buffer} ·
`access` {streaming, random, mixed} · `sensitivity` {bandwidth, latency,
capacity} · `hot_fraction` 0..1 · `skew_alpha` ≥0 · `phase` {active, inactive,
prefill, decode, gather} · `placement` (planner output).

## 3. CXL pressure model (v1 — single ceiling)
```
CXL_BW_CEILING_GIB = 35.5          // measured pair ceiling, May 2026
pressure_factor    = clamp(cxl_load / ceiling, 0, 1.2)   // load supplied via
objplace_set_pressure(); default = saturated (conservative)
```
Known v1 limitation: ONE number models the tier; read and write traffic are not
distinguished. Replaced by §7 once gates pass.

## 4. Benefit-guided planner
Per candidate (whole object, or hot/cold partition of a skewed object):
```
cxl_penalty = 1 + base_penalty(access) * pressure_factor
              base: streaming 1.10, mixed 0.60, random 0.25
sens_mult   = bandwidth 1.0, latency 0.5, capacity 0.1
phase_mult  = active/prefill/decode/gather 1.0, inactive 0.1
density     = access_share / partition_fraction,
              access_share = hot_fraction ^ (1 / (1 + skew_alpha))
benefit_per_byte = sens_mult * phase_mult * (cxl_penalty - 1) * density
```
Greedy 0/1-knapsack: sort candidates by benefit-per-byte, fill the DRAM budget,
rest to CXL; partition decisions fold back to DRAM/CXL/SPLIT. This beats
hotness-only exactly where sensitivity separates equally-hot objects (+118%
measured).

## 5. Lifecycle (no migration)
`obj_create` registers + plans (no allocation) → `obj_rebalance()` global
re-plan of unmaterialized objects → `obj_ptr` / `obj_hot_ptr` / `obj_cold_ptr`
materialize on first call (one `numa_alloc_onnode` per partition), placement
then fixed. `obj_update_phase` / `obj_update_hotset` mutate metadata for the
next re-plan. Typical flow: create-all → rebalance → materialize → run.

## 6. Scope guard + known limitations (v1, from evaluation)
No automatic hot/cold detection; no page migration; no kernel module; no KV
claim; no multi-device policy. Planner has no INTERLEAVE candidate (uniform
bandwidth objects over budget go all-CXL: GNN-uniform −11.6%). Tight budgets
(0–1 objects fit) are degenerate. Pressure is supplied, not sensed.

## 7. PLANNED extension — per-direction budgets (pending gates, 2026-08-25)
Motivation and evidence: `PAPER.md` Thesis v2. Design intent, to be finalized
after Gates 1–2:
- **Two budgets per tier** replace the single ceiling: `(read_bw, write_bw)`.
  DRAM charges an app-level write **2×** (RFO + writeback, measured exact);
  CXL charges it against the write budget only (duplex link).
- **`dir` attribute** on objects: `READ_STREAM / WRITE_STREAM / RMW` — the
  planner's benefit term keys on direction × per-tier direction cost.
- **Staging API:** `obj_stage_out(h)` / `obj_stage_in(h)` — NT-store bulk copy
  DRAM↔CXL off the critical path (checkpoint/eviction verb; NT stores skip RFO).
- **LLM extension points (interfaces only):** object-class presets
  `KV_EVICT`, `PREFIX_INSERT`, `OPT_STATE` over `dir`; promote-on-hit hook.
  Explicit non-goal now: active-decode KV on CXL (read-latency trap).

## 8. Positioning caveat (unchanged, binding)
"Object-level sensitivity-aware tiering" is NOT net-new (SoarAlto OSDI'25,
X-Mem, Colloid SOSP'24 own neighboring claims). Deltas we may claim: online
hint-driven placement + CXL bandwidth-pressure arbitration + real CZ120; after
the pivot, **traffic direction as the placement signal**. Never claim "first
object-level tiering" / "first hotness-insufficiency"; cite SoarAlto, Memstrata,
Colloid explicitly. Verify Clove + VLDB'25 before claiming the direction delta.

## 9. API reference (v1, header `system/placement/objplace.h`)
Enums: `obj_type_t` {GENERIC, EMBEDDING, FEATURE, KV, BUFFER}; `access_pattern_t`
{STREAMING, RANDOM, MIXED}; `sensitivity_t` {BANDWIDTH, LATENCY, CAPACITY};
`phase_t` {ACTIVE, INACTIVE, PREFILL, DECODE, GATHER}; `placement_t` {DRAM, CXL,
SPLIT, INTERLEAVE}.
Config: `objplace_init(dram_node, cxl_node)` (env `OBJ_DRAM_NODE`/`OBJ_CXL_NODE`)
· `objplace_set_dram_budget(bytes)` (default 2 GiB; env `OBJPLACE_DRAM_BUDGET`)
· `objplace_set_pressure(load_gib_s)`.
Lifecycle: `obj_create(attr)` · `obj_rebalance()` · `obj_update_phase` ·
`obj_update_hotset` · `obj_destroy`.
Access: `obj_ptr` (NULL if SPLIT) · `obj_hot_ptr`/`obj_cold_ptr` ·
`obj_hot_bytes`/`obj_cold_bytes`.
Introspection: `obj_placement` · `obj_benefit_per_byte` · `placement_name` ·
`objplace_record_bytes` · `objplace_live_count`.
Legacy wrapper: `obj_alloc_hint(size, hint)` {BW_SENSITIVE, COLD_CAPACITY,
SKEW_HOT, SKEW_COLD} (forces a tier, bypasses budget) · `obj_free_hint`.
Python: ctypes bridge, `ObjAttr` mirrors `obj_attr_t`
(`benchmarks/embbench.py:alloc_table_objplace`).

## 10. PLANNED — write-path runtime (design-only; consolidated 2026-09-18)
*All decisions below are provisional and user-agreed on 2026-09-18 unless
marked OPEN or TO VERIFY. Nothing is built. Motivation and paper framing:
`PAPER.md` Thesis v3. PolyStore (FAST'25) is a source of ideas, not a
comparison method; "borrowed" marks what comes from it.*

**What it is.** A userspace runtime (library + one background process per
node, no root) that manages a bulk write from the moment an application
produces it until it rests on NVMe, using DRAM and CXL side by side
(borrowed) instead of DRAM-first. Rarely-read write streams go straight to
CXL; DRAM bandwidth is kept for programs that read.

### 10.1 Goals and principles (structure borrowed from PolyStore §4.1)
Each goal answers one observation of the motivation (`PAPER.md` O1–O3); each
principle is realised by exactly one component below.
- **Goal 1 — keep bulk writes off DRAM without slowing the writer.**
  (from O2: heavy DRAM writes slow DRAM readers; O3: the same writes on CXL do
  not.)
  *P1: a direct, copy-free write path onto raw CXL* — the writer gets a pointer
  into the device; no staging copy, no middleman. → Component A.
  *P2: interference-bounded, direction-aware placement* — decide per segment
  where a write goes, from per-device per-direction state, bounded by how much
  DRAM readers may slow down. → Component B.
- **Goal 2 — spend DRAM only where reading benefits.**
  (from O1: most written data is never read again.)
  *P3: read in place, promote by break-even* — DRAM is a cache for repeated
  reads only, with the threshold derived per consumer. → Component C.
- **Goal 3 — give up nothing today's staging provides: data still reaches
  NVMe in the client's format, and survives a process crash.**
  *P4: DRAM-free drain and node-owned metadata.* → Component D.

### 10.2 Overview, clients and API
One library + one background process per node. Data path of a write:
client shim → `reserve` (Component B decides device/path, Component A hands
out a segment) → writer fills it → `commit` → Component D drains it to NVMe;
reads go through `lookup` (Component C decides whether to promote).

**Clients and interception.**
Intercept below the application so it is unchanged (borrowed). Three shims
over one core API:
- File-style checkpoint (VeloC staging layer): `pwrite` → reserve / `copy_in`
  / commit. Exploratory application — replaceable if results are weak.
- GPU checkpoint (PyTorch built-in async checkpoint — user decision; others
  such as DataStates-LLM may follow): the shim provides the staging buffers
  and owns the GPU→host copy loop, one segment per chunk.
- KV cache layer (LMCache-like): hook its internal allocate / free / get
  calls (→ reserve / release / lookup). Handing it one big pool would hide
  objects, reads and releases from the runtime.

**Core API.**
- `reserve(size, hints) → pointer`: contiguous, at most one segment; THE moment
  placement is decided, so callers never assume the device. Hints: lifetime
  class (checkpoint version), likely-read-back, optional drain target
  (file, offset) — no target means never drained.
- `commit`, `release`, `lookup(object) → extents` (pointer for DRAM/CXL,
  copy-out for NVMe), `copy_in` (always NT stores; plain stores to CXL read
  before writing).
- No intermediate DRAM copy exists for CPU-sourced writes.

### 10.3 Component A — segment store on raw CXL (P1; PolyStore analogue: Poly-index)
CXL on c28 is devdax-only: a raw `mmap` range, 2 MB alignment, no file system,
no allocator (the earlier tmpfs + memory-policy placement no longer works).
- **Segments: 32 MB** (user decision). One segment table for CXL and for the
  DRAM spill pool / GPU bounce buffers, in shared memory mapped by every
  process; a free segment is claimed by compare-and-swap. **No middleman and
  no IPC on the data path** (user decision).
- **Two uses of segments.** (a) Log segments: each writer thread appends into
  its own open segment without locks; per-segment live-byte count; returned at
  zero; **no compaction in v1** (user decision). Waste is bounded because data
  dies in batches: a checkpoint version dies as a whole; under LRU the
  never-read majority of KV blocks dies in write order; a block that reaches
  the promotion threshold releases its CXL copy. (b) Buffer sets for GPU
  checkpoint clients: long-lived, virtually contiguous (scattered segments
  mapped at adjacent addresses with `mmap(MAP_FIXED)`), registered with CUDA
  once, overwritten in place, two alternating sets. A set may be overwritten
  only when its version is complete on NVMe and the other set holds a
  committed version, so one complete version is always on CXL.
- **Index** (borrowed: per-object map of segments to devices; an object may
  span segments and devices): extent lists in the same shared memory, owned by
  the node-level store, not by the writer — the background process must find
  segments to drain, and a restart after a crash is a new process that must
  find the checkpoint on CXL. Volatile, no journaling (CZ120 is DRAM-based; the
  durable copy is on NVMe). Crash cleanup reclaims only uncommitted
  reservations.

### 10.4 Component B — interference-bounded placement (P2; analogue: Poly-placement)
Borrowed: measure every short epoch, then reassign. We reassign segments, not
threads, and the objective is not the sum of bandwidths but: **make the write
stream as fast as possible while other DRAM readers slow down by no more than
one machine-wide bound** (user decision: one global bound).
- **Signals (no root).** (1) Own ledger: bytes committed per device per epoch.
  (2) Achieved write speed per thread and per path versus its calibrated solo
  speed (borrowed). (3) DRAM latency probe in the background process: ~1000
  dependent random reads over a region larger than the cache, ≈0.15 ms, pinned
  to a CCD with no writer thread.
- **Decision variable.** CPU sources: spill ratio = share of new segments
  taken from DRAM. GPU sources (resting place fixed on CXL): path per chunk —
  direct (GPU writes CXL; no DRAM traffic; 3.9 GiB/s on c28) or staged (GPU →
  reused pinned DRAM buffer → runtime-owned pinned copy threads NT-copy to
  CXL; 12 GiB/s; full DRAM write stream). Same rule drives both; "spill" for
  GPU sources means the share of chunks taking the staged path.
- **Rule: slow increase, fast decrease.** Start at 0. Published in shared
  memory by the background process; `reserve` only reads it.
- **Initial parameter values (chosen by Claude on user request; all tunable).**
  Probe period 10 ms while reservations arrive, 200 ms when idle. Policy epoch
  50 ms when active (mean of the last 5 probes), 200 ms when idle. Idle
  baseline = minimum probe latency of the last 60 s. Bound = 1.10 × baseline.
  Increase: +1/16 per epoch (ratio realised as n of every 16 segments; 0→100%
  in 0.8 s, inside one multi-second checkpoint), only if the CXL path is full
  (achieved < 0.8 × solo speed) AND probe ≤ 1.05 × baseline (margin against
  oscillation). Decrease: halve as soon as 2 consecutive probes exceed the
  bound (20 ms reaction), whoever caused the pressure. Per-stream memory: a
  periodic writer starts from the ratio its last burst ended with.
- **Both devices full:** `reserve` blocks (sleeps on the shared table). Direct
  write to NVMe as a third outlet: possible later extension.
- **Same-card constraint:** a write stream on a CXL card slows readers of the
  same card (−41% bandwidth, 2.2× latency), not of another card. With only
  dax0.0/dax1.0 (same two cards) separation is in time only (see drain).

### 10.5 Component C — read path: DRAM as a cache for repeated reads only (P3; analogue: Poly-cache)
- **Read in place;** promote to DRAM only after k reads (borrowed: per-device
  cache rule; migrate only when the target has headroom):
  `k = ceil( t_copy × (1 + w × pressure) / (t_cxl − t_dram) )` — rent-or-buy,
  at most 2× the optimal cost. Constants per CONSUMER type, calibrated at
  start-up. CPU consumer with current numbers (CXL read ≈ 1.2 × DRAM,
  t_copy ≈ 1.0): k ≈ 5 when idle; user's provisional default k = 2 until
  re-measured for KV-like reads. GPU consumer on c28: reads CXL at link speed
  (12.5 vs 12.3 GiB/s from DRAM) ⇒ never promote. Reads counted per `lookup`
  in a **10-minute window** (two 5-minute buckets; KV re-reads arrive seconds
  to minutes apart — to be re-derived as the 90th percentile of re-read gaps
  in the traces). Promotion also needs probe ≤ bound and free DRAM quota;
  unit = the segments read. **Checkpoints are never promoted.**

### 10.6 Component D — DRAM-free drain and recovery (P4; analogue: Poly-persist)
- **Drain:** background process reads CXL, writes NVMe with O_DIRECT (no DRAM
  traffic), segment by segment as segments commit, to the drain target given
  at reserve. Yields to active writers on the same cards; drains at full speed
  when free segments fall below a threshold. Last partial chunk padded, file
  truncated.
- **KV leaving the memory tier: the client's policy decides** (LMCache local
  disk, Mooncake SSD offload, HiCache L3 all keep a storage tier; hard-coded
  discard would be challenged). The runtime offers the drain. **Selective drain: REMOVED after
  trace analysis** (`experiments/2026-09-18-kv-selective-drain.md`): draining
  only blocks read at least once while resident saves 74–97% of NVMe writes but
  loses most storage-tier hits, because a 512 GiB tier holds a block ~160 s
  while reuse gaps reach minutes. An oracle needs only 15–41% of the writes at
  equal or better hit rate, so a good predictor would pay off — future work.
- **Recovery:** after an application crash a new process finds the newest
  complete checkpoint version through the node-owned index and restores from
  CXL; after a node failure or reboot it restores from NVMe. The two-buffer-set
  rule of Component A guarantees one complete version on CXL at all times.

### 10.7 Generality check (supplementary)
On c35/c36 (DRAM + Optane PM, no CXL) the same policy fed PM's characteristics
(fast reads, slow writes) should choose the opposite: buffer writes in DRAM,
read PM directly.

### 10.8 Facts measured for this design, and what is still unverified
Measured 2026-09-18 (`hardware/results/2026-09-18-gpu-devdax-dma.log`,
RTX 4060 Ti, PCIe gen4 x8): `cudaHostRegister` on devdax works; GPU writes CXL
directly at 3.9 GiB/s (12.3 into pinned DRAM); GPU reads CXL at 12.5 GiB/s;
unregistered copies are staged through DRAM by the driver at 12.1 GiB/s.
TO VERIFY (needs the machine): probe latency vs real-application slowdown;
O_DIRECT from a devdax buffer; cause and scope (per GPU or per host bridge) of
the 3.9 GiB/s cap; promotion constants for KV-like CPU reads; segment waste
without compaction; CUDA registration cost and limits for large devdax ranges.
OPEN (discussion): third outlet to NVMe; which further LLM checkpoint engines.

### 10.9 Evaluation consequences (user decisions 2026-09-18)
One GPU on c28 yields ~12 GiB/s, about 4% of the socket's DRAM write capacity,
so a real single-GPU checkpoint shows function, capacity and drain behaviour
but not interference. Decision: (1) reproduce a multi-GPU node's aggregate
stream with CPU threads (stated as emulated in the paper) AND (2) use a
bandwidth-bound CPU-side victim from training itself (CPU optimizer step,
ZeRO-Offload style). **The application set is not fixed:** LULESH + VeloC is
an exploratory application and is replaced if its results are weak. Selection
criterion for any application: a victim that is DRAM-bandwidth-bound,
co-located with a real bulk write stream.

## Change history (append-only — never rewrite entries)
- **2026-05-20** — v1 designed and built: object registry, single-ceiling
  pressure model, benefit-per-byte greedy planner, lazy materialization, no
  migration. Evaluated same week (=manual ±1%, +14.3% vs interleave, +118% vs
  hotness-only, ~0.2% overhead). Original file: `archive/DESIGN_OBJPLACE.md`.
- **2026-08-25** — pivot to direction-aware placement (advisor-aligned): §7
  planned — per-direction budgets (DRAM write ×2, CXL duplex), `dir` attribute,
  NT staging API, LLM extension points as interfaces only. Build gated on
  `experiments/2026-08-25-direction-gates.md`. §3 marked v1-limited. Docs
  reorganized (this file created from `DESIGN_OBJPLACE.md`).
- **2026-08-25 (later)** — gates PASSED; §7 unblocked. Measured constants for
  the extension: DRAM {read 68.6, NT-write 54.9, plain-write ×2}; CXL pair
  {read 45.8, NT-write 43.8, joint frontier peaking 59.4 @12:4, co-location
  penalties −41% bw / 2.2× chase}. New design input: thread/CCD placement of
  write streams is part of the mechanism (fabric-port sharing). Build awaits
  user approval (W3).
- **2026-09-18** — §10 added (design-only, user-agreed direction): write-path
  runtime inspired by PolyStore — interception at VeloC staging / KV CPU pool,
  per-writer append-only logs on raw devdax CXL + segment index, epoch-based
  placement with objective "bounded slowdown of DRAM readers" (not total
  bandwidth) and per-device per-direction accounting from §7, read-in-place
  with conditional promotion, background drain CXL→NVMe, PM nodes as
  supplementary generality check. User ruling: finish the design before any
  experiment.
- **2026-09-18 (later)** — User correction: PolyStore is a source of ideas, not
  a comparison method. §10 reworded from "PolyStore does X, we differ by Y" to
  "borrowed from PolyStore / what memory changes". No design content changed.
- **2026-09-18 (design discussion 1)** — §10.2 decided provisionally with the
  user: reserve→commit as the only write primitive (plus lookup / release /
  copy_in / crash cleanup around it), 32–64 MB segments with per-thread
  append, shared segment table claimed by compare-and-swap with no middleman
  on the write path, no compaction in v1 (group by lifetime), no crash
  consistency.
- **2026-09-18 (design discussion 2)** — §10.3 decided provisionally with the
  user: three no-root signals with a DRAM latency probe, slow-increase /
  fast-decrease spill ratio with a configurable bound, adaptive probe rate +
  per-stream memory for short writes, blocking `reserve` when both devices are
  full. §10.3a added after the user required LLM-scale checkpoints (tens of
  GB): virtually contiguous multi-segment buffers become the normal path; GPU
  direct copy into devdax is the top feasibility risk.
- **2026-09-18 (feasibility check)** — GPU can register and write directly
  into devdax CXL (correct data, no DRAM bounce) but at 3.9 vs 12.3 GiB/s into
  pinned DRAM; GPU reads from CXL are full speed. §10.3a risk item replaced by
  this result; cause of the cap open. LLM checkpoint client: PyTorch async
  checkpoint confirmed by the user, others may be added later.
- **2026-09-18 (design discussion 3)** — §10.4 decided provisionally:
  read in place; promotion threshold from a rent-or-buy break-even formula
  (gives k≈5 with current numbers; user's provisional default k=2 until
  constants are re-measured); checkpoints never promoted; segment-wise O_DIRECT
  drain that yields to writers unless space is short. KV expiry changed from
  "discard" to "follow the client's policy, runtime offers drain" because
  LMCache / Mooncake / HiCache all keep an SSD tier.
- **2026-09-18 (design discussion 4 — walkthrough)** — §10.6 added: seven
  adjustments from tracing an LLM checkpoint and a KV block end to end (shared
  index owned by the node-level store; log segments vs reusable GPU buffer
  sets; path choice direct/staged for GPU sources with runtime-owned copy
  threads; drain target on reserve; allocator-level KV hook; per-consumer
  promotion constants — GPU consumers never promote; no IPC on the data path)
  plus the evaluation concern that one GPU on c28 yields only ~12 GiB/s.
- **2026-09-18 (consolidation)** — §10 rewritten as one consistent text
  (previous §10.2–10.6 patch list folded in, no decision dropped). New
  decisions: 32 MB segments; one machine-wide slowdown bound; initial policy
  constants (10/200 ms probe, 50 ms epoch, +1/16 increase, halve on 2 probes
  over 1.10× baseline); 10-minute read window; selective KV drain (read at
  least once while resident) pending trace analysis; evaluation uses emulated
  multi-GPU streams + a CPU-optimizer victim; LULESH+VeloC is exploratory only.
- **2026-09-18 (restructure)** — §10 regrouped in PolyStore's shape at the
  user's request: goals G1–G3 (each tied to a motivation observation) →
  principles P1–P4 → four components A–D (segment store, placement, read path,
  drain and recovery). Content unchanged except the added Recovery paragraph.
- **2026-09-18 (trace analysis)** — Selective KV drain removed from Component
  D: refuted by `experiments/2026-09-18-kv-selective-drain.md`. KV drain follows
  the client's policy unchanged.
