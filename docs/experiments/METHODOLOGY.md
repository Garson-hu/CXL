# Measurement methodology (invariants)

*Apply to every experiment unless a file explicitly says otherwise. Append new
invariants with a date; never delete (mark superseded instead).*

- **Median of 5** for headline numbers; 3 s+ per point; pre-touched buffers.
- **Disjoint physical cores** for victim vs aggressor (`--cpu-offset` /
  within-process CPU assignment). Lesson from May Phase 2: shared cores
  produced a false 8.75× "interference" that was CPU contention.
- **Placement verified** with `move_pages` (`--verify-placement` /
  `--strict-placement`) for every CXL-bound buffer.
- **DRAM control next to every CXL number** — system drift is real (DRAM
  latency moved 184.9→205.5→174.8 ns across 2026 configs) and NPS4
  (2026-08-12) made all earlier DRAM numbers incomparable.
- **Write-side kernels use NT stores** unless the experiment is explicitly
  about plain-store RFO behavior (added 2026-08-25: plain stores put an RFO
  read on the read direction and contaminate direction-split measurements).
- **Machine state header** in every raw log: node map, decoder state, famfs
  status, date. Raw artifacts live in `experimental_results/<experiment-name>/`
  (same basename as the summary md; convention adopted 2026-08-25 — earlier
  paths migrated). Files there are append-only once written.
- **CPU pool = node 0** (NPS4: 64 logical CPUs) for membench/cxlprobe unless
  the experiment is about quadrant affinity.
- **Victim and aggressors on separate CCDs** (added 2026-08-25, gate-2 v1
  lesson): same-CCD threads share one CCD→IO-die fabric port, which dominates
  cross-node interference measurements — victims were hurt regardless of the
  aggressor's memory target. Use two processes with `--cpu-offset` ≥16 apart
  (node-0 quadrant = cpus 0–15 CCD0, 16–31 CCD1). Within-node co-run modes
  (duplex on ONE node) may stay single-process.
- Planner pressure default = saturated (conservative) for ObjPlace runs.
- **Write experiments must write data-carrying lines** (added 2026-09-22,
  `2026-09-22-zero-line-writes.md`): beside a co-running program c28 writes an
  all-zero 64 B line at near-full speed while any line with a non-zero byte is
  written at 66% (CXL) / 20% (DRAM) of that rate; alone the two are identical,
  so the difference only shows in interference experiments. Fill every source
  buffer with pseudo-random data (never a sparse touch, memset(0) or calloc),
  and check the pattern of any producer before trusting its write rate or the
  harm it causes. Copy sources of the phase-2 producer were 98% zero until
  2026-09-22; `writer.h`, `membench` and the PyTorch producer were not affected.
