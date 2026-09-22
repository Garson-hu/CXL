# Benchmark and application survey for the cxlpath evaluation

Compiled 2026-09-21. Method: every paper row below was filled from the paper PDF itself (downloaded and text-searched), its artifact repository, or official docs; the URL used is in the row. Where I could only reach an abstract or a secondary page, the cell says **not verified**. Nothing is filled from memory unless explicitly flagged as such. Two facts were measured directly on c28 on 2026-09-21: `nvidia-smi` reports the RTX 4060 Ti as 8188 MiB, PCIe Gen4 x8 max, compute capability 8.9.

Abbreviations: TTFT = time to first token; TBT/ITL/TPOT = time between tokens; RSS = resident set size; MLC = Intel Memory Latency Checker.

---

## 1. CXL / tiered-memory systems

| Paper (venue) | Applications / benchmarks (datasets, sizes) | Metrics | Hardware (real vs emulated CXL) | Baselines | Bandwidth-bound victims / co-location experiment | URL used |
|---|---|---|---|---|---|---|
| **TPP** (ASPLOS'23) | Meta production services: Web1 (HHVM), Web2 (Python), Cache1, Cache2, Data Warehouse, Ads. Sizes not stated. | App throughput normalized to all-local; fraction of accesses served from local node; promotion/demotion counts | Pre-production x86 CPU + FPGA-based CXL 1.1 card; also dual-socket with one socket's cores disabled | Default Linux, NUMA Balancing (AutoNUMA), AutoTiering, TMO | None | https://ar5iv.labs.arxiv.org/html/2206.02878 |
| **Pond** (ASPLOS'23) | 158 workloads: Redis, VoltDB, TPC-H on MySQL, Spark, GAPBS, SPLASH2x, SPEC CPU 2017, PARSEC, Azure-internal | Normalized slowdown; tail latency / runtime / throughput per workload; DRAM savings | 2x Skylake 8157M (384 GB/socket) or 2x EPYC 7452; **emulated** CXL = CPU-less remote socket (78 ns vs 142 ns) | All-local-DRAM VM; static pool fraction | "GAPBS workloads generally see higher slowdowns". No co-location. | https://ar5iv.labs.arxiv.org/html/2203.00241 |
| **HeMem** (SOSP'21) | GUPS microbenchmark; TPC-C on Silo; FlexKVS; GapBS (graph) | GUPS/s, runtime, throughput, tail latency under performance isolation, NVM wear | 1 socket Cascade Lake 24c, 192 GB DDR4 + 768 GB Optane (real NVM, no CXL) | Optane Memory Mode (hardware), Nimble (OS). Other baselines: **not verified** (full paper paywalled) | KV-store isolation experiment (tail latency) per abstract; details **not verified** | https://nvmw.ucsd.edu/nvmw2022-program/nvmw2022-data/nvmw2022-paper4-final_version_your_extended_abstract.pdf ; https://sysartifacts.github.io/sosp2021/summaries/hemem |
| **MEMTIS** (SOSP'23) | 8 benchmarks, 20 threads: Graph500 (66.3 GB), PageRank/GAP on Twitter (12.3 GB), XSBench (63.4 GB), Liblinear KDD12 (67.9 GB), Silo YCSB-C (58.1 GB), Btree (38.3 GB), 603.bwaves (11.1 GB), 654.roms (10.3 GB) | Performance normalized to all-NVM (THP on); tier ratios 1:2, 1:8, 1:16 | Xeon Gold 5218R, 6x16 GB DDR4 + 6x128 GB Optane per socket; CXL **emulated** (remote NUMA, 177 ns) | AutoNUMA, AutoTiering, Tiering-0.8, TPP, Nimble, HeMem | None. SPEC pair chosen "since they are the only ones that consume more than 10GB" | https://multics69.github.io/pages/pubs/memtis-lee-sosp23.pdf |
| **Colloid** (SOSP'24) | GUPS (72 GB working set, 24 GB hot set, 15 cores); GAPBS PageRank on Twitter; Silo YCSB-C (400M KV, ~60 GB); CacheLib/CacheBench HeMemKV (~75 GB) | Throughput, execution time, convergence time, vs contention intensity | 2x Xeon Platinum 8362 (32c), 8 DDR4-3200 channels; alternate tier = remote socket over UPI (**emulated**, 70 vs 135 ns) | HeMem, TPP, MEMTIS, each with/without Colloid | **Yes — the whole evaluation is a co-location study.** Memory antagonist on 5/10/15 cores doing sequential 1:1 read/write on a 500 MB buffer pinned to the default tier = 0x/1x/2x/3x intensity = 0/51/65/70 % of bandwidth | https://www.cs.cornell.edu/~ragarwal/pubs/colloid.pdf |
| **Nomad** (OSDI'24) | Zipfian microbenchmark (WSS 10 / 13.5 / 27 GB); Redis + YCSB-A (13/24/36.5 GB RSS); PageRank 2^26 vertices (22 GB); Liblinear | Bandwidth GB/s, ops/s, runtime, promotions/demotions, migration success rate | 4 platforms: SPR + Agilex-7 FPGA CXL 16 GB (A, B); Cascade Lake + Optane (C); **AMD Genoa + 4x Micron CXL 256 GB (pre-market)** (D) | TPP, Memtis-Default, Memtis-QuickCool, no-migration | None | https://arxiv.org/html/2401.13154 |
| **Memstrata / Intel Flat Memory Mode** (OSDI'24) | **115 workloads** in VMs: DaCapo, Renaissance, Ruby YJIT, DeathStarBench (web); TPC-C on Silo, TPC-H on PostgreSQL; DLRM; YCSB on FASTER/Redis/memcached; HiBench on Spark; GAP; SPEC CPU 2017 | Slowdown vs all-local DRAM; outlier = slowdown > 5 %; estimator accuracy; parameter sensitivity (§6.3) | Pre-production Xeon 6, 128 GB DDR5 + 128 GB CXL on 3 Astera Leo x16 cards (**real**), ~50 GB/s per card | TPP (guest), hardware-tiering only, CXL-only, all-local | **Noisy-neighbour VM running 6-thread Intel MLC** sized to the victim VM. Worst outlier: **649.fotonik3d_s**. Workloads split into train/test sets for the slowdown estimator | https://www.usenix.org/system/files/osdi24-zhong-yuhong.pdf |
| **Demystifying CXL Memory** (MICRO'23) | Microbench: `memo`, Intel MLC. Latency-sensitive: Redis + YCSB-A, DeathStarBench (compose posts / read timelines / mixed), FIO. Throughput: **DLRM inference (MERCI setup)**, SPECrate 2017 **fotonik3d, mcf, roms, cactuBSSN** (the four highest-MPKI) | p99 latency, throughput, bandwidth efficiency | 4th-gen Xeon + 3 **real** CXL devices (ASIC hard-IP and FPGA soft-IP) vs NUMA emulation | Default page allocation vs Caption; Redis+TPP | DLRM + SPEC members presented as the "memory-bandwidth-intensive" class (Caption gains up to 24 %). Multiple SPEC instances co-run. Key claim: real CXL != emulated CXL | https://arxiv.org/pdf/2303.15375 |
| **Dissecting CXL Memory Performance at Scale** (arXiv 2409.14317; published venue **not verified** here) | **265 workloads**: Redis, VoltDB, CloudSuite, Phoronix, GAPBS, PBBS, Spark, GPT-2, MLPerf, Llama, SPEC CPU 2017, PARSEC | Slowdown vs local DRAM; tail latency; stall breakdown | SPR and EMR 2-socket servers + **4 real CXL devices** (3 ASIC, 1 FPGA; CXL-D x16/4 DIMMs 52 GB/s, the others x8/2 DIMMs 18–24 GB/s) | Local DRAM, NUMA | **Names the bandwidth-bound set: 603.bwaves, 619.lbm, 649.fotonik3d, 654.roms need > 24 GB/s and slow down > 50 % when the device saturates.** 519.lbm slowdown comes from store-buffer stalls / RFOs. "Recommendation #1: Tail latency should be used as a key metric" | https://arxiv.org/pdf/2409.14317 |
| **SoarAlto** (OSDI'25) | GAPBS (bc/sssp/tc/pr on urand, kron, twitter; bc-urand 134M vertices, ~20 GB), ML (gpt-2 named), Redis, SPEC CPU 2017; 56 workloads for the predictor; 8 threads, 2.3–21 GB/s, RSS 8–35 GB | Slowdown relative to DRAM-only; pages migrated; sensitivity to AOL thresholds (§6.8) | CloudLab Skylake 2x10c (**emulated**, 90/190 ns, 49/17 GB/s) + local SPR with ASIC 128 GB CXL expander PCIe5 x8 (**real**, 218/26 GB/s) | TPP, Nomad, NBT (Linux NUMA balancing tiering), Colloid, NoTier (first touch) | **§6.9–6.10 bandwidth contention: 0–9 Intel MLC threads (~8 GB/s each, 48 GB/s = 98 % of fast-tier bandwidth, latency 2x) next to bc-urand** | https://www.usenix.org/system/files/osdi25-liu.pdf |
| **M5** (ASPLOS'25) | 12 benchmarks: SPECrate mcf_r, cactuBSSN_r, fotonik3d_r, roms_r (top-4 MPKI, 8 instances each); Redis + YCSB-A; Liblinear KDD12; GAP BFS/SSSP/PR/CC/BC/TC (Twitter, Google graphs); ~8 GB footprints | Execution time / speedup; hot-page identification accuracy | 2x Xeon 6430 + Agilex-7 FPGA CXL (**real** CXL protocol, FPGA device) | ANB (AutoNUMA balancing), DAMON | None | https://jiyuan.is/papers/asplos25-m5.pdf |
| **NeoMem** (MICRO'24) | 8 benchmarks, 32 threads, RSS 10.3–19.7 GB: DeathStarBench, PageRank, XSBench, GUPS, Silo YCSB-C, Btree, 603.bwaves, 654.roms | Geomean speedup; slowdown; parameter sensitivity | SPR + Agilex-7 FPGA CXL 16 GB DDR4-2666; host 4x32 GB DDR5-4800; fast:slow 1:2 default | TPP, AutoNUMA, PTE-scan, PEBS, first-touch | None | https://arxiv.org/pdf/2403.18702 |
| **Performance Characterization of CXL Memory and Its Use Cases** (IPDPS'25; arXiv 2405.14209) | ZeRO-Offload training (BERT 110M–4B, GPT2 4/6/8B); FlexGen inference on an **NVIDIA A10**; HPC: NPB BT, LU, CG, MG, SP, FT + XSBench | Training throughput, step breakdown, runtime | 3 systems (Xeon Gold 6438Y+, Xeon Platinum 8470, EPYC 9354) with 3 vendors' **real** CXL | LDRAM only, LDRAM+RDRAM, LDRAM+CXL, interleave-all, AutoNUMA tiering | **MG is "bandwidth-sensitive", CG "latency-sensitive".** The ZeRO-Offload CPU optimizer is described as **latency**-sensitive (2–18 % slower on CXL), not bandwidth-bound | http://pasalabs.org/papers/2025/IPDPS25_cxl_eval.pdf ; https://arxiv.org/pdf/2405.14209 |
| **Optimizing System Memory Bandwidth with Micron CXL (CZ122)** (arXiv 2412.12491, Intel + Micron) | Intel MLC R/W mixes; Llama-3-8B-Instruct CPU inference (IPEX, bf16, batch 1); FAISS on MS Turing-ANNS 1B; HPC: OpenFOAM, HPCG, Xcompact3d, POT3D | Bandwidth; output-token latency (42.91 -> 36.83 ms, +17 % at 3:1); ms/query (+23 %); HPCG +27 %, POT3D +27 % | Xeon 6 6900P + 8x Micron CZ122 128 GB (**real**, sibling of our CZ120) | DRAM-only vs Linux weighted interleave | All four classes are presented as bandwidth-bound. States LLM token generation is read-only traffic bottlenecked on re-reading weights | https://arxiv.org/pdf/2412.12491 |
| **CXL-Interference** (arXiv 2411.18308; venue **not verified**) | RocksDB, Filebench, MLPerf (filesystem-side victims); GAPBS, Redis (memory-side); FIO; background CXL load/store/non-temporal-store traffic | Throughput / trial-time degradation | 4th-gen Xeon Platinum and Gold systems, **real** CXL | — (characterization); Intel RDT used as mitigation | **Four interference types (CXL<->SSD, CXL<->main memory). Non-temporal stores to CXL hurt filesystem apps by up to 90 %** | https://arxiv.org/pdf/2411.18308 |
| **MT2** (FAST'22; Optane, not CXL) | fio DRAM/NVM read/write tasks; YCSB on RocksDB as latency-critical task; GraphChi as best-effort task; 8 noisy neighbours | Per-task throughput (GB/s), p95 latency | Optane + DRAM server (details not extracted) | No regulation vs MT2 throttling | Canonical victim / noisy-neighbour bandwidth-regulation design | https://ipads.se.sjtu.edu.cn/_media/publications/yijfast22.pdf |

**What the family agrees on.** (i) The common application core is GAPBS (PageRank/BC on Twitter or urand), Silo YCSB-C, Redis + YCSB-A, Liblinear KDD12, XSBench, Btree, GUPS, and SPEC CPU 2017 members (603.bwaves, 654.roms, 649.fotonik3d, 619.lbm, mcf, cactuBSSN). (ii) The accepted way to create controlled bandwidth pressure is an MLC or sequential read/write antagonist on a swept number of cores (Colloid, SoarAlto, Memstrata). (iii) The standard metric is slowdown relative to an all-DRAM run. (iv) The standard kernel baseline set in 2025 is TPP, Nomad, NBT, Colloid, NoTier (SoarAlto).

---

## 2. LLM KV-cache offloading / storage for serving

| Paper (venue) | Engine | Models | Datasets / traces / rates | Metrics | Hardware | Baselines | URL used |
|---|---|---|---|---|---|---|---|
| **vLLM / PagedAttention** (SOSP'23) | vLLM | OPT-13B/66B/175B, LLaMA-13B | ShareGPT and Alpaca lengths, Poisson arrivals at swept request rates; 1-hour traces (15 min for 175B) | Normalized latency (s/token) vs request rate | A100 on GCP A2 instances | FasterTransformer, Orca (Oracle/Pow2/Max) | https://arxiv.org/pdf/2309.06180 |
| **FlexGen** (ICML'23) | FlexGen | OPT-30B, OPT-175B (others **not verified**) | Synthetic prompt/gen lengths; HELM | Generation throughput (token/s), effective batch size | 1x NVIDIA **T4 16 GB**, 208 GB host DRAM | DeepSpeed ZeRO-Inference, HF Accelerate, Petals | https://arxiv.org/pdf/2303.06865 |
| **CacheGen** (SIGCOMM'24) | HF-based + LangChain integration (became LMCache) | Mistral-7B, Llama-34B, Llama-70B (long-context fine-tunes) | 662 contexts: LongChat, TriviaQA, NarrativeQA (LongBench), WikiText | KV size, TTFT, accuracy / F1 / perplexity | 4x A40, 384 GB DRAM, 2x Xeon Gold 6130 | Default uniform 3/4/8-bit quantization; §7.5 also applies CacheGen on top of context-compression baselines H2O and LLMlingua | https://arxiv.org/pdf/2310.07240 |
| **CacheBlend** (EuroSys'25) | vLLM-based | Mistral-7B, Yi-34B, Llama-70B (8-bit for large) | 2WikiMQA, Musique (extended); other datasets **not verified** | TTFT, throughput at equal TTFT, F1 / Rouge-L | Runpod: 2x A40, 128 GB RAM, 1 TB NVMe measured 4.8 GB/s | Full KV recompute, prefix caching (RAM and RAM+SSD), full KV reuse (PromptCache), MapReduce / MapRerank | https://arxiv.org/pdf/2405.16444 |
| **LMCache tech report** (arXiv 2510.09665) | vLLM v0.10.2 + LMCache v0.3.6 | Llama-3.1-8B-Instruct, Sao10K-L3-8B, Llama-3.1-70B, Qwen2.5-Coder-32B, Qwen2.5-72B, Qwen3-Coder-480B-FP8 | Emulated **multi-round QA** (10K-token document + short question per query; 20K for the 8B model; 100 output tokens; 40 initial users + arrival at swept QPS); **LongBench**; vLLM random dataset; production traces of "company F/G" compressed to 1 hour | TTFT, ITL, throughput (QPS) at equal TTFT; per-component delay | **8x H100** (GMI Cloud); CPU offload cap **500 GB** | Basic vLLM (GPU prefix cache), vLLM v0.11.0 native CPU offloading, two commercial endpoints | https://arxiv.org/pdf/2510.09665 |
| **Mooncake** (FAST'25) | Mooncake vs vLLM v0.5.1 | **Dummy model with LLaMA3-70B architecture** (trace replay) | Kimi **conversation** trace (12,031 req, avg in 12,035 / out 343, 40 % cache ratio), **tool&agent** trace (23,608 req, 8,596 / 182, 59 %), **synthetic** (3,993 req, 15,325 / 149, 66 %, Poisson; from ShareGPT + L-Eval + LooGLE) | TTFT, TBT (mean of worst 10 % gaps), **effective request capacity under SLO** (TTFT 30 s; TBT 100/200/300 ms), prefill **GPU time**, **cache hit rate** | 16 nodes x 8 A800-80GB, 4x 200 Gbps RDMA per node | vLLM, vLLM + prefix caching, vLLM + chunked prefill | https://www.usenix.org/system/files/fast25-qin.pdf ; traces https://github.com/kvcache-ai/Mooncake/tree/main/FAST25-release/traces |
| **CachedAttention / AttentionStore** (ATC'24) | Own PyTorch engine, continuous batching | LLaMA-13B, LLaMA-65B, LLaMA-2-70B, Falcon-40B, Mistral-7B (32K) | **ShareGPT: 9K conversations, avg 5.75 turns, ~52K turns; warm up on 10K turns** | Cache hit rate, TTFT, prefill throughput, GPU time / cost | 4x A100-80GB, **128 GB DRAM, 10 TB SSD**, PCIe Gen4 | Recomputation (RE) | https://www.usenix.org/system/files/atc24-gao-bin-cost.pdf |
| **InfiniGen** (OSDI'24) | FlexGen-based | OPT-6.7B/13B/30B, Llama-2-7B/13B | lm-eval-harness few-shot (COPA, OpenBookQA, WinoGrande, PIQA, RTE), WikiText-2, PTB, PG-19 for long sequences | Accuracy / perplexity, wall-clock inference latency vs batch and sequence length | **1x RTX A6000 48 GB**, Xeon Gold 6136, 96 GB DDR4-2666, PCIe 3.0 x16 | UVM, FlexGen, H2O, KV quantization | https://www.usenix.org/system/files/osdi24-lee.pdf |
| **HCache** (EuroSys'25) | DeepSpeed-MII | Llama2-7B, Llama2-13B (1x A100), OPT-30B (4x A100); 16K context | **ShareGPT4** conversations, **L-Eval**; load rate in sessions/s | TTFT, TBT | 4x A100-40G, 256 GB DDR4, 4x Samsung PM9A3 4 TB; sensitivity on A30 / 4090 / H800 | Recomputation (DeepSpeed-MII), KV offload (AttentionStore re-implementation), Ideal | https://arxiv.org/pdf/2410.05004 |
| **IMPRESS** (FAST'25) | Own | OPT-6.7B/13B/30B | PIQA, RTE, COPA, OpenBookQA with 2–10 shared few-shot prefixes (avg 4.8k–5.7k prefix tokens), reuse frequency normally distributed | TTFT, accuracy vs KV retention ratio | 2x EPYC 7763, 128 GB DRAM, 1x A100-80GB, 2 TB SSD (~5 GB/s); 10 GB GPU cache + 32 GB CPU cache | ReComp, AS-like (AttentionStore), AS+H2O+LRU, AS+H2O+LFU | https://www.usenix.org/system/files/fast25-chen-weijian-impress.pdf |
| **SGLang HiCache** (LMSYS blog 2025-09-10; not a paper) | SGLang | DeepSeek-R1-671B, Qwen3-235B-A22B | LooGLE (`loogle_wiki_qa.json`) long-context; multi-turn benchmark with 2048-token requests | TTFT, throughput, hit rate (40 % -> 80 % in a user report) | 8x H20-3e; 8x H800 + 8 RDMA NICs | Recompute / no hierarchical cache; backends 3FS, Mooncake, NIXL, file | https://lmsys.org/blog/2025-09-10-sglang-hicache/ |
| **DistServe** (OSDI'24) | DistServe | OPT-13B/66B/175B | ShareGPT (chatbot), HumanEval (code), LongBench (summarization) | SLO attainment, per-GPU goodput | 4 nodes x 8 A100-80GB, 25 Gbps cross-node | vLLM, DeepSpeed-MII | https://arxiv.org/pdf/2401.09670 |
| **Splitwise** (ISCA'24) | vLLM-based + simulator | Llama2-70B, BLOOM-176B | **Azure LLM inference traces** (code, conversation; 2023-11-11; TIMESTAMP, ContextTokens, GeneratedTokens) | TTFT, TBT, E2E, cost / power | DGX-A100, DGX-H100 VMs on Azure | Homogeneous A100 / H100 clusters | https://arxiv.org/pdf/2311.18677 ; https://github.com/Azure/AzurePublicDataset/blob/master/AzureLLMInferenceDataset2023.md |
| **Beluga** (arXiv 2511.20172; SIGMOD'26 per Related.md) — KV on CXL | vLLM V1 v0.8.5 | Qwen-32B unquantized | **LV-Eval**, plus LV-Eval-2K/4K/8K variants; cache-populate vs cache-hit runs | Avg and P99 TTFT, avg and P99 TPOT, QPS | 2 servers x 8 H20 96 GB, 16 vLLM instances; GPUs access a shared memory pool "through CXL switches" (**real**) | vLLM, vLLM + MoonCake v3.2 over RDMA (through LMCache v0.3.1); local-DRAM and RDMA pools in microbenchmarks | https://arxiv.org/pdf/2511.20172 |
| **TraCT** (arXiv 2512.18194) — KV on CXL | Dynamo v0.5.0 + vLLM v0.10.1.1 | DeepSeek-R1-Distill-Llama-8B | Three workloads A/B/C (input ~4.4k tokens, output ~215); QPS sweep | TTFT CDF (avg, P99), throughput | 2 servers, each **1x A6000 48 GB**, 512 GB DRAM; **Niagara 2.0 CXL Type-3 device (640 ns, 10.1 GB/s by MLC)**, 64 GB shared. Note: Related.md lists this as emulated; the paper text says a real device measured with MLC | NIXL/UCX over 100 Gbps NIC; **LMCache with a 48 GB DRAM prefix cache** | https://arxiv.org/pdf/2512.18194 |
| **Exploring CXL-based KV Cache Storage** (NeurIPS'24 ML-for-Systems workshop, ByteDance) | gpt-fast (modified for batching) | LLaMA-2-7B / 13B | Prefill requests of varying context length | TTFT vs recompute under 400 ms SLO; ROI model (GPU count) | 1-socket Xeon Platinum, 1 TB DDR5-4800, 1x H100, 256 GB ASIC CXL card (**real**) | KV recompute; KV in CPU DRAM | https://mlforsystems.org/assets/papers/neurips2024/paper17.pdf |
| **CXL-SpecKV** (arXiv 2512.11920; FPGA'26 per Related.md) | Own | 22 configurations, LLaMA-2/3 7B–70B, Qwen 1.8B–72B, Mistral/Mixtral, Gemma | Chatbot (128/256) and other length classes; details not extracted | Throughput, latency | 8x A100-80GB + 4x Agilex-7 FPGAs + CXL 2.0 expander | **not verified** | https://arxiv.org/pdf/2512.11920 |

### How LMCache itself is benchmarked (repo + docs)

| Item | Content | URL used |
|---|---|---|
| Repo `benchmarks/` directory | `long_doc_qa/`, `multi_round_qa/`, `multi_doc_qa/`, `rag/`, `microbenchmark/`, `storage_backend_io/`, `ttft-estimator/`, `musa/` | https://api.github.com/repos/LMCache/LMCache/contents/benchmarks |
| `multi_round_qa/multi-round-qa.py` | Flags `--num-users --num-rounds --qps --shared-system-prompt --user-history-prompt --answer-len --sharegpt --time --output`. README example: 10 users, 5 rounds, QPS 0.5, 1000-token system prompt, 2000-token history, 100-token answer, `mistralai/Mistral-7B-Instruct-v0.2`. ShareGPT mode via `prepare_sharegpt_data.sh` (ShareGPT_V3_unfiltered_cleaned_split.json). Output: QPS, prompt and generation throughput, average TTFT, per-request `summary.csv` | https://raw.githubusercontent.com/LMCache/LMCache/dev/benchmarks/multi_round_qa/README.md |
| `long_doc_qa/long_doc_qa.py` | Defaults read from the argparse block: document length 20000 tokens, 8 documents, 100 output tokens, repeat count 2, repeat mode `random`, 2 in-flight requests | https://raw.githubusercontent.com/LMCache/LMCache/dev/benchmarks/long_doc_qa/long_doc_qa.py |
| `lmcache bench engine` CLI (current docs) | Six workloads: `long-doc-qa` (`--ldqa-document-length` 10000, `--ldqa-query-per-document` 2, `--ldqa-num-inflight-requests` 3), `multi-round-chat` (`--mrc-shared-prompt-length` 2000, `--mrc-chat-history-length` 10000, `--mrc-user-input-length` 50, `--mrc-output-length` 200, `--mrc-qps` 1.0, `--mrc-duration` 60), `long-doc-permutator` (CacheBlend-style), `prefix-suffix-tuner` (`--psf-thrash` = tier size in GB to overflow; reports pass-2 hit rates), `rag-qa-quality` (musique, hotpotqa; F1), `random-prefill` (`--rp-request-length` 10000, 50 requests, max_tokens=1). Metrics: TTFT mean/P50/P90/P99, decode speed mean/P99, input/output throughput | https://docs.lmcache.ai/cli/bench.html |
| Docs benchmarking walkthrough | Qwen/Qwen3-8B, long-doc-qa, 10,000-token documents, 10 GB KV volume, 4 in-flight, `--l1-size-gb 66 --eviction-policy LRU`; result: mean TTFT 757 ms -> 185 ms, duration 23.47 s -> 13.79 s. GPU not named | https://docs.lmcache.ai/getting_started/benchmarking.html |
| Hardware assumptions | "Linux · Python 3.9–3.13 · NVIDIA GPU (compute 7.0+) · CUDA 12.1+". No minimum VRAM stated. Examples use 7B–8B models (needs >= ~16–24 GB VRAM in BF16); the tech report uses 8x H100 | https://docs.lmcache.ai/getting_started/installation.html |
| Storage backends | CPU RAM, local disk, GDS, Redis/Valkey, Mooncake, InfiniStore, S3, NIXL, and others; **a `DAX` L2 backend already exists** that maps `/dev/daxX.Y` ("byte-addressable memory devices such as persistent memory or CXL memory"), fixed-size slots (`device_path`, `max_dax_size_gb`, `slot_bytes`), volatile index. Storage-plugin and remote-storage-plugin extension points are documented | https://docs.lmcache.ai/ ; https://docs.lmcache.ai/mp/l2_storage/dax.html |

Trace facts checked from the data: Mooncake FAST'25 traces are JSONL with `timestamp, input_length, output_length, hash_ids`; the first rows give 14 ids for 6758 tokens and 5 ids for 2290 tokens, i.e. one hash id per 512 tokens. BurstGPT (arXiv 2401.17644): 10.31 M requests from regional Azure OpenAI GPT services over 213 days (https://arxiv.org/pdf/2401.17644).

---

## 3. Checkpointing systems

| Paper (venue) | Models and checkpoint sizes | Framework | Metrics | Hardware / storage | Baselines | URL used |
|---|---|---|---|---|---|---|
| **CheckFreq** (FAST'21) | ResNet18/50, ResNext101, DenseNet121, VGG16, InceptionV3 (ImageNet-1k), BERT-Large pretraining | PyTorch 1.1 + DALI | Runtime overhead (sync up to 70 %, CheckFreq < 3.5 %), recovery time, checkpoint frequency | 8x V100 + 1.8 TB SSD; 8x 1080Ti + HDD; 24 cores, 500 GB DRAM | Epoch-boundary checkpointing; every 200 iterations for BERT | https://www.usenix.org/system/files/fast21-mohan.pdf |
| **Check-N-Run** (NSDI'22) | Production-scale DLRM (Meta); sizes not extracted | Meta PyTorch training stack | Checkpoint write bandwidth, storage capacity, quantization latency, accuracy | HGX-like nodes, up to 1.5 TB DRAM and 56 cores per node, up to 16 nodes; remote storage | Accuracy figures compare one-shot / intermittent quantized-checkpoint baselines; a system-level baseline is not named in the text I extracted (**not verified**) | https://www.usenix.org/system/files/nsdi22-paper-eisenman.pdf |
| **Gemini** (SOSP'23) | GPT-2, BERT, RoBERTa scaled 10B–100B (GPT-2 100B on 16 instances) | DeepSpeed ZeRO-3 | **Average wasted time**, checkpoint time, checkpoint frequency, iteration-time impact | 16x AWS p4d.24xlarge (A100); p3dn.24xlarge; remote persistent storage | Strawman (checkpoint every 3 h, "following the setup in training BLOOM"), HighFreq (saturate remote storage bandwidth) | https://www.cs.rice.edu/~eugeneng/papers/SOSP23.pdf |
| **DataStates-LLM** (HPDC'24) | BLOOM-3B, LLaMA-30B, LLaMA2-7B/13B/70B; **10–15 GB checkpoint per GPU**; OSCAR-en data | DeepSpeed v0.11.2 + Megatron-LM | **Checkpointing throughput seen by training** (size / blocked time), iteration duration while checkpointing, end-to-end runtime | ALCF Polaris, 4x A100-40GB per node, Lustre | DeepSpeed default (sync `torch.save`), asynchronous checkpointing (CheckFreq / LightCheck / Lightning style), TorchSnapshot | https://arxiv.org/pdf/2406.10707 |
| **ByteCheckpoint** (NSDI'25) | vDiT 4B (FSDP, A100-80GB), tGPT 70B (Megatron-LM, H800-80GB); production scale | FSDP, Megatron-LM, veScale | **Checkpoint stall (blocking time)**, end-to-end save time, load / resharding time, **ETTR** | Production clusters, HDFS | PyTorch DCP, Megatron MCP | https://www.usenix.org/system/files/nsdi25-wan-borui.pdf |
| **PCcheck** (ASPLOS'25) | Checkpoint = model + optimizer: VGG16 1.1 GB, Transformer-XL 2.7 GB, BERT 4 GB, **OPT-1.3B 16.2 GB, OPT-2.7B 45 GB, BLOOM-7B 108 GB** | PyTorch 2.1 | Training throughput / slowdown vs checkpoint frequency; goodput under preemption | GCP a2-highgpu-1g (**1x A100-40GB**, 85 GB DRAM, 1 TB pd-ssd); **Titan RTX 24 GB + Optane PMEM** box; multi-VM for OPT-2.7B / BLOOM-7B | CheckFreq, GPM, Gemini (re-implemented), ideal no-checkpoint | https://anakli.inf.ethz.ch/papers/PCcheck_asplos25.pdf |
| **FastPersist** (arXiv 2406.13768; venue **not verified**) | GPT-3 style 0.7B–13B dense + 1.8B MoE | DeepSpeed, `torch.save` replacement | Checkpoint write throughput (GB/s), speedup over `torch.save`, training slowdown when checkpointing every iteration | 8x DGX-2 (128 V100-32GB), 8 NVMe per node, 24.8 GB/s peak write | `torch.save` | https://arxiv.org/pdf/2406.13768 |
| **Just-In-Time Checkpointing** (EuroSys'24) | **not verified** (only the abstract page was reachable) | **not verified** | Recovery time, wasted GPU work, steady-state overhead ("nearly zero") | **not verified** | Periodic checkpointing | https://www.microsoft.com/en-us/research/publication/just-in-time-checkpointing-low-cost-error-recovery-from-deep-learning-training-failures/ |
| **TorchSnapshot** (PyTorch library) | 20 GB model (DDP benchmark) | PyTorch DDP; FSDP, DeepSpeed-OPT, torchrec benchmark dirs | Save time: `torch.save` ~32 s vs 13.91 s (1 GPU) to 1.29 s (32 GPUs) on local FS | p4d.24xlarge; local FS and FSx for Lustre | `torch.save` | https://github.com/pytorch/torchsnapshot/tree/main/benchmarks/ddp |
| **PyTorch DCP `async_save`** (PyTorch blog with IBM, 2024) | 7B: training downtime per checkpoint **148.8 s -> 6.3 s**; GPU->CPU phase 6–14 s for 7B–13B | FSDP / torchtitan | Training "down time" per checkpoint | IBM cluster (details not stated) | Synchronous DCP; earlier `torch.save` | https://pytorch.org/blog/reducing-checkpointing-times/ |
| **VeloC** (IPDPS'19; overview arXiv 2103.02131) | ECP applications **HACC, LatticeQCD, EXAALT**; HACC at full Summit scale reached 224 TB/s local blocking write. IPDPS'19 evaluation details **not verified** (paywalled). Shipped test application: `heatdis`. A follow-up (arXiv 2112.02289) uses a 1 GiB-per-rank microbenchmark on Theta | MPI; sync or async (active backend) modes; scratch + persistent tiers | Local checkpoint throughput, overhead of background flush to Lustre | Summit, Theta, others | — | https://ar5iv.labs.arxiv.org/html/2103.02131 ; https://veloc.readthedocs.io/en/latest/userguide.html ; https://arxiv.org/pdf/2112.02289 |
| **SCR** (SC'10; extended version used) | **pF3D** laser-plasma code, in production on Hera, Atlas, Coastal | MPI, multi-level (RAM / flash / PFS) | **Machine efficiency**, parallel-file-system load, checkpoint cost per level | LLNL clusters | Single-level PFS checkpointing | https://www.osti.gov/servlets/purl/1225695 |
| **FTI** (SC'11) | **SPECFEM3D** (Tohoku earthquake) on 1152 GPUs; overhead as low as 8 % | MPI, 3-level + Reed-Solomon | Checkpoint overhead at high frequency | TSUBAME2.0 | **not verified** | https://dl.acm.org/doi/10.1145/2063384.2063427 (abstract via search) |

Takeaways: the ML papers report (a) the time training is blocked per checkpoint, (b) iteration time or throughput at a given checkpoint frequency, (c) a failure-aware end metric (Gemini's wasted time, ByteCheckpoint's ETTR, PCcheck's goodput). PCcheck is the precedent for a single-GPU checkpoint evaluation with checkpoint sizes 1–108 GB. None of them measures what the staging copy does to other DRAM users — that gap is ours.

---

## 4. PolyStore (FAST'25) — structural inspiration only, not a baseline

| Category | Content | URL used |
|---|---|---|
| Hardware configs | Config I: Optane PM + NVMe; Config II: NVMe + SATA SSD; Config III: three devices | https://www.usenix.org/system/files/fast25-ren.pdf |
| Microbenchmarks | Sequential / random read and write with direct I/O across thread counts; file sharing; DRAM-cache impact (working set fits / 16:1 overflow); sensitivity to epoch interval, Poly-index node size, and underlying file systems (NOVA+F2FS vs ext4-DAX+ext4); scaling to three devices | same |
| Macrobenchmarks | Filebench Varmail and Fileserver | same |
| Applications | RocksDB with YCSB A–F (32 threads, 10M keys); Redis (AOF logging + async RDB checkpoint, 16 instances, SET); GraphWalker (MS-PPR, 64 GB graph); **multi-application run (RocksDB + 16 Redis instances)**; failure recovery | same |
| Their comparison set (for structure only) | PM-only / NVMe-only / SATA-only file systems, Orthus (caching), Strata and SPFS (tiering), P2CACHE | same |

Structure worth copying: microbenchmarks that isolate each mechanism -> sensitivity studies -> real applications -> a multi-application run -> recovery.

---

## 5. Memory-bandwidth-bound CPU workloads and the evidence

| Workload | Evidence that it is bandwidth-bound | Source |
|---|---|---|
| SPEC CPU 2017 **603.bwaves, 619.lbm, 649.fotonik3d, 654.roms** | "four bandwidth-bound workloads requiring over 24GB/s"; > 50 % slowdown once the CXL device saturates; lbm slowdown from store-buffer stalls / RFOs (write-heavy) | Dissecting CXL, https://arxiv.org/pdf/2409.14317 |
| SPECrate 2017 **fotonik3d, mcf, roms, cactuBSSN** | The four highest-MPKI members, used as the "memory-bandwidth-intensive" class; same four independently chosen by M5 | https://arxiv.org/pdf/2303.15375 ; https://jiyuan.is/papers/asplos25-m5.pdf |
| 649.fotonik3d_s | Most severe outlier of 115 workloads under Intel Flat Memory Mode | https://www.usenix.org/system/files/osdi24-zhong-yuhong.pdf |
| **DLRM inference** (embedding reduction, MERCI setup) | Embedding reduction is 50–70 % of inference latency; used as the bandwidth-intensive throughput application | https://arxiv.org/pdf/2303.15375 |
| **CPU LLM decoding** (Llama-3-8B, IPEX; llama.cpp) | Token generation "necessitates repeated reading of model weights for each token"; +17 % from extra bandwidth (Intel + Micron). llama.cpp community measurements report decode scaling with memory bandwidth (community source, weaker evidence) | https://arxiv.org/pdf/2412.12491 ; https://github.com/ggml-org/llama.cpp/discussions/3167 |
| **HPCG, OpenFOAM, Xcompact3d, POT3D** | Presented as bandwidth-hungry HPC; HPCG +27 %, POT3D +27 % with CXL bandwidth expansion | https://arxiv.org/pdf/2412.12491 |
| **NPB MG** (vs CG) | MG labelled "bandwidth-sensitive", CG "latency-sensitive" on real CXL | http://pasalabs.org/papers/2025/IPDPS25_cxl_eval.pdf |
| **STREAM** | Defined as measuring "sustainable memory bandwidth"; kernels COPY, SCALE, ADD, TRIAD | https://www.cs.virginia.edu/stream/ref.html |
| **Intel MLC / sequential R-W antagonist** | Used as the bandwidth aggressor by Memstrata, SoarAlto, Colloid | see §1 |
| **GAPBS** (PR, BC) | Universally used, but the slowdown is dominated by LLC-miss demand reads (latency-like), and Pond reports high sensitivity. Treat as memory-intensive, not purely bandwidth-bound | https://arxiv.org/pdf/2409.14317 ; https://ar5iv.labs.arxiv.org/html/2203.00241 |
| **XSBench** | Used by MEMTIS, NeoMem, IPDPS'25 as the HPC representative; no explicit bandwidth-bound statement found | see §1 |
| **ZeRO-Offload CPU optimizer step** | **Counter-evidence:** described as memory-*latency*-sensitive (2–18 % slower on CXL), not bandwidth-bound. Do not present it as a bandwidth victim without measuring it ourselves | http://pasalabs.org/papers/2025/IPDPS25_cxl_eval.pdf |
| Graph500 | Used by MEMTIS (66.3 GB); no bandwidth statement found | https://multics69.github.io/pages/pubs/memtis-lee-sosp23.pdf |

---

## 6. Recommendation for our evaluation

### (a) Bandwidth-bound victim applications, ranked

1. **SPEC CPU 2017 bandwidth members: 619.lbm / 519.lbm_r, 649.fotonik3d / 549.fotonik3d_r, 603.bwaves, 654.roms (rate mode, N copies).** This is the only group that a paper explicitly measures as bandwidth-bound on real CXL (Dissecting CXL), that Memstrata reports as its worst outlier, and that Demystifying-CXL and M5 independently select by MPKI. lbm is write-heavy (RFO stalls), so it also probes writer-vs-writer contention. Needs a SPEC licence; on a 128-core EPYC run enough copies to load the DRAM channels and report the copy count.
2. **GAPBS PageRank and BC (Twitter, urand/kron).** Appears in Pond, MEMTIS, Colloid, Nomad, Memstrata, M5, SoarAlto, HeMem, CXL-Interference — no reviewer will question it. Be honest that it is memory-intensive with a latency component; it is the natural "DRAM reader" for the slowdown bound.
3. **CPU LLM decoding (llama.cpp or IPEX, Llama-3-8B class).** Read-only, bandwidth-bound per the Intel + Micron CZ122 study, and thematically consistent with an inference node where the KV offload writer runs next to CPU-side inference. Report tokens/s and per-token P99.
4. **DLRM inference (embedding reduction, MERCI setup).** The bandwidth-intensive application of Demystifying-CXL; also in Memstrata's set. Fits the "AI training/serving node" scenario next to checkpoint writes.
5. **HPC kernels: NPB MG, HPCG, XSBench, and LULESH itself.** MG and HPCG have explicit bandwidth evidence; they pair naturally with VeloC (simulation ranks are the victims of their own node's checkpoint staging).

Add one **latency-sensitive victim with tail latency** (Redis + YCSB-A or Silo YCSB-C, P99) because Dissecting-CXL explicitly recommends tail latency and Demystifying/Nomad/M5/Colloid all use it. Use **Intel MLC / STREAM / a Colloid-style sequential antagonist only for controlled sweeps**, never as the headline.

### (b) Bulk-write producers to pair with them

| Scenario | Victims | Writer |
|---|---|---|
| HPC node | LULESH ranks, NPB MG, HPCG | VeloC async checkpoint (LULESH today; HACC is VeloC's flagship application per the VELOC overview — whether a public HACC I/O kernel is usable was not verified) |
| Training node | DLRM inference or SPEC rate copies; data-loader processes | PyTorch DCP `async_save` with checkpoint sizes following PCcheck's table (16 GB / 45 GB / 108 GB for OPT-1.3B / OPT-2.7B / BLOOM-7B with optimizer state) and DataStates-LLM's 10–15 GB per GPU shard |
| Inference node | CPU LLM decode, Redis P99 | LMCache KV offload (real) + the Mooncake-trace stand-in scaled to several instances |

Report the writer side with the community's metrics: training blocked time per checkpoint and iteration time at a fixed checkpoint frequency (DataStates, ByteCheckpoint), plus one failure-aware metric (wasted time or ETTR); for KV, TTFT/ITL and hit rate. Report the victim side as slowdown vs running alone.

### (c) Feasible LMCache + vLLM setup on the 8 GB RTX 4060 Ti

Measured on c28: 8188 MiB, PCIe Gen4 x8, compute capability 8.9 (LMCache needs >= 7.0). Weight sizes and KV geometry below come from the Hugging Face `config.json` / safetensors listings (KV bytes per token = 2 x layers x kv_heads x head_dim x 2 bytes).

| Model | Weights | KV per token (FP16) | Verdict |
|---|---|---|---|
| Qwen/Qwen2.5-1.5B-Instruct | 2.88 GiB | 28 KiB (28 layers, 2 KV heads) | **Primary.** 32K context, ~4 GiB left for GPU KV |
| Llama-3.2-1B-Instruct | 2.30 GiB | 32 KiB (16 layers, 8 KV heads) | **Primary alternative**, 128K context |
| Qwen/Qwen2.5-7B-Instruct-AWQ (4-bit) | 5.19 GiB | 56 KiB | **Stretch**: needs `--max-model-len` 8–16K, `--enforce-eager`, high `--gpu-memory-utilization`; only ~1–1.5 GiB for GPU KV (estimate, must be measured) |
| Llama-3.2-3B-Instruct BF16 | 5.98 GiB | 112 KiB | Too tight in BF16; only with a 4-bit quantization |
| Qwen3-4B BF16 / 8B-class BF16 | 7.49 GiB / > 8 GiB | 144 KiB / 128–144 KiB | Does not fit |

- **Workloads:** `lmcache bench engine` `long-doc-qa` (10,000-token documents, as in the docs walkthrough), `multi-round-chat` (2000 shared + 10000 history, QPS sweep), `prefix-suffix-tuner` with `--psf-thrash` to overflow the DRAM tier, and `random-prefill`; plus the older `multi-round-qa.py --sharegpt`. Datasets that match prior work: LongBench (LMCache report, CacheGen), ShareGPT multi-turn (vLLM, CachedAttention, HCache), LooGLE / L-Eval (Mooncake synthetic, HiCache, HCache), and Mooncake conversation / tool&agent traces for arrival and prefix-reuse patterns.
- **Backends to compare inside LMCache:** vLLM alone (GPU prefix cache), vLLM native CPU offload, LMCache CPU-RAM (all DRAM), LMCache local disk (NVMe), **LMCache's existing DAX backend on a devdax (flat all-CXL)**, and LMCache + cxlpath as a storage plugin.
- **Metrics:** TTFT mean/P50/P90/P99, ITL, QPS at a TTFT SLO, hit rate, prefill GPU time saved (Mooncake's metric), plus our own: co-located victim slowdown and DRAM bytes lent.
- **Honest limit:** a 10K-token document is only ~273 MiB of KV at 28 KiB/token, and one small GPU behind PCIe 4.0 x8 cannot produce a write stream that stresses DRAM or CXL bandwidth. So the 4060 Ti run is the *end-to-end correctness and latency* experiment (the small GPU KV pool actually helps: almost every reuse is served from the offload tier). The *bandwidth-stress* experiment must use several stand-in producers with 8B–70B KV geometry; Mooncake's own evaluation replays traces with a dummy LLaMA3-70B model, which is the precedent to cite.
- **On the H100 / A100 / 4x A6000 nodes (no CXL):** (i) run the LMCache report's configuration (Llama-3.1-8B-Instruct with 20K-token inputs, a 32B model on H100) and log every KV store/load (size, timestamp) — replay those logs on c28 so the stand-in is calibrated by real data, and validate on a different trace than the one used for calibration; (ii) capacity-vs-hit-rate curves on LongBench / ShareGPT / Mooncake traces to justify a TB-scale tier; (iii) show the DRAM-side problem exists without CXL: LMCache CPU offload next to a bandwidth-bound victim; (iv) real FSDP + DCP `async_save` stall numbers for 7B–13B models as the checkpoint ground truth.

### (d) Baselines comparable papers would expect

- **Placement alternatives on the same machine:** all-DRAM staging (what DCP `async_save`, VeloC scratch on tmpfs, and LMCache CPU-RAM do today); all-CXL flat (LMCache DAX backend; VeloC scratch on the dax device); direct-to-NVMe (sync save, LMCache local disk); Linux weighted interleave (the CZ122 paper's method).
- **Kernel tiering:** the SoarAlto set — TPP, NBT, Nomad, Colloid, NoTier. At minimum NBT/TPP since they are upstream. Colloid is the closest contention-aware design; it reads Intel CHA counters, so whether it runs on our EPYC is **not verified**.
- **Bandwidth regulation instead of redirection:** throttle the writer (MT2-style, or resctrl memory-bandwidth allocation) and show what it costs in write throughput. Reviewers will ask "why not just throttle?".
- **Domain systems:** checkpointing — DCP sync and async, TorchSnapshot, DataStates-LLM, PCcheck (open source), CheckFreq, VeloC default; KV — vLLM prefix caching, vLLM CPU offload, LMCache stock backends, Mooncake store, optionally SGLang HiCache.
- An **oracle / ideal** line (PCcheck's no-checkpoint ideal, HCache's Ideal, victim running alone).
- PolyStore stays out of the baseline list (project rule).

### (e) What reviewers commonly criticise, with sources where I have one

| Risk | Source | What to do |
|---|---|---|
| Emulated CXL | Demystifying-CXL: real CXL differs from NUMA emulation in latency and bandwidth efficiency | We run on real CZ120 — state it; but it is one device type on one platform, whereas Dissecting-CXL used four devices. Acknowledge, and show sensitivity by varying the number of dax devices |
| No tail latency | Dissecting-CXL Recommendation #1 | P99 for the latency victim and for TTFT/ITL |
| Selective benchmarking; not evaluating degradation | Heiser, "Systems Benchmarking Crimes" | Show the cases where cxlpath loses or is neutral: no victim present, read-heavy KV hits served from CXL, small objects, writer-only runs |
| Microbenchmarks presented as overall performance; simplified simulated system | Heiser | The KV stand-in must be backed by the real LMCache + vLLM run and calibrated from real logs |
| Same data for calibration and validation | Heiser; Memstrata splits its workloads into training and test sets | Fit the slowdown model and the break-even promotion rule on one set of victims/traces, validate on another |
| No proper baseline; only evaluating against yourself; not comparing with the state of the art | Heiser | Section (d) |
| Relative numbers only; missing platform specification | Heiser; Hoefler and Belli Rule 9 | Absolute GB/s, seconds, tokens/s next to every ratio; full platform table |
| No indication of significance | Heiser; Hoefler and Belli Rules 5–6 (confidence intervals for nondeterministic data, do not assume normality) | Repetitions + CIs; the project already knows probe noise on c28 is an issue |
| No sensitivity study | Present in every comparable: Colloid (contention 0–3x), SoarAlto (tier ratios, AOL thresholds, 0–9 MLC threads), Memstrata §6.3, PolyStore (epoch, index node size) | Sweep the slowdown bound, writer intensity, DRAM budget, number of CXL devices, NVMe drain rate, object size |
| Single workload / single domain | My judgement from the tables: accepted papers use 8–12 applications (MEMTIS 8, NeoMem 8, M5 12) or 100+ (Pond, Memstrata, Dissecting) | 3 producers x 5–6 victims is in range if every pairing is reported |
| Single node, small GPU | My judgement: Mooncake uses 128 GPUs, LMCache 8x H100; but InfiniGen (1x A6000), FlexGen (1x T4), PCcheck (1x A100), TraCT (1x A6000 per server) and the IPDPS'25 CXL study (1x A10) were accepted with one modest GPU | Frame the contribution as host-memory-path, complement with H100/A100 trace collection |
| Overhead accounting | Heiser ("throughput degraded by x% => overhead is x%") | Report CPU cost of the runtime and the drain, not only throughput deltas |

---

## 7. URLs relied on

CXL / tiered memory
- https://ar5iv.labs.arxiv.org/html/2206.02878 (TPP)
- https://ar5iv.labs.arxiv.org/html/2203.00241 (Pond)
- https://multics69.github.io/pages/pubs/memtis-lee-sosp23.pdf (MEMTIS)
- https://nvmw.ucsd.edu/nvmw2022-program/nvmw2022-data/nvmw2022-paper4-final_version_your_extended_abstract.pdf (HeMem extended abstract)
- https://sysartifacts.github.io/sosp2021/summaries/hemem (HeMem artifact summary, via search result)
- https://www.cs.cornell.edu/~ragarwal/pubs/colloid.pdf (Colloid)
- https://arxiv.org/html/2401.13154 (Nomad)
- https://www.usenix.org/system/files/osdi24-zhong-yuhong.pdf (Memstrata)
- https://jiyuan.is/papers/asplos25-m5.pdf (M5)
- https://arxiv.org/pdf/2403.18702 (NeoMem)
- https://www.usenix.org/system/files/osdi25-liu.pdf (SoarAlto)
- https://arxiv.org/pdf/2303.15375 (Demystifying CXL Memory)
- https://arxiv.org/pdf/2409.14317 (Dissecting CXL Memory Performance at Scale)
- https://arxiv.org/pdf/2412.12491 (Micron CZ122 + Intel Xeon 6)
- https://arxiv.org/pdf/2411.18308 (CXL-Interference)
- https://arxiv.org/pdf/2405.14209 and http://pasalabs.org/papers/2025/IPDPS25_cxl_eval.pdf (real-world CXL use cases, IPDPS'25)
- https://ipads.se.sjtu.edu.cn/_media/publications/yijfast22.pdf (MT2)

KV cache / serving
- https://arxiv.org/pdf/2309.06180 (vLLM)
- https://arxiv.org/pdf/2303.06865 (FlexGen)
- https://arxiv.org/pdf/2310.07240 (CacheGen)
- https://arxiv.org/pdf/2405.16444 (CacheBlend)
- https://arxiv.org/pdf/2510.09665 (LMCache tech report)
- https://www.usenix.org/system/files/fast25-qin.pdf (Mooncake)
- https://github.com/kvcache-ai/Mooncake/tree/main/FAST25-release/traces and https://raw.githubusercontent.com/kvcache-ai/Mooncake/main/FAST25-release/README.md (traces)
- https://www.usenix.org/system/files/atc24-gao-bin-cost.pdf (CachedAttention)
- https://www.usenix.org/system/files/osdi24-lee.pdf (InfiniGen)
- https://arxiv.org/pdf/2410.05004 (HCache)
- https://www.usenix.org/system/files/fast25-chen-weijian-impress.pdf (IMPRESS)
- https://lmsys.org/blog/2025-09-10-sglang-hicache/ (SGLang HiCache)
- https://arxiv.org/pdf/2401.09670 (DistServe)
- https://arxiv.org/pdf/2311.18677 (Splitwise)
- https://github.com/Azure/AzurePublicDataset/blob/master/AzureLLMInferenceDataset2023.md (Azure traces)
- https://arxiv.org/pdf/2401.17644 (BurstGPT)
- https://arxiv.org/pdf/2511.20172 (Beluga)
- https://arxiv.org/pdf/2512.18194 (TraCT)
- https://mlforsystems.org/assets/papers/neurips2024/paper17.pdf (ByteDance CXL KV)
- https://arxiv.org/pdf/2512.11920 (CXL-SpecKV)
- https://api.github.com/repos/LMCache/LMCache/contents/benchmarks ; https://raw.githubusercontent.com/LMCache/LMCache/dev/benchmarks/multi_round_qa/README.md ; https://raw.githubusercontent.com/LMCache/LMCache/dev/benchmarks/long_doc_qa/long_doc_qa.py
- https://docs.lmcache.ai/ ; https://docs.lmcache.ai/getting_started/installation.html ; https://docs.lmcache.ai/getting_started/benchmarking.html ; https://docs.lmcache.ai/cli/bench.html ; https://docs.lmcache.ai/mp/l2_storage/dax.html
- Hugging Face `config.json` and model API for Qwen/Qwen2.5-1.5B-Instruct, Qwen/Qwen2.5-3B-Instruct, Qwen/Qwen2.5-7B-Instruct(-AWQ), unsloth/Llama-3.2-1B-Instruct, unsloth/Llama-3.2-3B-Instruct, unsloth/Meta-Llama-3.1-8B-Instruct, Qwen/Qwen3-4B, Qwen/Qwen3-8B (https://huggingface.co/<model>/resolve/main/config.json)

Checkpointing
- https://www.usenix.org/system/files/fast21-mohan.pdf (CheckFreq)
- https://www.usenix.org/system/files/nsdi22-paper-eisenman.pdf (Check-N-Run)
- https://www.cs.rice.edu/~eugeneng/papers/SOSP23.pdf (Gemini)
- https://arxiv.org/pdf/2406.10707 (DataStates-LLM)
- https://www.usenix.org/system/files/nsdi25-wan-borui.pdf (ByteCheckpoint)
- https://anakli.inf.ethz.ch/papers/PCcheck_asplos25.pdf (PCcheck)
- https://arxiv.org/pdf/2406.13768 (FastPersist)
- https://www.microsoft.com/en-us/research/publication/just-in-time-checkpointing-low-cost-error-recovery-from-deep-learning-training-failures/ (JIT checkpointing, abstract only)
- https://github.com/pytorch/torchsnapshot (README and benchmarks/ddp/README.md)
- https://pytorch.org/blog/reducing-checkpointing-times/ (DCP async checkpointing)
- https://ar5iv.labs.arxiv.org/html/2103.02131 ; https://veloc.readthedocs.io/en/latest/userguide.html ; https://arxiv.org/pdf/2112.02289 (VeloC)
- https://www.osti.gov/servlets/purl/1225695 (SCR, extended version)
- https://dl.acm.org/doi/10.1145/2063384.2063427 (FTI, abstract via search)

PolyStore
- https://www.usenix.org/system/files/fast25-ren.pdf

Bandwidth-bound evidence and methodology
- https://www.cs.virginia.edu/stream/ref.html (STREAM)
- https://github.com/ggml-org/llama.cpp/discussions/3167 (llama.cpp CPU performance discussion; community source, surfaced by search, not read in full)
- https://gernot-heiser.org/benchmarking-crimes.html (Heiser)
- https://htor.inf.ethz.ch/publications/img/hoefler-scientific-benchmarking.pdf (Hoefler and Belli, SC'15)

Local
- /home/ghu4/CXL/Related.md (read only, for venue labels of Beluga and CXL-SpecKV and for the existing PolyStore notes)
- `nvidia-smi` on c28, 2026-09-21 (GPU memory, PCIe link, compute capability)
