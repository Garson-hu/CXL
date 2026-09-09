# 2026-09-08 — Phase 4a: memory objects of LULESH 2.0 and VeloC, and what belongs on CXL

**STATUS: ANALYSIS DONE 2026-09-08 (static, from source). Instrumented measurement +
placement experiments (4b) not started — 4b needs healthy DRAM.** Campaign Phase 4 of
`2026-09-08-write-tier-campaign.md`. Sources: LULESH 2.0 at `~/apps/lulesh` (LLNL master,
commit 3e01c40); VeloC at `~/checkpoint/veloc/src` (user's branch — includes a
`flush_mem` direct-memory path not in upstream).

## LULESH 2.0 — what one timestep does to memory
`LagrangeLeapFrog` = nodal phase → element phase → time constraints. Per element
(`numElem = s³`) and per node (`(s+1)³`), Real_t = 8 B:

| group | arrays | per-step traffic | class |
|---|---|---|---|
| **A. read-only after init** | `nodelist`(8 idx/elem), `lxim/lxip/letam/letap/lzetam/lzetap`, `elemBC`, `nodeElemStart/CornerList`, `symmX/Y/Z`, `volo`, `elemMass`, `nodalMass`, `regElemList` | read 1–4× / step, never written | **read-mostly → DRAM** (or anywhere; small: ~100 B/elem) |
| **B. per-phase temporaries** | `fx_elem/fy_elem/fz_elem` (8/elem ×3, allocated TWICE per step: stress + hourglass), `sigxx/yy/zz`, `determ`, `dvdx/dvdy/dvdz`, `x8n/y8n/z8n` (8/elem ×6), `vnewc`, `pHalfStep`, and 14 EOS temporaries per region (`e_old … pbvc`) | written once, **read back within the same phase (µs–ms later)**, then freed | **write-then-read-immediately → NOT a CXL candidate by the policy**; largest write volume of the step (~600 B/elem peak) |
| **C. state, read-modify-write** | `x,y,z` (+= xd·dt), `xd,yd,zd` (+= xdd·dt), `e,p,q,ql,qq` (EOS), `v` (= vnew), `ss`, `dxx/dyy/dzz`, `delv`, `vdov`, `arealg`, `delv_*`, `delx_*`, `vnew` | written 1× / step, read 1–5× / step (`x,y,z,xd,yd,zd` are gathered through `nodelist` in 3–4 phases) | **read-heavy overall → DRAM**; pure 1:1 RMW streams only for `e,p,q,v,ss` (duplex-shaped, but reads are on the critical path) |
| **D. accumulated forces** | `fx,fy,fz`, `xdd,ydd,zdd` | zeroed, RMW-accumulated by node-gather (random), read once by the acceleration update | random RMW, latency-bound → **DRAM** |
| **E. checkpoint / history** | a snapshot of C (+ needed A) ≈ 280 B/elem + 104 B/node | written once per checkpoint interval, read only on restart | **THE write-tier object** — LULESH has no built-in checkpointing; VeloC supplies it |

Footprint ≈ s³ × ~950 B at the hourglass peak (temporaries dominate): s=100 → ~0.95 GB
(4× the 256 MB L3), s=160 → ~3.9 GB, s=200 → ~7.6 GB. Use **s ≥ 160** for out-of-LLC runs.

**Honest verdict for the solver loop:** LULESH contains no array that is write-heavy
*and* not re-read soon. Everything it writes is either consumed within the phase (B) or
is state that is read several times before its next write (C). By the policy
`write-heavy ∧ low immediate reuse ∧ DRAM pressure → CXL`, **nothing inside the loop
qualifies**; the qualifying object is the checkpoint (E). Two secondary, speculative
uses that only 3c-style measurements can settle: (i) group-B temporaries written with
NT stores to CXL under heavy DRAM pressure (they spill past L3 at s ≥ 100 and cost a CXL
read-back — the exact trade-off the stencil `copyback/pingpong` measures); (ii) the
1:1 RMW state (`e,p,q,v,ss`) as duplex streams. Default plan: DRAM for A–D, CXL for E.

## VeloC — the checkpoint data path (this branch)
1. `VELOC_Mem_protect` registers application regions (`mem_regions[name][id] = {ptr,size}`) —
   no copy; these live wherever the app put them (DRAM).
