#!/usr/bin/env python3
"""Generates project/deck.json and project/slides/<id>.html for the 2026-09-22 status deck (Slides artifact type)."""
import json, os, datetime
ROOT = os.path.dirname(os.path.abspath(__file__)); SL = f"{ROOT}/project/slides"; os.makedirs(SL, exist_ok=True)
IMG = dict(cliff="/_blob/ba078b8ace0becf69658ac520641035d", duplex="/_blob/f3876b11f96d0b8801fdf77942f10f1d", o3="/_blob/0d19e94d67f59686fb1d4351659295c0", kv="/_blob/e8e365a62c556e82ec373e8b73b6df0b",
           budget="/_blob/e6a33ec926517e50c6361da647b48ea6", core="/_blob/de3e9d965e527c013857237257fb26e2", dcp="/_blob/e3267eb86ac9d3eef2b2847df944d1a9", controller="/_blob/a9993f8f69a3bacb6c320797d31d7df9",
           zeroline="/_blob/8242a16cf4a01cfec614b38045793411", guard="/_blob/643bee33f953138d1a97685060ae51bf")
LIGHT, LIGHT2, DARK, INK, INK2, DRAM, CXL, MUTED = "#f7f6f2", "#eceee9", "#15202b", "#15202b", "#4a5568", "#c8511b", "#1f6f78", "#6a7179"
HEAD = "font-family:'Source Serif 4', Georgia, serif"; BODY = "font-family:'IBM Plex Sans', Arial, sans-serif"
order = []; files = {}
CONV = 'Convention in every figure: <span style="color:#c8511b"><b>orange = DRAM / today&#39;s practice</b></span>, <span style="color:#1f6f78"><b>teal = CXL</b></span>, grey = throttled or reference; dotted line = a 7% slowdown bound.'
OBJ = 'Expected objections, answered by measurement: "add more CXL cards" &rarr; the policy follows measured capacity (4 cards: 85 GiB/s), a bigger pipe means a smaller loan; "nothing writes 44 GiB/s" &rarr; burst rate, not average &mdash; any multi-threaded checkpoint copy exceeds the pair momentarily.'
DUP = 'Both components read CXL while producers write it &mdash; allowed by the duplex link. One leftover rule ("the drain yields to active writers") is a DRAM habit and is on the fix list; see the open issues.'
FULL = '"CXL is full" is judged against a fixed 43.9 GiB/s capacity; beside llama.cpp the achievable rate is 29, so the loan never triggers &mdash; fullness must be measured, not assumed.'
STEP2B = 'Measured fullness: judge &#8220;CXL is full&#8221; from the achieved rate under the current co-runner, not a constant; re-run llama.cpp-32'
STEP2 = 'Measured fullness: judge "CXL is full" from the writers&#39; achieved rate vs a rate measured under the current co-runner, not a constant; re-run llama.cpp-32'

def slide(sid, title, body, notes="", source="", bg=LIGHT, eyebrow=""):
    order.append(sid)
    eb = f'<p style="font-size:24px; color:{CXL}; font-weight:600; letter-spacing:2px; text-transform:uppercase">{eyebrow}</p>' if eyebrow else ""
    foot = f'<p style="position:absolute; left:128px; bottom:64px; width:1400px; font-size:24px; color:{MUTED}">{source}</p>' if source else ""
    num = f'<p style="position:absolute; right:128px; bottom:64px; width:120px; text-align:right; font-size:24px; color:{MUTED}">{len(order)}</p>'
    aside = f"<aside>{notes}</aside>" if notes else ""
    html = f'''<section id="{sid}" data-transition="fade" style="background:{bg}; color:{INK}; {BODY}; padding:88px 128px 160px; display:flex; flex-direction:column; gap:24px">
{eb}<h2 style="{HEAD}; font-size:54px; font-weight:600; line-height:1.1">{title}</h2>
{body}
{foot}{num}{aside}
</section>
'''
    files[f"project/slides/{sid}.html"] = html
def ul(items, size=28, color=INK):
    return f'<ul style="font-size:{size}px; line-height:1.4; color:{color}">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
def p(text, size=28, color=INK, extra=""):
    return f'<p style="font-size:{size}px; line-height:1.4; color:{color}; {extra}">{text}</p>'
def card(title, text, w="flex:1", accent=CXL, size=24):
    return f'<div style="{w}; display:flex; flex-direction:column; gap:10px; background:#ffffff; padding:24px 28px; border:1px solid #dcdad3; border-top:6px solid {accent}; border-radius:12px"><h3 style="font-size:28px; font-weight:600; line-height:1.2">{title}</h3><p style="font-size:{size}px; line-height:1.4; color:{INK2}">{text}</p></div>'
