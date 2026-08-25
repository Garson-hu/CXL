# Paper: Organization, Claims, Positioning

*The paper-writing reference: thesis, structure, main claims (each with its
evidence in `experiments/`), and how we position against prior work. Literature
scan: `Related.md` (repo root). Status: **direction pivot 2026-08-25**
(advisor-aligned); two gate experiments decide go/no-go — see
`experiments/2026-08-25-direction-gates.md`. History: Change history at bottom.*

## Thesis v2 (2026-08-25) — direction-aware placement

**Every tiering system treats CXL as a slow READ tier for cold data. Its
full-duplex link and the CPU's asynchronous stores make it a WRITE-preferred
tier — and placing data by memory-traffic *direction*, not hotness, unlocks it.**

Three mechanisms, all verifiable on commodity CZ120:
1. **Duplex link.** CXL rides PCIe: separate physical wires per direction. A DRAM
   channel is one shared bus with turnaround penalties. Write traffic on CXL can
   ride a direction readers do not use.
2. **The DRAM write tax is 2×.** A cacheable store = RFO read + writeback: every
   app-level written byte costs two bytes of DRAM bus. Measured exactly: DRAM
   stream-write 34.3 GiB/s = read ceiling 68.8 / 2 (NPS4 node). Moving a write
   stream off DRAM returns *twice* its bandwidth to DRAM readers.
3. **Stores are asynchronous, loads stall.** Store buffers hide CXL's ~287 ns
   latency for writes; loads eat it. Write-heavy objects are the most
   CXL-tolerant objects that exist.

First evidence (2026-08-25): CXL plain-store write 27.9 GiB/s **exceeds the
shared-pipe prediction (45.6/2 = 22.8) by +22%** — partial duplex confirmed;
DRAM fits the shared-pipe model to 0.3%. Framing bonus: the NVM-era rule
("keep writes OFF the far tier" — Optane writes were slow) **inverts** on CXL.

## Working title
Direction-aware memory placement for CXL (system: ObjPlace + per-direction
planner; name TBD). Prior thesis (sensitivity-aware placement) is subsumed as the
foundation — direction is the strongest sensitivity signal.

## Target venues
OSDI'27 / ASPLOS'27 (~Dec 2026), SOSP'27, FAST'28. Zero admin dependency: all
measurements run on node 4 as-is (no BIOS change, no famfs favors).

## Paper structure (planned)
1. **Intro** — tiering is direction-blind; CXL is write-preferred; contributions.
2. **Background** — CXL.mem duplex protocol vs DDR bus; RFO/writeback; NT stores.
3. **Characterization** — the direction matrix on real CZ120 (per-direction
   ceilings, duplex co-run, cross-interference asymmetry, load-vs-store latency
   tolerance) + the May foundation (bandwidth-bound interference 2.0–2.13×).
4. **Design** — ObjPlace with **per-direction bandwidth budgets** (read budget +
   write budget per tier, replacing the single-ceiling pressure model); objects
   declare traffic direction: read-stream / write-stream / RMW-stream; DRAM side
   charges writes 2×. NT-store staging engine for bulk write paths.
5. **Implementation** — userspace + libnuma; extension of existing ~700 LOC runtime.
6. **Evaluation** — microbench matrix; write-heavy use cases: **checkpoint staging
   (VeloC)** as the real-app anchor; synthetic multi-tenant mixes; overhead.
   LLM workloads: later, via reserved extension points (below).
7. **Discussion** — pair granularity (BIOS-gated per-card parked), single host.
8. **Related work** / **Conclusion.**

## Main claims (v2 — D-series; gates pending)
- **D1 (measured).** Per-direction ceilings on real CZ120: read 45.6 GiB/s,
  plain-write 27.9 app-level; DRAM 68.8 / 34.3 per NPS4 node.
- **D2 (measured).** DRAM writes pay exactly 2× (34.3 × 2 = 68.6 ≈ 68.8); CXL
  writes beat the shared-pipe model by +22% — the tiers differ *in kind*.
- **D3 (GATE 1 — pending).** Duplex co-run: reads + NT-writes together clear
  well above the single-direction ceiling on CXL while DRAM stays pinned at its
  one-pipe total.
- **D4 (GATE 2 — pending).** Cross-interference asymmetry: a write stream added
  to DRAM visibly hurts DRAM readers; the same stream on CXL leaves CXL (and
  DRAM) readers ~unharmed. This is the system's core action measured in isolation.
- **D5 (design).** A planner with per-direction budgets beats hotness-only and
  single-budget placement whenever write streams are present.
