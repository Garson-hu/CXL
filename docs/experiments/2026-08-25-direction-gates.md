# 2026-08-25 — Direction gates: is CXL a write-preferred tier?

**STATUS: ACTIVE.** The two gate experiments for Thesis v2 (`../PAPER.md`):
they decide whether the direction-aware pivot proceeds. Machine: NPS4 (nodes
0–3 = CPU quadrants; node 4 = CXL Pair A, 508 GiB). Methodology:
`METHODOLOGY.md` (NT stores on the write side is mandatory here).

## Motivation (measured 2026-08-25, W0 quick-look)
| | read (stream) | plain-store write | shared-pipe prediction | actual vs prediction |
|---|---:|---:|---:|---:|
| DRAM node 0 @8T | 68.8 GiB/s | 34.3 GiB/s | 34.4 (= read/2) | **exact fit (−0.3%)** |
| CXL node 4 @8–16T | 45.6 GiB/s | 27.9 GiB/s | 22.8 (= read/2) | **+22% above** |

A plain store = RFO read + writeback (2 bytes of traffic per written byte).
DRAM fits the one-shared-pipe model exactly; CXL exceeds it — first evidence its
two link directions add capacity. Third mechanism (not bandwidth): stores are
asynchronous (store-buffer-hidden), loads stall ~287 ns.

## Gate 1 — duplex matrix
**Hypothesis:** CXL's two link directions are independent resources; risk = the
device serializing internally (shared DRAM bus behind the controller).
**Setup:** one `membench --mode=duplex` process: R stream-read threads + W
NT-write threads, separate buffers, same node. Sweep R:W = 16:0, 12:4, 8:8,
4:12, 0:16 on node 4; identical sweep on node 0 as control.
**Pass:** read side holds near solo level while writes add on top; CXL
aggregate clearly > 45.6 single-direction ceiling (target ≥ ~60 GiB/s). DRAM
control: aggregate pinned ≈ 69 at every mix.
**Fail:** CXL aggregate stuck ≈ 45–55 with reads sagging ⇒ device serializes ⇒
thesis falls back to "async stores + capacity" (weak — rethink before building).
**Byproduct:** the planner's per-direction budget constants (`DESIGN.md` §7).

## Gate 2 — cross-interference asymmetry
**Hypothesis:** the system's core action — move write streams DRAM→CXL — helps
DRAM readers (the 2× tax refund) and does not hurt CXL readers (opposite link
direction).
**Setup A (DRAM victim):** victim = ptr-chase latency AND 4T stream-read on
node 0. Worlds: idle · +8T NT-writers→node 0 · +8T NT-writers→node 4.
**Setup B (CXL victim):** victim = ptr-chase AND 4T stream-read on node 4.
Worlds: idle · +8T NT-writers→node 4 · +8T NT-writers→node 0.
Disjoint cores throughout; single process (`loaded-latency
--aggressor-kind=write-nt --aggressor-node=N`) or two processes with
`--cpu-offset`.
**Pass:** DRAM victim visibly hurt by DRAM writers and ~unhurt when the same
writers target CXL; CXL victim ~unhurt by CXL writers.
**Fail modes:** (a) DRAM victim never hurt ⇒ benefit exists only under
saturation — scope claims to loaded servers; (b) CXL victim badly hurt ⇒
consistent with Gate-1 fail. **Watch victim tails**, not just means (E3
showed medians move first).

## Tooling status
`membench` extension IN PROGRESS (approved scope, not yet finished): modes
`stream-write-nt` + `duplex` (`--write-threads`, `--write-node`) and
`loaded-latency --aggressor-kind/--aggressor-node`; enum/option stubs are in,
kernels + dispatch + split reporting pending. Driver:
`hardware/scripts/duplex-gates.sh` (to be written) → log
`hardware/results/<date>-duplex-gates.log`.

## After the gates (agreed order, pending discussion)
1. **W3** per-direction planner in ObjPlace + `obj_stage_out/in` (`DESIGN.md` §7).
2. **W4** VeloC-style checkpoint-staging demo (source at ~/checkpoint/veloc).
3. **W5** LLM trace sanity: KV eviction/insertion GiB/s from LMSys/ShareGPT
   traces (`workloads/`) — decides LLM's role (headline vs extension).
4. Novelty double-check before any "first direction-aware" claim: Clove
   (arXiv 2605.20370) + VLDB'25 CXL line.

## Results
*(pending — appended here when the gates run)*
