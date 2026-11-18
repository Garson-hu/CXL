#!/usr/bin/env python3
"""Build the exploratory-study deck of 2026-10-27 (reuse windows, future-aware prefetching and cache capacity in training and inference)
for the group meeting: an editable PowerPoint (python-pptx, 16:9, white background, Calibri) plus a preview PDF/PNGs drawn by matplotlib
from the same slide data (layout check only — there is no PowerPoint or LibreOffice on c28; DejaVu Sans is wider than Calibri, so what
fits in the preview fits in PowerPoint), outline.md and README.md. Slide text follows Simplified Technical English: short sentences, one
idea each, active voice. Every number on the slides comes from docs/experiments/2026-10-27-reuse-window-prefetch.md and the figure data
tables in experimental_results/2026-10-27-reuse-window-prefetch/figs/; the figures are drawn by scripts/figs_deck_2026-10-27.py.
usage: scripts/deck_2026-10-27.py   (run after scripts/figs_deck_2026-10-27.py; writes docs/slides/SLIDES_2026-10-27-reuse-window-prefetch.pptx,
       docs/slides/2026-10-27-reuse-window-prefetch/{deck-preview.pdf,preview/slide-NN.png,outline.md,README.md})"""
import os, textwrap
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HERE = os.path.join(ROOT, "docs", "slides", "2026-10-27-reuse-window-prefetch"); FIG = os.path.join(HERE, "figs"); OUTP = os.path.join(HERE, "preview"); os.makedirs(OUTP, exist_ok=True)
DECK = os.path.join(ROOT, "docs", "slides", "SLIDES_2026-10-27-reuse-window-prefetch.pptx")
W, H = 13.333, 7.5
INK, MUTED, NAVY, TINT, LINE = "1F2D3D", "6B6B6B", "1B2A41", "F3F6FA", "D9DEE5"
FONT = "Calibri"
TAGS = {"Oracle": "FBE3E3", "Trace-driven simulation": "FDEBD9", "Trace analysis": "FDEBD9", "Real-system measurement": "E3F1E1", "Framing": "EEEEEE"}
TAG_ORDER = ["Real-system measurement", "Trace-driven simulation", "Trace analysis", "Oracle", "Framing"]
TABLE_W = [2.0, 3.0, 3.4, 3.93]

