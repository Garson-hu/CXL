# 2026-10-27 — Exploratory study: reuse windows, future-aware prefetching and cache capacity in training and inference

**STATUS: CLOSED 2026-10-27 (branch `explore/reuse-window-prefetch`; not merged).** **Findings in one paragraph.** *Training:* the
batch schedule is known a whole epoch ahead in standard loaders (and for all epochs from the seed), but a future-aware prefetcher
needs almost none of it: with storage faster than the trainer (BeeGFS at ≥ 8 streams, 0.25–0.82 GB/s, against a 0.21 GB/s A100
trainer) a window of 0.1–0.25 s — one file's fetch time — already yields ~100% hits at every capacity from 30 GiB up; windows of
tens of seconds matter only when the storage bandwidth is within ±10% of the rate the trainer needs after cache retention, and no
window helps when storage is slower than that (the single-stream reader, a 16× faster trainer). The hit-vs-window curve is a
saturating exponential H = H0(C) + (1 − H0)(1 − e^(−W/τ)) whose time constant τ is set by the bandwidth margin, not by the
capacity (τ ≈ 0.2 s when B ≥ 1.15× the demand; 5–50 s at 0.92–0.98×), and whose floor H0(C) = c + (1 − c) ln(1 − c), c = C / dataset,
is the LRU retention under per-epoch reshuffling (our derivation, matched by the real trace to ±0.002). Capacity's value for training is
therefore retention, not prefetch depth: 60 GiB retains 7.5% of a 166 GiB dataset and 180 GiB all of it after the first epoch, which
removes the storage traffic entirely and makes the trainer independent of storage speed. A naive prefetcher that does not protect
resident data due inside its window loses up to 6 points at long windows. *Inference:* a historical window used for retention does
not beat LRU (−0.03 … +0.04 at every capacity), a historical window used for admission does (+0.05 … +0.19 over LRU, 6–30× fewer
writes) but stays 0.001–0.018 below the RQ1 adaptive policy, whose gap rule sets the window from the measured residence; the best
fixed window grows with capacity (50 s at 30–60 GiB, 200–300 s at 120–360 GiB) and fails at 720 GiB where admit-all wins. Tripling
the capacity with CXL (60 → 180 GiB) is worth +0.04 to LRU and +0.155 / +0.073 to reuse-aware admission (conversation / tool agent).
The two workloads do not share a window–hit law: training's window is a latency to hide, inference's is a residence to match. Nothing
here changes the main line's negative joint-benefit result. An independent exploratory branch of the project, from the
meeting with Dr. Mueller: (training) how much FUTURE knowledge of the batch schedule is useful for prefetching training samples into
a DRAM/CXL cache, as a function of the future window W and the capacity C; (inference) whether a HISTORICAL window of reuse
information improves LRU for the KV cache, and how the useful window relates to capacity; (both) what a small DRAM-only cache
(60 GiB) loses against a larger DRAM + CXL cache (180 GiB). It does not change the research direction, the three RQs, the charter,
the decision report or the gate status, and it does not touch the Phase 3 negative joint-benefit result. Evidence types: **REAL**
(a real CosmoFlow training run on the A100 node c33 with an explicit schedule and an access trace; real sampler measurements),
**SIM** (trace-driven prefetch and KV-cache replay), **LIT** (published results, cited as such and kept apart from ours).
Raw: `experimental_results/2026-10-27-reuse-window-prefetch/` (`train/`: the trace run, `train/sim/`: sweeps; `infer/`: the KV
campaign, `infer/stats/`, `infer/horizon/`; `run_all.sh` / `run_sweep.sh` = exact commands). Code: `scripts/train_prefetch_sim.py`
(new), `scripts/kv_admission_sim.py` (window policies added, existing policies unchanged), `scripts/kv_window_stats.py`,
`kv_window_tables.py`, `kv_horizon_eval.py`, `window_figs.py` (new), `experimental_results/.../train/train_trace.py` (new).

