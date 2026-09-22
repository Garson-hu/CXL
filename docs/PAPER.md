# Paper: Organization, Claims, Positioning

*The paper-writing reference: thesis, structure, main claims (each with its
evidence in `experiments/`), and how we position against prior work. Literature
scan: `Related.md` (repo root). Status: **Thesis v3** (horizontal write path,
PolyStore-inspired) agreed 2026-09-18; the runtime (`cxlpath`) is BUILT
(2026-09-19); the motivation and the positioning of the gain were restructured
on 2026-09-21 after the user's review of the outline. **No evaluation experiment
has been run.** Thesis v2 (2026-08-25, both gates passed) is the measured
foundation. History: Change history at bottom.*

## Thesis v3 (2026-09-18, revised 2026-09-21) — the horizontal write path: CXL by default, DRAM on loan

*Builds on Thesis v2 below (its mechanisms and D-claims stay valid and become
the characterization). v3 changes the FRAMING and the SYSTEM, following the paper
shape of PolyStore (FAST'25; notes in `Related.md`): one strong phenomenon → a
practical but "systems-heavy" design → large effect. The system is built
(`DESIGN.md` §10); nothing below is an evaluation result. O2's headline victim is the CPU optimizer step (phase-1 result); LULESH is dropped as the
victim and stays a checkpoint client.*

**The phenomenon, in one sentence.** Today every bulk write lands in DRAM first
(checkpoint staging buffers, CPU-side KV-cache pools, tiering systems that
demote only after data turns cold), although most of that data is never read
again, and the act of writing it into DRAM slows down every other program that
is reading DRAM at the same time.

**The thesis.** DRAM should not be the default first stop of the write path.
Use DRAM and CXL side by side ("horizontally", PolyStore's word): write-only and
low-reuse data goes to CXL BY DEFAULT; DRAM is BORROWED for writes only while CXL
is the bottleneck and the loan does not slow other DRAM readers beyond a bound;
otherwise DRAM is spent on the minority of data that is read again. We manage
the whole path of a bulk write, from the moment the application produces it until
it rests on NVMe (checkpoint: application memory → staging → NVMe; KV cache:
GPU → CPU-side pool → colder storage). *(Until 2026-09-21 this paragraph said
such streams "never touch DRAM", which contradicted the controller.)*

**Role of PolyStore (user ruling 2026-09-18): a source of ideas, NOT a
comparison method or baseline.** We study it and carry its ideas into memory.
What we borrow: using devices side by side instead of stacked; splitting one
object into segments placed on different devices; re-measuring every short
epoch and reassigning writers; migrating only when the target device has
headroom; cache rules chosen per device; and its paper shape. What has to
change when the devices are memories, because of what we measured: (a) on DRAM,
reads and writes share one pipe and writes hurt reads disproportionately;
(b) CXL memory is reached over PCIe lanes and its own controller, not over the
DDR channels, so a write stream placed there stops competing with DRAM readers;
(c) moving hot data up into DRAM is itself a write stream into DRAM, which is
exactly the traffic that slows DRAM readers. So the borrowed epoch mechanism
gets a different objective — make the write stream as fast as possible while
other DRAM readers slow down by no more than a bound — and the per-device cache
rule comes out as: writes bypass DRAM BY DEFAULT and borrow it only under that
bound; only repeated reads earn a place in DRAM. The
paper cites PolyStore as related work and as the origin of these ideas; the
intro, the novelty argument and the baselines are NOT built around it.

**Where the gain comes from (repositioned 2026-09-21).** The earlier text said
"from separating reads and writes, not from adding bandwidth: 44 GiB/s of CXL on
top of 273 GiB/s of DRAM is only +15%". That compared against the WRONG DRAM
number. Once DRAM readers must be protected, the DRAM write bandwidth that may
actually be used is small: in the probe calibration a 77 GiB/s write stream
already cost a bandwidth-bound reader 12–14% and 113 GiB/s cost it 23%
(`experimental_results/2026-09-19-cxlpath-build/V5-probe-calibration.txt`), and in
the live controller test 31–38 GiB/s of our own DRAM writes lifted the latency
probe ~5% (`.../B-live/`). Interpolating these few points, a 7–10% protection
bound leaves only some 40–60 GiB/s of usable DRAM write bandwidth — THE SAME
ORDER as the CXL pair's 43.9 GiB/s.
**MEASURED with the system, 2026-09-22 (`experiments/2026-09-22-three-policies.md`, the core
figure):** beside a moderate victim (a reader using ~100 of the socket's ~273 GiB/s) a 64 GiB
checkpoint copy through cxlpath finishes in 0.97–0.99 s at 4–6% harm — 1.5× faster than all-CXL,
3.3× faster than a DRAM writer throttled to the same harm, 5× less harm than today's all-DRAM
staging at 1.4× its time; its 65 GiB/s is 0.9 of "CXL capacity + DRAM budget". Beside a SATURATED
victim (CPU Adam over 24 GB) every copy is source-bound at ~18 GiB/s, so the destination changes
only the harm: 15.6% (DRAM) vs 6.6% (CXL); cxlpath correctly lends nothing; throttling to 7% harm
costs 1.8× the time. Wording for the paper: "approaches the sum" for a moderate victim; "same
completion, 2.4× less harm" for a saturated one. **Extended to four victims the same day
(llama.cpp decoding, GAPBS PageRank): the headroom guard on the absolute probe level (1.3× the
unloaded level) is what tells the two regimes apart — with it cxlpath lends only to the moderate
victim and equals all-CXL beside the three saturated ones (2.4–3.5× less harm than DRAM staging
at the same completion; today's staging costs llama.cpp 34% and PageRank 44%). Limitation to
state: beside read-saturated victims even all-CXL exceeds a 7% bound (the copy's source reads),
and cxlpath does not pace the producer; the paper reports it and lists producer pacing as future
work.** The paragraph below is the phase-1 budget.
**MEASURED 2026-09-22 (`experiments/2026-09-21-dram-write-budget.md`):** under a 7% bound the
usable DRAM write bandwidth is 40 GiB/s (pure writes) / 28 GiB/s (copies) beside a synthetic
reader and 17.5 / ~9–30 beside a saturated CPU Adam step — the same order as, or below, the
CXL pair's 43.9 GiB/s. So the sum is ≈ 2× either simple policy for the reader, and for the
saturated victim ≈ 1.4× all-CXL and ≈ 3.5× a rate-limited DRAM writer. State the multiple
against BOTH simple policies; the loan is whatever the victim leaves over, and the controller
measures it. Copies to CXL still cost 3–5% at 25–40 GiB/s (the source read stays in DRAM).
The paragraph below is the pre-measurement hypothesis, kept for the record.
**Hypothesis to measure first: under an equal reader-protection bound, "CXL by
default + DRAM on loan" delivers roughly the SUM — about twice either simple
policy** (all-CXL is capped at the CXL capacity; a rate-limited all-DRAM writer
is capped at the DRAM budget under the bound). A multiple, a figure, and the core
of the paper.
Caveats that must be stated: (1) the DRAM budget depends on the victim — the
interpolation above mixes two set-ups and is an ESTIMATE, not a result; (2) the
argument needs a producer that can exceed ~44 GiB/s, which is about BURST rate,
not average rate (one unthrottled core already pushes 41 GiB/s; average KV write
rates are 3–8 GiB/s); (3) with more cards the CXL share grows (4 cards: 85 GiB/s,
`experiments/2026-09-08-cxl-card-scaling.md`) and the loan shrinks — the policy
follows the capacity it measures, it does not assume one.
Still true from the old positioning: by default 60–80% of written data never
enters DRAM at all, and staging no longer occupies DRAM capacity for the tens of
seconds a 0.9 GiB/s NVMe needs per checkpoint.

### Motivation (§3 of the paper) — one table, three observations, three strawmen
Facts that hold WITHOUT our system; they answer "what is wrong with today's
practice". Each observation carries exactly what its data can prove (revised
2026-09-21: O1 used to conclude "DRAM should be spent on reads only", which
contradicted a controller that lends DRAM to writers).
- **Table 1.** Today's bulk writers — checkpoint libraries, KV-cache layers,
  kernel memory tiering — with the first stop of their data (DRAM in all three),
  the share that is read again, and the extra traffic they cause (staging copy,
  demotion / migration). "Kernel tiering is DRAM-first" lives here as a row.
- **O1 — moving this data off DRAM is nearly free.** 60–80% of KV-cache blocks
  are never read after being written (three production traces,
  `experiments/2026-09-09-kv-trace-analysis.md`); checkpoints are read only after
  a failure. So placing it elsewhere costs almost no read-back penalty.
  Implication (user's wording): *write-only or low-reuse data should not consume
  DRAM by default.* Flip side, which motivates goal G2: a minority IS read again
  (20–40% of KV blocks, seconds to minutes later) — DRAM is worth spending on
  exactly that data. Figure exists.
- **O2 — keeping it in DRAM is harmful.** A program that writes heavily into DRAM
  slows down other programs that read DRAM. Headline figure MUST be a real
  application that already uses most of the DRAM bandwidth (candidate: all-core
  LULESH) taking a realistically sized checkpoint, showing how much its own
  compute step slows down. The synthetic result (4 CCDs of NT writers,
  ~273 GiB/s → DRAM reader 12× slower, `experiments/2026-09-14-stencil-3c.md`
  and the write-tier campaign) goes beside it as the worst case. The figure
  design is our answer to "real write streams never saturate DRAM" (reviewer
  question 5): we do not claim saturation; a moderate write burst hurts an
  application that is already bandwidth-bound. **Candidate measured 2026-09-22
  (`experiments/2026-09-22-three-policies.md`, `headline-adam-timeline.png`): a CPU-offloaded
  training step (Adam over 24 GB, 80 threads) runs 15–17% slower for the 3.5 s a 64 GiB
  checkpoint is copied into DRAM staging; into CXL staging the same copy costs 6.5% (the
  source read) — one timeline carries O2 and O3.**
- **O3 — CXL is a safe destination.** THE empirical statement of the section; it
  is not pre-empted in Background: *redirecting the write stream from DRAM to CXL
  largely removes its interference with the DRAM reader* (D4: reader back to
  idle speed; stencil proxy: DRAM-resident application slows 0–5% while the write
  stream saturates CXL, `experiments/2026-09-14-stencil-3c.md`). Precise wording:
  the WRITE half leaves DRAM; the read of the source data remains in BOTH
  placements (it lifted the latency probe ~20% in the live controller test), so
  the comparison is fair but a co-runner's slowdown is not zero.
- **Three simple policies, one figure** (axes: DRAM-reader slowdown; writer
  completion time). (1) All-DRAM: fails on reader slowdown (O2). (2) All-CXL:
  protects readers, but caps the producer at the CXL write capacity — 43.9 GiB/s
  here, which ONE core already reaches (41 GiB/s), and 3.9 instead of 12.3 GiB/s
  for a GPU source on this platform. (3) Rate-limited all-DRAM: protects readers
  too, but caps the producer at the DRAM budget under the bound (tens of GiB/s,
  see "Where the gain comes from"), lengthens the checkpoint, and keeps tens of GB
  in DRAM for tens of seconds. ⇒ *We therefore need to use CXL by default while
  opportunistically borrowing DRAM only when doing so does not hurt readers.*
  This sentence ends §3, IS design principle P2, and opens §4.
  Expected attacks: "add more CXL cards" → the policy follows measured capacity;
  more cards mean a smaller loan, not a different system. "Nothing writes
  44 GiB/s" → burst rate, not average; one core copies at 41 GiB/s, so every
  multi-threaded checkpoint copy exceeds the pair momentarily.
- **Moved out of the motivation's closing argument (user review):** "raw devdax
  has no allocator" cannot justify a dynamic policy, and it is not a pitfall of
  today's practice at all — it is a challenge of REALIZING our idea. It goes to
  the Introduction's challenge list (paired one to one with the segment-store
  contribution) and is stated in §4.1 as principle P1; it is never argued inside
  the design section.
- **First experiments (none run yet):** the O2 headline figure; the three-strawmen
  figure; the usable DRAM write bandwidth under a protection bound for the chosen
  victim (the number the gain hypothesis stands on).

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
1. Microbenchmark, the core figure: writer completion time and DRAM-reader
   slowdown for the three strawmen of §3 (all-DRAM, all-CXL, rate-limited
   all-DRAM) AND for our system, all under the same reader-protection bound;
   plus the static split sweep (all DRAM, 70/30, 50/50, all CXL). The strawman
   half is shown in §3; the evaluation adds our system on the same axes and tests
   the "roughly the sum" hypothesis.
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

**Main risk (updated 2026-09-21; the system is built).** The gain hypothesis —
about twice either simple policy under an equal protection bound — rests on an
interpolated DRAM budget and is unmeasured; if the budget under the bound turns
out much larger than the CXL capacity, the multiple shrinks toward the old +15%
and the paper falls back on "readers protected, 60–80% of data never enters DRAM,
DRAM capacity freed", which is real but not a multiple. The real-application gap
(O2 headline) is equally unknown. Both are the first things to measure.

### Facts from building the system (2026-09-19) that the paper has to deal with
The runtime (`cxlpath`) is built (`DESIGN.md` §10, as built). Nothing below is an
evaluation result; these are constraints and openings found on the way.
- **One core saturates our CXL write direction.** A single unthrottled NT-store
  thread pushes 41 GiB/s = 94% of the dax0.0/dax1.0 pair's 43.9 GiB/s. So "CXL
  write capacity is the scarce resource" holds for ANY multi-threaded writer on
  this platform, and spill to DRAM is the normal case for a fast writer, not a
  corner case. It also caps what the evaluation can show: a writer can never get
  more than ~44 GiB/s from CXL here (DRAM takes ~277).
- **The durable tier is slow.** The NVMe sustains 0.9 GiB/s regardless of
  parallelism; a 32 GB checkpoint needs ~36 s to become durable. This strengthens
  the case for a large staging tier that is not DRAM (tens of GB held for tens of
  seconds), and means every end-to-end checkpoint number is NVMe-bound.
- **The GPU path has a platform cap:** GPU → CXL direct 3.9 GiB/s vs 12.3 GiB/s
  into pinned DRAM (reads from CXL: 12.5). The runtime turns this into a policy
  choice (direct when DRAM is under pressure, staged when calm); measured through
  PyTorch: 4.3 → 10.5 GiB/s as the staged share rises. Cause unknown; must be
  stated as a property of this platform.
- **A cheap no-root signal exists.** 1000 dependent DRAM loads every 10 ms
  (1.26% of one core) track a bandwidth-bound reader's slowdown monotonically
  (1.18× at −13% … 6.5× at −92%) and let the controller react 16 ms after an
  injected DRAM aggressor. Candidate for a figure in the design section.
- **The writers' own source reads count.** Copying 50 GiB/s out of DRAM into CXL
  lifts DRAM latency ~20% although nothing is written to DRAM. "Writes to CXL are
  free for DRAM readers" (O3) must be worded as "the write half is free; the read
  of the source remains" — true for both placements, so the comparison is fair,
  but the absolute slowdown of a co-runner is not zero.
- **Costs measured on the way:** the library adds 82 ns per 32 MiB write and no
  system call on the data path; CPU readers see CXL at 1.77× DRAM streaming time
  (k = 3); a GPU reader sees no difference (never promote).

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

## Paper structure (planned — v3, modelled on PolyStore FAST'25; revised 2026-09-21)
**How PolyStore separates WHY from HOW (re-read on 2026-09-21 at the user's request).**
- *Introduction:* context → the prevailing philosophy (hierarchy) → THREE
  LIMITATIONS of it ("First … Second … Finally …") → the insight in one sentence
  ("we argue that a horizontally structured architecture …") → the system in a few
  lines → the CHALLENGES OF REALIZING the insight → contributions that answer the
  challenges one to one → headline numbers.
- *§3 "Analyzing hierarchy pitfalls":* pure analysis of today's practice — one
  table, one figure. It never mentions the new system.
- *§4.1 "Design goals":* goals, each driven by numbered principles written as
  REQUIREMENTS ("… must support … with minimal synchronization overhead"). This
  is where "what we want to build, and for which problem" lives — BEFORE any
  mechanism. Requirements that come from the idea itself rather than from the
  pitfalls (its Goal 3: durability, crash consistency, sharing) are phrased
  "should not compromise …" and were announced as challenges in the introduction.
- *§4.2 "Overview":* every principle → one named component; one architecture
  figure; the prototype in a few lines.
- *§4.3–4.8, one subsection per component:* a lead-in of two to five sentences
  that restates the local need and points back ("Existing solutions … lack … To
  address these limitations, we propose Poly-cache"), then ONLY mechanism:
  structures, algorithms, parameters. A parameter may carry a one-clause reason
  ("2 MB to balance memory and concurrency and to match the maximum block I/O
  size"). No evidence, no re-derivation from the motivation, no weighing of
  alternatives.
- *§5:* opens with evaluation questions, one per component.

**Rule for our paper (user, 2026-09-21): the design section says HOW, never WHY.**
Everything that says what we want to build, and for which existing problem, comes
before the mechanisms: Introduction (limitations → insight → challenges →
contributions), §3 (findings), §4.1 (goals and principles), §4.2 (overview).
Rationale that came from BUILDING the system — median instead of minimum for the
probe reference, capacity thresholds instead of per-writer speed, the non-starving
drain, "a key names one object" — does not go into §4 as narrative: it becomes a
sensitivity / ablation result in the evaluation or a paragraph of the discussion.
(`DESIGN.md` §10.11 keeps the full engineering record.)

1. **Introduction** — (a) context: bulk writers (checkpoint staging, KV-cache
   pools, memory tiering) and CXL memory next to DRAM; (b) the prevailing
   practice: DRAM-first; (c) its three limitations — *First,* DRAM bandwidth and
   capacity are spent on data that is never read again; *Second,* bulk writes into
   DRAM slow every co-running DRAM reader, and later migration adds more DRAM
   writes; *Finally,* the obvious remedies trade one problem for another:
   throttling lengthens the write, and sending everything to CXL caps the
   producer at CXL's small write capacity; (d) the insight: CXL by default, DRAM
   lent to writers only under a reader-protection bound, and its benefits;
   (e) the system in a few lines; (f) the challenges of realizing it and (g) the
   contributions, one to one:
   C1 a raw devdax device has neither allocator nor file system and is shared by
   many unprivileged processes → a segment store with a shared index and no
   system call on the data path;
   C2 placement must know how full CXL is and how much headroom DRAM has, without
   privileged counters, and react within tens of milliseconds → latency probe +
   ledger + slow-increase / fast-decrease controller;
   C3 the re-read minority deserves DRAM, but promotion is itself a DRAM write
   stream → read in place, break-even promotion under the bound;
   C4 staged data must still reach NVMe in the client's format and survive
   crashes, without the drain becoming a new source of DRAM traffic → DRAM-free
   drain, runtime-side reclaim, node-owned metadata;
   (h) headline results (after the evaluation).
2. **Background** — HARDWARE FACTS ONLY (user review 2026-09-21): DRAM reads and
   writes share the memory-system resources and heavy writes delay reads (write
   drain mode); CXL memory is reached over PCIe lanes and its own controller,
   not over the DDR channels, with its own bandwidth; how bulk writers work
   today (checkpoint staging, KV CPU pools, tiering demotion). DRAM capacity
   pressure: one paragraph + citations. NOT here: the empirical result of O3,
   and NOT "CXL read and write directions are independent" — a Thesis-v2
   leftover that overstates (same-card writes cost readers −41%) and that v3
   does not need.
3. **DRAM-first pitfalls (motivation)** — pure analysis of today's practice and
   of the obvious remedies; our system is not mentioned. Table 1; O1 moving this
   data is nearly free (takeaway: low-reuse data should not consume DRAM by
   default; a minority is read again); O2 keeping it in DRAM is harmful; O3 CXL
   is a safe destination; one figure with the three simple policies on two axes.
   The section closes with its ONLY forward-looking sentence, the hinge into §4:
   *"We therefore need to use CXL by default while opportunistically borrowing
   DRAM only when doing so does not hurt readers."*
4. **Design and implementation** —
   4.1 *Design goals* — WHAT we want and for WHICH problem: goals G1–G3 with
   principles P1–P4 as requirement statements, each naming the finding or the
   challenge it answers (draft text: `DESIGN.md` §10.1).
   4.2 *Overview* — principle → component; architecture figure; the life of a
   write, a read and a drain; the prototype (library + one background process,
   no root).
   4.3 segment store on raw CXL · 4.4 interference-bounded placement ·
   4.5 read path · 4.6 DRAM-free drain and recovery · 4.7 clients (file
   checkpoint, GPU checkpoint, KV layer) — HOW ONLY: short lead-in, then
   structures, algorithms, parameters. Detail: `DESIGN.md` §10.3–10.6.
5. **Implementation** — userspace library + background process, no root; shims
   for VeloC, PyTorch async checkpoint, a KV layer. (May be merged into §4 as
   PolyStore does.)
6. **Evaluation** — opens with questions: (Q-A) what does the segment store
   cost, and how much space is wasted without compaction? (Q-B) does placement
   keep DRAM readers within the bound, and what does the writer pay, versus
   all-DRAM, all-CXL and a rate-limited writer — the three strawmen of §3 plus
   our system on the same two axes? (Q-C) does break-even promotion beat
   always/never promote? (Q-D) does the drain stay off DRAM, and how fast is
   recovery from CXL vs NVMe? (Q-E) do real applications benefit? Then:
   microbenchmarks, parameter sensitivity and ablations (bound, step, epoch,
   segment size; reference estimator; fullness signal), per-component, real
   applications, PM configuration as supplement.
7. **Discussion** — why not NVMe directly; single platform; one CXL card pair;
   GPU→CXL write cap; per-client quotas.
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
- **One-line delta, Thesis v3 (2026-09-21):** first system that makes CXL the
  DEFAULT first stop of bulk writes and lends DRAM to writers only under a
  reader-protection bound, managing the whole path to NVMe, on real CXL hardware.
  (The line below is the Thesis-v2 formulation; "direction" is no longer the
  headline signal.)
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
- **2026-09-19** — System built (`DESIGN.md` §10 as built). Added "Facts from
  building the system": one core saturates the CXL pair's write direction, the
  NVMe sustains 0.9 GiB/s, the GPU→CXL direct-write cap, the no-root latency
  probe as a usable signal, and the caveat that the writers' source reads still
  load DRAM. Evaluation still to be planned with the user.
- **2026-09-21** — Outline reviewed by the user; three changes, each argued rather
  than accepted wholesale. (1) O1 no longer concludes "DRAM is for reads only"
  (it contradicted the controller that lends DRAM to writers); the observations
  now split the work — O1 moving is nearly free, O2 keeping is harmful, O3 CXL is
  a safe destination — and O1's implication is the user's "low-reuse data should
  not consume DRAM by default". (2) §3 ends with three strawmen (all-DRAM,
  all-CXL, rate-limited all-DRAM) on two axes and the sentence that is P2; "raw
  devdax has no allocator" moves to the opening of §4 as a challenge, "kernel
  tiering is DRAM-first" stays as a row of Table 1. (3) Background carries
  hardware facts only; "CXL directions are independent" is dropped as an
  overstated v2 leftover. Out of (2) came a REPOSITIONING of the gain: under a
  reader-protection bound the usable DRAM write bandwidth is only tens of GiB/s,
  the same order as the CXL pair, so "CXL by default + DRAM on loan" should
  deliver about twice either simple policy — a hypothesis on interpolated
  numbers, to be measured first. The thesis paragraph no longer says these
  streams "never touch DRAM".
- **2026-09-21 (second round)** — The user pointed out that the design section
  must say HOW only, and that "what we want to build, for which existing problem"
  belongs before it. PolyStore re-read for its technique (introduction:
  limitations → insight → challenges → contributions one to one; §3 pure
  analysis; §4.1 goals and principles as requirements; §4.2 overview; component
  subsections = short lead-in + mechanism). Outline changed accordingly: the
  "challenges" block I had put at the opening of §4 moves to the introduction
  and is paired with the contributions; the derivations ("comes from O2, O3 and
  the strawmen") leave the component subsections and live in §4.1; rationale
  learned while building goes to evaluation ablations or the discussion. §3 keeps
  exactly one forward-looking sentence, the hinge the user proposed.
- **2026-09-22** — Phase 1 measured: the DRAM write budget under a 7% reader-protection bound is
  18–40 GiB/s (pure) / ~9–29 (copies), same order as or below the CXL pair's capacity; positioning
  confirmed with a victim-dependent multiple (≈2× vs either simple policy for a synthetic reader;
  ≈1.4× vs all-CXL and ≈3.5× vs throttled DRAM for a saturated CPU Adam step). Headline victim
  = CPU optimizer step; LULESH dropped as victim. Benchmark survey saved to
  `benchmarks/results/2026-09-21-benchmark-survey.md`.
- **2026-09-22 (later)** — Phase 2 core figure measured (three simple policies + cxlpath beside a
  moderate and a saturated victim) and the O2 headline timeline. Gain wording fixed: "approaches
  the sum" (moderate victim: 1.5× all-CXL, 3.3× throttling at equal harm) and "same completion,
  2.4× less harm" (saturated victim, source-bound copy, no loan).
- **2026-09-22 (evening)** — Four-victim core figure; the guard (absolute probe level) decides the
  regime; producer pacing recorded as a limitation. Two more victims' budgets in
  `experiments/2026-09-22-budget-more-victims.md`.