def table(rows, widths, size=24, header=True):
    out = f'<table style="font-size:{size}px; line-height:1.3; border:1px solid #dcdad3">'
    for i, r in enumerate(rows):
        tag = "th" if (i == 0 and header) else "td"; bg = f' style="background:#e6e9e4"' if (i == 0 and header) else (' style="background:#ffffff"' if i % 2 == 1 else "")
        out += f"<tr{bg}>" + "".join(f'<{tag}{(" style=&quot;width:" + str(widths[j]) + "%&quot;").replace("&quot;", chr(34)) if i == 0 else ""}>{c}</{tag}>' for j, c in enumerate(r)) + "</tr>"
    return out + "</table>"
def img(key, w, h): return f'<img src="{IMG[key]}" alt="figure" style="width:{w}px; height:{h}px; object-fit:contain">'
def two(left, right, lw=760, gap=40): return f'<div style="display:flex; gap:{gap}px; align-items:start"><div style="width:{lw}px; display:flex; flex-direction:column; gap:18px">{left}</div><div style="flex:1; display:flex; flex-direction:column; gap:18px">{right}</div></div>'

# ---------------- cover ----------------
order.append("cover"); files["project/slides/cover.html"] = f'''<section id="cover" data-transition="fade" style="background:{DARK}; color:#f7f6f2; {BODY}; padding:128px; display:flex; flex-direction:column; justify-content:space-between">
<p style="font-size:28px; color:#9fc4c8; letter-spacing:2px; text-transform:uppercase">Project status · 2026-09-22</p>
<div style="display:flex; flex-direction:column; gap:28px">
<h1 style="{HEAD}; font-size:88px; font-weight:600; line-height:1.05">CXL by default, DRAM on loan:<br>managing the write path of bulk data</h1>
<p style="font-size:34px; line-height:1.4; color:#d7dde3; width:1500px">Where the idea came from, what the system does, and what the experiments show so far — checkpoint staging and KV-cache pools on a real CXL machine.</p>
</div>
<p style="font-size:26px; color:#9fc4c8">Runtime name: cxlpath (working name) · c28: AMD EPYC 9745, 755 GB DDR5, Micron CZ120 CXL memory · target quality: OSDI</p>
<aside>Three parts: background and motivation with the measured data, the problems and the design that answers them, the validation experiments run so far. Every data figure is drawn from raw results in the repository.</aside>
</section>
'''

# ---------------- outline ----------------
slide("outline", "Three parts", f'''
<div style="display:flex; gap:32px">
{card("1 · Background and motivation", "The machine and its two memory facts; today's DRAM-first write path; three observations from data (moving is nearly free, keeping is harmful, CXL is a safe destination); the three simple policies; where the literature stands.", accent=CXL, size=26)}
{card("2 · Problems and the design", "Each problem mapped to a requirement; the four components of cxlpath (segment store on raw CXL, the loan controller, the read path, the DRAM-free drain); the clients.", accent=DRAM, size=26)}
{card("3 · Validation so far", "Phase 1 (write budget under a bound), phase 2 (three policies vs cxlpath, real data re-run in progress), the real PyTorch producer, the regime signal, a methodology finding, open issues and next steps.", accent=INK2, size=26)}
</div>
{p(CONV, 26, INK2)}
''', notes="Set the colour convention once; it holds in every plot.")

# ---------------- Part 1 ----------------
slide("machine", "The machine: DRAM and CXL side by side on one socket", f'''
{table([["component", "what it is", "measured"],
 ["CPU", "AMD EPYC 9745: 128 cores in 8 CCDs, one NUMA node", "victim, probe and producer always on separate CCDs"],
 ["DRAM", "755 GB DDR5, 12 channels", "reads and writes share one pipe; socket write ceiling ~290 GiB/s"],
 ["CXL memory", "4 × Micron CZ120; usable pair dax0.0 + dax1.0 (hardware-hashed interleave), raw devdax, no NUMA node, no root", "NT writes 43.9 GiB/s, reads 45.6; one core alone writes 41"],
 ["CPU reading CXL", "sequential consumer", "24 GiB/s vs 41 from DRAM (1.7× slower)"],
 ["NVMe", "local, O_DIRECT", "0.9 GiB/s sustained at any parallelism"],
 ["GPU", "RTX 4060 Ti 8 GB", "GPU → CXL 3.9 GiB/s direct (12.3 into pinned DRAM); reads CXL at 12.5"]], [16, 46, 38], size=24)}
{p("Two memories with different physics: DRAM's reads and writes contend on one pipe; CXL hangs off PCIe lanes and its own controller. Everything in this deck is measured on this machine.", 26, INK2)}
''', notes="The hardware facts the whole story rests on: 43.9 GiB/s of CXL write capacity, and a DRAM write ceiling of ~290 GiB/s that reads and writes share.", source="hardware/results/, docs/experiments/2026-09-08-cxl-card-scaling.md", eyebrow="Part 1 · Background")

