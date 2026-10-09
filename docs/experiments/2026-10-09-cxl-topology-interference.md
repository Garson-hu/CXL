# 2026-10-09 — Does traffic to CXL hurt DRAM readers that share a core group with it? (topology-dependent interference)

**STATUS: OPEN — CXL part BLOCKED since 2026-10-09 19:13.** The reboot of 2026-10-07 18:51 reset `/dev/dax0.0`,
`/dev/dax1.0`, `/dev/dax2.0` to `root:root 0600` (no udev rule); the first full run stopped at
`/dev/dax0.0: Permission denied` before measuring anything. Admin request drafted 2026-10-09 (restore `kmem 0660` on
dax0.0/dax1.0 plus a persistent udev rule). DRAM-only pilot done (below).
Raw: `experimental_results/2026-10-09-cxl-topology-interference/` (`machine-state.txt`, `topo-dramonly.txt`,
`topo-dramonly-ccdmap.txt`). Tool: `benchmarks/memory/topo.c` (new; `readcost.c` untouched).

## Question
Every c28 interference experiment so far kept the writer's threads and the neighbour on different core groups
(METHODOLOGY, 2026-08-25: same-CCD threads share one CCD→IO-die port; the main campaign put copy threads on cpus
96–99/112–115 and neighbours on cpus 0–79). arXiv 2503.17864 reports that CXL traffic sharing a core complex with
DDR traffic can cut DDR bandwidth sharply. Does CXL traffic issued from the same core group as a DRAM reader (or
from the paired group) hurt that reader more, per byte, than DRAM traffic from the same place? If so, "writing to CXL
does not hurt DRAM readers" holds only under a thread-placement condition, and the system needs a placement rule.

## What MIKU (arXiv 2503.17864, Yang et al., 2025) does — read from the paper's HTML
- Platforms: Intel Xeon Gold 6530 with two Micron CXL devices; AMD EPYC 9634 with four.
- Cause on Intel: the CHA's request table (ToR) fills with long-latency CXL requests and back-pressures the ingress
  queue, so DDR requests from the same socket starve ("up to 81%" DDR bandwidth loss in the abstract, 89% in §4.2).
  On AMD the paper only states that co-running DDR and CXL work *within a CCX* "similarly led to degraded DDR
  bandwidth, especially for nt-stores", expects the CCX to be the shared structure, gives no AMD number and reports
  no cross-CCD bandwidth experiment.
- Mechanism: per-second Intel uncore counters (ToR occupancy and inserts) estimate CXL service time; when it exceeds
  an offline threshold, threads that access CXL (found via RDT bandwidth monitoring + PEBS address sampling) are
  confined to fewer cores (8 / 4 / 1 cores for loads / stores / nt-stores), then MBA or CPU quotas; it settles in
  ~6–7 s, so it targets phases of tens of seconds.
- Relation to us: MIKU throttles CXL traffic to protect DDR; it does not route writes between tiers and is not
  available on AMD counters as described. Our rule, if the effect is real on c28, would be placement of our own copy
  threads (we choose their CPUs) plus the existing feedback loop.

## Setup
c28, EPYC 9745 (8 CCDs × 16 cores, CCD k = cpus 16k..16k+15, one L3 each), NPS1, idle machine.
Foreground fixed on CCD 4: 4 threads stream through their own 256 MiB DRAM slices (cpus 64–67), then one thread
follows a random 1 GiB chain (cpu 64). Background: T threads (T = 1, 2, 4, 8) of one kind — `cxl_nt` (non-temporal
stores of random data from a 2 MiB cache-resident source into CXL), `copy_cxl` (DRAM→CXL, non-temporal), `cxl_st`
(ordinary stores into CXL), `cxl_rd` (streaming loads from CXL), `dram_nt` and `copy_dram` (the same into DRAM, as
references) — started 0.5 s before and running throughout (their rate is logged for the measured window). Placements:
`same` = cpus 72.. (CCD 4), `near` = cpus 80.. (CCD 5), `far` = cpus 0.. (CCD 0). A CXL-reader foreground runs a
smaller set (T = 8, `cxl_nt`, `copy_cxl`, `dram_nt`). All buffers pre-filled with pseudo-random data.
Full run: 5 repetitions, 3 s stream windows (METHODOLOGY). The DRAM-only pilot used 3 repetitions and 2 s windows.

## Pilot (DRAM-only, 3 repetitions, 2 s; medians; all repetitions within ±1 GiB/s)
Reader alone on CCD 4: 98.2 GiB/s (four threads on one CCD; the same four threads spread over four CCDs read
165 GiB/s on 2026-10-07, so one CCD's link caps a single-group reader at ~98), chain 133.6 ns.

| background, 8 threads | same CCD | paired CCD 5 | other CCD 0 |
|---|---|---|---|
| `dram_nt` (writes 71 / 67 / 78 GiB/s) | 28.4 GiB/s (−71%), chain 217 ns | 77.8 (−21%), 151 ns | 88.7 (−10%), 151 ns |
| `copy_dram` (copies 49 / 50 / 58 GiB/s) | 24.3 (−75%), 170 ns | 69.9 (−29%), 151 ns | 88.3 (−10%), 151 ns |

With 1 thread the same-CCD writer already costs 22% (`dram_nt`) and 29% (`copy_dram`).
CCD map (4 writer threads on each CCD in turn, reader on CCD 4): CCD 0, 1, 2, 3, 6, 7 → −9% to −10% (`dram_nt`,
writers reach 77–78 GiB/s) and −10% (`copy_dram`); CCD 5 → −21% / −29% (writers only 67 / 50 GiB/s); CCD 4 itself →
−60% / −61%. CCD 4 and 5 form a pair (the NPS4 quadrant of 2026-08: cpus 64–95); all other CCDs are equivalent.

## Plan for the CXL part (when access returns)
Full matrix with the default placements (same = CCD 4, near = paired CCD 5, far = CCD 0), 5 repetitions:
`./topo 5 > topo.txt` (~30 min). Interpretation: compare each CXL kind with the DRAM reference of the same placement
and thread count, per GiB/s moved. **The premise holds** if, at every placement, a CXL kind costs the DRAM reader no
more per GiB/s moved than the DRAM reference kind (then what the same and paired CCDs show is the shared CCD link,
which any traffic causes and which our copy-thread placement already avoids), and CXL writes from another CCD stay
near the small loss measured on 2026-10-07 (−4% for a DRAM→CXL copy beside a reader spread over four CCDs). **It needs
a placement condition** if CXL traffic from a shared or paired CCD costs clearly more per byte than DRAM traffic from
the same place (MIKU's queueing effect), or if CXL traffic from other CCDs is not small.
