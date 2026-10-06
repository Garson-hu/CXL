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

### 10.1 Goals and principles (draft of the paper's §4.1 — WHAT we want, for WHICH problem)
*Writing rule (user, 2026-09-21; PolyStore's technique): what we want to build and
the existing problem it answers are said HERE (and in the paper's introduction and
motivation). The component sections that follow say HOW only. Principles are
requirement statements; each is realised by exactly one component.*
- **Goal 1 — keep bulk writes off DRAM by default, without slowing the producer.**
  Answers: keeping such data in DRAM slows DRAM readers (O2); CXL is a safe
  destination (O3); neither "everything to CXL" nor a rate-limited "everything to
  DRAM" serves the producer (the three simple policies of `PAPER.md` §3).
  *P1: a direct, copy-free write path onto raw CXL.* Writers in many unprivileged
  processes must obtain space on a raw devdax device and fill it in place: no
  staging copy, no system call and no central allocator on the data path.
  (Challenge answered: a devdax device has neither allocator nor file system.)
  → Component A.
  *P2: interference-bounded, capacity-aware placement.* Placement must follow the
  CXL write capacity it measures and lend DRAM to writers only while other DRAM
  readers stay within a configured slowdown bound; it must react within tens of
  milliseconds and use no privileged counters. → Component B.
- **Goal 2 — spend DRAM where reading benefits.**
  Answers: most written data is never read again, a minority is (O1).
  *P3: read in place, promote by break-even.* Data is served from where it lies;
  a copy into DRAM is made only when the expected saving exceeds the cost of the
  copy, including the harm the copy does to other DRAM readers. → Component C.
- **Goal 3 — do not compromise what DRAM staging provides.** Data still reaches
  NVMe in the client's format, stays findable after its writer dies, and frees
  its space without the client's help.
  *P4: DRAM-free drain and node-owned metadata.* The path to NVMe must not pass
  through DRAM or the page cache, and the index must belong to the node, not to
  the writing process. → Component D.

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
  c28 scatter 100–160 ns). Headroom guard (revised 2026-09-22, §10.11 item 14):
  reference > 1.3 × the machine's UNLOADED probe level (median of 200 probes taken over 2 s at
  daemon start, or `--idle-ns`) ⇒ nothing may spill — this is what separates a victim that leaves
  headroom (probe ≈ unloaded) from a saturated one (probe ≥ 1.45× unloaded), which a relative bound
  cannot do. Increase +1/16 per epoch when the
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
10. **A key names ONE object (found by the all-clients run).** Every rerun of a
    checkpointing application writes "version 3" again; without a rule each
    rerun left one more 92 MiB object that is never older than the newest, so
    the store filled up (361 objects, 32 GiB), KV stores failed and LULESH sat in
    back-pressure; a lookup could also have returned the stale copy. Now
    beginning an object under an existing key supersedes the old one: its drain
    stops at once (the new writer owns the target file), it stays readable until
    the new object commits, then it is released; lookups return the newest
    generation; if the new writer dies, the old object is THE object again and
    its drain resumes. An object that owns its file is truncated to its size.
11. **A pin names the pinned object, not the key** (`cxlp_pin_t` = slot +
    generation), otherwise a reader that pinned before a supersede would unpin
    the new object and the old copy would never be released.
12. **Clients link the SHARED library and must not fall back silently.** The
    VeloC client once carried a static copy of an older libcxlpath, failed the
    metadata-layout check, fell back to stock VeloC, and one all-clients run
    measured stock VeloC without anybody noticing. Now: layout mismatch is an
    immediate explicit error, VeloC links `libcxlpath.so`,
    `VELOC_CXLPATH_REQUIRED=1` aborts instead of falling back, and the gates
    prove the path (objects listed on CXL, scratch directory stays empty).
13. **Preparing the policy experiment (2026-09-22) forced three daemon/store fixes:** (a) the DRAM
    pool is pre-allocated and mapped populated — with first-touch 4 KiB faults (tmpfs; shmem THP needs
    root) a spilled chunk was ~5× slower than a CXL chunk and cxlpath ran below all-CXL; pool trimming
    is opt-in now; (b) the slack rule ignores the tail epoch of a burst and an idle stream remembers the
    ratio it ran with while CXL was loaded (periodic bursts lost their ramp to tail-off decrements);
    (c) the active reference is fed only by epochs with CXL bytes (burst tails fed it idle values and
    the next burst started with halvings). Also `--margin`. Known property: with per-chunk spill and a
    fixed producer thread pool, CXL loses saturation as the spill grows, so the ≥ 90%-of-capacity
    "full" signal self-limits the spill; a producer with spare threads is needed for the loan to show.