# ------------------------------------------------------------------ slide data
def S(title, why, tags, fig, points, source, notes): return dict(kind="fig", title=title, why=why, tags=tags, fig=fig, points=points, source=source, notes=notes)
SLIDES = [
dict(kind="title", title="Reuse windows, future-aware prefetching and cache capacity in training and inference",
     subtitle="An exploratory study: how much of the future (training) or of the past (inference) a DRAM/CXL cache needs, and what the extra capacity buys",
     meta="Group meeting  ·  2026-10-27  ·  branch explore/reuse-window-prefetch (exploratory; the main line and its results are unchanged)  ·  evidence: a real CosmoFlow run on the A100 node c33, "
          "measured BeeGFS bandwidth, trace-driven cache simulation on the real demand, Mooncake KV-cache trace replay, oracles as upper bounds",
     notes="This deck reports an exploratory study that followed the meeting with Dr. Mueller. It asks how much knowledge of the future (in training) or of the past (in inference) a "
           "DRAM/CXL cache needs, and what the extra CXL capacity buys. It is a side branch: the research direction, the three RQs, the charter, the gates and the Phase 3 "
           "negative result are unchanged. Each slide carries evidence tags: Real-system measurement (the CosmoFlow run on c33, the BeeGFS bandwidth, the sampler measurements), "
           "Trace-driven simulation (the prefetch simulator on the real demand timeline; the KV-cache replay of the Mooncake traces), Trace analysis (offline statistics), "
           "Oracle (uses the future; an upper bound, not a method). Every number comes from the experiment report and its figure data tables; the figures are drawn from "
           "them by scripts/figs_deck_2026-10-27.py."),

S("Two caches, two kinds of knowledge: a training loader knows the future, a KV cache only knows the past",
  "Why this study: Dr. Mueller asked whether a cache can use a window of future accesses (training) or of past accesses (inference), and how the useful window depends on the capacity.",
  ["Framing"], "f01_overview",
  [("Training question", "A data loader draws the whole epoch order at the start of the epoch. How much of this future does a prefetcher need to fill a cache of C bytes? Does the useful window W depend on C?"),
   ("Inference question", "The KV cache of a serving engine sees only past lookups. Does a window of past accesses improve LRU, for eviction or for admission? How does the useful window relate to C?"),
   ("Capacity question", "What does a 60 GiB DRAM-only cache lose against 60 GiB DRAM + 120 GiB CXL, in both workloads? This is the CXL question behind the study.")],
  "docs/experiments/2026-10-27-reuse-window-prefetch.md (scope)  ·  prior results used as baselines: RQ1 consolidation (2026-10-21), Phase 3 joint-benefit analysis (2026-10-21)",
  "Why the two settings belong together: both are caches in front of an accelerator, both can sit in DRAM plus CXL, and both have a window of reuse information — but of opposite "
  "kinds. A training loader draws the whole epoch order at the start of the epoch (PyTorch RandomSampler: randperm when the iterator is created; tf.data: inside the shuffle op), "
  "and with a seeded sampler every future epoch is computable. So the prefetcher can know the future. A KV cache only sees the lookups that already happened. The three "
  "questions: (1) training: how much of the known future does a prefetcher need, as a function of the window W and the capacity C; (2) inference: does a window of past "
  "accesses improve LRU, for eviction or for admission, and how does the useful window relate to C; (3) both: what does 60 GiB of DRAM lose against 60 + 120 GiB with CXL. "
  "Context from the main line: RQ1 found that for the KV cache the value of reuse information lies in admission (which blocks to store), and that the adaptive gap rule "
  "(second touch with re-lookup gap below the online residence estimate, with a regime switch) is the best online policy we have. That policy is the baseline of slide 7. "
  "Literature for the training side: NoPFS (Dryden et al., SC'21) prefetches with full knowledge of the seeded schedule; Quiver (FAST'20), SHADE (FAST'23), HVAC "
  "(CLUSTER'22) and FitCache (IPDPS'26, this group) are training-data caches; none of them measures hit rate as a function of the future window."),

S("We recorded a real CosmoFlow run and replayed its demand in a cache simulator behind a storage link",
  "Why this setup: no training access trace with timestamps existed, and the useful window must depend on how fast the storage delivers files against the trainer's demand.",
  ["Real-system measurement", "Trace-driven simulation"], "f02_setup",
  [("Real measurements", "CosmoFlow (TensorFlow) on the A100 node c33: 61,440 files = 178 GB, 3 epochs, explicit seeded order, 74.9 samples/s = 0.217 GB/s in epochs 1–2. BeeGFS cold reads: 0.064 GB/s at 1 stream, 0.52 at 8 streams, 0.82 at 32."),
   ("Simulation", "The real demand timeline drives a cache of C bytes behind one storage link of B bytes/s. The prefetcher fetches samples due within the next W seconds. Resident data due inside W is protected. Used data stays (LRU). Epochs 1–2 are scored."),
   ("Metric", "Hit rate = share of the 122,880 sample demands of epochs 1–2 served from the cache: retained since the previous epoch, or prefetched and complete before its step. A prefetch still in flight is a miss.")],
  "train/run-61440 (trace, Slurm job 322135), train/beegfs-bw-c33.txt, train/sim/*.csv (scripts/train_prefetch_sim.py) under experimental_results/2026-10-27-reuse-window-prefetch/",
  "How. The group's CosmoFlow benchmark (TensorFlow, MLPerf HPC data) runs on the 61,440-file mini set on BeeGFS; one sample is one 2.9 MB TFRecord file, so the sample "
  "schedule is the file-read order. We replaced the benchmark's internal shuffle with an explicit seeded permutation per epoch (10 ms and 0.5 MB per epoch; all three epochs "
  "known 8 s after job start) and logged every file pull and every training step. The run: batch 4, 8 files read concurrently, 4 parallel parses, 3 epochs, 2,618 s; 63.5 "
  "samples/s in epoch 0 (cold BeeGFS reads) and 74.9 in epochs 1–2 (partly served by the node's 125 GB page cache), which is the compute-bound demand of 0.217 GB/s shown in "
  "panel (b). Panel (a): measured cold-read bandwidth from c33 against the number of concurrent streams; the run's reader used 8 streams, so 0.52 GB/s is its operating point; "
  "one stream (0.064 GB/s) is 3.4 times too slow for this trainer. The benchmark as shipped reads one stream and is I/O-bound at 5.4 samples/s (pilot). The simulator: one "
  "FIFO storage channel of B bytes/s (demand fetches ahead of queued prefetches, no preemption); a cache of C bytes; the prefetcher may fetch any sample due within the next W "
  "seconds (we also ran the variant where only the current epoch's order is known: identical results); prefetched data is pinned until its use; resident data due inside the "
  "window is protected from eviction; a demand whose prefetch is still in flight is a miss (the stall is recorded); misses are fetched on demand; used data stays (LRU). "
  "Epoch 0 is the cold start; epochs 1–2 are scored. The simulator was corrected twice during the sweeps (protection as a count of pending demands; traffic counted for the "
  "scored epochs only); the third pass is the data of every figure. Limit: the simulation does not slow the trainer, so when storage is slower than the demand the hit rate "
  "is right but the run time is not modelled."),

S("Storage speed, not window length, decides the hit rate: 0.1 s of future is enough when storage out-paces the trainer",
  "Why we tested it: clairvoyant prefetching (NoPFS) assumes the whole future schedule is valuable. We measured how much lead time a prefetcher really needs at each bandwidth.",
  ["Trace-driven simulation", "Real-system measurement"], "f03_window",
  [("Storage faster than the trainer (B ≥ 1.15×)", "BeeGFS at 4 or more streams: hits reach ≥ 0.999 at W = 0.1 s, the fetch time of one file, at every capacity from 15 GiB. Longer windows add nothing."),
   ("Storage near the limit (B = 0.92×)", "0.20 GB/s: the curve rises over tens of seconds. 120 GiB saturates at W = 25 s, 60 GiB at 100 s. 30 GiB stops at 0.78 because the cache cannot hold the queue."),
   ("Storage slower than the trainer (B ≤ 0.7×)", "One BeeGFS stream: 0.075 at every window. Every prefetch arrives late. A window cannot replace bandwidth.")],
  "figs/fig1-train-window-by-capacity.csv, figs/fig2-train-window-by-bandwidth.csv (train/sim/*.csv, third pass + the 16:40 grid)",
  "Result. Panel (a) fixes the capacity at 60 GiB (the DRAM-only cache) and varies the storage bandwidth: 0.064 GB/s (one BeeGFS stream), 0.20 (a simulated value at 0.92 "
  "of the trainer's demand), 0.33 / 0.52 / 0.82 (BeeGFS at 4 / 8 / 32 streams). The three measured bandwidths above the demand coincide: the hit rate jumps from the "
  "retention-only value 0.075 at W = 0 to 0.999 at W = 0.1 s and 1.000 from 0.5 s, and stays there up to 1,200 s. At 0.20 GB/s the curve rises slowly (0.17 at 0.1 s, 0.25 at "
  "5 s, 0.60 at 25 s, 0.98 at 50 s, 1.00 at 100 s). At 0.064 GB/s nothing changes: all 113,641 prefetches arrive late. Panel (b) fixes the bandwidth at 0.20 GB/s and varies "
  "the capacity: 120 GiB saturates at 25 s, 60 GiB at 100 s, 30 GiB reaches a plateau of 0.78 (27,116 prefetches stay late at every window because 30 GiB holds only 149 s "
  "of future data); 180 GiB is 1.0 at every window because the dataset fits. Explanation. A future window hides the fetch latency. When the storage link is faster than the "
  "demand, the queue is empty after one file's fetch time, so the window saturates at 0.1 s. When the link is at the edge of the needed rate, the window lets the prefetcher "
  "run ahead during the slower steps (the demand is 205 MB/s mean, 233 MB/s max), which takes tens of seconds of queue. When the link is slower than the demand, every byte "
  "still has to cross the same link, so no window helps. Two side results: a naive prefetcher that does not protect resident data due inside its window loses up to 5.7 "
  "points at long windows (it evicts samples it will need and refetches them late) — that is the cache-pollution effect of early prefetch, an implementation property, not a "
  "window property; and knowing all epochs from the seed gives the same numbers as knowing only the current epoch. What we learned: a training-data tier needs bandwidth and "
  "capacity, not clairvoyance; the standard tf.data pipeline already pulls 0.4–0.85 s ahead, which is enough when the storage keeps up."),

S("Capacity decides retention and storage traffic: a 60 GiB cache re-reads 92% of the data each epoch, 180 GiB none",
  "Why we tested it: with fast storage a prefetcher already reaches 100% hits from a 60 GiB DRAM cache. We asked what the extra 120 GiB of CXL still buys.",
  ["Trace-driven simulation"], "f04_capacity",
  [("Retention without prefetch", "LRU under per-epoch reshuffling keeps 1.8% / 7.5% / 37% / 68% of the data at 30 / 60 / 120 / 150 GiB and 100% from 180 GiB. Half the data in cache retains 19%, not 50%."),
   ("Storage traffic", "Bytes read from storage in epochs 1–2: 329 GB at 60 GiB (165 GB per epoch, 92% of all reads), 0 GB at 180 GiB. Equal at every window and bandwidth: a window moves reads earlier, it does not remove them."),
   ("What CXL buys for training", "Not more hits: prefetch already gives 100% from 60 GiB when storage is fast. It removes the storage traffic and the dependence on storage speed: at one BeeGFS stream 60 GiB gives 7.5%, 180 GiB gives 100%.")],
  "figs/fig3-train-capacity-by-window.csv, figs/fig4-train-storage-traffic.csv (train/sim/grid-bw0.52.csv, grid-bw0.2.csv, none.csv)",
  "Result. Panel (a): the grey curve is the hit rate without prefetch, i.e. what LRU retains from one epoch to the next when every epoch is reshuffled: 0.004 / 0.018 / "
  "0.040 / 0.075 / 0.186 / 0.368 / 0.679 at 15 / 30 / 45 / 60 / 90 / 120 / 150 GiB and 1.000 from 180 GiB (the dataset is 166 GiB). The curve is convex: half the dataset's "
  "capacity retains 19%, not 50%; the cloud-storage rule of thumb 'hit rate = cached fraction' over-estimates it 2–5 times. (It matches the closed form c + (1 − c) ln(1 − c) "
  "to ±0.002, c = C / dataset; we derived it but the figure does not need it.) With prefetch at 0.52 GB/s every window of 0.25 s or more lifts every capacity to 1.0 "
  "(green); at 0.20 GB/s a 50 s window gives 0.42 at 30 GiB, 0.98 at 60 GiB and 1.0 from 90 GiB (orange). Panel (b): the bytes read from storage in epochs 1–2 (356 GB of "
  "reads in total): 355 / 350 / 342 / 329 / 290 / 225 / 114 GB at 15 … 150 GiB and 0 from 180 GiB — the same with and without prefetch, at both bandwidths and at every "
  "window (0 wasted prefetches in every run). Explanation. The window changes when a byte is fetched, not how many bytes are fetched; only capacity changes the volume, "
  "through retention. So the CXL capacity does not add hits here — the 60 GiB cache already reaches 100% by prefetching when the storage is fast enough — but it removes "
  "the storage traffic (165 GB per epoch) and the dependence on storage speed: at one BeeGFS stream the 60 GiB cache gives 7.5% and the 180 GiB cache 100%. With only one "
  "reuse distance in training (one epoch, 820 s here), there is no intermediate horizon to tune: a cache either retains a sample for the next epoch or it does not."),

S("KV cache: a window of past accesses used for eviction does not beat LRU (−0.03 … +0.04 at every capacity)",
  "Why we tested it: a block accessed twice in the last W seconds may deserve more protection than LRU gives it for being recent. We built two eviction policies on this count.",
  ["Trace-driven simulation", "Trace analysis"], "f05_retention",
  [("Setup", "Mooncake conversation and tool-agent traces replayed in a host cache of 8B blocks (67.1 MB), 30–720 GiB; the first half warms, the second half is scored. Usable-prefix hit share: a hit counts only while every earlier block of the request also hit."),
   ("Result", "Window-protected LRU: −0.034 … +0.037 against LRU over 6 windows × 6 capacities × 2 traces. Window-LFU eviction: −0.001 … +0.008. At 720 GiB a 100 s protection loses 0.03 / 0.02."),
   ("Why it fails", "The count predicts reuse (41 / 54 / 83% for 1 / 2 / ≥ 3 past accesses) but recency alone predicts 44–53%, so protection changes few decisions. And 42% / 16% of the reuses sit on blocks with no access in the past 300 s, which no window sees.")],
  "figs/fig5-infer-window-retention-vs-lru.csv (infer/*-replay.csv)  ·  infer/stats/window-stats-{conversation,toolagent}.csv (offline statistics)",
  "How. Two eviction policies added to the RQ1 admission simulator, both admitting every block like LRU: window-protected LRU (wslru:W) keeps a protected segment for blocks "
  "with at least two accesses inside the last W seconds, the protection expiring after W seconds without an access, eviction from the unprotected part first; window-LFU "
  "(wlfu:W) evicts, among the K least recently used blocks (K = 64 or capacity/16), the one with the fewest accesses in the last W seconds. Windows 10 / 30 / 50 / 100 / 200 "
  "/ 300 s; capacities 30 / 60 / 120 / 180 / 360 / 720 GiB (at 720 GiB only the 100 s window was run); both Mooncake traces; the first half of each trace warms the cache "
  "and the online statistics, the second half is scored with the usable-prefix hit share (a block hit counts only while every earlier block of the same request also hit, "
  "because the engine can use a prefix only up to the first miss). Result: the figure shows the difference to LRU at the same capacity; every point lies between −0.034 and "
  "+0.037; the best window per capacity gains +0.000 / +0.009 / +0.018 / +0.037 / +0.018 on the conversation trace and +0.002 / +0.004 / +0.010 / +0.018 / +0.006 on the tool "
  "agent; window-LFU stays within +0.008. Explanation, from the offline statistics on the traces: the number of accesses in the past 300 s does predict reuse — the "
  "probability of a next access within 300 s is 41 / 54 / 83% for blocks with 1 / 2 / 3 or more past accesses — but recency alone predicts almost as well (44–53% for a last "
  "access 10–300 s ago, 7% beyond 900 s, 99.6% within 10 s), so a block with two accesses inside the window is already recent and protecting it changes few eviction "
  "decisions. And 42% (conversation) / 16% (tool agent) of the future reuses are on blocks with no access in the past 300 s (70% / 47% of all accesses), which no historical "
  "window can see. This repeats the RQ1 finding with a different policy family: historical information does not improve the eviction order; first-touch reuse is not "
  "predictable from history."),

S("A window used for admission helps (+0.05 … +0.19 over LRU) but never beats the RQ1 adaptive rule",
  "Why we tested it: RQ1 found that admission, not eviction, is where the value is. A fixed window is the simplest admission rule: store a block only if it was looked up within the last W seconds.",
  ["Trace-driven simulation", "Oracle"], "f06_admission",
  [("Result", "Best fixed window: +0.05 … +0.19 over LRU at 30–360 GiB (conversation; tool agent +0.02 … +0.09), with 6–30× fewer writes. But 0.004–0.018 below the RQ1 adaptive rule at every capacity."),
   ("Why it falls short", "The right window equals the residence time of the filtered cache, which grows with capacity: best W = 50 s at 30–60 GiB, 300 s at 180–360 GiB. The RQ1 rule measures this residence online; a fixed window guesses it."),
   ("Where it breaks", "At 720 GiB the capacity covers the reuse horizon. Every fixed window loses to admit-all (0.33 vs 0.58–0.62). The adaptive rule switches to first-touch admission and matches SLRU (0.62).")],
  "figs/table-infer-admission.csv, figs/fig6-infer-window-admission-vs-rq1.csv (infer/*-replay.csv)",
  "How. The admission policy wslru2nd:W stores a block only if it was looked up within the last W seconds (the first block of a request is always stored), with the "
  "window protection of the previous slide; it uses the bounded ghost of past lookups that the RQ1 policies already keep. Baselines on the same traces, capacities and "
  "scoring: LRU (admit all), second touch (store on the second lookup), 2nd_int (second touch only if the re-lookup gap is at most the online residence estimate), the RQ1 "
  "adaptive policy (2nd_int with an automatic switch back to first-touch admission when the admit-all residence exceeds the median first-touch re-lookup gap, on an SLRU "
  "structure), and the oracle (Belady with bypass — an upper bound that uses the future; it is not a method). Result (figure: hit share against capacity; the best window "
  "per capacity is annotated): the best fixed window gains +0.046 / +0.076 / +0.139 / +0.193 / +0.144 over LRU at 30 / 60 / 120 / 180 / 360 GiB on the conversation trace "
  "and +0.024 / +0.035 / +0.065 / +0.090 / +0.058 on the tool agent, and writes 0.25–3.1 TB in the scored half instead of 18 TB (6–30 times less); it is at or above second "
  "touch everywhere except 360 GiB. But it stays below the RQ1 adaptive rule at every capacity: −0.004 / −0.018 / −0.018 / −0.013 / −0.018 (conversation) and −0.001 / −0.008 "
  "/ −0.010 / −0.006 / −0.011 (tool agent). Explanation. The right admission window is the residence time of the filtered cache, which grows with capacity: the best W moves "
  "from 50 s at 30–60 GiB to 200 s at 120 GiB and 300 s at 180–360 GiB (4–8 times LRU's own residence of 6–72 s). A shorter window rejects blocks that would have been "
  "reused (W = 10 s is 0.016–0.197 below LRU from 120 GiB up); a longer window admits blocks that are evicted before their reuse and only adds writes (60 GiB: W = 300 s "
  "writes 4.25 TB for 0.180, W = 50 s writes 0.55 TB for 0.193). The RQ1 gap rule measures that residence online instead of guessing it, and its regime switch handles the "
  "case a fixed window cannot: at 720 GiB the capacity covers the reuse horizon, every fixed window loses to admit-all (0.331 against 0.580–0.620 on the conversation trace, "
  "0.717 against 0.840–0.858 on the tool agent), while the adaptive rule switches to first-touch admission and matches SLRU. Capacity: from 60 to 180 GiB, LRU gains "
  "+0.043 / +0.022, the RQ1 adaptive rule +0.155 / +0.073, the oracle +0.278 / +0.133 — the extra capacity is worth 3.5 times more with reuse-aware admission than with LRU, "
  "because LRU fills the extra 120 GiB with the same never-reused blocks. A future-horizon check (hit rates over the first 60 / 300 / 900 / 1,800 s after the scoring "
  "boundary) gives the same ranking; no online decision used future information."),

dict(kind="table", title="What we learned: the useful window is set by bandwidth (training) or residence (inference); capacity pays through retention",
     why="A longer future window or a historical window is not the lever. Capacity and the RQ1 admission rule carry the value. The main line is unchanged.",
     tags=["Real-system measurement", "Trace-driven simulation", "Oracle"],
     header=["Question", "What we tested", "Result", "What we learned"],
     rows=[["Future window (training)", "Prefetch W = 0–1200 s on the real demand; B 0.064–2 GB/s; C 15–360 GiB", "0.1 s suffices at B ≥ 1.15× demand; 25–100 s at 0.92×; nothing when B is lower", "The window hides a fetch latency. It is a bandwidth quantity, not a capacity quantity."],
           ["Capacity (training)", "LRU retention and storage reads vs capacity, with and without prefetch", "7.5% retained at 60 GiB, 100% at 180 GiB; storage reads 329 GB → 0 per two epochs", "CXL capacity buys independence from storage speed, not more hits than prefetch already gives."],
           ["Past window for eviction (inference)", "Window-protected LRU and window-LFU; 6 windows × 6 capacities × 2 traces", "−0.03 … +0.04 against LRU", "Did not work. Recency already orders resident blocks as well as a window count does."],
           ["Past window for admission (inference)", "Admit a block only if it was looked up within W s", "+0.05 … +0.19 over LRU; 0.001–0.018 below the RQ1 adaptive rule; fails at 720 GiB", "Works, but it is the RQ1 rule with a guessed parameter. The residence must be measured online."],
           ["Capacity (inference)", "60 GiB DRAM-only vs 60 + 120 GiB CXL, same policies", "LRU +0.04 / +0.02; RQ1 adaptive +0.155 / +0.073; oracle +0.28 / +0.13", "The extra capacity is worth 3.5× more with reuse-aware admission than with LRU."],
           ["A common window law?", "Compare the two window–hit relations", "Training: rise then plateau, set by B; inference: rise to the residence then fall", "No common law. Shared principle: the window is the time to fetch or hold data before its use."]],
     closing="Open: one training workload (CosmoFlow), and a simulation that does not slow the trainer when storage is too slow; a run with the cache in the loop would show the run-time effect. "
             "May come back to the main line: the retention curve and the 'capacity = independence from storage' argument for a training-data tier on CXL. "
             "Not worth more work: window-based eviction for KV blocks, fixed admission windows, longer training windows.",
     source="docs/experiments/2026-10-27-reuse-window-prefetch.md  ·  refs: NoPFS (Dryden et al., SC'21), Quiver (Kumar & Sivathanu, FAST'20), SHADE (Khan et al., FAST'23), HVAC (CLUSTER'22), FitCache (IPDPS'26), SOLAR (SC'22), Mooncake traces (Qin et al., FAST'25)",
     notes="Summary. What worked: a short future window (0.1 s) with adequate storage bandwidth; capacity as retention (and as independence from storage speed) for "
           "training; for inference, admission filtering — but the existing RQ1 adaptive rule, not a fixed window. What did not work: a window of past accesses used for "
           "eviction (two families, six windows, six capacities, two traces: nothing beyond LRU); a fixed admission window (always below the adaptive rule, and harmful at 720 "
           "GiB); longer future windows for training (free but useless beyond the saturation point); a single window law for both workloads. The original expectation of "
           "the meeting — that a longer future window or a historical window is the lever — is not supported by the data. What remains open: the training side rests on one "
           "workload (CosmoFlow; DeepCAM and dinov2 have no data on this cluster) and on a simulation that cannot slow the trainer, so the run-time effect in the starved "
           "regime is not measured; a run with the cache in the loop would close that. The inference side is trace replay in a single-tier cache; the tiers differ only in "
           "where the writes land, which the Phase 3 and hardware-validation reports cover. What the evidence suggests next, if anything is brought back to the main line: "
           "(1) a training-data tier on CXL needs bandwidth and capacity, not clairvoyance — the retention curve and the storage-independence argument are the usable "
           "pieces; (2) for the KV cache the RQ1 adaptive admission stays the reference, and a window parameter does not replace its online residence estimate. Nothing here "
           "changes the main line: the Phase 3 negative result on the joint value-cost policy and the RQ gate status stand. References: NoPFS — Dryden et al., 'Clairvoyant "
           "prefetching for distributed machine learning I/O', SC'21; Quiver — Kumar and Sivathanu, FAST'20; SHADE — Khan et al., FAST'23; HVAC — ORNL, CLUSTER'22; FitCache — "
           "this group, IPDPS'26; SOLAR — SC'22; Mooncake traces — Qin et al., FAST'25. Internal: docs/experiments/2026-10-27-reuse-window-prefetch.md (this study), the RQ1 "
           "consolidation and the Phase 3 reports of 2026-10-21."),
]

