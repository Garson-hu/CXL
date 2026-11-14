# 2026-11-12 — CXL vs. NVMe memory expansion for LLM serving (KV cache; exploratory)

**STATUS: IN PROGRESS — draft of 2026-11-14 07:50, the last replays are still running and the text carries PENDING marks (started 2026-11-12; branch `explore/cxl-vs-nvme-serving`, from `explore/gpu-kv-admission`, whose
store-counter fix every LMCache configuration uses; not merged anywhere).** This study does not change the research charter
or the conclusions of the 2026-11-04 and 2026-11-10 studies; it is the first of the three that runs on the real CXL devices.
Raw data: `experimental_results/2026-11-12-cxl-vs-nvme-serving/` (`README.md` there lists every file; `SUMMARY.md` is the
short version of this report; during the study the directory was a symlink to c28's local NVMe). Tools: `benchmarks/serving/`
(the 2026-11-04 harness with the tiers `hyb`, `daxl2`, `ssdn`; `kvtier/` logging hook in the cache server; `run_a.py`,
`run_eqhit.py`, `run_e.py`, `replay.py`; `analyze_tier*.py`, `table_tier_*.py`, `writes_tier.py`, `pairs_tier.py`,
`matrix_tier.py`, `verify_residency.py`, `trace_capacity_tier.py`).

<!-- SUMMARY -->
## Summary (2026-11-14)

Everything below is MEASURED on c28 — one RTX 4060 Ti (8 GiB, PCIe 4.0 ×8), Qwen2.5-3B-Instruct-AWQ, vLLM 0.31.0 + LMCache
0.5.5 — with the CXL results on the real devices (`/dev/dax1.0` + `/dev/dax0.0`, 512 GiB over one pair of CZ120 cards; KV
residency verified by content after every validation run) and the NVMe results with O_DIRECT (page cache verified empty). The
only model in the report is the offline trace-capacity analysis (C.6) and its timed variant (C.4.5), labelled as such.

**Verdict.** Under a fixed 80 GiB DRAM KV budget, 512 GiB of additional KV cache is worth having, and on this node it is
worth the same whether it is CXL memory or a properly configured NVMe tier. Expansion removes 16–24 % of the GPU's prefill
work at high load, roughly halves TTFT there and adds 6 % of throughput at saturation — with either medium, within 1 % of
each other in every replay. CXL's advantage is real per hit (a CXL hit costs what a DRAM hit costs; an NVMe hit is 1.2–3.1×
slower) but reaches end-to-end metrics only where a hit is not queued behind the GPU: 2.5–6.4 % of the requests of the
replayed traces.

1. **The CXL path is real and correct (A.3, I).** LMCache places KV on Device-DAX as first-level memory (registered with CUDA;
   the GPU copies from and to it directly) or as a second level behind DRAM; independent hashes of the device mapping match
   the stored chunks (85 / 85, 155 / 155, 35 / 35 objects; 340 / 340, 592 / 592 slots), and the cache server holds no DRAM
   copy of CXL-resident KV. No DRAM stand-in is used anywhere.
2. **One hit (C.1).** 16K-token prefix, idle server: GPU prefix cache 44 ms, DRAM 94 ms, CXL L1 93–94 ms, CXL as L2 114 ms,
   NVMe 290 ms, recompute 3,385 ms. The GPU reads CXL memory at 12.4 GiB/s — the rate of its own link, as from DRAM — and the
   NVMe delivers 2.9 GiB/s (on two of its four lanes). The GPU *writes* registered CXL memory at 3.89 GiB/s against
   12.14 GiB/s into DRAM.
3. **Identical hits under load and in bursts (C.2, C.3).** CXL L1 = DRAM in every quantile at every rate. NVMe: TTFT p50
   +55–71 % at 0.5–4 requests/s, 2.2–2.9× in bursts of up to 16 simultaneous hits (the device is the limit; more I/O threads
   change nothing); at saturation all cached tiers converge (5.0–5.3 requests/s).
4. **Trace replays, same requests in every configuration (C.4).**

   | window | cached share: DRAM only → + 512 GiB | recomputed tokens | TTFT p50 s: DRAM only → CXL hybrid / NVMe | TTFT mean s | completed req/s |
   |---|---|---|---|---|---|
   | conversation, 0.04× | 0.093 → 0.182 | −9.8 % | 3.92 → 3.20 / 3.19 | 7.04 → 6.36 / 6.36 | equal |
   | tool-agent, 0.04× | 0.383 → 0.446 | −10.2 % | 2.08 → 1.49 / 1.50 | 5.81 → 5.15 / 5.15 | equal |
   | conversation, 0.08× | 0.096 → 0.238 | −15.8 % | 16.71 → 8.67 / 8.62 | 22.42 → 13.32 / 13.25 | equal |
   | tool-agent, 0.08× | 0.396 → 0.495 | −16.3 % | 12.40 → 6.30 / 6.31 | 19.78 → 11.60 / 11.47 | equal |
   | conversation, 0.08×, long (11,250 s) | 0.097 → 0.309 (CXL) / 0.302 (NVMe) | −23.5 % / −22.7 % | 14.46 → 6.15 / 6.24 | 21.42 → 9.72 / 9.85 | equal |
   | conversation, 0.16× (overload) | 0.130 → 0.208 / 0.209 | −8.9 % / −9.0 % | 857 → 793 / 791 | 836 → 755 / 753 | 0.287 → 0.305 / 0.306 |

   The gain reaches hits and misses alike through the GPU's queue. The NVMe's slower load (78–106 ms at the median inside the
   cache server) runs while the request waits for the GPU; it shows only on hits that find the GPU free (+45 to +116 ms).
5. **Where the two extensions differ (C.4.4, C.4.5).** In the long window, the only one that fills them, the CXL hybrid
   keeps more (0.309 against 0.302; 28 of 2,728 requests) because it is one exclusive cache level of 592 GiB while a file tier
   is an inclusive second level of 512 GiB — a difference of tier structure, not of speed. PENDING-DAXL2-SUM Wherever the hit
   rates are equal the hybrid is the slower of the two by 0.3–1 % of the mean TTFT (its stores into CXL memory are slow).
6. **Sustained overload (C.4.5).** With default settings the engine died in both attempts: LMCache's read lock on looked-up
   chunks lasts 300 s, requests waited longer, and vLLM's default failure policy plus an assertion end the engine. With the
   lock at 7,200 s all three configurations complete; throughput then follows the cache (+6.3 % / +6.5 %) and the two media
   are equal again. The lookup runs a median 377–418 s ahead of the service there, which costs the extensions 3 points of
   cached share.
7. **Traffic on the CXL memory (C.5).** 2–18 MiB/s of reads and 22–74 MiB/s of writes on average; the busiest second moves
   2.1 GiB (< 5 % of the pair's bandwidth); reads and writes never overlap on the hybrid's path (one transfer thread); 79–86 %
   of the KV written to an extension is not read again within the window.
8. PENDING-SENS-SUM
9. **Costs of the CXL configuration.** Registering 592 GiB of host memory with CUDA takes 1.2 GiB of the 8 GiB card (every
   configuration therefore runs with a 14 % smaller GPU KV pool than in the previous study), and the store direction is 3.1×
   slower than into DRAM.
10. **Not established.** Anything beyond one small GPU and a 3B model; independent CXL devices; hardware-counter views of the
    traffic; run-to-run variation (one run per cell).

## Question

**Under a fixed host DRAM budget, how does CXL memory expansion compare with NVMe-based KV cache expansion in end-to-end LLM
serving?** The brief of 2026-11-12 asks for the real CXL path (no DRAM stand-in), an 80 GiB DRAM KV budget, a 512 GiB
extension on either medium with matched logical capacity, media costs separated from software-path overhead, and five
experiment families: A single-request retrieval cost, B end-to-end cache expansion on trace replays, C equal-hit comparison,
D concurrent retrieval, E KV read / write traffic on the CXL memory. It excludes new cache-replacement algorithms and
schedulers, intra-request decode offloading, and repeating the scheduling study. The report follows the brief's outline:
A configuration, B matrix, C results per family, D causal analysis, E cross-experiment analysis, F negative results,
G limitations, H final answers; I is the correctness checklist of the brief's section 15.

**Evidence labels.** MEASURED unless marked otherwise. **Model** = the offline LRU analysis of the traces (C.6) and its
variant driven by measured times (C.4.5) — not served by anything. **Previously measured** = a closed experiment file, cited
with its date. Device names are the node's own: `dax0.0`, `dax1.0` (used), `dax2.0` (another project's; never opened).

## A. Hardware and software configuration

### A.1 Platform (c28, inspected 2026-11-12; record: `experimental_results/2026-11-12-cxl-vs-nvme-serving/env/inspect-2026-11-12.txt`, script `benchmarks/serving/inspect_cxl_env.sh`)

| component | what is there | what it means for this study |
|---|---|---|
| CPU | AMD EPYC 9745, 1 socket, 128 cores / 256 threads, one NUMA node (node 0), kernel 6.14.11+ | vLLM on CPUs 96–119, LMCache on 120–127 (8 cores), request drivers on 80–87, samplers on 94–95, analysis scripts on 64–79; nothing else used the GPU or the CXL devices during the study |
| DRAM | 755 GiB installed (729 GiB free at the start) | the *budget* of the KV cache is 80 GiB (section A.5), not the installed memory |
| GPU | 1 × NVIDIA RTX 4060 Ti, 8,188 MiB, driver 580.65.06, PCIe 4.0 ×8 (the link idles at gen 1 and trains up under load) | host-to-GPU copies run at 12.4 GiB/s (measured in every run of Experiment A); the 8 GiB of GPU memory are shared by the model, vLLM's KV pool, LMCache's staging buffers and the GPU-side cost of registered host memory (A.4) |
| NVMe | SOLIDIGM SBFPFABU038T 3.5 TB (firmware 6CV10110), ext4 (`rw,relatime`) on `/mnt/local`, scheduler `none`, 512-byte logical blocks; **PCIe link trained at 16 GT/s ×2 of a ×4-capable device** | O_DIRECT reads through LMCache reach 2.9 GiB/s (Experiment A) — the device on half of its lanes; this is the SSD c28 has, disclosed as a limitation (G) |
| CXL | 4 × Micron CZ120 256 GiB (PCI 01:00.0, 02:00.0, c1:00.0, e1:00.0), all exposed as Device-DAX (`devdax`, 2 MiB alignment, `target_node 1`; no CXL NUMA node) | see A.2 |
| software | vLLM 0.31.0, LMCache 0.5.5 (multi-process mode), PyTorch 2.13.0 + CUDA 13.0, Python 3.12.15; model Qwen/Qwen2.5-3B-Instruct-AWQ, fp16 KV: 36 KiB per token, one 256-token chunk = 9,437,184 bytes (9 MiB), 16-token GPU blocks | same model and GPU as the 2026-11-04 and 2026-11-10 studies |

### A.2 CXL devices: what the DAX files are, and which were used

| device file | size | owner / mode | backing | use in this study |
|---|---|---|---|---|
| `/dev/dax1.0` | 289,373,421,568 B = 269.5 GiB | `root:kmem 0660` (user in `kmem`) | root decoder 0.1, 2-way interleave at 256 B over the card pair c1:00.0 + e1:00.0 | used, whole device |
| `/dev/dax0.0` | 260,382,392,320 B = 242.5 GiB | `root:kmem 0660` | root decoder 0.0, the **same** two cards, a second address window | used, whole device |
| `/dev/dax2.0` | 549,755,813,888 B = 512 GiB | `root:root 0600`, mounted as famfs on `/mnt/famfs/dax2.0` | root decoder 0.2 → port decoder 3.0 (2-way) → cards 01:00.0 + 02:00.0 | **not used, not opened** (another project) |

