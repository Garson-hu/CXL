# 2026-10-10 — Real LMCache KV traffic on c28, and host-memory traffic emulation of larger KV loads

**STATUS: CLOSED 2026-10-11.** Raw: `experimental_results/2026-10-10-lmcache-kv-traffic/` (`feasibility/`, `layer1/`, later
`layer2/`). Tools: `benchmarks/lmcache/` (`probe_rate.py`, `pcie_sampler.py`, `pcie_calibrate.py`, `serve_replay.py`,
`run_layer1.py`, `run_layer1_batch.sh`, `analyze_layer1.py`, `llama_drift_correction.py`), `benchmarks/memory/` (`kvemu.c`,
`run_layer2.py`, `run_layer2_batch.sh`, `analyze_layer2.py`), `benchmarks/policy/llama_control.sh`. Raw files over 500 kB
are gzip-compressed (the analysis scripts read them as they are). Agreed with the user 2026-10-10 (two layers; see "Rules agreed").

## Question
How much does a real KV cache (vLLM + LMCache) write into and read from host memory, how bursty is that traffic,
what does it do to neighbour programs, and — in emulation — what would larger KV loads do? This decides whether KV
traffic is a meaningful DRAM writer for the write-interference thesis, and calibrates the later capacity-matched
DRAM-first vs CXL-first comparison and the checkpoint-writes + KV-reads mixed experiment.

## Rules agreed (2026-10-10)
- Layer 1 = the real system on c28's GPU: KV store/load traffic, bursts, TTFT, neighbour slowdown. LMCache's reported
  bandwidth is kept apart from the GPU's measured PCIe traffic.
- Layer 2 = **host memory traffic emulation**, trace-driven, at 1×, 4×, 8× trace speed with 8B and 70B KV sizes.
  CPU copies are not GPU DMA: layer 2 characterizes host-memory traffic and its effect on neighbours, and is not
  presented as multi-GPU serving. Its store/load sizes and timing are calibrated from layer 1. For targets above
  what the device can take (e.g. 70B at 8× vs ~44 GiB/s into CXL) target rate, achieved rate and backlog are all
  recorded. Peaks and bursts are analysed, not only averages.

## Feasibility findings (2026-10-10, `feasibility/`)
- **GPU capacity.** Qwen2.5-1.5B (fp16, eager) with LMCache on the RTX 4060 Ti: the first 200 conversation requests
  sent at once (1 output token, prompts truncated to 16384 tokens for 55 of them) ran at 10,726 prompt tokens/s, of
  which 9,769/s computed (8.9% cached by vLLM). Real-time replay of the traces needs 25–38 k new prompt tokens/s
  (per-minute values, first 20 min, both traces): with one output token the card carries at most ~0.37×.
- **Overload at 0.2×** (`overload-0.2x/`, run stopped after 35 requests): with the trace's output lengths (cap 1024) and
  prompts up to 32,768 tokens the card served ~4,600 prompt tokens/s (smoke run: 725,233 prompt tokens in 159 s), so
  0.2× (~7 k/s offered in trace minutes 0–5) overloads it: TTFT rose to 34–38 s within the first trace seconds and kept
  growing. Layer 1 was redesigned with two operating points (below).
- **PCIe counter calibration** (`pcie-calibration.txt`): 8 × 1 GiB copies at 12.30 GiB/s (D2H) / 12.48 GiB/s (H2D) by
  wall clock read 14,738 / 14,544 MB/s in NVML's 20 ms counters (link gen 4 throughout; pinned and pageable host
  memory alike). NVML counts ~1.12× (D2H) / ~1.09× (H2D) the payload; payload figures below divide by these factors.
