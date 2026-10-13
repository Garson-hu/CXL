#!/usr/bin/env python3
"""Build the research-progress deck of 2026-10-13: an editable PowerPoint (python-pptx), a preview PDF + PNGs drawn
with matplotlib from the same slide data (for layout checks; the real rendering is PowerPoint's), and outline.md.
Slide text is written in Simplified Technical English style: short sentences, one idea each, active voice.
usage: scripts/deck_2026-10-13.py   (run after scripts/figs_deck_2026-10-13.py; writes docs/slides/SLIDES_2026-10-13-progress-report.pptx, the preview and outline.md)"""
import csv, glob, os, re, textwrap
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # scripts/ -> repo root
HERE = os.path.join(ROOT, "docs", "slides", "2026-10-13-progress-report"); FIG = os.path.join(HERE, "figs")   # deck sources: docs/slides is local-only (gitignored)
E = os.path.join(ROOT, "experimental_results"); OUTP = os.path.join(HERE, "preview"); os.makedirs(OUTP, exist_ok=True)
W, H = 13.333, 7.5
INK, MUTED, NAVY, TINT = "1F2D3D", "6B6B6B", "1B2A41", "EEF2F7"
TAGS = {"Hardware measurement": "DBE7F3", "Real application": "E3F1E1", "Trace-driven emulation": "FDEBD9", "Trace simulation": "EFE9F5", "Estimate": "F3F3F3",
        "Proposal (not implemented)": "FBE3E3", "Emulated policy": "FDEBD9", "System built 2026-09-19": "E3F1E1", "Analysis": "F3F3F3", "Summary": "F3F3F3", "Pending": "FBE3E3"}
FONT = "Calibri"

# ------------------------------------------------------------------ data for the dynamic slides
def eval_reps():
    p = os.path.join(E, "2026-10-12-budget-gated-admission", "evaluation", "summary.csv")
    if not os.path.exists(p): return 0
    tags = [r["tag"] for r in csv.DictReader(open(p))]
    return max((int(m[1]) for t in tags for m in [re.search(r"-r(\d+)$", t)] if m), default=0)
REPS = eval_reps()
HAVE_DEPTH = os.path.exists(os.path.join(FIG, "f18_bga_depth.png")); HAVE_VARY = os.path.exists(os.path.join(FIG, "f19_bga_varying.png"))

