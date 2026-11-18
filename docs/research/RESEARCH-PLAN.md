# Research Plan — CXL-enabled LLM Serving with Efficient KV Cache Reuse

*ACTIVE direction since 2026-11-10 (the user's decision). It replaces the charter of 2026-10-17 (`CHARTER.md`, same
directory) as the active direction; the charter stays unchanged as the record of the previous line, and every result
obtained under it remains valid. Living document: the body states the present plan, every change is one dated line in
the Change history at the end, and no history line is rewritten. Sections 1–7 carry the user's "Research State" of
2026-11-10 in its wording; the paragraphs marked **On record** attach what this repository has already measured —
source file, date, conditions — and what it leaves open. Nothing in an "On record" paragraph is a new decision.*

*Evidence labels: **HW** hardware microbenchmark on c28 · **REAL** real vLLM + LMCache serving on c28's RTX 4060 Ti ·
**EMU** host-memory traffic emulation (CPU copies, not GPU DMA) · **SIM** trace-driven simulation or offline cache
analysis, including the calibrated scheduler model · **SRC** source inspection. Experiment files are in
`docs/experiments/`, raw data in `experimental_results/<same name>/`.*

*Label note: from 2026-11-10 "RQ1 / RQ2 / RQ3" mean the questions of section 5. The questions of the 2026-10-17
charter are written "charter RQ1 / RQ2 / RQ3". Files dated before 2026-11-10 — including the serving-study report, whose
§13 says "RQ1" for reuse-aware admission — use the charter's meaning.*

## 1. Direction (user, 2026-11-10)

**CXL-enabled LLM Serving with Efficient KV Cache Reuse.**

Research goal: how can LLM serving systems use CXL-expanded memory to improve cross-request KV reuse and end-to-end
serving performance?

Focus: multi-turn and agentic LLM serving.

Decision: the project pivots away from the original direction, "Reuse- and Interference-Aware Unified DRAM/CXL Memory
Management" (charter of 2026-10-17).

## 2. Why CXL (user, 2026-11-10)

Two main hardware opportunities.

**Memory expansion.** Retain more reusable KV prefixes; reduce repeated GPU prefill computation; support large working
sets.

**Concurrent read/write bandwidth.** CPU-side CXL read-only 45.6 GiB/s; CPU-side CXL NT write-only 43.9 GiB/s;
concurrent read/write 59.4 GiB/s aggregate. Potential opportunity to overlap KV retrieval and persistence. End-to-end
serving benefit remains unverified.

Duplex bandwidth is one supporting motivation and possible optimization, not the entire paper.

**On record — memory expansion.**
- c28 holds 1.06 TiB of CXL (the two-card pair `dax0.0` + `dax1.0`, 242 + 269 GiB, and `dax2.0`, 512 GiB) beside 755 GiB
  of DRAM; the GPU KV cache of the serving configuration is 4.5 GB (121,792 tokens of Qwen2.5-3B-AWQ at 36 KiB per token).
- SIM (`2026-11-04-cxl-serving-scheduling-gap.md` §7.1, `replay/trace-reuse.csv`; LRU over 512-token blocks, 36 KiB per
  token): reusable share of the prompt tokens of the Mooncake hour — conversation 0.050 at 4.5 GB, 0.126 at 80 GB, 0.226
  at 160 GB, 0.309 at 320 GB, 0.370 at 640 GB; tool-agent 0.380, 0.435, 0.503, 0.558, 0.593. A 70B fp16 model needs 8.9×
  the bytes per token. SIM (`2026-10-09-kv-capacity-characterization.md`): one hour of chat creates about 11 TiB of
  distinct KV for an 8B model.
- REAL (same report §7.3; pinned DRAM standing in for CXL): a 320 GB host tier at a sustainable load lowers TTFT p50 by
  19 % (conversation) and 36 % (tool-agent), request time by 11 % / 21 %; the measured cached share stays within 2 points
  of the offline LRU.
- HW / REAL on the CXL data path itself: the GPU reads a CUDA-registered devdax mapping at 12.48 GiB/s against 12.49
  from pinned DRAM (`2026-10-07-read-cost.md`); an LMCache L1 on devdax gave the same hits and TTFT as a DRAM L1
  (`2026-10-11-capacity-matched-kv.md`, `2026-10-18-rq1-misscost-feasibility.md`). Not re-measured in the serving study:
  the DAX devices are root-only since 2026-10-18 (section 8).

**On record — concurrent read/write bandwidth.** The three numbers and their conditions:

