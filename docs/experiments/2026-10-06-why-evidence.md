# 2026-10-06 — Evidence for the "why": tail latency of an inference tenant, checkpoint frequency vs overhead, SSD endurance arithmetic, the persistent-memory control, a fixed-ratio split baseline, and the literature on bandwidth isolation

**STATUS: ACTIVE.** Raw: `experimental_results/2026-10-06-why-evidence/` (analyses), `2026-10-06-optane-control/`
(Slurm job on c35/c36), `2026-10-06-fixed-split-baseline/` (c28). Started after the advisor's review of 2026-10-04
("why do this at all; what can only CXL do; why not persistent memory; multi-tenancy").

## 1. Tail latency of the inference tenant (from the real-data re-run logs, no new runs)
`benchmarks/policy/tail_latency.py`: inter-token intervals of the llama.cpp victim inside the copy windows vs the 10 s
before (medians over the last 3 windows; raw `tail-latency-llama.txt`).

| victim | policy | p50 before → inside | p99 before → inside | p99 inside / before |
|---|---|---|---|---|
| llama.cpp, 80 threads | all-DRAM staging (today) | 30.9 → 48.4 ms | 31.2 → 49–50 ms | **1.56–1.60×** |
| llama.cpp, 80 threads | DRAM throttled 20 GiB/s | 30.8 → 35.2 ms | 31.0 → 35.6–37.8 ms | 1.15–1.22× |
| llama.cpp, 80 threads | all-CXL / cxlpath | 30.8 → 34.2 ms | 31.0 → 34.4–34.8 ms | 1.10–1.12× |
| llama.cpp, 32 threads | all-DRAM staging | 56.7 → 59.1 ms | 57.0 → 59.2–60.6 ms | 1.04–1.06× |
| llama.cpp, 32 threads | all-CXL / cxlpath | 56.5 → 56.8 ms | 56.8 → 56.9–57.0 ms | 1.00× |

Reading: for a co-located inference tenant a 64 GiB checkpoint staged in DRAM is a 1.6× per-token latency spike for
the ~1 s of the copy (every token during the burst, not a rare outlier); staged in CXL it is 1.1×.

## 2. Checkpoint frequency vs overhead (from the PyTorch producer measurements of 2026-09-22)
`checkpoint-frequency.txt`. Overhead = (training thread blocked + own compute slowed while the checkpoint is
written) / period; a checkpoint cannot start before the previous one is durable. 16 GiB state as measured; 64 GiB
with stall and persist scaled 4×.

| | 20 s | 30 s | 60 s | 120 s | 300 s | 600 s |
|---|---|---|---|---|---|---|
| stock DRAM staging, 16 GiB | cannot sustain | cannot sustain | 3.0% | 1.5% | 0.6% | 0.3% |
| cxlpath, 16 GiB | 4.0% | 2.7% | 1.4% | 0.7% | 0.3% | 0.1% |
| stock DRAM staging, 64 GiB | — | — | — | — | 2.4% | 1.2% |
| cxlpath, 64 GiB | — | — | — | 2.7% | 1.1% | 0.5% |

Shortest sustainable period under an overhead budget (16 GiB / 64 GiB): at 3%, stock every 60 s / 240 s, cxlpath every
27 s / 108 s; at 1%, stock every 180 s / 720 s, cxlpath every 81 s / 324 s. The stock path cannot checkpoint a 16 GiB
state more often than every 33 s at all (its persist takes 31 s); cxlpath every 20 s.