`dax0.0` and `dax1.0` are two windows over one hardware-interleaved pair of cards, not two independent devices: 242.5 + 269.5 GiB is
exactly the 2 × 256 GiB of the pair, every byte of both windows is striped across both cards, and traffic to one window shares the
cards with traffic to the other. Together they are the 512 GiB extension of the brief. Nothing was reconfigured (no `daxctl`, no
region or firmware change, no mount); the devices had no other user (no process maps them) and hold no data of another project
(they were this project's scratch space in all earlier phases). The mapping of the windows to the cards rests on the size accounting
and the decoder topology established in the 2026-08 / 2026-09 experiments; the kernel's CXL driver enumerates only the other pair.

### A.3 The KV data paths, validated (P0; `P0/tables-p0.md`, `benchmarks/serving/verify_residency.py`)

LMCache 0.5.5 offers three ways to put KV on these media. Their software paths differ, and the differences decide the results:

| | hybrid L1 on Device-DAX ("CXL memory tier") | DAX L2 adapter | file L2 adapter on NVMe (`fs_native`, C++; `fs`, Python) |
|---|---|---|---|
| where a new chunk goes | GPU → L1 object; the L1 allocator takes DRAM first and Device-DAX when DRAM is full. One copy, no later movement | GPU → DRAM L1 object, then an asynchronous store copies it into a fixed 9 MiB slot of the DAX arena (`ctypes.memmove` by a store worker) | GPU → DRAM L1 object, then an asynchronous store writes one file per chunk (O_DIRECT) |
| hierarchy | exclusive: a chunk is in DRAM **or** on CXL; unique capacity = DRAM + CXL | inclusive with the default write-through policy: every chunk is in the L2, the hot ones also in L1; unique capacity = L2 | the same as the DAX L2 |
| what a hit does | the GPU staging copy reads the L1 object where it is: straight from the DAX mapping, which is registered with CUDA (`cudaHostRegister`) | lookup finds the key in the L2, a load worker copies the slot into a freshly allocated DRAM L1 object (`memmove`, 4 load workers), then the usual GPU copy from pinned DRAM | the same with a file read (O_DIRECT, 4 I/O threads) instead of the `memmove` |
| CPU copies of a hit | none | one (CXL → DRAM) | one (NVMe → DRAM, by the kernel's direct I/O) |
| eviction | one LRU over all L1 objects at 0.8 of the L1 (DRAM + DAX); no demotion or promotion between the media | L1: LRU at 0.8; L2: its own LRU at 0.8 of the slots | L1: LRU at 0.8; L2: its own LRU at 0.8 of `max_capacity_gb` (file deletion); the Python `fs` adapter has no capacity limit |
| metadata | DRAM (Python dictionaries) | DRAM (key → slot; not recoverable after a restart) | DRAM index; the file names encode the keys |
| GPU memory cost | 2.03 MiB per GiB of registered memory (A.4) | none for the DAX arena (not registered) | none |

The validation runs (short single-request runs with hashing enabled; each check made right after its run, before anything else wrote to
the devices) established, for the real devices:

- **KV placed on CXL is on CXL.** The hook records the device offset and SHA-1 of sampled Device-DAX L1 objects 3 s after their
  allocation and of every chunk written to a DAX L2 slot; an independent process then maps the device read-only and hashes the same
  ranges. All compared ranges are equal: pure DAX L1 85 of 85, hybrid L1 on both windows 155 of 155 (114 on `dax1.0`, 41 on `dax0.0`),
  hybrid L1 over the full 512 GiB 35 of 35, DAX L2 340 of 340, DAX L2 over the full 512 GiB 592 of 592 (312 + 280).
- **No silent DRAM copy.** With 2.99 GiB of KV in a pure Device-DAX L1 the cache server's resident memory stays at 0.50 GiB
  (anonymous) — the DRAM tier of the same size holds 8.49 GiB; in the hybrid L1 the resident memory is the DRAM part and nothing else
  (2.01 / 4.01 / 80.01 GiB of shared memory for a 2 / 4 / 80 GiB DRAM part).
- **The GPU reads CXL memory directly.** Every Device-DAX arena reports a successful CUDA registration (`pinned: true`; 5 s per
  window at full size), the staging copies of CXL-resident chunks run at the same 12.4 GiB/s as from pinned DRAM (Experiment A), and
  LMCache's fallback for unregistered memory was measured separately (the `a-hyb-nopin` variant).
- **NVMe reads reach the device.** With `use_odirect` the block device's own counters (`/proc/diskstats`, `nvme1n1`) show exactly the
  bytes LMCache loaded and stored (10.30 GiB read = 10.30 GiB loaded; 2.99 GiB written = 2.99 GiB stored), 0 of 783,360 pages of the
  cache files are in the page cache, and the page cache does not grow. The **buffered control** (`use_odirect=false`, run
  `p0-ssdn-buf`) shows what contamination looks like in the same checks: 100 % of the files' pages in the page cache, 3.3 GiB of page
  cache growth, and **0 bytes read from the device** — every "SSD" hit of that run is a DRAM hit. No performance number of this study
  comes from buffered file I/O; the only buffered run in Experiment A (`a-ssdn-buf`) is labelled as the contaminated control.
- **Per-run isolation.** Every file-tier run writes to its own directory (`/mnt/local/ghu4/kvl2/<tag>`), removed after the run; the
  system-wide page cache was never dropped.

| run | tier | KV stored | L1 chunks written DRAM / DAX | L2 stored / loaded | residency check | LMCache resident memory, anonymous / shared | page-cache growth | NVMe device read / written |
|---|---|---|---|---|---|---|---|---|
| `p0-dram-s` | DRAM L1 8 GiB | 2.99 GiB | 340 / 0 | – | – | 8.49 / 0.01 GiB | 0.00 GiB | 0.00 / 0.00 GiB |
| `p0-dax-v` | pure Device-DAX L1 8 GiB (`dax1.0`) | 2.99 GiB | 0 / 340 | – | 85 of 85 equal | 0.50 / 0.01 GiB | 0.00 GiB | 0.00 / 0.00 GiB |
| `p0-hyb2-v` | hybrid L1: 2 GiB DRAM + 4 GiB `dax1.0` + 4 GiB `dax0.0` | 7.42 GiB | 227 / 617 | – | 155 of 155 equal | 0.50 / 2.01 GiB | 0.01 GiB | 0.00 / 0.00 GiB |
| `p0-hyb-full2` | hybrid L1: 4 GiB DRAM + 269.5 + 242.5 GiB | 5.20 GiB | 455 / 137 | – | 35 of 35 equal | 0.50 / 4.01 GiB | 0.00 GiB | 0.00 / 0.00 GiB |
| `p0-hyb-full80` | hybrid L1: 80 GiB DRAM + 512 GiB (the main configuration) | 5.20 GiB | 592 / 0 | – | starts and serves; nothing overflows in a short run | 0.49 / 80.01 GiB | 0.02 GiB | 0.02 / 0.00 GiB |
| `p0-daxl2-v` | DRAM L1 8 GiB + DAX L2 8 + 8 GiB, `skip_l1` | 2.99 GiB | 340 / 0 | 2.99 / 10.30 GiB | 340 of 340 equal | 8.50 / 0.01 GiB | 0.33 GiB | 0.00 / 0.00 GiB |
| `p0-daxl2-full2` | DRAM L1 80 GiB + DAX L2 512 GiB, `skip_l1` | 5.20 GiB | 592 / 0 | 5.20 / 19.16 GiB | 592 of 592 equal | 80.50 / 0.01 GiB | 0.00 GiB | 0.00 / 0.00 GiB |
| `p0-ssd-v` | DRAM L1 8 GiB + Python `fs` L2, O_DIRECT, `skip_l1` | 2.99 GiB | 340 / 0 | 2.99 / 10.30 GiB | 0.00 % of file pages cached | 8.49 / 0.01 GiB | 0.00 GiB | 10.30 / 2.99 GiB |
| `p0-ssdn-v` | DRAM L1 8 GiB + `fs_native` L2, O_DIRECT, `skip_l1` | 2.99 GiB | 340 / 0 | 2.99 / 10.30 GiB | 0.00 % of file pages cached | 8.49 / 0.01 GiB | 0.00 GiB | 10.30 / 2.99 GiB |
| `p0-ssdn-buf` | the same with buffered I/O (**control**) | 2.99 GiB | 340 / 0 | 2.99 / 10.30 GiB | **100.00 % of file pages cached** | 8.49 / 0.01 GiB | 3.32 GiB | **0.00 / 0.00 GiB** |

### A.4 GPU memory: registered host memory is not free (`env/vram-registered.txt`, `env/vram-vllm.txt`, `env/vram/fit-hyb-b6400-*`)

Registering host memory with CUDA costs GPU memory — 8 bytes per 4 KiB page, i.e. **2.03 MiB of GPU memory per GiB registered**,
the same for pinned DRAM and for a Device-DAX mapping. Measured with the cache server alone (no vLLM): 146 MiB with an 8 GiB DRAM L1,
206 MiB with the first 40 GiB segment of a lazily grown DRAM L1, 290 MiB with an 80 GiB Device-DAX L1, 670 MiB with 269.5 GiB,
830 MiB with the hybrid of 80 GiB DRAM + 269.5 GiB, and 1,318 MiB with the full hybrid of 80 + 512 GiB; a DAX **L2** arena of 512 GiB
costs nothing (it is not registered). The server adds ≈ 540 MiB of GPU staging buffers once vLLM connects.

On an 8 GiB card this decides the configuration. vLLM with the 7,456-block KV pool of the previous study takes 6,536 MiB; the full
hybrid L1 beside it would need 8.4 GiB. The first attempt failed exactly there (`void/p0-hyb-full-*`: vLLM refused to start with
6.21 GiB free). **Every run of this study therefore uses a GPU KV pool of 6,400 blocks (102,400 tokens, 3.52 GiB)** — 14 % less than
the 7,456 blocks of 2026-11-10 — with which the full hybrid fits (7,894 of 8,188 MiB at the peak of a stress run with concurrent 16K
prompts). The pool is the same in all configurations, as the brief requires; the cost is charged to all of them although only the
registered-memory design causes it, which is stated again in the limitations. (`gpu_util=0.8` only lets vLLM's start-up check pass;
the block count is set explicitly.)

### A.5 The DRAM budget

| quantity | value | how it is enforced / measured |
|---|---|---|
| KV cache budget in DRAM | 80 GiB nominal in every LMCache configuration | `--l1-size-gb 80`: the L1 allocator never holds more |
| effective DRAM capacity | 64 GiB at the eviction trigger (LRU at 0.8), ≈ 51 GiB after an eviction round (it removes 20 %) — for the DRAM-only and the L2 configurations; **80 GiB in the hybrid L1**, whose watermark applies to the whole 592 GiB, so the DRAM part stays full | LMCache's `--eviction-trigger-watermark 0.8`, `--eviction-ratio 0.2` (defaults); occupancy from `/status` every 5 s |
| DRAM the cache server really holds | 80.5 GiB resident (80.0 GiB of L1 + 0.5 GiB of process) once the L1 is allocated — the L1 is pinned and registered whether or not it is full | `/proc/<pid>/status` at 1 Hz (`RssAnon` + `RssShmem`) |
| staging buffers | none on the host: the GPU copy reads the pinned L1 object; an L2 hit is loaded into an L1 object (inside the 80 GiB) | source inspection + the resident-memory series |
| page cache | 0 with O_DIRECT (checked per run: growth of `Cached − Shmem`) | `/proc/meminfo` at 1 Hz |
| metadata | Python dictionaries inside the 0.5 GiB of process memory at these sizes | resident memory |
| not in the budget | vLLM's own resident memory, the node's other processes, kernel page tables of the DAX mappings (2 MiB pages) | reported per run |

Physical isolation of 80 GiB (cgroup limit, memory hot-unplug) is not possible without root; the budget is the cache-level limit above,
verified by the resident memory of the cache server and by the absence of page-cache growth in every run (tables in C.4).

## B. Experiment matrix

Common to every run: c28; Qwen2.5-3B-Instruct-AWQ; vLLM 0.31.0 with `--num-gpu-blocks-override 6400` (102,400 tokens of GPU KV),
`--max-num-seqs 16`, `--max-model-len 32768`, FCFS scheduling (vLLM's default); LMCache 0.5.5 multi-process server, 256-token chunks,
LRU, eviction trigger 0.8, eviction ratio 0.2, one GPU transfer thread, `lmcache_driven` transfers, prefetch limit 8; **the
store-counter fix of 2026-11-10 in every LMCache configuration** (`KVADM_POLICY=storefix`: without it vLLM's connector stops storing
after hits that waited, 31–33 % of the stores under overload; stock behaviour is otherwise unchanged — no admission, bypass or
priority mechanism of that study is enabled); the logging-only instrumentation of `benchmarks/serving/kvtier/` (LMCache) and
`benchmarks/serving/kvadm/` (vLLM). The branch starts from `explore/gpu-kv-admission` because the fix lives there.

Configurations (names as used in tables and file names):

| name | LMCache server | DRAM for KV | extension | what it stands for |
|---|---|---|---|---|
| `none` | – (vLLM alone) | 0 | – | recompute-only: only vLLM's GPU prefix cache |
| `dram80` | L1 80 GiB pinned DRAM | 80 GiB | – | the DRAM-only budget |
| `hyb` | hybrid L1: 80 GiB DRAM + `dax1.0` 269.5 GiB + `dax0.0` 242.5 GiB, all registered with CUDA | 80 GiB | 512 GiB CXL, exclusive (unique capacity 592 GiB) | LMCache's CXL memory tier: CXL as more L1 |
| `daxl2` | L1 80 GiB DRAM + `dax` L2 adapter over the same two windows (58,254 slots of 9 MiB) | 80 GiB | 512 GiB CXL, inclusive (unique capacity 512 GiB) | CXL behind the software path of a storage tier: isolates the medium from the path |
| `ssdn` | L1 80 GiB DRAM + `fs_native` L2 on `/mnt/local` (NVMe), O_DIRECT, 4 I/O threads, `max_capacity_gb` 512 | 80 GiB | 512 GiB NVMe, inclusive (unique capacity 512 GiB) | the SSD baseline |
| `ssd` | L1 80 GiB DRAM + Python `fs` L2, O_DIRECT (no capacity limit) | 80 GiB | NVMe | LMCache's other file adapter (A, C, D only) |
| `dax` | pure Device-DAX L1 on `dax1.0` | 0 | 80 GiB CXL | Experiment A only |

L2 policies. In the single-request, equal-hit and concurrency experiments (A, C, D) the L2 tiers run with `--l2-store-policy skip_l1`
(a chunk leaves L1 once it is in the L2), which forces every host hit to be read from the L2 — the point of those experiments. In the
replays (B) they run with LMCache's defaults: write-through (`default`: every chunk is written to the L2 and stays in L1 until the L1's
LRU evicts it) and no promotion (`default` prefetch: a chunk loaded from the L2 is a temporary L1 object for that request).

| phase | runs | what was run | window / load | raw data |
|---|---|---|---|---|
| P0 path validation | 10 + 3 | short single-request runs with hashing (pure DAX, hybrid on one and two windows, DAX L2, both file adapters, buffered control); the full 512 GiB mapping with a 4 GiB and an 80 GiB DRAM part and as an L2 | 2K and 8K prompts, 2 repetitions | `P0/` |
| GPU memory | 8 + 3 + 1 | cache server alone at 8 registration sizes; vLLM alone at three pool settings; stress run of the full hybrid with 6,400 blocks | – | `env/` |
| A single-request retrieval | 10 | DRAM, pure DAX, hybrid, hybrid unregistered, DAX L2, `fs_native` (4 and 16 threads), Python `fs`, buffered control, vLLM alone | 6 prefix lengths × 5 repetitions (3 for vLLM alone) | `A/` |
| B0 functional replays | 3 | `hyb`, `ssdn`, `daxl2` scaled down (2 GiB DRAM, 8–16 GiB extension) so that both levels fill and evict | tool-agent trace seconds 0–20 at 0.08× (114 requests, 34 GiB of KV) | `B0/` |
| C equal-hit comparison | 6 | DRAM, hybrid (pool on CXL), DAX L2, `fs_native`, Python `fs`, vLLM alone | 48 pre-populated prefixes (2K–16K), Poisson arrivals at 0.5 / 2 / 4 / 8 req/s, two passes each | `C/` |
| D concurrent retrieval | 6 | DRAM, hybrid, DAX L2, `fs_native` (4 threads; 16 threads with 16 prefetches in flight), Python `fs` | k = 1, 2, 4, 8, 16 simultaneous hits of 4K and 8K prefixes, 4 bursts each | `D/` |
| B end-to-end replays | PENDING-COUNT | per window (✓ = run): see the table below | conversation and tool-agent traces: seconds 0–400 at 0.08× (high load) and 0–200 at 0.04× (half that rate), 5,000 wall-seconds each; conversation 0–900 at 0.08× (long window, 11,250 s: the extensions fill and evict); conversation 0–400 at 0.16× (sustained overload, arrivals in 2,500 s) | `B/` |
| E traffic | – | from the B runs: per-second KV bytes read / written per medium, copy intervals, overlap | – | `B/*-traffic.csv`, `B/tables-e.md` |
| trace model | – | offline LRU over the replayed and longer windows at the capacities of the study (**not a measurement**) | 0–200 s … 0–3,600 s | `trace-model/` |

Replays of Experiment B, by window and configuration (every completed configuration; one run per cell):

| window | `none` | `dram80` | `hyb` | `daxl2` | `ssdn` | sensitivity |
|---|---|---|---|---|---|---|
| conversation 0–400 s, 0.08× (`conv08`) | ✓ | ✓ | ✓ | ✓ | ✓ | PENDING-SENS-CELLS |
| tool-agent 0–400 s, 0.08× (`tool08`) | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| conversation 0–200 s, 0.04× (`conv04`) | – | ✓ | ✓ | – | ✓ | – |
| tool-agent 0–200 s, 0.04× (`tool04`) | – | ✓ | ✓ | – | ✓ | – |
| conversation 0–900 s, 0.08× (`conv08L`) | – | ✓ | ✓ | PENDING-DAXL2-CELL | ✓ | – |
| conversation 0–400 s, 0.16× (`conv16r`) ¹ | – | ✓ | ✓ | – | ✓ | – |

¹ With LMCache `--l1-read-ttl-seconds 7200` and vLLM `kv_load_failure_policy=recompute` in all three configurations (C.4.5);
every other run of the study uses the defaults (300 s; `fail`). The cells marked – were planned at lower priority and not
run before the node's allocation ended (2026-11-14 19:53); `plan.txt` and `done.txt` in the results directory are the queue's
own record, `experiment-matrix.md` lists all runs with their settings, request counts, errors and use.

Void runs (kept, not used): the two sustained-overload replays with default settings (`void/b-conv16-dram80-*`,
`void/b-conv16-hyb-*`, 2026-11-14 02:49–04:15), in which vLLM's engine died 910 s into the replay (243 of 1,177 requests
completed; diagnosis in C.4.5); the first attempt at the full hybrid with 7,456 GPU blocks and the nine A runs queued behind it, which ran
against its left-over cache server (`void/`, 2026-11-12 15:28–15:32); the smoke runs of the first hour (`P0/p0-*-s`), whose residency
checks were made after later runs had overwritten the devices and were therefore repeated (`P0/p0-*-v`).

## C. Detailed results

### C.1 Experiment A — single-request retrieval cost (`A/tables-a.md`, `A/a-summary.csv`; figures A1–A4)

**Why.** The brief's Q3: what does a hit cost when the prefix comes from the GPU, DRAM, CXL or NVMe, and how does that compare with
recomputing it? The 2026-11-04 study measured DRAM and a Python file tier; CXL was blocked then.

**How.** `run_a.py`, one server configuration per run, idle server, one request at a time. For each prefix length (512 … 16,384
tokens, 5 repetitions, fresh pseudo-random prompts): the prompt once (**recompute**; LMCache stores its KV), wait until LMCache's
store controller is idle, the prompt again (**GPU prefix-cache hit**), eight 16,320-token fillers that push it out of the GPU's
6,400-block pool, the prompt a third time (**host-tier hit**). Tiers: DRAM L1 (80 GiB); pure Device-DAX L1 (80 GiB of `dax1.0`);
hybrid L1 with a 4 GiB DRAM part that the fillers occupy, so that every measured prompt is on CXL (checked per request: all of its
chunks carry LMCache's `devdax` medium); the same hybrid without CUDA registration of the DAX arenas; DAX L2 and the two NVMe file
adapters with `skip_l1`, which removes a chunk from L1 once it is in the L2, so that every host hit is read from the L2; the buffered
control; vLLM alone. Every part of the time line comes from records of the request itself: client (send, first token), vLLM hook
(queued, scheduled, first token), LMCache events (lookup, L2 load task, retrieve), the transfer's phase samples (host-to-GPU staging
copies; the GPU kernels that install the staged bytes in vLLM's KV blocks).

**Result.** TTFT of a host-tier hit, median of 5 (ms):

| source of the prefix | 512 | 1K | 2K | 4K | 8K | 16K | bytes moved at 16K |
|---|---|---|---|---|---|---|---|
| GPU prefix cache (vLLM alone) | 20 | 20 | 21 | 22 | 25 | 39 | – |
| GPU prefix cache (with LMCache, L1 tiers) | 28 | 29 | 31 | 32 | 36 | 44 | 9 MiB (the last chunk) |
| **DRAM L1** | 30 | 33 | 36 | 45 | 60 | **94** | 576 MiB |
| **CXL, pure Device-DAX L1** | 30 | 33 | 36 | 45 | 61 | **94** | 576 MiB |
| **CXL, hybrid L1 (chunks on Device-DAX)** | 30 | 33 | 36 | 45 | 60 | **93** | 576 MiB |
| CXL, hybrid L1, arenas not registered with CUDA | 32 | 33 | 38 | 45 | 62 | 96 | 576 MiB |
| **CXL, DAX L2 adapter** | 33 | 36 | 41 | 51 | 72 | **114** | 576 MiB CXL → DRAM, 576 MiB DRAM → GPU |
| **NVMe, `fs_native` L2, O_DIRECT, 4 I/O threads** | 37 | 47 | 62 | 95 | 160 | **290** | 576 MiB NVMe → DRAM, 576 MiB DRAM → GPU |
| NVMe, `fs_native`, 16 I/O threads | 38 | 46 | 63 | 98 | 164 | 296 | |
| NVMe, Python `fs` L2, O_DIRECT | 38 | 47 | 65 | 101 | 171 | 315 | |
| *file L2 with buffered I/O (control: the page cache answers)* | *33* | *35* | *40* | *50* | *71* | *113* | *no device read* |
| recompute (first occurrence, LMCache storing) | 81 | 154 | 309 | 647 | 1,424 | 3,385 | – |
| recompute (vLLM alone) | 78 | 151 | 306 | 642 | 1,413 | 3,366 | – |

Where the time of a 16K hit goes (ms; "other" = HTTP, tokenizer, queue hand-overs, scheduler steps):

| tier | lookup + media read | of which L2 load (GiB/s) | GPU transfer | of which staging copy (GiB/s) | KV install | prefill of the last token | other | LMCache CPU time |
|---|---|---|---|---|---|---|---|---|
| DRAM L1 | 1.2 | – | 50.3 | 45.3 (12.4) | 4.5 | 21.8 | 20.2 | 4.9 |
| CXL hybrid L1 | 1.2 | – | 50.4 | 45.3 (12.4) | 4.4 | 22.2 | 19.3 | 5.3 |
| CXL hybrid L1, not registered | 2.6 | – | 51.2 | 45.9 (12.3) | 4.4 | 22.2 | 20.0 | 56.4 |
| CXL DAX L2 | 20.1 | 17.4 (32.4) | 50.7 | 45.3 (12.4) | 4.4 | 22.2 | 20.9 | 138.7 |
| NVMe `fs_native` | 197.1 | 193.8 (2.90) | 50.6 | 45.3 (12.4) | 4.4 | 22.3 | 20.4 | 29.6 |
| NVMe Python `fs` | 221.8 | 215.4 (2.61) | 50.6 | 45.3 (12.4) | 4.4 | 21.7 | 21.2 | 36.8 |

**Explanation.**

1. *A hit on CXL memory costs what a hit on DRAM costs.* With the L1 object on Device-DAX the GPU's staging copy reads the CXL
   mapping at the same 12.4 GiB/s as pinned DRAM — the PCIe 4.0 ×8 link of the GPU is the limit, not the memory behind it — and
   nothing else in the request touches the KV. The two are within 1 ms at every length (93–94 ms at 16K). CXL's higher access latency
   and lower bandwidth (≈ 46 GiB/s for the pair against > 140 GiB/s for DRAM, earlier measurements) are invisible behind a 12.4 GiB/s
   consumer.
2. *The medium only matters when the path adds a copy.* As an L2, the same CXL memory costs one `memmove` into a DRAM L1 object before
   the GPU copy: 17.4 ms for 576 MiB with four load workers (32 GiB/s for the four workers together; a two-chunk load runs at 20 GiB/s), 20 ms more TTFT at 16K (+22 %) and 139 ms of CPU time per hit instead of 5. The NVMe pays the same extra step at
   2.9 GiB/s — a flat rate from 512 to 16K tokens, unchanged with 16 I/O threads, i.e. the device on its ×2 link — which is 194 ms at
   16K, two thirds of the request. Everything after the media read is identical in all tiers (GPU transfer 50.3–51.2 ms, install
   4.4 ms, last token 22 ms).
3. *Every tier beats recomputation at every length*, and the gap grows with the prefix because prefill is superlinear on this GPU
   (3.4 s at 16K): CXL L1 2.7× (512) to 36× (16K), CXL L2 2.5× to 30×, NVMe 2.2× to 11.6×.
4. *CUDA registration of the CXL arena buys almost no latency.* Without it the copy takes the driver's pageable path at 12.3 GiB/s:
   +1–3 ms per hit (≤ 3 %). What it costs instead is CPU: 56 ms of CPU time per 16K hit instead of 5, and on the store side one core
   is busy for the whole prefill of a new prompt (3,399 ms of CPU time during a 3,385 ms request). Registration, on the other hand,
   costs 1 GiB of GPU memory for the 512 GiB (A.4). On this card that is a real trade-off; the run is `a-hyb-nopin`.
5. *An L2 tier taxes GPU-prefix hits too.* LMCache's lookup loads every chunk it finds in the L2 before it answers, whether or not
   vLLM will need it. When the GPU still holds the prefix, vLLM uses one chunk of the 64 — but with the chunks only in the L2 the
   request has already waited for the whole read: 242 ms on NVMe at 16K against 44 ms with an L1 tier (68 ms with the DAX L2). This is
   the in-lookup prefetch the 2026-11-04 study listed as a generic tiering issue; here it is measured per medium. (With the default
   write-through policy the chunks are also in L1 as long as the L1 keeps them, so the tax applies to chunks the L1 has evicted.)
6. *Buffered file I/O would have looked like CXL.* The control run reads 576 MiB "from the file tier" at 32.9 GiB/s and returns a 16K
   hit in 113 ms — the page cache, i.e. DRAM outside the 80 GiB budget. The O_DIRECT runs are the NVMe numbers.
7. LMCache's presence costs a first occurrence about 1 % (3,385 against 3,366 ms at 16K: the KV is copied to the host during the prefill).
8. *The store direction is where the CXL path is slower — by 3.1×, and only when the arena is registered with CUDA.* Rate of the
   GPU's staging copies, each a 9 MiB chunk, timed by the transfer thread itself (all copies of the run; idle server):

   | run | host memory of the L1 object | GPU → host GiB/s, median (p10–p90) | host → GPU GiB/s, median |
   |---|---|---|---|
   | `a-dram` | pinned DRAM | 12.14 (12.07–12.20) | 12.43 |
   | `a-dax` | Device-DAX, registered with CUDA | **3.89 (3.85–3.90)** | 12.42 |
   | `a-hyb` | hybrid: the chunks that landed on Device-DAX / on DRAM | 3.89 / 12.18 (two modes) | 12.42 |
   | `a-hyb-nopin` | Device-DAX, not registered (driver's pageable path, CPU copy) | 11.48 (11.02–12.18) | 12.42 |

   The GPU reads CXL memory at the full rate of its link and writes it at 3.9 GiB/s; the same 3.85–3.90 GiB/s appears in every
   path-validation run and in the replays (C.4). Through the unregistered path — GPU → the driver's DRAM buffer → CPU copy into the
   DAX mapping — the same store runs at 11.5 GiB/s, so the limit is the device-initiated (DMA) write into the CXL window, not the
   CXL memory's write bandwidth as the CPU sees it. The cause below that level was not isolated in this study (no micro-benchmark
   of DMA writes was run). Its cost in serving is small because stores are paced by the prefill that produces them: a 16K first
   occurrence is 10 ms slower with the L1 object on CXL (3,395 against 3,385 ms, +0.3 %) although its 64 chunk copies take 100 ms
   longer in total — the copies run on the transfer thread behind the prefill, not in front of the first token.

![figA1-ttft-vs-prefix](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figA1-ttft-vs-prefix.png)
![figA2-retrieval-vs-prefix](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figA2-retrieval-vs-prefix.png)
![figA3-breakdown](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figA3-breakdown.png)
![figA4-bandwidth](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figA4-bandwidth.png)

### C.2 Experiment C — equal-hit comparison (`C/tables-c.md`, `C/c-summary.csv`; figures C1–C3)

**Why.** In an online replay a faster tier and a slower tier end up with different cache contents and different queues, so their
aggregate hit rates cannot be compared directly. Here every tier serves identical hits; whatever differs is the medium and its path.

**How.** `run_eqhit.py`. 48 prefixes (12 each of 2K, 4K, 8K and 16K tokens; 368,640 tokens = 12.7 GiB of KV) are stored by cold
requests; the driver waits until LMCache's store controller is idle. Then, for each offered rate (0.5, 2, 4, 8 requests/s, Poisson,
seeded — the same arrival instants in every tier) and two passes per rate: flush the GPU prefix cache with eight 16,320-token fillers,
then send one request per prefix in a seeded order = the prefix + 64 fresh tokens, 64 output tokens. A prefix is used once per pass,
so a hit can only come from the host tier. Tiers as in Experiment A (the hybrid with a 4 GiB DRAM part that the fillers occupy;
`skip_l1` for the L2 tiers); vLLM alone at 0.5 and 2 requests/s as the recompute reference.

*Equality, checked per run:* 96 requests per rate in every tier; 737,280 cached tokens and 25,920 MiB retrieved per rate in every
tier (identical); no request with a GPU-prefix hit; the 2,880 retrieved chunks are DRAM L1 objects in the DRAM run, Device-DAX L1
objects in the hybrid run (0 on DRAM), and L2 loads in the three L2 runs (0 served from L1); no request failed.

**Result** (TTFT in ms; completed requests/s over the pass). The "lookup interval" runs from vLLM's lookup request to the poll of
vLLM that finds the prefetch complete (`mp.lookup_prefetch.start` → `.end`; the end event is published by
`query_prefetch_status`, i.e. by the poll): it contains the L2 load **and** the wait until vLLM asks again.

| tier | 0.5 req/s: TTFT p50 / p95 | 2 req/s | 4 req/s | 8 req/s (saturated) | lookup interval p50 at 0.5 / 2 / 4 / 8 | lookup interval p95 at 8 | completed req/s at 8 |
|---|---|---|---|---|---|---|---|
| DRAM L1 | 105 / 195 | 146 / 268 | 234 / 655 | 1,376 / 3,323 | 1.8 / 10.3 / 14.7 / 15.8 | 56 | 5.23 |
| **CXL hybrid L1** | **104 / 193** | **147 / 285** | **232 / 641** | **1,375 / 3,322** | 2.0 / 10.4 / 14.7 / 16.5 | 55 | 5.21 |
| **CXL DAX L2** | **110 / 215** | **150 / 320** | **238 / 611** | **1,280 / 3,247** | 11.1 / 11.7 / 16.0 / 84.7 | 1,548 | 5.27 |
| **NVMe `fs_native`** | **162 / 393** | **250 / 485** | **400 / 854** | **1,690 / 3,604** | 98.4 / 103.4 / 117.4 / 575.9 | 1,290 | 5.00 |
| NVMe Python `fs` | 175 / 421 | 255 / 608 | 400 / 873 | 1,656 / 3,299 | 108.8 / 108.7 / 134.2 / 736.8 | 1,716 | 4.99 |
| recompute (vLLM alone) | 9,221 / 15,883 | 37,162 / 62,300 | – | – | – | – | 0.59 at an offered 2 |

Mean TTFT at 0.5 / 2 / 4 / 8 req/s: DRAM 95 / 160 / 288 / 1,386 ms; CXL hybrid 94 / 160 / 285 / 1,391; CXL L2 105 / 168 / 284 /
1,366; NVMe 192 / 271 / 411 / 1,685. Request time p50 at 0.5 / 2 / 4 / 8: DRAM 718 / 892 / 1,388 / 3,138 ms; NVMe 788 / 1,016 /
1,581 / 3,579 ms. GPU transfer p50 is the same in every tier (30 / 45 / 52 / 41 ms).

The lookup interval of the L2 tiers in its three parts, p50 / p95 in ms (96 requests per rate): before the load starts (L2 key lookup,
waiting for one of the 8 prefetch slots) | the load tasks | from the end of the load to the poll that collects it:

| tier | 0.5 req/s | 2 req/s | 4 req/s | 8 req/s |
|---|---|---|---|---|
| CXL DAX L2 | 1.1 / 1.7 \| 8.8 / 17.6 \| 1.4 / 10.1 | 1.0 / 1.7 \| 8.8 / 17.7 \| 6.2 / 28.0 | 1.0 / 2.0 \| 8.8 / 18.6 \| 9.4 / 50.4 | 1.9 / 49.8 \| 21.9 / 56.2 \| 47.7 / 1,463 |
| NVMe `fs_native` | 1.0 / 1.9 \| 96.7 / 194.6 \| 1.5 / 13.7 | 1.2 / 118.6 \| 96.8 / 198.7 \| 8.3 / 22.4 | 1.7 / 145.5 \| 96.8 / 198.6 \| 14.6 / 83.6 | 83.9 / 308.9 \| 202.0 / 489.5 \| 235.8 / 966.4 |
| NVMe Python `fs` | 2.2 / 4.0 \| 105.6 / 214.9 \| 1.4 / 18.4 | 2.1 / 4.4 \| 105.7 / 326.4 \| 7.2 / 31.3 | 2.4 / 4.6 \| 110.3 / 300.7 \| 16.5 / 60.9 | 6.3 / 17.5 \| 300.5 / 825.8 \| 229.5 / 1,063 |

**Explanation.**

1. *CXL as registered L1 memory is indistinguishable from DRAM under load as well*: every TTFT quantile, the request time and the
   throughput agree within 1–2 % at all four rates. Nothing in the path touches the medium except the GPU's 12.4 GiB/s copy.
2. *NVMe costs its media read on every hit, and the cost does not shrink in relative terms until the GPU saturates.* With equal
   hits the NVMe tier's TTFT p50 is 55 % above DRAM at 0.5 req/s, 71 % at 2 req/s and 71 % at 4 req/s (162 / 250 / 400 ms against
   105 / 146 / 234 ms); the whole difference is the L2 load (97 ms median for this mix of prefixes, the same at the three rates; the
   lookup interval of the L1 tiers is 1.8–15 ms). Mean TTFT doubles at low load (192 against 95 ms).