| number | what it is | conditions | source |
|---|---|---|---|
| 45.6 GiB/s | streaming-read ceiling of the `dax0.0` + `dax1.0` pair | 8–16 threads, pair online as NUMA node 4 (NPS4), 2026-08-25; the same value with 4 threads on one CCD on 2026-10-09; 49–51 GiB/s through devdax with 4–16 threads spread over four CCDs on 2026-10-07 | `2026-08-25-direction-gates.md`, `2026-10-09-cxl-topology-interference.md`, `2026-10-07-read-cost.md` (HW) |
| 43.9 GiB/s | NT-write capacity of the same pair | 4 or more writer threads (one unthrottled core already reaches 41); 43.9 alone with pseudo-random data on 2026-09-22 | `2026-09-08-write-tier-campaign.md`, `2026-09-22-zero-line-writes.md` (HW) |
| 59.4 GiB/s | best joint read + NT-write rate of the pair | one process, 12 read : 4 write threads: 26.0 read + 33.4 write; +30 % over the best single direction (45.8); DRAM in the same sweep stays at its read-only level (69.4–69.8) and falls to 53.3 as writes take over | `2026-08-25-direction-gates.md`, Gate 1 (HW) |

- At the 59.4 GiB/s point each direction runs below its solo rate — reads 26.0 of 45.8 (−43 %), writes 33.4 of 43.8
  (−24 %): the gain is in the aggregate (the experiment's verdict: "partial duplex", shared media behind the links).
  Which side gives way depends on the mix: 4 readers beside 8 NT writers keep 27.0 of 45.7 GiB/s (−41 %) and a dependent
  read takes 614 instead of 284 ns (2026-08-25, Gate 2b); 4 streaming readers beside an 8-thread DRAM → CXL copy of
  random data keep 48.3 of 51.4 GiB/s (−6 %) while the copy falls from 43.9 to 29.9 GiB/s and a dependent read takes 538
  instead of 229 ns (2026-10-07).
- The joint gain appears at every scale measured: +53 % on one card (37.1 vs 24.2 GiB/s), +36 % on the two cards of
  `dax2.0` (61.9 vs 45.6), +42 % on four cards (128.3 vs 90.2) (`2026-09-08-cxl-card-scaling.md`, HW).
- The serving path measured so far does not come near these rates. REAL: c28's GPU link carries 12.5 GiB/s (PCIe 4.0 ×8);
  a host hit moves 0.15–0.6 GB (4k–16k tokens); over a replay window retrieval averages at most 15 MB/s and stores
  38–80 MB/s (serving report §9.3, §13); real KV stores from the 4060 Ti come at 0.065–0.14 GB/s in 58 MB bursts
  (`2026-10-10-lmcache-kv-traffic.md`). REAL, mixed traffic: 47 GB/s checkpoint bursts into the cards that hold the KV
  cache leave KV loads and TTFT on this GPU unchanged (paired TTFT +0.02 s, link-bound;
  `2026-10-12-checkpoint-kv-mixed.md`).
- Server-scale KV traffic exists in the record only as EMU: at "8B 8×" the KV stores take about 36 of the pair's 46 GB/s
  of write capacity, at "70B 4×" the offered 53 GB/s exceeds it and the tier falls behind without bound
  (`2026-10-10-lmcache-kv-traffic.md`, `2026-10-12-checkpoint-kv-mixed.md`). SIM: with the reuse-aware admission of
  charter RQ1 the same loads write 88–91 % less, peaks at most 25 GB/s (`2026-10-21-joint-benefit-analysis.md`).
- So the user's statement stands as written — the end-to-end serving benefit of the concurrent bandwidth is unverified —
  and the record says where it could be tested: the regime needs GB/s-scale KV traffic in both directions (a GPU link
  faster than c28's, or several engines on one tier), which c28's only GPU does not produce (section 8).

## 3. Previous research (user, 2026-11-10)

Original topic: Reuse- and Interference-Aware Unified DRAM/CXL Memory Management (`CHARTER.md`; active 2026-10-17 →
2026-11-10). Main findings, each with its source on record:

- **Future KV reuse has substantial oracle value.** SIM, `2026-10-17-kv-reuse-oracle-study.md`: at 200 GiB an oracle
  serves 80 / 94 / 70 % of reuses (conversation / tool agent / synthetic) against 17 / 65 / 34 % for the best
  capacity-matched baseline (charter Gate 1 PASS).
- **Second-touch and adaptive admission reduce unnecessary writes by approximately 88–91 %.** SIM: second-touch alone
  −69 … −77 % of writes (`2026-10-20-rq1b-admission-study.md`); the adaptive admission (gap rule + regime switch) 88–91 %
  (`2026-10-21-joint-benefit-analysis.md`); consolidated in `rq1-consolidation-2026-10-21.md` (charter Gate 2 PARTIAL).
- **Historical reuse is more effective for admission than eviction ranking.** SIM, `2026-10-20-rq1b-admission-study.md`
  (the learned filter's benefit is second-touch admission); the exploratory study of 2026-10-27 on branch
  `explore/reuse-window-prefetch` found the same (window retention = LRU within ±0.04, window admission +0.05 … +0.19).
- **Joint value-and-cost management did not consistently outperform strong independent management.** SIM,
  `2026-10-21-joint-benefit-analysis.md`: joint = independent to −0.5 … +0.7 points on 24 real-trace configurations
  (charter hypothesis H2 not supported; Gate 3 not met).
- **DRAM/CXL hardware interference is significant, but tested KV workloads did not establish a strong need for joint
  control.** HW: the write-drain cliff (`2026-09-08-dram-write-drain.md`), the topology condition
  (`2026-10-09-cxl-topology-interference.md`); EMU on hardware, `2026-10-21-hw-validation-filtered-writes.md`: admit-all
  KV writes break the 7 % neighbour SLO (p99 +8.3 … +25 %), the admission-filtered stream stays inside (+1.6 … +4.0 %).

All negative results remain valid.

**On record — what exists from that line.** The admission policy of charter RQ1 exists as a trace simulator; it is not
wired into LMCache's store path and was never run in the serving loop (serving report §13). The write path and store
`cxlpath` is built (2026-09-19, branch `cxlpath`). The CXL characterisation of 2026-08-25 … 2026-10-09 (duplex, card
scaling, topology, read cost) is closed and cited above.

## 4. Latest serving study (user, 2026-11-10)

Branch `explore/cxl-serving-scheduling-gap`. Report `docs/experiments/2026-11-04-cxl-serving-scheduling-gap.md`;
self-contained summary `experimental_results/2026-11-04-cxl-serving-scheduling-gap/SUMMARY.md`. All REAL unless marked.

Findings:
- Larger host KV cache capacity improves serving performance. (§7.2–§7.3, §8)
- At 320 GB host cache, TTFT p50 improved 19 % for conversation and 36 % for tool-agent workloads under sustainable
  load. (§7.3: trace seconds 0–200 at 0.04×, 599 and 1,159 requests, against the 2 GB tier.)
- External KV hits can suffer long admission delays under GPU KV memory pressure. (§7.2c, §7.3)
- Tool-agent host hits: 3.3 s TTFT p50, compared with 0.3 s for GPU-prefix hits. (§7.3, 320 GB, 148 host-dominant hits;
  a third of them wait 13 s p50 between the lookup result and the load.)
- Actual KV transfer took approximately 0.05 s. (§7.3; 0.09 s in the overloaded replays, 19–85 ms for a whole hit alone, §3.)
- vLLM may require large upfront GPU KV reservations for external loads, while cache misses can proceed through chunked
  prefill. (SRC, vLLM 0.31.0 `vllm/v1/core/sched/scheduler.py`, the waiting loop of `schedule()`: slots for all external
  tokens are allocated at once, a failed allocation ends the scan, nothing falls back to computing the prefix.)
- Increasing transfer threads or enabling eager prefetch did not resolve the observed bottleneck. (§4, §5: every
  aggregate within 0.3 % on both traces.)

Limitations:
- Large-capacity serving experiments used pinned DRAM as a stand-in for CXL because DAX access was blocked.
- Main GPU was RTX 4060 Ti 8 GB.
- Larger GPU and real CXL serving validation remain necessary.

**On record — further limits of that study** (report §11): one model (3B-AWQ, 36 KiB per token); replay windows of
100 / 200 trace-seconds time-scaled to 0.08× / 0.04×, one replay per configuration (repeatability 0.02 % on TTFT p50,
window-to-window variance not measured); no code was changed, so the cause of the admission delay is established by
source inspection and per-request time lines, not yet by an intervention; the scheduling reference of its §6 is SIM
(7–27 % optimistic).

## 5. Candidate research questions (user, 2026-11-10; provisional — to be refined using experiments)

**RQ1 — CXL capacity and KV reuse.** How can CXL-expanded capacity improve cross-request KV reuse?
- *On record.* The reuse a capacity captures is a property of the trace and predictable from an offline LRU within
  2 points (REAL vs SIM, §7.1 / §7.3); short-distance reuse (tool-agent) is mostly captured by 5 GB, long-distance reuse
  (conversation) needs hundreds of GB for a 3B model. LMCache stores every prompt's KV — 75–99 GB per 100 trace-seconds,
  188–237 GB per 200 — and a 40 GB tier evicted its own working set inside a 7-minute run (§8). At 320 GB 84 % / 57 % of
  the prompt tokens are still computed: first occurrences (§12).
- *Open.* Real CXL not exercised in serving. Hour-scale reuse is SIM; the measured windows are 200 s. What the tier
  holds (admission and retention in the store path) is untested in the serving loop. The 3B model understates a 70B
  deployment's capacity need by 8.9×. The SSD-backed tier found fewer short-distance hits than 5 GB of DRAM, cause not
  isolated (§7.2b).

**RQ2 — GPU KV admission.** How can the serving runtime efficiently activate external KV under limited GPU memory?
- *On record.* Host-dominant hits are the slowest class whenever the GPU KV cache is saturated at their arrival:
  overloaded, 16.8 s p50 against 2.7 s for GPU-prefix hits and 11.5 s for misses at equal backlog (§7.2c); inside the
  bursts of a sustainable load, 3.3 s against 0.3 s (§7.3). With free blocks at arrival the same class is the fastest
  (conversation, 0.8 s against 5.2 s for misses). Mechanism: section 4 (SRC). The generic scheduling costs — queue scan
  bounded by the token budget, step-boundary notice of a finished load, one-step-late submission, FCFS — amount to
  20–40 % of mean TTFT at high load (SIM, §6), of which existing flags recover part (REAL: synchronous scheduling −14 %,
  hits-first −43 % for the hits, §4).
- *Open.* No intervention has been run. The condition (GPU-KV saturation) is shown on a 4.5 GB KV cache with a 3B model
  and 6–14k-token prompts; it is unverified on an 80-GB-class GPU. The source inspected is vLLM 0.31.0; the current
  upstream scheduler has not been checked. Closest published work: Bidaw (FAST '26) orders requests by KV-loading
  latency and size for a host + SSD store; it does not address this admission rule (§14).
- *Prediction on record* (report, executive summary, 2026-11-05): with a bounded block reservation for pending external
  loads, or chunked loading, host-dominant hits fall from 3.3 s / 16.8 s p50 toward the GPU-prefix-hit category's
  0.3 s / 2.7 s with no loss for misses.

**RQ3 — Concurrent data movement.** How can the serving runtime coordinate KV retrieval and persistence under
concurrency while exploiting CXL's read/write capabilities?
- *On record.* Hardware side: section 2 (joint rate +30 % over one direction; each direction below its solo rate;
  dependent reads 2.2–2.4× slower beside writes). Serving side (REAL): simultaneous loads serialise on LMCache's single
  transfer thread per engine — 16 hits of 8k tokens 428 ms p50, 7.7–11.9 GB/s over the burst (§5); stores are the larger
  flow, 4–170× the retrieval volume (§9.3); lookups queue behind the stores of the running prefill on the one CPU lookup
  worker (9–37 ms at concurrency 2–16, 295 ms at 2 req/s, §4).
- *Open.* No serving measurement so far in which CXL-side bandwidth or read/write concurrency limited anything
  (section 2). With reuse-aware admission in the store path the persistence stream shrinks by 88–91 % (SIM), so whether
  retrieval and persistence still contend after admission is itself unmeasured. The GB/s regime is out of reach of c28's
  GPU link (section 8).

## 6. Immediate priorities (user, 2026-11-10)

| # | priority (user) | serves | on record: what exists | on record: prerequisite or limit |
|---|---|---|---|---|
| 1 | Validate the GPU KV admission bottleneck with a minimal scheduling or reservation prototype. | RQ2 | mechanism located in the source (section 4); harness `benchmarks/serving/`; baseline runs below | first code change to vLLM in this project (the serving study changed none): behind a flag, default off, so the existing runs stay reproducible; check the current upstream scheduler first |
| 2 | Verify the effect on overall TTFT, tail latency, throughput and cache-miss performance. | RQ2 | baseline table below; repeatability of the replay method 0.02 % on TTFT p50 | throughput is visible only at saturation (0.08× replays; Experiment F long prompts): in the 0.04× replays every request completes at the offered rate. No 320 GB baseline exists at 0.08× (that sweep ended at 80 GB) |
| 3 | Repeat important results with real CXL memory. | RQ1, all | devdax L1 path used before (2026-10-11, 2026-10-18) | `/dev/dax0.0–2.0` are `crw------- root root` since 2026-10-18, checked again 2026-11-10: needs the administrator |
| 4 | Study concurrent KV reads and writes using actual serving data paths. | RQ3 | per-run store / retrieve events with timestamps (`*-kvevents.jsonl`) and 5 ms PCIe counters (`*-gpu.txt`) of all 66 serving runs, on c28's local NVMe (`/mnt/local/ghu4/results/2026-11-04-cxl-serving-scheduling-gap/`, not in git) | on c28 the real path is bounded by the 12.5 GiB/s GPU link and one 8 GiB GPU |
| 5 | Validate important mechanisms on a larger GPU and model. | RQ2, RQ1 | backup nodes c33 (A100 80 GB, `-p a100`) and c29 (H100 NVL 94 GB, `-p h100`) | no CXL on those nodes (DRAM tier only); their host DRAM size and a serving environment there are not yet checked |

Baselines for priorities 1–2 (REAL, 2026-11-05; `replay/replay-summary.csv`, `replay/tables-dl-hitcat.md`,
`replay/tables-d-hitcat.md` of the serving study; TTFT in seconds, p50 unless marked):

| metric | tool-agent 0.04×, 320 GB (`dl-tool-dram320`) | conversation 0.04×, 320 GB (`dl-conv-dram320`) | tool-agent 0.08×, 80 GB (`d-tool-dram80`) |
|---|---|---|---|
| all requests, TTFT p50 / p95 / p99 | 1.56 / 20.7 / 33.8 | 3.46 / 26.6 / 33.9 | 12.7 / 40.9 / 48.1 |
| host-dominant hits [n] | 3.3 [148] | 0.8 [65] | 21.0 [95]; 16.8 [69] at backlog < 20 |
| GPU-prefix hits | 0.3 | 0.2 | 6.8; 2.7 at backlog < 20 |
| misses | 5.1 | 5.2 | 13.8; 11.5 at backlog < 20 |
| request time p50 | 6.3 | 15.9 | 23.5 |
| computed prompt tokens/s | 1,117 | 1,155 | 2,322 |
| GPU busy share / largest backlog | 0.49 / 27 | 0.49 / 16 | 0.87 / 41 |

## 7. Research principles (user, 2026-11-10)

- Focus on concrete system problems.
- Use real measurements before proposing complex mechanisms.
- Keep previous negative findings.
- Do not force every CXL characteristic into the system design.
- Distinguish measured results from hypotheses and simulations.
- Aim for a coherent systems paper with meaningful end-to-end benefits.
- Claude handles code, data, experiments and figures; ChatGPT helps with research direction, experimental reasoning
  and analysis.

The repository's standing rules continue to apply (`docs/README.md`, `docs/experiments/METHODOLOGY.md`): every number
with units, node, date and its raw file; one experiment file per experiment; raw data append-only.

## 8. Open points (not decided; listed so that nothing is assumed)

- **Success criteria.** No gates are set for RQ1–RQ3. The charter's Gates 1–4 belong to its hypotheses H1 / H2.
- **Branch of the new main line.** This plan and the serving study sit on `explore/cxl-serving-scheduling-gap`, created
  under the instruction never to merge it into `evaluation`; `evaluation` (8e2d9e3) is its direct ancestor. Which branch
  carries the work from here is undecided.
- **Paper and design documents.** `docs/PAPER.md` (Thesis v3, the write path; last changed 2026-09-23) and
  `docs/DESIGN.md` (last changed 2026-10-17) describe the previous lines and are not updated.
- **Hardware.** (a) DAX permissions on c28 (administrator). (b) The only CXL node has an 8 GiB GPU on a 12.5 GiB/s link
  and the large GPUs have no CXL, so priorities 3 and 5 cannot be met on one machine today. (c) The regime of RQ3 needs
  server-scale traffic: emulation, labelled EMU as before, or other hardware.
- **Admission in the store path.** Whether the charter-RQ1 admission policy enters the serving loop under RQ1 is
  undecided.
- **Venue and timeline** under the new direction: not stated.

## Change history
- 2026-11-10 — plan created from the user's "Research State" of 2026-11-10 (direction change away from the 2026-10-17
  charter). "On record" paragraphs, the baseline table and the open points added from the repository's experiment files.