- **LMCache's reported bandwidth vs the GPU's counter — not settled (corrected 2026-10-10 14:30).** In the 20 s smoke run
  LMCache logged 381 stores, 18.28 GiB in total, at 6.5–9.7 GB/s each, while the TX counter never exceeded 3,236 MB/s
  in a 20 ms window (p99 3,229) and integrated to 21.8 GB ≈ 19.5 GB payload ≈ the stored volume. A first reading
  ("LMCache's figure is too high") was premature. Its store clock spans the whole store and stops after
  `store_stream.synchronize()` (`cache_engine.py` 469–592, `observability.py`), and with vLLM's 2048-token prefill
  chunks every store is ~56 MiB (2048 × 28 KiB): moved at ~9 GB/s it lasts ~6 ms, and one such store per 20 ms window
  reads exactly 0.0587 GB / 0.02 s = 2.94 GB/s payload = 3.23 GB/s in NVML units — the observed ceiling. The counter's
  20 ms window cannot resolve these bursts; their instantaneous rate is LMCache's, their per-20-ms rate the counter's.
  Loads are different: LMCache's retrieve clock also stops after `load_stream.synchronize()`, yet its figures
  (16–24 GB/s) exceed what this ×8 gen-4 link carried in the calibration (12.5 GiB/s). Resolved for stores, not for loads
  (2026-10-11, v2 sampler): stores — 5 ms bins of the cumulative counter show each 2048-token store as one burst of
  0.058 GB lasting ≤ 10 ms with a peak bin of ~7.8 GB/s (p50), so LMCache's ~9 GB/s per store is right. Loads — in the
  200 ms before each retrieve's log line the counter shows ~64% of the logged size (normal-conv-v2: 0.105 GB vs 0.164 GiB
  p50) and no window above the link rate; LMCache's retrieve figure is therefore not a link rate, but where the rest of
  the logged volume goes was not traced (retrieves are 1–3% of the KV volume here, so nothing below depends on it).
- **Sampler v1 lost windows** (2026-10-10): in the 38-minute runs the 20 ms throughput thread, sharing cpu 127 with the
  server, covered only 35% of the time (integral 48 GB vs 138 GiB stored). v2 (14:50) reads NVML's cumulative PCIe byte
  counters every ~1.4 ms on cpu 95 into 5 ms bins (exact totals; 20 ms coverage 96–97%). The v1 normal-load runs
  (`normal-conv`, `normal-tool`) keep their TTFT/rate/LMCache data; their counter data is superseded by the `-v2` reruns.
  5 ms bins can read above the link rate (max 18.9 GB/s) because a counter read can cover up to ~6.4 ms; peaks in 5 ms
  bins carry about ±30%.

## Layer 1 setup
vLLM 0.31.0 + LMCache 0.5.5 (`LMCacheConnectorV1`, local CPU backend, chunk 256 tokens, 100 GB host cache), Qwen2.5-
1.5B-Instruct, max model length 32768, GPU memory utilization 0.85, eager, fp16; server pinned to cpus 96–127 (CCDs 6–7),
replay client on 124–126, PCIe sampler on 127. Mooncake traces replayed open-loop (requests sent at their scaled
timestamps whatever happened before), the trace's output lengths capped at 1024, ignore EOS. Placement = the safe one
of `2026-10-09-cxl-topology-interference.md` (neighbours CCD 0–4, server CCD 6–7). Two operating points:
- **Normal load, 0.08×**: trace minutes 0–3 of conversation and of toolagent, no neighbour, run to the last answer
  (~38 min each): TTFT, achieved request and token rates, KV traffic.
- **Overload stress test, 0.2×**: conversation from trace minute 0, 10 min of serving, then requests still open are
  cancelled: the most KV traffic this card produces; alone and beside each policy-campaign neighbour on cpus 0..
  (reader 8 threads; PageRank, Adam step, llama.cpp 80 threads), each with a 60 s window before serving (server idle)
  as the neighbour's baseline. TTFT here measures the queue, not the service.
Reported per run: the replay rate is the offered load only; achieved requests/s, prompt and output tokens/s, the
backlog (requests sent but unanswered) over time, KV traffic by the GPU counter and by LMCache's log.

