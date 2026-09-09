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
