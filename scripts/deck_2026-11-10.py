#!/usr/bin/env python3
"""Build the progress deck of 2026-11-10 (6 slides): the GPU KV admission study (what we study, how the experiments are designed, what they
show) and one slide on the reuse distance of training data with CosmoFlow as the example. An editable PowerPoint (python-pptx, 16:9, white
background, Calibri) plus a preview PDF/PNGs drawn by matplotlib from the same slide data (layout check only: c28 has no PowerPoint or
LibreOffice; DejaVu Sans is wider than Calibri, so what fits in the preview fits in PowerPoint), outline.md and README.md.
Slide text is plain English: short sentences, every term explained where it first appears, every figure with a "how to read the figure" box
that names the axes. The numbers in the text are read from the data tables that scripts/figs_deck_2026-11-10.py writes next to the figures,
so text and figures cannot disagree.
usage: scripts/deck_2026-11-10.py   (run after scripts/figs_deck_2026-11-10.py; writes docs/slides/SLIDES_2026-11-10-kv-admission-progress.pptx
       and docs/slides/2026-11-10-kv-admission-progress/{deck-preview.pdf,preview/slide-NN.png,outline.md,README.md})"""
import csv, json, os, textwrap
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
HERE = os.path.join(ROOT, "docs", "slides", "2026-11-10-kv-admission-progress"); FIG = os.path.join(HERE, "figs"); OUTP = os.path.join(HERE, "preview"); os.makedirs(OUTP, exist_ok=True)
DECK = os.path.join(ROOT, "docs", "slides", "SLIDES_2026-11-10-kv-admission-progress.pptx")
W, H = 13.333, 7.5
INK, MUTED, NAVY, TINT, LINE = "1F2D3D", "6B6B6B", "1B2A41", "F3F6FA", "D9DEE5"
FONT = "Calibri"
TAGS = {"Real-system measurement": "E3F1E1", "Trace analysis": "FDEBD9", "Code reading": "E6E9F5", "Framing": "EEEEEE"}
TABLE_W = [1.75, 4.35, 3.3, 2.93]

# ------------------------------------------------------------------ numbers from the figure data tables
def table(name): return list(csv.reader(open(os.path.join(FIG, name + ".csv"))))[1:]
t1 = table("f01_problem"); ALONE_MISS, ALONE_HIT = float(t1[0][2]), float(t1[1][2]); BUSY = {r[1]: float(r[2]) for r in t1[2:]}
t3 = table("f03_cause"); CAUSE = [(float(r[1]), float(r[2])) for r in t3[:4]]; QUIET, BUSYP = float(t3[4][1]), float(t3[5][1])
t4 = table("f04_timeline"); TL = {(r[0], r[1]): (float(r[3]), float(r[4])) for r in t4}
ST, PR = "Stock server", "With the prototype"; HITS = ["host hit, sent at 0.5 s", "host hit, sent at 2.5 s", "host hit, sent at 4.5 s"]; LONG = "long request (28,000 tokens)"
t5 = table("f05_results"); R5 = {r[1]: [float(x) for x in r[2:6]] + [float(r[10])] for r in t5 if len(r) > 10}; KV = {r[1]: float(r[2]) for r in t5 if r[0].startswith("overload, KV")}
P04 = next(k for k in R5 if k.startswith("tool04-320-") and k != "tool04-320-base")           # the prototype run of the normal-load panel
N04, P4, N08, P8, PRIO = R5["tool04-320-base"], R5[P04], R5["tool08-320-base"], R5["tool08-320-p2"], R5.get("tool08-320-priohits")
RU = json.load(open(os.path.join(FIG, "f06_reuse-stats.json")))
pct = lambda a, b: f"{100 * (b - a) / a:+.0f} %".replace("-", "−")
PROTO04 = ("the first prototype version (token reserve and short steps)" if "tokfast11" in P04 else "the same prototype version as in (b)")