def pending_fig(name, title, lines):
    fig, ax = plt.subplots(figsize=(9.5, 4.4)); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.02, 0.05), 0.96, 0.9, boxstyle="round,pad=0.01,rounding_size=0.03", fc="#fbe3e3", ec="#c77", lw=1.2, transform=ax.transAxes))
    ax.text(0.5, 0.86, title, ha="center", va="center", fontsize=16, fontweight="bold", color="#7a1f1f", transform=ax.transAxes)
    ax.text(0.05, 0.74, "\n".join(lines), ha="left", va="top", fontsize=11, color="#222222", transform=ax.transAxes, linespacing=1.55)
    fig.savefig(os.path.join(FIG, name + ".png"), dpi=200, bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------ slides
def S(title, part, tags, fig, bullets, takeaway, source, notes): return dict(title=title, part=part, tags=tags, fig=fig, bullets=bullets, takeaway=takeaway, source=source, notes=notes)
SLIDES = []
SLIDES.append(dict(kind="title", title="Interference-Aware Data Management with DRAM and CXL Memory", subtitle="Research progress and experimental findings",
                   meta="Progress report for Dr. Mueller  ·  2026-10-13  ·  c28 (AMD EPYC 9745, 4× CXL CZ120) and c35 (Optane)",
                   notes="Title. This deck follows the research from the original CXL-first write isolation idea, through the advisor's unified memory management "
                         "suggestion, to the current direction: interference-aware capacity and bandwidth management. Every data figure is drawn from the raw result "
                         "files with matplotlib (presentation/2026-10-13-progress/make_figs.py). Each slide carries a tag that says what kind of evidence it shows."))
SLIDES.append(S("Bulk writes into DRAM stall every DRAM reader; the same writes into CXL do not", "Part I · Original research idea", ["Hardware measurement"], "f01_drain_cliff",
    ["Non-temporal writers on 4 of 8 core groups cut a 4-thread DRAM reader to 8% of its idle bandwidth. Writers on 1–2 groups cost it 18–21%. The loss is a cliff, not a slope.",
     "The memory controller enters write-drain mode when its write queue stays above the watermark. Reads then wait for short windows between write batches.",
     "Checkpoint staging and KV-cache stores are such bulk writes. Both grow with the model size.",
     "The same 8 writer threads into CXL cost the reader 0% when they run on another core group."],
    "CXL is a second, independent memory path. Bulk writes can use it without stalling DRAM readers.",
    "2026-09-08-dram-write-drain (run 2026-09-14) · 2026-10-09-cxl-topology-interference (2026-10-10)",
    "Setup: c28, EPYC 9745 with 8 core groups (CCDs) of 16 cores, NPS1, idle machine. The victim is a 4-thread streaming reader on CCD 0; the writers use non-temporal "
    "stores from other CCDs; 3 repetitions, medians. The CXL bar comes from the topology run of 2026-10-10 (reader on CCD 4, writers on CCD 0). "
    "Why non-temporal stores are the worst case: they skip the read-for-ownership and post full lines straight into the controller's write queue, so 2 threads already "
    "saturate one CCD. Plain stores also collapse the reader (4.1× in the August test). The reader plus the writers always sum to the socket's pipe (~290–300 GiB/s): one "
    "conserved pipe. Limits: synthetic streams, one machine; UMC counters were not available (perf_event_paranoid=2)."))
SLIDES.append(S("Original design: write to CXL by default, borrow DRAM only with measured headroom", "Part I · Original research idea", ["System built 2026-09-19"], "f03_arch_original",
    ["Every bulk write goes to a segment store on raw CXL (Device-DAX). There is no DRAM staging copy and no system call on the data path.",
     "DRAM is lent to a writer only while CXL is full and a DRAM latency probe shows headroom for other readers. The loan is revoked at zero cost.",
     "Reads are served in place. A block is copied to DRAM only when its reuse pays for the copy.",
     "Checkpoints drain from CXL to NVMe without a DRAM copy."],
    "DRAM held copies of CXL data (inclusive placement). DRAM added speed, not capacity.",
    "docs/DESIGN.md §10 · system/cxlpath (user-space runtime, built 2026-09-19)",
    "The runtime (cxlpath) has four components: a segment store on raw CXL with a node-owned index; interference-bounded placement driven by a DRAM latency probe "
    "(~1000 dependent reads every ~30 ms, no root, no counters) plus a write ledger; a read path that promotes by break-even; and a DRAM-free drain to NVMe. Clients: a "
    "VeloC-style checkpoint shim, the PyTorch async checkpoint stager, and an LMCache-like KV layer. The design borrows ideas from PolyStore (FAST'25) — using devices "
    "side by side — but PolyStore is not a baseline. The inclusive read path is what the advisor's suggestion (next part) questions."))
SLIDES.append(S("First results: the loan works beside moderate victims; beside saturated ones the guard lends nothing", "Part I · Original research idea", ["Real application"], "f02_original_core",
    ["64 GiB checkpoints every 25 s beside real programs on c28; 3 runs each, medians.",
     "DRAM staging slows the reader 28% and PageRank 68%. All-CXL harms them ≤ 1% but copies 1.5–2× slower.",
     "cxlpath lends 23–34% of the chunks: 6–8% harm, copies 1.3–1.5× faster than all-CXL.",
     "Beside the 80-thread Adam step the guard refuses every loan: cxlpath equals all-CXL (7% harm, 3.5 s)."],
    "The guard decides the regime. Beside DRAM-heavy programs it finds no headroom. We meet this limit again in Part VI.",
    "2026-09-22-three-policies-realdata/summary.csv (117 runs, 2026-09-22/23)",
    "Real applications: the synthetic 8-thread DRAM reader, PageRank (GAP benchmark suite, 32 threads, 192 GiB checkpoint every 30 s) and a CPU Adam optimizer step on 80 "
    "threads. The checkpoint producer fills its snapshot with pseudo-random data (an earlier campaign had written zero lines, which c28 writes at full speed — those numbers "
    "were discarded). Throttled DRAM at 20 GiB/s is the rate-limit strawman: it takes 3 s and still harms 7–11%. The controller's probe reads 1.96× its idle level beside "
    "Adam-80 and 1.13× beside the reader; the guard threshold is 1.3. A second limit found here: the CXL 'full' test used a constant capacity, which fails beside llama.cpp."))
SLIDES.append(S("The advisor's suggestion: manage DRAM and CXL as one pool with exclusive placement", "Part II · Advisor's suggestion", ["Proposal (not implemented)"], "f04_unified_pool",
    ["Our read path kept copies of CXL blocks in DRAM. The cache capacity stayed equal to CXL.",
     "Proposal (2026-10-09): one manager for both tiers. Each block lives in one tier. The manager does allocation, write placement, promotion, demotion, eviction and reclamation.",
     "Exclusive placement adds DRAM's capacity to the cache. It also needs migration, and every migration is a DRAM write."],
    "Decision: test the premises first. Build the full manager only if the data show that migration earns it.",
    "WORKLOG.md session 29 (discussion of 2026-10-09)",
    "The advisor's proposal came as a long document on unified DRAM/CXL management (promotion with invalidation of the CXL copy, demotion, reclamation). Our critical "
    "review checked the related work: NOMAD already keeps slow-tier copies (non-exclusive tiering); LMCache 0.5.5 already ships a DRAM-first DRAM + Device-DAX tier; TPP, "
    "Colloid, Memstrata, CAMP and AIM cover page-level tiering. The agreed plan (Direction 2): keep the write-interference motivation and the checkpoint evaluation, "
    "treat DRAM capacity and DRAM write bandwidth as two constrained resources, compare admission-only placement against migration, and do not build the full manager "
    "before the comparison. No part of the unified manager is implemented."))
SLIDES.append(S("Why unified management may matter: capacity and write bandwidth are two separate budgets", "Part II · Advisor's suggestion", ["Analysis", "Trace simulation"], "f21_two_resources",
    ["DRAM can add effective KV capacity: +3 to +15 points of reuse hits next to 512 GiB of CXL in the trace simulation (Part V).",
     "DRAM writes spend the bandwidth that DRAM readers are sensitive to (Part I).",
     "New writes, promotions and checkpoint copies all draw on that one bandwidth budget. Admitted and promoted blocks draw on capacity.",
     "Placement and migration must respect both budgets at the same time."],
    "We keep the write-interference motivation and add capacity as a second resource. Nothing on this slide is a built mechanism.",
    "Decisions of 2026-10-09 · 2026-10-09-kv-capacity-characterization",
    "This slide states the research judgement that came out of the discussion. Two things changed: DRAM is no longer only a faster copy of CXL data; it is scarce "
    "capacity that other blocks could use. And every DRAM write — a new block admitted to DRAM, a promotion, a checkpoint copy — spends the same interference budget, "
    "so a system that promotes aggressively can hurt neighbours as much as one that writes new data to DRAM. The experiments in Parts V–VII test these premises one by one."))
SLIDES.append(S("CXL writes spare a DRAM reader only from an unrelated core group", "Part III · Hardware characterization", ["Hardware measurement"], "f05_topology",
    ["8 threads writing CXL from the reader's own core group cut it 64%; from the paired group 15%; from any other group 0%.",
     "DRAM writes from the same places cost 72%, 20% and 10%.",
     "On the reader's own group the CXL rate stays at 44 GiB/s from 2 threads on, but the loss grows from 29% to 64% with 8 threads: stalled CXL requests crowd out the reader (the MIKU effect).",
     "A DRAM → CXL copy at the full 44 GiB/s from another group costs 1%."],
    "The premise holds under a placement condition. The system must put its copy threads on a group that runs no DRAM-sensitive tenant and is not paired with one.",
    "2026-10-09-cxl-topology-interference/topo.txt (2026-10-10; 5 runs × 3 s, medians)",
    "Motivation: MIKU (arXiv 2503.17864) reports that CXL traffic sharing a core complex with DDR traffic can cut DDR bandwidth sharply (Intel: up to 81–89%). On c28 the "
    "reader sits on CCD 4; CCD 5 is its paired group (they share a link to the IO die; the old NPS4 quadrant); CCD 0 stands for every other group. Every earlier campaign "
    "had the copy threads on CCDs 6–7 and the neighbours on CCDs 0–4, i.e. in the safe placement, so those results stand. Chain latency of the DRAM reader: unchanged from "
    "CCD 0 (133–137 ns) and CCD 5 for CXL kinds, 199–215 ns from CCD 4. GPU-to-CXL DMA uses no core and was not tested. The placement rule is proposed, not implemented."))
SLIDES.append(S("CXL readers lose 36–40% to CXL writes from anywhere; a dependent read takes 2.4× longer", "Part III · Hardware characterization", ["Hardware measurement"], "f06_cxl_reader",
    ["A 4-thread CXL reader (46 GiB/s alone) keeps 60–64% of its bandwidth while 8 threads write CXL, from any core group.",
     "One dependent read from CXL: 229 ns alone, 538 ns during a copy into CXL. The copy itself slows from 44 to 30 GiB/s.",
     "DRAM writes do not touch a CXL reader unless they share its core group.",
     "A GPU reads DRAM and CXL at the same 12.5 GiB/s on this machine; its PCIe link is the limit."],
    "CXL bandwidth is a managed resource too. A bulk writer and a latency-sensitive reader on the same cards need coordination.",
    "2026-10-09-cxl-topology-interference/topo.txt · 2026-10-07-read-cost/readcost.txt (medians of 3)",
    "Read cost without contention: a processor pays 1.67× per dependent read from CXL (226 vs 135 ns) and 1.8× per streaming thread; many threads get at most ~51 GiB/s "
    "from the two cards against ~280 GiB/s from DRAM. A checkpoint restored from CXL is still read 8–17× faster than from this SSD (2.6–2.9 GiB/s). The right panel is the "
    "overlap test of 2026-10-06: 4 streaming readers plus one chain reader while 8 threads copy 1 GiB pieces into DRAM or CXL. Reads and a copy overlap well on CXL for "
    "bandwidth (−6%) but not for single dependent reads (2.4×). This is the measured basis for the checkpoint + KV experiment in Part VII."))
SLIDES.append(S("Throttling DRAM does not protect neighbours, and persistent memory is not a substitute for CXL", "Part III · Hardware characterization", ["Trace-driven emulation", "Hardware measurement"], "f07_throttle_optane",
    ["DRAM writes capped at the CXL rate (48 GB/s) move the same bytes with the same bursts and still slow the Adam step 17.7% (uncapped: 17.8%). The CXL tier: 0.2%.",
     "Only a reader with spare bandwidth gains from the cap (6.2% → 3.8%). Busy neighbours react to the volume of DRAM writes, not to the peaks.",
     "On c35, non-temporal writes to Optane cost a same-socket DRAM reader 11.5% at 7.2 GiB/s; DRAM writes cost 8% at 17.8 GiB/s. Plain stores to Optane cut the reader from 39.9 to 1.9 GiB/s."],
    "The protection comes from placement on an independent path. Persistent memory shares the DRAM controllers; CXL does not.",
    "2026-10-11-throttled-dram-baseline · 2026-10-10-lmcache-kv-traffic/layer2 · 2026-10-06-optane-control (c35, run 2026-10-11)",
    "Left: host memory traffic emulation (Part IV method) with every KV store paced so that all stores together never exceed 48 GB/s; the capped DRAM tier then has the "
    "same 20 ms peaks, backlog and lateness as the CXL tier. The matched-throughput comparison shows that the CXL tier's protection is placement, not rate. Right: the "
    "Optane control on c35 (2 × Xeon Silver 4215, Optane DCPMM as a CPU-less NUMA node on socket 1); everything runs on socket 1 after a first attempt had measured the "
    "wrong socket. PM absorbs at most ~7 GiB/s of non-temporal writes per socket, so it cannot take a checkpoint or KV burst either. One of three repetitions of the "
    "plain-store cell read 19.1 GiB/s; it is reported as measured (median 1.9)."))
SLIDES.append(S("Real KV serving on the RTX 4060 Ti writes ~0.1 GB/s in short bursts and disturbs nobody", "Part IV · KV cache characterization", ["Real application"], "f08_real_kv",
    ["vLLM 0.31 + LMCache 0.5.5, Qwen2.5-1.5B, RTX 4060 Ti 8 GB (PCIe 4.0 ×8). Mooncake traces replayed open-loop.",
     "The card sustains ~0.08× of the trace (2.8–4.0 k prompt tokens/s). At 0.2× it saturates: TTFT grows without bound.",
     "Each KV store is a 0.058 GB burst at ~9 GB/s lasting ~10 ms, every ~0.28 s. Mean traffic: 0.09–0.14 GB/s.",
     "Neighbours beside saturated serving: reader −0.07%, PageRank −0.15%, Adam +0.07%, llama.cpp +0.1% (drift-corrected)."],
    "One small GPU cannot produce interfering KV traffic. The 1× / 4× / 8× trace rates need server-scale traffic, which we emulate.",
    "2026-10-10-lmcache-kv-traffic/layer1 (2026-10-10/11; NVML cumulative PCIe counters, 5 ms bins)",
    "Two operating points: normal load at 0.08× (trace minutes 0–3, run to the last answer, ~38 min) and a saturated stress test at 0.2× (10 min, then open requests "
    "cancelled). Real-time replay would need 25–38 k new prompt tokens per second; this card computes ~10 k with one output token, ~4.6 k with the trace's output lengths. "
    "Measurement notes: LMCache's own store figure (~9 GB/s per store) was confirmed once the sampler read NVML's cumulative counters every ~1.4 ms; 20 ms throughput "
    "windows cannot resolve 6 ms bursts. LMCache's retrieve figure is not a link rate; retrieves are 1–3% of the KV volume here. llama.cpp's raw +17% was its own "
    "context-growth drift, corrected with a control run (method noise ±5)."))
SLIDES.append(S("Host memory traffic emulation reproduces server-scale KV traffic from the traces", "Part IV · KV cache characterization", ["Trace-driven emulation"], "f22_emulation_method",
    ["Trace-driven: request arrivals and block hashes from the Mooncake traces at 1×, 4× and 8× speed; Llama-3.1-8B (64 MiB) and 70B (160 MiB) blocks.",
     "Stores and loads are CPU copies sized and timed from the real runs: 9.5 GB/s per transfer, 2048-token pieces, 7,300 tokens/s per request.",
     "Recorded: offered vs achieved bandwidth, 20 ms peaks, backlog and lateness, hit share, neighbour slowdown against its own quiet window.",
     "Limit: CPU non-temporal stores are not GPU DMA, and the two worker core groups cap DRAM bursts at ~150 GB/s per 20 ms."],
    "The emulation gives the traffic shape of a server, not a multi-GPU system. 70B 4× and 8× stand for several servers' aggregate traffic.",
    "benchmarks/memory/kvemu.c, kvemu2.c, run_exp2b.py · 2026-10-10-lmcache-kv-traffic/layer2",
    "Plausibility of the rates: one 8×H100 server at full prefill produces about 24–37 GiB/s of 8B KV and 7–10 GiB/s of 70B KV (estimate from published H100 throughput, "
    "not measured). 8B 1–8× therefore corresponds to 0.2–1.7 servers; 70B 4× and 8× to 5–15 servers — a KV-pool-node stress point, labelled as such everywhere. The "
    "online emulator (kvemu2) looks blocks up at arrival and counts a block as a hit only after its store has completed, so a backlog never produces false hits; the tier is "
    "chosen when the store starts, as LMCache allocates at offload time. Every copy is reported to the controller's ledger per 2 MiB piece."))
SLIDES.append(S("Server-scale KV writes into DRAM slow neighbours up to 63%; into CXL, at most 2%", "Part IV · KV cache characterization", ["Trace-driven emulation"], "f10_emulation_neighbors",
    ["KV tier in DRAM: neighbours lose 1–4% at 8B 1× (5 GB/s mean) and 16–18% at 8B 8× (39 GB/s). At 70B 8× the Adam step loses 63% (p99 +75%).",
     "KV tier in CXL: ≤ 2% for every neighbour and load; p99 tails ≤ +4%.",
     "The harm grows with the offered rate and its 20 ms bursts (offered peaks reach 300 GB/s)."],
    "Server-scale KV writes are a real DRAM aggressor. CXL placement removes the harm.",
    "2026-10-10-lmcache-kv-traffic/layer2/summary.csv (one run per cell, 2026-10-10/11)",
    "Neighbours: the 8-thread DRAM reader, PageRank on 80 threads and the CPU Adam step on 80 threads, each on cpus 0–79 with its own 60 s window before the traffic as "
    "baseline. llama.cpp is left out of the figure: its token rate drifts with the context, and the corrected values (±5 method noise) add nothing. Because the emulator "
    "caps DRAM bursts at ~150 GB/s while the trace offers up to 300, the DRAM-tier harm is understated at the top end. The conversation trace is used throughout; the tool "
    "agent trace is used in Part VII."))
SLIDES.append(S("CXL protects readers but takes at most ~46 GB/s; heavier loads fall behind", "Part IV · KV cache characterization", ["Trace-driven emulation"], "f09_emulation_rate",
    ["Both tiers keep up to 8B 8× on average, but CXL queues the bursts: 30 GB of backlog, stores 0.6 s late.",
     "70B 4× offers 53 GB/s. CXL achieves 47 and falls 1.4 TB behind (28 s late). 70B 8× offers 105 GB/s: 14 TB behind.",
     "DRAM keeps up at every load, at the cost of the neighbours on the previous slide."],
    "CXL-first alone cannot carry heavy loads. The missing bandwidth must come from DRAM, under control of the neighbours' SLO.",
    "2026-10-10-lmcache-kv-traffic/layer2/summary.csv",
    "Offered = the bytes the trace schedule demands if every transfer starts on time; achieved = stores written; the backlog is offered minus done, accumulated. The "
    "emulator keeps writing until every planned byte is done, so the overloaded runs last up to 10 minutes longer than planned. The two CXL cards of dax0.0 take ~44–47 "
    "GB/s of non-temporal writes from one core group; this is the ceiling every later experiment works against. 70B 4× is the configuration used in Parts V and VI as "
    "the 'above the ceiling' case."))
SLIDES.append(S("The host KV cache is capacity-bound; DRAM holding other blocks adds +3 to +15 points of hits", "Part V · Capacity and memory management", ["Trace simulation", "Estimate"], "f11_kv_capacity",
    ["One hour of the chat or agent trace creates ~11 TiB of distinct 8B KV. c28 has 512 GiB of CXL.",
     "LRU, 8B: 512 GiB of CXL serves 49 / 80 / 59% of reuses (conversation / tool agent / synthetic). +256 GiB of DRAM holding other blocks: +14 / +6 / +15 points. 1 TiB: 72 / 90 / 83%.",
     "70B: 19 / 65 / 31% at 512 GiB. Copies of CXL blocks in DRAM add nothing to these shares.",
     "Assumptions: no GPU prefix cache in front, LRU, one host per trace, bf16 KV sizes from the model configurations."],
    "For GPU-read KV, DRAM is worth more as extra capacity than as a faster copy: our GPU loads DRAM and CXL at the same speed.",
    "2026-10-09-kv-capacity-characterization/kv-capacity.csv (exact LRU stack distances)",
    "Three kinds of numbers are kept apart: exact trace counts; the model conversion (128 KiB per token for Llama-3.1-8B, 320 KiB for 70B, bf16); and the LRU simulation. "
    "A GPU prefix cache of ~40 GiB would absorb 12 / 61 / 9% of the 8B reuses, which the simulation ignores. What a hit is worth is an estimate: recomputing a 512-token "
    "8B block costs ~15–25 ms on one H100 against ~1.3 ms to load it at 50 GB/s; the DRAM-versus-CXL load difference is ~10% on an H100 (LMCache's published numbers) and "
    "zero on our GPU. The agent trace concentrates two thirds of its reuses on 0.5% of the blocks, so a small cache already serves most of them; chat needs capacity."))
SLIDES.append(S("Real LMCache: DRAM, DRAM-first hybrid and CXL-only L1 serve the same hits and TTFT on this GPU", "Part V · Capacity and memory management", ["Real application"], "f12_real_lmcache",
    ["Same 40 GiB L1 as pinned DRAM, LMCache's hybrid (20 GiB DRAM + 20 GiB Device-DAX) and pure CXL; 556 requests of the conversation trace at 0.08×.",
     "Hit share 0.079–0.080; TTFT p50 4.2–4.3 s, p99 34–35 s. Per request, TTFT differs by ≤ 0.04 s (noise ±0.15 s).",
     "LMCache's 80% eviction watermark leaves 8 GiB unused. In the hybrid that slack sits entirely in the CXL part: DRAM 18.2 / CXL 10.8 GiB used.",
     "LMCache's hybrid is hard-wired DRAM-first. A CXL-first order needs a code change, so CXL-first and borrowing were emulated."],
    "On this GPU the tier does not change serving. Capacity effects need the larger emulated cache.",
    "2026-10-11-capacity-matched-kv/real/summary.txt (multi-process LMCache, 2026-10-12)",
    "LMCache 0.5.5 multi-process mode (lmcache server + LMCacheMPConnector), chunk 256 tokens, LRU eviction, watermark 0.8. The hybrid is built with the Device-DAX L2 "
    "adapter on the same device, which LMCache turns into the L1 overflow; the allocator tries the pinned-DRAM pool first and uses DAX arenas as overflow, and the global "
    "LRU does not know the tiers. The per-pool occupancy comes from the server's allocator log (two summaries every 5 s). LMCache's /status reports no per-tier "
    "counters, so the per-tier write split and its effect on neighbours come from the emulated LMCache-like policy on the next slide. One run per configuration."))
SLIDES.append(S("At equal capacity, static admission beats our migration policies; CXL-first alone idles a fifth of the hits", "Part V · Capacity and memory management", ["Trace-driven emulation"], "f13_admission_migration",
    ["200 GiB of effective capacity for every policy; same trace, warm-up and eviction.",
     "Policies that fill both tiers reach hit share 0.190. CXL-first leaves 64 GiB of DRAM idle: 0.150. A global LRU does not help.",
     "The controller lends nothing next to Adam. Calm-time migration recovers half (0.172) for ~0.2 GB/s of DRAM writes — nothing next to Adam.",
     "A static 32% split reaches 0.190 at +2.4% median / +5.5% p99 Adam slowdown, inside the 7% SLO."],
    "Migration is cheap in DRAM writes but earns no unified manager yet. A plain admission split did better.",
    "2026-10-11-capacity-matched-kv/emulation/summary.csv (81 runs, 2026-10-11/12)",
    "Policies: all DRAM; LMCache-like (DRAM-first, global LRU, 0.8 watermark); static split (DRAM's 32% share of the slots by hash); CXL-first (per-tier LRU, DRAM "
    "stays empty); the existing controller's loans (borrowtier); the same with a global LRU (borrowglob); the same plus migration of blocks hit in CXL to DRAM while the "
    "controller reports DRAM calm (borrowmig); all CXL. Finding on the controller: its default 60 s loan block stopped every loan in bursty KV traffic; the runs use a 1 s "
    "block. Next to the 8-thread reader the loans do work (70B 4×: 9.7 GB/s lent, backlog 39 GB instead of 714). The overloaded runs' hit shares are inflated by the "
    "backlog (waiting stores do not evict) and are not compared. This is the slide that answers 'does migration earn a unified manager' — so far, no."))
SLIDES.append(S("The current controller reads a DRAM-heavy neighbour as 'no headroom' and lends nothing", "Part VI · Budget-gated admission", ["Trace-driven emulation"], "f14_controller_limit",
    ["70B 4× offers 52 GB/s and CXL takes 46. The deficit is 6 GB/s.",
     "The Adam step alone raises the DRAM latency probe to 275 ns (idle: 127 ns). The guard treats that as 'busy' and lends 0 GB/s. The backlog grows past 700 GB.",
     "Static splits show what Adam tolerates: 6 GB/s at +6.1% p99, 10 GB/s at +8.2%, 16 GB/s at +12.7%."],
    "A small, steady DRAM write budget fits the 7% SLO and bounds the backlog. The probe-based guard cannot find it.",
    "2026-10-11-capacity-matched-kv/emulation (opt-70b-4x-split24 / split40 / split, cxlfirst; daemon logs)",
    "The controller (cxlpathd) uses a dependent-read probe on a core of the neighbour's group as its signal and a guard of 1.3× the idle latency. The Adam step keeps "
    "the probe at 2.2× idle in every epoch, so no epoch qualifies for a loan although the SLO leaves room for about 6 GB/s of steady DRAM writes. The static splits write "
    "an evenly spread share of new blocks to DRAM; 6 GB/s equals the mean deficit, so the backlog stays bounded (176 GB peak, draining between bursts) but bursts still "
    "wait up to 3 s. Keeping stores within half a second needs ~16 GB/s, which breaks the p99 target. The guard is unchanged in all later experiments by the user's "
    "decision; the budget policy on the next slides is the alternative under test."))
SLIDES.append(S("Budget-gated admission: a token bucket decides, block by block, whether a new block may use DRAM", "Part VI · Budget-gated admission", ["Emulated policy", "Proposal (not implemented)"], "f15_budget_design",
    ["Credit refills at the budget B GB/s and is capped at d blocks (d = 1 by default). A new block goes to DRAM when a whole block of credit exists; otherwise to CXL.",
     "Unused credit is lost, so DRAM writes stay smooth. Same capacity (64 + 136 GiB), per-tier LRU and warm-up as the static split.",
     "B is calibrated on a separate trace segment against the SLO (p99 slowdown ≤ 7%). An oracle that switches B with the neighbour gives an upper bound."],
    "The simplest form of a shared DRAM write budget. Online estimation of B is not built.",
    "benchmarks/memory/kvemu2.c (policy budget, KV2_BUCKET_BLOCKS), 2026-10-12/13",
    "The policy is implemented in the emulator only. The selection of B uses a fixed rule applied to the calibration runs before any evaluation run: the feasible values "
    "are those for which the value and every smaller value meet the SLO; the chosen value is the feasible one with the highest hit share (the largest feasible one when "
    "the family is overloaded). A first version of the rule took the largest feasible value, which picked a 48% split with a lower hit share than 32% next to the reader; "
    "it was corrected before any affected run, and both versions are kept in the raw data. The bucket depth d is the subject of the sensitivity slide."))
SLIDES.append(S("Calibration: smoother DRAM writes buy SLO room, but a one-block bucket caps DRAM's share at ~25%", "Part VI · Budget-gated admission", ["Trace-driven emulation"], "f16_bga_calibration",
    ["Sweep next to Adam on a separate trace segment: split 8–48%, budget 2–32 GB/s, one run per point.",
     "Same mean DRAM rate, lower p99 for the budget (8B 8×: +6.8% vs +7.0% at ~9 GB/s); 20 ms peaks 20 vs 40–50 GB/s.",
     "A chunk's four blocks fall due together: one takes the bucket, three go to CXL. DRAM's share of writes stays ~25%.",
     "Hit share peaks when DRAM's share of new blocks equals its 32% share of capacity (32%: 0.204; 48%: 0.167)."],
    "Smoothness buys SLO room; the one-block bucket gives part of it back by under-using DRAM's capacity.",
    "2026-10-12-budget-gated-admission/calibration/summary.csv (72 runs, trace segment from 2040 s)",
    "Both neighbours were calibrated; the slide shows the Adam step (the DRAM-heavy case). Next to the 8-thread reader both families pass everywhere up to 32% / 32 GB/s "
    "with 0.6–4.1% mean bandwidth loss. The reader's p99 became measurable only after its bandwidth counter was changed to 64 MiB steps (the old 1 GiB counting "
    "quantized every 100 ms sample to ~10% steps); a 600 s quiet run showed both neighbours' p99 stable to ≤ 1.3% across 60 s windows, so the per-run 60 s quiet "
    "window is a valid baseline. 70B 4× is overloaded in every setting inside the SLO (backlog ≥ 100 GB), so its hit shares are not used for selection; the chosen "
    "settings there are budget 12 GB/s and split 16%."))
SLIDES.append(S("Evaluation under the same 7% SLO: budget-gated admission ties the best safe split; both beat the controller", "Part VI · Budget-gated admission", ["Trace-driven emulation"], "f17_bga_evaluation",
    ["Evaluation segment; settings fixed in advance by the calibration rule.",
     "Next to Adam: 8B 4× split 0.190 at +5.8%, budget 0.185 at +3.7%. 8B 8× budget 0.180 at +7.1% [6.6..7.6] — on the SLO — vs split 0.164 at +4.6%; held to 7%, a 24 GB/s budget ties the split. 70B 4×: a tie.",
     "The controller lends nothing next to Adam (0.157–0.161). Migration matches the split next to the reader at 0.2–1.9 GB/s of DRAM writes but breaks the SLO at 70B 4×.",
     (f"{REPS} runs per cell: hit shares reproduce to ±0.001, the p99 to ±0.5 points." if REPS > 1 else "One run per cell; two more independent repeats are running today.")],
    "Inside the same SLO a bandwidth budget ties the best static split: smoother writes, no extra hits. Both beat the current controller beside a DRAM-heavy neighbour.",
    "2026-10-12-budget-gated-admission/evaluation/summary.csv (2026-10-12/13)",
    "The evaluation uses the windows of Part V (8B 4× and 70B 4×: trace seconds 600–1320 at 4×; 8B 8×: 600–2040 at 8×). The calibration and evaluation segments do "
    "not overlap. Each configuration ran with the split at its chosen share, the budget at its chosen value, the controller, the controller plus migration, and CXL-first. "
    "Next to the reader the controller's loans arrive in bursts (20 ms peaks of 58–72 GB/s) and migration pushes the reader past the SLO at 70B 4×, while the split and "
    "the budget move three times the DRAM rate at +1.3 to +4.0%. The budget's per-minute p99 at 8B 8× next to Adam touched +7.1% in one minute of rep 1; the repeats "
    "show whether that is noise."))
if HAVE_DEPTH:
    SLIDES.append(S("A deeper bucket uses the budget fully, but on the evaluation segment it earns no extra hits", "Part VI · Budget-gated admission", ["Trace-driven emulation"], "f18_bga_depth",
        ["Sweep next to Adam, calibration segment: depth 1, 2, 4, 8 × budget 8, 16, 32 GB/s. At 8 GB/s the utilization rises from 0.31 to 0.91 and the admitted rate from 2.5 to 7.3 GB/s; 20 ms peaks grow from 20 to 31–52 GB/s.",
         "The hit share follows the admitted share, not the depth: it peaks when DRAM gets ~32% of the new blocks (0.201 at depth 4 / 16 GB/s; the 32% split: 0.204) and falls beyond. Adam's p99 follows the mean DRAM rate.",
         "Evaluation of depth 4 / 16 GB/s (3 runs): 0.187 at +5.3% — +0.002 over depth 1 for +1.6 points of p99, below the split's 0.190. At 8B 8× no deeper bucket beats depth 1 inside the SLO."],
        "With the right depth the budget policy is a smoother way to express the same static split, not a way to beat it.",
        "2026-10-12-budget-gated-admission/depth (18 runs) and depth-eval (3 runs), 2026-10-13",
        "Depth d lets the bucket bank d blocks of credit, so a chunk of four blocks can be admitted whole. Utilization = DRAM writes / budget; at depth 1 it is 0.15–0.31 "
        "because the three remaining blocks of each chunk go to CXL. The selection rule picked depth 4 / 16 GB/s for 8B 4× (0.201 on the calibration segment) and kept "
        "depth 1 / 32 GB/s for 8B 8×; the calibration optimum did not transfer to the evaluation segment (0.187), which has a different reuse structure. The point of "
        "depth for a future controller: a budget in GB/s that is actually used, so an online estimate of the safe budget maps directly to the admitted DRAM rate — "
        "depth 8 at 8 GB/s runs at 97% utilization and equals the 16% split (0.164 at +4.9%) with a margin to the SLO. 20 ms peaks: depth 1 ~20 GB/s, depth 4 27–36, "
        "depth 8 31–52, the split 40–50; Adam's p99 tracks the mean DRAM rate more than the peaks."))
else:
    pending_fig("f18_pending", "Bucket depth sensitivity — PENDING",
                ["Sweep next to the Adam step, 8B 4× and 8B 8×, calibration segment:", "   depth 1, 2, 4, 8 blocks  ×  budget 8, 16, 32 GB/s  (depth 1 = existing calibration runs)",
                 "Reported per run: hit share, DRAM admission share and budget utilization,", "   20 ms peak DRAM bandwidth, Adam p99 slowdown",
                 "Then: the best (depth, budget) pair inside the SLO × 3 independent runs", "   on the evaluation segment, comparable with the previous slide",
                 "Status: queued after the main chain on 2026-10-13; no result yet"])
    SLIDES.append(S("Bucket depth sensitivity: does a deeper bucket raise DRAM's useful share without breaking the SLO?", "Part VI · Budget-gated admission", ["Pending", "Trace-driven emulation"], "f18_pending",
        ["A deeper bucket admits more of a burst to DRAM: higher DRAM share and hit share, higher 20 ms peaks.",
         "Sweep: depth 1, 2, 4, 8 blocks × budget 8, 16, 32 GB/s next to the Adam step at 8B 4× and 8B 8×, on the calibration segment.",
         "Reported: hit share, DRAM admission share and budget utilization, 20 ms peak bandwidth, Adam p99 slowdown.",
         "Then the best safe (depth, budget) pair × 3 independent runs on the evaluation segment."],
        "Pending: the runs are queued behind the main chain (2026-10-13). No result is shown or estimated here.",
        "benchmarks/memory/run_bga_depth.sh (queued 2026-10-13 10:24)",
        "The one-block bucket's cap on DRAM's write share (~25%) is a property of the bucket depth, not of the budget. Depth d lets the bucket bank d blocks of credit, so "
        "a chunk of four blocks can be admitted whole at d = 4. The cost is in the 20 ms peaks, which is what the Adam step's p99 reacts to. The sweep answers whether "
        "a depth exists that reaches the split's hit share inside the SLO. This slide is replaced by the data slide when the runs finish."))
if HAVE_VARY:
    SLIDES.append(S("Adapting the budget to the neighbour drains the backlog; 70B 4× next to Adam stays marginal", "Part VI · Budget-gated admission", ["Trace-driven emulation"], "f19_bga_varying",
        ["Adam runs 30 s, pauses 30 s. At 70B 4× an oracle budget (12 GB/s while Adam runs, 32 while it pauses) cuts the peak backlog from 137–145 GB to 60 GB at the same Adam p99 (+6.8%). The controller lends only in the pauses: 201 GB.",
     "At 8B 8× the oracle equals the fixed budget (32 GB/s is already the largest swept); its +7.6% confirms 32 GB/s is above the SLO next to Adam.",
     "Long run, 12 min of 70B 4× next to Adam: stores reach 51.5 GB/s against 54 offered; the backlog swings between 38 and 280 GB; Adam's p99 sits at the SLO (budget +6.9%, split +7.3%). CXL-first grows to 1.2 TB."],
        "Dynamic adaptation buys backlog, not hits. A steady 70B 4× load next to Adam exceeds CXL plus the safe DRAM budget: capacity is insufficient, not merely tight.",
        "2026-10-12-budget-gated-admission/varying (24 runs, 2 per cell) and longrun (3 runs), 2026-10-13",
        "The neighbour is paused with SIGSTOP and resumed with SIGCONT every 30 s; Adam's p99 is computed over steps inside the on phases only. The oracle switches the "
        "budget file at each phase change; it is an upper bound for any online estimator, not a mechanism. At 70B 4× the oracle's mean DRAM rate rises from 8.5 to 12.2 "
        "GB/s and the peak backlog falls to 60 GB (two runs: 58 and 61); hit shares are unchanged because the configuration is overloaded. The controller does react to "
        "the pauses (6.1 GB/s lent on average) but lends nothing while Adam runs, so its backlog (201 GB) stays above the fixed policies'. Long run: offered 54.0 GB/s "
        "mean with minutes up to 58; achieved DRAM 8.1–8.7 plus CXL 42.8–43.4 = 51.5 GB/s; per-minute backlog 38–280 GB; the run drains in its last minute because the "
        "trace segment ends. Any sustained offered rate above ~52 GB/s would grow the backlog without bound; this is reported as insufficient capacity, not as stable."))
else:
    pending_fig("f19_pending", "Dynamic workload changes and long runs — PENDING",
                ["Varying load: Adam step 30 s on / 30 s off (SIGSTOP), 8B 8× and 70B 4×, 2 runs per cell:", "   static split and budget at their Adam-safe settings · ORACLE budget (switches with Adam)",
                 "   · existing controller · controller + migration · CXL-first", "Long run: 70B 4× next to Adam, 720 s of traffic (budget 12 GB/s, split 16%, CXL-first):",
                 "   per-minute backlog, achieved throughput and Adam p99: is the backlog bounded?", "Status: running since 2026-10-13 10:22 (49 evaluation repeats first); no result yet"])
    SLIDES.append(S("Dynamic workload changes and long runs: does dynamic bandwidth adaptation beat a fixed split?", "Part VI · Budget-gated admission", ["Pending", "Trace-driven emulation"], "f19_pending",
        ["Varying load: the Adam step runs 30 s and pauses 30 s. Fixed static split, fixed budget, an oracle budget that switches with Adam (an upper bound, not a mechanism), the controller, migration and CXL-first; 2 runs each.",
         "Long run: 70B 4× next to Adam for 720 s. The offered 52 GB/s is close to CXL (46) plus the safe DRAM budget (~6). Per-minute backlog, achieved throughput and Adam p99 show whether the backlog really stays bounded.",
         "If the backlog keeps growing, the result is reported as 'capacity insufficient', not as stable."],
        "Pending: running since 2026-10-13 10:22. No result is shown or estimated here.",
        "benchmarks/memory/run_bga_chain.sh (varying/, longrun/)",
        "Why the oracle: it shows the most a dynamic budget could gain when it knows the neighbour's state perfectly. A real mechanism would need an online estimate of "
        "the safe budget, which the current probe-based guard cannot provide beside DRAM-heavy neighbours. The long run matters because 6 GB/s of safe DRAM bandwidth "
        "equals the mean deficit at 70B 4×: any drift in the offered rate makes the backlog grow without bound. This slide is replaced by the data slide when the runs finish."))
SLIDES.append(S("Checkpoint writes and KV reads on the same CXL cards: KV priority protects loads, not the shared write pipe", "Part VII · Mixed applications", ["Real application", "Trace-driven emulation"], "f20_ckpt_kv",
    ["Real run: 96 GiB checkpoints every 8 s into the cards that hold the KV cache. KV loads and TTFT do not change (the GPU link is the limit). A CPU reader of CXL: 226 → 533 ns inside the bursts.",
     "Emulated 8B 4×: uncoordinated checkpoints add 44% to the median request delay. KV priority removes it (+14% checkpoint time). A 20 GB/s rate limit does not.",
     "Emulated 8B 8×: KV stores already use ~36 of ~46 GB/s. Any checkpoint pushes the median delay from 76 ms to ~8 s in every mode — confirmed from the raw load queues."],
    "Two writers on one CXL pipe need admission across writers: lend DRAM to one, or pace the checkpoint below the residual CXL capacity. Not built.",
    "2026-10-12-checkpoint-kv-mixed (real: 4 runs, tool agent trace at 0.08×; emulation: kvemu3, 8 runs)",
    "Real part: the KV L1 lives entirely in CXL (dax1.0); ckpt_cxl copies 96 GiB from DRAM into dax0.0 with 8 threads every 8 s; modes: uncoordinated, rate-limited to "
    "20 GB/s, and KV priority (each 2 MiB piece waits while NVML shows host-to-GPU traffic above 1 GB/s). TTFT is compared request by request against the run without a "
    "checkpoint: +0.02 s overall, +0.18 s for requests overlapping a burst, noise ±0.15 s. The CPU chain reader is the latency-sensitive victim; the rate limit lowers "
    "its latency to 271 ns but keeps CXL busy 64% of the time instead of 27%. Emulated part: kvemu3 adds the checkpoint writer and a per-load queue to the online emulator; "
    "the 8B 8× queue wait goes from 53 ms to ~8 s. Limits: one small GPU, CPU copies, one run per cell."))
SLIDES.append(dict(kind="cards", title="What we have learned", part="Part VIII · Current conclusions", tags=["Summary"], cards=[
    ("DRAM bulk writes can slow neighbours severely", "A 4-thread reader keeps 8% under saturating writers; server-scale KV writes cost neighbours up to 63%. (Slides 2, 12)"),
    ("CXL writes remove the harm under a placement condition", "≤ 2% for every neighbour when the writer's threads sit on an unrelated core group; the paired or own group gives no protection. (Slides 7, 12)"),
    ("CXL write bandwidth limits high-rate workloads", "~46 GB/s on the two cards; 70B 4× falls 1.4 TB behind; two writers on one pipe push KV load queueing to ~8 s. (Slides 13, 23)"),
    ("DRAM provides useful extra KV capacity", "+3 to +15 points of reuse hits in the trace simulation; idle DRAM costs a fifth of the hits in emulation. (Slides 14, 16)"),
    ("Static admission can outperform current migration policies", "A 32% split beat every controller policy inside the SLO; a bandwidth budget ties it at any bucket depth; only an adaptive budget adds value, by halving the 70B backlog. (Slides 16, 20–22)"),
    ("DRAM budget estimation and cross-writer coordination remain open", "The guard lends nothing beside DRAM-heavy neighbours; KV priority cannot share the write pipe. (Slides 17, 23)")],
    notes="Each card names the slide that carries its evidence. Items 1–3 are hardware measurements and emulation; item 4 is a trace simulation plus emulation; item 5 "
          "is emulation with calibration-chosen settings (repeats in progress); item 6 names the two open problems that the next phase must address."))
SLIDES.append(S("Proposed direction: interference-aware capacity and bandwidth management for DRAM/CXL memory", "Part VIII · Current conclusions", ["Proposal (not implemented)"], "f23_direction",
    ["Keeps the original thesis: bulk writes go to CXL by default; DRAM is granted on evidence.",
     "Adds the advisor's capacity view: each block lives in one tier; DRAM capacity is a second budget.",
     "Implemented so far, as emulated policies: budget-gated admission, per-tier capacity management, a minimal migration rule; and the real LMCache integration for DRAM, hybrid and CXL tiers.",
     "Proposals only: online estimation of the safe DRAM budget; one budget shared across KV admission, promotion and checkpoint writers."],
    "A minimal manager is justified only where the data show a gain: admission with a budget first, migration where DRAM is calm.",
    "This deck; docs/experiments/INDEX.md",
    "This slide connects the original paper idea with the advisor's suggestion. The write-interference motivation and the CXL-first default survive every experiment. "
    "The unified-pool view survives in reduced form: capacity is a real resource, but the data favour admission with a bandwidth budget over migration, and the "
    "controller's hardest part is estimating the safe budget, not moving data. Colours in the figure: green = emulated and measured, orange = minimal policy, red = "
    "proposal only."))
SLIDES.append(dict(kind="cards", title="Next steps and open questions", part="Part VIII · Current conclusions", tags=["Proposal (not implemented)"], cards=[
    ("Can dynamic admission beat the best static split?", "For a fixed budget: no, it ties the split at any depth (slides 20–21). It pays only by adapting to the neighbour (slide 22), which needs an online estimate of the safe budget."),
    ("Can we estimate the safe DRAM bandwidth online?", "The probe-based guard fails beside DRAM-heavy neighbours. Candidate: a write-rate probe calibrated against the measured SLO curve."),
    ("When are promotion or demotion necessary?", "So far only next to calm DRAM, and never better than admission. Decide after the repeats; keep migration minimal."),
    ("How should checkpoint writes and KV reads share CXL bandwidth?", "Cross-writer admission on one budget; pace the checkpoint below the residual CXL capacity; protect latency-sensitive CXL readers."),
    ("What minimal unified manager do the data justify?", "Admission with a budget, per-tier capacity management, calm-time migration. Nothing more until it is measured."),
    ("Priorities for the next phase", "1. Online estimation of the safe DRAM write budget (the current guard finds none beside Adam). 2. Cross-writer admission prototype for checkpoint + KV. 3. A selection rule with an SLO margin. 4. CXL-first patch for real LMCache.")],
    notes="Priorities follow the evidence: the first item is already running; items 2 and 3 address the two open problems; item 4 brings the real system back into the "
          "loop once the emulated policies have shown which one to build. No controller or unified-manager change is started without the measured gain."))

# ------------------------------------------------------------------ layout helpers
def fig_size(name, maxw, maxh):
    im = Image.open(os.path.join(FIG, name + ".png")); r = im.width / im.height; w = maxw; h = w / r
    if h > maxh: h = maxh; w = h * r
    return w, h
def tsize(t): return 26 if len(t) < 70 else 24 if len(t) < 90 else 22
def layout(sl):
    """positions in inches for a figure slide"""
    L = dict(title=(0.5, 0.28, 12.33, 1.0), part=(0.5, 1.22, 7.5, 0.3))
    fw, fh = fig_size(sl["fig"], 8.3, 5.05); L["fig"] = (0.5, 1.62, fw, fh)
    under = fh <= 4.0
    L["bullets"] = (9.1, 1.62, 3.73, 5.2 if under else 3.75)
    L["take"] = (0.5, 1.62 + fh + 0.22, 8.3, 1.0) if under else (9.1, 5.55, 3.73, 1.3)
    L["source"] = (0.5, 6.98, 11.3, 0.42); L["bsize"] = 13 if under else 12
    return L

# ------------------------------------------------------------------ PPTX
def rgb(h): return RGBColor.from_string(h)
def add_text(slide, x, y, w, h, text, size, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT, italic=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.03); tf.margin_top = tf.margin_bottom = Inches(0.02); tf.vertical_anchor = anchor
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        r = p.add_run(); r.text = ln; r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic; r.font.name = font; r.font.color.rgb = rgb(color)
    return tb
def add_bullets(slide, x, y, w, h, items, size):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.03); tf.margin_top = Inches(0.02)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        pPr = p._p.get_or_add_pPr(); pPr.set("marL", "228600"); pPr.set("indent", "-228600")
        bu = etree.SubElement(pPr, qn("a:buChar")); bu.set("char", "•")
        p.space_after = Pt(7); p.line_spacing = 1.08
        r = p.add_run(); r.text = it; r.font.size = Pt(size); r.font.name = FONT; r.font.color.rgb = rgb(INK)
    return tb