# ------------------------------------------------------------------ layout helpers
def fig_size(name, maxw, maxh):
    im = Image.open(os.path.join(FIG, name + ".png")); r = im.width / im.height; w = maxw; h = w / r
    if h > maxh: h = maxh; w = h * r
    return w, h
def tsize(t): return 24 if len(t) < 80 else 22 if len(t) < 100 else 20
def layout(sl):
    L = dict(title=(0.5, 0.22, 12.33, 0.98), why=(0.5, 1.18, why_w(sl["tags"]), 0.52), source=(0.5, 7.0, 11.4, 0.4))
    fw, fh = fig_size(sl["fig"], 12.33, 3.6); L["fig"] = (0.5 + (12.33 - fw) / 2, 1.72, fw, fh)
    n = len(sl["points"]); gap = 0.22; bw = (12.33 - gap * (n - 1)) / n; y0 = 1.72 + fh + 0.18; bh = 6.9 - y0
    L["points"] = [(0.5 + i * (bw + gap), y0, bw, bh) for i in range(n)]; L["psize"] = 12 if bh >= 1.3 else 11.5
    return L

# ------------------------------------------------------------------ PPTX
def rgb(h): return RGBColor.from_string(h)
def add_text(slide, x, y, w, h, text, size, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False, runs=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.04); tf.margin_top = tf.margin_bottom = Inches(0.03); tf.vertical_anchor = anchor
    p = tf.paragraphs[0]; p.alignment = align
    for txt, b in (runs or [(text, bold)]):
        r = p.add_run(); r.text = txt; r.font.size = Pt(size); r.font.bold = b; r.font.italic = italic; r.font.name = FONT; r.font.color.rgb = rgb(color)
    return tb
