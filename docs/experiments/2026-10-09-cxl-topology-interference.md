# 2026-10-09 — Does traffic to CXL hurt DRAM readers that share a core group with it? (topology-dependent interference)

**STATUS: CLOSED 2026-10-10.** The reboot of 2026-10-07 18:51 had reset `/dev/dax*` to `root:root 0600`; the first
full run (2026-10-09 19:13) stopped at `/dev/dax0.0: Permission denied` before measuring anything, so a DRAM-only pilot
ran first. The admin restored `root:kmem 0660` on dax0.0/dax1.0 by hand before 2026-10-10 11:28 (no udev rule: the
next reboot will reset it again); the full run took 2026-10-10 11:28–11:57.
Raw: `experimental_results/2026-10-09-cxl-topology-interference/` (`machine-state.txt`, `topo.txt` = full run,
`topo-dramonly.txt`, `topo-dramonly-ccdmap.txt` = pilot). Tool: `benchmarks/memory/topo.c` (new; `readcost.c`
untouched).

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

## Plan for the CXL part (written 2026-10-09, before the full run)
Full matrix with the default placements (same = CCD 4, near = paired CCD 5, far = CCD 0), 5 repetitions:
`./topo 5 > topo.txt` (~30 min). Interpretation: compare each CXL kind with the DRAM reference of the same placement
and thread count, per GiB/s moved. **The premise holds** if, at every placement, a CXL kind costs the DRAM reader no
more per GiB/s moved than the DRAM reference kind (then what the same and paired CCDs show is the shared CCD link,
which any traffic causes and which our copy-thread placement already avoids), and CXL writes from another CCD stay
near the small loss measured on 2026-10-07 (−4% for a DRAM→CXL copy beside a reader spread over four CCDs). **It needs
a placement condition** if CXL traffic from a shared or paired CCD costs clearly more per byte than DRAM traffic from
the same place (MIKU's queueing effect), or if CXL traffic from other CCDs is not small.

## Results — full run (2026-10-10, 5 repetitions × 3 s, medians; reader alone 98.0 GiB/s, 97.4–98.3 over 15 baselines)
DRAM reader on CCD 4 (4 streaming threads; chain 133.2 ns alone). Reader bandwidth with 8 background threads, and in
brackets the background rate:

| background kind | same CCD 4 | paired CCD 5 | other CCD 0 |
|---|---|---|---|
| `cxl_nt` write CXL | 35.5 (−64%) [43.9] | 83.2 (−15%) [43.0] | 97.7 (−0%) [43.9] |
| `copy_cxl` DRAM → CXL | 21.1 (−78%) [43.9] | 70.4 (−28%) [42.9] | 96.9 (−1%) [43.9] |
| `cxl_st` ordinary stores to CXL | 26.3 (−73%) [26.7] | 92.7 (−5%) [26.9] | 97.9 (−0%) [26.9] |
| `cxl_rd` read CXL | 34.4 (−65%) [39.0] | 86.8 (−11%) [41.6] | 98.1 (+0%) [45.4] |
| `dram_nt` write DRAM | 27.9 (−72%) [71.0] | 78.0 (−20%) [65.9] | 88.1 (−10%) [77.6] |
| `copy_dram` DRAM → DRAM | 24.3 (−75%) [48.8] | 70.2 (−28%) [49.5] | 88.7 (−10%) [57.5] |

Chain latency of the DRAM reader: from CCD 0 every CXL kind leaves it at 133–137 ns (DRAM writes: 148–150 ns); from
CCD 5 the CXL writes leave it at 132–138 ns (DRAM writes: 149–152 ns); from CCD 4 it rises to 199–215 ns for every kind.
With fewer threads (from `topo.txt`): from CCD 0 every CXL kind costs 0–2% at every thread count; from CCD 5 `cxl_nt`
costs 15–16% at 1, 2, 4 and 8 threads (CXL already saturated at ~43 GiB/s with one thread); from CCD 4 `cxl_nt` costs
21 / 29 / 38 / 64% at 1 / 2 / 4 / 8 threads while its rate stays at 43.9 GiB/s from 2 threads on.

CXL reader on CCD 4 (4 streaming threads 45.6 GiB/s, chain 227.8 ns), 8 background threads:

| background kind | same CCD 4 | paired CCD 5 | other CCD 0 |
|---|---|---|---|
| `cxl_nt` | 21.8 (−52%), 587 ns | 29.2 (−36%), 531 ns | 27.7 (−39%), 531 ns |
| `copy_cxl` | 7.8 (−83%), 616 ns | 27.4 (−40%), 536 ns | 29.1 (−36%), 528 ns |
| `dram_nt` | 29.1 (−36%), 267 ns | 45.5 (−0%), 228 ns | 45.9 (+1%), 228 ns |

## Verdict
- **The premise holds under a placement condition.** From a CCD that neither runs the DRAM reader nor is paired with
  its CCD, CXL traffic of every kind — including a DRAM→CXL copy at the full 44 GiB/s — costs the DRAM reader 0–2% in
  bandwidth and nothing in latency, while DRAM writes from the same place cost 10%. This is the regime of every earlier
  campaign (copy threads on CCDs 6–7, neighbours on CCDs 0–4, CCD 5 unused), so those results stand, but they hold
  only for that placement.
- **From the paired CCD**, CXL traffic hurts the reader's bandwidth about as much per GiB/s as DRAM traffic does
  (`copy_cxl` −28% at 43 GiB/s vs `copy_dram` −28% at 50 GiB/s): the two CCDs share a link and any traffic on it
  counts. Unlike DRAM writes, the CXL kinds do not raise the reader's latency from there.
- **From the reader's own CCD, CXL offers no protection and shows MIKU's effect**: with the CXL rate flat at
  43.9 GiB/s, the reader's loss grows from 29% (2 threads) to 64% (8 threads) — the extra threads add only stalled CXL
  requests, which crowd out the reader's requests inside the CCD. At 8 threads the copy to CXL hurts more than the copy
  to DRAM (−78% vs −75%) while moving less.
- **CXL readers are hurt by CXL writes from anywhere** (−36% to −40% bandwidth, chain 228 → ~530 ns from other CCDs),
  confirming the 2.4× of `2026-10-07-read-cost.md` independently of placement; DRAM writes do not touch them unless
  they share the CCD.
- Consequences for the system (proposed, not implemented): the daemon knows the tenants' CPUs (`--tenant-cpus`), so it
  can place its copy threads on CCDs that run no DRAM-sensitive tenant and are not paired with one, and use no more copy
  threads than needed to reach the CXL rate (beyond that they only add stalled requests). When no such CCD exists,
  the copy must be throttled like any other traffic. GPU-to-CXL DMA uses no CPU core and was not tested here.
