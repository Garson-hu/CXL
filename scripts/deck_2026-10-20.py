#!/usr/bin/env python3
"""Build the RQ1 progress deck of 2026-10-20 for the weekly advisor meeting: an editable PowerPoint (python-pptx, 16:9,
white background, Calibri) plus a preview PDF/PNGs drawn by matplotlib from the same slide data (layout check only — there
is no PowerPoint or LibreOffice on c28; DejaVu Sans is wider than Calibri, so what fits in the preview fits in PowerPoint)
and outline.md. Slide text follows Simplified Technical English: short sentences, one idea each, active voice.
usage: scripts/deck_2026-10-20.py   (run after scripts/figs_deck_2026-10-20.py; writes docs/slides/SLIDES_2026-10-20-rq1-progress.pptx,
       docs/slides/2026-10-20-rq1-progress/{deck-preview.pdf,preview/slide-NN.png,outline.md})"""
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
HERE = os.path.join(ROOT, "docs", "slides", "2026-10-20-rq1-progress"); FIG = os.path.join(HERE, "figs"); OUTP = os.path.join(HERE, "preview"); os.makedirs(OUTP, exist_ok=True)
DECK = os.path.join(ROOT, "docs", "slides", "SLIDES_2026-10-20-rq1-progress.pptx")
W, H = 13.333, 7.5
INK, MUTED, NAVY, TINT, LINE = "1F2D3D", "6B6B6B", "1B2A41", "F3F6FA", "D9DEE5"
FONT = "Calibri"
TAGS = {"Oracle": "FBE3E3", "Trace-driven simulation": "FDEBD9", "Trace analysis": "FDEBD9", "Real-system measurement": "E3F1E1", "Framing": "EEEEEE", "In progress": "FFF4CC"}