slide("cliff", "DRAM fact: reads and writes share one pipe, and past a point the reader falls off a cliff", f'''
{two(img("cliff", 1000, 524), ul([
 "A 4-thread DRAM reader on its own CCD; NT-store writers on other CCDs.",
 "Up to ~140 GiB/s of writes the reader loses 18–22%; at ~273 GiB/s (the socket's write ceiling) it loses 92%: 96 → 8 GiB/s, load latency 130 → 610 ns.",
 "Reader + writers always sum to ~290–300 GiB/s: one conserved pipe.",
 "Direction decides who suffers: reads 11–12×, plain-store writes 8×, mixed 6–7×, NT writes only −13–23%."], 25), lw=1000)}
''', notes="This is the write-drain cliff. It is a cliff, not a slope: the memory controller enters drain mode when its write queue stays full, and reads wait.", source="docs/experiments/2026-09-08-dram-write-drain.md (verified pass 1b2, healthy NPS1 DRAM)", eyebrow="Part 1 · Background")

slide("duplex", "CXL fact: reads and writes together exceed either alone (partial duplex)", f'''
{two(img("duplex", 980, 513), ul([
 "Mixed traffic on the card pair: 59–62 GiB/s against 44–46 for one direction (+30–36%); a single card +53%.",
 "Not isolation: a reader sharing the card with a full write stream keeps ~60% of its bandwidth (latency 2.2×); the writers keep 80%.",
 "Cards are isolation domains: traffic on one card costs the neighbour card nothing.",
 "Design consequence: reading CXL while it is written is cheap for the writers — the drain and the read path rely on it."], 24), lw=980)}
''', notes="The earliest finding of the project (August). Aggregate +30–50%, but a co-located reader still pays; the overstated 'directions are independent' sentence was removed from the paper.", source="docs/experiments/2026-08-25-direction-gates.md, 2026-09-08-cxl-card-scaling.md, 2026-09-02-pairb-card-interference.md", eyebrow="Part 1 · Background")

slide("today", "Today's bulk writers all make DRAM the first stop", f'''
{table([["bulk writer", "first stop of the data", "how much is read again", "extra traffic it causes", "representative systems"],
 ["Checkpoint staging (training)", "a DRAM staging copy, then a serializer thread writes NVMe/PFS", "only after a failure (rare)", "the staging copy (read + write of the whole state), then the serializer reads it again", "PyTorch DCP async_save, CheckFreq, Gemini, DataStates-LLM, VeloC"],
 ["KV-cache pools (LLM serving)", "a CPU-side DRAM pool for prefixes evicted from HBM", "22–42% of blocks, seconds to minutes later", "every prefill's KV written into DRAM; hits copied back", "LMCache, Mooncake store, vLLM CPU offload, CachedAttention"],
 ["Kernel memory tiering", "new pages in DRAM; demote when cold", "policy-dependent; write-once pages sit in DRAM until aged", "demotion / migration copies through DRAM", "TPP, Memtis, Nomad, Colloid, MEMSTRATA"]], [18, 22, 18, 22, 20], size=24)}
{p("Common shape: the data is written into DRAM by default, most of it is never read from there, and the act of writing it competes with every program that reads DRAM at the same time. None of these systems decides where a <i>write stream</i> should land; they place data by hotness after the fact.", 26, INK2)}
''', notes="Table 1 of the paper. The point is the shared shape, not any single system.", source="docs/PAPER.md §3 Table 1; Related.md (97 papers surveyed 2026-07)", eyebrow="Part 1 · Motivation")

slide("o1", "Observation 1 · Moving this data off DRAM is nearly free: most of it is never read again", f'''
{two(img("kv", 1000, 437), ul([
 "Prefix-cache pool: a block is written when a request's prefix KV is offloaded, read only if a later request shares that prefix. (Attention inside a request reads HBM, not the pool.)",
 "58–78% of written blocks are never hit by a later request; the number is conservative (output-token KV that is never reused is not even counted as written).",
 "Checkpoints are read only after a failure.",
 "Flip side: 22–42% of KV blocks ARE read back, seconds to minutes later — the minority that deserves DRAM. Predicting which ones in advance does not work (selective drain lowered the hit rate), so: write everything cheaply, promote what is actually read."], 24), lw=1000)}
''', notes="Answer to the natural objection that decoding reads all previous tokens: that is the GPU-resident cache; the pool is a different tier.", source="docs/experiments/2026-09-09-kv-trace-analysis.md (Mooncake FAST'25 traces), 2026-09-18-kv-selective-drain.md", eyebrow="Part 1 · Motivation")

slide("o2", "Observation 2 · Keeping it in DRAM is harmful", f'''
{img("budget", 1200, 480)}
{p("Under a 7% bound a co-runner may push only 40 GiB/s (pure) / 28 (copies) of DRAM writes beside a streaming reader and 18–21 / 9–12 beside the saturated applications — the order of the CXL pair's 43.9 GiB/s or below. Copies hurt ~2× more than pure writes: their source read shares the pipe.", 25, INK2)}
''', notes="Phase-1 result, but it belongs to the motivation: no system involved.", source="docs/experiments/2026-09-21-dram-write-budget.md, 2026-09-22-budget-more-victims.md (medians of 3 repetitions)", eyebrow="Part 1 · Motivation")