def add_box(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h)); s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    if line: s.line.color.rgb = rgb(line); s.line.width = Pt(0.75)
    else: s.line.fill.background()
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: s.adjustments[0] = 0.08
    return s
def chip_w(t): return 0.16 + 0.072 * len(t)
def why_w(tags): return 12.33 - sum(chip_w(t) + 0.1 for t in tags) - 0.3
def add_chips(slide, tags, right=12.83, y=1.22):
    x = right
    for t in reversed(tags):
        w = chip_w(t); x -= w + 0.1
        add_box(slide, x, y, w, 0.3, TAGS.get(t, "F3F3F3"))
        add_text(slide, x, y, w, 0.3, t, 9.5, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
def add_table(slide, x, y, w, h, header, rows, size=10.5):
    shp = slide.shapes.add_table(len(rows) + 1, len(header), Inches(x), Inches(y), Inches(w), Inches(h)); tbl = shp.table
    tblPr = tbl._tbl.tblPr; tblPr.set("bandRow", "0"); tblPr.set("firstRow", "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None: sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"       # "No Style, Table Grid": thin grid, no theme banding
    for j, cw in enumerate(TABLE_W): tbl.columns[j].width = Inches(cw)
    for i, row in enumerate([header] + rows):
        for j, txt in enumerate(row):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.06); c.margin_top = c.margin_bottom = Inches(0.03); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid(); c.fill.fore_color.rgb = rgb(NAVY if i == 0 else ("FFFFFF" if i % 2 else TINT))
            tf = c.text_frame; tf.word_wrap = True; p = tf.paragraphs[0]; r = p.add_run(); r.text = txt
            r.font.size = Pt(size); r.font.name = FONT; r.font.bold = (i == 0 or j == 0); r.font.color.rgb = rgb("FFFFFF" if i == 0 else INK)
    return shp
def build_pptx(path):
    prs = Presentation(); prs.slide_width = Inches(W); prs.slide_height = Inches(H); blank = prs.slide_layouts[6]
    for n, sl in enumerate(SLIDES, 1):
        s = prs.slides.add_slide(blank)
        if sl["kind"] == "title":
            add_text(s, 0.9, 1.9, 11.5, 1.7, sl["title"], 30, bold=True, color=NAVY, anchor=MSO_ANCHOR.BOTTOM)
            add_text(s, 0.9, 3.7, 11.5, 0.9, sl["subtitle"], 18, color=INK)
            add_text(s, 0.9, 4.75, 11.5, 0.9, sl["meta"], 12, color=MUTED)
            xx = 0.9; add_text(s, xx, 6.3, 2.2, 0.3, "Evidence tags on each slide:", 10, color=MUTED, anchor=MSO_ANCHOR.MIDDLE); xx += 2.2
            for t in TAG_ORDER:
                w = chip_w(t); add_box(s, xx, 6.3, w, 0.3, TAGS[t]); add_text(s, xx, 6.3, w, 0.3, t, 9.5, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE); xx += w + 0.1
        elif sl["kind"] == "table":
            add_text(s, 0.5, 0.22, 12.33, 0.98, sl["title"], tsize(sl["title"]), bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, 0.5, 1.18, why_w(sl["tags"]), 0.52, sl["why"], 11.5, color=MUTED, italic=True); add_chips(s, sl["tags"])
            add_table(s, 0.5, 1.75, 12.33, 4.05, sl["header"], sl["rows"])
            add_box(s, 0.5, 5.98, 12.33, 0.92, TINT)
            add_text(s, 0.62, 6.02, 12.1, 0.85, sl["closing"], 12, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, 0.5, 7.0, 11.4, 0.4, "Sources: " + sl["source"], 9, color=MUTED)
        else:
            L = layout(sl)
            add_text(s, *L["title"], sl["title"], tsize(sl["title"]), bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, *L["why"], sl["why"], 11.5, color=MUTED, italic=True); add_chips(s, sl["tags"])
            x, y, w, h = L["fig"]; s.shapes.add_picture(os.path.join(FIG, sl["fig"] + ".png"), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
            for (hd, tx), (bx, by, bw, bh) in zip(sl["points"], L["points"]):
                add_box(s, bx, by, bw, bh, TINT)
                add_text(s, bx + 0.1, by + 0.05, bw - 0.2, bh - 0.1, "", L["psize"], runs=[(hd + ".  ", True), (tx, False)])
            add_text(s, *L["source"], "Data: " + sl["source"] + "  ·  figure " + sl["fig"], 9, color=MUTED)
        add_text(s, 12.3, 7.05, 0.6, 0.3, str(n), 9.5, color=MUTED, align=PP_ALIGN.RIGHT)
        s.notes_slide.notes_text_frame.text = sl.get("notes", "")
    prs.save(path); print("wrote", path, len(SLIDES), "slides")

# ------------------------------------------------------------------ preview (matplotlib) + overflow check
def wrap(text, width_in, size, bold=False):
    cpl = max(10, int(width_in * 72 / (size * (0.60 if bold else 0.53))))        # DejaVu Sans is wider than Calibri: conservative
    return [l for t in (text if isinstance(text, list) else [text]) for l in (textwrap.wrap(t, cpl) or [""])]
def ptext(ax, x, y, w, h, text, size, bold=False, color="#1F2D3D", va="top", ha="left", warn="", italic=False):
    lines = wrap(text, w, size, bold); lh = size * 1.22 / 72; need = lh * len(lines)
    if need > h + 0.02: print(f"  OVERFLOW {warn}: needs {need:.2f} in, box {h:.2f} in ({len(lines)} lines at {size} pt)")
    yy = H - y if va == "top" else H - y - h / 2 + need / 2 - lh * 0.1
    for l in lines:
        ax.text(x if ha == "left" else x + w / 2, yy, l, fontsize=size * 0.98, fontweight="bold" if bold else "normal", color=color, va="top", ha=ha, family="DejaVu Sans", style="italic" if italic else "normal"); yy -= lh
def pbox(ax, x, y, w, h, fc, ec=None, r=0.08):
    ax.add_patch(FancyBboxPatch((x, H - y - h), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec or fc, lw=0.8))
def pchips(ax, tags, right=12.83, y=1.22):
    xx = right
    for t in reversed(tags):
        ww = chip_w(t); xx -= ww + 0.1; pbox(ax, xx, y, ww, 0.3, "#" + TAGS.get(t, "F3F3F3")); ax.text(xx + ww / 2, H - y - 0.15, t, ha="center", va="center", fontsize=9, color="#" + INK)
def build_preview():
    pdf = PdfPages(os.path.join(HERE, "deck-preview.pdf"))
    for n, sl in enumerate(SLIDES, 1):
        fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off"); fig.subplots_adjust(0, 0, 1, 1)
        if sl["kind"] == "title":
            ptext(ax, 0.9, 1.9, 11.5, 1.7, sl["title"], 30, bold=True, color="#" + NAVY, va="top", warn=f"s{n} title"); ptext(ax, 0.9, 3.7, 11.5, 0.9, sl["subtitle"], 18, warn=f"s{n} subtitle")
            ptext(ax, 0.9, 4.75, 11.5, 0.9, sl["meta"], 12, color="#" + MUTED, warn=f"s{n} meta")
            xx = 0.9; ax.text(xx, H - 6.45, "Evidence tags on each slide:", fontsize=10, color="#" + MUTED, va="center"); xx += 2.2
            for t in TAG_ORDER:
                ww = chip_w(t); pbox(ax, xx, 6.3, ww, 0.3, "#" + TAGS[t]); ax.text(xx + ww / 2, H - 6.45, t, ha="center", va="center", fontsize=9); xx += ww + 0.1
        elif sl["kind"] == "table":
            ptext(ax, 0.5, 0.22, 12.33, 0.98, sl["title"], tsize(sl["title"]), bold=True, color="#" + NAVY, va="middle", warn=f"s{n} title")
            ptext(ax, 0.5, 1.18, why_w(sl["tags"]), 0.52, sl["why"], 11.5, color="#" + MUTED, italic=True, warn=f"s{n} why"); pchips(ax, sl["tags"])
            rows = [sl["header"]] + sl["rows"]; rh = 4.05 / len(rows); y = 1.75
            for i, row in enumerate(rows):
                x = 0.5
                for j, txt in enumerate(row):
                    pbox(ax, x, y, TABLE_W[j], rh, "#" + (NAVY if i == 0 else ("FFFFFF" if i % 2 else TINT)), ec="#" + LINE, r=0)
                    ptext(ax, x + 0.06, y + 0.04, TABLE_W[j] - 0.12, rh - 0.08, txt, 10.5, bold=(i == 0 or j == 0), color="white" if i == 0 else "#" + INK, va="middle", warn=f"s{n} table r{i} c{j}")
                    x += TABLE_W[j]
                y += rh
            pbox(ax, 0.5, 5.98, 12.33, 0.92, "#" + TINT); ptext(ax, 0.62, 6.02, 12.1, 0.85, sl["closing"], 12, color="#" + NAVY, va="middle", warn=f"s{n} closing")
            ptext(ax, 0.5, 7.0, 11.4, 0.4, "Sources: " + sl["source"], 9, color="#" + MUTED, warn=f"s{n} source")
        else:
            L = layout(sl); x, y, w, h = L["fig"]
            ptext(ax, *L["title"], sl["title"], tsize(sl["title"]), bold=True, color="#" + NAVY, va="middle", warn=f"s{n} title")
            ptext(ax, *L["why"], sl["why"], 11.5, color="#" + MUTED, italic=True, warn=f"s{n} why"); pchips(ax, sl["tags"])
            im = Image.open(os.path.join(FIG, sl["fig"] + ".png")); ax.imshow(im, extent=(x, x + w, H - y - h, H - y), aspect="auto")
            for k, ((hd, tx), (bx, by, bw, bh)) in enumerate(zip(sl["points"], L["points"])):
                pbox(ax, bx, by, bw, bh, "#" + TINT); ptext(ax, bx + 0.1, by + 0.05, bw - 0.2, bh - 0.1, hd + ".  " + tx, L["psize"], warn=f"s{n} point {k + 1}")
            ptext(ax, *L["source"], "Data: " + sl["source"] + "  ·  figure " + sl["fig"], 9, color="#" + MUTED, warn=f"s{n} source")
        ax.text(12.83, 0.3, str(n), ha="right", va="bottom", fontsize=9.5, color="#" + MUTED)
        fig.savefig(os.path.join(OUTP, f"slide-{n:02d}.png"), dpi=80); pdf.savefig(fig); plt.close(fig)
    pdf.close(); print("wrote deck-preview.pdf and preview/slide-NN.png")

def write_outline():
    with open(os.path.join(HERE, "outline.md"), "w") as f:
        f.write("# Exploratory-study deck 2026-10-27 — outline\n\n| # | slide title | why | evidence | figure |\n|---|---|---|---|---|\n")
        for n, sl in enumerate(SLIDES, 1):
            f.write(f"| {n} | {sl['title']} | {sl.get('why', '—')} | {', '.join(sl.get('tags', []))} | {sl.get('fig', 'table')} |\n")
        f.write("\nEach content slide: one conclusion-style title, one 'why we did it' line, one matplotlib figure (or the summary table), three short statements, the data source, speaker notes with the why / how / result / explanation and the references.\n")
    with open(os.path.join(HERE, "README.md"), "w") as f:
        f.write("# Deck 2026-10-27 — reuse windows, future-aware prefetching and cache capacity (exploratory study)\n\n"
                "- `../SLIDES_2026-10-27-reuse-window-prefetch.pptx` — the editable deck (python-pptx, 16:9, Calibri); speaker notes carry the why / how / result / explanation and the references.\n"
                "- `figs/` — the Matplotlib figures (PNG 200 dpi + SVG) and `figs/SOURCES.md` (figure → raw files).\n"
                "- `preview/slide-NN.png`, `deck-preview.pdf` — layout preview drawn by matplotlib from the same slide data (no PowerPoint here); `outline.md` — the slide list.\n"
                "- Regenerate: `python3 scripts/figs_deck_2026-10-27.py && python3 scripts/deck_2026-10-27.py` from the repo root.\n"
                "- Data: `experimental_results/2026-10-27-reuse-window-prefetch/figs/*.csv` (figure data tables of the report), `train/run-61440/`, `train/beegfs-bw-c33.txt`; report `docs/experiments/2026-10-27-reuse-window-prefetch.md`.\n")
    print("wrote outline.md and README.md")

if __name__ == "__main__":
    build_pptx(DECK); build_preview(); write_outline()
