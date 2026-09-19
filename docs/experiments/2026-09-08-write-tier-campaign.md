# 2026-09-08 — CXL write-tier campaign: plan + TODO (umbrella, ACTIVE)

**STATUS: ACTIVE — this is the campaign-level plan the user laid out on
2026-09-08. It stays open until all phases close; each phase that runs gets its
own dated experiment file and an INDEX row, and its status is updated HERE.**
Rule for future sessions: read this file first; do not re-plan from scratch.
Thesis under test: `../PAPER.md` Thesis v2 (CXL as a write-preferred tier),
now to be validated end-to-end and enriched with PolyStore (FAST'25).

## Machine facts that shape the plan (verified 2026-09-08)
- c28: DRAM node 0 (773 GB) · **Pair A** = mem0 (e1:00.0) + mem2 (c1:00.0) as
  `/dev/dax0.0` (242.5 GiB devdax, root:kmem) AND `dax1.0` (269.5 GiB, = NUMA
  node 1) — SAME two cards, not independent · **Pair B** = mem1 (01:00.0) +
  mem3 (02:00.0) as `/dev/dax2.0` (512 GiB devdax, root:kmem).
- Per-card selection: **Pair B only**, via 256 B parity classes
  (`card=(off>>8)&1`, `2026-09-01-pairb-address-map.md`); measurement
  instrument, NOT app-usable (stripe finer than a page). **Pair A is hashed**
  (`2026-09-08-paira-interleave-hash.md`) — pair granularity only.
  Achievable device counts: 1 card (Pair B class) · 2 cards (Pair B) ·
  4 cards (Pair B + Pair A). **3 cards impossible.**
- **DRAM is currently crippled**: BIOS Memory/Chipselect Interleaving =
  Disabled → 25–41 GiB/s @32T (was 94.6), CXL is faster than DRAM
  (`hardware/results/2026-09-08-dram-interleave-regression.log`). Everything
  marked 🔴 below waits for that BIOS revert.
- NVMe on c28: Solidigm D5-P5430 3.84 TB at `/mnt/local` (ext4, 3.3 TB free);
  Samsung 894 GB = OS. **No persistent memory on c28.** PM lives on **c35/c36**
  (Cascade Lake, 192 GB DDR4, 1 TB Optane DCPMM as KMEM-DAX NUMA nodes 2+3,
  `-p cascade`, no CXL) — a second testbed for the PolyStore-style tier
  comparison, not a substitute for c28.
- Standing method rules: `METHODOLOGY.md` (victim/aggressor on separate CCDs,
  NT stores on the write side, median of ≥3, DRAM control beside every CXL
  number, raw data under `experimental_results/<same-basename>/`).

## Phase 1 — Why a DRAM reader drops 68.6 → 10.9 GiB/s under NT writers
**Deliverable A (analysis, 🟢 no machine needed):** written answers to
(1) how a DDR controller handles reads vs writes; (2) separate read/write
queues — yes; (3) shared resources — one half-duplex DQ bus, banks, scheduler;
(4) write-drain mode (write queue above high watermark → controller drains
writes in batches, reads wait) + tWTR/tRTW turnaround bubbles; (5) why NT
stores are worst: full-line, RFO-free, continuous writes keep the queue above
the watermark permanently (evidence already in hand: plain stores 4.1× vs NT
6.3×; 2 NT threads suffice — `2026-08-25-gate2-verification.md`);
(6) verification: `amd_umc_*` PMUs (CAS read / CAS write counts per UMC),
`amd_df`; blocked by `perf_event_paranoid=2` → admin ask.
**Deliverable B (experiment, 🔴 after BIOS revert):** matrix read-only /
write-only / read+write × writers {1,2,4,8,16} × {normal, NT} store; reader 4T
on CCD0, writers on CCD1; report reader BW, writer BW, sum vs pipe ceiling,
reader latency; add UMC CAS ratios if counters are granted. 3 reps.
File when run: `2026-09-XX-dram-write-drain.md`.

## Phase 2 — Can we select cards, and how does CXL bandwidth scale with cards?
**Five answers (🟢 already established, to be restated in the phase file):**
(1) yes — single card on Pair B via parity class (instrument only), pair-level
via contiguous mmap on dax0.0/dax2.0 (app-usable); (2) confirmed: Pair B stripe
rule + uniformity, Pair A hash, pair independence, Pair B card isolation,
single-card 23.9 / pair ~45 GiB/s; (3) missing: which class = which PCI card
(labels; needs root counters/telemetry; cosmetic); (4) system-ram suffices for
DRAM-vs-CXL(pair) placement via node 1, but node 1 shares hardware with dax0.0;
(5) devdax adds deterministic pair choice, per-card classes, NT-staging target,
and two pairs usable at once.
**Experiment (🟢 runnable now):** aggregate scaling for 1 / 2 / 4 cards ×
{read, NT-write, read+write at 3:1, 1:1, 1:3} × threads {4, 8, 16, 32};
locate the bottleneck: card link (~24/card), host bridge (Pair B 44.3 vs
2×23.9), CPU fabric (CCD port). DRAM read+write control 🔴.
File when run: `2026-09-XX-cxl-card-scaling.md`.

## Phase 3 — Stencil / pond simulation (application-like)
**Design (🟢 build now):** 3 buffers old/current/new, 8 GiB each (≫ 256 MB
L3); per step: read old + current → compute (5-point average + tunable FLOPs)
→ write new. Knobs: threads, per-buffer placement {dram, node1, dax0.0,
dax2.0}, store type {normal, NT}, steps. Records: per-step time, DRAM read BW,
CXL write BW. Case A all-DRAM; Case B new on CXL.
**Rotation problem (the real question):** next step's current = last step's
new → a CXL READ (45 vs ~95 healthy DRAM, and −41% under same-pair writes).
Strategies to implement and compare: static (fixed roles + copy-back),
pointer rotation (expected worst — control), ping-pong (two CXL write targets,
reads always from DRAM copy), migration (`obj_stage_in`-style async NT copy
CXL→DRAM overlapped with compute), multiple devices (write to Pair B while
reading last step from Pair A, alternate pairs — c28-unique).
Metric: steady-state per-step time over ≥20 steps, each strategy vs Case A.
Status: 3a code ✅ · 3b discarded (crippled DRAM) · 3c ✅ DONE 2026-09-14 (see `2026-09-14-stencil-3c.md`).
File: `2026-09-XX-stencil-write-tier.md`.

## Phase 4 — Real applications: LULESH + checkpoint (VeloC)
**4a object analysis (🟡, needs LULESH version confirmed — default LULESH 2.0
OpenMP):** classify arrays by measured R/W ratio + reuse distance (instrument
allocations; IBS/`perf mem` if permitted). Prior expectation: read-mostly
(nodal mass, connectivity, constants) → anywhere; write-then-immediately-read
(fx/fy/fz, `*_elem` temporaries) → NOT CXL; write-mostly / long-idle
(history fields, output fields, checkpoint snapshots) → CXL; RMW streams
(coords, velocities, accelerations) → duplex candidates, latency-sensitive —
measure. VeloC: write-once-read-on-restore staging buffers = ideal (Gate 2b).
**4b (🔴):** all-DRAM vs DRAM+CXL placement; then policy extraction:
`write-heavy ∧ low immediate reuse ∧ DRAM-bandwidth pressure → CXL`.
Files: `2026-XX-XX-lulesh-objects.md`, `2026-XX-XX-lulesh-placement.md`,
`2026-XX-XX-veloc-staging.md`.

## Phase 5 — PolyStore (FAST'25, Ren et al.) integration
PolyStore: storage media are "non-hierarchical"; use PM + NVMe *horizontally*
(concurrently) for cumulative bandwidth via a userspace POSIX-intercept
runtime + thin VFS layer (PolyOS); 1.11–9.38× micro, 1.52–2.02× apps.
**What it leaves open, and where we land:** (1) the same horizontal philosophy
at the MEMORY tier (DRAM + CXL), plus an axis PolyStore lacks — traffic
DIRECTION (duplex link, 2× DRAM write tax, async stores); (2) inter-device
interference/isolation (our card/pair data); (3) CXL as a staging tier between
memory and storage: DRAM →(NT)→ CXL →(drain)→ NVMe, the VeloC shape — a
combined-bandwidth checkpoint path; (4) borrow PolyStore's transparent-placement
interface idea (intercept layer) to answer "apps can't allocate this way".
Testbeds: c28 (DRAM/CXL/NVMe) primary; c35/c36 (DRAM/Optane PM) for a
PM-vs-CXL tier comparison if useful. ⏳ needs the PDF (read full text before
designing experiments) and Phase 4 checkpoint numbers.


## Phase 4 plan v2 — PROPOSED 2026-09-09 (user chose anchors A + B; C = optional probe)
**A. Checkpointing (rank 1)**
- A1 LULESH + VeloC: build LULESH 2.0 OpenMP (`SERCXX`, no MPI); baseline `-s 160 -i 100`
  (3.9 GB) at 16/32 threads with a per-step timer patch; protect the state arrays with
  `VELOC_Mem_protect`, checkpoint every 10 steps. VeloC: try the user's branch (deps: Boost,
  OpenSSL, MPI, er, axl, cereal — 1-day cap); fallback = a VeloC-shaped emulator (regions →
  scratch via pwrite/memcpy + async drain thread, same data path). Scratch placements:
  DRAM (`/dev/shm`), CXL node 1 (tmpfs `mpol=bind:1` if mountable; else test whether a
  `numactl --membind=1` writer lands tmpfs pages on node 1), `/dev/dax2.0` direct NT copy
  (= `obj_stage_out`). Persistent = `/mnt/local` NVMe. Metrics: step time during vs
  between checkpoints, checkpoint + drain time, with/without a DRAM-pressure aggressor.
  Comparison numbers need healthy DRAM (🔴 until then; CXL-side + build now).