slide("o3", "Observation 3 · CXL is a safe destination: the same write stream redirected to CXL costs the DRAM reader nothing", f'''
{two(img("o3", 1000, 437), ul([
 "The 8-thread NT write stream that collapses the reader 6.3× (68.6 → 10.9 GiB/s) costs it nothing when it goes to CXL (68.6 = idle, latency = idle).",
 "A stencil whose data lives on CXL runs at the same speed with and without 280 GiB/s of DRAM write pressure beside it; the all-DRAM version is 10× slower under that pressure.",
 "Precise form: the WRITE half leaves DRAM; the READ of the source data stays wherever the destination is (measured later as 3–7% of harm for copies out of a saturated DRAM)."], 25), lw=1000)}
''', notes="The empirical core of the motivation. The stencil result also says: move the write streams off DRAM, do not move the victim's buffers.", source="docs/experiments/2026-08-25-direction-gates.md (gate 2b), 2026-09-14-stencil-3c.md", eyebrow="Part 1 · Motivation")

slide("strawmen", "Three simple policies, and why each fails on one axis", f'''
<div style="display:flex; gap:28px">
{card("All-DRAM staging (today)", "Fastest copy while the DRAM pipe has room, but the reader pays: 27% slowdown beside a streaming reader, 42–71% beside PageRank, 16% beside a saturated Adam step — and it keeps tens of GB in DRAM for the tens of seconds a 0.9 GiB/s drain needs.", accent=DRAM)}
{card("All-CXL", "Protects the readers (0–2%) but caps every producer at the CXL write capacity, 43.9 GiB/s here — which a single core already reaches — and at 3.9 GiB/s for a GPU source on this platform.", accent=CXL)}
{card("Rate-limited all-DRAM", "Protects the readers too, but caps the producer at the DRAM budget under the bound (10–20 GiB/s for these victims): a 64 GiB copy takes 3.2–19 s, and the data still occupies DRAM.", accent=MUTED)}
</div>
{p("<b>So: use CXL by default, and borrow DRAM only while CXL is the bottleneck and the loan does not slow other DRAM readers beyond a bound.</b> This sentence closes the motivation and is design principle P2.", 28)}
{p(OBJ, 24, INK2)}
''', notes="The numbers here are from the real-data re-run (two repetitions) and phase 1.", source="docs/PAPER.md §3; numbers from 2026-09-22-three-policies-realdata (in progress)", eyebrow="Part 1 · Motivation")

slide("literature", "Where the literature stands", f'''
{table([["line of work", "representative papers", "what they do", "the gap"],
 ["CXL / tiered memory", "TPP (ASPLOS'23), Memtis (SOSP'23), Nomad (OSDI'24), Colloid (SOSP'24), Memstrata (OSDI'24), Pond (ASPLOS'23)", "place pages by hotness or latency; DRAM first, demote cold pages", "never ask where a write STREAM should land; migration is itself DRAM traffic"],
 ["Training checkpoints", "CheckFreq (FAST'21), Gemini (SOSP'23), DataStates-LLM (HPDC'24), VeloC, PyTorch DCP", "hide checkpoint cost with asynchrony, throttling, peer memory", "the staging copy lands in DRAM; the persist thread reads it again; throttled to protect the trainer"],
 ["KV-cache offload", "LMCache, Mooncake (FAST'25), CachedAttention (ATC'24), vLLM CPU offload", "keep evicted prefixes in a CPU DRAM pool or SSD, reuse across requests", "the pool's ingest is a DRAM write stream beside the engine; no bound on its cost"],
 ["Horizontal storage (inspiration)", "PolyStore (FAST'25)", "heterogeneous storage side by side, epoch re-balancing, per-device cache rules", "storage, not memory: no shared pipe, no cliff, no loan under a latency bound"]], [17, 30, 26, 27], size=24)}
{p("No system manages the write path of bulk data between DRAM, CXL and storage under a reader-protection bound. PolyStore is where several of our ideas and the paper's shape come from — not a baseline.", 25, INK2)}
''', notes="PolyStore is a source of ideas and of the paper's shape; it is neither a baseline nor the foil.", source="Related.md; benchmarks/results/2026-09-21-benchmark-survey.md", eyebrow="Part 1 · Related work")

# ---------------- Part 2 ----------------
slide("problems", "From problems to requirements", f'''
{table([["problem (what the data says)", "requirement / principle", "answered by"],
 ["Bulk writes land in DRAM and hurt every DRAM reader (O2); most of the data is never read again (O1)", "P2 · Writes bypass DRAM by default; DRAM is borrowed only while CXL is the bottleneck and co-runners stay inside a slowdown bound", "Component B: loan controller"],
 ["CXL is a raw devdax device: no allocator, no naming, no crash safety; one core already saturates it", "P1 · A shared, crash-safe segment store on the raw device; no system call on the data path", "Component A: segment store"],
 ["A minority is read again, seconds to minutes later; CPU reads from CXL are 1.7× slower", "P3 · Read in place; promote to DRAM only past break-even, and only when DRAM is calm", "Component C: read path"],
 ["Today's persist path reads the DRAM copy again and is throttled to protect the trainer", "P4 · Drain straight from CXL to NVMe; bounded durability lag; versions reclaimed", "Component D: drain, recovery"],
 ["Producers can be faster than CXL; GPU sources are slow into CXL directly", "the loan (P2); per-chunk GPU direct / staged paths", "Components B, GPU path"]], [40, 40, 20], size=24)}
''', notes="The bridge the paper needs before any mechanism: why before how. The design section then says only how.", source="docs/DESIGN.md §10.1 goals and principles", eyebrow="Part 2 · Design")

