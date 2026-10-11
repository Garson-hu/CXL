# 2026-10-06 — Optane control: does sending writes to persistent memory spare DRAM readers, as CXL does?

**STATUS: CLOSED 2026-10-11** (planned 2026-10-06 in `2026-10-06-why-evidence.md`; run 2026-10-11 10:41–10:55, Slurm job
310708 on c35). Raw: `experimental_results/2026-10-06-optane-control/` (`matrix.csv` = the 4-thread DRAM reader,
`aggressor.csv` = the writers' own rates, `machine-state.txt`, `stderr.log`); attempt 1 (2026-10-10, job 304547) in
`attempt1-socket0-pm-not-found/`. Script: `hardware/scripts/optane-control.sh`; summary: `hardware/scripts/summarize-optane-control.py`.

## Setup
c35: 2 × Xeon Silver 4215 (Cascade Lake, 8 cores each, no SMT), DDR4; persistent memory (Optane DCPMM) exposed as a
CPU-less NUMA node 3 (514 GB, KMEM-DAX system RAM) attached to socket 1 (distance 17 from node 1, 28 from node 0).
Everything on socket 1: a 4-thread streaming DRAM reader on node 1's first 4 cores; 1, 2 or 4 writer threads on its
other cores, writing node-1 DRAM or node-3 persistent memory with non-temporal (`stream-write-nt`) or ordinary stores
(`stream-write`); membench, data-carrying lines, 3 repetitions (medians; all within 1% unless stated).
Attempt 1 read the NUMA distance table by position, failed on node ids 0, 1, 3, left the PM node empty and measured
socket-0 DRAM only; fixed 2026-10-11 (`--cpu-node` added to membench, default unchanged).

## Results
Write capacity alone (GiB/s at 1 / 2 / 4 / 8 threads): DRAM NT 4.7 / 9.2 / 17.7 / 34.4, DRAM plain 10.1 / 19.8 / 32.5 /
36.5; **PM NT 4.4 / 7.3 / 7.3 / 7.0, PM plain 1.8 / 2.0 / 1.8 / 1.7**. Read, 8 threads: DRAM 68.2, PM 20.3 GiB/s.

The 4-thread DRAM reader (39.9 GiB/s alone) beside writers on the same socket (writers' own rate in brackets):

| writers | 1 thread | 2 threads | 4 threads |
|---|---|---|---|
| DRAM, NT | 38.3 (4.6) | 37.6 (9.1) | 36.7 (17.8) |
| **PM, NT** | 37.1 (4.3) | 34.4 (7.2) | 35.3 (7.2) |
| DRAM, plain | 37.1 (9.8) | 34.5 (18.8) | 23.8 (29.0) |
| **PM, plain** | 34.2 (1.7) | 12.4 (2.0; reps 11.1–12.9) | **1.9 (1.8; reps 1.8 / 19.1 / 1.9)** |

## Verdict
- Persistent memory absorbs at most ~7 GiB/s of non-temporal writes per socket (ordinary stores ~2 GiB/s), against
  34–37 GiB/s for DRAM and ~44 GiB/s for c28's CXL pair: it cannot take a checkpoint or KV burst.
- Redirecting writes to it does **not** spare the DRAM reader on the same socket — it hurts more per byte: NT writes to
  PM cost the reader 11.5% at 7.2 GiB/s where NT writes to DRAM cost 8% at 17.8 GiB/s; ordinary stores to PM cut the
  reader from 39.9 to 12.4 GiB/s (2 writers) and to 1.9 GiB/s (4 writers, two of three repetitions) while moving only
  ~2 GiB/s. PM shares the socket's memory controllers with DRAM, so its slow writes occupy them (MT², FAST'22). On c28
  the same redirection into CXL costs a DRAM reader on another CCD 0–2% (`2026-10-09-cxl-topology-interference.md`).
- One machine, one socket, membench only; the unstable repetition (19.1 GiB/s) is reported as measured.