- A2 `torch.save`-shaped optimizer snapshot: CPU emulation of a training loop — fp32
  params + Adam m/v (1–2 B params → 12–24 GB), each step = RMW update (DRAM-bound), every
  K steps serialize state to scratch {DRAM, CXL}. Same experiment shape, ML flavor; sets up
  (C) if wanted. torch 2.5.1 (dpu_torch env) available.
**B. KV-cache eviction / prefix insertion (rank 2)**
- B1 trace-driven KV traffic model (1–2 days): from ShareGPT / Mooncake (/ LMSys if token)
  traces derive per-session prefill sizes, turn gaps, reuse distances; convert to KV bytes
  for Llama-3.1-8B (≈128 KB/token fp16) → eviction + insertion GiB/s at target concurrency,
  and the "written-never-read" fraction. Decides headline vs extension.
- B2 KV-pool microbenchmark (no model): vLLM/LMCache-shaped CPU KV pool — prefill writes
  KV blocks (NT) to {DRAM, dax2.0, dax0.0}, later turns read them back into DRAM staging;
  driven by trace arrivals; plus a "decode" DRAM reader victim (Gate-2b shape). Metrics: pool
  write/read throughput, read-back latency, victim slowdown.
- B3 real serving only if B1/B2 justify: vLLM + LMCache (or SGLang) with the CPU pool on
  our placement, Llama-3.2-3B on the 4060 Ti, multi-turn replay; TTFT/TBT/throughput/
  sessions-before-collapse, pool on DRAM vs CXL.
**C (optional)** optimizer-state RMW stream on CXL with NT stores vs DRAM — tests the
published "pin optimizer to DRAM" conclusion.
**Schedule:** wk1 (09-09→15) A1 build+integration+baseline, B1; wk2 (→22) A1 comparison
(if DRAM healthy), A2, B2; wk3 (→29) B3 decision, start W3 planner against A/B; then
Phase 5 (PolyStore: A1 with concurrent CXL→NVMe drain). Files: `…-lulesh-veloc-ckpt.md`,
`…-optimizer-snapshot.md`, `…-kv-trace-analysis.md`, `…-kv-pool-bench.md`.
**Needs from user:** approval; trace files or permission to download ShareGPT/Mooncake
(LMSys needs an HF token); whether a built VeloC already exists.