slide("arch", "cxlpath in one picture", f'''
<div style="display:flex; gap:24px; align-items:center">
<div style="width:300px; display:flex; flex-direction:column; gap:14px">
<div style="background:#ffffff; border:2px solid {INK2}; border-radius:12px; padding:18px"><h3 style="font-size:26px; font-weight:600">Producers</h3><p style="font-size:24px; line-height:1.35; color:{INK2}">VeloC (HPC checkpoints) · PyTorch DCP async_save · KV-cache layer · GPU sources</p></div>
<div style="background:#ffffff; border:2px solid {INK2}; border-radius:12px; padding:18px"><h3 style="font-size:26px; font-weight:600">Consumers</h3><p style="font-size:24px; line-height:1.35; color:{INK2}">restore, prefix-cache hits, evaluation readers — read in place, or promoted</p></div>
</div>
<x-shape kind="arrow-right" style="width:70px; height:40px; background:{INK2}"></x-shape>
<div style="width:520px; display:flex; flex-direction:column; gap:14px">
<div style="background:#ffffff; border:2px solid {INK}; border-radius:12px; padding:18px"><h3 style="font-size:26px; font-weight:600">libcxlpath (in the producer's process)</h3><p style="font-size:24px; line-height:1.35; color:{INK2}">reserve → NT copy → commit on 32 MiB segments; objects, buffer sets, streams; pins and read counts; break-even promotion; no system call on the data path</p></div>
<div style="background:#ffffff; border:2px solid {INK}; border-radius:12px; padding:18px"><h3 style="font-size:26px; font-weight:600">cxlpathd (one daemon per store)</h3><p style="font-size:24px; line-height:1.35; color:{INK2}">DRAM latency probe · loan controller publishing a spill ratio · headroom guard · producer pacing (last resort) · drain to NVMe · version reclamation</p></div>
</div>
<x-shape kind="arrow-right" style="width:70px; height:40px; background:{INK2}"></x-shape>
<div style="flex:1; display:flex; flex-direction:column; gap:14px">
<div style="background:#e3eeef; border:2px solid {CXL}; border-radius:12px; padding:18px"><h3 style="font-size:26px; font-weight:600; color:{CXL}">CXL segment store (dax0.0 + dax1.0) — the default</h3><p style="font-size:24px; line-height:1.35; color:{INK2}">shared CAS segment table and object index in /dev/shm; survives a killed writer</p></div>
<div style="background:#f6e6de; border:2px solid {DRAM}; border-radius:12px; padding:18px"><h3 style="font-size:26px; font-weight:600; color:{DRAM}">DRAM pool — the loan</h3><p style="font-size:24px; line-height:1.35; color:{INK2}">pre-allocated, populated tmpfs; receives a fraction of new chunks only while CXL is full and the probe is under the bound</p></div>
<div style="background:#ffffff; border:2px solid {INK2}; border-radius:12px; padding:18px"><h3 style="font-size:26px; font-weight:600">NVMe / PFS</h3><p style="font-size:24px; line-height:1.35; color:{INK2}">O_DIRECT drain straight from the CXL mapping; DRAM is never read for it</p></div>
</div>
</div>
''', notes="Life of a write: reserve a chunk, the policy page says CXL or DRAM, NT-copy, commit; the daemon drains committed data to NVMe from CXL; consumers read in place or promote.", source="docs/DESIGN.md §10.2, §10.10", eyebrow="Part 2 · Design")

slide("compA", "Component A · A segment store on the raw CXL device", f'''
{two(ul([
 "32 MiB segments on each dax device; a shared segment table with CAS state transitions (free → reserved → committed → freeing) in /dev/shm — no central server on the data path.",
 "Writers work on per-thread log segments: <b>reserve → copy_to (non-temporal stores) → commit</b>; 82 ns of library work per 32 MiB write, zero system calls.",
 "A shared object index (key → extents, generation, supersede pointer) that survives a SIGKILLed writer; crash cleanup on attach.",
 "Buffer sets: virtually contiguous regions stitched from scattered segments, registered once with CUDA (~20 ms/GiB) for GPU sources and for the PyTorch stager.",
 "Streams: a file-style shim (packed extents) for clients that think in files (VeloC)."], 25),
 ul(["Why raw devdax: the kernel boots with CXL offline and no root is available; a NUMA-node view would also hide the card pair's topology.", "The DRAM pool is a tmpfs file, fallocated and mapped populated: first-touch faults had made a spilled chunk 5× slower than a CXL chunk.", "Small objects (KiB-MiB, the KV layer) use a larger object table; the same reserve/commit path."], 24, INK2), lw=1000)}
''', notes="Mechanism only; the rationale lives in DESIGN.md §10.11.", source="system/cxlpath/src/store.c, reserve.c, object.c, bufset.c; gates in docs/experiments/2026-09-08-write-tier-campaign.md Phase 5 v2", eyebrow="Part 2 · Design")