## Task A — what exists, what the literature says
**Training material in the group's tree (`~/hvac`):** the CosmoFlow TensorFlow/Keras benchmark (NERSC implementation, MLPerf HPC
v1.0 data) used for the HVAC and FitCache experiments (`~/hvac/benchmark/cosmoflow-benchmark-master`: `train.py`, `data/cosmo.py`,
configs, PDSW run scripts; conda env `hvac_tf`, TensorFlow 2.14 with GPU), the HVAC client (`GHU_HVAC`) and FitCache++
(`FitCachePP`), DeepCAM / dinov2 / Megatron-LM checkouts WITHOUT data on this cluster, and the CosmoFlow dataset on BeeGFS
(`/mnt/beegfs/ghu4/hvac/cosmoUniverse_2019_05_4parE_tf_v2`: 524,288 training TFRecords = 1.7 TB; the `_mini` subsets `train_1024`
and `train_61440` = 61,440 files of 2.9 MB mean = 178 GB / 166 GiB). One sample = one GZIP TFRecord file of a 128³ × 4 int16 volume,
so the sample schedule IS the file-read order. There was no existing training access trace with timestamps: one was collected
(Task B1). **Inference material:** the Mooncake conversation and tool-agent traces, the agent-runtime traces, and the RQ1 admission
simulator with LRU / SLRU / second touch / `2nd_int` / the adaptive regime policy / oracle and the bounded-ghost machinery.
**Literature (LIT, not our findings).** NoPFS (Dryden et al., SC'21, "clairvoyant prefetching") rests on exactly the premise of the
training question: the SGD access order is a function of the sampler's seed, so where and when every sample will be read is known
in advance; it reports up to 5.4× training-I/O speedups on ImageNet-1k/22k and CosmoFlow. Quiver (Kumar & Sivathanu, FAST'20)
avoids thrashing when the cache is much smaller than the working set with *substitutable* hits (any cached sample instead of a
specific one) and shares the cache across jobs. SHADE (Khan et al., FAST'23) caches by sample importance and reports up to 4.5× the
hit ratio of LRU at the same size. HVAC (ORNL, CLUSTER'22) is a transparent node-local read cache for Summit (67–85% of training time
in PFS I/O at scale); FitCache (IPDPS'26, this group) adds multi-tier fastest-responder reads (−40% training time on Frontier).
SOLAR (SC'22) precomputes the shuffle lists of all epochs and orders them to maximize reuse between consecutive epochs; Lee & Bahn
show that full per-epoch reshuffling defeats the OS buffer cache. The known rule of thumb for an LRU cache under per-epoch
reshuffling is "hit rate ≈ the cached fraction of the dataset" (cloud-storage studies); none of these papers gives a window-vs-hit
function, which is what this study measures.

## Task B1 — how far ahead a training system knows its batches (REAL measurements)
- **PyTorch samplers (measured on c28):** `RandomSampler` draws the WHOLE epoch order with `torch.randperm` when its iterator is
  created, i.e. at epoch start — 0.5 ms / 4.4 ms / 277 ms and 0.5 / 4 / 108 MiB for 61,440 / 524,288 / 14.2 M samples;
  `DistributedSampler` is deterministic in (seed, epoch), so ANY future epoch's order can be computed ahead (1.2 / 12 / 545 ms per
  rank); `WeightedRandomSampler` is known at epoch start for that epoch's weights — importance sampling that updates weights per
  batch (SHADE-style) breaks the lookahead; the DataLoader's own fetch horizon is `prefetch_factor × num_workers` = 4 batches.
- **TensorFlow (the CosmoFlow benchmark as run by the group):** `tf.data.Dataset.shuffle(len(files), reshuffle_each_iteration=True)`
  draws the epoch's permutation inside the shuffle op when the epoch's iteration starts; it is not exposed to the application and is
  reproducible only with a fixed seed; the pipeline's lookahead is `prefetch(4)` batches. Replacing it with an explicit seeded
  permutation (our `train_trace.py`) makes every epoch's order available at job start: 0.20 ms for 1,024 files, 10–11 ms (0.49 MB) for
  61,440, before the first batch (18 s into the pilot, ≈ 9 s in the full run).
- **Runtime-available vs oracle:** in the standard pipelines the order of the CURRENT epoch is known at its start (a lookahead of one
  epoch, 1.7 h here) and, with a seeded sampler, the order of all epochs from job start; dynamic sampling, curriculum or
  per-batch importance updates reduce that to whatever the sampler commits to. CosmoFlow has none of these (fixed dataset, no
  augmentation, one sample per file), so batch IDs determine the file reads exactly. The simulator therefore distinguishes
  `avail all` (seeded: all epochs known at job start), `avail epoch` (standard: known at epoch start) and `avail none`.
- **The real run (REAL):** CosmoFlow on c33 (A100 80 GB), batch 4, SGD, the benchmark's model and parse; pilot on `train_1024`
  (2 epochs): 5.4 samples/s with the benchmark's single-stream reader on cold BeeGFS (15.7 MB/s — I/O-bound: BeeGFS delivers
  0.064 GB/s to one stream, 0.33 / 0.52 / 0.66 / 0.82 GB/s to 4 / 8 / 16 / 32 streams from c33; 0.06 / 0.32 / 0.49 from c28) and
  9.9 samples/s (28.7 MB/s) once the files were in the node's page cache — the trainer's compute-bound rate. The full run
  (`run-61440`: 61,440 files, 3 epochs, 8 files read concurrently, 4 parallel parses) gives the demand timeline of a compute-bound
  trainer at ~10 samples/s = 29 MB/s; it ran 63.5 / 74.9 / 74.9 samples/s in epochs 0 / 1 / 2 (184 / 217 / 217 MB/s of files; step 62 → 53 ms at batch 4, p99 91 → 70 ms —
  epoch 0 pays cold BeeGFS reads, epochs 1–2 partly hit the node's 125 GB page cache), i.e. the demand is a smooth stream of
  205 MB/s mean, 222 MB/s p99, 233 MB/s max per second, and the tf.data pipeline itself pulls each file only 0.4–0.85 s before the
  step that consumes it (its own lookahead: 8 files in flight + 8 batches). Against the measured BeeGFS bandwidth this trainer needs
  ≥ 8 parallel streams just to keep up (0.52 GB/s) and 3.4× more than one stream delivers (0.064 GB/s); the schedule of all three
  epochs was known 8.1 s after job start (10–11 ms per epoch), the first batch ran at ≈ 9 s, the run took 2,618 s.

## Task B2 / B3 — the future-window sweep on the real trace (SIM on REAL demand; `train/sim/`, `run_sweep.sh`; fig-train-window, fig-train-capacity)
**Model (`train_prefetch_sim.py`).** The demand stream = the training steps of the real run (each sample due at the start of the step
that consumes it, 184,320 demands over 3 epochs, 2,609 s); one cache of C bytes fed by one storage channel of B bytes/s (FIFO, no
preemption, demand fetches ahead of queued prefetches); the prefetcher may fetch any sample due within the next W seconds whose
epoch order is available (`all`: every epoch from the seed at job start; `epoch`: from the epoch's start; `none`); prefetched data is
pinned until its use and issued only when the cache can hold it (so the window is capacity-bound); resident data due inside the
window is protected from eviction until that use (a count of pending demands — a sample due in two epochs inside one window keeps
its protection until the second); a demand that finds its prefetch in flight or queued is a MISS (late prefetch, no second fetch,
the stall recorded); misses fetch on demand and are inserted; used data stays (LRU) for the next epoch. Epoch 0 is the cold start,
epochs 1–2 are scored. Bandwidths: the measured BeeGFS points (0.064 GB/s one stream, 0.33 at 4, 0.82 at 32 streams), the
near-demand points 0.15 / 0.20 / 0.25 GB/s, 2.0 (an NVMe-class store) and ∞; trainer speeds ×1 (measured), ×4, ×16 (faster GPUs
or several trainers on one link). Two bugs found and fixed by the sweeps themselves are recorded in `run_sweep.sh` (the first pass
lost the protection of samples due in two epochs; the second counted epoch-0 prefetch traffic).

| hit rate (epochs 1–2), storage B → | 0.064 GB/s (1 stream; 0.3× demand) | 0.15 (0.7×) | 0.20 (0.92×) | 0.25 (1.15×) | 0.33 (1.5×) | 0.82 (3.8×) | 0.82, trainer ×4 (0.94×) | 0.82, trainer ×16 (0.24×) |
|---|---|---|---|---|---|---|---|---|
| C = 30 GiB, W = 0 / 5 / 25 / 100 / 300 s | .018 / .018 / .018 / .018 / .018 | .018 / .018 / .018 / .018 / .018 | .018 / .119 / .262 / .779 / .779 | .018 / 1.00 / 1.00 / 1.00 / 1.00 | .018 / 1.00 / 1.00 / 1.00 / 1.00 | .018 / 1.00 / 1.00 / 1.00 / 1.00 | .018 / .290 / 1.00 / 1.00 / 1.00 | .018 / .018 / .018 / .018 / .018 |
| C = 60 GiB (DRAM-only), W = 0 / 5 / 25 / 100 / 300 s | .075 / .075 / .075 / .075 / .075 | .075 / .075 / .075 / .075 / .075 | .075 / .247 / .600 / 1.00 / 1.00 | .075 / 1.00 / 1.00 / 1.00 / 1.00 | .075 / 1.00 / 1.00 / 1.00 / 1.00 | .075 / 1.00 / 1.00 / 1.00 / 1.00 | .075 / .729 / 1.00 / 1.00 / 1.00 | .075 / .075 / .075 / .075 / .075 |
| C = 120 GiB, W = 0 / 5 / 25 / 100 / 300 s | .368 / .368 / .368 / .368 / .368 | .368 / .449 / .488 / .513 / .513 | .368 / .782 / 1.00 / 1.00 / 1.00 | .368 / 1.00 / 1.00 / 1.00 / 1.00 | .368 / 1.00 / 1.00 / 1.00 / 1.00 | .368 / 1.00 / 1.00 / 1.00 / 1.00 | .368 / 1.00 / 1.00 / 1.00 / 1.00 | .368 / .368 / .368 / .368 / .368 |
| C = 180 GiB (DRAM + CXL) and up, any W | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| fine windows at C = 60 GiB: W = 0.1 / 0.25 / 0.5 / 1 s | – | – | – | .999 / 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 / 1.00 | – | – |

1. **Three regimes, set by the storage bandwidth against the rate the trainer needs after retention, (1 − H0(C)) × 0.21 GB/s.**
   *Comfortable* (B ≥ 1.15×): a window of 0.1–0.25 s — one 2.9 MB file at 9–45 ms plus the queue — gives 100% hits at every
   capacity; W95 = 0.1 s; nothing improves beyond it. *Marginal* (0.92–0.98×, i.e. B = 0.20 GB/s or the ×4 trainer on 0.82 GB/s):
   the window smooths the queue: at 60 GiB 5 s → 0.25, 25 s → 0.60, 50 s → 0.98, 100 s → 1.0; at 120 GiB, where retention lowers the
   needed rate, 25 s suffices; at 30 GiB the plateau is 0.78 (the capacity bounds the queue the window can build: late prefetches).
   *Starved* (≤ 0.7×: one BeeGFS stream, the ×16 trainer): no window helps at 30–60 GiB — the storage cannot supply the stream,
   every prefetch arrives late, the backlog is unbounded; at 120 GiB retention makes 0.15 GB/s almost enough (0.37 → 0.51).
2. **More future knowledge does not hurt with a window-aware cache and does not help beyond τ.** With the protection of resident
   data due inside the window, every curve is monotone and flat after its knee up to W = 1,200 s (the prefetcher simply stops at
   the capacity: 297 s of data at 60 GiB); the storage traffic is the same at every W > 0 (329 GB per two epochs at 60
   GiB = the bytes LRU misses anyway, fetched earlier); the costs of a long window are occupancy (the cache fills with pinned future
   data up to C) and lead time (p50 = W up to the capacity bound). A **naive prefetcher** (no protection) loses 0.2 → 5.7 points at
   60 GiB as W grows from 5 to 200 s (0.998 → 0.943): it evicts retained samples it will need inside its own window and refetches
   them late — the "cache pollution by early prefetch" the brief asked about, and it is an implementation property, not a window one.
3. **Lookahead needed in time:** 0.1–0.25 s in the comfortable regime, 50–100 s in the marginal one. The standard tf.data pipeline
   already pulls 0.4–0.85 s ahead (B1), so with adequate storage it needs no explicit schedule at all; the whole-epoch (or
   whole-run) knowledge of B1 is only needed when the storage is marginal — and then it is 1–2 minutes of it. `avail epoch`
   (order known from the epoch's start) equals `avail all` at every window (the first files of an epoch are fetched on demand in
   9 ms each; 9–13 samples per run).
4. **Late / wasted prefetches, stalls:** in the comfortable regime 0 late prefetches at W ≥ 0.25 s (18–104 at 0.1 s), 0 wasted,
   stall 0; in the marginal regime late prefetches fall from 33k (W = 5 s, ×4) to 0 (W ≥ 10–50 s); in the starved regime every
   prefetch is late (113,641 of 113,641 at 60 GiB) and the queue never drains — the trainer would run at storage speed, which the
   trace-driven replay cannot show (its timeline is the real GPU-bound run's).

## Task B4 — the window–hit function (`train_window_fit.py`, fig-train-fit)
- **Floor, H0(C) = LRU retention under per-epoch reshuffling.** Two independent uniform permutations put a sample at fractions p, p′
  of consecutive epochs; the distinct bytes between its two reads are (1 − p) + p′ − (1 − p)p′ of the dataset, so LRU with
  c = C / D hits iff p(1 − p′) ≥ 1 − c, whose probability is **H0(c) = c + (1 − c) ln(1 − c)** (c < 1; 1 above). The real trace (W = 0,
  `none` sweep): 0.004 / 0.018 / 0.040 / 0.075 / 0.186 / 0.368 / 0.679 / 1.000 at c = 0.09 / 0.18 / 0.27 / 0.36 / 0.54 / 0.72 / 0.90 /
  1.09 against 0.004 / 0.017 / 0.041 / 0.075 / 0.185 / 0.368 / 0.681 / 1.000 predicted (±0.002). The literature's "hit ≈ cached
  fraction" (c) overestimates LRU by 2–5× (0.36 vs 0.075 at 60 GiB); c²/2 is right only for small c.
- **Rise.** Of the three forms tried (exponential, rational, linear ramp), all anchored at the measured H0(C): in the comfortable regime
  (B = 0.33) the exponential and the ramp fit exactly (RMSE 0.000, τ = W* = 0.2 s, the smallest grid value) and transfer to another
  bandwidth (B = 0.25 held out: RMSE 0.000) and to the unseen capacity (leave-one-out 0.000); in the marginal regime (B = 0.20) the
  exponential fits best (RMSE 0.025 vs 0.046 rational, 0.023 ramp but worse out of sample) with **τ = 49.5 / 23.8 / 5.5 s at
  C = 30 / 60 / 120 GiB** and plateau H1 = 0.79 / 1.00 / 1.00; leave-one-capacity-out RMSE 0.07 (three capacities to interpolate from),
  and it does NOT transfer to B = 0.25 (RMSE 0.23) because τ collapses from tens of seconds to 0.2 s as the margin opens. The ×4
  trainer at 0.82 GB/s (margin 0.94×) gives τ = 11.5 / 3.9 / 0.2 s.
- **The function, as the data supports it:** H(W, C, B) = H0(C) + (H1 − H0(C)) (1 − e^(−W/τ)), with H0(C) = c + (1 − c) ln(1 − c),
  H1 = 1 when B ≥ (1 − H0(C)) r and the capacity holds the queue, and τ a function of the margin B / ((1 − H0(C)) r): ≈ one file's fetch
  time for margins ≥ 1.15, 5–50 s near 1, undefined (no rise) below ~0.7. Capacity enters only through H0 (which lowers the needed
  bandwidth and shortens τ) and the queue bound; it does not set the window. It is validated across bandwidths within a regime
  and across capacities (interpolation in log C), and it fails across regimes — which is the point: the window is a bandwidth
  quantity.

## Task D (training) — capacity: DRAM-only 60 GiB vs DRAM + CXL 180 GiB (`none` and `all-bw*` sweeps; fig-train-capacity)
| capacity | c = C / D | LRU hits, no prefetch | hits with prefetch (B ≥ 0.25 GB/s, W ≥ 0.25 s) | storage traffic per two epochs (GB): no prefetch / with prefetch | hits with prefetch at B = 0.20 (W = 50 s) | at B = 0.064 (any W) |
|---|---|---|---|---|---|---|
| 30 GiB | 0.18 | 0.018 | 1.000 | 350 / 350 | 0.423 | 0.018 |
| 60 GiB (DRAM-only) | 0.36 | 0.075 | 1.000 | 329 / 329 | 0.983 | 0.075 |
| 120 GiB | 0.72 | 0.368 | 1.000 | 225 / 225 | 1.000 | 0.368 |
| 180 GiB (DRAM + CXL) | 1.09 | 1.000 | 1.000 | 0 / 0 | 1.000 | 1.000 |

With adequate storage bandwidth the small DRAM-only cache already reaches 100% hits by prefetching, so the CXL capacity does not
add hits; it removes the storage traffic (178 GB per epoch at 60 GiB → 0 once the dataset fits) and makes the trainer independent
of the storage: at one BeeGFS stream the 60 GiB cache gives 7.5% and the 180 GiB cache 100%. The best window does not change with
capacity in the comfortable regime (0.1–0.25 s everywhere) and shrinks with capacity in the marginal one (τ 50 → 5 s from 30 to
120 GiB) because retention lowers the rate the storage must supply. "How long a reuse can be retained": one epoch is the only reuse
distance in training (820 s here), so a cache retains a sample for the next epoch with probability H0(c): 7.5% at 60 GiB, 100% at
180 GiB; there is no intermediate horizon to tune.


## Task C — inference: window-based reuse LRU against the existing policies (SIM, `infer/`)
**C1 — historical window statistics (`infer/stats/`, `kv_window_stats.py`; offline, trace only).** For every scored block access,
the number of the block's accesses in the past W seconds and whether it is accessed again within the next 60 / 300 / 900 s:

| trace, W = 300 s | class | share of accesses | P(next access ≤ 300 s) | share of the reuses within 300 s |
|---|---|---|---|---|
| conversation | unseen in the past 300 s | 70.3% | 16.8% | 42.3% |
| conversation | 1 access | 15.6% | 40.6% | 22.7% |
| conversation | 2 accesses | 6.6% | 54.1% | 12.9% |
| conversation | ≥ 3 accesses | 7.5% | 83.1% | 22.2% |
| tool agent | unseen in the past 300 s | 47.2% | 17.5% | 16.0% |
| tool agent | 1 access | 10.9% | 40.9% | 8.7% |
| tool agent | 2 accesses | 4.6% | 54.2% | 4.8% |
| tool agent | ≥ 3 accesses | 37.3% | 97.6% | 70.5% |

The window count carries information beyond "seen": P(reuse within 300 s) rises 41 → 54 → 83% with 1 → 2 → ≥ 3 past accesses
(conversation). Recency carries most of it: a previous access 10–300 s ago means 44–53% reuse, > 900 s ago 7%; a previous access
within 10 s means 99.6% (the burst: the same prefix looked up by consecutive requests — 4.5% of the conversation accesses and 35% of
the tool-agent accesses, which is why the tool-agent baselines start at 0.61). Shorter windows (10–50 s) see almost nothing but
the burst class (unseen 92–96%). And, as RQ1 found, the blocks unseen within 300 s (70% / 47% of accesses) still hold 42% / 16% of
the future reuses: first-touch reuse is not predictable from a historical window.

**C2 — the policies (added to `kv_admission_sim.py`, suffix `:W`).** `wslru:W` = LRU with a protected segment for blocks with ≥ 2
accesses inside the last W s; protection expires after W s without an access (the block goes to the probation tail); eviction from
probation first. `wlfu:W` = among the K = min(64, cap/16) least recently used blocks, evict the one with the fewest accesses in the
last W s (ties: the least recent). `wslru2nd:W` = `wslru:W` plus admission only of blocks looked up within the last W s (first block of
a request always admitted): the window as an admission rule. Metadata: the access times inside the window per block (a deque; 1–3
entries typically) plus the bounded ghost of looked-up-but-not-resident blocks that the RQ1 policies already keep; expiry is lazy
(stamps older than W are dropped when the block is examined). They differ from LRU when a block accessed twice inside W is kept
over a more recently admitted single-access block (retention), and from admit-all when a first-touch block is not stored (admission).
Baselines (identical traces, capacities, scoring = usable-prefix hit share of the second half): LRU, SLRU, second touch (unbounded
ghost), `2nd_int` (gap ≤ residence), the RQ1 adaptive policy (gap rule + `res_ft` regime switch on SLRU, dead-eviction residence
estimator), ORACLE (Belady with bypass). Capacities 30 / 60 / 120 / 180 / 360 / 720 GiB of 8B blocks (67.1 MB).

**C3 / D — results (`infer/tables.md`, fig-infer-window, fig-infer-capacity):**

| usable-prefix hit share | conv 30 | conv 60 (DRAM-only) | conv 120 | conv 180 (DRAM + CXL) | conv 360 | conv 720 | tool 30 | tool 60 | tool 120 | tool 180 | tool 360 | tool 720 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LRU | 0.114 | 0.117 | 0.137 | 0.160 | 0.318 | 0.580 | 0.613 | 0.617 | 0.627 | 0.638 | 0.721 | 0.840 |
| SLRU | 0.116 | 0.121 | 0.154 | 0.190 | 0.309 | 0.620 | 0.615 | 0.618 | 0.634 | 0.653 | 0.711 | 0.858 |
| second touch (unbounded ghost) | 0.122 | 0.138 | 0.213 | 0.299 | 0.465 | – | 0.619 | 0.628 | 0.672 | 0.715 | 0.793 | – |
| `2nd_int` (gap ≤ residence) | 0.157 | 0.196 | 0.289 | 0.354 | 0.484 | – | 0.635 | 0.653 | 0.695 | 0.728 | 0.789 | – |
| RQ1 adaptive (gap rule + regime switch, SLRU) | 0.164 | 0.210 | 0.294 | 0.365 | 0.479 | 0.620 | 0.637 | 0.660 | 0.702 | 0.733 | 0.790 | 0.858 |
| best window-protected LRU `wslru:W` (W) | 0.114 (10) | 0.126 (200) | 0.155 (300) | 0.197 (300) | 0.335 (300) | 0.546 (100) | 0.615 (200) | 0.621 (200) | 0.636 (300) | 0.656 (300) | 0.727 (200) | 0.824 (100) |
| best window-LFU `wlfu:W` (W) | 0.114 (10) | 0.125 (300) | 0.143 (300) | 0.167 (200) | 0.322 (200) | – | 0.615 (200) | 0.620 (300) | 0.629 (100) | 0.641 (200) | 0.723 (300) | – |
| best window admission + protection `wslru2nd:W` (W) | 0.160 (50) | 0.193 (50) | 0.276 (200) | 0.353 (300) | 0.461 (300) | 0.331 (100) | 0.636 (30) | 0.652 (50) | 0.692 (200) | 0.728 (300) | 0.779 (300) | 0.717 (100) |
| ORACLE | 0.336 | 0.476 | 0.645 | 0.754 | 0.931 | 1.000 | 0.719 | 0.786 | 0.868 | 0.920 | 0.996 | 1.000 |
| LRU residence p50 (s) | 6 | 12 | 24 | 36 | 72 | 156 | 6 | 12 | 24 | 36 | 75 | 159 |
| host writes in the scored half, TB: LRU / RQ1 adaptive / best window admission | 18.5 / 0.9 / 0.6 | 18.5 / 1.4 / 0.6 | 18.3 / 1.9 / 2.8 | 18.2 / 2.1 / 3.1 | 16.9 / 2.8 / 2.5 | 15.1 / 14.5 / 1.5 | 18.2 / 0.9 / 0.3 | 18.1 / 1.4 / 0.6 | 18.0 / 1.9 / 2.8 | 17.8 / 2.1 / 3.1 | 16.5 / 2.9 / 2.5 | 14.7 / 14.2 / 1.5 |

1. **A historical window used for RETENTION does not improve LRU.** `wslru:W` and `wlfu:W` with admit-all stay within −0.03 … +0.04
   of LRU / SLRU at every capacity on both traces (the best of 6 windows each). This repeats the RQ1 finding (historical retention
   ranking ≈ LRU): once a block is in the cache, recency already orders it as well as a window count does.
2. **A historical window used for ADMISSION helps a lot — and it is the RQ1 rule in a fixed-parameter form.** `wslru2nd:W` gains
   +0.05 … +0.19 over LRU (conversation) and +0.02 … +0.09 (tool agent) while writing 6–30× less (0.3–3.1 TB vs 18 TB), but it stays
   0.001–0.018 BELOW the RQ1 adaptive policy at every capacity, and its best window grows with the capacity: W* = 50 s at 30–60 GiB,
   200 s at 120 GiB, 300 s at 180–360 GiB — 4–8× LRU's residence time (6–72 s), because the right admission window is the residence
   of the FILTERED cache (108–456 s here), which the gap rule measures online instead of guessing. At 720 GiB every fixed window
   loses to admit-all (0.33 vs 0.58–0.62): the capacity now covers the reuse horizon and filtering only throws hits away — the RQ1
   regime switch handles that case (0.620 = SLRU), a fixed window does not. Short windows (10 s) catch only the burst class (0.121
   at every capacity on the conversation trace).
3. **Capacity:** from the DRAM-only 60 GiB to the DRAM + CXL 180 GiB, LRU gains +0.043 / +0.022 (conversation / tool agent), the RQ1
   adaptive policy +0.155 / +0.073 and the oracle +0.278 / +0.133; the extra capacity is worth 3.5× more with reuse-aware admission
   than with LRU, because LRU fills the extra 120 GiB with the same 70% of dead blocks (residence 12 → 36 s, hits barely move),
   while admission lets the residence grow from 93 s to 186 s and keep the 40–55% of re-seen blocks that return within that time.
   "How long a reuse can be retained" is the residence: LRU 0.2 s per GiB (6 s at 30 GiB … 156 s at 720 GiB); filtered 3 s per GiB.
   An equal-total-capacity control (180 GiB of DRAM vs 60 + 120) gives identical hits in this simulator by construction (reads are
   tier-independent, measured 2026-10-07); the tiers differ only in where the writes land (the Phase 3 and hardware-validation files).
4. **Future-horizon evaluation (C4, `infer/horizon/`; plain hit rate over all scored accesses):** the ranking of the policies is the
   same over the first 60 / 300 / 900 / 1,800 s after the scoring boundary as over the whole half (e.g. 180 GiB conversation: RQ1
   adaptive 0.131 / 0.138 / 0.143 / 0.143 vs LRU 0.048 / 0.061 / 0.066 / 0.062); the window-admission policy's early advantage with a
   long window (`wslru2nd:300`: 0.090 in the first 60 s at 60 GiB vs 0.070 overall) is the warm-up's residue, not a durable effect.
   No online decision used future information; the horizons only slice the evaluation.

## Task E — the metrics asked for (inference; the training ones are in Task B)
Per policy and capacity the campaign CSVs carry: accesses, reuse accesses, hits, usable hits, misses (new / after eviction / after
bypass), recomputed tokens, usable tokens, TTFT model, written blocks and TB, bypassed blocks, evictions, residence p50 of all and
of never-hit blocks, the online residence estimate, hits by fifth, the ghost's size; `infer/tables.md` prints them.

## Task F — why the curves look as they do
**Training.** A larger future window improves the hit rate only while the prefetch queue is the bottleneck: with storage faster than
the trainer the queue is empty after one file's fetch time, so the curve saturates at W ≈ 0.1–0.25 s; with storage at the edge of the
needed rate the window lets the prefetcher run ahead during the slightly slower steps (the demand is 205 MB/s mean, 233 max, the
steps 53 ms p50 / 70 ms p99), which takes tens of seconds of queue and saturates at 50–100 s; below the needed rate nothing
saturates because every byte must still cross the same link. Saturation is bandwidth-limited first and capacity-limited second:
the capacity bounds how much future data can be pinned (297 s at 60 GiB, 149 s at 30 GiB — which is why the 30 GiB plateau at
B = 0.20 is 0.78), and it sets the retention floor that lowers the needed bandwidth. Early prefetch evicts useful data only in a
prefetcher that does not know its own window (−5.7 points); a window-aware one never loses hits to a longer window.
**Inference.** A historical window is useful only where it changes a decision that recency does not already make. Retention: a
block with two accesses inside W is already recent, so protecting it changes little (+0.00 … +0.04); the count predicts reuse (41 →
54 → 83% for 1 → 2 → ≥ 3 past accesses) but recency predicts it almost as well (44–53% for a 10–300 s gap), and 42% / 16% of the
future reuses sit on blocks with NO access in the past 300 s, which no window sees. Admission: the window decides whether a block
is stored at all, and that is where the hits and the writes are — but the right window is the cache's own residence time, which
grows with capacity (W* 50 → 300 s from 30 to 360 GiB) and is what the RQ1 gap rule measures online; a fixed window writes more
without more hits when it exceeds the residence (W = 300 s at 60 GiB: 3.09 TB for 0.180 vs 0.55 TB for 0.193 at W = 50 s) and loses
everything when the capacity covers the reuse horizon (720 GiB). Window and capacity are therefore tied through the residence,
not through a fixed function. **Can a policy or window be selected from the future-reuse / observation-window / capacity
relationship?** Training: yes, from the bandwidth margin (W ≈ fetch time; tens of seconds if marginal) — not from capacity. Inference:
yes, but as the residence the cache measures online (the RQ1 rule), not as a constant; the fixed-window family is dominated by it.

## Task G — training vs inference
| property | training (CosmoFlow, REAL trace) | inference (Mooncake KV, SIM) |
|---|---|---|
| future information | the whole epoch's order at epoch start (all epochs from the seed); 10 ms and 0.5 MB to materialize | none online; the future is used only to score |
| reuse structure | every sample once per epoch; reuse distance = one epoch (820 s, 166 GiB); no popularity | 70% / 47% of accesses never seen in the past 300 s; bursts (0–10 s, 4.5% / 35%) and a 10–300 s band at 44–53% reuse |
| what a window buys | hides the fetch latency: 0.1–0.25 s with adequate storage, 50–100 s when marginal, nothing when starved | admission: +0.05 … +0.19 over LRU at 6–30× fewer writes; retention: nothing |
| how the best window scales with capacity | it does not (comfortable) or shrinks (marginal: retention lowers the needed bandwidth) | it grows with the residence: 50 s at 30–60 GiB → 300 s at 180–360 GiB; no window at 720 GiB |
| capacity's value | retention H0(c) = c + (1 − c) ln(1 − c): 7.5% at 60 GiB, 100% at 180 GiB; with prefetch, storage traffic and independence from storage speed | 60 → 180 GiB: LRU +0.04 / +0.02, reuse-aware admission +0.155 / +0.073, oracle +0.28 / +0.13 |
| a common law? | H = H0(C) + (1 − H0)(1 − e^(−W/τ)), τ from the bandwidth margin | hits rise with the admission window up to the residence, then fall; the residence is the window |
There is one shared principle — the useful window is the time the cache needs to hold or fetch the data before its use — but its
value comes from different places (a link bandwidth vs an eviction age), so no single window function covers both; the brief's
option of leaving them separate is the honest one.

## D7 — answers
1. **Future reuse information available in training:** the full epoch order at epoch start in both PyTorch (randperm at
   `__iter__`) and tf.data (inside the shuffle op, exportable with a seeded permutation), all epochs from the seed with
   `DistributedSampler`; 10 ms and 0.5 MB per epoch at 61k samples, 0.3 s and 108 MB at ImageNet-22k scale; dynamic sampling
   shortens it to what the sampler commits to.
2. **Prefetch value vs future window:** saturates at W ≈ 0.1–0.25 s (one file) when the storage out-paces the trainer by ≥ 15%,
   at 50–100 s when the margin is ±10%, never when the storage is slower; more knowledge beyond that is free but useless.
3. **Does a historical window improve LRU for inference?** As a retention rule, no (±0.04); as an admission rule, yes (+0.05 …
   +0.19), but it is a fixed-parameter version of the RQ1 gap rule and 0.001–0.018 below it at every capacity.
4. **Window vs capacity:** training — independent (the window is a bandwidth quantity; capacity sets the retention floor);
   inference — the useful admission window equals the filtered cache's residence, ≈ 3 s per GiB here, so it grows with capacity
   and vanishes once the capacity covers the reuse horizon.
5. **Real benefit of the CXL capacity:** training — 100% retention of a 166 GiB dataset vs 7.5%, i.e. no storage traffic and no
   dependence on storage speed (hits themselves are reachable by prefetch from 60 GiB when the storage is fast); inference —
   +0.04 (LRU) to +0.155 / +0.073 (reuse-aware admission) usable hit share, the gain being 3.5× larger with admission.
6. **Consistent with RQ1?** Yes: historical retention ranking ≈ LRU, admission is where the value is, first-touch reuse is
   unpredictable, and the admission window must track the residence — all reproduced with a different policy family.
7. **Potentially useful for the unified DRAM/CXL line:** the retention formula H0(c) and the "capacity = independence from
   storage" argument for training-data caches on CXL; the fact that a 0.25-s lookahead suffices (a training-data tier needs
   bandwidth and capacity, not clairvoyance); the inference result that the admission window is the residence (already in RQ1).
8. **Not worth more investment:** window-based retention for KV blocks (three families, six windows, six capacities: nothing);
   fixed admission windows (dominated by the adaptive rule); longer future windows for training; a unified window function.

## Change history
- 2026-10-27: opened and closed on the exploratory branch; the first two passes of the training sweeps were discarded after two
  simulator corrections recorded in `train/sim/run_sweep.sh` (window protection as a count; scored-epoch traffic accounting).