### Phase 4 TODO (approved 2026-09-09 — execute one item at a time, in order)
| # | item | status |
|---|---|---|
| A1.1 | LULESH 2.0 OpenMP built (`~/apps/lulesh`, SERCXX); baseline `-s 160 -i 30`: 1.07 s/step @16T, 0.87 s/step @32T (crippled DRAM) | ✅ 2026-09-09 |
| A1.2 | User's VeloC-instrumented LULESH built at `~/apps/lulesh-veloc` (`-DWITH_VELOC`, MPI 1 rank, `mpirun --bind-to none`; client auto-launches `veloc-backend` from PATH); 11 protected arrays = 348 MB at s=160; ckpt call 0.07–0.08 s | ✅ 2026-09-09 |
| A1.3 | Scratch placement without root via `LULESH_CKPT_NODE=1` (verified); VeloC rebuilt at `~/apps/veloc-inst` with EXDEV fallback → drain to NVMe works, no skipped ckpts. dax2.0 NT path pending | ✅ 2026-09-09 (dax2.0 path ⬜) |
| A1.4 | Checkpoint experiment — crippled-DRAM results DISCARDED (2026-09-14). Re-run on healthy DRAM needs a devdax scratch path (VeloC flush_mem → dax mmap, NT copy); then scale-up + aggressor | ⬜ needs dax scratch path first |
| A2.1 | Optimizer-snapshot emulator (torch CPU): fp32 params + Adam m/v, RMW step, `torch.save` every K steps to scratch {DRAM, CXL} | ⬜ |
| B1.1 | ShareGPT + Mooncake ×3 traces in `workloads/` (gitignored; LMSys skipped — needs HF token) | ✅ 2026-09-09 |
| B1.2 | Trace analysis — `2026-09-09-kv-trace-analysis.md`: 58–78% never-read, 3–8 GiB/s writes, gaps p50 ≤2 min | ✅ 2026-09-09 (first pass) |
| B2 | KV-pool microbenchmark (NT writes to {DRAM, dax2.0, dax0.0}, trace-driven, DRAM-reader victim) | ⬜ |
| B3 | Real serving (vLLM+LMCache on 4060 Ti) — only if B1/B2 justify | ⬜ decision after B2 |
| C | Optimizer-state RMW on CXL vs DRAM (optional probe) | ⬜ after A+B |

## TODO (update statuses here; ✅ done · 🟢 runnable · 🟡 partial · 🔴 blocked on BIOS · ⏳ needs user)
| # | item | status |
|---|---|---|
| 0 | Admin: Memory/Chipselect Interleaving → Auto; keep CXL Memory Attribute = Enabled; CAP_PERFMON or paranoid=1; udev rule for dax perms | ⏳ user emails |
| 1a | Phase 1 mechanism write-up (6 questions) — `2026-09-08-dram-write-drain.md` Part A | ✅ 2026-09-08 |
| 1b | Phase 1 read/write matrix × writers × store type (+UMC counters if perf allowed) | ✅ DONE 2026-09-14 — cliff confirmed on healthy NPS1: reader 12× (96→8 GiB/s) once writers on 4 CCDs saturate the ~290 GiB/s pipe; reads/plain writes/mixed 6–12×, NT writes −13–23%; neighbour-CCD −20%. First multi-CCD pass invalid (pre-touch overlap) → redone with epoch stamps. No UMC counters |
| 2a | Phase 2 five-answers section — `2026-09-08-cxl-card-scaling.md` Part 1 | ✅ 2026-09-08 |
| 2b | CXL 1/2/4-card scaling — `2026-09-08-cxl-card-scaling.md` Part 2: linear scaling, HB −6%, cross-pair −1%, duplex at every scale | ✅ 2026-09-08 |
| 3a | Stencil code `benchmarks/stencil/pond.c` (3 buffers + DRAM staging, placement/threads/NT knobs, policies rotate/copyback[--alt]/migrate, per-step BW+timing) | ✅ built 2026-09-08 (smoke-tested 1 GiB) |
| 3b | Stencil CXL-side strategy comparison — results DISCARDED (crippled DRAM, 2026-09-14); code kept | ⬜ superseded by 3c |
| 3c | Stencil Case A vs Case B, healthy DRAM (+ pressure aggressor) — CXL via daxA/daxB only (node 1 gone) | ✅ DONE 2026-09-14 — idle: all-DRAM best, `new`-on-CXL +19%…+2.2×; under 280 GiB/s DRAM write pressure all DRAM-reading variants 10× slower, all-on-CXL immune (0.60 s), aggressor-on-CXL leaves all-DRAM at 95%. Verdict: relocate the write streams, not the victim's buffers (`2026-09-14-stencil-3c.md`) |
| 4a | LULESH + VeloC object analysis — `2026-09-08-lulesh-veloc-objects.md` (static; LULESH cloned to ~/apps/lulesh) | ✅ analysis 2026-09-08 · measurement pending approval |
| 4b | LULESH all-DRAM vs placement; VeloC staging; policy | 🟢 UNBLOCKED (needs a direct dax scratch path: tmpfs-on-CXL trick is gone) |
| 5 | PolyStore full read ✅ 2026-09-08 (gap list in `Related.md`) → DRAM→CXL→NVMe experiment design | 🟡 design pending Phase 4 numbers |

**Agreed order:** 1a → 2a/2b → 3a/3b (all CXL-side, DRAM-independent) →
[BIOS revert] → 1b → 3c → 4 → 5. Every step is presented before execution.

## Phase 5 v2 — BUILD PLAN for the write-path runtime (APPROVED by the user 2026-09-19 — executing)
Supersedes the Phase 5 sketch above. Design: `../DESIGN.md` §10 (goals G1–G3,
principles P1–P4, components A–D). Scope of this plan: feasibility checks →
full implementation → end-to-end integration tests. **Evaluation experiments
are NOT in this plan; they are discussed after step F.**

**How it runs unattended.** This table is the single source of state. A session
starts by reading it, takes the FIRST item that is not ✅, does it, runs its
gate, records the result (status here + one WORKLOG line + raw logs under
`experimental_results/2026-09-19-cxlpath-build/`), then continues with the
next item. Nothing else is needed to resume after a session ends.
**Stop and ask the user when:** a gate fails in a way that changes the design
(not a bug); anything needs root, a BIOS change, dax2.0, or another node; a
step would delete or rewrite existing results; two fix attempts on the same
gate have failed; or the step is marked ⏳.
Standing rules: `METHODOLOGY.md`; only dax0.0 / dax1.0; every program that
writes to a dax device restores or owns its range; code in `system/cxlpath/`
(C11 core + Python shim for PyTorch), `make test` must pass at the end of every
step; no evaluation claims from gate numbers.

User decisions 2026-09-19: plan approved; system name `cxlpath`; work on branch
`cxlpath`, one commit per step (message starts with the step id, no Claude
attribution); V5 measurement allowed. Status column: ✅ done · ▶ in progress ·
(blank) not started · ⏳ needs user.

