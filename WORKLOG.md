# Worklog — primary progress tracker

**This is the main place to track the project.** Open this first: the Current
Status below tells you where we are; the Session Log is the reverse-chronological
history. For depth, open only the core docs (see the Doc Map). Keep `docs/` lean —
new findings go here in WORKLOG, not into new scattered files.

---

## Current Status (2026-08-25)

**Project.** CXL + LLM systems research for a top systems venue (OSDI/ASPLOS'27,
SOSP'27, FAST'28). On `c28` directly.

**Direction — v2 PIVOT (2026-08-25, advisor-aligned):** *Direction-aware memory
placement* — CXL's full-duplex link + asynchronous stores make it a
**write-preferred tier**; place objects by memory-traffic *direction*
(read-stream / write-stream / RMW), with per-direction bandwidth budgets in the
ObjPlace planner. Zero admin dependency (runs on node 4 as-is). Two GATE
experiments decide go/no-go (duplex matrix; cross-interference asymmetry) — specs
in `docs/experiments/2026-08-25-direction-gates.md`. LLM support = reserved
interfaces only for now
(KV-evict / prefix-insert / optimizer-RMW classes; see `docs/PAPER.md`). Prior
per-card direction (Ideas 1–3, confirmed 2026-07-08) is PARKED: BIOS
de-interleave remains gated; twins +34% and quadrant affinity become supporting
characterization. First evidence for v2: DRAM writes pay exactly the 2× RFO tax
(34.3 = 68.8/2); CXL plain-writes beat the shared-pipe model by +22%.

**Hardware (REBOOT #3 ~2026-08-27, verified 2026-08-28 — log
`hardware/results/2026-08-28-post-reboot-fused-node.log`).** AMD EPYC 9745
Turin, back to **NPS1** (node 0 = all 256 CPUs + 773 GB DRAM, now 151.9 ns —
faster than every prior config, older DRAM baselines stale). **ALL CXL fused
into node 1 (~1018 GiB, all three dax regions system-ram): 238.6 ns, 46.9 @8T /
48.7 @32T GiB/s** (matches Pair-A striped ceiling — allocator placement across
pairs not controllable from userspace). **famfs GONE** (DeepTier off the box —
constraint lifted). **2026-09-01: dax2.0 = DEVDAX, root:kmem 0660, mmap-able by ghu4; node 1 = Pair A only
(508 GiB). Pair B = plain 256 B stripe, card=(off>>8)&1 — PER-CARD TARGETING WORKS via
dax offsets** (`docs/experiments/2026-09-01-pairb-address-map.md`). Pair A still 2-way
root-hashed (unsplittable). Gate results (08-25, NPS4 node 4 = Pair A
alone) remain valid device physics; W3 baselines must be re-measured. GPU 1×
RTX 4060 Ti 8 GB. No MLC — custom `membench` + `cxlprobe`.

**What is built.** `system/placement/`: ObjPlace runtime (`objplace.{h,c}`,
`libobjplace.so`), benchmarks `bwbench` / `gnnbench` / `sensbench` / `mixbench`,
overhead `obench`, `test_objplace`. `benchmarks/`: `membench` (C) + Python
orchestrators (`phase21/22`, `confirm`, `integ`, `eval_objplace`, `eval_block2`) +
`embbench.py` (ctypes bridge to ObjPlace).

**Headline results** (full tables: `docs/RESULTS.md`). CXL latency 1.53× DRAM, BW
35.5 GiB/s. Bandwidth-bound CXL victim 2.0–2.13× under co-runner (latency-bound
≤1.23×, DRAM ~1.0×). ObjPlace = manual ±<1%, +14.3% vs interleave (skewed
embedding), +315% bandwidth recovery, +118% vs hotness-only, pressure-aware
(+67%→+116%), overhead ~0%. GNN skewed +8.3% / uniform −11.6%.

**GATES PASSED (2026-08-25).** G1 duplex: CXL joint 59.4 GiB/s vs 45.8 single
(+30%); DRAM pinned/degrading — write direction is real added capacity. G2b
(CCD-separated): write stream moved DRAM→CXL costs the DRAM reader NOTHING
(68.6 GiB/s = idle; 10.9 under DRAM writers = 6.3× collapse), latency idle-equal,
writers keep 80%. CXL co-located readers pay (−41% bw; chase 2.2×). Bonus: same-CCD
victim/aggressor threads share a fabric port that dominates cross-node interference
— now a methodology invariant. Full tables:
`docs/experiments/2026-08-25-direction-gates.md`.