slide("compB", "Component B · The loan controller: DRAM lent to writers under a latency bound", f'''
{two(img("controller", 960, 414), ul([
 "<b>Signal:</b> a DRAM latency probe on a spare core every 10 ms while writers are active; windowed medians give an idle and an active reference.",
 "<b>Actuator:</b> a published spill ratio (n/16 of new chunks go to the DRAM pool): +1/16 per calm epoch, halved after two epochs over the bound.",
 "<b>Only when it can help and cannot hurt:</b> CXL ≥ 90% of its write capacity, probe under bound × idle, and a headroom guard (no loan above 1.3× the calibrated idle level).",
 "<b>Memory and last resort:</b> each stream keeps the ratio it reached; if no loan is possible and the probe still exceeds the bound, a token bucket paces the producer."], 24), lw=960)}
''', notes="The figure is a real run beside the 8-thread reader: the probe rises to the bound during a copy, the ratio ramps to 30–40% and is remembered, and the loan sits on top of the CXL stream.", source="system/cxlpath/src/policy.c, probe.c, controller.c, daemon/cxlpathd.c; trace: three-policies-realdata/reader-cxlpath-b1.09-rep1-daemon.csv", eyebrow="Part 2 · Design")

slide("compCD", "Components C and D · Read in place, promote on break-even; drain without DRAM", f'''
<div style="display:flex; gap:32px">
{card("C · Read path", "Consumers pin an object (slot + generation) and read it where it is. Every read is counted; an object is promoted to DRAM only when its read count passes the break-even k derived from measured rates (CXL read 24 GiB/s, DRAM read 41, copy 25 → k = 3 here), and only while the DRAM probe says DRAM is calm — the promotion copy is itself a DRAM write stream. KV objects that were never read are simply reclaimed.", accent=CXL, size=24)}
{card("D · Drain and recovery", "The daemon writes committed data to NVMe with O_DIRECT straight from the devdax mapping (4 KiB-aligned body direct, tails buffered; files byte-identical). Checkpoint versions form chains; a version is reclaimed once its successor is durable. Durability lag is bounded (2 s) even under continuous writers. A killed writer's reservations are cleaned up on the next attach; the index is rebuilt from committed segments.", accent=DRAM, size=24)}
</div>
{p(DUP, 25, INK2)}
''', notes="", source="system/cxlpath/src/readpath.c, drain.c", eyebrow="Part 2 · Design")

slide("clients", "Clients: what a producer has to change", f'''
{table([["client", "integration", "what we learned"],
 ["VeloC (HPC checkpoints)", "storage-module patch: pwrite → reserve / copy_in on packed extents; byte-exact round trip", "a stale static library silently fell back to stock VeloC; the path is now proven by a gate"],
 ["PyTorch torch.distributed.checkpoint", "CxlpathWriter / Reader = DCP's AsyncStager + StorageWriter; CPU tensors NT-copied by 8 pinned threads (one core cannot fill CXL from Python)", "stock async_save without a stager copies nothing; DCP's own BlockingAsyncStager (pinned DRAM copy) is today's practice"],
 ["KV-cache layer", "a trace-driven stand-in with LMCache's call pattern; the real LMCache + vLLM integration is a phase-3 item", "version chains and supersede semantics came from this client"],
 ["GPU sources", "per 32 MiB chunk: direct write into a CUDA-registered CXL buffer set (3.9 GiB/s cap) or staged through pinned DRAM", "the direct-write cap does not react to anything visible without root"]], [22, 44, 34], size=24)}
''', notes="", source="system/cxlpath/clients/, src/gpu/", eyebrow="Part 2 · Design")

# ---------------- Part 3 ----------------
slide("plan", "Evaluation plan and where it stands", f'''
{table([["phase", "question", "status (2026-09-22)"],
 ["1 · DRAM write budget", "How many GiB/s of bulk writes into DRAM cost a DRAM-bound program 5 / 7 / 10%? Pure vs copies; CXL as control", "done, valid (five victims; LULESH dropped as insensitive)"],
 ["2 · Core figure, O2 headline", "A periodic 64 GiB copy beside a victim: all-DRAM (NT / plain), all-CXL, throttled DRAM, cxlpath — slowdown vs completion", "superseded (zero-line snapshot); re-run with random data: 2 of 3 repetitions done, 7 victims"],
 ["2b · The real producer", "torch.distributed.checkpoint.async_save: stock DRAM stager vs CxlpathWriter", "done, valid (3 repetitions)"],
 ["3 · Components, sensitivity, clients", "ablations (guard, bound, step, fullness), read path, read-while-write (duplex), real LMCache + vLLM, VeloC end to end", "to agree next"]], [22, 50, 28], size=24)}
{p("Invariants: victim, probe and producer on separate CCDs; slowdown = median step time inside the copy window vs the 10 s before; median over the last 3 of 6 windows, then over 3 repetitions; every number links its raw log.", 24, INK2)}
''', notes="", source="docs/experiments/INDEX.md, METHODOLOGY.md", eyebrow="Part 3 · Validation")