## Layer 1 results (real vLLM + LMCache on the RTX 4060 Ti, Qwen2.5-1.5B; `layer1/summary.txt`)
| run | achieved (offered 0.08× / 0.2×) | TTFT p50 / p99 | KV stores on the link | store bursts | KV loads (LMCache) |
|---|---|---|---|---|---|
| normal-conv-v2 | 0.243 req/s, 2,790 prompt tok/s, 85 out tok/s | 7.0 / 74.4 s (thirds 4.2 / 5.0 / 29.5 s) | 198.7 GB in 2,284 s = 0.087 GB/s incl. ~0.021 GB/s background ≈ LMCache's 138 GiB | 2,823 × 0.058 GB, ≤ 10 ms, peak 5 ms bin p50 7.8 GB/s, every ~0.28 s | 90 retrieves, 22.9 GiB |
| normal-tool-v2 | 0.475 req/s, 4,001 prompt tok/s (45% cached by vLLM) | 6.6 / 94.2 s | 192.8 GB = 0.085 GB/s | 2,985 × 0.058 GB | 195 retrieves, 33.5 GiB |
| sat-* (5 runs, 10 min) | 0.37–0.39 req/s, 4,200–4,450 prompt tok/s; 681–696 of 918 requests never answered | queue (40 → 145 s) | 82–85 GB = 0.135–0.141 GB/s | ~1,300 × 0.058 GB, peak bin p50 ~7.8, max 11.5 GB/s | 13–22 retrieves, 2.5–2.7 GiB |

The v1 `normal-conv` run of the same window had TTFT thirds 3.3 / 4.1 / 4.1 s and a backlog peak of 19 (v2: 32); 0.08×
sits near this card's capacity, so the last third queues in some runs. LMCache's per-store records: 2048 tokens (p50) in
5.9 ms (p50) — ~9.9 GB/s on the link; one request's consecutive stores 250–270 ms apart (~7,300 prefill tokens/s per
request). **Neighbours beside saturated real serving** (60 s server-idle window as baseline): reader −0.07% (100 ms slices
with a store burst −0.12%), PageRank −0.15%, Adam step +0.07%; llama.cpp raw +17.1% is its own context-growth drift
(36 → 26 tok/s alone over 12 min, `layer1/llama-control-alone.txt`), corrected **+0.1%** (`llama-corrected.txt`).

## Layer 2 results (HOST MEMORY TRAFFIC EMULATION, `layer2/summary.txt`, `summary.csv`)
kvemu, conversation trace, cache warmed with trace seconds 0–600, ~245 s of traffic; Llama-3.1-8B / 70B block sizes;
calibrated per transfer 9.5 GB/s, 2048-token pieces, 7,300 tokens/s per request; tier 200 GiB in DRAM or in CXL
(dax0.0); 64 workers on CCDs 6–7 (+ SMT siblings); stores = non-temporal stores from a cache-resident source, loads =
streaming loads. One run per cell. **Emulation limit: the DRAM tier's peaks are capped at ~150 GB/s per 20 ms by the two
worker CCDs' links, while the offered peaks reach 185–301 GB/s, so DRAM-tier bursts — and the harm they do — are
understated above that level.** Offered = what the trace schedule demands if every transfer starts on time.

| config | offered mean | offered worst 1 s / 20 ms p99 / max (GB/s) | DRAM tier: achieved, backlog max, late max | CXL tier: achieved, backlog max, late max |
|---|---|---|---|---|
| 8B 1× | 5.4 GB/s | 16 / 62 / 105 | 5.1, 0.3 GB, 0 ms | 5.1, 2.5 GB, 0 ms |
| 8B 4× | 21.2 | 37 / 113 / 212 | 19.8, 1.6 GB, 2 ms | 19.8, 4.5 GB, 68 ms |
| 8B 8× | 41.8 | 64 / 185 / 301 | 38.9, 3.1 GB, 15 ms | 38.9, 30.4 GB, 589 ms |
| 70B 1× | 13.6 | 35 / 101 / 169 | 13.0, 1.0 GB, 0 ms | 13.0, 6.6 GB, 27 ms |
| 70B 4× | 53.0 | 84 / 154 / 253 | 50.7, 5.3 GB, 15 ms | **46.7: cannot keep up**, deficit 1.39 TB, 28 s late |
| 70B 8× | 104.5 | — | 99.6, 13.4 GB, 68 ms | **46.8: cannot keep up**, deficit 14.1 TB, 286 s late |