**Open issues / honest gaps.** Novelty double-check pending (Clove, VLDB'25 line).
Multi-tenant evidence still synthetic. No established-baseline comparison yet
(TPP/MEMTIS/Colloid/Nomad). NPS4 invalidated all NPS1 DRAM baselines. Old parked
gaps unchanged (INTERLEAVE candidate, per-card access, KV claim).

**Per-card unlocked (2026-09-02).** Pair B addressable per card via /dev/dax2.0 offsets; cards
measured as isolation domains (`docs/experiments/2026-09-02-pairb-card-interference.md`).
The parked per-card direction is no longer blocked — it merges into the direction-aware
thesis as "place write streams on their own card".

**Next step (critical path) — CAMPAIGN PLAN 2026-09-08:** the four-phase plan +
PolyStore integration lives in `docs/experiments/2026-09-08-write-tier-campaign.md`
(ACTIVE umbrella; per-phase TODO with statuses — READ IT FIRST). Order: 1a mechanism
write-up → 2b CXL 1/2/4-card scaling → 3a/3b stencil (all DRAM-independent) →
[BIOS: Memory Interleaving back to Auto] → 1b DRAM write-drain matrix → 3c → 4 LULESH/
VeloC → 5 PolyStore. Blockers: DRAM interleave disabled (2026-09-08 log); PolyStore PDF;
LULESH version. Each step needs explicit user approval before execution.

**Doc Map (reorganized 2026-08-25 — rules in `docs/README.md`).**
- `WORKLOG.md` (this file) — status + history. **Start here.**
- `docs/PAPER.md` — thesis, claims, positioning (living; append-only Change history).
- `docs/DESIGN.md` — CURRENT system design + API (living; append-only Change history).
- `docs/experiments/INDEX.md` — one row per experiment: date, question, verdict, link.
- `docs/experiments/YYYY-MM-DD-<content>.md` — one file per experiment; ONE active,
  frozen once closed. `METHODOLOGY.md` holds the shared invariants.
- `docs/guides/STUDY_GUIDE_OBJPLACE_DETAILED.md` — code-level onboarding walkthrough.
- `docs/slides/` — dated decks.
- `Related.md` (repo root) — literature scan (2026-05-20; superseded for coverage by the 2026-07-08 review).
- `DEEP_RESEARCH_2026-07-08-cxl-landscape.html` (repo root) — 97-paper verified map + gap analysis (Part I) + ranked research directions + 8-week plan (Part II). **The reference document for related work and claims.**
- `benchmarks/results/2026-07-08-cxl-lit-review.json` — machine-readable records for all 97 papers (evidence quotes, corrections).
- `docs/archive/` — superseded per-phase notes (kept for reference, not maintained).

---

## Session Log

### 2026-09-02 (session 16) — Card-vs-card interference: cards ARE isolation domains
**Experiment** `docs/experiments/2026-09-02-pairb-card-interference.md` (cxlprobe gained
`--class` for chase + `daxstridewr` NT-write mode). Victim on card A (even class) vs 8T
aggressors on card B (odd) or card A, separate CCDs, 3 reps. **Cross-card: latency
victim unchanged (225→225 ns mean, p50 219 under reads AND NT writes); bandwidth victim
−6% under reads, 0% under writes. Same-card: latency 1.93× (reads) / 2.06× (writes);
bandwidth −51% (read+read fair share) but only −5% under writes (card-level duplex ≈
+55% joint).** Symmetric arm (victim on B, writes on A): +2%. Cross-card asymmetry: readers
protected, NT writers yield ~30% (overlap-estimated). **Meaning:** "writer gets its own
card" gives Gate-2b-grade isolation inside the CXL tier; planner can treat cards as
independent budgets (read ~23.9, write ~21.9, joint ~37; co-located-write latency ×2).
First real-hardware CXL-to-CXL card-granularity interference measurement.

### 2026-09-01 (session 15) — dax2.0 is ours; Pair B card map PROVEN (plain 256 B stripe)
**Machine:** admin switched dax2.0 to devdax (17:45, no reboot) and granted group kmem
(0660, ghu4 in kmem ~20:00); node 1 = Pair A only (508 GiB). open+mmap verified across
the device (devdax enforces bounds at fault time — never touch past 512 GiB).
**Experiment** `docs/experiments/2026-09-01-pairb-address-map.md`: P1 halves identical
(46.0 GiB/s, 219 ns) → not concatenated; P2 every co-run 24+24 → one shared pair;
P3 256-B classes: each alone 23.9 (one card), even+odd 44.3, even+even 24.3 → **plain
modulo stripe `card=(off>>8)&1`**; P3b parity uniform across the whole window. My
Aug-28 "linear layout" hypothesis refuted; E1's Pair-A hash stands (root-level XOR),
Pair B's host-bridge-level interleave uses plain bits. **First single-CZ120 number:
23.9 GiB/s read @8T per card.** Tools: `cxlprobe --mode=daxstride` (new),
`hardware/scripts/pairb-address-map.sh`. **Consequence:** per-card experiments
(card-vs-card interference, per-card write streams) are possible NOW via dax offsets,
no further admin change. Label assignment (which class = 01:00.0 vs 02:00.0) still an
assumption from decoder3.0 target order.

### 2026-08-25 (session 14) — Direction pivot: write-preferred CXL + gate experiments
**Context:** advisor lukewarm on the interleaving/per-card ask (system changes are
troublesome); interested in read/write path separation on CXL. Discussed and
sharpened his idea: NOT "CXL write BW > read BW" (false: 27.9 vs 45.6) but three
real mechanisms — duplex link (separate wires per direction), the 2× DRAM write
tax (RFO+writeback on a shared bus; measured exact: 34.3 = 68.8/2), and
asynchronous stores hiding CXL latency. Quick-look W0 numbers: CXL plain-write
27.9 GiB/s = +22% over the shared-pipe prediction (partial duplex, first
evidence). **Decisions:** (1) pivot the paper thesis to direction-aware placement
(`docs/PAPER.md` Thesis v2); (2) LLM support = reserved interfaces only
(KV-evict/prefix-insert/optimizer-RMW classes, `obj_stage_out/in` staging API,
promote-on-hit hook) — implementation later, trap documented (active-decode KV on
CXL = read-latency loss); (3) two GATES before any system code: duplex matrix +
cross-interference asymmetry (full specs + pass/fail in `docs/EXPERIMENT_PLAN.md`);
(4) per-card direction parked. **Docs reorganized (user-approved scheme):**
`docs/experiments/` with dated per-experiment files + INDEX + METHODOLOGY;
`DESIGN.md` + `PAPER.md` as living docs with append-only Change-history
sections; guides/ + slides/ folders; RESULTS.md / EXPERIMENT_PLAN.md /
DESIGN_OBJPLACE.md dissolved into the new files (originals preserved in
`docs/archive/`); rules in `docs/README.md`; CLAUDE.md policy updated. User
feedback captured: present multi-step plans and get explicit agreement BEFORE
executing (memory: feedback_confirm_before_do). Gate specs + eventual results:
`docs/experiments/2026-08-25-direction-gates.md`. **Later same day (user-approved):**
data migrated to `experimental_results/<md-name>/` layout (user's convention;
user renamed old `experiments/` → `experimental_results/` themselves); repo pushed
to private GitHub `Garson-hu/CXL` (main, SSH); membench extended (NT-write kernel,
`duplex` mode, cross-node write aggressors — ~130 lines) and BOTH GATES RUN AND
PASSED (results above + in the gates file). Gate-2 v1 same-CCD confound caught and
fixed with the CCD-separated re-run (both datasets kept). Tools:
`hardware/scripts/duplex-gates.sh` + `duplex-gate2b.sh`.

### 2026-08-14 (session 13) — Post-reboot: NPS4 discovered; E4 hypothesis CONFIRMED
**What happened:** admin BIOS visit + reboot (~08-12) after the Thursday meeting.
Result is NPS1→**NPS4** (4 CPU quadrants + CXL = node 4), NOT CXL de-interleave
(decoders unchanged: 3 windows, all ways=2 gran=256). His "3 regions vs 4 devices"
email observation = firmware window carving (Pair A in 2 windows + Pair B in 1),
not a kernel flaw. **Gold:** NPS4 exposes per-card quadrant affinity — mem0→n3,
mem1→n0 (Pair A spans two quadrants), mem2+mem3→n1 (Pair B one quadrant) —
independently confirming the E4 "farther but wider" topology hypothesis. Speeds
re-verified: CXL 287 ns / 45.4 GiB/s @8T (unchanged); DRAM node 0 improved to
174.8 ns (quadrant-local). famfs FUSE restarted, still holds dax2.0.
**Files:** `hardware/results/2026-08-14-post-reboot-nps4-check.log`; memory
project_hardware updated.

### 2026-08-11..12 (session 12) — Four pre-BIOS experiments + research-update deck
**Experiments** (log: `hardware/results/2026-08-11-prelim-fourexp.log`; new tool
`benchmarks/memory/cxlprobe.c`): **E1** stripe-trick NEGATIVE — offset classes
exceed one card's ceiling (37.8 > ~24 GiB/s); AMD hashes way-selection above page
bits; software cannot split a firmware pair (THP also never engaged on CXL node:
AnonHugePages=0, MADV_COLLAPSE rc=-1). **E2** cross-pair BLOCKED — famfs FUSE
holds dax2.0 exclusively (SIGBUS on first read); needs a world-readable famfs file
or 1-hour unmount. **E3** tails benign — p99.9 < 1 µs at all loads (no
Melody-style spikes on CZ120); real signal = CXL median +15% / p90 +40–54% under
own load while DRAM flat ⇒ congestion, not spikes, is the design signal. **E4**
twins — Pair A 47.7 GiB/s @32T vs Pair B 35.5 flat (May) = +34% ceiling gap;
DRAM drift control 4–11%; hypothesis: Pair A spans two fabric quadrants
(confirmed next session). **Deliverable:** 12-slide research-update deck
`docs/SLIDES_2026-08-12-cxl-research-update.pptx` (landscape → paper pitch →
May+August evidence → asks); May slide framed as Idea 1 prototype.

### 2026-07-06..08 (session 11) — Deep literature review (97 papers) + research directions
**What we did:** Ran a 7-stage multi-agent deep literature review of CXL systems research
2022–2026 (10 discovery sweeps incl. 2026 accepted lists + adversarial multi-device hunt →
97 per-paper deep-reads against primary sources with verbatim evidence quotes → 39
skeptical re-verifications → map-audit intuition checks). Survived 5 session-limit
interruptions via journal-harvest + continuation-script relaunches (nothing re-run).
Then synthesized research directions in-context (user asked to stop agents to save tokens).
**Key verified findings:** (1) Of 97 records: 26 single-device, 10 multi-device-pooled
(always fused), only 7 multi-device-independent — none manages commodity ASIC expanders
independently on one host. (2) CXL-to-CXL cross-device interference never measured
(CXL-Interplay DAC'25 = 1 device/testbed, says so verbatim; Melody ASPLOS'25 = 4 devices
on different hosts, punts mitigation). (3) All multi-tenant CXL QoS regulates above one
fused pool (Memstrata, MTTM, Equilibria, Mercury). (4) Near-miss ring to cite: CSFQ
transport (NSDI'26), Weisgut (VLDB'25), CXL-CCL, Liaw&Chen. (5) Corrections from
verification: ArtMem = Optane not CXL; Beluga = 32 devices; SupMario ≥5 devices,
arXiv-only (ASPLOS'25 version = Melody); ATC discontinued after '25.
**Decisions:** Direction confirmed — device-granular CXL management as umbrella (Idea 1),
device-isolation multi-tenancy (Idea 2) and adaptive interleaving (Idea 3) as
emphasis/mechanism; famfs/FAST as pivot if the decoder gate fails. Week-2 interference
data picks Idea 1 vs Idea 2 emphasis. Avoid: object-tiering headline (SoarAlto/OBASE/
Clove), KV substrates, switch pools, kernel patches, pure characterization.
**Files added/changed:** `DEEP_RESEARCH_2026-07-08-cxl-landscape.html` (Part I map +
Part II directions), `benchmarks/results/2026-07-08-cxl-lit-review.json`, WORKLOG,
memory (project_direction, project_hardware, project_litreview, feedback_token_budget,
MEMORY.md).
**Next steps:** (1) Admin ticket (de-interleave dax2.0 + sysctl access) — critical path;
(2) 8-week plan Weeks 1–2: per-device baselines, interference matrix, tail sweeps;
(3) decision gate per plan.

### 2026-06-12 (session 9) — Deep-research scan for the next direction
**What we did:** Ran a multi-agent deep-research pass (103 agents, claims verified
3-vote against primary PDFs) on "what real-CXL direction could make a FAST/OSDI
paper from c28." Full report: `benchmarks/results/2026-06-12-deep-research-directions.json`.
**Ranked findings:**
1. **Device-granular CXL placement/QoS across 4 devices (top, verifiably open).**
   CXL-Interplay (DAC'25) — "first real-HW CXL interference study" — has only ONE
   device per testbed and never measures CXL-to-CXL; Micron/Intel's 8-device study
   fuses all devices into one NUMA node; Melody (ASPLOS'25) documents unstable µs
   tail latencies on real CXL and explicitly punts mitigation. Treating each device
   as a schedulable resource (cross-device interference + tail-aware placement)
   extends ObjPlace directly. Needs ≥2 system-ram CXL nodes (free a FAMFS device).
2. **FAST angle: three-tier DRAM/CXL/SSD storage/buffer-pool on real ASIC CXL +
   famfs.** Only prior real-HW validation is a workshop paper on an FPGA prototype
   whose authors leave exactly our questions open; famfs itself disclaims storage
   semantics ("not a data storage tool") and is unmerged/in transition — building
   storage semantics above it is unclaimed. Caveat: CZ120 is volatile (no
   persistence story; scope crash-consistency out or log to SSD).
3. **R/W-mix-aware dynamic DRAM:CXL bandwidth steering.** DRAM loses ~20% at 1R:1W
   while CXL *improves* (bidirectional PCIe); optimal split is workload-dependent
   and static kernel interleave can't track it. Best as a mechanism inside idea 1.
4. **AVOID: GPF/crash-consistency** — real spec gap but CZ120s are volatile; cannot
   exercise end-to-end on our hardware.
**Leverage (verified):** NUMA emulation is documented as misleading (MICRO'23: up to
26% latency / 3–66% BW error; Melody: emulation misses µs tails entirely) and
top-venue CXL papers are dominated by hyperscaler-affiliated groups → our 4 real
ASIC devices + famfs deployment is a rare position. **Closest competitor:** MTTM
(EuroSys'26) partitions the *DRAM* tier for multi-tenant bandwidth — adjacent, not
occupying device-side CXL contention. Must cite.
**Decision (2026-06-12): Idea 1 agreed**, combined with the original kickoff idea
(LLM cold-data offload + promotion/demotion) — the original idea returns as (a) the
LLM-era workload/evaluation domain and (b) a *device-aware, sensitivity-driven*
object promotion/demotion mechanism (not page-hotness migration, which is the
crowded lane). Combined thesis: *sensitivity- and device-aware placement AND
movement of memory objects across DRAM and multiple real CXL devices for LLM-era
workloads.* Staged plan + full findings written to `DEEP_RESEARCH_2026-06-12.html`
(repo root). Go/no-go = stage-2 cross-device interference characterization (needs
admin to free one FAMFS device; keep one on famfs as Idea-2 fallback).
**Process rule (2026-06-12):** max 10 concurrent subagents, strict, all
conversations (saved to memory).

### 2026-06-12 (session 10) — 4-vs-2 device decision + critical de-interleave finding
**Question:** for a strong first FAST/ObjPlace paper, take all 4 CXL devices (push the
DeepTier ASPLOS project off its 2 famfs devices) or stay on 2? Ran a bounded workflow
(10 agents, ≤4 concurrent; verified vs primary PDFs). Raw:
`benchmarks/results/2026-06-12-four-vs-two-devices-analysis.json`.
**Verdict (unanimous across 3 judge lenses + internal delta): 4 devices helps only
MODESTLY and QUANTITATIVELY — do NOT push DeepTier.** The first-of-kind headline
("first real-HW CXL-to-CXL cross-device interference + per-device QoS") is fully
established at **2 de-interleaved NUMA nodes**; the decisive never-published experiment
(victim on CXL-node-A degrading under aggressor on disjoint-core CXL-node-B) needs
exactly two. 4 devices only adds saturation *curves*, a same-vendor device-population
heterogeneity figure, and a bin-packing scheduler search space — strengthening, not
new claim classes — and risks the "gains from more hardware, not mechanism" critique.
Competitive proof count is not the currency: Micron used 8 devices (fused) and bought
zero interference novelty; Weisgut (VLDB'25) used 4 separate nodes but placement-only.
**THE REAL GATE (bigger than 2-vs-4): can c28 even expose per-device CXL NUMA nodes?**
Live sysfs (verified this session): the 512 GiB system-ram region (dax2.0) is produced
by root `decoder0.2` with **interleave_ways=2** (2 devices fused); host-bridge
`decoder3.0` reads **locked=1**; root decoders 0.0/0.1/0.2 read locked=0. So per-device
granularity needs root-level CXL **region teardown + recreate at interleave_ways=1** —
unverified on Zen5/Turin, and we lack passwordless sudo. This gate is IDENTICAL effort/
risk for the 2-node and 4-node paths, so 4 buys zero de-risking. **It blocks the entire
device-granular direction (Idea 1) at any device count until resolved.**
**Decision:** (1) FIRST verify de-interleave feasibility on the 2 devices we already
control (dax2.0) — the true go/no-go — via an admin request; (2) if it works,
de-interleave dax2.0 ONLY, keep DeepTier on dax0.0/dax1.0 famfs, ship the cross-device
interference + per-device-placement contribution at 2 nodes with a REAL co-located
tenant + established baselines (TPP/MEMTIS/Colloid/SoarAlto — the paper's actual #1
weakness, orthogonal to device count); (3) hold 4-device scaling as an optional
post-DeepTier camera-ready robustness pass. Earlier (session 9) "4 devices is the
strength" framing is now qualified: the strength is ≥2 *de-interleaved* devices, not raw count.

### 2026-05-20 (session 8) — Doc consolidation; WORKLOG is now the tracker
**What we did:** Collapsed `docs/` from 21 scattered files to **5 core docs** +
`docs/archive/`. Created `docs/RESULTS.md` (all results in one place), `docs/PAPER.md`
(org + claims + positioning), `docs/EXPERIMENT_PLAN.md` (done + next + reproduce);
folded the API reference into `docs/DESIGN_OBJPLACE.md`; kept
`docs/STUDY_GUIDE_OBJPLACE.md`. Archived the per-phase result/plan/direction notes
(SMOKE/PHASE1-3/2.1/2.2/INTEGRATION/EVAL_*/FINAL_STATUS/DIRECTION_DECISION/
NOVELTY_GAP/RELATED_WORK/MEASUREMENT_PLAN/PLAN_LLM_ERA/EVALUATION_PLAN/API) into
`docs/archive/` (raw CSVs remain under `benchmarks/results/`). Rewrote this Current
Status to be the single up-to-date status, with a Doc Map.
**Decisions:** WORKLOG is the primary progress tracker from now on; `docs/` keeps
only paper-org / claims / plan / results / design; no new scattered docs (summarize
into WORKLOG, archive temporaries).
**Files changed:** `docs/{RESULTS,PAPER,EXPERIMENT_PLAN}.md` (new),
`docs/DESIGN_OBJPLACE.md` (API folded in), `docs/archive/*` (19 files moved),
`WORKLOG.md`, `CLAUDE.md` (docs policy).
**Next:** real two-tenant workload + INTERLEAVE planner candidate (not started).

### 2026-05-20 (session 7) — Block-2 evaluation (pressure / budget / GNN / overhead)
Pressure-aware (+67%→+116% vs hotness-only), DRAM-budget +18–22% at 40–60%, GNN
skewed +8.3% / uniform −11.6% (no INTERLEAVE candidate), overhead ~0%. Fixed GNN
gather to be memory-bound (memcpy). Results in `docs/RESULTS.md` §5.

### 2026-05-20 (session 6) — ObjPlace runtime + Block-1 evaluation
Refactored `obj_alloc_hint` prototype into the **ObjPlace** object-placement runtime
(registry + benefit-per-byte planner + CXL-pressure model). All 5 eval targets met
(`docs/RESULTS.md` §4). Integrated into embbench/bwbench/gnnbench/sensbench.

### 2026-05-20 (session 5) — Direction locked + minimal prototype
Confirmation runs (median-5) held: CXL bandwidth victim 2.01×/2.13×, embedding skew
~15%. Locked direction; built minimal `obj_alloc_hint` prototype.

### 2026-05-19 (session 4) — Phase 2.1/2.2 + integration
Disjoint-core retest overturned Phase 2 (CPU-contention artifact). Bandwidth-bound
multi-thread victim 2.0–2.13× on CXL; latency-bound ≤1.23×; DRAM ~1.0%. See
`docs/RESULTS.md` §2.

### 2026-05-19 (session 3) — Deep-research pass, benchmark harness, first real CXL numbers
**What we did:**
- Wrote four research docs in `docs/`:
  - `RELATED_WORK_CXL_LLM.md` — survey of CXL tiering, CXL+LLM, embedding/GNN-on-heterogeneous-memory, and CXL QoS prior art with per-paper analysis.
  - `NOVELTY_GAP_TABLE.md` — 17-row comparison table and answers to the seven framing questions.
  - `DIRECTION_DECISION.md` — five candidate sub-directions (A LLM KV, B umbrella interference+placement, C embedding/GNN, D multi-CXL aggregation, E pivot), each with thesis, mechanism, experiments, hardware feasibility, four risk vectors, and an explicit go/no-go signal tied to Phase 1–2 measurements.
  - `PLAN_LLM_ERA_CXL.md` — 1–2 week plan with status, hypotheses, deep-research tasks, measurement plan summary, prototype plan, risks, and go/no-go matrix.
  - `MEASUREMENT_PLAN.md` — three-phase measurement plan (baseline / interference matrix / workload smoke).
- Built `benchmarks/memory/membench.c` (custom C, libnuma-based, no MLC required). Modes: latency, stream-read, stream-write, random-read, mixed, loaded-latency. CSV output. Refuses to allocate on a node with 0 MB online and prints the exact unblock command.
- Built `benchmarks/kvcache/kvbench.py` (KV-cache-shape memory benchmark; configurable layers/heads/seq/batch; placement modes dram/cxl/interleave/split).
- Built `benchmarks/embedding/embbench.py` (row-gather; uniform + Zipfian; placement modes dram/cxl/interleave/skew).
- Added five helper scripts under `scripts/`: `check-cxl-memory.sh`, `run-dram-cxl-baseline.sh`, `run-interference-matrix.sh`, `run-kv-cache-bench.sh`, `run-embedding-gather-bench.sh`.
- Discovered between sessions: **admin onlined `dax2.0` → NUMA node 1 has 522 GB CXL online.** Ran first real DRAM-vs-CXL smoke. Results in `benchmarks/results/<TS>-smoke/` and summarized in `docs/SMOKE_RESULTS_2026-05-19.md`.

**Decisions:**
- Direction remains **not locked**. Hypothesis stage. Lock only after Phase 1 + Phase 2 produce go/no-go signals on (a) CXL latency budget, (b) per-device bandwidth saturation, (c) asymmetric multi-process interference.
- LLM treated as motivation + one workload class — not the only target. Embedding and GNN gather are first-class evaluation workloads so the paper survives the small (4060 Ti 8 GB) local GPU.
- Avoid: MoE-on-CXL (closed), switch-pool (no switch), basic Memstrata port (incremental).

**Measurements (smoke, single thread, 512 MiB / thread, 3 s):**

| Metric | DRAM | CXL (dax2.0) | CXL/DRAM |
|---|---:|---:|---:|
| Pointer-chase latency | 184.9 ns | 276.5 ns | **1.50×** |
| Sequential read BW | 32.2 GiB/s | 19.5 GiB/s | 0.60× |
| Sequential write BW | 31.1 GiB/s | 18.5 GiB/s | 0.59× |
| Random read BW | 2.30 GiB/s | 1.58 GiB/s | 0.69× |
| Stream-read 4-thread BW | 69.2 GiB/s | **35.6 GiB/s** (saturated) | 0.51× |
| Stream-read 32-thread BW | 94.6 GiB/s | 35.5 GiB/s (still flat) | 0.37× |

Hypothesis 1 (CXL latency closer to DRAM than 2×) **supported**.
Hypothesis 2 (per-device BW saturates early, BW pressure dominates) **strongly supported** — saturation by 4 threads at ~99% of theoretical 36 GB/s.

**Files added/changed:**
- `docs/RELATED_WORK_CXL_LLM.md` (new)
- `docs/NOVELTY_GAP_TABLE.md` (new)
- `docs/DIRECTION_DECISION.md` (new)
- `docs/PLAN_LLM_ERA_CXL.md` (new)
- `docs/MEASUREMENT_PLAN.md` (new)
- `docs/SMOKE_RESULTS_2026-05-19.md` (new)
- `benchmarks/memory/{membench.c,Makefile,README.md}` (new)
- `benchmarks/kvcache/kvbench.py` (new)
- `benchmarks/embedding/embbench.py` (new)
- `scripts/{check-cxl-memory.sh,run-dram-cxl-baseline.sh,run-interference-matrix.sh,run-kv-cache-bench.sh,run-embedding-gather-bench.sh}` (new)
- `benchmarks/results/2026-05-19-<TS>-smoke/{smoke.csv,scaling.csv,notes.log}` (new)
- `WORKLOG.md` (this file)

**Next steps:**
- Run full Phase 1: `./scripts/run-dram-cxl-baseline.sh` (~15 min) — produces latency, BW, scaling, loaded-latency CSVs in a timestamped dir.
- Run Phase 2: `./scripts/run-interference-matrix.sh` — produces interference matrices on DRAM and CXL.
- Run Phase 3 smoke: `./scripts/run-kv-cache-bench.sh` and `./scripts/run-embedding-gather-bench.sh`.
- Decide direction using the matrix in `docs/PLAN_LLM_ERA_CXL.md` § "Go / no-go criteria".
- Open ask to admin if Phase 2 shows interesting interference: free `dax0.0` or `dax1.0` (whichever is least load-bearing) to enable multi-CZ120 NUMA experiments (Direction D).

### 2026-04-18 (session 2) — Hardware inspection on c28; MLC blocked
**What we did:**
- Discovered Claude Code's environment *is* c28 (`hostname=c28`) — no ssh/salloc needed. Corrected CLAUDE.md accordingly.
- Ran `hardware/scripts/inspect-system.sh` and appended cxl/daxctl/tools/sudo probes to the log.
- Attempted to run MLC; found two blockers: MLC not installed, and CXL not online as a NUMA node.
- Added `hardware/scripts/setup-mlc.sh` (checks common install paths, prints Intel fetch instructions).

**Decisions:**
- Hold MLC sweep until CXL is brought online as system-ram and MLC is fetched. No attempt to brute-force via custom user-space benchmark (dax chardevs are `root:600`, user has no passwordless sudo).
- GPU on c28 is too small (4060 Ti 8 GB) for anything beyond small quantized 7B — plan to use c29 (H100) or c30–31 (A6000) for model-scale experiments once direction is locked.

**Measurements (inspection only):**

| Thing | Observed |
|---|---|
| CPU | EPYC 9745 Turin, 256 logical / 128 physical, single NUMA node |
| DRAM | 773 GB, one node |
| GPU | 1× RTX 4060 Ti 8 GB (driver 580.65.06, CUDA 13.0) |
| CXL devices (lspci) | 4× Micron 6400 @ 01:00.0, 02:00.0, c1:00.0, e1:00.0 |
| CXL bus endpoints (`cxl list`) | 2 committed — mem1 (port3/endpoint5), mem3 (port3/endpoint6) |
| CXL sysfs | mem0–mem3 all present, each `ram_size=0x4000000000` (256 GB) |
| CXL exposed as | devdax only — `dax0.0` 242 GiB, `dax1.0` 269 GiB, `dax2.0` 512 GiB, all target_node 1 |
| NUMA nodes | only node 0 — CXL not online |
| Kernel | 6.14.11+ with `memhp_default_state=offline` |
| Tools installed | `cxl`, `daxctl`, `ndctl`, gcc 12.4.0 |
| MLC | missing |
| sudo | needs password |

**Files added/changed:**
- `hardware/results/2026-04-18-inspect.log` — raw inspection output (never edit)
- `hardware/scripts/setup-mlc.sh` — MLC presence check / install hints
- `CLAUDE.md` — corrected access section (dev env = c28), added CXL-bring-online + MLC-fetch sections
- Memory: `project_hardware.md` rewritten with measured state (GPU, CXL offline, sudo, MLC)

**Next steps:**
- Open a ticket with ARC admins (or request sudo for the session) to run:
  ```
  sudo daxctl reconfigure-device --mode=system-ram --no-online dax0.0 dax1.0 dax2.0
  sudo daxctl online-memory dax0.0 dax1.0 dax2.0
  ```
  Confirm `numactl --hardware` shows new node(s) for CXL.
- Fetch Intel MLC (EULA form → tar → `~/mlc/Linux`, add to PATH).
- Re-run `hardware/scripts/mlc-sweep.sh <DRAM_NODE> <CXL_NODE(s)>`.
- Separately, decide whether we want all 4 CZ120 devices exposed (need to commit mem0 + mem2 as endpoints first) or whether the current 3-region devdax layout is acceptable for first experiments.

### 2026-04-18 (session 1) — Project scaffolding + doc/memory scheme
**What we did:**
- Created initial directory scaffold (notes/, hardware/, experiments/, workloads/, papers/, writing/, scripts/) with planning docs covering field landscape, options A–E, Week 1 plan, reading list, decisions log, open questions.
- User trimmed the scaffold to a lean layout: removed `notes/`, `papers/`, `writing/`; added `system/` for the future built system.
- Updated `README.md` to match the lean layout.
- Adopted the three-layer doc/memory scheme (per-project memory, WORKLOG.md, CLAUDE.md) and created `WORKLOG.md`, `CLAUDE.md`, and `.claude/skills/update-mem/SKILL.md`.
- User initialized the repo as git (`.git`, `.gitignore`).

**Decisions:**
- Direction lock deferred until Week 1 hardware data.
- Planning context lives in conversation + per-project memory, not in the repo.
- System paper target, not characterization paper.
- Doc/memory layers: CLAUDE.md for codebase rules, WORKLOG.md for session narrative, per-project memory for indexed facts across sessions.

**Measurements:** None — hardware not yet accessed.

**Files added/changed:**
- `README.md`
- `hardware/scripts/{inspect-system.sh,mlc-sweep.sh,llm-baselines.sh}`
- `WORKLOG.md` (this file)
- `CLAUDE.md`
- `.claude/skills/update-mem/SKILL.md`
- `.gitignore` (user-added)
- Memory: `user_role.md`, `project_hardware.md`, `project_direction.md`, `project_layout.md`, `reference_arc_cluster.md`, `MEMORY.md`

**Next steps:**
- Run Week 1 hardware verification on c28: `ssh arc.csc.ncsu.edu`, `salloc -p turin128 -w c28`, then `hardware/scripts/inspect-system.sh` → `mlc-sweep.sh` → `llm-baselines.sh`. Dump output into `hardware/results/` as dated files.
- Confirm GPU presence on c28.
- Compare measured CXL latency against Micron's "remote socket DRAM" claim and Memstrata's 2× assumption.