# ------------------------------------------------------------------ slide data
def S(title, why, tags, fig, points, source, notes): return dict(kind="fig", title=title, why=why, tags=tags, fig=fig, points=points, source=source, notes=notes)
SLIDES = [
dict(kind="title", title="RQ1: Is future reuse information valuable and predictable?",
     subtitle="Progress on the reuse-aware half of unified DRAM/CXL memory management for the LLM KV cache",
     meta="Weekly advisor meeting  ·  2026-10-20  ·  evidence: public Mooncake traces (trace-driven simulation), real runs on c28 (vLLM 0.31 + LMCache 0.5.5, RTX 4060 Ti), oracles",
     notes="This deck reports one research question, RQ1. The story runs from the upper bound (an oracle) through every realistic source of "
           "future-reuse information we tested, to the one method that gave a useful result. Each slide carries evidence tags: Oracle (uses the "
           "future), Trace-driven simulation (exact replay of real traces in a capacity model), Real-system measurement (vLLM + LMCache on the "
           "RTX 4060 Ti). Every number comes from the raw result files in experimental_results/; the figures are drawn from them by scripts/figs_deck_2026-10-20.py."),

S("The cache decides per block what to store and keep; RQ1 asks whether it can know future reuse",
  "Why this question: every decision of the cache (admit, place, keep, move) depends on whether the block will be read again, and most blocks never are.",
  ["Framing"], "f01_overview",
  [("RQ1 (this deck)", "Is future reuse valuable, and can the cache get it online? Gate 1: an oracle beats the best online policy by ≥ 5 points. Gate 2: an online method keeps ≥ 50% of that gain."),
   ("RQ2", "Joint placement, retention and movement across DRAM and CXL. Is migration needed when placement at creation is good?"),
   ("RQ3", "Movement under interference: a safe DRAM write budget, budget-gated admission, coordination of bulk writers. RQ1 supplies the value model that RQ2 and RQ3 use.")],
  "docs/research/CHARTER.md (gates fixed 2026-10-17, before the experiments)  ·  setting of all trace studies: Mooncake conversation and tool-agent traces, Llama-3.1-8B blocks of 64 MiB, host cache 200 GiB = DRAM 64 + CXL 136",
  "Research direction (fixed 2026-10-17): reuse- and interference-aware unified DRAM/CXL memory management. Primary application: the KV cache of LLM "
  "serving (vLLM + LMCache); secondary: checkpoint staging. The three research questions are listed on the slide; this deck is only about RQ1. The "
  "figure shows the setting: the serving engine creates KV blocks for every request; a host cache of DRAM and CXL (one pool, each block in one tier) "
  "stores them; a block is later read again (a hit saves the recompute) or never (its write and its capacity were wasted). In the public Mooncake traces "
  "76% (chat) and 78% (tool agent) of all blocks are never read again. The quantitative gates were written into the charter before the first experiment "
  "and were not changed afterwards."),

S("LRU stores every block and evicts the oldest; an oracle stores only blocks with a future read",
  "Why this matters: reuse distance = the data that arrives between two uses of a block. A hit needs a reuse distance below the capacity; dead blocks inflate it for everyone.",
  ["Trace analysis"], "f02_lru_vs_oracle",
  [("Toy example, 2 slots", "LRU gets 0 of 2 reuses: block C, never read again, pushes A out. The oracle skips C and gets both hits with one write less."),
   ("Real traces", "76–79% of blocks are never read again, yet LRU writes and keeps them all. Only 19% (chat) and 65% (tool agent) of reuses fit in a 200 GiB LRU stack."),
   ("Timing", "The median gap between two uses of a chat block is 114 s. A 200 GiB cache turns over in about 60 s. Most reused blocks leave before their second use.")],
  "experimental_results/2026-10-17-kv-reuse-oracle-study/characterization-*.json (trace characterization, 8B blocks)",
  "Two concepts for the rest of the deck. Reuse distance: how much other data arrives between two uses of the same block; with LRU a block hits only if "
  "its reuse distance is below the cache capacity. Future reuse: whether and when a block is read again at all. The toy example shows why the oracle's "
  "advantage is admission rather than eviction order: with two slots, LRU must store C and lose A, while an oracle that knows C is dead keeps A and B. "
  "The right panel shows that the real traces are dominated by such C blocks: three quarters of all blocks are never read again, and because they fill "
  "the cache, only 19% of the chat reuses fit within 200 GiB of LRU stack. The median reuse gap (114 s on chat) is about twice the cache turnover (60 s), "
  "so LRU evicts most reused chat blocks before their second use."),

S("An oracle that knows future reuse serves 80% / 94% of reuses where LRU serves 17% / 65%: Gate 1 passes",
  "Why we did it: to measure the most that future reuse information can be worth to a 200 GiB DRAM + CXL cache before we try to predict any of it.",
  ["Oracle", "Trace-driven simulation"], "f03_oracle",
  [("Method", "Exact replay of the Mooncake traces in a capacity model, scored on the second half. The oracle (Belady's MIN with bypass) never stores a block without a future read."),
   ("Result", "+62 points (chat) and +29 points (tool agent) of reuse hits over the best online policy; 26–27% fewer recomputed tokens; 82–83% fewer bytes written into host memory."),
   ("Mechanism", "The oracle does not evict better among live blocks. It never stores dead ones, so live blocks get about 4× the capacity. Seeing 300 s ahead gives 94% of its gain.")],
  "experimental_results/2026-10-17-kv-reuse-oracle-study/oracle-8b-capacity.csv, oracle-8b-capacity-online.csv (2026-10-17)",
  "The first experiment of the charter. We replay the real traces exactly (every request, its block hashes and timestamps) in a capacity-only model: a "
  "block is a hit when it is resident at access time; stores complete at once; no bandwidth or interference enters, so this is the ceiling of the "
  "information, not a system prediction. Baselines: CXL-first with LRU over 136 GiB, a static split of new blocks between the tiers with LRU per tier, "
  "one global LRU over 200 GiB, and segmented LRU (the best online policy we found). The oracle serves 80% of the chat reuses and 94% of the tool-agent "
  "reuses; LRU-type policies serve 17% and 65%. The gain is worth more than five times the capacity: the oracle at 200 GiB beats LRU at 1 TiB. Almost all "
  "of the gain comes from not storing the 76–79% of blocks that are never read again (host writes fall from 18 TB to 3 TB in the test half); this is also "
  "why the write side of the result matters for RQ3. Gate 1 passes on all three traces. Limits: capacity-only model, three traces (one synthetic), one "
  "block size and capacity from the earlier campaigns."),

S("No feature known when a block is created separates the 24% that will be reused from the 76% that will not",
  "Why we did it: if creation-time features predicted reuse, the cache could skip dead blocks at admission, which is exactly where the oracle's gain comes from.",
  ["Trace analysis", "Trace-driven simulation"], "f04_prediction",
  [("Features tested", "Position in the request, request length, continuation depth, new blocks, turns so far, time since the previous turn, prompt and answer length. Every bucket stays within 10–35%."),
   ("Rules built on them", "Segmented LRU, reactive promotion, an admission filter on the fitted probability, eviction by past-use count: at best 6% of the oracle's gain. Gate 2 fails."),
   ("Why it fails", "The strong signals (a past reuse, 300 s idle) appear after ~150 s; the cache turns over in ~60 s. An online model confirms it: precision for new blocks 1.2–1.4× random.")],
  "experimental_results/2026-10-17-kv-reuse-oracle-study/characterization-*.json, oracle-8b-capacity*.csv  ·  2026-10-18-rq1b-history-learning/*-predict.json (chronological online models)",
  "Second step: predict the oracle's decision from what the cache can see when a block is created. The left panel plots, per feature bucket, the share "
  "of new blocks that are read again later (test half). All buckets lie in a narrow band around the base rate; the one informative bucket, continuation "
  "depth 8–31, says that deep blocks of a continuing conversation are rarely reused (6–10%), and that is the lever the admission study on slide 7 uses. "
  "The right panel shows the online rules we tried on top of these features; none recovers more than 6% of the oracle's gain. The signals that do "
  "predict reuse are historical: a block that was reused once will be reused again with 42–45%, five times with 88–98%, and a block idle for 300 s is "
  "dead with 96–98%. But at 200 GiB the cache turns over every ~60 s while the median first reuse comes after ~150 s, so most blocks are evicted before "
  "they can show either signal. The history-learning round (2026-10-18) repeated the test with strictly chronological, continually updated models (per "
  "root, per context, online logistic regression): average precision for new blocks 0.045–0.051 against a 0.037 base rate at a 60 s horizon. Gate 2 "
  "fails for block-level prediction; the synthetic trace is predictable from request features but it is synthetic."),

S("Application hints pay only when the cache turns over faster than the agent re-reads its context",
  "Why we did it: the application may know what the cache cannot see: that a chat session will continue, or that an agent loop will call the model again.",
  ["Oracle", "Trace-driven simulation", "Real-system measurement"], "f05_hints",
  [("Session hints (simulation)", "A perfect 'session continues' hint is an oracle: 54% / 42% of the block oracle's gain. The signals a chat system has (idle time, an end event 60 s late) give 0%."),
   ("Agent events (real runs)", "OpenAI Agents SDK on vLLM + LMCache: continue / end are known at once and block-exact. But LRU already serves 96.5–98.6% of reuses when the cache holds the live contexts."),
   ("When they pay", "Only when the cache turns over within ~2 reuse horizons but still holds the live set: 90% of the gain (+7 points). Elsewhere 0–4%; a 200 GiB tier with ≤ 64 agents is outside.")],
  "2026-10-17-kv-session-hint-study/session-hints-8b-200GiB.csv  ·  2026-10-17-rq1b-agent-runtime-validation (real runs)  ·  2026-10-17-rq1b-reuse-horizon/lt-k16-l1g-bg2-churn0-replay.csv (16 agents, real tools, real background churn)",
  "Third step: information the application holds. Session hints (left, trace simulation at 200 GiB): reuse is 89–95% within a session and the next turn "
  "re-reads about four fifths of the previous turn's blocks, so a perfect 'continues' hint recovers about half of the block oracle's gain (74% when bounded "
  "to 300 s). Everything a chat client could really provide is worth nothing: session idle time equals LRU, and an end-of-session event that arrives 60 s "
  "late comes after LRU evicted the blocks anyway. An end event with no delay (53%) is realistic only for agent frameworks. We therefore ran real agents: "
  "the OpenAI Agents SDK loop on vLLM 0.31 + LMCache 0.5.5 on the RTX 4060 Ti (Qwen2.5-3B-AWQ; 400 tasks; 8 and 16 agents; short synthetic tools, then "
  "real pandas/pytest tools with real background chat traffic on the same server). Verified: the runtime knows continue / end at the end of every LLM "
  "call; on continue 100% of the context is re-read 1.3–3 s later; on end 84–85% of the task's private chunks are dead but the end event arrives 0.4 s "
  "after the last KV write, so it cannot cancel a write unless stores are deferred (LMCache's lazy offload crashed, so the −49% write saving stays "
  "simulated). The right panel replays the real trace with the real events: at 24–32 blocks (1.3–1.7× the live working set) the continue event recovers "
  "90% of the oracle's gain; from 48 blocks on LRU already serves 99% and the events add nothing. Over 144 replay settings the median recovery is 0%. A 200 GiB tier serving up to 64 such agents sits in the LRU regime, where the signal is worth nothing; that placement is an ESTIMATE from the public agent traces (horizons 6–11 s p50, prompts 20–60k tokens), not a measurement. "
  "Gate 2 is PARTIAL for agents: information PASS, hit value only under capacity pressure. Recommendation kept: carry the lifecycle event as a cheap "
  "release / deferred-store interface for RQ3, not as a hit-rate predictor."),

S("Miss cost and reuse history add nothing to eviction that LRU does not already do",
  "Why we did it: two more ways to rank what to evict: keep the blocks that cost most to recompute, or keep the blocks whose own history predicts a re-read.",
  ["Real-system measurement", "Trace-driven simulation"], "f06_cost_retention",
  [("Miss cost (measured)", "Recompute: 0.134 ms per token. A load from DRAM or the CXL devdax: ≤ 1/15 of that, tiers equal. A hole kills the suffix, so vLLM / LMCache already evict tails first."),
   ("Cost-aware retention", "A cost tie-break among the least-recently-used blocks gives −1 to 0% of the oracle's gain. A pure cost ranking evicts the shared system prompt: zero hits. SLRU + cost = SLRU."),
   ("History-based retention", "A block's own history predicts its next use well (precision 0.75 / 0.99 vs base 0.20 / 0.65), but LRU already keeps those blocks. Learned retention ranking: 0–2%.")],
  "2026-10-18-rq1-misscost/misscost-summary.json (TTFT microbenchmark, 3 repetitions), mc-*-tail-replay.csv  ·  2026-10-18-rq1b-history-learning/mc-*-th0-replay.csv, *-predict.json",
  "Fourth step: maybe the value of a block is not only whether it is reused but what a miss costs, or maybe history helps retention even if it cannot "
  "help admission. Miss cost was measured on the real system (left): time to first token for cold prompts, prompts served from vLLM's GPU prefix cache, "
  "and prompts served from LMCache's L1 placed in DRAM or on the CXL device (devdax). Recompute grows with the prompt (0.134 ms per token, +7% per 1k "
  "position); a load from either tier is below the measurement floor, at most 1/15 of the recompute, and DRAM and CXL are indistinguishable. A changed "
  "token in the middle of a prompt makes the cached suffix useless (measured: a hole at half the prompt costs the same as a clean half prefix), which is "
  "why vLLM and LMCache already evict a request's tail before its head. The right panel shows the retention policies at 200 GiB: a cost-aware tie-break "
  "(−1 to 0%), SLRU plus cost (= SLRU), and three history-based rankings from the 2026-10-18 round: decayed popularity, the learned class hit rate and "
  "the per-root rate used for retention only (0–2%). The prediction itself is good: once a block has been used twice, count × last-interval tables reach "
  "average precision 0.75 on chat and 0.99 on the tool-agent trace, stable over time. It does not help because the blocks it identifies are the ones LRU "
  "keeps anyway; the blocks LRU loses are needed ~108 s after an eviction that happens ~39 s after their last use, and no ranking among resident blocks "
  "can hold them 3.5× longer while new blocks pour in. Conclusion: the tier a block lives in does not change its miss cost, and the value input to RQ2 "
  "stays recency / frequency plus chain structure plus the agent lifecycle events."),

S("Learning which new blocks not to store beats SLRU on both real traces and cuts host writes by two thirds",
  "Why we did it: the oracle's lever is admission. History cannot say which new block will be reused, but the cache's own hits and evictions can say which classes never are.",
  ["Trace-driven simulation", "In progress"], "f07_admission",
  [("Mechanism", "Each class (root × position × continuation depth) keeps a decayed hit-before-eviction rate from the cache's own hits and evictions. New blocks of a class below 0.15 are not stored."),
   ("Result at 200 GiB", "Hit share 0.18 → 0.27 (chat), 0.65 → 0.69 (tool agent): 14–16% of the oracle's gain. Writes 18 TB → 4–6 TB (−66 to −78%). Learned rule: skip deep blocks of continuations."),
   ("Limits", "Synthetic trace hurt (−9 to −21%); threshold hand-set; a depth bug found on 2026-10-20 made the class (root, position) in effect. The corrected re-run with fixed rules is running.")],
  "2026-10-18-rq1b-history-learning/mc-*-th0.15-replay.csv (closed 2026-10-20)  ·  2026-10-20-rq1b-admission-study (active, not yet reported)",
  "Fifth step, and the first positive online result. The idea inverts the prediction problem: instead of predicting which new block will be reused, let "
  "the cache label its own decisions. Every admitted block becomes a sample of its class: positive at its first hit, negative when it is evicted without "
  "a hit. The class is (root prefix, position bucket, continuation-depth bucket); a decayed rate with a Beta prior falls back to 'admit' for new or "
  "rare classes. When a class's rate drops below 0.15 after 50 samples, new blocks of that class are bypassed (never stored), except the first block of "
  "a request. The replay uses prefix-aware scoring (a chunk counts only while every earlier chunk of its request hit) and LMCache's tail-first eviction "
  "order, the same for all policies; the threshold was chosen on the agent traces and applied unchanged. At 200 GiB the usable-prefix hit share rises "
  "from 0.178 (LRU) / 0.209 (SLRU) to 0.273–0.274 on chat and from 0.648 / 0.661 to 0.689–0.691 on the tool-agent trace, while 4–6 TB instead of 18 TB "
  "are written into host memory; at 100 GiB 12–14% of the oracle's gain, at 400 GiB 3–6% (the gain shrinks when the cache stops being under pressure). "
  "Per-access audit: the avoided misses are leading blocks of conversations (positions 0–7, 60–300 s old) that now survive until the next turn; the new "
  "misses are the 5–10% of deep continuation blocks that would have been reused. Negative results kept: the online logistic version is unstable; "
  "retention-only learning gives nothing (previous slide); the synthetic trace, whose reuse is not class-structured, loses hits. Two caveats found on "
  "2026-10-20: the depth term of the class was computed after the request's own earlier blocks were marked seen, so the class was effectively (root, "
  "position); and the learned rule resembles a fixed rule ('do not store beyond position 8 of a continuation'). A corrected re-run with four static "
  "admission rules, a feedback-correctness audit (censored feedback, exploration, delayed labels, frozen statistics), mixed traces and the two real "
  "agent traces is running tonight; its report is not written yet, so no number from it is on these slides."),

dict(kind="table", title="RQ1: future reuse is worth a lot, but only its negative side is learnable online",
     why="Gate 1 PASS (value). Gate 2 PARTIAL (online availability): 14–16% of the oracle's gain at 200 GiB; the agent continue event reaches 50–90% only under capacity pressure.",
     tags=["Oracle", "Trace-driven simulation", "Real-system measurement"],
     header=["Approach", "Why we tried it", "Main result", "What we learned"],
     rows=[["Oracle (Belady with bypass)", "Upper bound of future information", "80 / 94% of reuses vs 17 / 65% for LRU; host writes −82%", "The value is large. It comes from not storing dead blocks, not from better eviction."],
           ["Block-level prediction", "Skip dead blocks when they are created", "Features move reuse only within 10–35%; online rules ≤ 6% of the gain", "Creation-time features carry no signal; the strong signals arrive after eviction."],
           ["Session hints", "A chat app may know the session continues", "Perfect hint 54 / 42% (an oracle); real chat signals 0%", "Chat has no early signal. False positives are the costly error."],
           ["Agent lifecycle events", "An agent loop knows continue / end", "Real events exact and timely; 0–4% at normal capacity, 90% in the pressure band", "Pays only when the cache turns over within ~2 reuse horizons; it is a release interface."],
           ["Miss-cost-aware retention", "Keep the blocks that cost most to recompute", "−1 to 0% of the gain; DRAM and CXL loads equal; tail-first already in production", "Miss cost is prefix-structural and already exploited; the tier does not change it."],
           ["History-based retention", "Past reuse predicts the next reuse", "Average precision 0.75 / 0.99, but 0–2% of the gain", "What history predicts well, LRU already keeps."],
           ["Learned admission", "Learn which classes never hit before eviction", "14–16% of the gain; writes −66 to −78%; first online method beating SLRU", "Learning what not to store works. New-block reuse stays unpredictable."]],
     closing="Open question for this week: how much of the admission gain comes from online learning rather than a simple fixed rule, such as 'do not store blocks beyond position 8 of a continuation'? "
             "The corrected re-run with fixed-rule baselines is running (2026-10-20); the deck will carry its numbers once the report is written.",
     source="All rows: docs/experiments/2026-10-17-kv-reuse-oracle-study.md, 2026-10-17-kv-session-hint-study.md, 2026-10-17-rq1b-*.md, 2026-10-18-rq1-misscost-feasibility.md, 2026-10-18-rq1b-history-learning.md",
     notes="Summary of RQ1 after seven rounds. The ordering is the reasoning chain: the oracle showed the value and located it in admission; creation-time "
           "prediction failed, which pointed at the application; the application's signals turned out to be oracle-only for chat and condition-bound for "
           "agents; miss cost and retention learning were ruled out as alternative value models; and the learned admission filter, which learns the negative "
           "class rather than predicting reuse, is the one online method with a real gain. Gates: Gate 1 PASS, Gate 2 PARTIAL (threshold unchanged). What RQ1 "
           "hands to RQ2/RQ3: a fixed, cheap value model (recency / frequency, chain structure, agent lifecycle events, learned admission classes), a uniform "
           "miss cost per chunk across tiers, and the fact that the write saving of admission is of the order of the oracle's own (−72% vs −82%). Open "
           "question: how much of the admission gain is learning and how much is a fixed rule. Status on the evening of 2026-10-20: the re-run with the "
           "corrected class, four static rules, the feedback audit, mixed traces and the real agent traces is executing; the 200 GiB replays have finished "
           "but the report (2026-10-20-rq1b-admission-study.md) is not written and nothing has been checked. PRELIMINARY, unreviewed, from the raw logs "
           "g-conversation-c3200.log / g-toolagent-c3200.log: on the chat trace the fixed rule 'bypass position ≥ 8' gives 0.273, the same as the 2026-10-18 "
           "learned policy, and the corrected learned class 0.314; on the tool-agent trace that fixed rule is harmful (0.525 vs LRU 0.648) while the learned "
           "class gives 0.720. If this holds after review, the answer is: a fixed rule captures the chat gain, learning is needed to avoid harm on other "
           "workloads and adds a few points on top. Treat these three sentences as a note for the discussion, not as a result."),
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
    widths = [1.9, 2.6, 3.75, 4.08]
    for j, cw in enumerate(widths): tbl.columns[j].width = Inches(cw)
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
            add_text(s, 0.9, 2.0, 11.5, 1.6, sl["title"], 34, bold=True, color=NAVY, anchor=MSO_ANCHOR.BOTTOM)
            add_text(s, 0.9, 3.7, 11.5, 0.8, sl["subtitle"], 19, color=INK)
            add_text(s, 0.9, 4.7, 11.5, 0.7, sl["meta"], 12.5, color=MUTED)
            xx = 0.9; add_text(s, xx, 6.3, 2.2, 0.3, "Evidence tags on each slide:", 10, color=MUTED, anchor=MSO_ANCHOR.MIDDLE); xx += 2.2
            for t in ["Oracle", "Trace-driven simulation", "Real-system measurement", "Trace analysis", "Framing", "In progress"]:
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
            ptext(ax, 0.9, 2.0, 11.5, 1.6, sl["title"], 34, bold=True, color="#" + NAVY, va="top", warn=f"s{n} title"); ptext(ax, 0.9, 3.7, 11.5, 0.8, sl["subtitle"], 19, warn=f"s{n} subtitle")
            ptext(ax, 0.9, 4.7, 11.5, 0.7, sl["meta"], 12.5, color="#" + MUTED, warn=f"s{n} meta")
            xx = 0.9; ax.text(xx, H - 6.45, "Evidence tags on each slide:", fontsize=10, color="#" + MUTED, va="center"); xx += 2.2
            for t in ["Oracle", "Trace-driven simulation", "Real-system measurement", "Trace analysis", "Framing", "In progress"]:
                ww = chip_w(t); pbox(ax, xx, 6.3, ww, 0.3, "#" + TAGS[t]); ax.text(xx + ww / 2, H - 6.45, t, ha="center", va="center", fontsize=9); xx += ww + 0.1
        elif sl["kind"] == "table":
            ptext(ax, 0.5, 0.22, 12.33, 0.98, sl["title"], tsize(sl["title"]), bold=True, color="#" + NAVY, va="middle", warn=f"s{n} title")
            ptext(ax, 0.5, 1.18, why_w(sl["tags"]), 0.52, sl["why"], 11.5, color="#" + MUTED, italic=True, warn=f"s{n} why"); pchips(ax, sl["tags"])
            widths = [1.9, 2.6, 3.75, 4.08]; rows = [sl["header"]] + sl["rows"]; rh = 4.05 / len(rows); y = 1.75
            for i, row in enumerate(rows):
                x = 0.5
                for j, txt in enumerate(row):
                    pbox(ax, x, y, widths[j], rh, "#" + (NAVY if i == 0 else ("FFFFFF" if i % 2 else TINT)), ec="#" + LINE, r=0)
                    ptext(ax, x + 0.06, y + 0.04, widths[j] - 0.12, rh - 0.08, txt, 10.5, bold=(i == 0 or j == 0), color="white" if i == 0 else "#" + INK, va="middle", warn=f"s{n} table r{i} c{j}")
                    x += widths[j]
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
        f.write("# RQ1 progress deck 2026-10-20 — outline\n\n| # | slide title | why | evidence | figure |\n|---|---|---|---|---|\n")
        for n, sl in enumerate(SLIDES, 1):
            f.write(f"| {n} | {sl['title']} | {sl.get('why', '—')} | {', '.join(sl.get('tags', []))} | {sl.get('fig', 'table')} |\n")
        f.write("\nEach content slide: one conclusion-style title, one 'why we did it' line, one matplotlib figure (or the summary table), three short statements, the data source, speaker notes.\n")
    print("wrote outline.md")

if __name__ == "__main__":
    build_pptx(DECK); build_preview(); write_outline()
