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
  status, date. Raw logs are append-only dated files in `hardware/results/`.
- **CPU pool = node 0** (NPS4: 64 logical CPUs) for membench/cxlprobe unless
  the experiment is about quadrant affinity.
- Planner pressure default = saturated (conservative) for ObjPlace runs.