slide("phase1", "Phase 1 · The usable DRAM write budget under a bound is small", f'''
{two(table([["victim", "7% budget, pure writes", "7% budget, copies", "probe level beside it"],
 ["synthetic reader, 8 threads (~100 GiB/s)", "40 GiB/s", "28 GiB/s", "1.0× idle (135 ns)"],
 ["CPU Adam step, 80 threads (340 GB/s of traffic)", "17.5 GiB/s", "~9–30 (source-bound)", "1.95× (262 ns)"],
 ["llama.cpp decode, 80 threads", "18–21 GiB/s", "11–12 GiB/s", "~1.5× (200 ns)"],
 ["GAPBS PageRank 2^26, 80 threads", "18–21 GiB/s", "11–12 GiB/s", "1.4× (200 ns)"],
 ["copies into CXL instead (control)", "—", "cost 3–5% at 25–40 GiB/s (the source read)", "—"]], [40, 18, 22, 20], size=24),
 ul(["The budget is the same order as, or below, the CXL pair's 43.9 GiB/s: the loan can at best roughly double the write path, never add an order of magnitude.", "Copies hurt ~2× more than pure writes: the source read shares the pipe.", "Headline victim chosen here: the CPU-offloaded Adam step (ZeRO-Offload style training) — the most bandwidth-bound real workload we have."], 24, INK2), lw=1060)}
''', notes="", source="docs/experiments/2026-09-21-dram-write-budget.md, 2026-09-22-budget-more-victims.md", eyebrow="Part 3 · Validation")

slide("core", "Phase 2 · Simple policies vs cxlpath, real data (3 repetitions)", f'''
{img("core", 1450, 403)}
{ul(["<b>Moderate victims</b> (reader, PageRank-32): cxlpath lends 23–34% of the chunks — 1.3–1.5× faster than all-CXL inside the bound, ~3× faster than a throttled writer at equal harm, 4–10× less harm than today's staging.",
     "<b>Saturated victim</b> (Adam-80): every copy is source-bound at ~18 GiB/s; only the harm changes (16% DRAM vs 7% CXL); cxlpath correctly lends nothing.",
     "<b>llama.cpp-32:</b> real data copies into DRAM at only 22 GiB/s (93 with zeros), slower than into CXL (29): DRAM staging has no speed advantage there; cxlpath = all-CXL because CXL never looks full (open issue)."], 24)}
''', notes="All three repetitions; the numbers moved by at most a point or two from the two-repetition version.", source="docs/experiments/2026-09-22-three-policies-realdata.md (closed 2026-09-23)", eyebrow="Part 3 · Validation")

slide("guard", "The regime signal: the absolute probe level decides whether a loan is safe", f'''
{two(img("guard", 860, 410), ul([
 "A probe bound maps to victim slowdown by a victim-dependent factor (a 10% probe rise ≈ 7% for the reader, ≈ 19% for Adam, ≈ 30% for PageRank), so a bound alone over-lent beside saturated victims (PageRank 36% vs 14% all-CXL).",
 "The absolute level separates the regimes: ~135–155 ns with headroom, 190–270 ns saturated. Guard = 1.3× a 2 s calibration of the idle level.",
 "Result: the loan goes only to the reader, PageRank-32 and llama.cpp-32; beside saturated victims cxlpath = all-CXL with 2.4–3.5× less harm than DRAM staging.",
 "Pacing (last resort) works where the probe is clean (Adam-32: 11.5% → 8% at 1.3× the time), is marginal where the victim's own phases move it."], 24), lw=860)}
''', notes="", source="docs/experiments/2026-09-22-three-policies.md (extension), 2026-09-22-moderate-pacing-dcp.md; probe levels from the daemon logs", eyebrow="Part 3 · Validation")

slide("dcp", "The headline with the real producer: dcp.async_save beside a training step", f'''
{img("dcp", 1400, 452)}
{p("16 GiB state dict every 30 s beside the 80-thread Adam step; three repetitions within 0.3 points. <b>Training thread blocked 0.8 s vs 1.6 s; 7.2% vs 12% slowdown during the stage; no tail vs a 0.4–1.5% tail for the 30 s of serialisation; durable after 19 s vs 31–33 s.</b> Beside llama.cpp-32 the stock stager is faster (0.31 vs 0.55 s) but hurts 14% vs 2–4%.", 24, INK2)}
''', notes="Observations 2 and 3 in one timeline with the real library: the stage window and the persist tail. This replaces the synthetic headline.", source="docs/experiments/2026-09-22-moderate-pacing-dcp.md item 3; benchmarks/policy/torch_ckpt_producer.py", eyebrow="Part 3 · Validation")