| id | step | gate (pass condition) | if it fails |
|---|---|---|---|
| **V — feasibility checks (small yes/no programs)** | | | |
| V1 ✅ | O_DIRECT write to `/mnt/local` with a devdax mapping as the source buffer | file on NVMe byte-identical; no EFAULT/EINVAL | drain copies through a small reused DRAM buffer (DRAM traffic ≤ NVMe speed, ~3 GiB/s) — note in DESIGN D |
| V2 ✅ | virtually contiguous buffer: scattered 32 MB devdax segments mapped at adjacent addresses with `MAP_FIXED`; CPU write/read across the seams | data verified across seams | buffer sets use physically contiguous runs of segments |
| V3 ✅ | `cudaHostRegister` on (a) a stitched buffer from V2, (b) large ranges 1 / 8 / 64 / 200 GiB: success, time, limits | registration succeeds for ≥ 8 GiB per buffer; time recorded | register per segment lazily; cap buffer-set size |
| V4 ✅ | PyTorch 2.5.1 `async_save` / `staging`: can the staging buffers and the storage writer be supplied by us? (code reading + 20-line prototype) | a checkpoint staged into our buffer and restored correctly | hook at `torch.save`-level pinned copy instead; ⏳ ask user if neither works |
| V5 ✅ | probe calibration: DRAM latency probe vs DRAM write load at 0 / 10 / 20 / 40 / 70 / 100 % (membench aggressor, separate CCDs), beside a bandwidth victim | probe latency rises monotonically with victim slowdown; pick the bound constant | ⏳ stop: signal (3) of Component B needs redesign |
| V6 ✅ (open) | (time-boxed 1 h, optional) GPU→CXL 3.9 GiB/s cap: try registration flags, pinned-mapped kernel copy, IOMMU state visible without root | cause identified or recorded as open | keep as open item; design already handles both paths |
| **A — segment store (P1)** | | | |
| A1 ✅ | skeleton `system/cxlpath/`: Makefile, headers, test harness, device layer (map dax0.0/dax1.0 + DRAM pool via memfd/shm, 32 MB geometry) | `make test` maps both devices and the pool, unmaps cleanly | — |
| A2 ✅ | shared segment table, compare-and-swap claim/release, owner + state per segment | stress: 8 processes × 8 threads, 10⁶ claims, no double claim, no leak | — |
| A3 ✅ | `reserve` / `commit` / `release`, per-thread open log segments, live-byte accounting, reclaim at zero, `copy_in` (NT stores) | unit tests; write throughput within 5 % of a raw NT memcpy to the same device | profile; reduce table touches |
| A4 ✅ | shared index (object → extents), `lookup`, objects outlive the writer; cleanup of uncommitted reservations | kill -9 a writer mid-write: committed objects readable from a new process, uncommitted space reclaimed | — |
| A5 ✅ | buffer sets (uses V2/V3): create, two alternating sets, overwrite rule | rule test: a set cannot be overwritten before its version is drained and the other committed | — |
| **B — placement (P2)** | | | |
| B1 ✅ | background process + shared policy page (published ratio/path, read by `reserve` without IPC) | `reserve` sees a changed ratio within one epoch; no syscalls on the data path (strace) | — |
| B2 ✅ | latency probe thread, idle baseline (60 s minimum), adaptive 10 / 200 ms period | probe overhead ≤ 2 % of one core; values match V5 | — |
| B3 ✅ | ledger + achieved-speed signal with per-path solo calibration | "CXL full" detected when 2 writers exceed the pair's write capacity, not detected with 1 | — |
| B4 ✅ | controller: +1/16 per 50 ms epoch, halve on 2 probes over bound, per-stream memory, blocking `reserve` | deterministic tests with injected signals; live: spill rises only when CXL is full and DRAM calm, halves within 50 ms of an injected DRAM aggressor | — |
| B5 ✅ | GPU source: direct vs staged path per chunk, runtime-owned pinned copy threads | both paths produce verified data; path switches under injected pressure | — |
| **C — read path (P3)** | | | |
| C1 ✅ | read counting in a 10-minute window (two buckets), per-consumer constants calibrated at start-up, break-even k | unit tests; calibration prints k for CPU consumer and "never" for GPU consumer on c28 | — |
| C2 ✅ | promotion of read segments to the DRAM pool under the bound, release of the CXL copy; checkpoints never promoted | object readable before/during/after promotion; no promotion while probe > bound | — |
| **D — drain and recovery (P4)** | | | |
| D1 ✅ | drain targets on `reserve`; segment-wise O_DIRECT drain (per V1), padding/truncate | drained file byte-identical to the source (checksum), for sizes not multiple of 32 MB | — |
| D2 ✅ | pacing (yield to writers, full speed under space pressure); reclaim rules for checkpoint versions | writer speed during drain within 10 % of no-drain; free space never reaches 0 in a 10-version loop | — |
| D3 ✅ | recovery API: newest complete version from CXL, else NVMe | kill the application after commit: restore from CXL verified; after clearing the store: restore from NVMe verified | — |
| **E — clients** | | | |
| E1 ✅ | file-style shim + VeloC (`~/checkpoint/veloc`, existing hook point) | LULESH + VeloC checkpoint lands on NVMe, restart works | — |
| E2 ✅ | PyTorch async checkpoint shim (per V4) | small model on the 4060 Ti: async checkpoint through the runtime, reload gives identical tensors | — |
| E3 ✅ (LMCache ⏳) | KV client: trace-driven stand-in with allocate / free / get semantics (Mooncake traces). LMCache itself is NOT installed and needs vLLM — ⏳ ask user before attempting the real integration | replay of a trace through the runtime with correct data on every hit | — |
| **F — system complete** | | | |
| F1 ✅ | end-to-end run of all three clients together for 10 minutes, invariants checked (no leak, no lost object, files identical) | clean run | — |
| F2 ✅ (user review ⏳) | DESIGN.md updated to "as built" (§10 status, API reference), WORKLOG summary, list of what changed versus the design | user review ⏳ → then discuss evaluation | — |

### Phase 5 v2 results log (one entry per finished step; raw: `experimental_results/2026-09-19-cxlpath-build/`)
- **V1 ✅ 2026-09-19** — O_DIRECT from a devdax mapping WORKS on dax0.0 and dax1.0 (2 GiB, 32 MB
  `pwrite`s, file byte-identical). Speed equals O_DIRECT from DRAM (0.89–0.95 vs 0.91–0.93 GiB/s):
  the NVMe, not the source, is the limit. Note for D2: a single synchronous writer gets only
  ~0.9 GiB/s from the Solidigm drive — try parallel/queued writes there. Tool:
  `system/cxlpath/checks/v1_odirect_devdax.c`.

- **V2 ✅ 2026-09-19** — 16 scattered, out-of-order 32 MB segments of dax0.0 mapped at adjacent
  addresses with `MAP_FIXED` (0.035 ms total); data verified through independent linear mappings
  and with writes straddling every seam. Virtually contiguous buffer sets are feasible.