3. *As an L2, CXL stays within 5 % of DRAM* (+5 ms at 0.5 req/s, +3–4 ms at 2 and 4 req/s): the `memmove` into DRAM takes 8.8 ms
   where the NVMe read takes 97 ms. The medium is worth an 11× faster media read; the path (an L2 at all) costs the 8.8 ms.
4. *At saturation the GPU decides, and the tiers converge.* At an offered 8 req/s the server completes 5.0–5.3 requests/s in every
   cached configuration: the bound is the decode of 64 tokens per request and the GPU KV pool, not retrieval. TTFT is then mostly
   queueing (p50 1.3–1.7 s). NVMe still loses 4 % of throughput (5.00 against 5.23 req/s) and 23 % of TTFT p50: its lookup interval
   p50 rises from 98 to 576 ms — 84 ms before the load starts (the 8 prefetch slots are taken), 202 ms in the load itself (97 ms at
   low load; concurrent loads share the device's 2.9 GiB/s) and 236 ms until vLLM collects the result.
5. *The L2 path has a tail the L1 path does not have, and the tail belongs to the path, not to the medium.* At 8 req/s the lookup
   interval p95 is 1.5 s for the DAX L2 and 1.3–1.7 s for NVMe against 55 ms for the L1 tiers. For the DAX L2 the load itself is
   still 22 ms p50 / 56 ms p95; the rest (48 ms p50, 1.46 s p95) lies between the end of the load and the poll that collects it. An
   L1 hit is complete when vLLM first asks; an L2 hit is loaded asynchronously and is picked up at a later poll, and with a saturated
   engine the later poll is up to 1–1.5 s away. NVMe pays the same wait (236 ms p50, 966 ms p95) on top of its slower load. (The
   bursts of Experiment D, sent to an otherwise idle engine, do not show this wait: there the poll follows the load within 2–9 ms and
   what grows is the queueing for prefetch slots and load workers inside LMCache.)
6. *Recompute is not a competitor at these prefix lengths.* Without a host tier the same sequence overloads the GPU already at
   0.5 req/s (TTFT p50 9.2 s; 0.59 requests/s is all it completes at an offered 2 req/s, TTFT p50 37 s): 88× the DRAM / CXL TTFT at 0.5 req/s and
   250× at 2 req/s, and one ninth of the saturated throughput of any cached configuration.

![figC1-ttft-vs-rate](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figC1-ttft-vs-rate.png)
![figC2-throughput-vs-rate](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figC2-throughput-vs-rate.png)
![figC3-parts-vs-rate](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figC3-parts-vs-rate.png)

### C.3 Experiment D — concurrent retrieval (`D/tables-d.md`, `D/d-summary.csv`; figures D1–D3)

**Why.** One hit at a time hides what limits many hits at once: the medium's bandwidth, LMCache's worker pools, the GPU link, the
CPU copies, or vLLM. The brief asks which, and warns against blaming the storage device by default.

**How.** `run_e.py`, scenario e1. A pool of 16 prefixes each of 4,096 and 8,192 tokens is stored in the tier; for k = 1, 2, 4, 8, 16
and four bursts per point: flush the GPU prefix cache, then send k requests at the same instant, each hitting a different prefix (4
output tokens). Per request: the lookup (with the L2 load), the wait between the end of its lookup and the start of its GPU
transfer, the GPU transfer; per burst: retrieved bytes over the time from the first lookup start to the last KV on the GPU
("aggregate"), L2 bytes over the union of the L2 load intervals ("media"), staged bytes over staging time ("H2D"). Tiers as in A and C,
plus `fs_native` with 16 I/O threads and 16 prefetch requests in flight (LMCache's defaults are 4 and 8). All 1,488 measured requests
completed; every chunk came from the intended medium (per-request medium letters / L2 load tasks).

**Result**, 8,192-token prefixes (288 MiB per request; medians over the bursts' requests):

| tier | TTFT p50 (ms) at k = 1 / 2 / 4 / 8 / 16 | TTFT max at 16 | lookup + media p50 at 1 / 4 / 16 | lookup end → transfer start p50 at 1 / 4 / 16 | aggregate GiB/s at 1 / 4 / 16 | media GiB/s at 1 / 16 |
|---|---|---|---|---|---|---|
| DRAM L1 | 52 / 101 / 158 / 255 / 430 | 721 | 1.2 / 2.4 / 6.5 | 2.5 / 61 / 302 | 9.7 / 7.8 / 7.0 | – |
| **CXL hybrid L1** | **52 / 103 / 159 / 258 / 428** | 712 | 1.2 / 2.6 / 6.9 | 2.3 / 63 / 296 | 9.7 / 7.8 / 7.0 | – |
| **CXL DAX L2** | **62 / 120 / 185 / 277 / 453** | 734 | 11.5 / 37.6 / 93.7 | 2.9 / 53 / 219 | 7.0 / 6.5 / 6.8 | 31.8 / 29.9 |
| **NVMe `fs_native`, 4 threads** | **150 / 247 / 350 / 547 / 940** | 1,614 | 99 / 294 / 861 | 2.6 / 2.4 / 2.6 | 2.2 / 2.7 / 2.9 | 2.91 / 2.91 |
| NVMe `fs_native`, 16 threads, 16 prefetches | 153 / 254 / 365 / 604 / 999 | 1,649 | 102 / 308 / 922 | 2.6 / 2.5 / 2.7 | 2.2 / 2.6 / 2.8 | 2.84 / 2.91 |
| NVMe Python `fs` | 161 / 297 / 547 / 997 / 1,540 | 1,882 | 111 / 394 / 1,461 | 2.4 / 57 / 84 | 2.0 / 2.1 / 2.5 | 2.66 / 2.91 |

The 4,096-token prefixes give the same picture at half the size (TTFT p50 at k = 16: DRAM 264 ms, CXL hybrid 259, CXL L2 277, NVMe
513 / 537 / 761). The host-to-GPU staging rate is 12.4 GiB/s in every cell of every tier.

**Explanation — where the bottleneck is, tier by tier.**

1. *DRAM and CXL L1: the GPU transfer path.* The lookup stays in the millisecond range at any k; what grows is the wait between a
   request's lookup and its transfer (2.5 → 302 ms at k = 16) — LMCache runs the transfers of one engine one after the other on a
   single thread, each 25–40 ms for 288 MiB, so k hits queue for it. The aggregate rate is 7.0–9.7 GiB/s, below the link's
   12.4 GiB/s only by the per-transfer overheads and by the GPU's concurrent decode steps. **CXL and DRAM are the same in every
   column**: the pair's bandwidth (≈ 46 GiB/s) is 3.7× what one GPU link can draw, so the medium never queues.
2. *CXL as an L2: LMCache's load path, not the medium.* The media copies run at 30–32 GiB/s whatever the concurrency (four load
   workers), still 2.4× the GPU link. The lookup interval nevertheless grows to 94 ms p50 at k = 16 (9 ms before the load starts,
   65 ms in the load tasks, 9 ms until vLLM collects the result), because the loads of many requests share the four workers and at
   most eight prefetch requests are in flight; the price is +18–20 % TTFT at k = 1–4 and +5 % at k = 16, where
   the transfer queue dominates again. The slowdown of this configuration is software path and CPU copy; the device has headroom.
3. *NVMe: the device.* The media rate is 2.91 GiB/s from k = 1 to k = 16 — flat, 4× below the GPU link — and the aggregate
   retrieval rate equals it (2.2 → 2.9 GiB/s): the read is the bottleneck (lookup interval 861 ms p50 at k = 16: 378 ms waiting for
   a prefetch slot, 300 ms in the load, 2 ms until collected), the transfer thread waits for data (lookup end →
   transfer start stays at 2.5 ms; the GPU transfer never queues). TTFT is 2.2–2.9× DRAM at every k (940 against 430 ms at k = 16,
   1.6 s against 0.72 s for the slowest request). More I/O threads and more prefetch slots change nothing in the aggregate and make
   the median slightly worse (more loads share the same 2.9 GiB/s, each takes longer: 860 against 300 ms per load at k = 16); the
   Python adapter, which does not bound its concurrent reads, is 64 % worse than `fs_native` at k = 16 for the same reason. This is
   the case where attributing the slowdown to the storage device is correct — with the caveat that the device runs on a ×2 link.
4. *vLLM is not the limit in any tier here*: the scheduler admits a request 4–30 ms after its KV has arrived (queued → scheduled
   tracks the retrieval latency), and k = 16 × 8K (131K tokens) exceeds the 102K-token pool only momentarily because requests finish
   after 4 tokens.

![figD1-throughput-vs-k](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figD1-throughput-vs-k.png)
![figD2-latency-vs-k](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figD2-latency-vs-k.png)
![figD3-ttft-vs-k](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figD3-ttft-vs-k.png)

### C.4 Experiment B — end-to-end cache expansion (`B/tables-b.md`, `B/tier-summary.csv`; figures B1–B5)

**Why.** The brief's Q1 and Q2: with the DRAM KV budget fixed at 80 GiB, what does an extension of 512 GiB buy end to end, and is it
the same whether the extension is CXL memory or an NVMe file tier? Experiments A, C and D compared the tiers on identical hits; here
each configuration builds its own cache content online, under a trace.

**How.** `replay.py` replays a window of a Mooncake trace open-loop: every request is sent at its trace time divided by the time
scale (0.08× = 12.5 wall-seconds per trace second; requests that share one of the trace's quantised timestamps are spread over that
trace second), whatever happened to earlier requests, with its prompt of the recorded length built from the trace's 512-token block
hashes (two requests share a prefix exactly where the trace says they do; prompts are cut to the model's 32,768-token context) and
the trace's output length, capped at 1,024 tokens. The same window, the same prompts and the same arrival instants go to every
configuration. Windows:

| name | trace, seconds | time scale | wall time | requests | prompt tokens ¹ | KV of all prompts | distinct KV stored ² |
|---|---|---|---|---|---|---|---|
| `conv08` | conversation, 0–400 | 0.08× | 5,000 s | 1,177 | 13.46 M | 462 GiB | 359.6 GiB |
| `tool08` | tool-agent, 0–400 | 0.08× | 5,000 s | 2,332 | 19.42 M | 667 GiB | 340.9 GiB |
| `conv04` | conversation, 0–200 | 0.04× | 5,000 s | 599 | 6.88 M | 236 GiB | 197.6 GiB |
| `tool04` | tool-agent, 0–200 | 0.04× | 5,000 s | 1,159 | 9.79 M | 336 GiB | 188.7 GiB |
| `conv08L` | conversation, 0–900 (long window) | 0.08× | 11,250 s | 2,728 | 30.54 M | 1,048 GiB | 734.9 GiB |
| `conv16r` | conversation, 0–400 (the requests of `conv08`) | 0.16× | 2,500 s of arrivals | 1,177 | 13.46 M | 462 GiB | 359.6 GiB |

¹ As counted by vLLM (the trace's token counts plus the chat template, ≈ 55 tokens per request; the offline model of C.6 counts
the trace's own 13.39 / 19.36 / 6.85 / 9.76 / 30.38 M). ² Distinct 256-token chunks that LMCache stored in the run × 9 MiB — the
"total unique KV footprint" of the window; the same in every configuration of a window within 0.1 GiB. The offline model, which
counts 512-token trace blocks, gives 350 / 335 / 192 / 185 / 712 GiB.

0.04× and 0.08× are the two rates of the 2026-11-04 and 2026-11-11 studies. What they mean on this GPU is measured, not assumed:
the table of each window gives the share of time the GPU was running a step and the largest backlog. At 0.08× the GPU is busy
81–88 % of the time and every configuration completes every request, so this is a high but sustainable load, with bursts that
queue for tens of seconds; 0.04× is half that rate. Neither is a sustained overload, in which completed work per second could
depend on the cache — the 0.16× round was added for that (the same 400 trace seconds in half the wall time; it runs with two
settings the other rounds do not need, C.4.5). Every window starts with an
empty cache: the first minutes of every run are a cold start, and they are part of every number below.

*Definitions.* **Cached share** = prompt tokens that were not computed ÷ all prompt tokens of the window (one denominator for every
column): vLLM's own count of cached tokens per request, split by where they came from — **GPU prefix** (vLLM's block pool still held
them; no bytes moved), **DRAM** (retrieved from L1 objects in DRAM), **CXL L1** (retrieved from L1 objects on Device-DAX), **L2**
(retrieved from chunks that the lookup of this request loaded from the L2: DAX slots or NVMe files). The medium of every retrieved
chunk is taken from LMCache's own record of the object at the moment it reserved it for reading. **Recomputed** = the rest.
**TTFT** is client-side (send → first token), **request time** send → last token. **Throughput**: completed requests/s and output
tokens/s over the window from the first send to the last completion — in an open-loop replay that completes every request these are
set by the trace, so the table also gives the prompt tokens the GPU actually computed per second and the share of time it was busy.
**L2 prefetch** = `l2.prefetch.lookup.submitted` → `l2.prefetch.load.completed` inside the cache server, joined to the request's
lookup (C.2 explains why the lookup interval itself is not a retrieval time under load).

*Memory-budget accounting, per run:* the largest resident set of the cache server (anonymous + shared memory), of vLLM, the minimum
of `MemAvailable`, the growth of the page cache, bytes read from / written to the NVMe device (`/proc/diskstats`), all sampled at
1 Hz by the hook inside the cache server.

*Validity checks, per run:* every request answered with HTTP 200, without an error and with at least one output token (status 200
alone is not enough: a stream that was open when the engine died keeps its 200, C.4.5); no error line in the logs of vLLM or LMCache; for the L2 tiers, the
join of prefetches to lookups is consistent (`prefix_hit_count` × 256 = the lookup's `l2_hit_tokens`) for every request; outputs of
the same request compared across configurations (`check_outputs.py`).

#### C.4.1 Conversation trace, 0–400 s at 0.08× (high load) — DRAM only vs. CXL vs. NVMe

Runs `b-conv08-dram80`, `b-conv08-hyb`, `b-conv08-ssdn` (2026-11-12, 5,007 s each, 1,177 requests, 13.46 M prompt tokens; all
requests HTTP 200, no error line in either log).

| configuration | cached share | GPU prefix | DRAM | CXL L1 | L2 (NVMe) | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed prompt tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only, 80 GiB | 0.096 | 0.045 | 0.051 | – | – | 12.17 | 16.71 | 61.94 | 82.90 | 22.42 | 33.87 | 92.14 | 0.235 | 80 | 2,430 | 0.88 | 34 |
| 80 GiB DRAM + 512 GiB CXL (hybrid L1) | **0.238** | 0.045 | 0.078 | 0.116 | – | 10.25 | **8.67** | 41.89 | 56.48 | 13.32 | 24.02 | 68.32 | 0.235 | 80 | 2,047 | 0.81 | 25 |
| 80 GiB DRAM + 512 GiB NVMe (`fs_native` L2) | **0.238** | 0.045 | 0.045 | – | 0.149 | 10.25 | **8.62** | 41.81 | 55.98 | 13.25 | 23.86 | 67.91 | 0.235 | 80 | 2,047 | 0.81 | 25 |

Offline model of the same window (C.6): 0.132 at 80 GiB (0.101 at the 64 GiB at which the DRAM tier starts to evict), 0.239 at
≥ 320 GiB.

Cache and memory budget:

| configuration | L1 max GiB | L2 max GiB | evicted from L1 GiB | evicted from the extension | written to DRAM / CXL / NVMe GiB | read back from DRAM+CXL L1 / CXL / NVMe GiB | cache server RSS max GiB | page-cache growth GiB | NVMe device read / written GiB | cache server CPU s |
|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only | 64.1 of 80 | – | 370.7 | – | 425.5 / – / – | 23.5 / – / – | 81.0 | 0.21 | 0.0 / 0.2 | 51 |
| DRAM + CXL | 359.6 of 592 (80.0 DRAM + 279.6 CXL) | – | 0 | 0 | 80.0 / 279.6 / – | 89.5 / 53.4 / – | 81.0 (80.0 of it shared memory) | 0.48 | 0.0 / 0.2 | 56 |
| DRAM + NVMe | 64.1 of 80 | 359.5 of 512 | 375.2 | 0 | 359.6 / – / 359.5 | 89.5 / – / 68.7 | 81.0 | 0.18 | 68.7 / 360.4 | 61 |

**Result 1 — the two extensions retain the same KV and remove the same recomputation.** Both keep every chunk the window
produces (359.6 GiB; neither evicts anything from the extension), both find the same 7,627 chunks again, and both recompute
exactly 10,248,620 prompt tokens — 1.92 M (15.8 %) fewer than DRAM alone. The cached share goes from 0.096 to 0.238 in both, on
the offline model's value for unlimited capacity (0.239). The DRAM-only tier holds 51–64 GiB at a time and evicts 370.7 GiB over
the run: it writes 425.5 GiB to keep 9.6 % of the prompt tokens from being computed.

**Result 2 — TTFT halves with either extension, and the two extensions are within 1 % of each other.** p50 16.7 → 8.7 / 8.6 s,
p95 61.9 → 41.9 / 41.8 s, mean 22.4 → 13.3 / 13.3 s. Paired per request (the same request of the trace in two runs): CXL − DRAM
only: mean −9.10 s, median −2.47 s, 76 % of requests faster; NVMe − DRAM only: −9.17 s, −2.53 s, 79 %; **CXL − NVMe: mean
+0.07 s, median +0.01 s** — the NVMe configuration is the faster one by half a percent.

**Result 3 — throughput is unchanged.** 0.235 requests/s and 80 output tokens/s in all three: the replay is open-loop and every
configuration completes every request, so completed work per second is set by the trace. What changes is how much the GPU has
to do for it: 2,430 → 2,047 computed prompt tokens/s, GPU busy 0.88 → 0.81, largest backlog 34 → 25. Whether capacity raises
throughput when the GPU cannot keep up is the question of the 0.16× round (C.4.5).

**Explanation.**

1. *Why the hit rates are equal.* The window produces 359.6 GiB of distinct KV; both extensions are larger. With enough room the
   cache content is decided by the trace alone, and both configurations store every computed chunk (write-through to the NVMe;
   overflow to CXL in the hybrid). The only difference is where a chunk sits when it is found: the hybrid's DRAM part holds the
   *first* 80 GiB written and never evicts them (0.078 of the tokens come from there), the NVMe configuration's DRAM holds the
   *most recent* 51–64 GiB (0.045) and serves everything older from the files (0.149).
2. *Why the gain is in the queue, not in the hits.* The requests that are served from the extension are 108 (CXL) / 131 (NVMe)
   of 1,177; yet 76–79 % of all requests are faster, and requests that miss (< 10 % of the prompt cached) have a p50 of 17.95 s with
   DRAM only (n = 708) and of 10.65 / 10.59 s with an extension (n = 576). The time line of an extension hit shows where its TTFT is spent (p50, ms):

   | configuration | n | TTFT | lookup interval | of which L2 prefetch | GPU transfer | queued → scheduled | scheduled → first token |
   |---|---|---|---|---|---|---|---|
   | DRAM + CXL | 108 | 6,076 | 471 | – | 98 | 5,878 | 239 |
   | DRAM + NVMe | 131 | 6,265 | 545 | 170 | 108 | 5,462 | 248 |

   A hit is still a request that waits ≈ 5.5 s for the GPU behind other requests' prefills. The extension removes 15.8 % of the
   GPU's prefill work; at a utilisation of 0.88 that shortens every queue, for hits and misses alike.
3. *Why the NVMe's slower retrieval does not show.* Inside the cache server an NVMe load takes 106 ms at the median and 384 ms
   at p95 (max 652 ms; 193 requests loaded 68.7 GiB at 2.83 GiB/s; for prefixes ≥ 16K tokens the median is 325 ms). Experiment A
   measured what that costs on an idle server: a 16K hit in 290 ms from the NVMe against 93 ms from CXL L1 (+197 ms). Here the load runs while the request is waiting for the
   GPU anyway — the lookup starts when vLLM's scheduler first reaches the request in its queue (a median 1–3 s after it was
   sent), the first token follows 5–10 s later at the median (`pairs_tier.py lookups`) — so it is hidden behind a wait
   for the GPU that is 14–50× longer. On the 69 requests that are extension hits in both runs the median TTFT difference CXL − NVMe is
   +1 ms.
4. *Why the CXL configuration is the slower one by half a percent.* It is not noise: over the first 600 s, where the hybrid
   still writes to its DRAM part and the three configurations do the same thing, their per-request prefill times agree to
   ±0.06 % and the TTFTs to tens of ms. After the DRAM part is full (≈ 1,100 s) the hybrid's prefill of requests with identical
   cached tokens is 0.3 % longer (+3–4 ms per request at the median; 78–81 % of the requests are slower) and its TTFT 21–189 ms later (mean per
   segment), the queue amplifying the prefill difference. The identified difference between the runs at that point is the store direction of C.1 item 8: the GPU writes into
   CUDA-registered CXL memory at 3.89 GiB/s instead of 12.14 GiB/s, so the 279.6 GiB of stores occupy the transfer path for
   71.9 s instead of 23 s — while the GPU is computing. The NVMe configuration stores into DRAM at 12.14 GiB/s and writes the
   files from DRAM with CPU threads (1.0 GiB/s per store task), off the GPU's path.
5. *The DRAM budget holds in all three.* The cache server's resident set is 81.0 GiB in each (the hybrid's DRAM part is 80.0 GiB
   of shared memory); the page cache grows by 0.2–0.5 GiB (logs); the NVMe device read 68.69 GiB — the 68.67 GiB the L2 loaded,
   i.e. every NVMe hit was read from the device, none from the page cache.

*What this window does not test.* 359.6 GiB fits in both extensions, so nothing here separates them by capacity or by eviction
behaviour; and the load is high enough that queueing hides a retrieval of a few hundred ms. The long window (C.4.4, the
extensions fill and evict), the lower rate (C.4.3, shorter queues) and the overload round (C.4.5) cover those.

#### C.4.2 Tool-agent trace, 0–400 s at 0.08× (high load)

Runs `b-tool08-{none,dram80,hyb,daxl2,ssdn}` (2026-11-13, 5,002–5,010 s each, 2,332 requests, 19.42 M prompt tokens; all requests
HTTP 200, no error line in any log). The conversation window got the same two additional configurations (`b-conv08-none`,
`b-conv08-daxl2`); their rows are in the table of C.4.1's window in `B/tables-b.md` and are used below.

| configuration | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | computed prompt tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vLLM alone (no host cache) | 0.274 | 0.274 | – | – | – | 14.10 | 32.86 | 102.58 | 123.20 | 40.70 | 46.31 | 124.88 | 0.465 | 2,815 | 0.93 | 103 |
| DRAM only, 80 GiB | 0.396 | 0.255 | 0.141 | – | – | 11.72 | 12.40 | 60.31 | 83.18 | 19.78 | 23.44 | 82.49 | 0.466 | 2,343 | 0.86 | 60 |
| + 512 GiB CXL, hybrid L1 | **0.495** | 0.276 | 0.140 | 0.079 | – | 9.81 | **6.30** | 39.64 | 58.66 | 11.60 | 15.13 | 61.99 | 0.466 | 1,961 | 0.79 | 44 |
| + 512 GiB CXL, L2 adapter | **0.495** | 0.277 | 0.116 | – | 0.102 | 9.81 | **6.29** | 39.49 | 58.37 | 11.47 | 14.90 | 61.54 | 0.466 | 1,961 | 0.79 | 44 |
| + 512 GiB NVMe, `fs_native` L2 | **0.495** | 0.278 | 0.115 | – | 0.102 | 9.81 | **6.31** | 39.36 | 58.38 | 11.47 | 14.93 | 61.39 | 0.466 | 1,961 | 0.79 | 44 |

Offline model of the window: 0.351 with the GPU pool alone, 0.400 at 64 GiB, 0.496 at ≥ 320 GiB. The window produces 340.9 GiB
of distinct KV; no extension evicts. Cache server RSS 81.0 GiB in the four cached configurations, page-cache growth
0.14–0.18 GiB, NVMe device read 67.9 GiB = the L2's loads.

**Result.** The same picture as the conversation window, on a trace with three times the reuse: the three extensions end at
the same cached share (0.495, the model's value for unlimited capacity), recompute the same 9.81 M tokens (16.3 % fewer than
DRAM alone, 30.4 % fewer than vLLM alone), and halve the TTFT of the DRAM-only configuration (p50 12.40 → 6.3 s, mean 19.78 →
11.5–11.6 s). Among the extensions the all-request statistics differ by at most 1.1 % (mean 11.47 / 11.47 / 11.60 s). Paired
per request: CXL L2 − NVMe 0.00 s (mean and median; 49 % of requests faster with CXL), CXL hybrid − NVMe +0.13 s mean, +0.02 s
median.

**Explanation.**

1. *The GPU's own prefix cache carries most of this trace's reuse, and it needs the host tier to do so under load.* vLLM alone
   reaches 0.274, below the model's 0.351 for a 3.52 GiB pool: with up to 103 requests waiting, the pool's blocks are in use by
   running requests, not holding old prefixes. With a host tier behind it the total is on the model's line (0.396 against 0.400;
   0.495 against 0.496) — what the pool cannot keep comes back from the host.
2. *DRAM is the larger step here, the extension the smaller.* 80 GiB of DRAM removes 2.38 M recomputed tokens and takes the TTFT
   p50 from 32.9 to 12.4 s; the 512 GiB behind it remove another 1.91 M and take it to 6.3 s. In the conversation trace it is the
   other way round (0.68 M, then 1.92 M): its reuse is spread over longer distances.
3. *The medium of the extension is again invisible in the totals,* for the reason of C.4.1: an extension hit waits 3.3–3.4 s
   (p50) for the GPU; the load from the NVMe inside the cache server takes 104 ms at the median and 382 ms at p95 (CXL L2: 12.7 /
   73.7 ms), and it runs during that wait.

#### C.4.3 Half the rate (0.04×), trace 0–200 s — conversation and tool-agent

Runs `b-conv04-{dram80,hyb,ssdn}` (2026-11-13, 4,982 s each, 599 requests, 6.88 M prompt tokens) and `b-tool04-{dram80,hyb,ssdn}`
(2026-11-13, 4,984 s each, 1,159 requests, 9.79 M prompt tokens); all requests HTTP 200, no error line in any log.

Conversation:

| configuration | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | computed prompt tok/s | GPU busy | backlog max | queued → scheduled p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only, 80 GiB | 0.093 | 0.044 | 0.048 | – | – | 6.25 | 3.92 | 27.44 | 37.33 | 7.04 | 16.87 | 44.95 | 0.120 | 1,254 | 0.51 | 15 | 94 |
| + 512 GiB CXL, hybrid L1 | **0.182** | 0.044 | 0.094 | 0.044 | – | 5.63 | **3.20** | 26.32 | 35.83 | 6.36 | 14.49 | 43.26 | 0.120 | 1,131 | 0.49 | 15 | 86 |
| + 512 GiB NVMe, `fs_native` L2 | **0.182** | 0.044 | 0.051 | – | 0.086 | 5.63 | **3.19** | 26.31 | 35.80 | 6.36 | 14.38 | 43.21 | 0.120 | 1,131 | 0.49 | 15 | 107 |

Offline model: 0.100 at 64 GiB, 0.183 at ≥ 240 GiB. The window produces 197.6 GiB of distinct KV; no extension evicts.

Tool-agent:

| configuration | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | computed prompt tok/s | GPU busy | backlog max | queued → scheduled p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only, 80 GiB | 0.383 | 0.297 | 0.086 | – | – | 6.04 | 2.08 | 25.04 | 37.44 | 5.81 | 7.41 | 41.20 | 0.233 | 1,212 | 0.50 | 26 | 111 |
| + 512 GiB CXL, hybrid L1 | **0.446** | 0.298 | 0.121 | 0.027 | – | 5.42 | **1.49** | 23.59 | 36.40 | 5.15 | 6.28 | 38.19 | 0.233 | 1,088 | 0.48 | 26 | 67 |
| + 512 GiB NVMe, `fs_native` L2 | **0.446** | 0.298 | 0.091 | – | 0.057 | 5.42 | **1.50** | 23.56 | 36.33 | 5.15 | 6.29 | 38.09 | 0.233 | 1,088 | 0.48 | 26 | 78 |

Offline model: 0.340 with the GPU pool alone, 0.389 at 64 GiB, 0.447 at ≥ 240 GiB. The window produces 188.7 GiB of distinct KV;
no extension evicts. Cache server RSS 80.9–81.0 GiB, page-cache growth 0.39–0.76 GiB, NVMe device read 19.3 GiB = the L2's loads.

**Result.** At half the rate the GPU is busy half of the time and the median request is scheduled within 0.1 s of its arrival.
The extension still removes a tenth of the recomputed tokens (9.8 % in the conversation window, 10.2 % in the tool-agent one), but there is less waiting to
remove. Conversation: TTFT p50 −18 % (3.92 → 3.2 s), mean −10 % (7.04 → 6.36 s), p95 −4 %. Tool-agent: p50 −28 % (2.08 →
1.49 s), mean −11 % (5.81 → 5.15 s), p95 −6 %. In both, half of the requests are unchanged (paired median difference 0.00 s; the
mean difference is −0.68 and −0.66 s). CXL and NVMe are again equal in every all-request statistic (conversation 3.20 / 3.19 s
p50, 6.36 / 6.36 s mean; tool-agent 1.49 / 1.50 s, 5.15 / 5.15 s; paired mean and median difference 0.00 s in both).

**Explanation — where the NVMe's slower read does show, and why it does not move the totals.** With the queue out of the way
for half of the requests, the retrieval itself becomes visible on the requests that have one. Pairing every request that
loaded from the NVMe L2 with the same request in the hybrid run (same cached tokens in both):

| window | requests that loaded from the NVMe | NVMe load p50 / p95 ms | TTFT NVMe − CXL hybrid, median / mean ms | of these, served without a queue (TTFT < 1 s with CXL) | their TTFT p50, CXL → NVMe ms | median / mean difference ms |
|---|---|---|---|---|---|---|
| conversation 0.04× | 64 of 599 | 78 / 373 | +17 / +61 | 29 | 284 → 338 | +73 / +122 |
| tool-agent 0.04× | 64 of 1,159 ¹ | 80 / 328 | +17 / +64 | 29 | 319 → 445 | +116 / +133 |
| conversation 0.08× | 193 of 1,177 | 106 / 408 | −6 / −114 | 55 | 307 → 415 | +86 / +123 |
| tool-agent 0.08× | 202 of 2,332 | 104 / 382 | −17 / −74 | 59 | 308 → 432 | +45 / +101 |

¹ The equal counts of the two 0.04× windows (64 and 29) are a coincidence: the requests and the bytes differ (20.4 and 19.3 GiB
loaded).

A hit that finds the GPU free is 45–116 ms slower from the NVMe at the median (+15 to +36 % of its TTFT), 0.10–0.13 s on
average — the size Experiment A measured on an idle server for prefixes of 4K–8K tokens. Such requests are 2.5–5 % of a
window. For the others the sign of the difference is that of the queue they happened to meet, not of the medium. In the
all-request mean the NVMe's retrieval is worth 64 × 61 ms ÷ 599 = 6.5 ms in the conversation window at 0.04× — 0.1 % of a
6.36 s mean — and 64 × 64 ms ÷ 1,159 = 3.5 ms in the tool-agent window; the mean is made of prefills of prompts that were not
cached (a 16K miss costs 3.4 s) and of the bursts' queues (p95 26 s and 24 s, the same in both configurations).

*The two traces differ in where the host reuse sits, not in the outcome.* In the tool-agent window the GPU's own prefix cache
serves 0.298 of the prompt tokens and the host tiers another 0.086 (DRAM only) or 0.148 (with an extension); of the hybrid's
0.148, 0.121 comes from its DRAM part and only 0.027 from CXL memory (9.1 GiB read in the whole replay): the hybrid keeps
the first 80 GiB written in DRAM, and in this window those serve more reuse than the most recent 64 GiB that the NVMe
configuration's DRAM holds (0.091); that configuration takes 0.057 from the files (19.3 GiB). The totals are the same; the
amount of traffic that reaches the extension is not — it follows from which chunks the DRAM part keeps, not from the medium
behind it.

#### C.4.4 Conversation trace, long window: 0–900 s at 0.08× — the extensions fill and evict

Runs `b-conv08L-hyb` (2026-11-13 17:22–20:31), `b-conv08L-ssdn` (20:31–23:40), `b-conv08L-dram80` (23:40–02:49 on 2026-11-14), `b-conv08L-daxl2`
(TODO; added 2026-11-13 23:41 as the equal-capacity partner of the NVMe run). 11,250 s of replay each, 2,728 requests,
30.54 M prompt tokens; all requests HTTP 200, no error line in any log. The window produces 734.9 GiB of distinct KV
(83,600 chunks) — more than any configuration can hold.

| configuration | effective capacity GiB ¹ | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | request p50 s | p95 | req/s | out tok/s | computed prompt tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only, 80 GiB | 64 | 0.097 | 0.047 | 0.051 | – | – | 27.57 | 14.46 | 63.07 | 85.06 | 21.42 | 32.76 | 91.57 | 0.241 | 83 | 2,438 | 0.88 | 39 |
| + 512 GiB CXL, hybrid L1 | 473.6 | **0.309** | 0.047 | 0.073 | 0.190 | – | 21.09 | 6.15 | 33.38 | 49.40 | 9.72 | 20.77 | 58.76 | 0.242 | 83 | 1,868 | 0.78 | 25 |
| + 512 GiB CXL, L2 adapter | 409.6 | TODO |
| + 512 GiB NVMe, `fs_native` L2 | 409.6 | **0.302** | 0.047 | 0.045 | – | 0.211 | 21.31 | 6.24 | 33.29 | 49.42 | 9.85 | 20.93 | 59.19 | 0.242 | 83 | 1,887 | 0.78 | 25 |

¹ 0.8 × the tier's size, the point at which LMCache's eviction starts: the hybrid is one L1 of 592 GiB (80 DRAM + 512 CXL)
whose objects exist once; an L2 of 512 GiB is inclusive — it also holds a copy of what is in the DRAM L1 — so the DRAM adds
nothing to the unique capacity. Offline model of the window: 0.101 at 64 GiB, 0.309 at 409.6 GiB, 0.312 at 473.6 GiB, 0.318 with
unlimited capacity (reached at 592 GiB).

| configuration | L1 max GiB | L2 max GiB | evicted from L1, DRAM / CXL GiB | evicted from the L2 | written to DRAM / CXL / NVMe GiB | read from the extension GiB | cache server RSS max GiB | page-cache growth GiB | NVMe device read / written GiB | cache server CPU s |
|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only | 64.1 of 80 | – | 907.6 / – | – | 964.8 / – / – | – | 81.0 | 0.30 | 0.0 / 0.4 | 115 |
| DRAM + CXL hybrid | 473.6 of 592 | – | 68.7 / 215.4 | – | 148.7 / 593.6 / – | 199.1 | 81.1 (80.0 shared memory) | 0.29 | 0.0 / 0.4 | 149 |
| DRAM + NVMe L2 | 64.8 of 80 | 409.6 of 512 | 912.6 / – | 46,612 keys = 409.7 GiB | 750.1 / – / 749.8 | 221.9 | 81.0 | 0.39 | 221.9 / 751.9 | 142 |

**Result 1 — when the extensions fill, the larger effective capacity wins by a little, and it is the CXL hybrid that has
it.** The NVMe L2 reaches its 409.6 GiB watermark 5,966 s into the replay and starts to evict; the hybrid reaches 473.6 GiB
at 7,144 s. Until 6,083 s no request has a different number of cached tokens in the two runs. From there to the end, 28 requests (1.0 % of the window) find more of their prompt in the hybrid — 219,904 tokens more in total —
and none finds more on the NVMe. Cached share 0.309 against 0.302; 1.0 % fewer recomputed tokens.

**Result 2 — in TTFT that is worth 1.3 % of the mean and nothing at the percentiles.** Mean 9.72 against 9.85 s, p50 6.15
against 6.24 s, p95 33.38 against 33.29 s, p99 49.40 against 49.42 s. Paired per request (hybrid − NVMe), by the time the
request was sent:

| sent | requests | with more cached tokens in the hybrid | their mean TTFT difference ms | requests with equal cached tokens: mean / median TTFT difference ms |
|---|---|---|---|---|
| 0–6,000 s (neither extension evicts) | 1,409 | 0 | – | +59 / +16 |
| 6,000–7,500 s | 341 | 8 | −1,243 | −217 / −1 |
| 7,500–9,000 s | 405 | 7 | −1,569 | −370 / +4 |
| 9,000–11,250 s | 573 | 13 | −1,526 | −288 / +5 |
| whole window | 2,728 | 28 | −1,456 (median −886) | −110 / +9 |

Before either extension evicts the hybrid is the slower one, as in the short windows (+59 ms mean, +16 ms median; its
prefill of identical-work requests is 0.3–0.7 % longer once its DRAM part is full). After the NVMe L2 starts to evict, the
28 requests that keep their hit are 1.5 s faster, and the requests behind them in the queue gain 0.2–0.4 s on average while
their median does not move.

**Result 3 — the NVMe's retrieval in the long window.** 620 requests loaded 221.9 GiB from the files (the device read
221.9 GiB: no page-cache help); the load inside the cache server takes 104 ms at the median, 406 ms at p95 and 1,044 ms at
most (315 ms at the median for prefixes ≥ 16K tokens). The NVMe is being written during 800 s of the replay (749.8 GiB at
0.94 GiB/s) and read during 78 s (2.83 GiB/s); reads and writes overlap for 44 s. Pairing the 617 requests that loaded from
the NVMe and have the same cached tokens in the hybrid run: TTFT NVMe − CXL +12 ms at the median, +185 ms mean; the 175 of
them that found the GPU free (TTFT < 1 s in the CXL run; 6.4 % of the window) have a TTFT p50 of 318 ms from CXL and 463 ms
from the NVMe (median difference +103 ms, mean +222 ms).