# ------------------------------------------------------------------ slide data
SLIDES = [
dict(kind="fig", kicker="1 · The problem   |   Progress report, 2026-11-10: CXL-enabled LLM serving with KV cache reuse",
     title=f"Saved KV data loads in {ALONE_HIT:.0f} ms, but on a busy server the requests that use it wait seconds",
     why="What we study: a server keeps the computed state of earlier prompts (the KV cache) in host memory. A later request can load it and skip the computation. "
         "Does the server use it fast?",
     tags=["Real-system measurement"], fig="f01_problem",
     points=[("Background", f"To answer a prompt, the model first reads it. The result is the KV cache. If a new request starts with the same text, the server can load the saved KV "
                            f"({ALONE_HIT:.0f} ms) and not compute it again ({ALONE_MISS:.0f} ms). GPU memory is small. Host memory is large: DRAM today, CXL in our plan."),
             ("The problem", f"On a busy server, a request that loads its KV from host memory waits {BUSY['host hit']:.1f} s for its first token. The load itself takes 0.05 s. "
                             f"A request whose KV is still in GPU memory waits {BUSY['GPU hit']:.1f} s. We want to know why, and if we can fix it."),
             ("How to read the figure", "Y axis: time to first token = the time from sending a request to its first output token. Lower is better. (a) One request alone on an idle "
                                        "server. (b) The median over the requests of a real trace on a busy server. Each bar is one kind of request.")],
     source="2026-11-04 serving study (one request alone)  ·  replay/tool04-320-base (tool-agent trace, 1,159 requests, 320 GB host cache)",
     notes="What we study. An LLM server computes a KV cache while it reads a prompt (the prefill). Requests of the same session or agent often start with the same text, so the KV of "
           "that prefix can be reused. GPU memory holds little of it (here 119k tokens), so the saved KV is kept in host memory by LMCache; in our plan this host tier is CXL memory. "
           "In all runs of this study the host tier is pinned DRAM, because the CXL devices on c28 are not accessible now (root-only permissions). So these are host-memory results, "
           f"not CXL measurements. Panel (a), from the 2026-11-04 study: a 4,000-token prompt alone on the idle server; computing it takes {ALONE_MISS:.0f} ms, loading the saved KV from "
           f"host memory takes {ALONE_HIT:.0f} ms to the first token. Panel (b), this study: the Mooncake tool-agent trace at a load the server can keep up with (GPU busy 49 % of the "
           f"time), stock vLLM 0.31.0 + LMCache 0.5.5, model Qwen2.5-3B-Instruct-AWQ, RTX 4060 Ti 8 GB, 320 GB host cache. Median time to first token: GPU hit {BUSY['GPU hit']:.2f} s, "
           f"host hit {BUSY['host hit']:.2f} s, miss {BUSY['miss']:.2f} s. A request counts as a host hit when at least half of its prompt is loaded from host memory, as a GPU hit when "
           "at least half is still in the GPU prefix cache, as a miss when less than 10 % is cached."),

dict(kind="table", kicker="2 · Experiment design",
     title="Experiment design: read the code, log every scheduling decision, test one cause at a time, then replay real traces",
     why="Why this design: the earlier study guessed the cause from the code. Here we measure it. We test every change against the unchanged server with the same requests.",
     tags=["Framing"],
     header=["Step", "What we did", "What it answers", "Setup"],
     rows=[["1. Read the code", "Read the scheduler of vLLM 0.31 and the connector of LMCache 0.5.5: the serving engine and the KV cache that we use.",
            "The exact rules that decide when a waiting request may start.", "The installed source, with file and line."],
           ["2. Log every decision", "Added logging-only hooks. For every attempt to start a request we record: free GPU memory, memory needed, accepted or refused, and the reason.",
            "Where the waiting time goes, in seconds per cause.", "Cost: 6 microseconds per engine step, 0.01 % of the run time."],
           ["3. Controlled tests", "Built small scenarios: one long request with cached requests behind it; GPU memory filled to a chosen level; a hit and a miss of the same length.",
            "Cause and effect, one mechanism at a time.", "3 repetitions; same machine; same GPU memory pool."],
           ["4. Real traces", "Replayed the Mooncake tool-agent and conversation traces at normal load and at overload (arrivals twice as fast). Stock server against prototype.",
            "The end-to-end effect on hits, misses and all requests.", "RTX 4060 Ti 8 GB, Qwen2.5-3B, 320 GB host cache (DRAM: the CXL devices are not accessible now)."],
           ["5. Other sizes", "Repeated the tests with 2.7 times the GPU KV memory and with a larger model (7B).",
            "Is the problem only our small GPU?", "RTX 4060 Ti 16 GB machines."]],
     closing="In every comparison only the scheduler setting changes. The requests, their arrival times, the model, the GPU memory pool and the host cache size stay the same.",
     source="docs/experiments/2026-11-10-gpu-kv-admission.md (environment, parts A, B, C)",
     notes="The five steps follow the brief of the study. Step 1: the admission path of a waiting request in vllm/v1/core/sched/scheduler.py and kv_cache_manager.py, and the LMCache "
           "connector. Step 2: the hooks wrap four functions of the scheduler process and only write log lines; the scheduler call takes 129 microseconds without them and 135 with "
           "them, and the stock run with hooks reproduces the earlier run without hooks. Step 3: scenarios built with a driver that starts long-running requests to fill the GPU KV "
           "memory to a chosen level and then sends probes; the memory pressure is read from the scheduler's own counters. Step 4: the replay sends each request at its trace time, "
           "whatever happened to earlier requests. Normal load is 0.04 times the trace speed (the server keeps up, GPU busy 49 %), overload is 0.08 times (the backlog grows). The GPU "
           "KV pool is fixed to 7,456 blocks in all compared runs. Step 5: machines with the same GPU model and 16 GB; a faster GPU (A100, H100) is in use by other users until "
           "2026-11-13. Some runs of steps 4 and 5 were still in the queue when this deck was built."),

dict(kind="fig", kicker="3 · Result: the cause",
     title="The cause is the scheduler's step budget and a full GPU, not the memory reservation that we suspected",
     why="Why we measured it: the earlier explanation was a memory rule: a hit must reserve GPU memory for its whole saved prefix before it can load. "
         "The logs show which rule really makes requests wait.",
     tags=["Code reading", "Real-system measurement"], fig="f03_cause",
     points=[("What we found", f"The engine works in steps of at most 2,048 tokens. A long prompt uses the whole step, for many steps. In these steps the engine does not look at "
                               f"the waiting queue: {CAUSE[0][0]:.0f} % of the waiting time. GPU memory full, and the first request in line blocks the rest: "
                               f"{CAUSE[1][0]:.0f}–{CAUSE[1][1]:.0f} %. The reservation rule: {CAUSE[3][0]:.1f} %."),
             ("What it means", f"A host hit that arrives when no long prompt is being read answers in {QUIET:.1f} s. One that arrives during a long prompt waits {BUSYP:.1f} s. "
                               "The saved KV is fast. The scheduler makes it wait. Misses and GPU hits wait for the same reasons."),
             ("How to read the figure", "(a) X axis: the reason why a request waits. Y axis: share of the total waiting time of host hits, in percent. Blue: normal load. Purple: "
                                        "overload. (b) Y axis: median time to first token of a host hit. The two bars split the requests by what the server was doing when they arrived.")],
     source="replay/tool04-320-base (normal load), replay/tool08-320-base (overload); stock vLLM 0.31.0 + LMCache 0.5.5",
     notes="How the shares are computed. Every engine step that a request spends waiting is charged to one reason, from the scheduler's own state in that step. 'Step budget' = the "
           "running requests used all 2,048 tokens of the step, so the scheduler did not enter its waiting-queue loop (or earlier admissions of the same scan used the rest). 'Not "
           "enough free GPU memory' = the request at the head of the queue was refused because the blocks of its whole sequence were not free, and the scan stopped there; this rule "
           "is the same for hits and misses. 'Reservation' = the request fitted in the free blocks but not under the blocks reserved for prefills in flight; this was the suspected "
           "cause, and it refused 17 of 4,924 attempts at normal load and 9 of 6,527 under overload. A controlled test confirms the symmetry: with too little free memory a hit and a "
           "miss of the same length are refused by the same rule and admitted in the same step after memory is released. Panel (b): 73 host hits arrived when no prefill was in "
           f"flight ({QUIET:.2f} s), 75 arrived during one ({BUSYP:.1f} s). The large gap between host hits and GPU hits in slide 1 is partly this: a prefix is served from host "
           "memory mostly when the server is busy and the GPU cache has been overwritten. The same picture holds with 2.7 times the GPU memory: the memory part disappears (0 "
           "refusals), the step-budget part stays (the same 20 % of the run has its budget used up). One more finding from the logs: when a refused request is retried, the stock "
           "LMCache connector skips saving its new KV (slide 5, panel c)."),

dict(kind="side", kicker="4 · Result: a fix, in a controlled test",
     title="A small scheduler change gives a cached request its first token after about 1 s, not 4 to 8 s",
     why="Why this test: one long request and three cached requests behind it, with enough free GPU memory. It isolates the step-budget cause. "
         "The prototype changes scheduling rules only; the engine code is not patched.",
     tags=["Real-system measurement"], fig="f04_timeline",
     points=[("The prototype", "It keeps a small part of every step for short work. So the engine looks at the queue also during a long prompt. While a cached request is on its "
                               "way, the steps are short. Long requests still start in arrival order."),
             ("Result", f"First token of the three host hits: {TL[(ST, HITS[0])][0]:.1f} / {TL[(ST, HITS[1])][0]:.1f} / {TL[(ST, HITS[2])][0]:.1f} s → "
                        f"{TL[(PR, HITS[0])][0]:.1f} / {TL[(PR, HITS[1])][0]:.1f} / {TL[(PR, HITS[2])][0]:.1f} s. Cost: the long request gets its first token "
                        f"{100 * (TL[(PR, LONG)][0] / TL[(ST, LONG)][0] - 1):.0f} % later. Two of the three hits still finish as late as before: after its first token a request gets "
                        "one token per step, and steps are long while the long prompt is read."),
             ("How to read the figure", "Each row is one request. X axis: seconds since the long request was sent. The colours show what the request is doing. Grey: it waits and the "
                                        "engine does not look at it. Black tick: first token. Top: stock server. Bottom: prototype.")],
     source="E16/c1c: c1c-base, c1c-tokfast512-sync (1 of 3 repetitions; medians of the three hits over all repetitions: 0.94 / 1.04 / 1.10 s)",
     notes="The scenario (run_adm.py plan c1): six small requests decode in the background and 5,500 of the 7,456 GPU KV blocks are free, so memory is not the limit. A miss of "
           "28,000 tokens starts its prefill; host hits of 4,000 tokens are sent 0.5, 2.5 and 4.5 s later and a 4,000-token miss 1.5 s later; every request generates 16 tokens. "
           "Stock: every request sent during the long prefill gets its first token after the long request's (7.3 s). The prototype (flags tokres=768, fastchunk=512, with synchronous "
           "scheduling): before each step it caps the running long prefill so that up to 768 tokens are left for short work (the tail of a loaded hit, short prompts), or one token "
           "so that the scan of the queue runs; while a lookup or a load is under way the whole step is limited to 512 tokens, so the step boundaries that a hit needs come sooner; "
           "a request that needs more than the reserve is not started with the left-over, so long work stays first-come-first-served (the red bar of the 4,000-token miss). Cost: the "
           "long request's first token 10 % later, the 4,000-token miss about 12 % later. The request time (last token): first hit 8.3 → 4.8 s, the other two 6.4 → 6.5 s and 4.4 → 4.7 s, "
           "because a decoding request gets one token per engine step and a step is a 2,048-token chunk (0.3 s) during the prefill. Existing vLLM options do not give this result: "
           "synchronous scheduling alone changes nothing here; a prefill cap of 1,024 tokens helps the first hit (2.3 s) but slows the long request by 18 % and is worse on every "
           "metric in the overloaded trace; a 512-token step for everybody is worse everywhere. Three other ideas were tested and did not work: relaxing the memory reservation of a "
           "load (one preemption per trial), computing instead of loading when the load is refused (never possible: the same memory rule refuses both), loading the KV in pieces (not "
           "possible in the connector protocol, and it would not be admitted earlier)."),

dict(kind="fig", kicker="5 · Result: real traces",
     title="On real traces: a clear gain at normal load; under overload it is a trade, and the order of requests matters most",
     why="Why both loads: a fix must help when the server keeps up and must not hurt when it does not. Stock and prototype serve the same requests with the same arrival times.",
     tags=["Real-system measurement"], fig="f05_results",
     points=[("Normal load (a)", f"Mean time to first token of all requests: {N04[3]:.1f} → {P4[3]:.1f} s ({pct(N04[3], P4[3])}). Host hits {N04[0]:.1f} → {P4[0]:.1f} s, GPU hits "
                                 f"{N04[1]:.1f} → {P4[1]:.1f} s. Misses pay a little: {N04[2]:.1f} → {P4[2]:.1f} s ({pct(N04[2], P4[2])}). Requests finish {abs(100 * (P4[4] - N04[4]) / N04[4]):.0f} % "
                                 "sooner on average. A second machine gives the same picture (−23 %)."),
             ("Overload (b)", f"The prototype moves waiting time from hits to misses: host hits {N08[0]:.1f} → {P8[0]:.1f} s, misses {N08[2]:.1f} → {P8[2]:.1f} s, all requests "
                              f"{pct(N08[3], P8[3])}. " + (f"vLLM's own priority scheduler does better ({pct(N08[3], PRIO[3])}) if we tell it in advance which requests are hits. "
                              "A real client does not know this." if PRIO else "")),
             ("How to read the figure, and (c)", "(a), (b) Y axis: mean time to first token in seconds. One group of bars per kind of request. Blue: stock. Orange: prototype. Green: "
                                                 f"priority with perfect knowledge. (c) KV saved to host memory in the overload run: {KV['tool08-320-base']:.0f} GB. The stock server "
                                                 f"loses about a third after retries. A small fix saves all of it ({KV['tool08-320-storefix']:.0f} GB).")],
     source=f"(a) replay/tool04-320-base, {P04} ({'first prototype version' if 'tokfast11' in P04 else 'same version as in (b)'})  ·  (b), (c) tool08-320-base, -p2 (prototype with safety rules), -priohits, -storefix",
     notes="The replays: Mooncake tool-agent trace, the same requests and arrival times in every run, GPU KV pool 7,456 blocks, 320 GB host cache; request kinds are fixed by the "
           f"stock run and the same requests are followed in the other runs. Panel (a), normal load (0.04 times the trace speed, 1,159 requests): prototype = {PROTO04}. All requests: "
           f"mean time to first token {N04[3]:.2f} → {P4[3]:.2f} s, median 1.56 → 1.21 s, 95th percentile 21.0 → 17.6 s, 99th percentile unchanged (34 s); mean request time "
           f"{N04[4]:.1f} → {P4[4]:.1f} s; the misses' request time +1 %; throughput unchanged. Replication on a second machine (same GPU model, 80 GB host cache, the safe prototype "
           "version): mean time to first token 5.41 → 4.19 s (−23 %), host hits median 6.6 → 1.6 s, misses +8 %. Panel (b), overload (0.08 times, 544 requests): prototype = token "
           "reserve and short steps with two safety rules and a 3-second bypass of a request that waits for memory. It is a trade: host hits −43 %, misses +29 %, all requests −4 %, "
           "95th percentile +8 %. The first prototype version passed blocked requests without a limit: hits 4 to 7 times sooner, but single requests waited up to 78 s (stock 53 s). "
           "The green bars are vLLM's existing priority scheduling with ORACLE priorities: a request that was a hit in the stock run is sent with priority 0. It lowers the mean time to "
           "first token of all requests by 33 % and the mean request time by 16 %, with misses +15 %. A client cannot know in advance which requests are hits; a server could find out "
           "with a cache lookup at arrival. So under overload the order of requests matters more than the mechanisms of the prototype; the combination is in the queue. Panel (c): the "
           "LMCache connector adds the hit length to a counter at every retry of a waiting request, and the save of new KV starts at that counter, so retried requests skip their "
           "saves: 5–6 % of the KV at normal load, 31–33 % under overload, also in the runs of the earlier study. The fix alone (stock scheduling) saves 109 GB and no kind of request "
           "is slower (all within 3 % of stock)."),

dict(kind="fig", kicker="6 · Side question: reuse distance of training data (CosmoFlow)",
     title="Reuse distance in CosmoFlow training: a file comes back after about one full pass over the data, never inside the same epoch",
     why="The question: how many data references occur before the same data is accessed again, and does the same data appear again in the same epoch? "
         f"Measured on our CosmoFlow run: {RU['files']:,} files (178 GB), {RU['epochs']} epochs.",
     tags=["Real-system measurement", "Trace analysis"], fig="f06_reuse",
     points=[("Answer 1: references in between", f"Reuse distance = the number of other files read between two reads of the same file. Mean: {RU['mean']:,.0f}, the whole data set once "
                                                 f"(178 GB, about 15 minutes). Smallest {RU['min']:,}, largest {RU['max']:,}: almost two passes. Reason: the benchmark shuffles the file "
                                                 "order again for every epoch."),
             ("Answer 2: again in the same epoch?", f"No. In each of the {RU['epochs']} epochs every one of the {RU['files']:,} files is read exactly once. No file is read twice in an "
                                                    "epoch: an epoch is one pass over a shuffled list. With 4 GPUs (we ran the data pipeline for 4 ranks) it is the same, but "
                                                    "only 1 file in 4 comes back to the same GPU in the next epoch."),
             ("How to read the figure; why it matters", "(a) X axis: position in the run, in files read so far. Each row is one file, a dot is one read, dashed lines are epoch borders. "
                                                        "(b) X axis: reuse distance. Y axis: number of re-reads with this distance. Why it matters: a cache that keeps the most recent "
                                                        f"half of the files serves only {100 * RU['lru_hit_share_cache_50pct']:.0f} % of the re-reads.")],
     source="CosmoFlow run of 2026-10-27 on c33 (train/run-61440/reads.txt)  ·  benchmark code data/cosmo.py  ·  scripts/cosmoflow_shard_check.py",
     notes="The data: the group's CosmoFlow benchmark (TensorFlow, MLPerf HPC data) on the 61,440-file subset (one sample per file, about 2.9 MB each, 178 GB), 3 epochs, batch size "
           "4, on the A100 node c33; every file read was logged (184,320 reads). CosmoFlow has one sample per file and no augmentation, so the file order is the sample order. "
           f"Answer 1. For every re-read we count the other files read since the last read of the same file. There are {RU['re_reads']:,} re-reads (every file twice, in epochs 2 and "
           f"3). Mean {RU['mean']:,.0f} = N − 1 with N = {RU['files']:,}; median {RU['median']:,.0f}; 5 % are below {RU['p5']:,.0f} and 5 % above {RU['p95']:,.0f}; smallest "
           f"{RU['min']:,}, largest {RU['max']:,}. In bytes: 178 GB read in between on average; in time: 873 s on average (1.7 s to 1,784 s). The shape is a triangle from 0 to 2N − 2 "
           "because the benchmark draws a new random order for every epoch (tf.data shuffle over the whole file list with reshuffle_each_iteration=True): a file read late in one epoch "
           "and early in the next has a short distance, one read early and then late has a long distance. Without reshuffling every distance would be exactly N − 1. The full data set "
           "has 524,288 files (1.7 TB); the same rule gives a mean of about 524,287 files. Answer 2. Counted per epoch: 61,440 reads, 61,440 different files, 0 files read twice, in "
           "each of the 3 epochs. With several GPUs (Horovod) the benchmark shuffles the file list with the same seed on every rank and then gives rank r every R-th file. We ran this "
           "pipeline for 4 ranks on the CPU (TensorFlow 2.14, 1,024 files, 3 epochs): in every epoch each file is read by exactly one rank, and 22–30 % of a rank's files come back to "
           "the same rank in the next epoch. So for a cache on one node the distance is longer than one epoch. Why it matters for a cache: a cache that evicts the least recently used "
           f"files and holds 25 % / 50 % / 75 % of the files serves {100 * RU['lru_hit_share_cache_25pct']:.1f} % / {100 * RU['lru_hit_share_cache_50pct']:.1f} % / "
           f"{100 * RU['lru_hit_share_cache_75pct']:.1f} % of the re-reads of this trace (computed from the trace; it follows c + (1 − c) ln(1 − c)), less than the cached share, "
           "because the files read most recently are the ones that will come back last. A cache that never evicts (keeps a fixed part of the data) serves its share: 50 % cached, 50 % "
           "served."),
]