- **V3 ✅ 2026-09-19** — `cudaHostRegister` accepts the stitched buffer (512 MiB, 9 ms; GPU copy into
  it verified, 3.92 GiB/s = the known direct-write cap) and plain ranges of 1 / 8 / 64 / 200 GiB:
  ~20 ms per GiB (200 GiB = 4.1 s), unregister ~15 ms per GiB, no limit hit. Registering a whole
  buffer set once at start-up is cheap. Tool: `system/cxlpath/checks/v2v3_stitch_register.c`.

- **V4 ✅ 2026-09-19** — PyTorch 2.5.1 `dcp.async_save` takes our staging through the `AsyncStager`
  protocol on the storage writer: `stage()` returned CPU tensors living inside a CUDA-registered
  dax0.0 mapping (`torch.frombuffer` over `mmap`), training mutated the model afterwards, and
  `dcp.load` restored the checkpoint-time values exactly. Open for E2: the storage-writer half —
  DCP serialises staged tensors into `.distcp` files itself; either feed that stream through the
  file-style shim (one CXL→CXL copy) or stage directly in the serialised layout. Tool:
  `system/cxlpath/checks/v4_torch_async_stage.py`.

- **V5 ✅ 2026-09-19** — The DRAM latency probe TRACKS the slowdown of a bandwidth-bound reader,
  monotonically and with ±1% repeatability (3 reps × 10 s; victim 8 readers cpus 0–7, probe cpu 16,
  NT writers cpus 32+; `V5-probe-calibration.txt`):

  | DRAM NT-write load | victim read GiB/s | victim slowdown | probe p50 ns/load | probe vs idle |
  |---|---|---|---|---|
  | 0 | 99.6 | — | 138 | 1.00× |
  | 77 GiB/s (28% of 277) | 85–88 | −12…−14% | 163 | 1.18× |
  | 113 GiB/s (41%) | 77–78 | −23% | 182 | 1.32× |
  | 203 GiB/s (73%) | 39 | −61% | 291 | 2.1× |
  | 267 GiB/s (96%) | 8.8–9.6 | −91% | 722 | 5.2× |
  | 277 GiB/s (100%) | 8.0 | −92% | 900 | 6.5× |

  Consequences for Component B: the default bound 1.10× idle corresponds to roughly a 7% reader
  slowdown; idle noise is small (p99 = 1.07× p50), so "mean of 5 probes" and "2 consecutive probes
  over the bound" will not fire when idle. Load steps follow CCD count (one CCD of writers tops out
  at ~77 GiB/s). First attempt had a timing bug in the probe loop (read 0.3 ns/load); fixed by a
  non-inlined probe function with integer clock math — reuse THAT code in B2. Tool:
  `system/cxlpath/checks/v5_probe_calib.c`.

- **V6 ✅ (cause still open) 2026-09-19** — The 3.9 GiB/s GPU→CXL write cap does not move with
  anything visible without root: registration flags default / portable / mapped all 3.91; a GPU-side
  copy through the mapped device pointer 3.91; two concurrent streams into dax0.0 + dax1.0 = 3.91
  in TOTAL (same two cards, so this says nothing about per-card). GPU (bus 61) and the CXL cards
  (c1, e1) sit under different Turin root complexes; IOMMU is present (ivhd0–2). A concurrent
  CXL + pinned-DRAM test is not informative (GeForce has one D2H copy engine: 2.97 + 2.97). Left
  open; the design handles both paths (DESIGN §10.4). Tool: `system/cxlpath/checks/v6_gpu_write_cap.c`.

- **A1–A3 ✅ 2026-09-19** — `system/cxlpath/` (C11, `make test` on sparse /dev/shm files,
  `make test-dax` on the first 8 GiB of dax0.0 + dax1.0, which cxlpath owns). A1 device layer +
  shared metadata in `/dev/shm/cxlpath.<name>`. A2 segment table claimed by compare-and-swap:
  8 processes × 8 threads × 10⁶ claims, no double claim, no leak — the stress test caught one real
  ordering bug (owner must be cleared BEFORE a segment becomes FREE). A3 reserve / commit / abort /
  release on per-thread append-only segments per (device, lifetime class), reserved bytes count as
  live, sealed + empty segments return to the pool, `copy_in` with AVX2 NT stores: 16-thread
  hammer with random release order, data verified, everything reclaimed; throughput through the
  library 98.0% (dax) / 99.3% (shm) of a raw NT memcpy (gate ≥ 95%; ratio only, not a performance
  claim). Raw: `A1-A3-test-dax.txt`.

- **A4 ✅ 2026-09-19** — Object index in the shared metadata (open-addressing hash of
  `cxlp_obj_t`, extents claimed by compare-and-swap; one writer per object). Gate: a writer commits
  3 objects (44–70 MiB, not segment multiples), starts a 4th, leaves a raw uncommitted reservation
  and is SIGKILLed; `cxlp_cleanup_dead` drops exactly the uncommitted object and recounts live
  bytes of the dead writer's segments from the index; a NEW process reads the 3 objects
  byte-exactly, the 4th is absent; after release every segment is free (fake devices and
  dax0.0 + dax1.0). Plus 4 processes × 300 put / get+verify / release with no leak. Known limit:
  `cxlp_get` copies at most 64 extents (2 GiB) — lift when a client needs it. Raw: `A4-test-dax.txt`.

- **A5 ✅ 2026-09-19** — Buffer sets: two sets per client built from SCATTERED segments (device
  fragmented on purpose), stitched per process with `MAP_FIXED`, state in shared metadata. Overwrite
  rule verified step by step: v2 goes to the other set; v3 is refused until v1 is drained (draining
  the newer v2 does not help); v3 then overwrites v1's set while v2 stays intact and is reported as
  the newest complete version; a new process recovers v2 byte-exactly through its own mapping.
  Passes on fake devices and on dax0.0 + dax1.0. **Component A complete.** Raw: `A5-test-dax.txt`.

- **B1 ✅ 2026-09-19** — Shared policy page in the store metadata + `cxlpathd` (one background
  process per node). `reserve()` reads a per-stream "n of every 16 new segments go to DRAM" value;
  bit-reversed spreading gives exactly 80/40/10 of 160 segments for 8/4/1 of 16. No daemon or a stale
  heartbeat ⇒ all CXL. CXL out of space ⇒ DRAM only if the daemon says DRAM is within the bound,
  else `reserve` blocks on a futex in the shared table (woke 300 ms after a 300 ms release). A real
  daemon published a forced ratio 12–17 ms after the request (gate: one 200 ms idle epoch). strace:
  **0 system calls between the data-path markers** (320 reservations, new segments on CXL and DRAM,
  2.5 GiB copied; 256 in the whole run). All ways back to FREE now pass an exclusive FREEING state.