## 3. SSD endurance arithmetic (why a KV pool cannot live on flash at production churn)
The KV write rate of the Mooncake traces is 2.7–3.2 GiB/s for an 8-billion-parameter model and 6.7–8.1 for 70B
(`2026-09-09-kv-trace-analysis.md`) = 250–300 TB/day (8B) and 620–750 TB/day (70B). Our NVMe (Solidigm D5-P5430,
3.84 TB, QLC) is rated 0.58 drive writes per day for random writes = 2.2 TB/day, about 4 PB over five years
([spec](https://www.avendor.com/products/solidigm-d5-p5430-series-3-84-tb-2-5in-pcie-4-0-x4-3d5-qlc-generic-single-p),
[family page](https://www.mouser.pl/solidigm-d5-p5430-solid-state-drives)); the churn is 110–340× that budget, and
even against a sequential-write rating several times higher it stays in the tens. The drive's sequential write
specification is 3 GB/s; we measured 0.9 GiB/s sustained with O_DIRECT. Hits from flash: 0.9 GiB/s vs 12.5 (GPU
reading CXL) and 24 (CPU reading CXL).

## 4. Literature check: "the existing remedy for memory-bandwidth interference is throttling"
Confirmed from the sources: MT² (FAST'22) "regulates memory bandwidth among concurrent applications by detecting
memory traffic interference ... and leverages a dynamic bandwidth throttling algorithm"; it also states the
persistent-memory fact we rely on: "NVM and DRAM share the same memory bus, and their traffic is mixed together and
interferes with each other" ([USENIX page](https://www.usenix.org/conference/fast22/presentation/yi-mt2)). Optane on one
socket: 39 GB/s read, 13 GB/s write, ~3× asymmetry, which HeMem (SOSP'21) builds its placement around
([Optane evaluation](https://arxiv.org/pdf/1908.06503)). Intel MBA, MemGuard (RTAS'13), PARTIES (ASPLOS'19) and ARM
MPAM regulate by delaying or capping the offender's requests (to be cited from the originals in the paper's
related-work pass). No mechanism in this literature moves the traffic to another memory pipe.

## 5. Persistent-memory control (c35/c36, Optane as KMEM-DAX NUMA nodes) — PENDING
`hardware/scripts/optane-control.sh`, Slurm job 304547 (queued behind other users). Questions: PM write capacity vs
threads (NT and plain stores); PM read capacity; a 4-thread DRAM reader beside 4/8/16 writers into DRAM vs into PM.

## 6. Fixed-ratio split baseline (the weighted-interleave strawman) — DONE (24 runs, 3 repetitions)
`ckpt_producer split --split16 4|8`: a FIXED 25% / 50% of the chunks go to DRAM, the rest to CXL — what a static
weighted interleave does. Same protocol as the real-data re-run; medians of 3 repetitions (`summary.csv`).

| victim | 25% DRAM | 50% DRAM | cxlpath (adaptive; from `2026-09-22-three-policies-realdata.md`) |
|---|---|---|---|
| reader, 8 threads (moderate) | 1.24 s, 6.2% | 1.06 s, 13.7% | 1.07 s at 6.2% (share 0.27); 0.98 s at 6.2% (0.34) |
| PageRank-32 (moderate), 192 GiB | 3.67 s, 9.4% | 3.15 s, 21.9% | 3.35 s at 7.8% (0.24); 3.49 s at 6.3% (0.23) |
| Adam-80 (saturated) | 3.50 s, 10.0% | 3.61 s, 12.2% | 3.50 s at 6.6% (0, no loan) |
| llama.cpp-80 (saturated) | 1.42 s, 16.5% | 1.31 s, 20.9% | 1.65 s at 8.7% (0, no loan) |

Reading: a fixed share cannot be right for both regimes. At 25% it under-uses the headroom beside the reader (1.24 s
where cxlpath gets 1.07 s at the same harm) and already costs the saturated victims 1.5–1.9× the harm of cxlpath for
no speed gain (Adam 10.0% vs 6.6%, llama.cpp 16.5% vs 8.7%); at 50% it reaches cxlpath's speed beside the reader but
at 2.2× the harm (13.7%) and 3.5× beside PageRank-32 (21.9% vs 6.3%). The adaptive share — lend only when CXL is the
bottleneck and the probe shows headroom, nothing beside a saturated victim — is what the controller contributes over
interleaving.

## Verdict
(pending sections 5 and 6)