**Result 4 — against DRAM only, the long window gives the largest gain of the study.** The cached share triples (0.097 →
0.302 / 0.309), 22.7 % / 23.5 % of the recomputed tokens disappear (27.57 → 21.31 / 21.09 M), and TTFT falls by more than half at
the median and the mean (p50 14.46 → 6.2 s, mean 21.42 → 9.8 s) and by 47 % at p95 (63.1 → 33.3 s). Paired per request:
CXL hybrid − DRAM only −11.70 s mean, −4.87 s median, 86 % of the requests faster; NVMe − DRAM only −11.57 s, −4.78 s, 87 %.
The DRAM-only tier writes 964.8 GiB and evicts 907.6 GiB of it to keep 5.1 % of the prompt tokens from being computed; its
GPU is busy 0.88 of the time against 0.78, with up to 39 requests waiting against 25. Completed requests and output tokens
per second are again the same in all three (0.241–0.242 req/s, 83 tok/s): the replay is open-loop and nothing is dropped.

**Result 5 — reuse over a longer horizon** (`tables-writes.md`). Of the 83,600 distinct chunks stored, a later lookup of
the window finds 21.1 % again in the hybrid, 20.8 % with the NVMe L2 and 4.1 % with DRAM only (short window, 5,000 s: 18.6 %
and 4.6 %). The delay from a chunk's store to its first reuse is 1,271 s at the median and 4,056 s at the 90th percentile
with an extension (longest 9,447–9,639 s); DRAM only reuses within 553 / 2,474 s. So a 2.25× longer window raises the share
of written KV that is ever read back from 19 to 21 %: 79 % of what the extension stores (580 GiB of 735 GiB) is not found
again within 11,250 s.