2. `checkpoint_mem`: for raw-pointer regions in async mode this branch first tries
   **`storage()->flush_mem(regions)`** (direct memory flush, no local file); otherwise it
   writes a header + every region into the **scratch file** with `posix_cached_file_t::pwrite`
   (synchronous `pwrite` to the local file `fl`), and an **async thread** re-reads the local
   file and mirrors each range to the remote/persistent file `fr` (`async_write`,
   bounded by `MAX_QUEUE_SIZE`).
3. The backend `posix_module` moves `scratch → persistent` with `posix_transfer_file`
   (read scratch, write persistent) and restores `persistent → scratch` on restart.
Objects and classes: **app regions** — read once per checkpoint (streaming) → DRAM;
**scratch file** — write-once, read-once (drain), read again only on restart → **CXL**;
**persistent** — write-once → **NVMe `/mnt/local`**; async queue metadata — tiny → DRAM.

## How to put the scratch tier on CXL with zero application changes
- `scratch` = a tmpfs mounted with `mpol=bind:1` (node 1 = the CXL cards at c1/e1): every
  checkpoint page lands in CXL memory through the page cache; the drain reads CXL → NVMe.
  Needs one root `mount` (small admin ask) — the deployable path.
- Or the branch's `flush_mem` path pointed at a CXL mmap (`/dev/dax2.0`, NT-store copy):
  that is literally `obj_stage_out()` from `DESIGN.md` §7 — our own code, no root.

## 4b design (after the BIOS revert)
LULESH-OpenMP `-s 160 -i 100`, 16–32 threads; VeloC checkpoint every 10 steps of the
state arrays (E). Compare per-step time during and between checkpoints for
scratch ∈ {tmpfs on DRAM node 0, tmpfs on CXL node 1, dax2.0 via flush_mem}, with and
without a DRAM-pressure aggressor (8T NT writers on node 0, separate CCD). Expected by
Gate 2b: checkpoint-to-CXL leaves step time at idle level; checkpoint-to-DRAM stalls
steps while the pwrite stream drains. Secondary (optional): group-B temporaries on
CXL with NT stores under pressure (needs an allocator hook in `Allocate<>()`).
Policy extraction then reads directly off the table: E → CXL always; B → CXL only under
pressure and only if duplex covers the read-back; A, C, D → DRAM.

