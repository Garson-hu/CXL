# CXL + LLM Research Project

Target: top systems venue (OSDI'27, ASPLOS'27, SOSP'27, FAST'28). 10–12 month timeline from April 2026. Primary inspiration: Memstrata (OSDI'24, Zhong et al.).

## Directory layout

- [hardware/](hardware/) — c28 measurement artifacts
  - [scripts/](hardware/scripts/) — `inspect-system.sh`, `mlc-sweep.sh`, `llm-baselines.sh`
  - [results/](hardware/results/) — raw dated output, never edited
- [experiments/](experiments/) — experiments driving system design
  - [baselines/](experiments/baselines/) — KV-cache placement comparisons (DRAM, CXL-pinned, interleaved)
- [system/](system/) — the system being built (populated once direction is locked)
- [workloads/](workloads/) — trace configs (LMSys-Chat-1M, ShareGPT, BurstGPT, Azure LLM Inference Traces)
- [scripts/](scripts/) — utility scripts (ssh helpers, data processing)

## Hardware

- **c28** (queue `-p turin128`): AMD EPYC 9745 Turin 128c, 768 GB DDR5-4800, 4× Micron CZ120 CXL (1 TB total), custom 6.14.11+ kernel. GPU configuration unknown — Week 1 priority.
- Backup GPU nodes: c29 (H100 NVL 94 GB), c33 (A100 80 GB), c30–31 (4× A6000 48 GB), `rtx4060ti16g` pool.
- Frontier at ORNL available for large-scale baselines if needed.

## Current phase

Week 1 — hardware verification on c28. Run the three scripts in [hardware/scripts/](hardware/scripts/), dump output into [hardware/results/](hardware/results/). Deliverables: raw latency/bandwidth numbers for DRAM + per-CXL-device + 4-device aggregate, whether c28 has GPUs, whether vLLM/llama.cpp can pin KV cache to CXL via `numactl`.