# ------------------------------------------------------------------ layout helpers
def fig_size(name, maxw, maxh):
    im = Image.open(os.path.join(FIG, name + ".png")); r = im.width / im.height; w = maxw; h = w / r
    if h > maxh: h = maxh; w = h * r
    return w, h
def tsize(t): return 24 if len(t) < 80 else 22 if len(t) < 100 else 20
def chip_w(t): return 0.16 + 0.072 * len(t)
def why_w(tags): return 12.33 - sum(chip_w(t) + 0.1 for t in tags) - 0.3
PSIZE = 11.5
def layout(sl):
    L = dict(kicker=(0.5, 0.1, 12.33, 0.26), title=(0.5, 0.34, 12.33, 0.86), why=(0.5, 1.2, why_w(sl["tags"]), 0.52), source=(0.5, 7.02, 11.4, 0.36))
    if sl["kind"] == "fig":
        fw, fh = fig_size(sl["fig"], 12.33, 3.22); L["fig"] = (0.5 + (12.33 - fw) / 2, 1.78, fw, fh)
        n = len(sl["points"]); gap = 0.2; bw = (12.33 - gap * (n - 1)) / n; y0 = 1.78 + fh + 0.14; bh = 6.94 - y0
        L["points"] = [(0.5 + i * (bw + gap), y0, bw, bh) for i in range(n)]
    elif sl["kind"] == "side":
        fw, fh = fig_size(sl["fig"], 8.55, 5.1); L["fig"] = (0.5, 1.8 + (5.1 - fh) / 2, fw, fh)
        n = len(sl["points"]); gap = 0.14; x0 = 0.5 + fw + 0.22; bw = 12.83 - x0; hs = [1.32, 1.92, 1.56] if n == 3 else [(5.08 - gap * (n - 1)) / n] * n; y = 1.8; L["points"] = []
        for h in hs: L["points"].append((x0, y, bw, h)); y += h + gap
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
def add_chips(slide, tags, right=12.83, y=1.24):
    x = right
    for t in reversed(tags):
        w = chip_w(t); x -= w + 0.1
        add_box(slide, x, y, w, 0.3, TAGS.get(t, "F3F3F3"))
        add_text(slide, x, y, w, 0.3, t, 9.5, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
def add_table(slide, x, y, w, h, header, rows, size=11):
    shp = slide.shapes.add_table(len(rows) + 1, len(header), Inches(x), Inches(y), Inches(w), Inches(h)); tbl = shp.table
    tblPr = tbl._tbl.tblPr; tblPr.set("bandRow", "0"); tblPr.set("firstRow", "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None: sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"       # "No Style, Table Grid": thin grid, no theme banding
    for j, cw in enumerate(TABLE_W): tbl.columns[j].width = Inches(cw)
    for i, row in enumerate([header] + rows):
        for j, txt in enumerate(row):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.07); c.margin_top = c.margin_bottom = Inches(0.03); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid(); c.fill.fore_color.rgb = rgb(NAVY if i == 0 else ("FFFFFF" if i % 2 else TINT))
            tf = c.text_frame; tf.word_wrap = True; p = tf.paragraphs[0]; r = p.add_run(); r.text = txt
            r.font.size = Pt(size); r.font.name = FONT; r.font.bold = (i == 0 or j == 0); r.font.color.rgb = rgb("FFFFFF" if i == 0 else INK)
    return shp
def build_pptx(path):
    prs = Presentation(); prs.slide_width = Inches(W); prs.slide_height = Inches(H); blank = prs.slide_layouts[6]
    for n, sl in enumerate(SLIDES, 1):
        s = prs.slides.add_slide(blank); L = layout(sl)
        add_text(s, *L["kicker"], sl["kicker"], 10.5, color=MUTED, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, *L["title"], sl["title"], tsize(sl["title"]), bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, *L["why"], sl["why"], 11.5, color=MUTED, italic=True); add_chips(s, sl["tags"])
        if sl["kind"] == "table":
            add_table(s, 0.5, 1.82, 12.33, 4.1, sl["header"], sl["rows"])
            add_box(s, 0.5, 6.08, 12.33, 0.82, TINT)
            add_text(s, 0.62, 6.1, 12.1, 0.78, sl["closing"], 12.5, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, *L["source"], "Source: " + sl["source"], 9, color=MUTED)
        else:
            x, y, w, h = L["fig"]; s.shapes.add_picture(os.path.join(FIG, sl["fig"] + ".png"), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
            for (hd, tx), (bx, by, bw, bh) in zip(sl["points"], L["points"]):
                add_box(s, bx, by, bw, bh, TINT)
                add_text(s, bx + 0.1, by + 0.05, bw - 0.2, bh - 0.1, "", PSIZE, runs=[(hd + ("  " if hd.endswith("?") else ".  "), True), (tx, False)])
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
def pchips(ax, tags, right=12.83, y=1.24):
    xx = right
    for t in reversed(tags):
        ww = chip_w(t); xx -= ww + 0.1; pbox(ax, xx, y, ww, 0.3, "#" + TAGS.get(t, "F3F3F3")); ax.text(xx + ww / 2, H - y - 0.15, t, ha="center", va="center", fontsize=9, color="#" + INK)
def build_preview():
    pdf = PdfPages(os.path.join(HERE, "deck-preview.pdf"))
    for n, sl in enumerate(SLIDES, 1):
        fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off"); fig.subplots_adjust(0, 0, 1, 1); L = layout(sl)
        ptext(ax, *L["kicker"], sl["kicker"], 10.5, bold=True, color="#" + MUTED, va="middle", warn=f"s{n} kicker")
        ptext(ax, *L["title"], sl["title"], tsize(sl["title"]), bold=True, color="#" + NAVY, va="middle", warn=f"s{n} title")
        ptext(ax, *L["why"], sl["why"], 11.5, color="#" + MUTED, italic=True, warn=f"s{n} why"); pchips(ax, sl["tags"])
        if sl["kind"] == "table":
            rows = [sl["header"]] + sl["rows"]; rh = 4.1 / len(rows); y = 1.82
            for i, row in enumerate(rows):
                x = 0.5
                for j, txt in enumerate(row):
                    pbox(ax, x, y, TABLE_W[j], rh, "#" + (NAVY if i == 0 else ("FFFFFF" if i % 2 else TINT)), ec="#" + LINE, r=0)
                    ptext(ax, x + 0.07, y + 0.04, TABLE_W[j] - 0.14, rh - 0.08, txt, 11, bold=(i == 0 or j == 0), color="white" if i == 0 else "#" + INK, va="middle", warn=f"s{n} table r{i} c{j}")
                    x += TABLE_W[j]
                y += rh
            pbox(ax, 0.5, 6.08, 12.33, 0.82, "#" + TINT); ptext(ax, 0.62, 6.1, 12.1, 0.78, sl["closing"], 12.5, color="#" + NAVY, va="middle", warn=f"s{n} closing")
            ptext(ax, *L["source"], "Source: " + sl["source"], 9, color="#" + MUTED, warn=f"s{n} source")
        else:
            x, y, w, h = L["fig"]; im = Image.open(os.path.join(FIG, sl["fig"] + ".png")); ax.imshow(im, extent=(x, x + w, H - y - h, H - y), aspect="auto")
            for k, ((hd, tx), (bx, by, bw, bh)) in enumerate(zip(sl["points"], L["points"])):
                pbox(ax, bx, by, bw, bh, "#" + TINT); ptext(ax, bx + 0.1, by + 0.05, bw - 0.2, bh - 0.1, hd + ("  " if hd.endswith("?") else ".  ") + tx, PSIZE, warn=f"s{n} point {k + 1}")
            ptext(ax, *L["source"], "Data: " + sl["source"] + "  ·  figure " + sl["fig"], 9, color="#" + MUTED, warn=f"s{n} source")
        ax.text(12.83, 0.3, str(n), ha="right", va="bottom", fontsize=9.5, color="#" + MUTED)
        fig.savefig(os.path.join(OUTP, f"slide-{n:02d}.png"), dpi=80); pdf.savefig(fig); plt.close(fig)
    pdf.close(); print("wrote deck-preview.pdf and preview/slide-NN.png")

def write_outline():
    with open(os.path.join(HERE, "outline.md"), "w") as f:
        f.write("# Progress deck 2026-11-10 — outline\n\n| # | section | slide title | figure |\n|---|---|---|---|\n")
        for n, sl in enumerate(SLIDES, 1): f.write(f"| {n} | {sl['kicker'].split('|')[0].strip()} | {sl['title']} | {sl.get('fig', 'table')} |\n")
        f.write("\nEach slide: a conclusion as the title, one line that says why, one matplotlib figure (or the design table), three short text boxes — one of them explains how to "
                "read the figure (axes, colours) — the data source, and speaker notes with the details.\n")
    with open(os.path.join(HERE, "README.md"), "w") as f:
        f.write("# Deck 2026-11-10 — GPU KV admission study (progress) and the reuse distance of training data (CosmoFlow)\n\n"
                "- `../SLIDES_2026-11-10-kv-admission-progress.pptx` — the editable deck (python-pptx, 16:9, Calibri), 6 slides; the speaker notes carry the details and the caveats.\n"
                "- `figs/` — the matplotlib figures (PNG 200 dpi + SVG), their data tables (CSV / JSON), `figs/SOURCES.md` (figure → raw files) and `figs/cosmoflow-shard-check.txt`.\n"
                "- `preview/slide-NN.png`, `deck-preview.pdf` — layout preview drawn by matplotlib from the same slide data (no PowerPoint on c28); `outline.md` — the slide list.\n"
                "- Regenerate: `python3 scripts/figs_deck_2026-11-10.py && python3 scripts/deck_2026-11-10.py` from the repo root (the slide text reads its numbers from the figure data "
                "tables). When `replay/tool04-320-p2` exists, panel (a) of slide 5 switches to it automatically.\n"
                "- Data: `experimental_results/2026-11-10-gpu-kv-admission/` (replays, controlled scenarios), the CosmoFlow trace of 2026-10-27 on branch `explore/reuse-window-prefetch`; "
                "report `docs/experiments/2026-11-10-gpu-kv-admission.md`. The study was still running when the deck was built (2026-11-10 23:50).\n")
    print("wrote outline.md and README.md")

if __name__ == "__main__":
    build_pptx(DECK); build_preview(); write_outline()