- **B2 ✅ 2026-09-19** — Probe in the daemon (code shape of V5), pinned to cpu 16, everything else kept
  off that CCD. Overhead with writers active (10 ms probes, 50 ms epochs): **1.26% of one core**
  (gate 2%). Idle 130–141 ns per load, 11× under 80 NT writers (298 GiB/s). Found and fixed: log
  writes to the NFS home stretched 50 ms epochs to 150 ms — the loop now never waits for I/O.
- **B3 ✅ 2026-09-19** — Ledger (bytes + copy time per device, per stream) fed by `cxlp_copy_to`;
  start-up calibration of the CXL write path: solo 33–41 GiB/s, capacity 43.9 GiB/s. Signal: full
  at ≥ 90% of capacity, slack below 70%. Live: 1 writer at 20 GiB/s → full in 0% of epochs;
  4 writers (43.9 GiB/s) → 100%. **Finding: one unthrottled core already pushes 41 GiB/s = 94% of
  the card pair's write capacity** (flagged full in 71% of its epochs), so the gate's "1 writer"
  had to be a rate-limited one.
- **B4 ✅ 2026-09-19** — Controller (+1/16 per 50 ms epoch, halve on 2 consecutive probes over the
  bound, per-stream memory). Deterministic tests with injected signals pass. Live (4 writers, 60 GiB/s
  demand; 64-thread DRAM aggressor injected for 4 s): spill settles at 6/16 = CXL 37 + DRAM 20 GiB/s
  with probe 131 vs reference 130 and no halving; all 30 increases happened in epochs with CXL full
  and probe ≤ 1.05× reference; **first halving 16 ms after the aggressor starts, spill 0 after
  46 ms**, none while it runs, rises again after it leaves. Raw: `B-live/`.
  **Design changes forced by the live runs (to be folded into DESIGN §10.4 at F2):**
  (1) the reference is the MEDIAN of epoch means, not the minimum — an idle c28 reads 100–160 ns
  from probe to probe, a minimum sits 15–25% below typical and made normal readings look like
  pressure; (2) TWO references: idle (60 s) and active (2 s window, only epochs with writer activity
  and none of our bytes in DRAM, frozen while we spill, known after 5 epochs) — because the writers'
  own source reads (50 GiB/s from DRAM) lift the probe ~20% with zero spill; (3) the idle state uses
  a loose bound (1.5×) because idle readings are too noisy for 10%; (4) headroom guard: reference
  > 2.0× the lowest idle reference ever seen ⇒ nothing may spill; (5) the per-writer-speed fullness
  rule over-spilled (11/16 for a 60 GiB/s demand) and was replaced by capacity thresholds; new
  slack rule: spill shrinks by 1/16 per epoch when CXL runs below 70% — DRAM is only for the excess.
  Not covered: another tenant writing to the same cards outside cxlpath.

- **B5 ✅ 2026-09-19** — GPU sources (`libcxlpath_gpu`, optional, CUDA): per 32 MiB chunk either
  direct (GPU → CUDA-registered CXL buffer set) or staged (GPU → one of 4 reused pinned DRAM buffers →
  a runtime-owned copy thread pinned to a chosen CPU NT-copies to CXL). 1 GiB copies byte-exact at
  staged 0/16, 16/16, 8/16, 3/16 with exactly the published share: **direct 3.91 GiB/s, staged
  12.16 GiB/s** (link 12.29), 8/16 → 5.87. Live with a real daemon: a first burst starts direct, the
  staged share reaches 0.95 while DRAM is calm (11.5 GiB/s), falls to 0.00 during a 64-thread DRAM
  aggressor (3.7 GiB/s), returns to 1.00 afterwards; every verified copy byte-exact while switching.
  "Path full" for a GPU source = direct path delivers < 80% of the calibrated link speed (sticky).
  **Component B complete.** Raw: `B-live/B5-*`.