- **D6 (use case).** Checkpoint staging on CXL (VeloC pattern): app slowdown
  during checkpoint shrinks vs DRAM staging, at equal or better checkpoint time.

**Do NOT claim:** CXL write bandwidth > read bandwidth (false on CZ120: 27.9 vs
45.6); "first LLM-on-CXL"; any active-decode KV-on-CXL benefit (read-latency
trap); per-card results (hardware still pair-interleaved).

## Foundation (May 2026, all survived — feeds §3–§4)
C1 bandwidth is the binding constraint (latency 1.5×, BW 35.5/pair). C2 CXL
co-tenant interference 2.0–2.13× bandwidth-bound / ≤1.23× latency-bound / ~1.0×
DRAM. C3 ObjPlace = manual ±1% @ ~0% overhead. C4 +14.3% vs interleave, +315%
recovery under aggressor. C5 +118% vs hotness-only. C6 pressure-aware
(+67%→+116%). Evidence: `experiments/2026-05-19-baseline-objplace.md`.

## LLM extension points (interfaces now, implementation later — 2026-08-25)
Design so LLM support plugs in without rework; do not build it yet:
- **Object classes** (extend `obj_type_t` / attrs): `KV_EVICT` (write-once
  park, read-once resume), `PREFIX_INSERT` (write-once, read-on-hit,
  promote-on-hit), `OPT_STATE` (1:1 RMW stream — the duplex sweet spot).
- **Direction attr** on `obj_attr_t`: `dir ∈ {READ_STREAM, WRITE_STREAM, RMW}` —
  the planner keys on it; LLM classes are presets over it.
- **Phases already exist** (`PREFILL/DECODE/GATHER` in `phase_t`) — keep.
- **Staging API**: `obj_stage_out(h)` / `obj_stage_in(h)` — NT-store bulk copy
  DRAM↔CXL off the critical path (the KV-eviction / checkpoint verb).
- **Promote-on-hit hook**: callback when a CXL-resident object turns read-hot.
Rationale recorded in WORKLOG session 14: active-decode KV stays in DRAM (read
trap); the LLM story rides eviction/insertion/optimizer streams.

## Positioning (delta over `Related.md`)
- **Characterization** (Demystifying CXL MICRO'23, Micron/Intel white paper,
  VLDB'25 studies): document R/W behavior; build nothing on it. We build the
  placement system.
- **Tiering** (TPP, MEMTIS, Colloid, Nomad, SoarAlto, Memstrata): hotness/
  contention signals, single bandwidth number per tier, direction-blind. Nomad's
  dirty-page migration pain is *evidence for* write-direction awareness.
- **KV-offload systems** (Mooncake, AttentionStore, LMCache): move KV to slower
  tiers but direction-blind, RDMA/SSD-oriented; none exploit duplex.
- **NVM-era write avoidance** (HeMem etc.): inverted premise — we show the rule
  flips on CXL. Clean narrative hook.
- Prior deltas retained: online hint-driven vs SoarAlto's offline profiles;
  object granularity vs Memstrata's VM/page; real CZ120 vs emulation.
- **One-line delta: first system to use memory-traffic *direction* as the
  placement signal, validated on real CXL silicon.** (Verify against Clove +
  VLDB'25 line before writing intro — flagged in
  `experiments/2026-08-25-direction-gates.md`.)

## Parked (revive only if an app demands or hardware unlocks)
Per-card placement / interleave adaptation (Ideas 1–3 original form): BIOS
de-interleave still gated (NPS4 reboot did not change CXL decoders); twins gap
+34% and quadrant-affinity confirmation stay as supporting characterization.
Cross-pair E2 still blocked on famfs access. Details:
`experiments/2026-08-11-percard-prelim.md`.

## Change history (append-only — never rewrite entries)
- **2026-05-20** — Thesis v1: sensitivity-aware CXL placement (bandwidth is the
  scarce resource; sensitivity + skew beat hotness as signals). Claims C1–C6
  established, all evidence-backed.
- **2026-07-08** — Direction confirmed as device-granular CXL management
  (per-card placement / isolation / adaptive interleaving) after the 97-paper
  verified review.
- **2026-08-25** — Thesis v2: direction-aware placement (CXL = write-preferred
  tier: duplex link, 2× DRAM write tax, async stores). Per-card form parked
  (BIOS-gated, advisor lukewarm). LLM support scoped to reserved interfaces.
  C-claims kept as Foundation; D-claims added, D3/D4 gated on
  `experiments/2026-08-25-direction-gates.md`.
