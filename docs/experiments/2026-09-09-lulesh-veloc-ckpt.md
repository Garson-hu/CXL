# 2026-09-09 — A1: LULESH + VeloC checkpointing with scratch on DRAM vs CXL

> **DISCARDED 2026-09-14 (user decision):** every number in this file was measured while
> DRAM channel interleaving was disabled in BIOS (2026-08-27 → 2026-09-09; DRAM 25–41 GiB/s
> instead of 141). The user classified that data as trash. Keep the file for the method and
> the tooling only; do not cite its results. Re-run on healthy DRAM under a new dated file.


**STATUS: CXL-SIDE DONE 2026-09-09 (3 reps). Result: putting the checkpoint scratch on
CXL roughly halves the checkpoint's interference with compute (+4.8% → +2.9% per step at
one checkpoint per 10 steps; +9.0% → +6.2% at one per 5), and the checkpoint call itself
is 9% faster on CXL (0.072 vs 0.079 s per 348 MB). Effect is real but small at this
checkpoint volume; scaling and the DRAM-pressure variant are next (🔴 for healthy-DRAM
numbers).** Campaign Phase 4 anchor A, items A1.2–A1.4. Raw:
`experimental_results/2026-09-09-lulesh-veloc-ckpt/`.

## Setup
- App: the user's VeloC-instrumented LULESH 2.0 (`~/checkpoint/LULESH`, copied to
  `~/apps/lulesh-veloc`), built `-DUSE_MPI=1 -DWITH_VELOC=1`, 1 MPI rank,
  `mpirun --bind-to none` (default core binding halves OpenMP throughput), 16 OpenMP
  threads (`OMP_PROC_BIND=close OMP_PLACES=cores`), `-s 160 -i 40` (4.1 M elements,
  ~3.9 GB footprint). 11 protected arrays (x,y,z,xd,yd,zd,nodalMass,e,p,v,elemMass) =
  **348 MB per checkpoint**.
- VeloC: rebuilt from the user's branch into `~/apps/veloc-inst` (socket_queue, no DPU
  relay) with one patch — `posix_transfer_file` falls back to pread/pwrite when
  `copy_file_range` fails with EXDEV (tmpfs scratch → ext4 NVMe persistent; the stock
  build silently lost every drain and then skipped every second checkpoint). Config:
  `scratch=/dev/shm/lulesh_scratch`, `persistent=/mnt/local/ghu4/veloc_persistent`
  (NVMe), `mode=async`, `max_versions=2`. The client auto-launches `veloc-backend`
  from PATH.
- **Scratch placement without root:** tmpfs page-cache pages follow the writing
  thread's memory policy (verified 2026-09-09: a `numactl --membind=1 dd` to `/dev/shm`
  moved node-1 free memory by exactly the file size). Hook in LULESH:
  `LULESH_CKPT_NODE=1` wraps `VELOC_Checkpoint` in `set_mempolicy(MPOL_BIND, node 1)` /
  `MPOL_DEFAULT`. Verified: node-1 free −700 MB = 2 × 365 MB scratch files.
- Two added env hooks: `LULESH_STEP_TIMES=1` prints per-cycle compute time
  (excludes the checkpoint call); `LULESH_CKPT_NODE`. Per-checkpoint call time printed
  from the app side.

## Results (median of 3 reps; step = compute cycle time excluding the checkpoint call)
| config | step median (s) | per rep | ckpt call (s) | #ckpt / 40 steps | elapsed (s) | vs no-ckpt |
|---|---:|---|---:|---:|---:|---:|
| no checkpoint | 0.767 | 0.762 / 0.767 / 0.776 | — | 0 | 31 | — |
| DRAM scratch, every 10 | 0.804 | 0.812 / 0.803 / 0.804 | 0.079 | 4 | 32 | **+4.8%** |
| CXL scratch, every 10 | 0.789 | 0.784 / 0.789 / 0.800 | 0.072 | 4 | 32 | **+2.9%** |
| DRAM scratch, every 5 | 0.836 | 0.834 / 0.847 / 0.836 | 0.079 | 8 | 34 | **+9.0%** |
| CXL scratch, every 5 | 0.814 | 0.799 / 0.814 / 0.817 | 0.072 | 8 | 33 | **+6.2%** |
DRAM state: crippled (interleave disabled, 25–41 GiB/s) — numbers are for this
configuration only; a first single run before the 3-rep set showed a larger gap
(0.899 vs 0.816) and is superseded.

## Reading
1. The synchronous part (VeloC's `pwrite` of 348 MB into scratch) costs ~0.07–0.08 s
   either way — it is a single-thread memcpy-class copy, not bandwidth-bound; CXL is 9%
   faster because tmpfs page allocation on node 1 avoids DRAM's write-tax path.
2. The asynchronous part — the backend reading scratch and writing NVMe, plus the
   checkpoint's own read of the app's arrays — is what slows compute steps. With scratch
   on CXL the drain's reads leave DRAM alone: the compute penalty drops from +4.8% to
   +2.9% (every 10) and from +9.0% to +6.2% (every 5). This is Gate 2b at application
   level, in the predicted direction.
3. The absolute effect is small because LULESH's checkpoint stream is tiny relative to
   memory bandwidth (348 MB per 4–8 s ≈ 45–90 MB/s). The write-tier benefit scales with
   checkpoint volume and frequency, i.e. with how close the drain gets to DRAM's
   remaining bandwidth — which is exactly the pressure regime the thesis targets.

## Next for A1
- Scale the stream: larger state (`-s 220` → ~0.9 GB/ckpt), more ranks per node
  (4–8 MPI ranks each checkpointing), checkpoint every 2–5 steps; report the
  drain bandwidth actually sustained.
- Direct dax2.0 path: replace the tmpfs pwrite by an NT-store copy into a `/dev/dax2.0`
  mapping (VeloC's `flush_mem` hook = `obj_stage_out`), then drain CXL → NVMe.
- DRAM-pressure aggressor variant and healthy-DRAM re-run (🔴).
- PolyStore section: concurrent CXL → NVMe drain as the DRAM→CXL→NVMe path.
