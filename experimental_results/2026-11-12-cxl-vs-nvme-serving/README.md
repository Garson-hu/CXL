# 2026-11-12 — CXL vs. NVMe memory expansion for LLM serving: raw data

Report: `docs/experiments/2026-11-12-cxl-vs-nvme-serving.md`. One-page summary: `SUMMARY.md` in this directory.
Branch `explore/cxl-vs-nvme-serving` (not merged). Node c28, 2026-11-12 … 2026-11-14.

## Layout

| path | content |
|---|---|
| `experiment-matrix.md`, `experiment-matrix.csv` | every run of the study, one row each (`matrix_tier.py`): phase, configuration, workload, settings that differ from the common ones, measured and filler requests with their errors, requests answered with status 200 but without an output token, completion, exit code, and its use — result, functional check, GPU-memory record or void |
| `plan.txt`, `done.txt`, `chain.txt`, `queue_*.log` | the run plan as executed by `benchmarks/serving/queue_tier.sh` (one line per run with its full configuration), exit code and end time of every run, start / end log |
| `env/` | environment inspection of 2026-11-12 (`inspect-2026-11-12.txt`: CPU, memory, CXL topology and Device-DAX devices, NVMe, GPU, versions), GPU memory by CUDA-registered host memory (`vram-registered.txt`), vLLM's GPU footprint at three pool sizes (`vram-vllm.txt`), the fit test of the full hybrid (`vram/`) |
| `P0/` | path validation: short runs with content hashes; `*-residency.txt` = result of the independent check of each run (device mapping hashes, page-cache residency of the cache files); `tables-p0.md` |
| `A/` | Experiment A, single-request retrieval: per run `*-tier-timeline.csv` (one row per request with every interval of its path), `*-tier-summary.md`; `tables-a.md`, `a-summary.csv` |
| `C/` | Experiment C, equal-hit comparison: the same per-run files; `tables-c.md`, `c-summary.csv` |
| `D/` | Experiment D, concurrent retrieval: the same; `tables-d.md`, `d-summary.csv` |
| `B0/` | functional replays with scaled-down tiers (both levels fill and evict) |
| `B/` | Experiments B and E, trace replays: per run `*-replay.json` (hit shares, TTFT, throughput), `*-tier.json` (tokens by source, bytes by medium, traffic, memory, CPU), `*-requests.csv` (per-request time line from vLLM's events), `*-tier-requests.csv` (per request: tokens by host medium, lookup interval, L2 prefetch), `*-traffic.csv` (per second: bytes read / written per medium, GPU link bytes, L1 / L2 occupancy), `*-client.jsonl` (client-side records with the output hash), `*-analysis.txt` (one summary line per run, written by the queue); `tables-b.md` (replay tables per window), `tables-e.md` (traffic and overlap), `tables-writes.md` (what became of every stored chunk; GPU transfer operations; L2 load and store tasks), `tier-summary.csv`, `writes-summary.csv` |
| `trace-model/` | offline LRU capacity model of the two traces (**a model, not a measurement**) |
| `figs/` | all figures (matplotlib): A1–A4, C1–C3, D1–D3, B1–B5, E1, T1 |
| `void/` | runs that are not results: the first attempt at the full hybrid (vLLM did not start) and the nine runs that ran against its left-over cache server; the two sustained-overload replays with default settings in which vLLM's engine died (`b-conv16-dram80`, `b-conv16-hyb`; report C.4.5); kept for the record |

Every run `<tag>` has `<tag>-meta.txt` (the configuration, the exact command lines of vLLM and of the LMCache server, versions),
`<tag>-driver.txt` (the driver's log) and `<tag>-client.jsonl`.

## Not in the repository

The bulky per-run logs stay on c28 under `/mnt/local/ghu4/results/2026-11-12-cxl-vs-nvme-serving/`: `*-kvevents.jsonl` (mirror of
LMCache's events with the medium of every L1 object and one line per chunk copied to / from the DAX devices or the files),
`*-vllmevt.*.jsonl` (vLLM's scheduler events), `*-steps.csv`, `*-gpu.txt` / `*-cpu.txt` (samplers), `*-server.log`,
`*-lmcache.log`, `*-status.txt` (LMCache `/status` at 1 Hz). The tables can be rebuilt from them with the scripts below.

## Rebuilding

All scripts are in `benchmarks/serving/` (Python environment and CPU sets as in `queue_tier.sh`):

```
inspect_cxl_env.sh                          # env/inspect-<date>.txt
vram_registered.sh                          # env/vram-registered.txt
queue_tier_p0a.sh <results> p0|p0full|a     # P0 and A runs with their residency checks
queue_tier.sh <results> <results>/plan.txt  # B0, C, D, B runs; starts the per-run analysis
verify_residency.py <events> [--files dir]  # independent residency check of one run
analyze_tier.py <dir> <tag>                 # A / C / D: per-request time line
analyze_tier_replay.py <dir> <tag>          # B / E: tier summary of a replay
table_tier_p0.py | table_tier_a.py | table_tier_cd.py c|d | table_tier_b.py <dir> <figs>   # tables and figures
writes_tier.py <B dir>                      # E: write-side accounting of ALL replays, tables-writes.md (with tags: only those rows)
pairs_tier.py <B dir> pair|cached|l2pair|l2tags|l2direct|overload|lookups|since|startup|timed ...   # per-request comparisons of two replays, lookup timing,
                                            # the overload round, the timed cache model (prints; the paired numbers of the report)
matrix_tier.py <results>                    # experiment-matrix.md / .csv
trace_capacity_tier.py <csv> <png>          # trace model
check_outputs.py <dir> <ref tag> <tag ...>  # output equality across tiers
collect_tier.sh                             # copies the small artifacts from c28's local disk into this directory
```