**Explanation.**

1. *Why the hybrid caches more: it is the tier's structure, not the medium.* CXL memory is byte-addressable, so LMCache
   can use it as part of its first level: an object lives either in DRAM or in CXL memory, and the tier evicts at 0.8 × 592
   GiB. A file tier has to sit behind the DRAM level as a second level; with write-through its 512 GiB also hold a copy of
   everything in DRAM, and it evicts at 0.8 × 512 GiB. Both evict in batches of a fifth of the watermark (three drops of 94.5 GiB in the
   hybrid, five of 81.5 GiB in the NVMe L2), so after its first eviction the hybrid holds 379–474 GiB (424 GiB on average)
   and the NVMe L2 328–410 GiB (369 GiB on average). The offline model, which assumes a cache that stays at its capacity,
   gives 0.309 and 0.312 at the two watermarks — 0.003 and 0.006 above the runs; read at the average occupancies instead it
   gives 0.309 for 424 GiB and 0.302 for 369 GiB (linear interpolation between its points), the measured values. The
   55 GiB between the two tiers are worth 0.7 points of cached share at this point of the trace's capacity curve. The CXL L2
   run (TODO) puts the CXL memory behind the same second-level interface, capacity and eviction as the NVMe.
2. *Why 28 requests move the mean by 0.13 s.* Each of them loses a hit of 7,850 tokens on average with the smaller
   capacity — ≈ 1.7 s of prefill at this GPU's rate (a 16K miss costs 3.4 s) — and at a utilisation of 0.78 the requests queued behind it wait for that
   prefill too: the requests with equal cached tokens are 0.2–0.4 s faster on average in the segments where the 28 occur,
   with an unchanged median.
3. *Why the NVMe's slower retrieval still does not show in the totals.* It is larger here than in the short windows — 620
   loads, a tail of 1 s, loads next to a store task 11–20 % slower (2.88 → 2.55 GiB/s for loads of at least 32 chunks, 2.86 →
   2.29 GiB/s over all loads, 10th percentile 0.97 GiB/s) because the device is being written 7 % of the time — and it is
   visible on the 175 hits that find the GPU free (+103 ms at the median). An extension hit still waits 3.5–3.6 s (p50)
   between queueing and scheduling; summed over the window the NVMe's retrieval is 617 × 185 ms ÷ 2,728 = 42 ms of the mean,
   against 9.8 s.

