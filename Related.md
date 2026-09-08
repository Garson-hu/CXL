# Related Work for Sensitivity-Aware CXL Placement

*Compiled 2026-05-20. Sources: paper PDFs, USENIX/ACM/IEEE pages, arXiv, project repos. Items I could not confirm against a primary source are explicitly marked **(needs verification)**. This is a literature scan, not a substitute for reading the 6–8 closest papers in full — those are flagged.*

---

## 1. Executive Summary

**Has our exact idea already been done?** No single system does *application-hint-driven, online, object-level, sensitivity-aware placement across DRAM and real CXL that jointly reasons about bandwidth sensitivity + access skew + phase + CXL pressure under multi-tenant contention.* But the idea is **substantially less novel than it looks** — every individual axis is occupied, and two recent papers occupy large fractions of the combination. Treat the headline as "novel in combination and in execution," not "untouched space."

**Which papers are closest (collision risk, highest first):**
1. **SoarAlto — "Tiered Memory Management Beyond Hotness" (OSDI'25)** — object-level, profile-guided, uses an MLP-aware "Amortized Offcore Latency" metric to capture bandwidth-vs-latency sensitivity. This is the academic statement of roughly half our thesis. **Read in full before locking the pitch.**
2. **Memstrata (OSDI'24)** — our stated inspiration; multi-tenant CXL sensitivity isolation on real CXL, but VM/page granularity, transparent (no app hints).
3. **Liu/Wang "Exploring Real-world CXL" (arXiv 2405.14209, 2024) & PASA IPDPS'25** — object-level, bandwidth-sensitivity-aware DRAM/CXL interleaving on real CXL; even touch LLM inference (FlexGen). Characterization+allocator, not a serving system.
4. **Colloid (SOSP'24)** — "hotness is not the key, loaded latency is"; page-level, transparent, but owns the "contention/bandwidth matters more than hotness" argument.
5. **Liaw & Chen, CXL tensor allocation for LLM fine-tuning (arXiv 2507.03305, 2025)** — sensitivity-tiered, tensor (object) level, real CXL, latency-first allocator. Training, not serving; single-tenant.

**Strongest novelty gap:** The *combination* of (a) **multi-tenant CXL bandwidth-contention as a first-class placement driver**, (b) at **object granularity inside an application**, (c) driven by **lightweight online application hints** (not offline profiling), (d) on **real commodity CXL (CZ120 devdax)**. No paper unifies object-granular placement (SoarAlto/X-Mem) with multi-tenant CXL-pressure arbitration (Memstrata/vTMM). Phase-awareness and multi-tenant interference are the two axes that are essentially *unoccupied* in the embedding/feature/vector literature and weakly occupied elsewhere.

**Biggest collision risk:** **SoarAlto (OSDI'25).** It already published "object-level placement beyond hotness, using a metric that captures bandwidth/MLP sensitivity." If we cannot crisply differentiate (we are: *online hint-driven vs offline profile-guided; multi-tenant vs single-tenant; real CXL vs NUMA-emulated; serving phase-aware vs static*), the "object-level sensitivity-aware" framing is weak. **Do not claim object-level sensitivity-aware tiering as a net-new concept.** Secondary risk: the "skew-aware embedding placement" result (our ~11–17%) sits in a *very* crowded space (RecShard, Bandana, CARINA, Cosmos) — skew alone is table stakes, not a contribution.

---

## 2. Our Current Idea

Commodity CXL memory (e.g., Micron CZ120) has **acceptable latency** (~2–3× DRAM, in the hundreds of ns) but a **low per-device bandwidth ceiling** — we measured saturation around **35.5 GiB/s** on a single CZ120, consistent with published characterizations (Liu et al. report >50% slowdown once a workload needs >24 GB/s; Micron CZ122 work treats CXL as bandwidth expansion). Because the bandwidth ceiling is low, **bandwidth-bound objects suffer severe contention on CXL** — we measured a stream-read victim slowing **2.0–2.13×** under a stream-read aggressor on CXL, while the same setup on DRAM shows almost no slowdown. By contrast, **latency-bound or cold objects can tolerate CXL** residency with little harm.

We therefore propose a runtime that places **individual objects** across DRAM and CXL based on **object sensitivity** (bandwidth-bound vs latency-tolerant/cold), **access skew**, **workload phase**, and **CXL pressure**, using **application-level hints** rather than purely transparent page hotness tracking. The prototype (`system/placement/`) exposes `obj_alloc_hint` and a minimal object-placement API. Current evidence: skew-aware embedding-table placement gives ~11–17% (≈15% in stable settings); a KV layer-split did **not** help (we will not claim KV benefit unless request/recency skew is redesigned).

---

## 3. Closest Prior Work

### 3.1 SoarAlto — "Tiered Memory Management Beyond Hotness" (OSDI'25) — *the paper to beat*
Liu, Hadian, Xu, Li (Virginia Tech). [paper](https://www.usenix.org/conference/osdi25/presentation/liu) · [PDF](https://www.usenix.org/system/files/osdi25-liu.pdf) · [code](https://github.com/MoatLab/SoarAlto).
**What they do:** Argue *hotness ≠ performance* — hot pages aren't always performance-critical. Introduce **AOL (Amortized Offcore Latency)**, a metric combining access latency with **memory-level parallelism (MLP)** to capture true performance impact; **SOAR**, a profile-guided **static object allocator** ranking objects by performance contribution; and **ALTO**, lightweight page-migration regulation. Evaluated on **NUMA emulation** (DDR4 SKX / DDR5 SPR two-socket), **not real CXL**, under fast-tier contention.
**Why close:** Object-level + explicitly "beyond hotness" + MLP-aware sensitivity metric. This is essentially half of our thesis (object granularity + bandwidth/latency sensitivity) already in print at a top venue.
**Why it doesn't fully cover us:** (1) **Profile-guided / static** (SOAR needs an offline AOL profiling pass) — we propose **live application hints**, no profiling run. (2) **NUMA-emulated, not real CXL** — we have real CZ120. (3) **Limited phase adaptivity** and **no multi-tenant CXL-pressure** dimension. (4) Requires offcore performance counters; a hint API avoids that.
**To differentiate:** Frame our delta explicitly as *dynamic vs static, hint-driven vs profile-driven, multi-tenant vs single-tenant, real-CXL vs emulated.* Must cite, must compare, ideally must beat or clearly orthogonalize.

### 3.2 Memstrata + Intel Flat Memory Mode (OSDI'24) — *our stated inspiration*
Zhong, Berger, Waldspurger, Cidon, et al. (Columbia / Microsoft). [paper](https://www.usenix.org/conference/osdi24/presentation/zhong-yuhong) · [PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/03/2024-FlatMemoryMode-Memstrata-OSDI2024.pdf).
**What they do:** First study of hardware-managed CXL tiering (Intel Flat Memory Mode, 128 GB local + 128 GB CXL). ~82% of 188 Azure workloads degrade <5%, but "outlier" VMs degrade up to ~34% from inter-VM contention. **Memstrata** = lightweight multi-tenant allocator: **page coloring + LLC partitioning** to remove inter-VM contention, plus an **online slowdown estimator** (random-forest on L2/L3 miss latency + MPKI, ~86% accuracy) that gives sensitive VMs more local DRAM (~10% of pages re-allocated every 10s). Worst-case slowdown 35%→<6%.
**Why close:** Real CXL, multi-tenant, sensitivity-aware — exactly our high-level framing. The "give sensitive workloads more local DRAM" intuition is shared.
**Why it doesn't fully cover us:** VM/page granularity, transparent online estimation (no application hints), generic VMs (not LLM/embedding objects). Treats a VM as a black box; we open it up to **intra-application object placement**. Whether its estimator uses bandwidth as an explicit feature **(needs verification)**.
**To differentiate:** Intra-application object granularity + explicit app hints about which objects are bandwidth-bound, vs Memstrata's VM-granular black-box estimation.

### 3.3 "Exploring and Evaluating Real-world CXL" (arXiv 2405.14209, 2024) + PASA IPDPS'25
Liu, Wang, et al. (UC Merced / W&M / MemVerge). [paper](https://arxiv.org/html/2405.14209v1); companion [PASA IPDPS'25 PDF](http://pasalabs.org/papers/2025/IPDPS25_cxl_eval.pdf) **(mechanism details need verification — PDF didn't text-extract)**.
**What they do:** Characterize three real CXL cards across AMD/Intel hosts; propose a **data-object-level interleaving policy** — match interleaving to per-object access pattern, striping bandwidth-sensitive objects and concentrating latency-sensitive ones. Objects selected if ≥10% of footprint + intensive access. Workloads include NPB, graph, **and LLMs (BERT/GPT2 via ZeRO-Offload, LLaMA/OPT via FlexGen)**.
**Why close:** This is the single closest prior art to our *object-level, bandwidth-sensitivity-aware DRAM/CXL placement* claim, and it touches LLM inference.
**Why it doesn't fully cover us:** Characterization + general allocator, **not an LLM-serving system** and not multi-tenant. No KV/serving-object semantics, no phase, no request-recency skew, no contention-isolation, hints derived from size/access not from a serving engine.
**To differentiate:** Serving-native object types, phase + skew + CXL-pressure signals, multi-tenant isolation.

### 3.4 Colloid — "Tiered Memory Management: Access Latency is the Key!" (SOSP'24)
Vuppalapati, Agarwal (Cornell). [PDF](https://www.cs.cornell.edu/~ragarwal/pubs/colloid.pdf) · [code](https://github.com/host-architecture/colloid).
**What they do:** Show that everyone packs hot pages into the lowest-*unloaded*-latency tier, but under load **loaded latency can inflate ~2.5×**, so SOTA can be 2.3× off optimal. **Colloid** balances hot data by *measured loaded (queueing) latency* across tiers; bolts onto HeMem, TPP, and MEMTIS. **NUMA-emulated** (no real CXL/HBM).
**Why close:** Strongest conceptual cousin of our bandwidth-pressure thesis — loaded latency rises precisely under bandwidth contention. Owns the "hotness is not the key, contention is" argument.
**Why it doesn't fully cover us:** Page-level, transparent, no object semantics, no application hints, emulated. Reactive page balancing rather than proactive sensitivity classification.
**To differentiate:** Object-level + explicit bandwidth-bound classification + app hints, vs reactive page-level loaded-latency balancing. This is the key "why not just balance latency at page granularity?" comparison.

### 3.5 Liaw & Chen — CXL-Attached Memory Allocation for Long-Context LLM Fine-Tuning (arXiv 2507.03305, 2025)
[paper](https://arxiv.org/abs/2507.03305). **Real CXL** (SMART Modular CMM CXL-2.0 on Xeon 6780E + H100).
**What they do:** PyTorch extension for **tensor-level** NUMA placement + a **CXL-aware latency-first greedy allocator** with a **4-level latency-sensitivity classification**: latency-critical tensors (optimizer state) pinned to DRAM, latency-tolerant tensors interleaved across CXL for bandwidth. Placing optimizer state on CXL → ~4× slowdown (motivates sensitivity).
**Why close:** Most conceptually similar single system — sensitivity-aware, object(tensor)-level, real CXL, latency-vs-bandwidth tiering. Validates our hypothesis on the training side.
**Why it doesn't fully cover us:** **Fine-tuning, not serving**; no KV cache, no prefill/decode phase, no request skew, single-tenant; sensitivity classes are hand-coded, not driven by runtime hints or CXL-pressure feedback.
**To differentiate:** Serving-time, multi-tenant, phase+skew, runtime-hint-driven.

### 3.6 Beluga — CXL-Based KVCache Management for LLMs (SIGMOD'26, arXiv 2511.20172)
Yang, Hu, Li, Li, et al. (Alibaba) **(author list needs verification)**. [paper](https://arxiv.org/abs/2511.20172).
**What they do:** First system letting **GPUs directly access a CXL switch pool** (XConn switch, 8 TB, ~1 TB/s, ~750 ns). Unified symmetric address space + native load/store; **software interleaving at 2 MB granularity** across CXL devices; cache-oblivious scheduling. 89.6% TTFT cut, 7.35× throughput vs RDMA.
**Why close:** Same hardware substrate (GPU↔CXL pool) and target workload; strongest empirical CXL-KV result.
**Why it doesn't fully cover us:** **Deliberately anti-tiering** — explicitly "application-agnostic, hint-free," flat hierarchy, no sensitivity-aware migration, no multi-tenant isolation. It is the design antithesis of our approach.
**To differentiate:** "Beluga proves the substrate; we show what skew + multi-tenancy + sensitivity hints buy you on top of it."

### 3.7 X-Mem — "Data Tiering in Heterogeneous Memory Systems" (EuroSys'16) — *the ancestor*
Dulloor et al. [PDF](https://courses.grainger.illinois.edu/ece598ms/fa2019/papers/paper121.pdf).
**What they do:** `xmalloc(tag)` API — programmer/data-classifier tags allocations; tier chosen **per data structure** from profiled access characteristics **including bandwidth**. Heterogeneous-memory emulation; MemC3/VoltDB/GraphMat.
**Why close:** The canonical **object-level, application-tagged, bandwidth-aware** tiering baseline — the intellectual origin of our idea.
**Why it doesn't fully cover us:** Pre-CXL (2016), manual tags, no automated/lightweight hint inference, single-tenant, no phase, no CXL-pressure.
**To differentiate:** We modernize X-Mem for CXL, add online lightweight hints + CXL-pressure + multi-tenant signals.

---

## 4. CXL Memory Tiering and Isolation

| System | Venue | One-line |
|---|---|---|
| **Memstrata** | OSDI'24 | §3.2 — multi-tenant CXL isolation, VM/page, page coloring + slowdown estimator. |
| **Pond** | ASPLOS'23 | CXL memory pooling for cloud; ML predicts latency-insensitive VMs + untouched memory; ~7% DRAM savings. VM granularity, capacity/cost-driven, **emulated CXL latency**. Not bandwidth/contention. [arXiv](https://arxiv.org/abs/2203.00241) |
| **TPP** | ASPLOS'23 | §5 — transparent page placement on **real CXL** (Meta fleet); hotness-driven demotion/promotion; merged into Linux. Page-level, no hints, no bandwidth signal. [arXiv](https://arxiv.org/abs/2206.02878) |
| **CXL-Interference** | arXiv 2411.18308 (venue NV) | First characterization of CXL interference on **real CXL** (MMEM↔CXL and SSD↔CXL traffic). Corroborates our 2.0–2.13× finding. Regulation, not placement. **(venue needs verification)** [PDF](https://arxiv.org/pdf/2411.18308) |
| **Dissecting CXL Memory at Scale / Alto** | arXiv 2409.14317 | 4 real CXL devices; **>24 GB/s demand → >50% slowdown from device queueing**; cross-socket CXL 2.9× slowdown. "Best-shot" interleave + Alto adaptive tiering. Strongest evidence for our bandwidth-ceiling claim; competing optimization at interleave-ratio/page level. [arXiv](https://arxiv.org/abs/2409.14317) |
| **Space-Control** | arXiv 2603.06951 (2026) | Process-level **security** isolation for disaggregated CXL (gem5/SST sim). Multi-tenant but access-control, not perf-QoS. Cite for "isolation in CXL ≠ performance isolation." |
| **MT2** | FAST'22 | Memory-bandwidth regulation on hybrid NVM/DRAM; detects noisy neighbors and throttles. Ancestor of CXL multi-tenant bandwidth interference; Optane, throttling not placement. [PDF](https://ipads.se.sjtu.edu.cn/_media/publications/yijfast22.pdf) |
| **Demystifying CXL Memory** | MICRO'23 | First real-CXL characterization (latency 130–200 ns); citation anchor for "latency acceptable, bandwidth is the constraint." [arXiv](https://arxiv.org/abs/2303.15375) |
| **Micron CZ122 BW optimization** | arXiv 2412.12491 (2024) | **8× Micron CZ122** (sibling of our CZ120); static page interleaving DDR5+CXL, +24–39% BW. Treats CXL as bandwidth expansion. The naive uniform-interleave baseline we must beat. [arXiv](https://arxiv.org/abs/2412.12491) |

**Takeaway:** The dominant granularity here is **page** (TPP, Memstrata enforcement, Alto) or **VM** (Pond, Memstrata scope). Multi-tenant CXL bandwidth contention is *characterized* (CXL-Interference, Dissecting-CXL) and *throttled* (MT2, Memstrata page-coloring) but never turned into an **object-level placement decision**. That conversion is our wedge.

---

## 5. Heterogeneous Memory and Page Migration

| System | Venue | Granularity / Guided? | Bandwidth | Skew | Phase | Multi-tenant | Note |
|---|---|---|---|---|---|---|---|
| **SoarAlto** | OSDI'25 | object + page / profile-guided | **Yes (MLP/AOL)** | Yes | weak | no | §3.1 — the paper to beat. [code](https://github.com/MoatLab/SoarAlto) |
| **HeMem** | SOSP'21 | page + per-app policy | **Yes (NVM BW asymmetry)** | Yes | some | partial (KV isolation) | Foundational bandwidth-aware tiering on **real Optane**; PEBS sampling. [ACM](https://dl.acm.org/doi/10.1145/3477132.3483550) |
| **MEMTIS** | SOSP'23 | page (dynamic huge/base) | no | **Yes (full access distribution, intra-huge-page skew)** | some | no | Best skew treatment at page level; Optane + NUMA-emulated CXL. [PDF](https://multics69.github.io/pages/pubs/memtis-lee-sosp23.pdf) |
| **Colloid** | SOSP'24 | page / transparent | Yes (loaded latency) | inherited | yes | implicit | §3.4. |
| **Nomad** | OSDI'24 | page / transparent | no | hotness | **yes (anti-thrash under pressure)** | no | Non-exclusive tiering + transactional migration; 6× over TPP under pressure. [arXiv](https://arxiv.org/abs/2401.13154) |
| **M5** | ASPLOS'25 | page + **64B sub-page** | no | **yes (sparse hot pages)** | partial | no | **Real CXL** device-driven profiling. Sub-page skew complements object placement. [PDF](https://jiyuan.is/papers/asplos25-m5.pdf) |
| **TMTS** | ASPLOS'23 | page/process / transparent | no | yes | **yes (adaptive, fleet)** | **yes (SLO, fleet)** | Google warehouse-scale tiering, 2-yr deployment; production multi-tenant SLO framing. [PDF](https://www.micahlerner.com/assets/pdf/adaptable.pdf) |
| **vTMM** | EuroSys'23 | page/VM | no | yes | some | **yes (cross-VM fast-mem pool)** | PML-based tracking; VM fast-memory arbitration ≈ our CXL-pressure arbitration, but VM-granular. [ACM](https://dl.acm.org/doi/10.1145/3552326.3587449) |
| **MemBrain** | TACO'22 | allocation-site/object / auto-guided | partial | yes | some | no | Associates profiles with malloc call sites; close to our hint idea. [arXiv](https://arxiv.org/abs/2110.02150) |
| **bkmalloc / Flexible Object Tiering** | TACO'25 | object / allocator-guided | NV | NV | NV | no | Allocator notifies daemon to tier large objects. Hint- vs profile-driven **(needs verification)**. [ACM](https://dl.acm.org/doi/10.1145/3708540) |
| **CachedArrays** | IPDPS'24 | **object (variable size)** / **semantic future-use hints** | partial | yes | **yes (future-use)** | no | Strong on the "application hints" axis (Julia, ML training, NVRAM). [PDF](https://arch.cs.ucdavis.edu/assets/papers/ipdps24-cachedarrays.pdf) |
| **Thermostat** | ASPLOS'17 | page (4K/2M) / transparent | no | yes | limited | no | Foundational transparent two-tier hotness. [ACM](https://dl.acm.org/doi/10.1145/3037697.3037706) |
| **Nimble** | ASPLOS'19 | page / transparent | n/a | n/a | n/a | no | Migration-mechanism speedup (~15×); composes under any policy. [PDF](https://www.cs.yale.edu/homes/abhishek/ziyan-asplos19.pdf) |
| **AutoNUMA / Linux tiered memory** | kernel | page / transparent | no | recency | reactive | no | The default baseline to beat; TPP merged here. |
| **HMSDK** | SK hynix SDK (not a paper) | page / weighted BW interleave + DAMON | yes | yes | some | no | Real-system bandwidth-aware interleaving artifact; cite as engineering precedent, not academic work. [repo](https://github.com/skhynix/hmsdk) |

**Takeaway:** Object-level placement (X-Mem, MemBrain, CachedArrays, bkmalloc, SoarAlto) and application hints (X-Mem, CachedArrays) both exist. "Hotness ≠ performance" is owned by Colloid + SoarAlto. **None combine object-granular hint-driven placement with multi-tenant CXL-pressure arbitration.** Standard baseline comparison set used by SoarAlto: **TPP, MEMTIS, Colloid, Nomad** (+ AutoNUMA). We should run against this set.

---

## 6. CXL and LLM Memory Systems

| System | Venue/Year | Hardware | Granularity | Guided? | BW-sens | Skew | Phase | Multi-tenant | Note |
|---|---|---|---|---|---|---|---|---|---|
| **Liaw & Chen tensor alloc** | arXiv'25 (2507.03305) | **real CXL** | tensor | yes (4-level) | yes | impl | no (training) | no | §3.5 — closest sensitivity-aware CXL object placement, but fine-tuning. |
| **Beluga** | SIGMOD'26 (2511.20172) | **real CXL** switch pool | KV block (2MB interleave) | **no (hint-free)** | yes (interleave) | tested (Zipf) | eliminated | no | §3.6 — flat pool, anti-tiering. |
| **TraCT** | arXiv'25 (2512.18194) | **emulated CXL (MLC)** | KV block | partial (hint-based) | transfer | **yes (prefix/recency)** | **yes** | multiplexed | Most direct serving competitor on phase+recency+hints. **Read in full; emulated not real.** [arXiv](https://arxiv.org/abs/2512.18194) |
| **CXL-SpecKV** | FPGA'26 (2512.11920) | **real CXL + FPGA** | 4KB page, layer-aware | yes (LSTM prefetch) | yes (compress) | hot/cold | **yes** | no | 3-tier GPU/FPGA/CXL; needs custom FPGA NDP. [arXiv](https://arxiv.org/abs/2512.11920) |
| **CXL-PNM (1M-token)** | arXiv'25 (2511.00321) | **simulated** PNM | token pages | yes | yes | **yes (sparse attn)** | decode | no | Steady-token selection GPU↔CXL; custom silicon. |
| **CXL-NDP / TRACE** | arXiv'24-25 (2509.03377) | **mostly simulated** | weights/KV pages | no | **yes (core focus)** | impl | no | partition only | Bandwidth amplification via in-controller compression, not placement. Complementary (place vs compress). [arXiv](https://arxiv.org/abs/2509.03377) |
| **Exploring CXL KV (ByteDance/Yale)** | NeurIPS'24 WS | **real CXL** | KV block (coarse) | partial | no | partial (prefix) | no | no | Validates CXL-as-KV-store; flat capacity. [PDF](https://mlforsystems.org/assets/papers/neurips2024/paper17.pdf) |
| **Mooncake** | FAST'25 (2407.00079) | **no CXL** (DRAM/SSD/RDMA) | KV block | scheduler | network-aware | **yes** | **yes** | **yes (overload reject)** | Reference KV-pool architecture; we'd sit under a Mooncake-like scheduler. [arXiv](https://arxiv.org/abs/2407.00079) |
| **LMCache** | arXiv'25 (2510.09665) | **no CXL** | KV block | control-API | pipelined | yes (prefix) | yes (PD) | cross-engine | Practical KV-tiering substrate; a CXL backend is a natural implementation vehicle for us. [PDF](https://arxiv.org/pdf/2510.09665) |
| **AttentionStore** | ATC'24 | HBM/DRAM/SSD | KV (per-layer) | no | no | yes (session) | prefill reuse | sessions | Multi-turn KV persistence. [paper](https://www.usenix.org/conference/atc24/presentation/gao-bin-cost) |
| **InfiniGen** | OSDI'24 | GPU+host DRAM | token/KV | no | no | yes (importance) | decode | no | Speculative important-token prefetch. [paper](https://www.usenix.org/conference/osdi24/presentation/lee) |
| **Pie** | arXiv'24 (2411.09317) | CPU pool (GH200 NVLink, not CXL) | KV page | no | no | yes (recency) | impl | no | Performance-transparent swapping. |
| **FlexGen** | ICML'23 | GPU+CPU+disk (no CXL) | tensor | LP cost model | impl | no | no | no | Classic placement-by-cost ancestor; used as a workload in §3.3. [arXiv](https://arxiv.org/abs/2303.06865) |
| **DistServe** | OSDI'24 | no CXL | n/a | n/a | n/a | n/a | **yes (PD disagg)** | n/a | Phase-disaggregation background. [arXiv](https://arxiv.org/abs/2401.09670) |

**Takeaway:** CXL-KV serving systems either treat CXL as a **flat pool / transfer substrate** (Beluga, TraCT, ByteDance-KV) or rely on **custom NDP/FPGA/PNM silicon** (CXL-SpecKV, CXL-PNM, CXL-NDP). **Multi-tenant interference on a commodity-CXL KV serving tier is essentially unaddressed.** Note for our own work: our KV layer-split null result is consistent with this literature — KV benefit comes from **prefix/request/recency skew** (TraCT, Mooncake, LMCache, AttentionStore), not static layer assignment. Do not claim KV benefit until recency skew is redesigned.

---

## 7. Embedding, GNN, Feature Store, and Vector Search

| System | Venue/Year | Hardware | Granularity | Guided? | BW | Skew | Phase | Multi-tenant | Note |
|---|---|---|---|---|---|---|---|---|---|
| **RecShard** | ASPLOS'22 | GPU HBM+UVM (no CXL) | table+row | yes | yes (MILP) | **yes** | no | no | Skew+BW-aware row placement; the classic precedent for our embedding result. [arXiv](https://arxiv.org/abs/2201.10095) |
| **Bandana** | MLSys'19 | NVM+DRAM | embedding vector→block | yes (co-access) | **yes** | yes | no | no | Co-access grouping to amplify slow-tier BW; canonical "naive per-object placement wastes far-tier BW." [arXiv](https://arxiv.org/abs/1811.05922) |
| **CARINA** | SIGMOD'25 | CXL **(real vs emulated NV)** | table/row (NV) | likely | yes | likely | NV | NV | **Most direct embedding-on-CXL competitor; read full PDF.** [ACM](https://dl.acm.org/doi/10.1145/3725274) |
| **ReCXL** | ISCA'24 | CXL + NMP (sim) | embedding op | no (arch) | **yes (quantifies CXL BW deficit)** | no | no | no | Its motivation = our motivation; runs whole embedding step in CXL via NMP. [IEEE](https://ieeexplore.ieee.org/document/10609725) |
| **DreamShard** | NeurIPS'22 | multi-GPU | table | partial (RL) | indirect | no | no | no | Learned table-to-device placement. [arXiv](https://arxiv.org/abs/2210.02023) |
| **RecNMP** | ISCA'20 | DIMM-NMP (sim) | embedding vector | partial | yes | partial | no | no | Embedding gather/reduce near memory. |
| **TensorDIMM** | MICRO'19 | buffered DIMM pool (sim) | vector/tensor op | limited | yes | no | no | no | Disaggregated embedding pool ancestor. [PDF](https://arxiv.org/pdf/1908.03072) |
| **PaGraph** | SoCC'20 | GPU+DRAM | vertex feature | yes | yes | **yes (degree)** | no | no | "Feature is object, hotness governs tier." [ACM](https://dl.acm.org/doi/10.1145/3419111.3421281) |
| **BGL** | NSDI'23 | distributed GPU+DRAM | vertex feature | yes | yes | yes | partial (sampling order) | partial (inter-stage) | Dynamic feature cache + stage isolation. [paper](https://www.usenix.org/conference/nsdi23/presentation/liu-tianfeng) |
| **Ginex** | VLDB'22 | SSD+DRAM | vertex feature | yes (lookahead) | yes | yes | partial | no | Belady-optimal feature caching. [arXiv](https://arxiv.org/abs/2208.09151) |
| **XGNN** | VLDB'24 | multi-GPU+host (**mentions CXL**) | feature | partial | yes | partial | no | no | Unified store over heterogeneous memory incl. CXL **(real CXL? needs verification)**. [PDF](https://ipads.se.sjtu.edu.cn/_media/publications/tang-vldb24.pdf) |
| **DiskANN** | NeurIPS'19 | SSD+DRAM | vector + graph block | partial | yes | partial (hop) | no | no | Foundational DRAM/SSD vector tiering. [PDF](https://suhasjs.github.io/files/diskann_neurips19.pdf) |
| **SPANN** | NeurIPS'21 | SSD+DRAM | cluster/posting list | yes (query-aware) | yes | partial | no | no | Centroids in DRAM, lists on SSD. [arXiv](https://arxiv.org/abs/2111.08566) |
| **Cosmos** | 2025 (2505.16096) | **simulated** CXL (4 dev) | cluster | yes | yes | **yes (adjacency)** | no | no | Skew-aware ANN cluster placement across CXL; needs in-CXL cores. **Key skew-on-CXL competitor (vector domain).** [arXiv](https://arxiv.org/abs/2505.16096) |
| **IKS** | ASPLOS'25 | **simulated** CXL Type-2 NMA | whole-DB scan | no | **yes** | **no (assumes no reuse)** | no | partial (spatial DB partition) | Flagship RAG-on-CXL; brute-force ENNS. Its multi-DB partition seeds the multi-tenant angle. [PDF](https://arg.csl.cornell.edu/papers/iks-asplos2025.pdf) |
| **FaTRQ** | arXiv'26 (2601.09985) | CXL Type-2 + accel (sim) | vector (quant residual) | partial | **yes (far-mem-aware)** | partial | no | no | Tiered residual quantization to cut far-tier traffic; overlaps our CXL-pressure dimension. [arXiv](https://arxiv.org/abs/2601.09985) |

**Takeaway:** **Skew is table stakes** here (RecShard, Bandana, CARINA, Cosmos, all GNN). **Bandwidth sensitivity** is widely handled. **Phase and multi-tenant interference are essentially unhandled** as placement signals (closest: IKS static DB partitioning, BGL inter-stage isolation). **Almost nobody runs on real CXL** — RecShard=GPU/UVM, Bandana=NVM, DiskANN/SPANN=SSD, ReCXL/Cosmos/IKS/FaTRQ=simulation. CARINA and XGNN are the only possible real-CXL candidates **(needs verification)**.

---

## 8. Comparison Table

Legend: ✓ yes · ~ partial/indirect · ✗ no · ? needs verification. Granularity: V=VM, Pr=process, Pg=page, O=object/struct, T=tensor, R=row/vector, K=KV block, Cl=cluster.

| Paper | Venue/Yr | Real CXL? | Gran. | App-guided? | BW-sens? | Skew? | Phase? | Multi-tenant? | Overlap with us | Remaining gap for us |
|---|---|---|---|---|---|---|---|---|---|---|
| **SoarAlto** | OSDI'25 | ✗ (NUMA emu) | O+Pg | ~ (profile) | ✓ (MLP/AOL) | ✓ | ~ | ✗ | Object-level beyond-hotness sensitivity | Online hints, multi-tenant, real CXL, serving phase |
| **Memstrata** | OSDI'24 | ✓ | V/Pg | ✗ | ~ (?) | ~ | ✓ | ✓ | Multi-tenant CXL sensitivity | Object granularity, app hints |
| Pond | ASPLOS'23 | ✗ (emu lat) | V | ✗ | ✗ | ✗ | ~ | ~ | CXL cost case, predict-tolerant pattern | BW/contention, objects, hints |
| TPP | ASPLOS'23 | ✓ | Pg | ✗ | ✗ | ✓ | ~ | ✗ | DRAM+CXL substrate | Everything beyond page hotness |
| **Colloid** | SOSP'24 | ✗ (NUMA emu) | Pg | ✗ | ✓ (loaded lat) | ✓ | ✓ | ~ | "Contention > hotness" | Objects, hints, real CXL |
| HeMem | SOSP'21 | ✗ (Optane) | Pg | ~ | ✓ | ✓ | ~ | ~ | BW-aware alloc + isolation | CXL, objects, hints |
| MEMTIS | SOSP'23 | ✗ (Optane/emu) | Pg | ✗ | ✗ | ✓ | ~ | ✗ | Skew sophistication | BW, objects, multi-tenant |
| Nomad | OSDI'24 | ✓ (?) | Pg | ✗ | ✗ | ~ | ✓ | ✗ | Pressure-reactive migration | Sensitivity, objects, hints |
| M5 | ASPLOS'25 | ✓ | Pg+64B | ✗ | ✗ | ✓ | ~ | ✗ | Sub-page skew on real CXL | BW, objects, hints |
| TMTS | ASPLOS'23 | ✗ (prod 2-tier) | Pg/Pr | ✗ | ✗ | ✓ | ✓ | ✓ | Production multi-tenant SLO | Objects, hints, CXL, BW |
| vTMM | EuroSys'23 | ✗ | Pg/V | ✗ | ✗ | ✓ | ~ | ✓ | Cross-VM fast-mem arbitration | Object granularity, BW, hints |
| X-Mem | EuroSys'16 | ✗ | O | ✓ (tags) | ✓ | ✓ | ~ | ✗ | Object+tagged+BW-aware | CXL, online hints, multi-tenant |
| MemBrain | TACO'22 | ✗ | O/site | ✓ (auto) | ~ | ✓ | ~ | ✗ | Site-based online guidance | CXL, BW classes, multi-tenant |
| CachedArrays | IPDPS'24 | ✗ (NVRAM) | O | ✓ (future-use) | ~ | ✓ | ✓ | ✗ | Semantic object hints | CXL, BW classes, multi-tenant, general |
| **Liu/Wang Real-CXL** | arXiv'24 | ✓ | O→Pg | ✓ | ✓ | ~ | ✗ | ✗ | Object BW-aware DRAM/CXL interleave | Serving, phase, skew, multi-tenant |
| **Liaw&Chen** | arXiv'25 | ✓ | T | ✓ (4-level) | ✓ | ~ | ✗ | ✗ | Sensitivity-tiered CXL objects | Serving, phase, recency, multi-tenant |
| Beluga | SIGMOD'26 | ✓ | K | ✗ | ✓ | ✓ | ✗ | ✗ | GPU↔CXL KV substrate | Tiering, hints, sensitivity, multi-tenant |
| TraCT | arXiv'25 | ✗ (MLC emu) | K | ~ | ✗ | ✓ | ✓ | ~ | Phase+recency CXL KV | Real CXL, sensitivity, multi-obj, isolation |
| CXL-SpecKV | FPGA'26 | ✓ (+FPGA) | Pg | ✓ | ✓ | ~ | ✓ | ✗ | Tiered KV + phase + BW | Commodity HW, hints, multi-tenant |
| CXL-NDP/TRACE | arXiv'24 | ✗ (sim) | Pg | ✗ | ✓ | ~ | ✗ | ~ | CXL BW bottleneck | Placement (they compress), hints, phase |
| Mooncake | FAST'25 | ✗ | K | ~ | ~ | ✓ | ✓ | ✓ | KV pool, phase, overload | CXL tier, object sensitivity |
| RecShard | ASPLOS'22 | ✗ (HBM/UVM) | R | ✓ | ✓ | ✓ | ✗ | ✗ | Skew+BW row placement | CXL, online, phase, multi-tenant |
| Bandana | MLSys'19 | ✗ (NVM) | R→blk | ✓ | ✓ | ✓ | ✗ | ✗ | Slow-tier embedding placement | CXL, phase, multi-tenant |
| CARINA | SIGMOD'25 | ? | R (?) | ✓(?) | ✓ | ✓(?) | ? | ? | CXL embedding serving | **Verify; likely single-tenant, no phase** |
| ReCXL | ISCA'24 | ✗ (sim NMP) | emb op | ✗ | ✓ | ✗ | ✗ | ✗ | CXL BW deficit motivation | Placement on commodity HW, skew/phase |
| Cosmos | 2025 | ✗ (sim) | Cl | ✓ | ✓ | ✓ | ✗ | ✗ | Skew-aware CXL placement | Commodity HW, DRAM/CXL tiering, phase, multi-tenant |
| IKS | ASPLOS'25 | ✗ (sim) | DB scan | ✗ | ✓ | ✗ | ✗ | ~ | RAG-on-CXL, multi-DB partition | Skew, tiering, real HW, hints |

---

## 9. Novelty Assessment

**What part of our idea is already covered (do NOT claim as novel):**
- *Object-level placement on heterogeneous memory* — X-Mem (2016), MemBrain, CachedArrays, bkmalloc, **SoarAlto (OSDI'25)**.
- *"Hotness ≠ performance; use a bandwidth/latency/contention-aware signal"* — **Colloid (SOSP'24)**, **SoarAlto (OSDI'25)**.
- *Bandwidth-sensitivity-aware DRAM/CXL placement at object level* — Liu/Wang real-CXL (2024), Liaw&Chen (2025).
- *Multi-tenant sensitivity isolation on CXL* — **Memstrata (OSDI'24)**, vTMM, TMTS (at VM/page).
- *Skew-aware embedding/feature placement* — RecShard, Bandana, CARINA, Cosmos, PaGraph (very crowded; our ~11–17% embedding result is incremental here).
- *Application hints for tiering* — X-Mem (tags), CachedArrays (future-use), MemBrain (call-site).

**What part is NOT covered (defensible white space):**
- **No system unifies object-granular, hint-driven placement with multi-tenant CXL bandwidth-pressure arbitration.** SoarAlto is object-level but single-tenant + profile-static; Memstrata is multi-tenant but VM-granular + transparent. The intersection is open.
- **Live, lightweight application-level bandwidth-sensitivity hints (no offline profiling pass).** SoarAlto's SOAR needs offline AOL profiling; CachedArrays hints are future-use/movement, not bandwidth-bound-vs-latency-bound. An online hint API stating "object X is bandwidth-bound → DRAM; object Y is latency-tolerant/cold → tolerate CXL" is not directly occupied.
- **Phase + CXL-pressure as first-class joint placement signals.** Phase is essentially unhandled in the heterogeneous-memory/embedding literature; CXL-pressure feedback driving object placement is unhandled.
- **Multi-tenant interference on commodity CXL as a placement driver for application objects** (vs characterization in CXL-Interference, throttling in MT2/Memstrata-coloring).
- **Real CZ120 commodity CXL evaluation** of object-level sensitivity-aware placement (most competitors are NUMA-emulated, Optane, SSD, or simulated/NMP).

**Is "object-level sensitivity-aware CXL placement" still novel?** **As a standalone phrase, no** — SoarAlto and Liu/Wang/Liaw&Chen already occupy it. **As a system that adds multi-tenant CXL-pressure + online hints + serving-phase awareness on real commodity CXL, the *combination* is defensible** but must be argued carefully against SoarAlto and Memstrata, not asserted.

**Claims to AVOID:**
- "First to do object-level sensitivity-aware tiering." (SoarAlto, X-Mem.)
- "First to observe hotness is insufficient / bandwidth matters." (Colloid, SoarAlto, HeMem.)
- "First skew-aware embedding/CXL placement." (RecShard, Bandana, CARINA, Cosmos.)
- Any KV-cache benefit claim from layer-split — our own null result + the literature say benefit comes from recency/prefix skew.
- "First multi-tenant CXL memory management." (Memstrata.)

**Claims that look DEFENSIBLE (pending the closest-paper reads):**
- First to drive object placement from **online application hints + live CXL-pressure feedback** (no offline profiling), as opposed to profile-guided (SoarAlto) or transparent (Colloid/Memstrata).
- First to handle **multi-tenant CXL bandwidth contention at intra-application object granularity** (bridging Memstrata's multi-tenancy and SoarAlto's object granularity).
- A **unified object-level hint interface** spanning embeddings/features/serving objects, validated on **real commodity CZ120 CXL** with measured contention (2.0–2.13×) and a measured per-device ceiling (~35.5 GiB/s).

---

## 10. Recommended Paper Positioning

**1. Strongest positioning (recommended): "Multi-tenant, hint-driven object placement on commodity CXL."**
Position against **Memstrata** (multi-tenant but VM/black-box) and **SoarAlto** (object-level but single-tenant/offline). Claim: *the first system to place application objects across DRAM and real CXL using lightweight online hints + live CXL-pressure feedback, explicitly to manage multi-tenant bandwidth contention.* The 2.0–2.13× contention measurement and ~35.5 GiB/s ceiling on real CZ120 anchor the motivation; the multi-tenant + online-hints combination is the novelty. This leans into the two genuinely under-served axes (phase, multi-tenant) and the real-hardware advantage.

**2. Safer positioning: "An empirical study + placement policy for commodity CXL under contention."**
Lead with characterization (corroborating Liu et al. / Dissecting-CXL on real CZ120), then present sensitivity-aware placement as the natural policy response, citing SoarAlto/Colloid as the page-level/emulated predecessors we extend to objects on real hardware. Lower novelty ceiling but very hard to refute; good fallback if the multi-tenant mechanism doesn't show large wins. Best fit for a measurement-friendly venue or if results are modest.

**3. Risky positioning to avoid: "First object-level sensitivity-aware CXL tiering."**
This collides head-on with SoarAlto (OSDI'25) and Liu/Wang/Liaw&Chen. A reviewer who knows SoarAlto will reject the novelty claim outright. Also avoid an embedding-skew-centric framing — RecShard/Bandana/CARINA/Cosmos make ~15% skew-aware embedding gains look incremental. **Do not build the paper's identity on skew or on "object-level beyond hotness."**

---

## 11. Bibliography

**CXL tiering / pooling / isolation**
- Pond — CXL-Based Memory Pooling, ASPLOS'23. https://arxiv.org/abs/2203.00241
- TPP — Transparent Page Placement for CXL, ASPLOS'23. https://arxiv.org/abs/2206.02878
- Managing Memory Tiers with CXL in Virtualized Environments (Memstrata), OSDI'24. https://www.usenix.org/conference/osdi24/presentation/zhong-yuhong
- CXL-Interference: Analysis and Characterization, arXiv'24 (venue NV). https://arxiv.org/pdf/2411.18308
- Dissecting CXL Memory Performance at Scale (Alto), arXiv'24. https://arxiv.org/abs/2409.14317
- Demystifying CXL Memory, MICRO'23. https://arxiv.org/abs/2303.15375
- Optimizing System Memory Bandwidth with Micron CXL (CZ122), arXiv'24. https://arxiv.org/abs/2412.12491
- Space-Control: process-level isolation for CXL, arXiv'26. https://arxiv.org/abs/2603.06951
- MT2: Memory Bandwidth Regulation on Hybrid NVM/DRAM, FAST'22. https://ipads.se.sjtu.edu.cn/_media/publications/yijfast22.pdf
- HMSDK (SK hynix, engineering SDK). https://github.com/skhynix/hmsdk

**Heterogeneous memory / page migration**
- SoarAlto — Tiered Memory Management Beyond Hotness, OSDI'25. https://www.usenix.org/conference/osdi25/presentation/liu · https://github.com/MoatLab/SoarAlto
- HeMem, SOSP'21. https://dl.acm.org/doi/10.1145/3477132.3483550
- MEMTIS, SOSP'23. https://multics69.github.io/pages/pubs/memtis-lee-sosp23.pdf
- Colloid — Access Latency is the Key!, SOSP'24. https://www.cs.cornell.edu/~ragarwal/pubs/colloid.pdf
- Nomad — Non-Exclusive Memory Tiering, OSDI'24. https://arxiv.org/abs/2401.13154
- M5 — Page Migration for CXL Tiered Memory, ASPLOS'25. https://jiyuan.is/papers/asplos25-m5.pdf
- TMTS — Adaptable Memory Tiering at Warehouse-Scale, ASPLOS'23. https://www.micahlerner.com/assets/pdf/adaptable.pdf
- vTMM — Tiered Memory for VMs, EuroSys'23. https://dl.acm.org/doi/10.1145/3552326.3587449
- X-Mem — Data Tiering in Heterogeneous Memory, EuroSys'16. https://courses.grainger.illinois.edu/ece598ms/fa2019/papers/paper121.pdf
- MemBrain — Online Application Guidance, TACO'22. https://arxiv.org/abs/2110.02150
- Flexible Object Tiering (bkmalloc), TACO'25. https://dl.acm.org/doi/10.1145/3708540
- CachedArrays, IPDPS'24. https://arch.cs.ucdavis.edu/assets/papers/ipdps24-cachedarrays.pdf
- Thermostat, ASPLOS'17. https://dl.acm.org/doi/10.1145/3037697.3037706
- Nimble, ASPLOS'19. https://www.cs.yale.edu/homes/abhishek/ziyan-asplos19.pdf

**CXL / LLM memory systems**
- Exploring and Evaluating Real-world CXL, arXiv'24. https://arxiv.org/html/2405.14209v1
- Performance Characterization of CXL Memory (PASA), IPDPS'25. http://pasalabs.org/papers/2025/IPDPS25_cxl_eval.pdf
- CXL-Attached Memory Allocation for Long-Context LLM Fine-Tuning (Liaw & Chen), arXiv'25. https://arxiv.org/abs/2507.03305
- Beluga — CXL KVCache Management, SIGMOD'26 / arXiv'25. https://arxiv.org/abs/2511.20172
- TraCT — Disaggregated LLM Serving with CXL Shared Memory KV, arXiv'25. https://arxiv.org/abs/2512.18194
- CXL-SpecKV — Disaggregated FPGA Speculative KV, FPGA'26. https://arxiv.org/abs/2512.11920
- CXL-PNM — Scalable PNM for 1M-token LLM Inference, arXiv'25. https://arxiv.org/html/2511.00321v1
- CXL-NDP / TRACE, arXiv'24-25. https://arxiv.org/abs/2509.03377
- Exploring CXL-based KV Cache Storage for LLM Serving, NeurIPS'24 ML-for-Sys WS. https://mlforsystems.org/assets/papers/neurips2024/paper17.pdf
- Mooncake, FAST'25 / arXiv'24. https://arxiv.org/abs/2407.00079
- LMCache, arXiv'25. https://arxiv.org/pdf/2510.09665
- AttentionStore / CachedAttention, ATC'24. https://www.usenix.org/conference/atc24/presentation/gao-bin-cost
- InfiniGen, OSDI'24. https://www.usenix.org/conference/osdi24/presentation/lee
- Pie — Pooling CPU Memory for LLM Inference, arXiv'24. https://arxiv.org/abs/2411.09317
- FlexGen, ICML'23. https://arxiv.org/abs/2303.06865
- DistServe, OSDI'24. https://arxiv.org/abs/2401.09670

**Embedding / GNN / feature store / vector search**
- RecShard, ASPLOS'22. https://arxiv.org/abs/2201.10095
- DreamShard, NeurIPS'22. https://arxiv.org/abs/2210.02023
- Bandana, MLSys'19. https://arxiv.org/abs/1811.05922
- CARINA — CXL-Oriented Embedding Serving, SIGMOD'25. https://dl.acm.org/doi/10.1145/3725274
- RecNMP, ISCA'20. https://arxiv.org/abs/1912.12953 (id needs verification)
- TensorDIMM, MICRO'19. https://arxiv.org/pdf/1908.03072
- ReCXL — Near-CXL-Memory Recommendation Training, ISCA'24. https://ieeexplore.ieee.org/document/10609725
- PaGraph, SoCC'20. https://dl.acm.org/doi/10.1145/3419111.3421281
- BGL, NSDI'23. https://www.usenix.org/conference/nsdi23/presentation/liu-tianfeng
- Ginex, VLDB'22. https://arxiv.org/abs/2208.09151
- MariusGNN, EuroSys'23. https://arxiv.org/abs/2202.02365
- XGNN, VLDB'24. https://ipads.se.sjtu.edu.cn/_media/publications/tang-vldb24.pdf
- DiskANN, NeurIPS'19. https://suhasjs.github.io/files/diskann_neurips19.pdf
- SPANN, NeurIPS'21. https://arxiv.org/abs/2111.08566
- Cosmos — CXL Full In-Memory ANN Search, arXiv'25. https://arxiv.org/abs/2505.16096
- IKS — Accelerating RAG (Intelligent Knowledge Store), ASPLOS'25. https://arxiv.org/abs/2412.15246
- FaTRQ — Tiered Residual Quantization for Far-Memory ANNS, arXiv'26. https://arxiv.org/abs/2601.09985

---

### Verification to-do before citing in a submission
- **Read in full:** SoarAlto (OSDI'25), Memstrata (OSDI'24), Colloid (SOSP'24), CARINA (SIGMOD'25, PDF was blocked), TraCT (2512.18194, lossy fetch), Liu/Wang real-CXL (2405.14209).
- Confirm real-CXL vs emulation for: Pond, Nomad, CARINA, XGNN, RecXL.
- Confirm whether Memstrata's slowdown estimator uses bandwidth as an explicit feature.
- Confirm venues for: CXL-Interference, Cosmos, FaTRQ; and full author lists for Beluga, HeMem, MEMTIS, Bandana, IKS, RecNMP arXiv id.
- Confirm bkmalloc (TACO'25) is hint- vs profile-driven.

## PolyStore (FAST'25) — read in full 2026-09-08 (docs/PolyStore_FAST25.pdf, local only)
Ren, Domingo, Zhang, John (Rutgers), Pitchumani (Samsung), Kashyap (EPFL), Kannan (Rutgers).
**Claim:** storage media are now "non-hierarchical" (PM, NVMe, SATA overlap in capability);
the philosophy of hierarchy (caching/tiering/app-directed) leaves cumulative bandwidth
unused. PolyStore = horizontally structured HSD architecture: userspace runtime
intercepting POSIX + thin VFS component (PolyOS) atop device-optimized FSes (NOVA/ext4/F2FS).
**Mechanisms:** Poly-inode (logical file → several physical files), Poly-index (range tree,
2 MB nodes, per-range RW locks), Poly-placement (Alg. 1: epoch-based 200 ms thread
remapping low↔high device with STABLE state; Alg. 2: bandwidth-aware BW_Move of hot blocks
to the faster device only when it is not saturated + capacity-aware CAP_Move at 90%),
Poly-cache (userspace DRAM cache, device-specific admission: bypass cache for PM reads,
dynamic cache ratio for SSDs, concurrent evictions across devices), Poly-persist
(coordinated atomicity/durability across FSes, journal on the fast device).
**Numbers (Config I: 256 GB Optane PM + 1 TB NVMe; PM 4.6/13.2 GB/s W/R, NVMe 1.2/1.2):**
seq write 2.16× vs PM-only, 3.25× vs NVMe-only, 4.23× vs Orthus; dynamic placement reaches
92.3% of combined; random-write latency −6.38×; reads +1.11× over PM-only; three devices
91.7% of combined; RocksDB YCSB A/F 1.52–2.02×; multi-app 1.96× vs P2CACHE.
**Three hierarchy pitfalls they name (§3):** writes forced to the top device → contention as
threads grow; eager migration/eviction steals bandwidth; DRAM caching static, not
heterogeneity-aware.
**What it does NOT cover — our openings:** (1) memory tier / byte-addressable CXL (they stop
at file/block, 2 MB ranges); (2) host-side traffic DIRECTION as a placement axis (RFO tax,
duplex link, async stores) — they model devices by measured R/W bandwidth only; (3)
inter-device interference/isolation is assumed away (they monitor saturation, never
cross-device disturbance); (4) PM is treated as *read-preferred* (bypass cache for PM
reads) — CXL is the mirror image (write-preferred), a clean contrast for the intro;
(5) no memory→storage staging path (our DRAM→CXL→NVMe checkpoint shape).
**Reusable ideas:** epoch-based thread/device remapping with saturation guard (Alg. 1)
maps onto per-direction budgets; "migrate only if target not saturated" (Alg. 2) is our
promote-on-hit rule; POSIX-intercept + thin kernel shim answers "apps can't allocate
this way" for the memory tier (malloc/mmap interposition).
