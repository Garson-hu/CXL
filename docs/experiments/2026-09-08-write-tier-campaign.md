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
Status: 3a code 🟢 · 3b CXL-side relative results 🟡 · 3c Case A vs B 🔴.
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
| 1b | Phase 1 read/write matrix × writers × store type (+UMC counters if perf allowed) | 🟢 UNBLOCKED 2026-09-10 (DRAM restored) |
| 2a | Phase 2 five-answers section — `2026-09-08-cxl-card-scaling.md` Part 1 | ✅ 2026-09-08 |
| 2b | CXL 1/2/4-card scaling — `2026-09-08-cxl-card-scaling.md` Part 2: linear scaling, HB −6%, cross-pair −1%, duplex at every scale | ✅ 2026-09-08 |
| 3a | Stencil code `benchmarks/stencil/pond.c` (3 buffers + DRAM staging, placement/threads/NT knobs, policies rotate/copyback[--alt]/migrate, per-step BW+timing) | ✅ built 2026-09-08 (smoke-tested 1 GiB) |
| 3b | Stencil CXL-side strategy comparison — results DISCARDED (crippled DRAM, 2026-09-14); code kept | ⬜ superseded by 3c |
| 3c | Stencil Case A vs Case B, healthy DRAM (+ pressure aggressor) — CXL via daxA/daxB only (node 1 gone) | 🟢 UNBLOCKED 2026-09-10 |
| 4a | LULESH + VeloC object analysis — `2026-09-08-lulesh-veloc-objects.md` (static; LULESH cloned to ~/apps/lulesh) | ✅ analysis 2026-09-08 · measurement pending approval |
| 4b | LULESH all-DRAM vs placement; VeloC staging; policy | 🟢 UNBLOCKED (needs a direct dax scratch path: tmpfs-on-CXL trick is gone) |
| 5 | PolyStore full read ✅ 2026-09-08 (gap list in `Related.md`) → DRAM→CXL→NVMe experiment design | 🟡 design pending Phase 4 numbers |

**Agreed order:** 1a → 2a/2b → 3a/3b (all CXL-side, DRAM-independent) →
[BIOS revert] → 1b → 3c → 4 → 5. Every step is presented before execution.

## Change log (append-only)
- 2026-09-08 — created from the user's four-phase plan + PolyStore request;
  machine facts, blockers, and file naming fixed.
- 2026-09-08 (later) — 1a written; PolyStore read in full, gap list appended to
  `Related.md`; 2b launched; PDF kept local (`/docs/*.pdf` gitignored).
- 2026-09-08 (evening) — 2b done (3 reps; first run killed by a session restart,
  reps 2–3 re-run); Phase 2 file closed; pond.c built. Next: 3b needs approval.
- 2026-09-08 (night) — 3b done: all policies work; results are a high-DRAM-pressure
  preview (DRAM crippled), 3c required for the real ranking. Next: 4a (LULESH).

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