## Addendum 2026-09-08 — candidate applications from the literature (broad scan)
Sources: the 97-paper review JSON (`benchmarks/results/2026-07-08-cxl-lit-review.json`),
PolyStore (FAST'25), and general systems knowledge. Fit criteria: (1) a large object
written far more than it is read; (2) reads come later (next phase / on hit / on
failure), not within the same phase; (3) written while the app is DRAM-bandwidth-bound;
(4) runnable on c28 (CPU-side, 8 GB GPU, single node).

| rank | application / object | write-then-read distance | literature evidence (CXL) | fit | c28 feasibility |
|---|---|---|---|---|---|
| 1 | **Checkpoint / snapshot staging** — VeloC/SCR (HPC), `torch.save` model+optimizer state (ML), MicroVM snapshots | read only on failure/restore (hours) or once by a drain | Aquifer (snapshots restored from CXL pool, 2.2× invocation); SAP HANA fast restart from CXL (EDBT); CXL-Powered DB "dual checkpoint" (ICDE, conceptual) | ★★★ exact shape of Gate 2b | ✅ VeloC in workspace; LULESH cloned; NVMe `/mnt/local` for persistent |
| 2 | **LLM KV-cache eviction / prefix-cache insertion** (multi-turn serving) | read on reuse next turn (seconds–minutes) or never; active-decode KV is the anti-case | Beluga SIGMOD'26 (real ASIC, 7.35× vs RDMA path), TraCT, ITME (+35.7% over CPU offload), "Exploring CXL KV Cache Storage" (+30% batch under TTFT SLO), Mooncake FAST'25 (KVCache store on DRAM/SSD); all direction-blind | ★★★ largest paper appeal; write volume O(GB) per prefill | 🟡 CPU-side KV pool + small model on 8 GB GPU or CPU inference; traces in `workloads/` |
| 3 | **Optimizer state / gradient RMW streams** (ZeRO-Offload-style CPU Adam, activation offload) | 1:1 read-modify-write per step; activations: written forward, read backward | Long-context fine-tuning paper (real ASIC): naive CXL placement made CPU optimizer STEP ~4× slower → they pin optimizer to DRAM. **Directly testable counter-hypothesis:** with NT stores + streaming reads (duplex) the RMW stream may be CXL-friendly | ★★☆ the duplex sweet spot; contradicts a published conclusion | ✅ emulate CPU-Adam over multi-GB fp32 tensors, no big GPU needed |
| 4 | **LSM KV store write path** — RocksDB WAL (append, read on recovery), memtable flush → SST, compaction outputs | WAL: on recovery; flush/compaction outputs: read later by queries (minutes) | PolyStore RocksDB YCSB A/F 1.52–2.02×; Samsung CMM-H db_bench; Nomad Redis YCSB 50/50 | ★★☆ WAL/flush buffers fit; the memtable (random RMW skiplist) does NOT | ✅ RocksDB builds on c28; needs allocator/placement hooks for WAL and flush buffers |
| 5 | **Redis RDB snapshot / AOF rewrite** | snapshot: read never (until restore) | PolyStore evaluated Redis AOF; Nomad Redis | ★★☆ | ✅ easy |
| 6 | **Out-of-core / edge-centric graph processing** (X-Stream, GraphChi, GridGraph update streams; GraphWalker walk logs) | scatter writes update stream → gather reads it next phase (the stencil rotation problem, sequential) | PolyStore GraphWalker (writes walk info; 1.84×); many CXL papers use PageRank but vertex-array RMW is random → poor | ★★☆ two-device ping-pong applies | ✅ |
| 7 | **DB spill / external sort / hash-join partitions / shuffle** (DuckDB, Spark, HANA temp tables) | written once, read once by the next operator | SAP HANA temp tables on CXL only 4–13% slower (VLDB'24) — temporaries tolerate CXL; in-memory data processing paper (VLDB'25) | ★★☆ write-once-read-once sequential | 🟡 DuckDB out-of-core TPC-H on c28 |
| 8 | **DB WAL / redo log, dirty-page writeback** | log: on recovery; pages: read by later queries | CXL-Powered DB (ICDE): dirty-page sync, force commit with CXL+PMEM | ★★☆ excellent shape, modest volume | 🟡 PostgreSQL/MySQL |
| 9 | **In-situ HPC I/O staging / burst buffers** (ADIOS2, DataSpaces) | simulation writes every N steps, analysis reads later | thin CXL evidence; classic HPC pattern | ★★☆ same shape as checkpoint with a consumer | 🟡 ADIOS2 install |
| 10 | **Append-only logs / telemetry / message queues** | read once by lagging consumers | 3 weak CXL mentions | ★★☆ structurally ideal, no CXL literature | ✅ synthetic |
| ✗ | active-decode KV cache; HANA HEX heap (random); embedding tables (read gathers); PageRank vertex arrays; TPC-C OLTP (lock-bound); ANN/vector search | read-heavy or random | SAP: HEX on CXL −78%; long-context paper: optimizer pinned to DRAM | poor | — |

**Cross-cutting evidence for the write-tier premise:** Micron/Intel Xeon 6 white paper — DRAM loses 20% at 1:1 R:W while CXL-only *gains* on mixed R/W (214 vs 205 GB/s), best DRAM+CXL 2W:1R +34%; Samsung CMM-H — NT stores ~7× faster than temporal stores on the device; VLDB'25 (FPGA devices) — writes scale 2×/3×/3.7× with 2/3/4 devices but those devices write at 13.5–18 vs read 38–40 GB/s — **device-dependent asymmetry** (our CZ120: write 22 ≈ read 24 per card) — worth a sentence in the paper.

**Recommendation:** two anchors + one probe. (A) Checkpointing (rank 1) — LULESH+VeloC, plus a `torch.save`-shaped snapshot of optimizer state; deployable, advisor-aligned. (B) KV-cache eviction/prefix insertion (rank 2) — paper appeal, evidence-rich, direction-blind prior work. (C) Optimizer-state RMW stream (rank 3) as a focused experiment that tests a published "pin to DRAM" conclusion against duplex. RocksDB/Redis (4–5) as secondary breadth if time allows.