- **C1 + C2 ✅ 2026-09-19** — Read path: `cxlp_obj_pin/unpin` (readers get pointers, CXL or DRAM),
  per-EXTENT read counts in a two-bucket window (default 2 × 5 min; a range pin counts only the
  extents it touches), threshold k per consumer type published by the daemon from
  `k = ceil(t_copy × (1 + w × pressure) / (t_cxl − t_dram))`, w = 10, "never" when the CXL penalty is
  < 5%. Promotion by a daemon thread (off the probe's CCD), only while DRAM is within its bound and the
  pool has room: NT copy into the DRAM pool, relocation under the object's seqlock, the old CXL copy
  released once no reader pins the object; `release` is refused while pinned; NOPROMOTE objects
  (checkpoints) never move. Unit tests on fake and dax devices pass (k = 5 / 10 / 2 / never for the
  design's example numbers; a reader pinned before the move keeps valid data).
  **Calibrated on c28 (single-thread streaming, 128 MiB): DRAM 40.8 GiB/s, CXL 23.0 GiB/s (1.77×),
  copy CXL→DRAM 23.5 GiB/s ⇒ k = 3 when DRAM is calm** (k = 5 was published while the probe sat
  slightly above its reference); **GPU consumer: CXL 12.45 vs DRAM 12.46 GiB/s ⇒ never.** Live: an
  object read k times under a real daemon moved to the DRAM pool byte-exactly. Note: the design's
  k ≈ 5 came from the stencil proxy (1.2×); a single streaming reader sees 1.77×, hence the smaller k.
  Known limit: if the daemon dies between relocation and the deferred release, the old CXL bytes stay
  counted as live. **Component C complete.** Raw: `C-live/`.
- Housekeeping: the A3 throughput gate compares two runs at the device limit, which vary by ~8%;
  it failed once by noise (raw 43.8 vs library 40.x) and now takes the best of 9 alternating runs.

- **D1 ✅ 2026-09-19** — Drain targets per object (path + file offset, descriptor table in shared
  metadata) and per buffer-set version. The daemon's drain thread writes extent by extent / segment by
  segment with O_DIRECT straight from the CXL mapping (4 KiB-aligned body; sub-4 KiB tails through a
  buffered descriptor; falls back to buffered where O_DIRECT is refused), fsyncs when an object is
  complete, truncates a buffer-set file to its exact size. Byte-identical files for 1 B, 4095, 4096,
  4097, 5 MiB+3, 32 MiB, 40 MiB+777, 100 MiB+1; two objects in one file (second at offset 8192); the
  first 32 MiB of an object was on NVMe while the object was still being written; buffer-set versions
  of 300 MiB+12345 identical, and the overwrite rule is now driven by the real drain. The drainer pins
  the object it writes, so a release waits. Fake devices and dax0.0 + dax1.0, target `/mnt/local`.
- **D2 ✅ 2026-09-19** — Pacing: the drain yields while CXL writers moved bytes in the last 100 ms,
  unless free CXL segments fall below 25%. Live: 4 unlimited writers reach 43.90 GiB/s alone and
  **43.89 GiB/s with a 6 GiB drain backlog pending** (100.0%; gate ≥ 90%); the backlog finished 16 s
  after they started. 10 versions × 2 GiB on an 8 GiB store: versions 1–4 at 37 GiB/s, then
  back-pressure holds the producer at the NVMe's pace (0.95 GiB/s), all 10 files byte-identical, all
  segments free at the end (36 s in total). **Fact: the Solidigm NVMe sustains 0.90–0.92 GiB/s for
  O_DIRECT writes whatever the parallelism (1–16 threads, 4–32 MiB I/Os)** — one drain thread is
  enough, and a 32 GB checkpoint needs ~36 s to become durable.
  **Design gap found by the first D2 run (it hung): a producer blocked in `reserve()` cannot release
  its own old versions, so reclaiming must be done by the RUNTIME.** Added version chains
  (`cxlp_obj_set_version`): the drain thread releases every version that is on NVMe once a newer
  version of its chain is committed; chain objects are NOPROMOTE.
- **D3 ✅ 2026-09-19** — Recovery: an application SIGKILLed right after commit (before any drain) —
  a new process restores the 90 MiB checkpoint from CXL byte-exactly through the node-owned index,
  the store still drains the dead writer's checkpoint; after the store is destroyed and recreated
  (reboot: CXL content gone) the object is absent from CXL and the NVMe file is byte-identical.
  Buffer sets: `cxlp_bufset_newest` (A5) gives the newest committed version to a new process.
  **Component D complete.** Raw: `D-live/`.

- **E1 ✅ 2026-09-19** — File-style shim in the library (`cxlp_stream_*`): write() calls of any
  size are packed back to back into whole 32 MiB extents (the last one is shrunk), so drained files
  stay 4 KiB-aligned; `cxlp_read` (ranged, pinned), `cxlp_chain_newest`, `cxlp_shrink`. Test: 150 MiB
  + 4321 B written as random pieces of 1 B–9 MiB = four whole extents + one short; 200 random reads and
  the drained file byte-exact; the older version reclaimed by the runtime.
  VeloC: patch `system/cxlpath/clients/veloc/veloc-cxlpath.patch` (193 lines, applied to the project's
  copy `~/apps/veloc-src`, installed in `~/apps/veloc-cxlpath-inst`; the user's `~/checkpoint/veloc`
  tree was NOT touched). Enabled at run time by `VELOC_CXLPATH_STORE=<store>`: `checkpoint_mem` writes
  the normal VeloC file image as one cxlpath stream (no scratch file, no backend transfer), target =
  the file VeloC would have put in `persistent`, versions form a chain; `restart_test` / `restart`
  prefer the copy on CXL. Live gate (`tests/live/e1_veloc.sh`): API round trip of 3 versions
  (80 MiB + 12 MiB + 777 B) — no scratch file, restart in a new process from CXL byte-exact, and after
  the store is destroyed STOCK VeloC restarts from the drained NVMe file byte-exact; LULESH -s 100:
  **the 4 checkpoint files drained by cxlpathd are byte-identical to the files stock VeloC writes**,
  and LULESH restarts from the newest version on CXL (rc=0, 4.9 ms). Raw: `E1-veloc/`.

- **E2 ✅ 2026-09-19** — PyTorch client `system/cxlpath/clients/pytorch/cxlpath_dcp.py` (ctypes over
  the new `build/libcxlpath.so`): `CxlpathWriter` = DCP `StorageWriter` + `AsyncStager`,
  `CxlpathReader` = DCP `StorageReader`; used through the standard `dcp.async_save` / `dcp.load`.
  `stage()` copies every tensor GPU → a CUDA-registered CXL buffer set with `cxlp_gpu_copy_in` (path
  per 32 MiB chunk from the published ratio) and waits when neither set may be overwritten;
  `write_data()` moves no data (records offset/nbytes of tensors that already live in the set);
  `finish()` writes two small metadata files and arms the drain of the USED prefix of the set;
  the reader restores from the buffer set if that version is still on CXL, else from the NVMe file.
  This resolves the open point of V4 by option "own storage format behind the DCP plugin interface"
  (no CXL→CXL serialisation copy). Gate, 1.5 GiB model on the 4060 Ti, weights changed right after
  every `async_save`: v1 reloaded from CXL = checkpoint-time values (0.10 s); v3 waited 0.45 s for
  v1 to reach NVMe before overwriting v1's set; v1 then reloaded from NVMe byte-exact (0.72 s), v2/v3
  from CXL; after the store is destroyed v3 reloads from NVMe byte-exact. Training was blocked
  0.35 s / 0.27 s / 0.60 s; the copy ran at 4.3 → 5.7 → 10.5 GiB/s as the staged share rose while
  DRAM was calm. Limits: plain tensors and picklable objects only (no DTensor/ShardedTensor); one
  rank per writer; the reader is not protected against a writer that starts overwriting the set.
  Found on the way: a buffer set must drain only its used prefix (`cxlp_bufset_set_used`), and the
  writer keeps per-checkpoint state so an overlapping save cannot disturb a running one.
  Raw: `E2-pytorch/`.

- **E3 ✅ 2026-09-19 (real LMCache integration still ⏳ user)** — `tests/tools/cxlp_kv_replay.c`: a KV
  layer in miniature driven by the Mooncake traces, with the call pattern of an LMCache-like layer —
  pin/unpin for every block of the longest matching prefix, allocate + fill + commit for the rest, and
  ITS OWN LRU eviction (the runtime does not decide what a KV layer drops). Block content is a function
  of the block hash, so every hit is checked word by word. With a real cxlpathd (4 MiB blocks, first
  4000 requests of each trace, 12 GiB layer capacity): conversation 105,904 blocks / 6,470 hits;
  toolagent 75,443 / 24,927; synthetic 121,877 / 23,225 — **971 GiB stored, 213 GiB read back,
  0 verification errors, 0 failed stores**; hot blocks were promoted while the traces ran (up to
  23,550 hits served from the DRAM pool); every segment free at the end. Object table size is now a
  store parameter (`obj_slots`; small objects need more than the default 8 per segment).
- **Correction to E1 and a lesson (found while checking F1's output).** After E1 the shared-metadata
  layout changed twice, but the VeloC client still carried the STATIC copy of libcxlpath from E1 time:
  its attach failed on the layout check and the patch fell back to stock VeloC without anybody
  noticing (my scripts discarded stderr). Consequence: in the FIRST F1 run the VeloC and LULESH loops
  exercised stock VeloC, not cxlpath (PyTorch and KV parts were valid); that run's raw files are kept
  under `F1-all/first-run-veloc-fellback/`. Fixes: a layout mismatch is an immediate, explicit error
  in `cxlp_attach`; VeloC links the SHARED library; `VELOC_CXLPATH_REQUIRED=1` turns the fall-back
  into an abort and is set by every gate; the E1 and F1 gates now PROVE the path (checkpoint objects
  listed on CXL, scratch directory stays empty through checkpoint and restart). E1 rerun with these
  checks: PASS — restart came from CXL, drained files byte-identical to stock VeloC's.

- **F1 ✅ 2026-09-19 (third run; the first two found real defects)** — `tests/live/f1_all.sh`: VeloC
  round trips, LULESH + VeloC, PyTorch `async_save` loop, KV trace replay, all on ONE store (2 × 16 GiB
  CXL + 4 GiB DRAM pool) for 600 s, a 64-thread DRAM aggressor for 5 s every minute.
  Run 1 looked green but was void for VeloC/LULESH (stale static library → silent fall-back to stock
  VeloC, see the correction above); it did expose **drain starvation** (a KV layer that writes all the
  time kept the drain yielding forever; PyTorch waited 62 s for a buffer set) → the drain now stops
  yielding when space is short, a writer is blocked on it, or work is pending > 2 s.
  Run 2, with VeloC truly on cxlpath, FAILED: **re-written keys piled up** — every rerun writes
  "version 3" again, `cxlp_obj_begin` did not notice the existing key, 361 objects (32 GiB) filled the
  store, 392,077 KV stores failed, LULESH sat in back-pressure until its timeout, 89 GiB overflowed
  into the DRAM pool → a key now names ONE object (supersede rule), pins name the pinned object,
  regression `tests/test_replace.c`.
  Run 3 **PASS**: VeloC 3,746 round trips, LULESH 34 runs, PyTorch 219 versions (219 reloads from CXL +
  217 from NVMe, training blocked 0.13 s on average, never waited for a buffer set), KV 17 replays =
  603,398 blocks with 91,563 hits checked word by word — **0 errors of any kind, 0 failed stores,
  3.07 TiB written through CXL, no scratch file ever written, 2 checkpoint objects left (the newest of
  each chain), and after a sweep every one of the 1,152 segments free.** Policy during the run: 3,758
  fast decreases around the 10 aggressor bursts, GPU chunks on the staged path in 11,003 epochs.
  Raw: `F1-all/` (runs 1 and 2 kept in sub-folders).
- **F2 ✅ 2026-09-19 (ends with the user's review ⏳)** — `DESIGN.md` §10 is "as built" (AS BUILT
  paragraphs per component, §10.10 code map / API / tests, §10.11 thirteen differences between the
  agreed design and the built system, each with the evidence that forced it); `PAPER.md` got "Facts
  from building the system"; `system/cxlpath/README.md`; WORKLOG session 23. **The build plan is
  complete. Next, with the user: evaluation plan; names; whether to attempt a real LMCache integration.**

## Change log (append-only)
- 2026-09-08 — created from the user's four-phase plan + PolyStore request;
  machine facts, blockers, and file naming fixed.
- 2026-09-08 (later) — 1a written; PolyStore read in full, gap list appended to
  `Related.md`; 2b launched; PDF kept local (`/docs/*.pdf` gitignored).
- 2026-09-08 (evening) — 2b done (3 reps; first run killed by a session restart,
  reps 2–3 re-run); Phase 2 file closed; pond.c built. Next: 3b needs approval.
- 2026-09-08 (night) — 3b done: all policies work; results are a high-DRAM-pressure
  preview (DRAM crippled), 3c required for the real ranking. Next: 4a (LULESH).
- 2026-09-19 — Phase 5 v2 build plan PROPOSED (feasibility checks V1–V6 → components A–D →
  clients E → system complete F); evaluation deliberately excluded. Awaiting user approval.
- 2026-09-19 (later) — Phase 5 v2 APPROVED; name `cxlpath`; branch `cxlpath`, commit per step.
- 2026-09-19 (end of day) — Phase 5 v2 COMPLETE: V1–V6, A1–A5, B1–B5, C1–C2, D1–D3, E1–E3, F1–F2 all ✅
  (E3 = trace-driven stand-in; real LMCache ⏳ user; F2 awaits the user's review). Evaluation not started.

## Naming (rule 2026-09-08 — do not use "Pair A"/"Pair B" in new text)
| historical label | what it is | use instead |
|---|---|---|
| Pair A | two cards at PCI c1:00.0 + e1:00.0, exposed as two firmware windows `/dev/dax0.0` (242.5 GiB) and `dax1.0` (= NUMA node 1, 269.5 GiB); root-level hashed interleave, not splittable | `dax0.0` / `node 1` (same two cards) |
| Pair B | two cards at PCI 01:00.0 + 02:00.0 behind host bridge pci0000:00, one window `/dev/dax2.0` (512 GiB); plain 256 B stripe, `card = (offset>>8)&1` | `dax2.0`; single cards "卡 01" / "卡 02" |
- 2026-09-08 (late) — 4a static analysis done: the write-tier object in LULESH is the
  checkpoint, not any solver array; VeloC scratch is the natural CXL tier; 4b designed.
- 2026-09-09 — Phase 4 plan v2 proposed (A checkpointing + B KV-cache; C optional).
- 2026-09-10 — reboot 09-09: DRAM restored (141 GiB/s @32T); CXL NUMA node removed, all
  dax devdax; dax2.0 currently root-only. 1b/3c/4b unblocked; tooling must use devdax paths.
- 2026-09-14 — user ruling: all crippled-DRAM measurements (08-27→09-09) are trash;
  3b and A1.4 results discarded, code kept; 1b/3c next.
- 2026-09-14 (evening) — 1b and 3c run on healthy NPS1 DRAM. 1b: write-drain cliff confirmed at socket scale (reader 12× under 273 GiB/s NT writes from 4 CCDs; NT writers immune, everything else 6–12×); first multi-CCD pass invalidated by aggressor pre-touch overlap → membench now stamps measure_start/end_epoch, summarizer checks overlap. 3c: `new`-on-CXL does not rescue a DRAM-reading app under pressure; all-on-CXL immune; aggressor-on-CXL leaves the app at 95%. Thesis wording to revisit: move the write STREAMS to CXL. Next: real apps (A/B) with this framing.