(achieved = stores; loads 0.3–2.9 GB/s in addition. "Deficit" = offered minus done, accumulated: the emulator keeps
going until every planned byte is written, so these runs last up to 10 min longer than planned.)

Neighbour slowdown, KV tier in **DRAM / CXL** (%, own 60 s BEFORE window as baseline; llama.cpp drift-corrected):

| neighbour | 8B 1× | 8B 4× | 8B 8× | 70B 1× | 70B 4× | 70B 8× |
|---|---|---|---|---|---|---|
| reader, 8 threads | +0.9 / +0.1 | +2.9 / +0.7 | +6.2 / +1.2 | +1.9 / +0.6 | +7.3 / +1.4 | +16.8 / +1.7 |
| PageRank, 80 | +2.0 / −0.8 | +7.4 / +0.3 | +15.8 / −0.2 | +4.2 / −0.0 | +21.9 / +0.1 | +40.2 / −0.5 |
| Adam step, 80 | +1.4 / +0.1 | +8.1 / +0.2 | +17.8 / +0.2 | +3.5 / +0.1 | +22.6 / +0.1 | +62.7 / +0.1 |
| llama.cpp, 80 (±5 method noise) | +3.8 / −2.3 | +2.7 / −1.7 | +3.5 / +1.5 | +2.1 / −3.0 | +11.2 / −5.4 | +22.5 / −2.0 |

Tails (DRAM / CXL tier): PageRank trial time p99 +26 / +4% (8B 8×), +36 / +4% (70B 4×), +49 / +4% (70B 8×); Adam step
p99 +31 / +1%, +45 / +0%, +75 / +0%, worst step +83% (70B 8×, DRAM). Reader's worst 100 ms slice: 60 GiB/s with the DRAM
tier at 70B 4×/8× (p1 80 → 70 GiB/s at 70B 8×) vs 66–73 GiB/s with the CXL tier.

## Verdict
- **Real KV traffic from one small GPU does not interfere.** On c28 the real LMCache store stream is ~0.065–0.14 GB/s on
  average — 2048-token bursts of 0.058 GB at ~9–10 GB/s lasting ~6 ms, every ~0.28 s — and no neighbour moves
  (−0.15% to +0.1%, also in the 100 ms slices that contain a burst). The card's compute caps it far below the trace.
- **Emulated KV traffic at server scale does** (host memory traffic emulation, not multi-GPU serving): with the KV
  tier in DRAM the neighbours lose +1–4% at 8B 1× (5 GB/s mean, bursts to 105 GB/s), +3–8% at 8B 4×, +4–18% at 8B 8×
  and +17–63% at 70B 8× (tails up to +83%); the harm grows with the offered rate and its bursts, and the emulator
  understates DRAM bursts above ~150 GB/s.
- **Placing the KV tier in CXL removes that harm** for every neighbour and load (≤ 1.7%, tails ≤ +4%), but **CXL alone
  cannot carry the heavier loads**: bursts queue (8B 8×: 30 GB backlog, 0.6 s late) and from 70B 4× on (offered mean
  53 GB/s > ~47 GB/s) it falls behind without bound. That is the regime the interference-aware DRAM loan exists for —
  the original thesis applied to KV traffic; whether the loan carries it without the harm is the next experiment
  (capacity-matched DRAM-first vs CXL-first, then the checkpoint + KV mixed experiment).