TODO: CXL L2 at equal capacity (cached share equal to the NVMe's? does the medium show?).

#### C.4.5 Sustained overload: conversation trace, 0–400 s at 0.16×

The same 1,177 requests as C.4.1, sent twice as fast (2,500 s instead of 5,000 s). At 0.08× the GPU was busy 0.81–0.88 of
the time; at 0.16× it cannot keep up while requests arrive, the backlog grows for 2,500 s and drains afterwards.

**The first two attempts are void, and why** (`void/b-conv16-dram80-*`, DRAM only, 2026-11-14 02:49–03:32, and
`void/b-conv16-hyb-*`, CXL hybrid, 03:32–04:15; default settings of both servers, as in every other run of the study).
vLLM's engine process died in both, on the same request — 910 s into the DRAM-only replay. Of its 1,177 requests, 243 had
completed; 179 were in flight and ended with the engine's error on an already-open stream (HTTP 200, no output token); 755 were sent after
the crash and were refused. The sequence, from the two logs and the event mirror (times of the DRAM-only run):

1. Request 247 is sent at 02:59:28.5. vLLM's scheduler reaches it in the waiting queue at 03:00:18.9 and starts its lookup:
   LMCache finds four of its chunks (1,024 tokens) in L1 and read-locks them. The request then waits for the GPU behind the
   backlog (vLLM's log at 03:05:32: 5 running, 174 waiting, 34 deferred).
2. A read lock in LMCache's L1 expires after 300 s (`--l1-read-ttl-seconds`, default).
3. At 03:05:32.5 — 313.6 s after the lookup (313.8 s in the hybrid run) — the request is scheduled and its retrieve is
   submitted. LMCache refuses two of the four chunks: `Failed to read prefetched object …: The specified key exists but
   cannot be read`, `Some keys not found during retrieve!`. The chunks are still in the cache; `L1Manager.unsafe_read`
   returns `KEY_NOT_READABLE` for an object whose read lock is no longer held. (The other two are the first two chunks
   of the prompt; a renewal of their lock by later lookups of other requests would explain why they stayed readable —
   not checked.)
4. vLLM 0.31.0's default `kv_load_failure_policy` is `fail`: `Failing 1 request(s) due to KV load failure
   (failure_policy=fail, 512 tokens affected)`. One step later the scheduler's `_update_from_kv_xfer_finished` asserts
   that the request it has just removed is still known (`assert req_id in self.requests`), and `EngineCore encountered a
   fatal error`.

So the stock stack does not survive this load: a request with a host-cache hit that waits more than 300 s between its
lookup and its retrieve loses the hit, and the loss kills the engine. Eviction is not involved — the hybrid had evicted
nothing (91.8 of 592 GiB in use) and failed on the same two chunks — and neither is the medium: it is a timeout of the
cache server meeting a failure path of the engine, in any configuration with a host cache. In the other 19 replays of
this study no load failed: neither log has an error line and every request produced output tokens.

**The round as run** (`b-conv16r-{dram80,ssdn,hyb}`, 2026-11-14 04:15–07:35): the same two settings in all three
configurations — LMCache `--l1-read-ttl-seconds 7200` (a lookup keeps its chunks readable for the whole wait) and vLLM
`kv_load_failure_policy=recompute` (a failed load becomes a recomputation instead of a failed request). All 1,177 requests
completed in each run (HTTP 200, no error, at least one output token); no error line in either log; **no load failed**, so
the second setting was never exercised — the longer read lock alone is what the round needed.

| configuration | completed req/s, whole run | during the arrivals (0–2,500 s) | after them | run length s | cached share | GPU prefix | DRAM | CXL L1 | L2 | recomputed Mtok | TTFT p50 s | p95 | p99 | mean | output tok/s | GPU busy | backlog max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DRAM only, 80 GiB | 0.287 | 0.287 | 0.287 | 4,096 | 0.130 | 0.045 | 0.086 | – | – | 11.70 | 857 | 1,546 | 1,565 | 836 | 97.7 | 1.00 | 460 |
| + 512 GiB CXL, hybrid L1 | **0.305** | 0.296 | 0.322 | 3,855 | **0.208** | 0.045 | 0.078 | 0.085 | – | 10.66 | 793 | 1,328 | 1,344 | 755 | 103.8 | 1.00 | 437 |
| + 512 GiB NVMe, `fs_native` L2 | **0.306** | 0.296 | 0.324 | 3,848 | **0.209** | 0.045 | 0.094 | – | 0.070 | 10.65 | 791 | 1,321 | 1,337 | 753 | 104.0 | 1.00 | 437 |

Offered: 0.471 requests/s for 2,500 s. Cache server RSS 81.1–81.2 GiB in all three; page-cache growth 0.11–0.37 GiB; the DRAM
tier evicts 342–345 GiB in the two configurations that have one of 80 GiB, no extension evicts (359.3 GiB of 409.6 / 473.6 GiB
used); NVMe device read 34.0 GiB = the L2's loads.

**Result 1 — at saturation, capacity is throughput.** The GPU runs a step 100 % of the time in all three runs, and the
server completes what the GPU can compute: 0.287 requests/s with DRAM only, in the arrival phase and in the drain alike. With
either extension 9.0 % of the recomputed prompt tokens disappear (11.70 → 10.65 M) and the same 1,177 requests are finished in
3,848–3,855 s instead of 4,096 s: **+6.3 % / +6.5 % completed requests and output tokens per second** (0.305 / 0.306 against
0.287 req/s; 104 against 98 output tokens/s). The gain grows as the cache fills: +3 % while requests arrive (740 against 718
completed by 2,500 s), +12–13 % in the drain (0.322–0.324 against 0.287 req/s). This is the only round of the study in which
the cache changes completed work per second; at 0.04× and 0.08× every configuration completes what the trace offers.

**Result 2 — TTFT is the queue, and the queue is 8–14 % shorter.** A request waits 13–14 minutes for its first token in
every configuration (p50 857 s with DRAM only, 791–793 s with an extension; mean 836 → 753–755 s, −10 %; p95 1,546 → 1,321–1,328 s,
−14 %). Paired per request, extension − DRAM only: −80 / −83 s on average, −63 / −65 s at the median, 76 % of the requests
faster. No host cache makes this load serveable; it removes a tenth of the wait.

**Result 3 — CXL and NVMe are equal here too, and the small difference goes the other way.** Cached share 0.208 / 0.209 (two
requests find 10,752 tokens more with the NVMe configuration), recomputed tokens within 0.1 %, run length 3,855 against
3,848 s. Paired, CXL hybrid − NVMe: TTFT +2.4 s mean and +2.1 s median (+0.3 %), 81 % of the requests later with the hybrid.
The requests with the same cached tokens in both runs (1,175) have 0.19 % more prefill time in the hybrid (+6.1 s summed over
3,196 s; +3.0 ms per request at the median); at saturation every second of GPU time is a second of queue for everything behind
it, and the hybrid's run ends 7 s later. The NVMe's retrieval is slower than at 0.08× — 85 loads, 301 ms at the median, 712 ms at
p95 inside the cache server (106 / 384 ms at 0.08×), on a device that is being written 10 % of the time (374 s of 3,848 s) —
and none of it reaches a request: the load runs minutes before the request is served (Result 4).

**Result 4 — under overload the lookup runs far ahead of the service, which costs the extensions a part of their hits and
gives the small DRAM tier more of them.** Compared with the same requests at 0.08× (C.4.1): the extension configurations
cache 0.208 / 0.209 instead of 0.238 — 61–63 requests have fewer cached tokens (−0.40 / −0.41 M), none has more; DRAM only caches
0.130 instead of 0.096 — 77 requests have more (+0.75 M), 38 have fewer (−0.28 M).

**Explanation.**

1. *Why throughput follows the cache only here.* The replay is open-loop. Below saturation the completed requests per second
   equal the arrivals whatever the cache does, and saved prefill shows up as idle GPU time (busy 0.88 → 0.81 at 0.08×) and
   shorter queues. At 0.16× there is no idle time to gain, so 9 % less prefill becomes a 6 % shorter run (decode work, 340
   output tokens per request, is the same in all three). The value of the extension is the recomputation it removes; whether
   that appears as latency or as throughput depends on which side of saturation the server is.
2. *Why the two media cannot differ at saturation.* vLLM's scheduler starts the cache lookup of a waiting request when it
   first reaches it in the queue, not when it is served. In this round that is 229–250 s (median) after the request was sent
   and **377–418 s (median; 921–1,007 s at the 90th percentile) before its first token** — at 0.08× the same interval is 5–10 s
   (`pairs_tier.py lookups`). An NVMe load of 0.3–0.9 s is finished long before the GPU is free for the request; the medium of
   the extension is off the critical path by three orders of magnitude. What remains is the hybrid's slower store direction
   (3.89 GiB/s into CUDA-registered CXL memory, C.1 item 8), which is on the GPU's side of the path — the candidate for its
   0.19 % longer prefill, as in the other windows; it was not isolated.
3. *Why the extensions lose hits and the DRAM tier gains them.* A lookup finds only what has been stored before it runs, and
   what it finds is read-locked until the request is served. With the lookup hundreds of seconds ahead of the service, a request
   does not find the KV of predecessors that are still waiting in front of it: 61–63 requests lose their hit in the extension
   configurations, which keep everything that was stored. For the DRAM-only tier the same shift has a second, larger effect: a
   chunk has to survive in the tier only until the lookup, not until the service. The tier is written at 0.098 GiB/s (400.1 GiB
   in 4,096 s), so the 418 s are ≈ 41 GiB of writes that a chunk no longer has to outlive — in a tier that holds 64 GiB.
   A cache model driven by the measured lookup and first-token times of each run (`pairs_tier.py timed`: trace blocks, LRU of
   the tier's effective capacity, lookup at the measured instant and counted as a hit then, store at the first token; **a
   model, not a measurement**) gives 0.134 for DRAM only at 0.16× and 0.101 at 0.08× (measured 0.130 and 0.096), and 0.209 for
   both extensions at 0.16× and 0.239 at 0.08× (measured 0.208 / 0.209 and 0.238). With the lookup placed at the send time
   instead it gives 0.178 for the extensions, so the timing of the lookup is what sets the shares. Whether the locked chunks
   also take space from the rest of the tier makes no difference in the model (0.134 with and without). The gain of the DRAM
   tier therefore rests on the long read lock: it is a property of this round's setting, not of DRAM.
4. *What the two timeouts mean.* In 689–725 of the 1,177 requests more than 300 s pass between the lookup and the first token:
   with LMCache's default read-lock TTL each of them that has a host hit loses it, and with vLLM 0.31.0's default failure policy
   the first such loss ends the engine (the void runs). A second limit, the 600-s lifetime of LMCache's per-request session
   (hard-coded), is exceeded by 370–424 requests; it shows as 286–352 warnings per run (`free_lookup_locks … before its prefetch
   result was consumed`) and has no effect on the results here: the tokens found by the lookup and the cached tokens of the
   request are equal for every request of the three runs. Neither limit is specific to a medium or to this study's tiers.

PENDING-PART part_C4_sens.md

#### C.4.7 The brief's seven questions for Experiment B

1. *How much extra KV data does CXL retain?* The DRAM-only tier holds 51–64 GiB at any time and evicts the rest: 371 GiB of the
   426 GiB it writes in the conversation window at 0.08×, 908 GiB of 965 GiB in the long window. The hybrid retains everything
   the four 5,000-s windows produce — 359.6, 340.9, 197.6 and 188.7 GiB, i.e. 3–5.6× what the DRAM tier holds — and evicts
   nothing; in the long window it holds 379–474 GiB (424 GiB on average after its first eviction) of the 734.9 GiB produced.
2. *How many recomputations are eliminated?* Prompt tokens that are no longer computed, against DRAM only: 1.92 M of 12.17 M
   (15.8 %, conversation 0.08×), 1.91 M of 11.72 M (16.3 %, tool-agent 0.08×), 0.62 M of 6.25 M and of 6.04 M (9.8 % and 10.2 %,
   the two 0.04× windows), 6.48 M of 27.57 M (23.5 %, long window; 6.26 M = 22.7 % with the NVMe), 1.04 M of 11.70 M (8.9 %,
   overload). Against vLLM alone the extension configurations compute 20.3 % (conversation) and 30.4 % (tool-agent) fewer
   prompt tokens at 0.08×.
3. *Does NVMe achieve comparable cache-hit rates?* The same ones wherever the extension does not fill: the same chunks are
   found again (7,627 in the conversation window at 0.08×) and the same number of tokens is recomputed, to the token. In the
   long window it is 0.7 points behind the hybrid (0.302 against 0.309) for a reason of tier structure (C.4.4); under overload
   0.209 against 0.208.
4. *How much slower is NVMe retrieval?* On an idle server the media stage of a 16K hit takes 197 ms from the NVMe (2.9 GiB/s)
   and does not exist for CXL L1 (the GPU copies from the device mapping; lookup 1.2 ms). In the replays the load inside the
   cache server takes 78–106 ms at the median and 328–410 ms at p95 (1,044 ms at most; 301 / 712 ms under overload), against
   12–13 ms / 74–79 ms for the same loads from the CXL L2.
5. *Does that latency affect TTFT?* For the hits that find the GPU free, yes: +45 to +116 ms at the median, 2.5–6.4 % of the
   requests of a window. For the window as a whole, no: every all-request statistic is within 1 % of the CXL configurations,
   and the paired per-request difference has a median of 0.00–0.02 s.
6. *Does increased cache capacity change throughput?* Not at 0.04× and 0.08×, where every configuration completes the
   offered load (it changes how busy the GPU is: 0.88 → 0.78–0.81). At saturation it does: +6.3 % / +6.5 % completed requests
   and output tokens per second at 0.16×.
7. *Do the benefits depend on the workload or the arrival pattern?* On both, through three quantities. (a) *Where the trace's
   reuse sits.* The tool-agent trace has three times the reuse, most of it at short distance: the GPU's own prefix cache
   serves 0.27–0.30 of its prompt tokens, 80 GiB of DRAM is the larger step (2.38 M tokens at 0.08×) and the extension the
   smaller (1.91 M); in the conversation trace it is the other way round (0.68 M, then 1.92 M). (b) *The length of the
   window.* The extension adds 9 points of cached share over the first 200 trace seconds of the conversation trace, 14 over
   400 s and 21 over 900 s (tool-agent: 6 and 10) — a short segment understates a large cache. (c) *How busy the GPU is.* The
   same tenth of removed prefill is worth 4–6 % at p95 at half the rate, half of the TTFT at 0.08× and throughput at 0.16×
   (E.2). Bursts decide the tail: at 0.04× the p95 (24–27 s) is the queue of the trace's bursts and moves by 4–6 %, while
   the median moves by 18–28 %. Under overload the extension loses 3 points of cached share to the early lookup (C.4.5).
   No synthetic burst pattern was replayed in B; bursts of simultaneous hits are Experiment D.

Figures of Experiment B (one colour per configuration in every panel; the offline model in B1 and B4 is a model):

![figB1-capacity-share](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figB1-capacity-share.png)
![figB1b-hit-sources](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figB1b-hit-sources.png)
![figB2-ttft](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figB2-ttft.png)
![figB2b-ttft-cdf](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figB2b-ttft-cdf.png)
![figB3-throughput](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figB3-throughput.png)
![figB4-recomputed](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figB4-recomputed.png)
![figB5-occupancy](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figB5-occupancy.png)

### C.5 Experiment E — KV read / write traffic on the extension during serving (`B/tables-e.md`, `B/tables-writes.md`, `B/*-traffic.csv`; figure E1)

**Why.** The brief's Q5: when a serving system retrieves and persists KV at the same time, how much traffic reaches the CXL
memory, do the two directions overlap, and do they disturb each other? The project's earlier hardware work found strong
read/write interference on this node under synthetic load; the question is whether a serving workload gets near it.

**How.** No extra runs: every replay of Experiment B records, inside the cache server, one line per chunk copy that touches
the extension (direction, bytes, start, end, and the medium of the L1 object or the L2 slot / file), the phase samples of the
GPU transfer thread (every staging copy with its interval), LMCache's own operation events (store / retrieve submitted,
started, ended; L2 load and store tasks), and 1 Hz samples of the cache server's memory and of the NVMe device counters.
`analyze_tier_replay.py` turns the copy records into per-second traffic and into exact overlap of read and write intervals;
`writes_tier.py` follows every stored chunk to see whether it was read again, and compares the rate of L2 loads with and
without a store in progress. What "traffic" means here: the application's copies into and out of the device mapping, each
timed individually and attributed to the medium by the address of its buffer (the mappings are verified by content in P0).
It is not the cards' view: hardware counters of the memory controllers are not accessible on this node (G).

**Result 1 — traffic volume and rate** (CXL configurations; replay length 5,000 s; "busy" = union of the copy intervals):

| replay | configuration | read from CXL GiB | written to CXL GiB | average read / write MiB/s | read busy s | write busy s | rate while busy, read / write GiB/s | largest second, read / write GiB |
|---|---|---|---|---|---|---|---|---|
| conversation 0.08× | hybrid L1 (GPU ↔ CXL) | 53.4 | 279.6 | 11 / 57 | 4.8 | 71.9 | 12.4 ¹ / 3.89 | 1.28 / 0.25 |
| tool-agent 0.08× | hybrid L1 | 52.4 | 260.9 | 11 / 53 | 4.7 | 67.1 | 12.4 ¹ / 3.89 | 2.14 / 0.24 |
| conversation 0.04× | hybrid L1 | 10.3 | 117.6 | 2 / 24 | 0.9 | 30.2 | 12.4 ¹ / 3.89 | 1.16 / 0.23 |
| tool-agent 0.04× | hybrid L1 | 9.1 | 108.7 | 2 / 22 | 0.8 | 28.0 | 12.4 ¹ / 3.89 | 1.16 / 0.25 |
| conversation 0.08×, long window (11,250 s) | hybrid L1 | 199.1 | 593.6 | 18 / 54 | 18.4 | 152.7 | 12.4 ¹ / 3.89 | 1.71 / 0.25 |
| conversation 0.16×, overload (3,855 s) | hybrid L1 | 39.4 | 279.3 | 10 / 74 | 3.7 | 71.8 | 12.4 ¹ / 3.89 | 2.14 / 0.22 |
| conversation 0.08× | L2 adapter (CPU copies CXL ↔ DRAM) | 69.0 | 359.6 | 14 / 74 | 3.2 | 16.8 | 21.8 / 21.5 | 1.76 / 0.25 |
| tool-agent 0.08× | L2 adapter | 67.9 | 340.9 | 14 / 70 | 3.2 | 15.7 | 21.4 / 21.7 | 2.14 / 0.25 |

¹ per-copy rate of the staging copies (C.1); the table's own "read GiB/s while busy" for the hybrid (11.1–11.4) is a lower
bound, because a retrieve that mixes DRAM and CXL chunks is counted with its whole interval.

For comparison, the NVMe configuration of the same replays: 68.7 / 359.5 GiB read / written (conversation 0.08×), read at
2.83 GiB/s while busy (24.3 s), written at 0.92 GiB/s while busy (388.7 s), largest second 1.76 / 0.25 GiB; under overload
34.0 / 359.3 GiB, read at 2.69 GiB/s (12.6 s), written at 0.96 GiB/s (374.1 s).

The extension is idle almost all of the time. In the busiest replays the CXL memory is being read for 3–5 s and written for
16–72 s out of 5,000; the average traffic is 11–14 MiB/s of reads and 53–74 MiB/s of writes. The largest second moves 2.1 GiB
of reads — 17 % of what the GPU's link can take (12.4 GiB/s) and under 5 % of the pair's measured bandwidth (≈ 46 GiB/s) — and
0.25 GiB of writes in every configuration and on every medium: stores are produced by prefill, and 0.25 GiB is the KV of
≈ 7,300 prompt tokens (36 KiB each) — about the most this GPU prefills in a second.

**Result 2 — overlap of retrieval and persistence.**

| replay | configuration | store ops | retrieve ops | retrieves submitted or running while a store op was open | seconds with a store open / a retrieve open / both | seconds of the wall clock with read and write traffic in the same second | overlap of the copies themselves, s |
|---|---|---|---|---|---|---|---|
| conversation 0.08× | DRAM only | 8,180 | 76 | 44 (58 %) | 135.3 / 18.3 / 0.00 | – | – |
| conversation 0.08× | CXL hybrid L1 | 7,214 | 266 | 121 (45 %) | 180.5 / 42.5 / 0.00 | 149 | 0.00 |
| conversation 0.08× | CXL L2 adapter | 7,217 | 266 | 107 (40 %) | 115.2 / 44.1 / 0.00 | 152 | 0.22 |
| conversation 0.08× | NVMe L2 | 7,214 | 266 | 108 (41 %) | 115.2 / 42.2 / 0.00 | 147 | 14.65 |
| tool-agent 0.08× | CXL hybrid L1 | 7,584 | 669 | 302 (45 %) | 171.8 / 84.5 / 0.00 | 155 | 0.00 |
| tool-agent 0.08× | CXL L2 adapter | 7,579 | 664 | 271 (41 %) | 111.4 / 85.9 / 0.00 | 166 | 0.22 |
| tool-agent 0.08× | NVMe L2 | 7,581 | 658 | 266 (40 %) | 111.4 / 86.6 / 0.00 | 159 | 14.50 |
| conversation 0.04× | CXL hybrid L1 | 3,867 | 101 | 35 (35 %) | 90.5 / 10.3 / 0.00 | 31 | 0.00 |
| conversation 0.04× | NVMe L2 | 3,867 | 101 | 29 (29 %) | 63.1 / 10.5 / 0.00 | 48 | 2.58 |
| tool-agent 0.04× | CXL hybrid L1 | 4,040 | 229 | 85 (37 %) | 86.5 / 22.1 / 0.00 | 29 | 0.00 |
| tool-agent 0.04× | NVMe L2 | 4,040 | 229 | 73 (32 %) | 61.2 / 22.2 / 0.00 | 40 | 1.82 |
| conversation 0.08×, long window | DRAM only | 18,730 | 154 | 79 (51 %) | 307.2 / 36.8 / 0.00 | – | – |
| conversation 0.08×, long window | CXL hybrid L1 | 15,454 | 810 | 349 (43 %) | 377.8 / 118.8 / 0.00 | 471 | 0.00 |
| conversation 0.08×, long window | NVMe L2 | 15,563 | 784 | 303 (39 %) | 241.8 / 118.6 / 0.00 | 464 | 44.27 |
| conversation 0.16×, overload | DRAM only | 8,023 | 122 | 68 (56 %) | 128.0 / 40.3 / 0.00 | – | – |
| conversation 0.16×, overload | CXL hybrid L1 | 7,519 | 217 | 101 (47 %) | 181.0 / 63.1 / 0.00 | 118 | 0.00 |
| conversation 0.16×, overload | NVMe L2 | 7,514 | 219 | 99 (45 %) | 117.7 / 64.8 / 0.00 | 15 | 7.43 |

At the level of the application the two directions meet often — with an extension, 40–45 % of the retrieves at 0.08×,
45–47 % at 0.16× and 29–37 % at 0.04× are submitted or run while a store operation is pending, and 150–166 seconds of a high-load replay contain
both a read and a write on the extension. At the
level of the copies they never meet on the GPU path: LMCache moves KV between the GPU and the host on one transfer thread,
store and retrieve operations are served one after the other, and the time with both kinds open is 0.00 s in every run.
In the hybrid L1 that is the only path to the CXL memory, so its read and write intervals do not overlap at all. Only the L2
adapters have their own worker threads: on the CXL L2 the copies overlap for 0.22 s of a replay, on the NVMe for 14.5 s (its
writes are slow enough to be in progress 8 % of the time).

What a retrieve waits for is mostly not the other direction either: between submission and start a retrieve waits 0.1–36 ms
at the median and 0.5–0.8 s at p95; of the summed waiting time another transfer operation was open during a third
(conversation at 0.08×: 10–13 s of 33–39 s, i.e. 48 ms per retrieve) to 45 % (tool-agent: 56–62 s of 131–138 s). The rest matches the pick-up of the operation at
a step boundary of the engine described in the 2026-11-11 study and is not transfer traffic.

**Result 3 — interference where overlap exists** (L2 load tasks of at least 32 chunks = 288 MiB; rate = bytes ÷ summed task
time):

| replay | L2 | loads with no store task open: n, GiB/s | loads with a store task open: n, GiB/s (10th percentile of the per-load rates) |
|---|---|---|---|
| conversation 0.08× | CXL, DAX slots | 49, 30.0 | 42, **15.5** (9.5) |
| tool-agent 0.08× | CXL, DAX slots | 51, 30.1 | 37, **15.6** (11.5) |
| conversation 0.08× | NVMe files | 30, 2.89 | 60, 2.64 (2.34) |
| tool-agent 0.08× | NVMe files | 27, 2.89 | 61, 2.78 (2.66) |
| conversation 0.04× | NVMe files | 16, 2.90 | 13, 2.89 (2.86) |
| tool-agent 0.04× | NVMe files | 18, 2.89 | 9, 2.77 (2.11) |
| conversation 0.08×, long window | NVMe files | 98, 2.88 | 182, 2.55 (1.99) |
| conversation 0.16×, overload | NVMe files | 6, 2.05 | 38, 2.09 (1.04) |

A load from the CXL L2 runs at half its rate when a store to the CXL L2 is in progress during part of it (30 → 15.5 GiB/s;
the median load takes 49 ms instead of 15 ms). On the NVMe the loss is 0–11 % (largest in the long window, where the device is being written 7 % of the time), with a tail for small loads (10th percentile
0.9 GiB/s over all loads against 2.7 GiB/s without a store). Under overload the lookups — and with them the loads — come in
bursts as the scheduler works through its queue: the 85 loads of that run fall into 15 seconds of the wall clock (193 loads in 164 seconds at 0.08×), run at 2.05–2.09 GiB/s with or
without a store task open, and take 301 ms at the median instead of 106 ms. Whether the CXL slowdown is the medium (reads under concurrent
writes, as in the project's earlier synthetic measurements) or the cache server's own threads sharing its eight cores was not
separated: both copies are CPU `memmove`s of the same process, and no counter distinguishes the two here. In serving it is
below visibility: about one second of affected loads per 5,000-s replay, tens of ms on a request that then waits seconds for
the GPU.

**Result 4 — the store direction is the slow one on the GPU ↔ CXL path, and the write traffic is mostly never read.**
(a) Stores into the CUDA-registered CXL arenas run at 3.89 GiB/s against 12.14 GiB/s into DRAM (C.1 item 8): the hybrid's
store operations take 38 ms at p95 instead of 21 ms and are open 172–181 s per high-load replay instead of 111–115 s;
this is the one place where the CXL configuration is measurably behind (C.4.1 item 4). (b) No admission policy is enabled in
this study — LMCache stores every chunk the GPU computed — so the write traffic is the prefill traffic. Following every stored
chunk (`tables-writes.md`):

| replay | configuration | stored: distinct GiB (chunks stored more than once) | found again by a later lookup in the window, share of distinct chunks | never found GiB | copied back to the GPU GiB | delay from store to first reuse, p50 / p90 s |
|---|---|---|---|---|---|---|
| conversation 0.08× | DRAM only (evicts) | 359.5 (7,511 stored again) | 0.046 | 342.9 | 23.5 | 507 / 1,272 |
| conversation 0.08× | any extension | 359.6 | 0.186 | 292.5 | 89.5 | 1,126 / 2,859 |
| tool-agent 0.08× | DRAM only | 340.8 (7,468) | 0.054 | 322.4 | 94.3 | 529 / 1,305 |
| tool-agent 0.08× | any extension | 340.9 | 0.199 | 273.1 | 145–146 | 1,125 / 2,859 |
| conversation 0.04× | DRAM only | 197.6 (2,408) | 0.048 | 188.1 | 11.4 | 962 / 2,417 |
| conversation 0.04× | any extension | 197.6 | 0.144 | 169.2 | 32.5 | 1,716 / 2,925 |
| tool-agent 0.04× | DRAM only | 188.7 (2,422) | 0.052 | 178.8 | 28.9 | 963 / 2,417 |
| tool-agent 0.04× | any extension | 188.7 | 0.153 | 159.9 | 49.8 | 1,715 / 2,894 |
| conversation 0.08×, long window | DRAM only | 734.8 (26,171) | 0.041 | 704.7 | 53.1 | 553 / 2,474 |
| conversation 0.08×, long window | CXL hybrid L1 / NVMe L2 (both evict) | 734.9 | 0.211 / 0.208 | 579.8 / 581.9 | 275.6 / 268.0 | 1,271 / 4,056 |
| conversation 0.16×, overload | DRAM only | 359.2 (4,654) | 0.082 | 329.6 | 39.6 | 370 / 633 |
| conversation 0.16×, overload | CXL hybrid L1 / NVMe L2 | 359.3 | 0.155 / 0.156 | 303.6 / 303.2 | 75.3 / 75.7 | 700 / 1,586 |

With an extension, 79–86 % of the bytes written were not found by any later request of the same window; four fifths of the
CXL write traffic bought nothing inside the window. This is an accounting of what happened, not a policy that was run, and
it is censored by the window: chunks stored near its end had little time to be reused (in the long window of 11,250 s the share
found again is 0.21 instead of 0.19, C.4.4). It bounds what an admission policy could remove from the write side — and, given (a), from the one
place where the CXL path costs time.

**The brief's five questions.**

1. *How frequently do retrieval and persistence overlap?* As operations, constantly under load (40–45 % of retrieves meet a
   pending store at 0.08×, 29–37 % at 0.04×); as copies on the medium, never in the hybrid L1 (one transfer thread) and for 0.2 s per 5,000 s in the CXL
   L2 adapter.
2. *What is the instantaneous traffic?* Reads: bursts at the rate of the GPU link, up to 2.1 GiB in a second; writes: at most
   0.25 GiB in a second, set by the GPU's prefill rate; averages 11–14 and 53–74 MiB/s.
3. *Does it approach the CXL bandwidth?* No: the largest second is under 5 % of the pair's ≈ 46 GiB/s, the average three
   orders of magnitude below it. The limits that are reached are the GPU link (12.4 GiB/s for reads) and the 3.89 GiB/s
   store path.
4. *Is there evidence of read/write interference?* Where the two directions run on separate threads, yes: CXL L2 loads halve
   in rate next to a store. It is rare and small in this workload, and its cause (medium or CPU) is not isolated. On the GPU
   path the question does not arise, because the software serialises the two directions.
5. *Does the workload justify a duplex-aware serving mechanism?* Not on this evidence: with one small GPU the traffic is far
   from the medium's capacity and the stack already serialises the two directions. What would change the picture is outside
   this node — several or faster GPUs on one CXL pair, which multiply both the prefill (write) rate and the retrieval bursts,
   and a transfer path with more than one thread. This study did not measure either (G).

![figE1-traffic](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figE1-traffic.png)

### C.6 Trace-driven capacity analysis (a cache model — not a measurement)

Everything in this subsection is computed offline from the two Mooncake traces; nothing in it was served by a model. It is kept apart
from C.4 for that reason and is used only to say which capacities a given trace window can exercise at all.

**Method.** `benchmarks/serving/trace_capacity_tier.py` replays the prompts of a trace window, in trace order, through one LRU over
512-token hash blocks with prefix semantics (a request is served up to its first block that is not in the cache; the code of
`trace_reuse.py`, 2026-11-04), at 36 KiB of KV per token, and reports the share of prompt tokens a cache of that size serves. An LRU
hierarchy is inclusive, so the share a tier adds is the difference between two capacities. The capacities that correspond to this
study: 3.52 GiB (the GPU pool of 6,400 blocks), 64 GiB (the 80 GiB DRAM tier at its 0.8 eviction trigger), 409.6 GiB (a 512 GiB L2 at
its trigger; with the write-through policy the L2 holds a superset of L1, so this is the unique capacity of `daxl2` and `ssdn`),
473.6 GiB (the 592 GiB hybrid L1 at its trigger), and unbounded. Raw output: `trace-model/trace-capacity.csv`; figure:
`figs/figT1-trace-capacity.png`.

![trace model](../../experimental_results/2026-11-12-cxl-vs-nvme-serving/figs/figT1-trace-capacity.png)

Share of prompt tokens served, by capacity (GiB):

| trace, window | requests | prompt tokens (M) | KV of all prompts (GiB) | 3.52 | 64 | 80 | 160 | 320 | 409.6 | 473.6 | 592 | unbounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| conversation 0–200 s (replayed at 0.04×) | 599 | 6.85 | 235 | 0.045 | 0.100 | 0.132 | 0.181 | 0.183 | 0.183 | 0.183 | 0.183 | 0.183 |
| conversation 0–400 s (replayed at 0.08×) | 1,177 | 13.39 | 460 | 0.045 | 0.101 | 0.132 | 0.196 | 0.239 | 0.239 | 0.239 | 0.239 | 0.239 |
| conversation 0–900 s (replayed at 0.08×, long window) | 2,728 | 30.38 | 1,043 | 0.047 | 0.101 | 0.137 | 0.219 | 0.293 | 0.309 | 0.312 | 0.318 | 0.318 |
| conversation 0–1,800 s (not replayed) | 5,719 | 61.82 | 2,122 | 0.048 | 0.103 | 0.136 | 0.226 | 0.304 | 0.328 | 0.337 | 0.352 | 0.358 |
| conversation 0–3,600 s (not replayed) | 12,031 | 123.34 | 4,235 | 0.050 | 0.103 | 0.136 | 0.234 | 0.316 | 0.340 | 0.351 | 0.370 | 0.383 |
| tool-agent 0–200 s (replayed at 0.04×) | 1,159 | 9.76 | 335 | 0.340 | 0.389 | 0.407 | 0.446 | 0.447 | 0.447 | 0.447 | 0.447 | 0.447 |
| tool-agent 0–400 s (replayed at 0.08×) | 2,332 | 19.36 | 665 | 0.351 | 0.400 | 0.418 | 0.464 | 0.496 | 0.496 | 0.496 | 0.496 | 0.496 |
| tool-agent 0–900 s (not replayed) | 5,462 | 44.71 | 1,535 | 0.362 | 0.408 | 0.430 | 0.487 | 0.538 | 0.547 | 0.550 | 0.553 | 0.553 |
| tool-agent 0–1,800 s (not replayed) | 11,375 | 91.46 | 3,140 | 0.368 | 0.413 | 0.434 | 0.496 | 0.548 | 0.563 | 0.569 | 0.576 | 0.577 |
| tool-agent 0–3,600 s (not replayed) | 23,608 | 184.57 | 6,337 | 0.377 | 0.420 | 0.442 | 0.508 | 0.562 | 0.576 | 0.583 | 0.593 | 0.595 |

What the model says about the windows of C.4:

- **The reuse that needs hundreds of GiB exists in these traces, and it is a matter of the window length.** In the first 200 trace
  seconds everything reusable fits in 160 GiB; in the first 400 s the conversation trace still gains 4.4 points between 160 and
  320 GiB; in the first 900 s it gains 7.4 points between 160 and 320 GiB and another 2.4 beyond 320 GiB; over an hour the curve still
  rises at 592 GiB. A short window therefore understates a large cache by construction, and no statement about the value of a large
  cache in this report is based on the 200-s windows alone.
- **How much a 512 GiB extension can add over the 80 GiB DRAM tier, by window (conversation trace):** 0.183 − 0.100 = 8 points of the
  prompt tokens (0–200 s), 14 points (0–400 s), 21 points (0–900 s, either extension), 24–25 points (0–3,600 s). On the tool-agent
  trace: 6, 10, 14 and 16 points; there the GPU pool alone already serves 34–38 % (short-distance reuse of the agent's own previous step).
- **Whether the extensions fill.** A cache that never evicts stores each distinct block once: (1 − unbounded share) × KV of all
  prompts = 350 GiB (conversation 0–400 s), 335 GiB (tool-agent 0–400 s), 192 / 185 GiB (the 200-s windows) — all below 409.6 GiB,
  so in the four standard windows the extension tiers of C.4 never reach their eviction trigger and behave as unbounded caches. The
  long window (conversation 0–900 s: 712 GiB of distinct KV) is the one that fills and evicts both extensions; their eviction and
  deletion paths were additionally exercised at small scale in the B0 runs.
- **Difference between the two extensions that the model predicts:** none in the standard windows, and 0.3 points in the long one
  at the two eviction triggers (0.312 for the hybrid's 473.6 GiB against 0.309 for an L2's 409.6 GiB). The long replay measured
  0.7 points (C.4.4): both tiers evict a fifth of their trigger at a time and therefore hold less than the trigger on average
  (424 and 369 GiB), and read at those occupancies the model gives the measured 0.309 and 0.302. It is still a capacity effect.

Limits of the model: one LRU in trace order with instantaneous stores. In the replays a block becomes available only when its request
has finished and the store has completed, arrival order under overload differs from completion order, the L1 evicts in rounds (20 % of
the tier at a time, so its mean occupancy is below 64 GiB), and LMCache works with 256-token chunks. The measured shares of C.4 are
compared with the model there; for the sustained-overload round, where the time between a request's lookup and its service is
hundreds of seconds, C.4.5 uses a variant of the model driven by the measured lookup and first-token times.

## D. Causal analysis

Each subsection of C carries its own Why / How / Result / Explanation. This section puts the important results side by side
and names, for each, the part of the serving path that causes it. The path of a request with a host hit is: arrival → waiting
queue of vLLM → **lookup** (LMCache finds the prefix; an L2 tier loads it into DRAM now) → wait for the GPU → **retrieve**
(host → GPU over the GPU's link, one transfer thread) → prefill of the uncached rest → first token; its KV is **stored**
(GPU → host, same thread; an L2 tier then writes it to its medium with CPU threads) while and after it is computed.

**D.1 A hit on CXL memory costs what a hit on DRAM costs.**
*Why:* CXL memory has a higher access latency and a lower bandwidth than DRAM; does a KV hit see either?
*How:* identical hits from each tier on an idle server (A), under Poisson load at four rates (C), and in bursts of 1–16
simultaneous hits (D); every measured chunk verified to be on the device.
*Result:* 93–94 ms for a 16K-token hit from either (within 1 ms at every length); every TTFT quantile, the request time and
the throughput within 1–2 % at all four rates; the same in every column of the burst experiment.
*Explanation — the GPU link:* on a hit the only reader of the KV bytes is the GPU's staging copy, which runs at 12.4 GiB/s
over PCIe 4.0 ×8 whether the source is pinned DRAM or the registered Device-DAX mapping. The CXL pair delivers ≈ 46 GiB/s;
one GPU link cannot ask for more than a quarter of it.

**D.2 A hit on the NVMe tier costs its media read, on every hit, until the GPU saturates.**
*Why:* an SSD tier must first bring the KV into DRAM; how much of a hit is that?
*How:* the same three experiments, O_DIRECT, page cache verified empty, device counters equal to the bytes loaded.
*Result:* 2.9 GiB/s from 512 to 16K tokens and from 1 to 16 concurrent hits; a 16K hit in 290 ms against 93 ms (+197 ms);
TTFT p50 +55–71 % on identical hits at 0.5–4 requests/s; 2.2–2.9× in bursts (940 against 430 ms at k = 16).
*Explanation — the L2 load inside the cache server:* the device is the limit (flat rate, unchanged with 16 I/O threads,
aggregate retrieval rate = media rate, the GPU transfer never queues behind it). It runs on half of its lanes here (G).

**D.3 Behind the same software path, the medium is worth an 11× faster media read.**
*Why:* separate the medium from the path — CXL memory used as an L2, exactly like the files.
*How:* the `dax` L2 adapter over the same 512 GiB, in A, C, D and in the 0.08× replays.
*Result:* media copy at 30–32 GiB/s against 2.9 GiB/s; 8.8 ms against 97 ms per load on the equal-hit mix; a 16K hit on an
idle server in 114 ms (CXL L2) against 290 ms (NVMe) and 94 ms (DRAM or CXL L1); under load within 5 % of DRAM where the NVMe
is 55–71 % above it; in the replays indistinguishable from the NVMe L2 (paired mean difference 0.00 s on the tool-agent
window, −0.03 s on the conversation window).
*Explanation — the L2 path:* an L2 hit pays one copy into a DRAM object and is collected by a later poll of vLLM's scheduler;
at saturation that poll, not the medium, makes the tail (lookup interval p95 1.5 s for the CXL L2 with a 56 ms load).

**D.4 In the replays the extension's value is the recomputation it removes, and the queue passes it on to every request.**
*Why:* what does 512 GiB behind an 80 GiB DRAM tier buy end to end?
*How:* five trace windows replayed open-loop with the same requests in every configuration; hit shares by source, per-request
pairing.
*Result:* cached share 0.096 → 0.238 (conversation, 0.08×), 0.396 → 0.495 (tool-agent), 0.097 → 0.302 / 0.309 (long window);
15.8 %, 16.3 % and 22.7–23.5 % fewer recomputed tokens; TTFT p50 −48 %, −49 %, −57 %; 76–87 % of all requests of the two
conversation windows faster, including those that miss (p50 of misses 17.95 → 10.6 s in the 5,000-s window).
*Explanation — the GPU's prefill queue:* at a utilisation of 0.86–0.88 every prefill that is not computed shortens the wait of
the requests behind it. An extension hit itself still waits 3.3–5.9 s (p50) for the GPU; the gain is not a faster hit but a
less busy GPU (0.88 → 0.78–0.81). At half the rate (busy 0.5) the same tenth of removed work is worth −18 % / −28 % at the
median and −4 % / −6 % at p95.

**D.5 The medium of the extension does not show in the totals of any replay.**
*Why:* D.2 says an NVMe hit is 2–3× slower; does a served trace notice?
*How:* CXL hybrid, CXL L2 and NVMe L2 on the same windows; requests paired by index; the requests that loaded from the NVMe
paired with themselves in the CXL run.
*Result:* equal cached shares and recomputed tokens wherever no extension evicts; all-request TTFT statistics within 1 %
(paired median difference 0.00–0.02 s). The NVMe's load (78–106 ms p50, 328–410 ms p95 inside the cache server) appears only
on hits that find the GPU free: +45 to +116 ms at the median, for 2.5–6.4 % of the requests of a window.
*Explanation — retrieval and queueing overlap instead of adding up:* the L2 load starts with the lookup, which vLLM issues
when the request reaches the scheduler, and the request is served 5–10 s later at the median (377–418 s under overload). A
load of 0.1–1 s inside that interval is free. Averaged over all requests the NVMe's retrieval is 3.5–42 ms of a 5–10 s mean.

**D.6 Where the two extensions do differ in hits, it is the tier's structure, not the medium's speed.**
*Why:* the long window is the only one that fills the extensions.
*How:* 11,250 s of replay, 735 GiB of distinct KV; occupancy and evictions over time; per-request cached tokens.
*Result:* hybrid 0.309, NVMe L2 0.302; 28 requests (1.0 %) keep a hit only in the hybrid, none the other way; mean TTFT
−1.3 %, percentiles equal.
*Explanation — unique capacity:* byte-addressable memory can extend the first level, where an object exists once (592 GiB,
eviction from 473.6); a file tier sits behind the DRAM level and, with write-through, repeats its contents (512 GiB, eviction
from 409.6). With batch eviction the tiers hold 424 and 369 GiB on average, and the offline model read at those values gives
the two measured shares. PENDING-DAXL2-LONG

**D.7 Capacity changes throughput only at saturation, and then equally for both media.**
*Why:* the brief's question 6.
*How:* open-loop replays at 0.04× and 0.08× (GPU busy 0.5 and 0.8–0.9) and at 0.16× (busy 1.00).
*Result:* identical completed requests/s and output tokens/s in every configuration of a window at 0.04× and 0.08×; at 0.16×
0.287 → 0.305 (CXL) / 0.306 (NVMe) requests/s, +6.3 % / +6.5 %, for 9.0 % fewer recomputed tokens.
*Explanation — which side of saturation:* below it, saved prefill becomes idle GPU time and shorter queues; at it, saved
prefill becomes completed work. The medium cannot matter at saturation because the lookup runs minutes ahead of the service.

**D.8 The two places where the CXL configuration is behind are on the GPU's side.**
*Result (store direction):* the GPU writes into CUDA-registered CXL memory at 3.89 GiB/s against 12.14 GiB/s into DRAM (the
read direction is 12.4 GiB/s for both); in the replays the hybrid's prefill of identical-work requests is 0.2–0.7 % longer
once its DRAM part is full, and its mean TTFT 0.07–0.13 s later than the NVMe configuration's at 0.08× (2.4 s at 0.16×).
*Explanation:* stores share the transfer thread and the GPU with the prefill that produces them; the device-initiated write
into the CXL window is the slow step (through the unregistered path the same store runs at 11.5 GiB/s). The cause below that
level was not isolated. PENDING-DRAM592
*Result (GPU memory):* registering 592 GiB of host memory with CUDA takes 1.2 GiB of the 8 GiB card; every configuration of
this study therefore runs with a GPU KV pool of 6,400 instead of 7,456 blocks.
*Explanation:* 2.03 MiB of GPU memory per GiB registered (8 bytes per 4 KiB page, A.4), the same for pinned DRAM and for a
Device-DAX mapping — a cost of the registered-memory design per GiB of host memory, not of CXL; 1.3 % of a 94 GiB card.

**D.9 Sustained overload breaks the stock stack for a reason that has nothing to do with the medium.**
*Result:* with default settings the engine died in both attempts at 0.16×, on the same request, 314 s after its lookup.
*Explanation — a timeout meeting a failure path:* LMCache's read lock on looked-up chunks lasts 300 s; a chunk whose lock has
expired is refused at the retrieve although it is still in the cache; vLLM 0.31.0 fails the request by default and then trips
an assertion. Under overload more than half of the requests wait longer than 300 s between lookup and service (C.4.5).

**D.10 The traffic on the CXL memory is far from its limits, and its two directions never meet on the hybrid's path.**
*Result:* averages of 11–18 MiB/s read and 53–74 MiB/s written; largest second 2.1 GiB read, 0.25 GiB written — under 5 % of
the pair's bandwidth; copy-level overlap of reads and writes 0.00 s in every hybrid run.
*Explanation — one GPU and one transfer thread:* writes are paced by this GPU's prefill (≈ 7,300 tokens/s at most), reads by
its link, and LMCache serialises the two on a single thread. Whether the medium's duplex behaviour matters is decided by the
number and speed of the GPUs in front of it, which this node cannot vary.

## E. Cross-experiment analysis

**E.1 Cache capacity ↔ hit rate.** Measured cached share of the prompt tokens against the KV capacity of the configuration
(GPU pool 3.52 GiB + what the host tiers hold at their eviction trigger), next to the offline LRU model of the same window
(C.6; a model):

| window | vLLM alone, 3.5 GiB | + 80 GiB DRAM (64 effective) | + 512 GiB L2 (409.6 effective) | hybrid L1 (473.6 effective) | model at 64 / 409.6 / 473.6 GiB |
|---|---|---|---|---|---|
| conversation 0–200 s, 0.04× | – | 0.093 | 0.182 (NVMe) | 0.182 | 0.100 / 0.183 / 0.183 |
| conversation 0–400 s, 0.08× | 0.045 | 0.096 | 0.238 (NVMe, CXL) | 0.238 | 0.101 / 0.239 / 0.239 |
| conversation 0–900 s, 0.08× | – | 0.097 | 0.302 (NVMe) PENDING-DAXL2-SHARE | 0.309 | 0.101 / 0.309 / 0.312 |
| tool-agent 0–200 s, 0.04× | – | 0.383 | 0.446 (NVMe) | 0.446 | 0.389 / 0.447 / 0.447 |
| tool-agent 0–400 s, 0.08× | 0.274 | 0.396 | 0.495 (NVMe, CXL) | 0.495 | 0.400 / 0.496 / 0.496 |
| conversation 0–400 s, 0.16× (overload) | – | 0.130 | 0.209 (NVMe) | 0.208 | 0.101 / 0.239 / 0.239 |

Below saturation the hit rate is a function of capacity and of the trace, and of nothing else: every measured point is on
the model's curve within 0.7 points, whichever medium provides the capacity. The three deviations have causes in the serving
system, not in the medium — the DRAM tier sits 0.4–0.7 points under the model, consistent with its eviction in rounds (it holds 51–64 GiB, not 64); vLLM alone on the
tool-agent trace sits 7.7 points under it because under a backlog of 103 requests the GPU pool holds running requests instead of old
prefixes; and under overload the shares move in opposite directions (0.130 instead of 0.096, 0.208 instead of 0.238) because
the lookup runs minutes ahead of the service (C.4.5). The capacity that matters grows with the length of the window:
everything reusable in 200 trace seconds fits in 160 GiB, 900 s still gain 2.4 points beyond 320 GiB, and the model's curve
for an hour is still rising at 592 GiB.

**E.2 Hit rate ↔ avoided prefill ↔ latency.** A point of cached share is a point of the prompt tokens that the GPU does not
compute; what that is worth depends on how busy the GPU is.

| window | GPU busy, DRAM only → with extension | recomputed tokens | TTFT p50 | TTFT mean | TTFT p95 | completed req/s |
|---|---|---|---|---|---|---|
| conversation 0.04× | 0.51 → 0.49 | −9.8 % | −18 % | −10 % | −4 % | = |
| tool-agent 0.04× | 0.50 → 0.48 | −10.2 % | −28 % | −11 % | −6 % | = |
| conversation 0.08× | 0.88 → 0.81 | −15.8 % | −48 % | −41 % | −32 % | = |
| tool-agent 0.08× | 0.86 → 0.79 | −16.3 % | −49 % | −42 % | −34 % | = |
| conversation 0.08×, long window | 0.88 → 0.78 | −22.7 % / −23.5 % | −57 % | −54 % | −47 % | = |
| conversation 0.16× | 1.00 → 1.00 | −9.0 % | −8 % | −10 % | −14 % | +6.3 % / +6.5 % |

The same tenth of removed prefill is worth a few percent at the tail when the GPU is half idle, half of the TTFT when it is
busy 88 % of the time, and throughput instead of latency once it is saturated. The latency gain comes through the queue (D.4),
so it is largest where the queue is long but still drains.

**E.3 Retrieval latency ↔ TTFT.** On identical hits the NVMe tier's TTFT is 1.2× (512 tokens) to 3.1× (16K tokens) that of
DRAM or CXL L1 on an idle server and 2.2–2.9× in bursts; how much of that becomes TTFT in serving depends on whether the
request would have waited anyway.

| situation | retrieval, NVMe vs. CXL L1 | effect on TTFT |
|---|---|---|
| idle server, one 16K hit (A) | 197 ms against 1 ms before the GPU copy | 290 against 93 ms (3.1×) |
| identical hits, Poisson 0.5–4 req/s (C) | L2 load 97 ms p50 | p50 +55 % to +71 %, mean ×2 at the lowest rate |
| identical hits, saturated at 8 req/s (C) | lookup interval 576 against 16 ms p50 | p50 +23 %, throughput −4 % |
| trace replay, hits that find the GPU free (B) | load 78–106 ms p50 | +45 to +116 ms at the median (+15 to +36 %), 2.5–6.4 % of the requests |
| trace replay, all requests (B) | load 78–106 ms p50, 328–410 ms p95 | within 1 %; 3.5–42 ms of a 5–10 s mean |
| trace replay under overload (B) | load 301 ms p50, 712 ms p95 | none: the load ends minutes before the service |

**E.4 Concurrent retrieval ↔ performance.** In bursts of k simultaneous hits (D) the tiers are limited by different parts
of the path: DRAM and CXL L1 by LMCache's single GPU-transfer thread and the GPU link (7.0–9.7 GiB/s aggregate; the wait for
the transfer grows from 2.5 to 302 ms at k = 16), the CXL L2 by LMCache's four load workers (media copies still at
30 GiB/s), the NVMe by the device (2.9 GiB/s at any k; TTFT 2.2× DRAM at k = 16). In the replays such bursts are rare: a
retrieve operation is open during 42–86 s of a 5,000-s replay at 0.08× (266 retrieves in the conversation window, 658–669 in
the tool-agent window), so concurrent retrievals are an exception, and the concurrency experiment describes a regime the
traces reach only in their largest bursts. Where the GPU is the limit (C at 8 requests/s, the overload round), all cached
configurations converge.

**E.5 CXL write traffic ↔ cache admission.** No admission policy runs in this study: LMCache stores every chunk the GPU
computes, so the write traffic on the extension is the prefill traffic — 109–280 GiB per 5,000-s replay, 594 GiB in the long
window, at most 0.25 GiB in any second. Of the distinct chunks written, a later lookup of the same window finds 14–21 %
again; 79–86 % of the bytes are never read back within the window (a bound that the window length censors: 0.19 after
5,000 s, 0.21 after 11,250 s). The writes are also the direction in which the GPU ↔ CXL path is slow (3.89 GiB/s) and the one
place where the hybrid measurably costs prefill time (D.8). The two facts point the same way: what an admission policy could
remove from the CXL memory is up to four fifths of its writes, and those writes are the hybrid's only measured cost. This
study did not run such a policy (the brief excludes it); the 2026-11-10 study did, for DRAM.

**E.6 NVMe bandwidth limits ↔ serving behaviour.** Through LMCache with O_DIRECT the device reads at 2.9 GiB/s (a quarter
of the GPU link) and absorbs stores at 0.92–0.96 GiB/s while busy. In the replays at 0.08× and 0.16× it is being written 7–10 % of the time and
read 0.3–0.7 %; loads next to a store task are 0–11 % slower, and under overload the median load takes 301 instead of 106 ms.
None of this limits serving here, for two reasons that are properties of this node's GPU rather than of SSDs in general: the
write rate is bounded by what one RTX 4060 Ti prefills (0.07–0.09 GiB/s on average at 0.08× and 0.16×, 0.25 GiB in the busiest second — a quarter
of the device's store rate), and reads are hidden behind the wait for the same GPU (E.3). The NVMe's read limit becomes the
serving limit only when hits are frequent, large and not queued — the conditions of Experiments C and D, not of the replayed
traces.

## F. Negative results

Stated without qualification; each is a measured outcome of this study.

1. **In none of the replays does the CXL extension give a better end-to-end result than the NVMe extension because of its
   speed.** Four 5,000-s windows (two traces, two rates), one long window and one overload round: cached share and recomputed
   tokens are equal wherever no extension evicts, every all-request TTFT statistic agrees within 1 %, completed requests/s are
   equal, and the paired per-request difference has a median of 0.00–0.02 s. The NVMe's slower read is visible only on hits
   that find the GPU free (+45 to +116 ms at the median, 2.5–6.4 % of the requests).
2. **The CXL hybrid is the slower configuration of the two by a small, consistent margin whenever the hit rates are equal:**
   +0.07 s (conversation) and +0.13 s (tool-agent) mean TTFT at 0.08×, +0.06 s in the first 6,000 s of the long window, +2.4 s
   (+0.3 %) under overload, where 81 % of the requests are later with the hybrid. Its prefill of identical-work requests is
   0.2–0.7 % longer; the identified candidate is the store direction into CUDA-registered CXL memory (3.89 GiB/s against
   12.14 GiB/s into DRAM). PENDING-DRAM592-F
3. **The one case in which the CXL configuration has more hits is a capacity effect.** Long window: 0.309 against 0.302,
   28 requests of 2,728, −1.3 % mean TTFT, equal percentiles. It comes from the hybrid being one exclusive level of 592 GiB
   against an inclusive second level of 512 GiB. PENDING-DAXL2-F
4. **Behind the same software path, CXL memory buys nothing over the NVMe in the replays.** As an L2, the CXL memory loads a
   prefix 8–9× faster than the files (12–13 ms against 104–106 ms at the median), and the two L2 configurations are
   indistinguishable in both 0.08× windows (paired mean difference 0.00 and −0.03 s).
5. **Capacity does not raise throughput at sustainable load.** At 0.04× and 0.08× every configuration — including vLLM alone
   — completes the same requests and output tokens per second. Throughput follows the cache only at saturation (+6.3 % /
   +6.5 % at 0.16×).
6. **Under overload the GPU remains the bottleneck with any cache.** TTFT is 13–14 minutes at the median in every
   configuration; 512 GiB of extension remove a tenth of it. The extension is also less effective there than at 0.08× (0.208
   instead of 0.238 of the prompt tokens), because lookups run minutes ahead of the service.
7. **The stock stack does not survive sustained overload with any host cache.** Both attempts with default settings lost
   vLLM's engine (read lock of 300 s; failure policy `fail`; assertion). The overload results exist only with two changed
   settings.
8. **Capacity beyond what the window reuses is unused, and most of what is stored is never read.** In the 200-s and 400-s
   windows 152–323 GiB of the 512 GiB stay empty; 79–86 % of the bytes written to an extension are not found again within the
   window (79 % after 11,250 s).
9. **Registered CXL memory costs GPU memory that an 8 GiB card cannot spare.** 1.2 GiB for the 592 GiB hybrid; the GPU KV
   pool of every configuration is 14 % smaller than in the previous study because of it. An unregistered arena avoids the cost
   and the slow store direction, at +1–3 ms per hit and a core of CPU during stores (A).
10. **No evidence that concurrent read and write traffic on the CXL memory matters for this workload.** Copy-level overlap is
    0.00 s on the hybrid's path in every run; the busiest second is under 5 % of the pair's bandwidth. The one interference
    that was measured (CXL L2 loads at half their rate next to a store) affects about a second of loads per replay, and its
    cause was not separated from CPU contention.
11. **At saturation with identical hits, the tiers converge** (Experiment C at 8 requests/s: 5.0–5.3 requests/s in every
    cached configuration, the NVMe 4 % behind).

## G. Limitations

- **One small GPU, one small model.** RTX 4060 Ti, 8 GiB, PCIe 4.0 ×8 (12.4 GiB/s host-to-GPU), Qwen2.5-3B (36 KiB of KV per token).
  The GPU link, not the memory tier, bounds every L1 hit here; a faster link (PCIe 5.0 ×16, ≈ 4–5× the rate) moves the bound towards
  the medium, and a 70B fp16 model has ≈ 9× the bytes per token. The ratios between tiers will change with both; nothing here
  predicts an H100. **No multi-GPU claim is made** — with several GPUs reading one CXL pair, the pair's ≈ 46 GiB/s would be shared,
  which this study cannot observe.
- **The GPU KV pool is 14 % smaller than in the previous study (6,400 against 7,456 blocks) in every configuration**, because the
  CUDA registration of 592 GiB of host memory takes 1.2 GiB of the 8 GiB card. The cost is caused by the hybrid-L1 design alone but is
  carried by all configurations, so that the GPU budget is equal; a configuration that registers only 80 GiB could have kept the
  larger pool. On a 94 GiB GPU the same registration is 1.3 % of the memory.
- **The NVMe device runs on half of its lanes** (PCIe 4.0 ×2 of ×4; 2.9 GiB/s through LMCache with O_DIRECT). This is the SSD c28
  has; a ×4 link or a striped set would roughly double or more the read rate and shrink the NVMe penalty accordingly. The ext4 file
  system, one file per 9 MiB chunk and LMCache's adapters are part of what was measured; `fs_native` and the Python adapter differ by
  10 %, and 16 I/O threads change nothing (the device is the limit).
- **`dax0.0` and `dax1.0` are one interleaved pair of cards.** The 512 GiB extension is two address windows over the same two CZ120
  devices; nothing here measures independent CXL devices, a CXL switch, or CXL as a NUMA node (the devices are Device-DAX only).
- **The DRAM budget is enforced at the cache level, not physically.** The node has 755 GiB; the 80 GiB is LMCache's L1 size. What the
  cache server really held is reported per run (resident memory, page cache, device counters); the OS was free to use the rest of the
  memory for anything else, and with O_DIRECT it did not use it for the KV files.
- **Replays are time-scaled windows of two traces**, one run per cell: trace seconds 0–400 at 0.08× and 0–200 at 0.04× of both
  traces (5,000 wall-seconds each), and of the conversation trace also 0–900 at 0.08× (11,250 s) and 0–400 at 0.16×. Prompts are
  rebuilt from the traces' hash blocks as pseudo-random tokens, outputs are capped at 1,024 tokens, and every window starts with an
  empty cache. Only the long conversation window (735 GiB of distinct KV) fills the 512 GiB extensions and makes them evict; the
  tool-agent trace was not replayed over a window that does, and reuse that needs more than an extension holds exists only in
  still longer windows (trace model, C.6 — a model, not a measurement). Run-to-run variation was not measured in this study (in
  the 2026-11-10 study repeated replays on this node agreed within 1 % on the all-request means); differences of about 1 % between
  two configurations are therefore reported as "equal" unless a paired per-request comparison supports them.
- **The two CXL configurations do not have the same unique capacity as the NVMe configuration.** The hybrid L1 holds every object
  once in 592 GiB (eviction from 473.6 GiB); an inclusive 512 GiB L2 evicts from 409.6 GiB. Where the extensions fill (C.4.4) part
  of the hybrid's advantage is this difference in tier structure; the CXL L2 run is the equal-capacity partner of the NVMe run.
- **The sustained-overload round ran with two non-default settings** (LMCache `--l1-read-ttl-seconds 7200`, vLLM
  `kv_load_failure_policy=recompute`) in all three configurations, because with the defaults the engine dies once a request with a
  host hit has waited more than 300 s (C.4.5). The long read lock also keeps looked-up chunks from being evicted for the whole wait,
  which is part of what that round measures.
- **Physical accesses to the CXL cards were verified by content and by residency, not by hardware counters.** The memory-controller
  and CXL counters need privileges the user does not have (`perf_event_paranoid=2`). What is established: the bytes are in the device
  mapping (independent hashes), they are nowhere else (resident memory), and the copies that touch them are timed individually. The
  traffic numbers of Experiment E are therefore the application's copies into and out of the device mapping, with their exact
  intervals — not the cards' own view of the load.
- **LMCache 0.5.5's tiers as they are.** No admission policy, no demotion or promotion between DRAM and CXL in the hybrid L1, no
  replacement algorithm was added (the brief excludes it). The L2 tiers ran with the default write-through and no promotion; the
  `retain` prefetch policy was not part of the main matrix.
- **The store-counter fix is not stock.** Every LMCache configuration runs with the one-line repair of 2026-11-10; without it the
  stores that follow waiting hits are lost under overload (31–33 % in that study), which would have penalised every tier alike.

## H. Final answers

**1. What is the strongest evidence supporting CXL memory expansion for LLM serving?**
Two findings, of different kinds. For *expansion*: with the DRAM KV budget fixed at 80 GiB, 512 GiB more cache removes
16–24 % of the GPU's prefill work in the windows replayed at high load (a tenth at half the rate and under overload), roughly
halves TTFT there (p50 −48 % to −57 %, mean −41 % to −54 %) and raises completed work by 6 % once the GPU is saturated — the
largest effect on the longest window. For *CXL as
the medium of that expansion*: a KV hit served from CXL memory is indistinguishable from one served from DRAM — 93–94 ms for
a 16K-token prefix, every quantile within 1–2 % under load and in bursts of 16 — with the bytes verified to be on the
device and nowhere else. No other extension medium in this study has that property; the NVMe tier's hits are 1.2–3.1× slower
on identical requests.

**2. In which workload regimes is CXL better than NVMe?**
Where a hit is not queued behind the GPU. With identical hits and a GPU that is not saturated the NVMe tier's TTFT is 55–71 %
higher at the median (Experiment C, 0.5–4 requests/s) and 2.2–2.9× in bursts of simultaneous hits (D); the gap grows with the
prefix (+197 ms at 16K tokens). In the trace replays this regime is 2.5–6.4 % of the requests — the hits that find the GPU
free, 45–116 ms faster from CXL at the median. CXL is also ahead when the cache fills, by the capacity that its first-level
integration adds (0.309 against 0.302 of the prompt tokens in the long window). It is **not** better at high load with queues
(all statistics within 1 %), and under sustained overload the NVMe configuration is ahead by 0.3 %. PENDING-SENS-H2

**3. What accounts for that difference?**
One extra stage and its rate: an SSD hit must be read into DRAM at 2.9 GiB/s (this device, on two of its four lanes) before
the GPU can take it, while the GPU copies from CXL memory directly at the rate of its own link (12.4 GiB/s). Whether that
stage is on the critical path decides everything else: LMCache starts the read at the lookup, and a request that then waits
seconds for the GPU does not notice it. The capacity difference is structural — byte-addressable memory can extend the first
cache level, where each object exists once; a file tier is a second level that repeats what the first holds.

**4. Can SSD caching provide similar end-to-end performance with a sufficiently optimized pipeline?**
On this node and these traces it already does, with LMCache's stock native file adapter and O_DIRECT: the same hit rates and
TTFT within 1 % of the CXL configurations in every replay, at high load, half load and overload. What makes that possible is
visible in the measurements — the load is started at lookup time and overlaps the wait for the GPU, stores go to DRAM first and
reach the SSD from CPU threads off the GPU's path, and the DRAM level serves the most recent 64 GiB itself. What a pipeline
cannot remove is the device's read rate: more I/O threads and more prefetch slots changed nothing (2.9 GiB/s at any
concurrency), so for hits that are not queued the gap of answer 2 remains. A faster device (four lanes, or a striped set)
would shrink it proportionally; that was not measured.

**5. What are the dominant bottlenecks after expanding cache capacity?**
The GPU, in three forms. (a) Prefill of what is still not cached: 76 % (conversation) and 50 % (tool-agent) of the prompt
tokens after expansion, at a GPU utilisation of 0.78–0.81; an extension hit still waits 3.3–5.9 s (median) for the GPU. (b)
The reuse the trace contains: with unlimited capacity the model's ceiling is 0.18–0.32 (conversation) and 0.45–0.50
(tool-agent) of the prompt tokens for the replayed windows. (c) On the hit path itself, the GPU's link and LMCache's single transfer
thread (7.0–9.7 GiB/s aggregate for concurrent hits), not the memory behind them. Under overload two properties of the stack
are added: the lookup runs minutes ahead of the service and misses what is stored in between (0.238 → 0.208), and the default
read-lock lifetime ends the engine.

**6. Does CXL read/write concurrency appear relevant?**
Not on this evidence. Retrieval and persistence meet as operations all the time (40–47 % of the retrieves at 0.08× and 0.16×
find a store pending) but never as copies on the hybrid's path, which one thread serialises; the traffic averages 2–18 MiB/s
of reads and 22–74 MiB/s of writes, and the busiest second is under 5 % of the pair's bandwidth. One GPU of this size cannot
generate the traffic at which the medium's duplex behaviour would be tested.

**7. What concrete systems research problem remains after the comparison?**
The comparison itself is closed for this node: expansion is worth having, and CXL does not beat a properly configured SSD tier
end to end on these traces. What the measurements leave open, without implying an architecture:

- *Hits that are not queued.* CXL's advantage exists per hit and disappears behind the GPU queue. Whether it matters end to
  end is a question about serving points where retrieval is on the critical path — hit-dominated workloads, a GPU with spare
  capacity, a faster GPU link — which a single RTX 4060 Ti reaches only in the equal-hit experiments.
- *When the lookup happens.* The cache is consulted when the scheduler first sees a request and the result is used when the
  request is served. Under overload the two are minutes apart: hits are missed (3 points of the prompt tokens), looked-up
  chunks must be held for the whole wait, and the stock timeouts turn that into a crash.
- *What is written.* Four fifths of the KV written to the extension are not read again within the window, and the store
  direction is the only measured cost of the CXL path. The 2026-11-10 study examined admission for the DRAM tier.
- *What registered memory costs the GPU,* and the related choice between an exclusive first level (more unique capacity,
  GPU memory per registered GiB, slow device-initiated writes) and an inclusive second level (none of the three, one copy more).
- *More or faster GPUs on one CXL pair* — the configuration in which the pair's bandwidth and its read/write interference
  could become limits — is outside what this node can measure.

## I. Correctness and experimental validity (the brief's section 15)

| # | requirement | how it was checked | result |
|---|---|---|---|
| 1 | CXL-resident KV is physically placed on the selected CXL DAX region | independent read-only mapping of the device, SHA-1 of the recorded ranges (`verify_residency.py`), right after each validation run; LMCache's own medium tag for every L1 object in every run | 85 / 85, 155 / 155, 35 / 35 (L1 objects); 340 / 340, 592 / 592 (L2 slots); in A, C, D every chunk of every measured CXL hit carries the `devdax` tag or an L2 load task (tables: "chunks DRAM / DAX / L2") |
| 2 | no silent DRAM copy of CXL data | resident memory of the cache server at 1 Hz against the KV held | pure DAX L1: 0.50 GiB resident with 2.99 GiB of KV on CXL; hybrid: the DRAM part only. The DAX **L2** path copies each hit into a DRAM L1 object by design — inside the 80 GiB budget, reported as such |
| 3 | DRAM-only stays within the 80 GiB cache budget | `--l1-size-gb 80`; occupancy from `/status`; resident memory | L1 occupancy ≤ 64 GiB (the 0.8 trigger) in every replay; resident memory 80.5 GiB (the pinned L1 itself); C.4 |
| 4 | NVMe reads are not page-cache hits | O_DIRECT in both adapters; `mincore` over the cache files; `/proc/diskstats`; page-cache growth per run; a buffered control | 0.00 % of file pages cached; device bytes read = bytes loaded; no page-cache growth in any NVMe run (C.4); the buffered control fails all three checks as it should |
| 5 | CXL and NVMe configurations have equal total cache capacity | configuration (512 GiB extension each) and occupancy over the run | `daxl2` and `ssdn`: identical (512 GiB inclusive L2, same watermark). `hyb`: 592 GiB exclusive L1 — 80 GiB more unique capacity (eviction from 473.6 instead of 409.6 GiB). In the four 5,000 s windows and in the overload round no extension reaches its watermark, so the difference never becomes a difference in contents; in the long window it does, and C.4.4 reports the hybrid's advantage there as a capacity effect, with the CXL L2 run as the equal-capacity partner of the NVMe run; stated in the limitations |
| 6 | the same requests in every configuration | seeded prompts, seeded arrival instants; the replay sends request i at its trace instant whatever happened before | request counts and prompt-token totals equal across the configurations of a group (C.2: also cached tokens and retrieved bytes; C.4: `n` and prompt tokens) |
| 7 | equal-hit experiments retrieve identical bytes | sums per rate and per burst | 737,280 cached tokens and 25,920 MiB per rate in all five tiers of C; equal byte totals per (L, k) in D |
| 8 | the GPU KV state is controlled | flush with 8 × 16,320 tokens (130,560 > the 102,400-token pool) before every measured hit / pass / burst | no GPU-prefix hit among the measured requests of A (host case), C and D |
| 9 | same GPU KV budget | `--num-gpu-blocks-override 6400` in every run | recorded in every run's `meta.txt` |
| 10 | the cache-correctness fix is applied equally | `KVADM_POLICY=storefix` in the vLLM environment of every LMCache configuration (plan file, `meta.txt`) | all LMCache runs; vLLM alone has no store path |
| 11 | failed requests are reported | status, error and output tokens of every request in `client.jsonl`; a request counts as completed only with HTTP 200, no error and at least one output token | A, C, D and every replay used as a result: none. Two replays lost vLLM's engine (sustained overload with default settings, C.4.5): 243 of 1,177 requests completed in the DRAM-only one; both are void and kept in `void/` |
| 12 | cache eviction is monitored | L1 / L2 eviction events with the medium; occupancy every 5 s | per run in C.4; the extension tiers' eviction paths exercised in B0 (2,200 L2 keys, 9.75 GiB of CXL L1 objects) |
| 13 | CXL integration correct, no DRAM measurements passed off as CXL | items 1 and 2; every CXL number in this report comes from a run on `/dev/dax1.0` / `/dev/dax0.0` | no DRAM stand-in is used anywhere in this study (unlike 2026-11-04 and 2026-11-10) |
| – | outputs unaffected by the tier | SHA-1 of the generated text of every request, compared with the DRAM run of the same experiment (temperature 0; `check_outputs.py`) | A (host hits): identical in all six cached tiers (30 / 30 each). C: CXL hybrid 384 / 384, CXL L2 381 / 384, NVMe 380 / 384 — the few differences come with different batch compositions, not with the medium (a loaded chunk is the stored chunk). D: 248 / 248 in every tier. Against recomputation the text differs more often (A: 29 of 30 prompts give the same text loaded and computed; C under load: 49 of 96), which is vLLM's batching and fp16 arithmetic, as in the 2026-11-10 study. B (replays, `check_outputs.py` on the client records): the output length of every request is the same in every pair of configurations of a window; the text is identical for 99.2 % of the requests between two extension configurations, for 98.5–98.7 % between an extension and DRAM only (conversation 0.04×), and for 97.0–98.0 % between a cached configuration and vLLM alone (conversation and tool-agent 0.08×). The pairs that differ only in the medium of the extension agree most often; the pairs whose cached shares, and with them the batches, differ most agree least |

Invalid or void runs, kept and excluded: `void/` (full hybrid with 7,456 GPU blocks: vLLM could not start; the nine runs behind it
ran against a left-over server; the two sustained-overload replays with default settings, `b-conv16-dram80` and `b-conv16-hyb`, in
which vLLM's engine died — diagnosis in C.4.5) and the first hour's smoke runs `P0/p0-*-s` (residency checked too late). Problems found and fixed
before the measurements: a failed start left the cache server running (the harness now cleans up and refuses busy ports); with
`skip_l1`, repeating a prompt before its L2 store has finished leaves chunks in L1 (the drivers now wait for the store controller).

## Change history

- 2026-11-14: draft committed while the last replays of Experiment B were still running (marked PENDING in the text).