14. **The headroom guard decides the regime (phase-2 finding, 2026-09-22).** A probe bound maps to a
    victim's slowdown by a factor that depends on the victim (a 10% probe rise ≈ 7% for a streaming
    reader, ≈ 19% for a CPU Adam step, ≈ 30% for PageRank), and beside a saturated victim the probe's
    scatter (p90/p50 ≈ 1.045) exceeds the signal of a 7% bound. With the guard at its original 2.0×,
    cxlpath lent DRAM beside PageRank and llama.cpp and hurt them 2–3× more than all-CXL. The absolute
    probe level separates the regimes (135 ns idle and beside a moderate reader; ~200 ns beside PageRank
    and llama.cpp; 262 ns beside the Adam step), so the guard is now **1.3× the unloaded level**, and
    that level is **calibrated over 2 s at daemon start** (`--idle-ns` overrides it when the daemon
    starts on a loaded machine) instead of being the lowest windowed reference ever seen. Result: the
    loan goes only to victims that leave headroom; beside saturated ones cxlpath = all-CXL.
15. **Producer pacing as the last resort (built 2026-09-22, commit 95e4a54).** cxlpath decides WHERE
    writes go; beside a read-saturated victim the SOURCE reads of a copy alone exceed a 7% bound (all-CXL
    costs llama.cpp 10%, PageRank 14%), and the only remaining lever is the copy rate. Rule: when no DRAM
    is being lent and the 50-epoch probe mean has been above bound × the calibrated idle level for two
    consecutive epochs, the daemon publishes a per-stream token bucket (policy page: `pace_on`,
    `pace_tokens`, `pace_bps`) at 0.75 × the achieved CXL rate; every further two epochs over the bound
    multiply the rate by 0.75, calm epochs (below margin × idle) add 1/16 of the CXL capacity, reaching
    the capacity switches pacing off; floor 1/32 of the capacity. `reserve` waits for tokens (200 µs
    sleeps); refills are per daemon tick, capped at 100 ms worth. `--no-pace` disables it. Measured
    (2026-09-22-moderate-pacing-dcp.md): it works where the probe is clean (Adam step on 32 threads:
    10.2% → 7.4% at 1.27× the completion time) and is marginal beside llama.cpp / PageRank on 80 threads,
    whose own phases move the probe mean by more than a 1.06× bound — a limitation to state: the probe
    is a proxy for the victim's slowdown, not a measurement of it.
16. **Not built:** per-client space quotas (one client's garbage can still
    starve the others of space — the F1 failure made that visible);
    DTensor/ShardedTensor support in the PyTorch plugin; a real
    LMCache integration (E3 is a trace-driven stand-in with the same call
    pattern); compaction; the PM configuration (§10.7).
17. **Parallel NT copy for CPU tensors in the PyTorch plugin (2026-09-22).** `cxlp_copy_in_par(dst, src,
    n, nthreads, cpus)` splits a copy over pinned threads; `CxlpathWriter` uses it for CPU-resident
    tensors (`copy_cpus=` or `CXLPATH_COPY_CPUS`), because one core cannot fill the CXL pair from a
    Python process the way the C producer's 8 threads do (measured 42 GiB/s with 8 pinned threads).

18. **Read path v2 — promotion is a copy, demotion is free (2026-10-06).** `cxlp_promote_pending` no longer relocates
    an extent: it copies it into the DRAM pool and records a *shadow* (`sh_dev/sh_seg/sh_off`, last-hit time, hit
    count) on the extent; `pin`/`lookup` return the shadow while it exists, the drain keeps reading the CXL original.
    `cxlp_shadow_trim(target)` drops least-recently-hit shadows (object granularity; an object with a `group` takes its
    whole group — a KV prefix chain is read together) by releasing DRAM space only: no write, and the extent's read
    counts restart so a dropped shadow needs fresh evidence. Shadows are capped (`--shadow-cap-gib`, default half the
    pool) and trimmed by the daemon when the pool's free segments fall below 1/8 so the loan is never blocked by
    copies. k per class: `CXLP_OBJ_LATENCY` objects (serving hits) promote at `--k-latency` (default 1) reads,
    bulk objects at the measured break-even k, GPU consumers never while DRAM is not faster for them.
    `cxlp_obj_prefetch(key)` queues an object without a read (the client's guess, e.g. a session's next turn).
    Reason: the advisor's "later reads are slow reads" question and the trace analysis of 2026-10-06 — with k = 3
    no KV block was ever promoted, and a relocation could not be undone without a write.
19. **CXL capacity is measured, not calibrated (2026-10-06).** "Full" compares the epoch's CXL write rate with the
    highest rate seen in the last 10 s of active epochs (capped by the start-up calibration), because the rate CXL
    can take depends on the co-runner (29 GiB/s beside llama.cpp, 44 alone); the constant rule never saw "full"
    beside llama.cpp-32 and lent nothing although the probe showed headroom. **The loan must pay:** the ledger's
    per-device copy times give a per-chunk rate for DRAM and CXL; two consecutive epochs in which DRAM chunks were
    slower than CXL chunks (beside llama.cpp: 22 vs 30 GiB/s) hand the loan back, whatever the probe says.
