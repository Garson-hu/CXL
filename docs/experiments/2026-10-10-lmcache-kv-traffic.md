# 2026-10-10 — Real LMCache KV traffic on c28, and host-memory traffic emulation of larger KV loads

**STATUS: OPEN.** Raw: `experimental_results/2026-10-10-lmcache-kv-traffic/` (`feasibility/`, `layer1/`, later
`layer2/`). Tools: `benchmarks/lmcache/` (`probe_rate.py`, `pcie_sampler.py`, `pcie_calibrate.py`, `serve_replay.py`,
`run_layer1.py`, `run_layer1_batch.sh`). Agreed with the user 2026-10-10 (two layers; see "Rules agreed").

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
  (16–24 GB/s) exceed what this ×8 gen-4 link carried in the calibration (12.5 GiB/s). To be resolved by aligning each
  logged store/retrieve with the counter windows around it (runs from 2026-10-10 14:30 on log the mono↔wall offset).

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
