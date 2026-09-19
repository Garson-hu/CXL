# System Design (current)

*The one document that always describes the system as it exists now.
History: `## Change history` at the bottom (append-only). Predecessor file:
`archive/DESIGN_OBJPLACE.md` (2026-05-20 original, verbatim).*

**Status 2026-08-25:** ObjPlace v1 (below) is built and evaluated
(`experiments/2026-05-19-baseline-objplace.md`). The per-direction extension
(§7) is DESIGNED-ONLY, gated on the experiments in
`experiments/2026-08-25-direction-gates.md`.

**Status 2026-09-19:** §10 (write-path runtime `cxlpath`, PolyStore-inspired) is
BUILT: `system/cxlpath/`, all steps of the build plan passed their gates
(`experiments/2026-09-08-write-tier-campaign.md`, "Phase 5 v2"). §10.10 maps the
code, §10.11 lists every point where the built system differs from the design
agreed on 2026-09-18, and why. No evaluation experiment has been run yet. §1–§9
describe the older ObjPlace v1 code, which cxlpath does not use.

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

## 10. Write-path runtime `cxlpath` (design consolidated 2026-09-18, BUILT 2026-09-19)
*The design text below was agreed with the user on 2026-09-18. It is now built;
paragraphs marked **AS BUILT** say what the code does where that differs from or
sharpens the design (summary in §10.11). Motivation and paper framing:
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

**AS BUILT (A).** Metadata lives in `/dev/shm/cxlpath.<store>` (segment table,
object hash table, extent pool, buffer-set table, drain descriptors, policy
page); a store owns a configured range of each dax device plus a tmpfs file as
DRAM pool. Every way back to FREE passes an exclusive FREEING state (the stress
test found an owner/free ordering bug). Reserved bytes count as live at once;
`cxlp_shrink` returns the unused end of a reservation. Objects: open-addressing
hash, one writer per object, readers pin. The library adds 82 ns per
segment-sized write (0.011% of the copy time) and makes no system call on
reserve → copy → commit → release (strace: 0). Object table default = 8 slots
per segment (objects of tens of MiB); smaller objects need `obj_slots`.

### 10.4 Component B — interference-bounded placement (P2; analogue: Poly-placement)
Borrowed: measure every short epoch, then reassign. We reassign segments, not
threads, and the objective is not the sum of bandwidths but: **make the write
stream as fast as possible while other DRAM readers slow down by no more than
one machine-wide bound** (user decision: one global bound).
- **Signals (no root).** (1) Own ledger: bytes and copy time per device and per
  stream, fed by `cxlp_copy_to` / `cxlp_account`. (2) Fullness of the CXL write
  direction = ledger throughput versus the capacity calibrated at start-up (the
  per-thread "achieved vs solo speed" test borrowed from PolyStore over-spilled
  and was dropped, §10.11). (3) DRAM latency probe in the background process: ~1000
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
- **Parameters and signals AS BUILT (values tunable; the live gates forced
  several changes, see §10.11).** Probe: 1000 dependent loads every 10 ms while
  writers are active, every 200 ms when idle; it costs 1.26% of one core. Epoch
  50 ms active / 200 ms idle. **Reference level = MEDIAN of epoch means, two of
  them:** idle (60 s window) and active (2 s window, fed only by epochs with
  writer activity and none of our bytes in DRAM; frozen while we spill; known
  after 5 such epochs, so a first burst spends ~250 ms on CXL only). Bound =
  1.10 × the reference in use; idle state uses a loose 1.5× (idle readings on
  c28 scatter 100–160 ns). Headroom guard: reference > 2.0 × the lowest idle
  reference ever seen ⇒ nothing may spill. Increase +1/16 per epoch when the
  CXL write direction is FULL = our own ledger shows ≥ 90% of the capacity
  calibrated at start-up (43.9 GiB/s) AND probe ≤ 1.05 × reference. **Slack rule
  (new):** below 70% of the capacity the ratio shrinks by 1/16 per epoch — DRAM
  is only for the excess. Decrease: halve on 2 consecutive probes over the bound.
  Per-stream memory (16 streams): an idle stream keeps its ratio published, it
  is halved by pressure while idle, and a burst restores it unless DRAM is under
  obvious pressure. Measured: spill settles at 6/16 for a 60 GiB/s demand (CXL
  37 + DRAM 20 GiB/s, probe 131 vs reference 130, no halving); first halving
  16 ms after an injected DRAM aggressor, spill 0 after 46 ms. GPU sources: the
  direct path counts as full when it delivers < 80% of the calibrated link speed;
  measured 3.91 (direct) vs 12.16 GiB/s (staged), share 0.95 when DRAM is calm,
  0.00 under the aggressor. One unthrottled core already pushes 41 GiB/s = 94%
  of the card pair's write capacity.
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