def add_box(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h)); s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    if line: s.line.color.rgb = rgb(line); s.line.width = Pt(0.75)
    else: s.line.fill.background()
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: s.adjustments[0] = 0.12
    return s
def add_chips(slide, tags, right=12.83, y=1.2):
    x = right
    for t in reversed(tags):
        w = 0.1 + 0.075 * len(t); x -= w + 0.12
        add_box(slide, x, y, w, 0.3, TAGS.get(t, "F3F3F3"))
        add_text(slide, x, y, w, 0.3, t, 9.5, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
def build_pptx(path):
    prs = Presentation(); prs.slide_width = Inches(W); prs.slide_height = Inches(H); blank = prs.slide_layouts[6]
    for n, sl in enumerate(SLIDES, 1):
        s = prs.slides.add_slide(blank)
        if sl.get("kind") == "title":
            add_box(s, 0, 0, W, H, NAVY, shape=MSO_SHAPE.RECTANGLE)
            add_text(s, 0.9, 1.9, 11.5, 1.8, sl["title"], 36, bold=True, color="FFFFFF")
            add_text(s, 0.9, 3.75, 11.5, 0.7, sl["subtitle"], 22, color="CADCFC")
            add_text(s, 0.9, 4.6, 11.5, 0.5, sl["meta"], 14, color="DDE6F0")
            add_text(s, 0.9, 6.3, 11.5, 0.4, "Evidence tag on each slide:  Hardware measurement · Real application · Trace-driven emulation · Trace simulation · Estimate · Proposal (not implemented)", 11, color="AFC0D6")
        elif sl.get("kind") == "cards":
            add_text(s, 0.5, 0.28, 12.33, 1.0, sl["title"], tsize(sl["title"]), bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, 0.5, 1.22, 7.5, 0.3, sl["part"], 11, color=MUTED); add_chips(s, sl["tags"])
            for i, (hd, tx) in enumerate(sl["cards"]):
                cx, cy = 0.5 + (i % 3) * 4.19, 1.7 + (i // 3) * 2.65
                add_box(s, cx, cy, 3.95, 2.4, TINT); add_box(s, cx + 0.2, cy + 0.2, 0.42, 0.42, NAVY, shape=MSO_SHAPE.OVAL)
                add_text(s, cx + 0.2, cy + 0.2, 0.42, 0.42, str(i + 1), 13, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
                add_text(s, cx + 0.75, cy + 0.15, 3.05, 0.9, hd, 13.5, bold=True, color=NAVY)
                add_text(s, cx + 0.2, cy + 1.05, 3.6, 1.3, tx, 11.5, color=INK)
        else:
            L = layout(sl)
            add_text(s, *L["title"], sl["title"], tsize(sl["title"]), bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, *L["part"], sl["part"], 11, color=MUTED); add_chips(s, sl["tags"])
            x, y, w, h = L["fig"]; s.shapes.add_picture(os.path.join(FIG, sl["fig"] + ".png"), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
            add_bullets(s, *L["bullets"], sl["bullets"], L["bsize"])
            x, y, w, h = L["take"]; add_box(s, x, y, w, h, TINT)
            add_text(s, x + 0.12, y + 0.06, w - 0.24, h - 0.12, [("Takeaway: " + sl["takeaway"]) if sl["takeaway"] else ""], 12.5, bold=False, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, *L["source"], f"Data: {sl['source']}  ·  figure {sl['fig']}", 9.5, color=MUTED)
        add_text(s, 12.3, 7.05, 0.6, 0.3, str(n), 9.5, color=MUTED if sl.get("kind") != "title" else "AFC0D6", align=PP_ALIGN.RIGHT)
        s.notes_slide.notes_text_frame.text = sl.get("notes", "")
    prs.save(path); print("wrote", path, len(SLIDES), "slides")

# ------------------------------------------------------------------ preview (matplotlib) + overflow check
def wrap(text, width_in, size, bold=False):
    cpl = max(10, int(width_in * 72 / (size * (0.62 if bold else 0.55))))        # DejaVu Sans is wider than Calibri: conservative
    return [l for t in (text if isinstance(text, list) else [text]) for l in (textwrap.wrap(t, cpl) or [""])]
def ptext(ax, x, y, w, h, text, size, bold=False, color="#1F2D3D", va="top", ha="left", bullets=False, warn=""):
    lines = []
    if bullets:
        for it in text:
            ls = wrap(it, w - 0.25, size); lines += ["• " + ls[0]] + ["   " + l for l in ls[1:]] + [""]
    else: lines = wrap(text, w, size, bold)
    lh = size * 1.25 / 72; need = lh * len([l for l in lines]) - (lh * 0.55 if bullets else 0)
    if need > h + 0.02: print(f"  OVERFLOW {warn}: needs {need:.2f} in, box {h:.2f} in ({len(lines)} lines at {size} pt)")
    yy = H - y if va == "top" else H - y - h / 2 + (lh * len(lines)) / 2 - lh
    for l in lines:
        ax.text(x if ha == "left" else x + w / 2, yy, l, fontsize=size * 0.98, fontweight="bold" if bold else "normal", color=color, va="top", ha=ha, family="DejaVu Sans"); yy -= lh
def pbox(ax, x, y, w, h, fc, ec=None, r=0.1):
    ax.add_patch(FancyBboxPatch((x, H - y - h), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec or fc, lw=0.8))
def build_preview():
    pdf = PdfPages(os.path.join(HERE, "deck-preview.pdf"))
    for n, sl in enumerate(SLIDES, 1):
        fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off"); fig.subplots_adjust(0, 0, 1, 1)
        if sl.get("kind") == "title":
            pbox(ax, 0, 0, W, H, "#" + NAVY, r=0)
            ptext(ax, 0.9, 1.9, 11.5, 1.8, sl["title"], 36, bold=True, color="white", warn=f"s{n} title"); ptext(ax, 0.9, 3.75, 11.5, 0.7, sl["subtitle"], 22, color="#CADCFC")
            ptext(ax, 0.9, 4.6, 11.5, 0.5, sl["meta"], 14, color="#DDE6F0")
            ptext(ax, 0.9, 6.3, 11.5, 0.4, "Evidence tag on each slide:  Hardware measurement · Real application · Trace-driven emulation · Trace simulation · Estimate · Proposal (not implemented)", 11, color="#AFC0D6")
        elif sl.get("kind") == "cards":
            ptext(ax, 0.5, 0.33, 12.33, 1.0, sl["title"], tsize(sl["title"]), bold=True, color="#" + NAVY, warn=f"s{n} title"); ptext(ax, 0.5, 1.22, 7.5, 0.3, sl["part"], 11, color="#" + MUTED)
            for i, (hd, tx) in enumerate(sl["cards"]):
                cx, cy = 0.5 + (i % 3) * 4.19, 1.7 + (i // 3) * 2.65
                pbox(ax, cx, cy, 3.95, 2.4, "#" + TINT); ax.add_patch(plt.Circle((cx + 0.41, H - cy - 0.41), 0.21, color="#" + NAVY)); ax.text(cx + 0.41, H - cy - 0.41, str(i + 1), ha="center", va="center", color="white", fontsize=13, fontweight="bold")
                ptext(ax, cx + 0.75, cy + 0.15, 3.05, 0.9, hd, 13.5, bold=True, color="#" + NAVY, warn=f"s{n} card {i + 1} head"); ptext(ax, cx + 0.2, cy + 1.05, 3.6, 1.3, tx, 11.5, warn=f"s{n} card {i + 1}")
        else:
            L = layout(sl); x, y, w, h = L["fig"]
            ptext(ax, 0.5, 0.33, 12.33, 1.0, sl["title"], tsize(sl["title"]), bold=True, color="#" + NAVY, warn=f"s{n} title"); ptext(ax, 0.5, 1.22, 7.5, 0.3, sl["part"], 11, color="#" + MUTED)
            im = Image.open(os.path.join(FIG, sl["fig"] + ".png")); ax.imshow(im, extent=(x, x + w, H - y - h, H - y), aspect="auto")
            ptext(ax, *L["bullets"], sl["bullets"], L["bsize"], bullets=True, warn=f"s{n} bullets")
            x, y, w, h = L["take"]; pbox(ax, x, y, w, h, "#" + TINT); ptext(ax, x + 0.12, y + 0.08, w - 0.24, h - 0.16, "Takeaway: " + sl["takeaway"], 12.5, color="#" + NAVY, warn=f"s{n} takeaway")
            ptext(ax, *L["source"], f"Data: {sl['source']}  ·  figure {sl['fig']}", 9.5, color="#" + MUTED, warn=f"s{n} source")
        tx = 12.83; ax.text(tx, 0.3, str(n), ha="right", va="bottom", fontsize=9.5, color="#" + MUTED if sl.get("kind") != "title" else "#AFC0D6")
        # chips (preview)
        if sl.get("kind") != "title":
            xx = 12.83
            for t in reversed(sl["tags"]):
                ww = 0.1 + 0.075 * len(t); xx -= ww + 0.12; pbox(ax, xx, 1.2, ww, 0.3, "#" + TAGS.get(t, "F3F3F3")); ax.text(xx + ww / 2, H - 1.35, t, ha="center", va="center", fontsize=9, color="#" + INK)
        fig.savefig(os.path.join(OUTP, f"slide-{n:02d}.png"), dpi=72); pdf.savefig(fig); plt.close(fig)
    pdf.close(); print("wrote deck-preview.pdf and preview/slide-NN.png")

def write_outline():
    with open(os.path.join(HERE, "outline.md"), "w") as f:
        f.write("# Research progress deck 2026-10-13 — outline\n\nTitle: Interference-Aware Data Management with DRAM and CXL Memory — Research Progress and Experimental Findings\n\n| # | slide | part | evidence | figure |\n|---|---|---|---|---|\n")
        for n, sl in enumerate(SLIDES, 1):
            f.write(f"| {n} | {sl['title']} | {sl.get('part', '—')} | {', '.join(sl.get('tags', []))} | {sl.get('fig', '—')} |\n")
        f.write("\nEach content slide: one conclusion-style title, one figure, two to four short statements, one takeaway, the data source, speaker notes.\n")
    print("wrote outline.md")

if __name__ == "__main__":
    build_pptx(os.path.join(HERE, "..", "SLIDES_2026-10-13-progress-report.pptx")); build_preview(); write_outline()   # the deck sits beside the earlier SLIDES_*.pptx
