# 2026-10-12 — Checkpoint writes and KV reads on the same CXL cards: does one hurt the other, and does coordination help?

**STATUS: CLOSED 2026-10-12.** Raw: `experimental_results/2026-10-12-checkpoint-kv-mixed/` (`real/`, `emulation/`).
Tools: `benchmarks/lmcache/run_2a.py --ckpt`, `ckpt_cxl.c`, `kvprio_gate.py`, `analyze_mp.py`; `benchmarks/memory/kvemu3.c`.
Agreed with the user 2026-10-11 (experiment 3); strategies: uncoordinated, fixed-rate checkpoint, KV priority.

## Question
CXL writes cut a CXL reader's bandwidth by ~40% and stretch a dependent read 2.4× (`2026-10-09-cxl-topology-
interference.md`). With the KV cache in CXL, does a checkpoint written into the same cards slow KV loads, TTFT and a
latency-sensitive CPU reader of CXL — and does a simple coordination rule (KV priority) or a fixed checkpoint rate help?

## Setup
- **Real** (vLLM 0.31 + LMCache 0.5.5 multi-process, Qwen2.5-1.5B, RTX 4060 Ti): KV L1 entirely in CXL (`--l1-devdax-path
  /dev/dax1.0`, 40 GiB, LRU, watermark 0.8); Mooncake toolagent trace minutes 0–2 at 0.08× (643 requests, 24.6 min).
  Checkpoint: `ckpt_cxl` copies 96 GiB DRAM → /dev/dax0.0 (same two cards) every 8 s with 8 threads (cpus 32–39), plus one
  thread following a random chain through 1 GiB of dax0.0 (cpu 64). Modes: none; `full` (uncoordinated); `rate` 20 GB/s;
  `kvprio` (each 2 MiB piece waits while `kvprio_gate.py` sees host→GPU traffic above 1 GB/s, i.e. KV loads; hold 5 ms).
  Same requests in every run, so TTFT is compared request by request against the run without a checkpoint.
- **Emulated** (host memory traffic emulation, `kvemu3`): KV tier entirely in CXL (150 GiB on dax0.0), toolagent trace
  warmed 0–600 s, then 8B 4× [600, 1320) and 8B 8× [600, 2040); checkpoint 64 GiB every 8 s into dax0.0 above the tier, same
  modes (`rate` 20 GB/s; `kvprio` pauses while any emulated load runs), same chain reader. Per load: queue wait and service
  time; per request: delay of its last load beyond the ideal (blocks × block / link).
- Commands (detached chain `benchmarks/lmcache/run_chain_2026-10-12.sh`, run 2026-10-12 06:07–08:17 on c28):
  `run_2a.py <real> <tag> workloads/mooncake_toolagent_trace.jsonl 0 120 0.08 dax 40 [--ckpt 96:8:full | 96:8:rate:20 |
  96:8:kvprio]`; `KV3_CKPT=64:8:<mode> KV3_READER=1 kvemu3 workloads/mooncake_toolagent_trace.jsonl 65536 600 <1320|2040>
  <4|8> cxl 0 150 0.8 64 96 4 9.5 7300`. Summary of the real runs: `real/summary.txt` (`analyze_mp.py`); TTFT pairing and
  the emulated load/delay percentiles were computed from `*-client.txt` and the `L`/`S3` lines of the emulator outputs.

## Results — real
| mode | checkpoint burst | CXL busy | CPU chain reader inside / outside bursts | KV loads on the link inside / outside bursts | TTFT vs the same request without checkpoint, median (all / overlapping a burst) |
|---|---|---|---|---|---|
| none | — | — | — | — | — |
| full | 2.19 s at 47.1 GB/s | 27% | 533 / 226 ns | 30 ms at 5.9 GB/s / 30 ms at 5.5 GB/s | +0.02 s / +0.18 s |
| rate 20 | 5.15 s at 20.0 GB/s | 64% | 271 / 226 ns | 20 ms, 5.5 GB/s / 30 ms, 5.4 GB/s | −0.03 s / +0.01 s |
| kvprio | 2.19 s (max 2.38) | 27% | 534 / 226 ns | 30 ms, 5.7 GB/s / 30 ms, 5.8 GB/s | +0.01 s / +0.04 s |

All four runs: 0.436 requests/s, 3,750 prompt tokens/s, LMCache found 34.7–34.8% of the requested chunks, L1 at most 32 of
40 GiB, KV stores 0.087–0.097 GB/s on the link. Without a checkpoint TTFT p50 3.66 s, p99 26.9 s; with one, p50 3.00–3.27 s (unpaired percentiles move by more than any
effect, hence the request-by-request comparison). Requests not overlapping
a burst moved by −0.15 to −0.04 s: the run-to-run noise of the paired comparison is about ±0.15 s.

## Results — emulated (KV loads in CXL; medians unless stated)
| config / mode | load service p50 / p99 | request extra delay p50 / p99 | checkpoint burst | paused per burst | chain reader mean |
|---|---|---|---|---|---|
| 8B 4×, none | 14.6 / 38.8 ms | 4.2 / 39.4 ms | — | — | 330 ns |
| 8B 4×, full | 17.4 / 47.7 ms | 6.0 / 55.3 ms | 2.75 s | 0 | 401 ns |
| 8B 4×, rate 20 | 18.0 / 48.3 ms | 6.6 / 55.8 ms | 4.04 s | 0 | 392 ns |
| 8B 4×, kvprio | 13.4 / 38.9 ms | 3.7 / 37.2 ms | 3.14 s | 448 ms | 404 ns |
| 8B 8×, none | 35.6 / 66.7 ms (queue wait p50 53 ms) | 76 / 761 ms | — | — | 440 ns |
| 8B 8×, full | 44.1 / 89.7 ms (queue wait p50 8.1 s) | 8,166 / 11,827 ms | 4.72 s | 0 | 504 ns |
| 8B 8×, rate 20 | 44.1 / 90.6 ms (wait 8.1 s) | 8,120 / 11,832 ms | 4.78 s | 0 | 502 ns |
| 8B 8×, kvprio | 40.0 / 70.6 ms (wait 8.0 s) | 8,005 / 11,403 ms | 8.85 s | 4,223 ms | 504 ns |

## Verdict
- **On c28's GPU the checkpoint does not slow the real KV path.** KV loads move at ~5.5–5.9 GB/s on the GPU link inside
  and outside checkpoint bursts (the ×8 gen-4 link, not CXL, limits them), and TTFT changes by +0.02 s overall and
  +0.18 s for requests overlapping a burst in the uncoordinated case — at the edge of the ±0.15 s noise.
- **A latency-sensitive CPU reader of CXL is hurt badly and no rule tested protects it:** one dependent read takes 533 ns
  inside uncoordinated bursts vs 226 ns outside (2.4×), 271 ns with the 20 GB/s rate (but CXL is busy 64% of the time
  instead of 27%), 534 ns with KV priority (which protects only the KV loads).
- **At emulated server-scale KV traffic the effect appears and KV priority removes it** (8B 4×: load service +19% p50 /
  +23% p99 and request delay +44% / +40% under uncoordinated checkpoints; KV priority restores them at +14% checkpoint
  duration). A fixed checkpoint rate does not help: it spreads the same interference over longer bursts.
- **When KV stores already fill most of the CXL write bandwidth, any checkpoint tips it over** (8B 8×: KV stores ~36 of
  ~46 GB/s; with a 64 GiB checkpoint every 8 s the queue wait of KV loads goes from 53 ms to ~8 s in every mode). KV
  priority on loads cannot help there: the contended resource is CXL *write* bandwidth shared by two writers. This is the
  case for coordinated write admission across workloads (lend DRAM to one writer, or pace the checkpoint below the
  residual CXL write capacity) — not tested here.
- Limits: one small GPU (its link hides CXL read contention); emulation = CPU copies, not GPU DMA; one run per cell; the
  real KV load count is small (61–72 transfer bursts per run, 15–36 inside checkpoint bursts).
