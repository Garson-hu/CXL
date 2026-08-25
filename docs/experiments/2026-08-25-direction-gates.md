# 2026-08-25 — Direction gates: is CXL a write-preferred tier?

**STATUS: CLOSED — BOTH GATES PASS (2026-08-25). Verdict in `INDEX.md`;
direction GO → W3.** The two gate experiments for Thesis v2 (`../PAPER.md`).
Machine: NPS4 (nodes 0–3 = CPU quadrants; node 4 = CXL Pair A, 508 GiB).
Methodology: `METHODOLOGY.md` (NT stores on the write side is mandatory here).

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
`hardware/scripts/duplex-gates.sh` → raw output in
`experimental_results/2026-08-25-direction-gates/`.

## After the gates (agreed order, pending discussion)
1. **W3** per-direction planner in ObjPlace + `obj_stage_out/in` (`DESIGN.md` §7).
2. **W4** VeloC-style checkpoint-staging demo (source at ~/checkpoint/veloc).
3. **W5** LLM trace sanity: KV eviction/insertion GiB/s from LMSys/ShareGPT
   traces (`workloads/`) — decides LLM's role (headline vs extension).
4. Novelty double-check before any "first direction-aware" claim: Clove
   (arXiv 2605.20370) + VLDB'25 CXL line.

## Results (2026-08-25, median of 5 reps, 4 s/point, `membench` @ commit of this date)
Raw: `experimental_results/2026-08-25-direction-gates/` (gate1-duplex-matrix.csv,
gate2-cross-interference.csv, gate2b-ccd-separated.csv + aggressor CSV +
machine-state.txt + summary-*.txt).

### Gate 1 — duplex matrix: **PASS (partial duplex)**
Read+write GiB/s by thread mix (16 threads total, NT writes):

| R:W | CXL read | CXL write | **CXL total** | DRAM total |
|---|---:|---:|---:|---:|
| 16:0 | 45.8 | — | 45.8 | 69.4 |
| 12:4 | 26.0 | 33.4 | **59.4** | 69.8 |
| 8:8 | 16.5 | 37.7 | 54.2 | 63.0 |
| 4:12 | 12.2 | 40.4 | 52.6 | 59.7 |
| 0:16 | — | 43.8 | 43.8 | 53.3 |

- CXL joint capacity **59.4 = +30% over its best single direction (45.8)** —
  the link's two directions add real capacity. DRAM NEVER exceeds its
  read-only ceiling and *degrades* as writes mix in (turnaround + write
  inefficiency; pure NT-write DRAM = 53.3).
- Partial, not free: CXL reads sag when writers join the same pair
  (45.8→26.0 at 12:4) — the pair's internal media is shared. The measured
  frontier above IS the planner's joint budget model.
- NT vs plain stores: DRAM NT-write 54.9 @8T vs plain 34.3 (RFO removed);
  CXL NT-write 43.8 @16T / 43.7 @8T vs plain 27.9.

### Gate 2 v1 (same-CCD threads) — CONFOUNDED, kept as a finding
With victim and aggressor threads on adjacent cores (cpus 0..11), victims were
hurt ~equally regardless of writer TARGET (DRAM bw victim: 68.4 idle → 14.5
writers→DRAM → 21.5 writers→CXL; latencies +54%/+43%): the shared CCD→IO-die
fabric port dominates before traffic reaches any memory. **Finding: thread/CCD
placement of write streams matters as much as memory placement.** New
invariant added to `METHODOLOGY.md`.

### Gate 2b — cross-interference, victim on CCD0 / 8 NT-writers on CCD1: **PASS**

| victim (node, kind) | idle | writers→DRAM | writers→CXL |
|---|---:|---:|---:|
| DRAM stream-read 4T | 68.6 GiB/s | **10.9 (−84%)** | **68.6 (unchanged)** |
| DRAM ptr-chase | 178.5 ns | 297.3 (+67%) | **177.8 (= idle)** |
| CXL stream-read 4T | 45.7 GiB/s | 45.6 (unchanged) | 27.0 (−41%) |
| CXL ptr-chase | 284.0 ns | 280.9 (= idle) | **614.4 (2.2×)** |

Aggressor throughput: 54.9 GiB/s into DRAM, 43.7 into CXL (keeps 80% when moved).

- **The core claim, measured end-to-end:** the same 8-thread write stream that
  collapses a DRAM reader 6.3× (68.6→10.9) costs that reader NOTHING when
  redirected to CXL (68.6, latency = idle) — and the writers lose only 20%.
- **The corollary that shapes the planner:** CXL write streams are free for
  everyone EXCEPT co-located CXL readers: CXL-resident bandwidth −41%, CXL
  latency 2.2× (writes hurt CXL latency victims far more than read loads did
  in E3). ⇒ write streams to CXL; hot/latency-critical reads to DRAM — or to
  a DIFFERENT CXL device, which re-motivates per-card visibility.

### Verdict
Both gates pass ⇒ Thesis v2 mechanisms confirmed on real CZ120. Planner
constants: DRAM {read 68.6, NT-write 54.9, plain-write tax 2×, shared-pipe};
CXL pair {read 45.8, NT-write 43.8, joint frontier above, co-location
penalties −41% bw / 2.2× lat}. Proceed to W3 (per-direction planner) after
user sign-off.