slide("zeroline", "A methodology finding: all-zero cache lines are written at full speed beside a co-runner, data lines are not", f'''
{two(img("zeroline", 860, 361), ul([
 "Found while comparing the PyTorch producer (29 GiB/s into CXL beside llama.cpp) with the C producer (43): the C snapshot was touched one word per 4 KiB — 98% zero lines.",
 "Alone, zeros and random data copy alike (43.9 → CXL, 94.5 → DRAM). Beside llama.cpp-32, zero lines keep 100% / 87%, data lines fall to 66% / 20%. One non-zero byte per 64 B line is enough; reads unaffected; huge pages irrelevant.",
 "Not every co-runner triggers it (the reader and PageRank-32 do not); the mechanism is open.",
 "Consequence: all phase-2 numbers before 2026-09-22 20:00 are superseded; phase 1, the cliff and the PyTorch producer wrote data and stand. Invariant: sources are pseudo-random, always."], 24), lw=860)}
''', notes="It cost a re-run, and it is a hardware observation nobody has reported for this platform.", source="docs/experiments/2026-09-22-zero-line-writes.md; METHODOLOGY.md", eyebrow="Part 3 · Validation")

slide("open", "What holds today, and what is open", f'''
<div style="display:flex; gap:32px">
<div style="flex:1; display:flex; flex-direction:column; gap:12px; background:#e3eeef; padding:26px 30px; border-radius:12px"><h3 style="font-size:30px; font-weight:600; color:{CXL}">Holds</h3>{ul(["The three observations, with real applications and real data.", "The loan is real and safe beside moderate victims (reader, PageRank-32): 1.3–1.5× all-CXL inside the bound, ~3× a throttled writer.", "Beside saturated victims cxlpath = all-CXL with 2.4–3.5× less harm than DRAM staging at the same completion.", "The real PyTorch producer: 2× shorter block, 1.7× sooner durable, no persist tail.", "Controller mechanics: the guard decides the regime; pacing engages where the probe is clean."], 24)}</div>
<div style="flex:1; display:flex; flex-direction:column; gap:12px; background:#f6e6de; padding:26px 30px; border-radius:12px"><h3 style="font-size:30px; font-weight:600; color:{DRAM}">Open</h3>{ul(["The duplex property is used only implicitly; the drain still yields to writers (a DRAM habit) and no experiment reads CXL while it is written.", FULL, "The DCP plugin stages into buffer sets, which are outside the loan; CPU tensors should go through reserve chunks.", "Pacing beside read-saturated victims is limited by probe noise: the probe is a proxy for the victim's slowdown, not a measurement of it.", "The zero-line trigger inside llama.cpp is unexplained; llama.cpp's token rate drifts with context over long runs."], 24)}</div>
</div>
''', notes="", eyebrow="Part 3 · Status")

slide("next", "Next steps (proposed order)", f'''
{table([["step", "what", "why now"],
 ["1", "Finish the real-data re-run; rewrite the phase-2 verdicts and the positioning", "the core figure must rest on data-carrying writes"],
 ["2", STEP2B, "the one case where the loan should have helped and did not"],
 ["3", "Put duplex back: an observation in §3; the drain never waits for writers; a read-while-write experiment", "the earliest finding is invisible in the paper today"],
 ["4", "Phase 3: sensitivity and ablations (guard, bound, step, fullness), read path, GPU paths", "second half of the evaluation"],
 ["5", "Real clients: LMCache + vLLM, VeloC + LULESH end to end, DCP through reserve chunks", "the real-application section"],
 ["6", "Write in parallel: intro, §3 as pure analysis, §4.1 requirements, components how-only", "outline agreed; figures now exist"]], [6, 60, 34], size=24)}
''', notes="Steps 2 and 3 are small code changes with unit tests; 4 and 5 are the bulk of the remaining machine time.", source="docs/PAPER.md, docs/DESIGN.md §10.11, WORKLOG.md session 26", eyebrow="Next")

deck = {"v": 4, "createdOnFiles": {"v": 1, "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, "title": "cxlpath status 2026-09-22", "order": order,
        "sections": {"intro": {"description": "What the deck covers", "start": "cover"}, "background": {"description": "The machine, today's DRAM-first write path, three observations from data, the simple policies and the literature", "start": "machine"},
                     "design": {"description": "Problems mapped to requirements, and the four components of cxlpath", "start": "problems"}, "validation": {"description": "The experiments run so far, what holds and what is open", "start": "plan"}, "next": {"description": "Proposed next steps", "start": "next"}},
        "faces": {"source-serif-4": {"family": "Source Serif 4", "href": "https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400..700&display=swap"}, "ibm-plex-sans": {"family": "IBM Plex Sans", "href": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap"}}, "designSystems": []}
os.makedirs(f"{ROOT}/project", exist_ok=True); json.dump(deck, open(f"{ROOT}/project/deck.json", "w"), indent=1)
for path, html in files.items(): open(f"{ROOT}/{path}", "w").write(html)
print(len(order), "slides:", " ".join(order))