**AS BUILT (C).** `cxlp_obj_pin/unpin`; counts are per EXTENT, so a ranged pin
promotes only what it reads; w = 10. Calibrated on c28 (single-thread streaming,
128 MiB): DRAM 40.8 GiB/s, CXL 23.0 GiB/s (1.77×), copy CXL→DRAM 23.5 GiB/s ⇒
**k = 3 when DRAM is calm** (the k ≈ 5 above came from the stencil proxy's 1.2×);
GPU consumer 12.45 vs 12.46 GiB/s ⇒ never. A promoter thread in the daemon
relocates under the object's seqlock; the old CXL copy is released once no
reader pins the object; `release` is refused while pinned.

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

**AS BUILT (D).** O_DIRECT from a devdax mapping works (V1); 4 KiB-aligned body
direct, sub-4 KiB tails buffered; files byte-identical for awkward sizes; a
buffer set drains only its used prefix. **The NVMe on c28 sustains 0.90–0.92
GiB/s whatever the parallelism**, so one drain thread is enough and a 32 GB
checkpoint needs ~36 s to become durable. Pacing: yield while CXL writers moved
bytes in the last 100 ms, EXCEPT when free CXL space is below 25%, when a writer
is blocked until a drain completes, or when work has been pending for more than
2 s (durability lag bound) — "yield while anybody writes" starved the drain in
the first all-clients run. **Checkpoint versions form chains and are reclaimed
by the RUNTIME** (on NVMe + a newer version committed): a producer blocked in
`reserve()` cannot release anything itself. Writers keep 99.7% of their speed
with a drain running beside them (43.89 → 43.76 GiB/s). KV selective drain stays
removed (trace analysis).

### 10.7 Generality check (supplementary)
On c35/c36 (DRAM + Optane PM, no CXL) the same policy fed PM's characteristics
(fast reads, slow writes) should choose the opposite: buffer writes in DRAM,
read PM directly.

### 10.8 Facts measured while building, and what is still unverified
Verified 2026-09-19 (`experimental_results/2026-09-19-cxlpath-build/`): GPU →
devdax works, direct writes 3.9 GiB/s vs 12.3 into pinned DRAM, GPU reads CXL at
12.5 GiB/s; O_DIRECT from devdax; scattered segments stitch into one buffer that
CUDA registers (~20 ms per GiB, 200 GiB ok); PyTorch 2.5.1 `async_save` accepts
our staging; the DRAM latency probe tracks a reader's slowdown monotonically
(1.18× at −13%, 6.5× at −92%); promotion constants for a CPU consumer; the
library's write-path overhead.
STILL OPEN: cause and scope (per GPU or per host bridge) of the 3.9 GiB/s cap —
registration flags, mapped copies and two devices change nothing; segment waste
without compaction under a long KV run (the three trace replays ended with every
segment free, but waste over time was not measured); another tenant writing to
the same cards outside cxlpath is invisible to the fullness signal; third outlet
to NVMe; a real LMCache integration (needs vLLM; ⏳ user decision).

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

### 10.10 As built — code map, API, tests
`system/cxlpath/`: `include/cxlpath.h` (client API), `include/cxlpath_daemon.h`
(probe, controller, references), `include/cxlpath_gpu.h`; `src/` store.c
(devices, segment table), reserve.c, object.c (index, crash cleanup), bufset.c,
policy.c (library side of B), probe.c, controller.c, readpath.c, drain.c,
stream.c (file-style shim), gpu/gpu.c; `daemon/cxlpathd.c` (probe loop +
promoter thread + drain thread); `clients/veloc/` (patch + round-trip helper),
`clients/pytorch/cxlpath_dcp.py` (DCP StorageWriter/AsyncStager + StorageReader).
API groups: store (`cxlp_open/attach/close/destroy`); segments; reservations
(`cxlp_reserve/commit/abort/release/shrink`, `cxlp_copy_in`, `cxlp_copy_to`,
`cxlp_account`); objects (`cxlp_obj_begin/append/commit/lookup/release`,
`set_flags`, `set_drain`, `set_version`, `cxlp_put*`, `cxlp_get`); read path
(`cxlp_obj_pin/unpin`, `cxlp_read`, `cxlp_k_compute`); buffer sets
(`cxlp_bufset_create/map/begin/commit/commit_drain/set_used/drained/newest/
version/destroy`); streams (`cxlp_stream_create/write/close/abort`,
`cxlp_chain_newest`, `cxlp_key_of`); GPU (`cxlp_gpu_init/register/copy_in`);
policy view (`cxlp_policy_view/force`).
Tests: `make test` (sparse files in /dev/shm as devices, plus an strace check of
the data path) and `make test-dax` (first 8 GiB of dax0.0 + dax1.0, which the
tests own); live gates in `tests/live/` (b_live.py, b5_live.py, c_live.py,
d_live.py, e1_veloc.sh, e3_kv.sh, f1_all.sh) need a quiet c28 and write their raw
output under `experimental_results/2026-09-19-cxlpath-build/`.

### 10.11 What changed versus the design agreed on 2026-09-18, and why
1. **Probe reference = median, not minimum; two references (idle / active).**
   An idle c28 reads 100–160 ns from probe to probe; a minimum sat 15–25% below
   typical and made normal readings look like pressure. The writers' own source
   reads (50 GiB/s from DRAM) lift the probe ~20% with zero spill, so the level
   "without our DRAM writes" must be learned during the burst.
2. **Idle state uses a loose bound (1.5×); headroom guard (2.0×) added.** The
   guard implements "spill only while DRAM has headroom" in absolute terms; the
   10% bound is relative ("no more than X because of OUR writes").
3. **CXL-full signal = ledger vs calibrated capacity; slack rule added.** The
   per-writer-speed test raised spill to 11/16 for a 60 GiB/s demand; with
   capacity thresholds it settles at 6/16, and spill now shrinks when CXL has
   slack. A single core saturates the pair (41 of 44 GiB/s).
4. **Reclaiming drained checkpoint versions is done by the runtime** (version
   chains). The first 10-version loop hung: a producer blocked in `reserve()`
   cannot release its own old versions.
5. **The drain never yields indefinitely** (space low, a blocked writer, or
   pending > 2 s). With a KV layer writing all the time the drain never ran and
   a PyTorch checkpoint waited a minute for a buffer set.
6. **PyTorch: own storage format behind the DCP plugin interface** (raw buffer
   set + small metadata, `CxlpathReader` for loading) instead of reproducing
   `.distcp` files — that would have cost a CXL→CXL serialisation copy.
7. **VeloC: a 193-line patch of the client** (`VELOC_CXLPATH_STORE`), applied to
   the project's copy `~/apps/veloc-src`; drained files are byte-identical to
   stock VeloC's, so stock VeloC restarts from them.
8. **Promotion unit = extent; k = 3 on c28** (design said ≈ 5 from a 1.2×
   penalty; a single streaming reader sees 1.77×).
9. **Smaller points:** FREEING segment state; `cxlp_shrink`; buffer sets drain
   their used prefix; `obj_slots` for small objects; the daemon's log is
   buffered (NFS writes stretched 50 ms epochs to 150 ms); the write-path
   overhead gate is deterministic (82 ns per segment) because throughput
   comparisons at the device limit vary by ±15% on this machine.
10. **Not built:** DTensor/ShardedTensor support in the PyTorch plugin; a real
    LMCache integration (E3 is a trace-driven stand-in with the same call
    pattern); compaction; the PM configuration (§10.7).

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
- **2026-09-19 (as built)** — §10 updated from "planned" to "built": AS BUILT
  paragraphs per component, §10.8 facts/open points refreshed, §10.10 code map /
  API / tests, §10.11 ten differences between the agreed design and the built
  system with the evidence that forced each (probe references, fullness and
  slack rules, runtime-side reclaim, non-starving drain, DCP storage format,
  VeloC patch, k = 3). Build record: `experiments/2026-09-08-write-tier-campaign.md`.