20. **The drain does not yield to writers (2026-10-06).** The former "give way while CXL writers moved bytes in the
    last 100 ms" rule was a DRAM habit: reads use the other direction of the link and the drain's NVMe-bound rate is
    a few percent of the write direction; the rule only delayed durability and had to be repaired by the
    urgent/overdue rules. Kept: buffer sets that gate a blocked writer first, and the low-space rule.
21. **PyTorch plugin: CPU tensors are objects (2026-10-06).** `cxlp_put_par` cuts a tensor into segment-sized chunks
    that pinned threads reserve / NT-copy / commit one by one — placement per chunk, so the DRAM loan applies to the
    real producer — and the objects drain into one file per checkpoint at increasing offsets (version chain per rank:
    older versions are reclaimed by the runtime once the newer is durable). The reader pins the object (CXL or its
    DRAM copy) and falls back to the file. GPU tensors keep the CUDA-registered buffer set. Reason: beside moderate
    victims the plugin had been "all-CXL" by construction (`2026-09-22-moderate-pacing-dcp.md` item 3).

### 10.12 Multi-tenant arbitration (DESIGNED 2026-10-06, not built)
A node runs several writers (streams) beside several readers (tenants). A stream carries a class (checkpoint or KV),
a weight and a space quota; the daemon arbitrates six shared resources:
1. **Who may still be hurt.** One latency probe per CPU group that hosts a DRAM-reading tenant (each costs ~1.3% of a
   core); the loan and the promotion copies are bounded by the most sensitive tenant (the lowest headroom over its own
   idle level); a tenant can declare itself indifferent, and its probe is then ignored.
2. **The DRAM loan.** The sum of all streams' DRAM write rates stays under what the governing probe allows; inside
   that budget the streams share by weight (weighted max-min: unused share flows to the others).
3. **CXL write capacity.** Latency-class streams (KV ingest) have priority: while one is active, bulk streams are paced
   with the existing token buckets to leave it headroom.
4. **CXL readers vs writers.** A full write stream costs a CXL reader 41–51% of its bandwidth (2026-08-25,
   2026-09-02); while latency-class reads (KV hits) are active, bulk writers are held below a measured fraction of the
   CXL capacity (the curve "writer rate → reader loss" is to be measured first; the working guess is 70%).
5. **Space.** Per-stream quotas on CXL segments and on the DRAM pool (loan + shadows); a stream over quota evicts its own
   oldest data (KV: oldest blocks; checkpoints: waits for its previous version to drain) and never another stream's.
   This replaces the ad-hoc rules that followed the F1 starvation (item 16).
6. **The drain.** Round-robin over streams, checkpoint versions before KV (durability is what checkpoints are for).
Evaluation: two producers (a checkpoint burst and a continuous KV ingest) beside two victims (one sensitive, one not);
the governing probe, the weighted split of the loan, the priority of KV ingest over the burst, and a stream over its
quota that cannot starve the others.

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
  API / tests, §10.11 the differences between the agreed design and the built
  system with the evidence that forced each (probe references, fullness and
  slack rules, runtime-side reclaim, non-starving drain, DCP storage format,
  VeloC patch, k = 3). Build record: `experiments/2026-09-08-write-tier-campaign.md`.
- **2026-09-21** — §10.1 wording aligned with the restructured motivation of
  `PAPER.md`: Goal 1 is "off DRAM by default" and takes P2 from the three-strawmen
  argument; Goal 2 derives from the flip side of O1; Goal 3 / Component A are
  introduced by the raw-devdax challenge. No design content changed.
- **2026-09-21 (second round)** — §10.1 rewritten in the register of PolyStore's
  §4.1 (goals; principles as requirement statements; each names the finding or
  challenge it answers) so that it can serve as the draft of the paper's §4.1.
  The paper's component sections will say HOW only; this file keeps the
  engineering rationale (§10.11). No design content changed.
- **2026-09-22** — §10.11 item 13: DRAM pool pre-allocated/populated (no faults on the data
  path), burst-tail fixes in the controller and the active reference, `--margin`; trimming opt-in.
- **2026-09-22 (later)** — §10.11 items 14–15: headroom guard 1.3× a calibrated unloaded probe level
  (was 2.0× the lowest windowed reference), `--idle-ns`; producer pacing recorded as not built.
- **2026-09-22 (night)** — §10.4 AS BUILT paragraph updated to the revised headroom guard.
- **2026-09-22 (late night)** — §10.11 item 15 rewritten: producer pacing is BUILT (token bucket in the
  policy page, daemon pacing controller, `--no-pace`), with its measured reach and limitation; item 17
  added: parallel NT copy for CPU tensors in the PyTorch plugin.
- **2026-10-06** — §10.11 items 18–21: read path v2 (shadow copies, free demotion, groups, k per class, prefetch),
  measured CXL capacity and the loan-must-pay rule, the drain no longer yields, CPU tensors as objects in the PyTorch
  plugin; §10.12 multi-tenant arbitration designed (not built). All from the advisor's review of 2026-10-04 and the
  user's decisions of 2026-10-06.
