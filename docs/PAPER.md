# Paper: Organization, Claims, Positioning

*The paper-writing reference: thesis, structure, main claims (each with its
evidence in `experiments/`), and how we position against prior work. Literature
scan: `Related.md` (repo root). Status: **Thesis v3 framing agreed 2026-09-18**
(horizontal write path, PolyStore-inspired) — DESIGN PHASE, no experiments until
the design is agreed. Thesis v2 (2026-08-25, both gates passed) is its measured
foundation. History: Change history at bottom.*

## Thesis v3 (2026-09-18) — the horizontal write path (DESIGN-ONLY, user-agreed framing)

*Builds on Thesis v2 below (its three mechanisms and D-claims stay valid and
become the characterization). v3 changes the FRAMING and the SYSTEM, following
the paper shape of PolyStore (FAST'25; notes in `Related.md`): one strong
phenomenon → a practical but "systems-heavy" design → large effect. No
experiments are scheduled until the design in `DESIGN.md` §10 is agreed.*
*(O2 below names LULESH as the headline application; per the user it is a
candidate only — any application meeting the criterion in the evaluation plan
can take its place.)*

**The phenomenon, in one sentence.** Today every bulk write lands in DRAM first
(checkpoint staging buffers, CPU-side KV-cache pools, tiering systems that
demote only after data turns cold), although most of that data is never read
again, and the act of writing it into DRAM slows down every other program that
is reading DRAM at the same time.

**The thesis.** DRAM should not always be the first stop of the write path.
Use DRAM and CXL side by side ("horizontally", PolyStore's word) and divide the
work by traffic direction: rarely-read write streams go straight to CXL and
never touch DRAM; DRAM bandwidth is kept for programs that read. We manage the
whole path of a bulk write, from the moment the application produces it until
it rests on NVMe (checkpoint: application memory → staging → NVMe; KV cache:
GPU → CPU-side pool → colder storage).

**Role of PolyStore (user ruling 2026-09-18): a source of ideas, NOT a
comparison method or baseline.** We study it and carry its ideas into memory.
What we borrow: using devices side by side instead of stacked; splitting one
object into segments placed on different devices; re-measuring every short
epoch and reassigning writers; migrating only when the target device has
headroom; cache rules chosen per device; and its paper shape. What has to
change when the devices are memories, because of what we measured: (a) on DRAM,
reads and writes share one pipe and writes hurt reads disproportionately;
(b) on CXL, the read direction and the write direction are largely independent;
(c) moving hot data up into DRAM is itself a write stream into DRAM, which is
exactly the traffic that slows DRAM readers. So the borrowed epoch mechanism
gets a different objective — make the write stream as fast as possible while
other DRAM readers slow down by no more than a bound — and the per-device cache
rule comes out as: writes bypass DRAM, only repeated reads may use DRAM. The
paper cites PolyStore as related work and as the origin of these ideas; the
intro, the novelty argument and the baselines are NOT built around it.

**Where the gain comes from.** Our usable device pair (dax0.0/dax1.0, the same
two cards) accepts about 44 GiB/s of NT writes while the DRAM socket accepts
about 273 GiB/s, so simply adding the two bandwidths gains only ~15%. The gain
comes from SEPARATING read traffic from write traffic (DRAM readers are no
longer slowed, and 60–80% of written data never enters DRAM), not from adding
bandwidth. The paper must say this explicitly.

### Motivation (§3 of the paper) — three observations, one figure each
These are facts that hold WITHOUT our system; they answer "what is wrong with
today's practice".
- **O1. Most data written into DRAM is never read again, so the DRAM write is
  wasted.** 60–80% of KV-cache blocks are never read after being written
  (three production traces, `experiments/2026-09-09-kv-trace-analysis.md`);
  checkpoints are read only after a failure. Figure exists.
- **O2. A program that writes heavily into DRAM slows down other programs that
  read DRAM.** Headline figure MUST be a real application that already uses
  most of the DRAM bandwidth (all-core LULESH) taking a realistically sized
  checkpoint, showing how much its own compute step slows down. The synthetic
  result (4 CCDs of NT writers, ~273 GiB/s → DRAM reader 12× slower,
  `experiments/2026-09-14-stencil-3c.md` and the write-tier campaign) goes
  beside it as the worst case. This figure design is our answer to the
  reviewer objection "real write streams never saturate DRAM" (reviewer
  question 5): we do not claim saturation; we show that a moderate write burst
  hurts an application that is already bandwidth-bound. **Figure NOT yet
  measured — first experiment once the design is agreed.**
- **O3. The same write stream sent to CXL does not slow down DRAM readers.**
  Microbenchmark: DRAM reader back to idle speed when the write stream moves to
  CXL (D4). Stencil proxy: application resident in DRAM slows 0–5% while the
  write stream saturates CXL (`experiments/2026-09-14-stencil-3c.md`). The
  point is "DRAM readers are not slowed"; idle CXL write bandwidth is mentioned
  only in passing (see sizing above).

Reviewer question 1 (DRAM capacity is short) is background: one paragraph plus
citations, not an observation.

### What belongs to the evaluation, not the motivation
These can only be answered WITH the system (its cost, and comparison with
alternatives):
- Cost to the writer: how much longer a checkpoint / KV insert takes when it
  goes to CXL instead of DRAM (reviewer question 3, second part). Not measured
  on a real application yet.
- Cost of reading back from CXL (question 6); it also sets the promote rule in
  the design. Known so far: stencil proxy reads a CXL buffer ~20% slower than
  DRAM; copying it back to DRAM first is ~2× slower.
- Rate-limiting the writer instead of moving it (question 7): a BASELINE in
  the evaluation (throttle the checkpoint until DRAM readers are unaffected,
  compare checkpoint duration). One sentence in the intro, not in motivation.
- A write stream on a CXL card slows readers of the SAME card (−41% bandwidth,
  2.2× latency; different cards: no effect — D4 corollary, D7) (question 9):
  a design CONSTRAINT plus one small experiment. With only dax0.0/dax1.0
  usable (same two cards) new experiments cannot show card separation; cite
  the 2026-09-02 data.
- Question 8 (why not write straight to NVMe) and question 10 (single AMD
  machine): one paragraph each in Discussion. Note that v3 brings NVMe back
  into scope as the END of the write path, not as an alternative to CXL.

### Evaluation plan (four parts; structure borrowed from PolyStore)
1. Microbenchmark: one write stream split between DRAM and CXL at several
   ratios (all DRAM, 70/30, 50/50, all CXL) beside a DRAM reader; plot writer
   speed and reader slowdown. Shows that a "maximize total bandwidth" policy
   and our policy choose different ratios — candidate core figure.
2. Per-component: dynamic vs fixed placement; with vs without the promote
   rule; drain thread reading CXL vs reading DRAM.
3. Real applications (SET NOT FIXED — user 2026-09-18: LULESH + VeloC is
   exploratory and is replaced if weak; criterion = a DRAM-bandwidth-bound
   victim co-located with a real bulk write stream; LLM checkpoint via PyTorch
   async checkpoint with the multi-GPU stream emulated by CPU threads and a
   CPU-optimizer victim, see `DESIGN.md` §10.9). Candidates: all-core LULESH + large VeloC checkpoint; trace-driven
   KV-cache inserts beside a program that reads like LLM inference; optional
   third: Redis snapshot (also a large write burst; PolyStore used Redis).
4. Baselines: all-DRAM (today's practice); all-CXL; rate-limited writer;
   kernel tiering if CXL can be onlined as a NUMA node (needs root — not
   possible today).

**Hardware scope.** c28 (DRAM + CXL + 3.5 TB Solidigm NVMe at `/mnt/local`) is
the main platform. c35/c36 (DRAM + 1 TB Optane PM, no CXL) are a SUPPLEMENTARY
configuration only: the same runtime should make the opposite decision there
(buffer writes in DRAM, read PM directly), which shows the policy follows each
device's per-direction characteristics rather than CXL-specific rules. Optane
is discontinued, so this is not a headline result.

**Main risk.** Expected effects today are "DRAM readers slow 0–5% instead of
20–30%" and "60–80% less data written into DRAM" — real but not multiples. The
real-application gap is unknown until the O2 figure is measured; if it is
small, rethink before building.

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

## Paper structure (planned — v3, modelled on PolyStore FAST'25, user request 2026-09-18)
PolyStore's shape: §3 a SHORT pitfall analysis (one table, one figure) → §4.1
goals, each driven by numbered principles → §4.2 overview mapping every
principle to a named component + one architecture figure → one subsection per
component → §5 evaluation opened by questions, one per component, then
microbenchmarks, sensitivity, real applications. We follow it; the motivation
carries the "why", every design choice points back to an observation.
1. **Introduction** — phenomenon in one sentence; why it is wrong now (CXL
   exists, its write direction is cheap and harmless to DRAM readers); the
   approach; contributions.
2. **Background** — DRAM read/write share one pipe (write drain mode); CXL.mem
   directions; how bulk writers work today (checkpoint staging, KV CPU pools,
   tiering demotion). DRAM capacity pressure: one paragraph + citations.
3. **DRAM-first pitfalls (motivation)** — Table 1: today's bulk writers, first
   stop of their data, share read again, extra traffic they cause. Then three
   observations, one figure each, each ending in an implication:
   O1 most written data is never read ⇒ DRAM should be spent on reads only (G2);
   O2 heavy DRAM writes slow DRAM readers, shown with a real bandwidth-bound
   application, synthetic worst case beside it ⇒ writes must leave DRAM (G1);
   O3 the same writes on CXL leave DRAM readers unaffected ⇒ CXL can be the
   first stop (G1). Closing paragraph: why simple fixes fall short (rate
   limiting lengthens the checkpoint; raw devdax has no allocator; kernel
   tiering still writes DRAM first) ⇒ G3 and the need for a system.
4. **Design** — 4.1 goals G1–G3 and principles P1–P4; 4.2 overview + figure;
   4.3 Component A segment store on raw CXL; 4.4 Component B
   interference-bounded placement; 4.5 Component C read path; 4.6 Component D
   DRAM-free drain and recovery; 4.7 clients (file checkpoint, GPU checkpoint,
   KV layer). Detail: `DESIGN.md` §10.
5. **Implementation** — userspace library + background process, no root;
   shims for VeloC, PyTorch async checkpoint, a KV layer.
6. **Evaluation** — opens with questions: (Q-A) what does the segment store
   cost, and how much space is wasted without compaction? (Q-B) does placement
   keep DRAM readers within the bound, and what does the writer pay, versus
   all-DRAM, all-CXL and a rate-limited writer? (Q-C) does break-even promotion
   beat always/never promote? (Q-D) does the drain stay off DRAM, and how fast
   is recovery from CXL vs NVMe? (Q-E) do real applications benefit? Then:
   microbenchmarks, parameter sensitivity (bound, step, epoch, segment size),
   per-component, real applications, PM configuration as supplement.
7. **Discussion** — why not NVMe directly; single platform; one CXL card pair;
   GPU→CXL write cap.
8. **Related work / Conclusion.**

## Main claims (v2 — D-series; gates pending)
- **D1 (measured).** Per-direction ceilings on real CZ120: read 45.6 GiB/s,
  plain-write 27.9 app-level; DRAM 68.8 / 34.3 per NPS4 node.
- **D2 (measured).** DRAM writes pay exactly 2× (34.3 × 2 = 68.6 ≈ 68.8); CXL
  writes beat the shared-pipe model by +22% — the tiers differ *in kind*.
- **D3 (measured 2026-08-25 — Gate 1 PASS).** Duplex co-run on CXL: 59.4 GiB/s
  joint (26.0 read + 33.4 NT-write at 12:4) = **+30% over the best single
  direction (45.8)**; DRAM never exceeds its one-pipe ceiling and degrades as
  writes mix in (69.8→53.3). Partial duplex: shared internal media, frontier
  measured.
- **D4 (measured 2026-08-25 — Gate 2b PASS, CCD-separated).** The 8-thread
  write stream that collapses a DRAM reader 6.3× (68.6→10.9 GiB/s) costs that
  reader NOTHING when redirected to CXL (68.6, latency 177.8 ns = idle);
  writers keep 80% (54.9→43.7). Corollary: CXL co-located readers DO pay
  (−41% bw; chase 2.2×) ⇒ separate write streams from hot reads across
  tiers/devices. Bonus finding: same-CCD victim/aggressor threads share a
  fabric port that dominates everything — thread placement is part of the
  system design.
- **D5 (design).** A planner with per-direction budgets beats hotness-only and
  single-budget placement whenever write streams are present.
- **D6 (use case).** Checkpoint staging on CXL (VeloC pattern): app slowdown
  during checkpoint shrinks vs DRAM staging, at equal or better checkpoint time.

- **D7 (measured 2026-09-02 — card-vs-card, Pair B via dax offsets).** Two CXL
  cards behind one host bridge are isolation domains: neighbor-card reads or
  saturating NT writes leave a latency victim at 0% change (225 ns), cost a
  bandwidth victim ≤6% (reads) / 0% (writes); same-card costs 1.9–2.1× latency,
  −51% bw. Card-level duplex ≈ +55% joint. First real-HW card-granularity CXL
  interference data. Enables "write streams get their own card".

**Do NOT claim:** CXL write bandwidth > read bandwidth (false on CZ120: 27.9 vs
45.6); "first LLM-on-CXL"; any active-decode KV-on-CXL benefit (read-latency
trap); per-card results on Pair A (root-hashed, unsplittable) — per-card
claims are Pair-B-only (dax offsets) until per-card NUMA exists.

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
- **PolyStore (FAST'25)** — related work and the origin of several of our
  ideas (horizontal device use, segment index, epoch rebalancing, per-device
  cache rules); a storage system for PM/NVMe/SATA, NOT a baseline and NOT the
  foil of the paper. Credit it where an idea is borrowed; our contribution is
  stated on its own terms (direction and interference in memory).
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
- **2026-08-25 (later)** — BOTH GATES PASSED same day: D3 = +30% duplex joint
  capacity; D4 = total DRAM-reader relief (idle-equal) at 80% writer
  throughput, with the CXL co-location penalty and the CCD fabric-port finding
  added. D5 planner design unblocked; W3 next pending user sign-off.
- **2026-09-02** — Per-card capability arrived without per-card NUMA: Pair B
  addressable per card via /dev/dax2.0 offsets (plain 256 B stripe proven
  2026-09-01); card-vs-card interference measured (D7): cards are isolation
  domains. The parked per-card direction un-parks as a mechanism INSIDE Thesis
  v2 (write streams to their own card), not a separate thesis.
- **2026-09-18** — Thesis v3 framing (user-agreed, design-only): the horizontal
  write path. One phenomenon (every bulk write lands in DRAM first; most is
  never read; the write slows DRAM readers), PolyStore-shaped paper
  (phenomenon → systems design → effect). The ten reviewer questions split into
  MOTIVATION (three observations O1–O3; question 5 answered by the O2 figure
  design) and EVALUATION (writer cost, read-back cost, rate-limit baseline,
  same-card constraint); questions 8 and 10 → Discussion. Scope widened to the
  whole write path ending on NVMe; PM nodes c35/c36 supplementary only. Gain is
  from separating directions, not adding bandwidth (~15% additive on
  dax0.0/dax1.0). Design: `DESIGN.md` §10. No experiments until design agreed.
- **2026-09-18 (later)** — User correction: PolyStore is a paper to learn from
  and borrow ideas from, not a comparison method. Removed the "how this differs
  from PolyStore (must be in the intro)" framing and the multiplier comparison;
  replaced with "Role of PolyStore" (what we borrow / what must change in
  memory) and a related-work entry that credits it.
- **2026-09-18 (design consolidation)** — Evaluation applications declared
  open (LULESH + VeloC exploratory only); LLM checkpoint added as a target
  workload (PyTorch async checkpoint; emulated multi-GPU stream + CPU-optimizer
  victim because c28 has one 12 GiB/s GPU). Design detail: `DESIGN.md` §10.
- **2026-09-18 (structure)** — Paper structure rewritten on PolyStore's
  format at the user's request: short pitfall-style motivation (table + three
  observations, each ending in an implication), goals → principles → four
  components, evaluation opened by per-component questions. Replaces the v2
  outline.
