# 2026-10-17 — RQ1-B: reuse horizon vs cache residence — under realistic capacity pressure and long reuse intervals, do real agent lifecycle signals substantially improve KV reuse over strong online baselines?

**STATUS: CLOSED 2026-10-17.** The last focused validation of RQ1-B. Evidence types, each labelled below:
**PUBLIC TRACE** (real timestamps of LLM calls in 1,781 agent sessions, Exgentic/agent-llm-traces on Hugging Face),
**REAL APPLICATION** (OpenAI Agents SDK loop with tools that really execute — pandas scans of 1.5M–6M-row CSV files, a
13-test pytest suite, model-written Python — on vLLM 0.31 + LMCache 0.5.5, c28's 4060 Ti; plus the short-tool runs of
the previous round, whose tool latencies were synthetic sleeps), **REAL BACKGROUND CHURN** (the Mooncake conversation
trace replayed on the same server at 0.05×), **TRACE SIMULATION on the real traces** (capacity / churn sweeps with the
real events; the extra churn in those sweeps is **SYNTHETIC** and labelled), **ORACLE** (Belady with bypass).
Previous rounds: `2026-10-17-kv-reuse-oracle-study.md`, `2026-10-17-kv-session-hint-study.md`,
`2026-10-17-rq1b-application-reuse-signals.md`, `2026-10-17-rq1b-agent-runtime-validation.md`.
Raw: `experimental_results/2026-10-17-rq1b-reuse-horizon/` (`public/` statistics and figure of the public trace;
`real/<tag>-*` the long-tool runs; `*-replay.csv`, `regime.csv`, figures). Code: `scripts/agent_trace_public_stats.py`,
`benchmarks/agent/agent_tasks_lt.py` (real-tool workload), `benchmarks/agent/run_chain_lt.sh`, `scripts/kv_agent_replay.py`
(now with `--churn`, `event_cont`, pressure metrics and regime variables), `scripts/kv_agent_regime.py`.

## The three quantities
- **Reuse horizon H:** previous use → next use of a task's own KV chunks (shared prefixes excluded).
- **Cache residence T_res:** write → eviction under LRU at the given capacity and production rate; T_res ≈ C / P where
  P is the total chunk production rate (agents plus any other tenant).
- **Signal lead L:** continue decision → next lookup (= tool time plus framework overhead); the end decision has no lead
  for the write (it comes 0.4 s after it) and a lead of one residence time for the eviction.
LRU loses a live block when H > T_res; a continue signal can protect it when L ≥ 0 (it always is) and the live working
set W_live fits the capacity. So the regime of interest is **W_live < C < P · H**.

## Task A — realistic reuse horizons (Deliverable 1)
### A1. PUBLIC TRACE: Exgentic/agent-llm-traces (CDLA-Permissive-2.0; downloaded 2026-10-17, 39 parquet shards)
1,781 sessions, 38,052 LLM calls; harnesses claude_code (829 sessions), tool_calling (430), smolagents_code (315),
openai_solo (114), tool_calling_with_shortlisting (82); models Claude Opus 4.5, Gemini 3 Pro, GPT-4.1, Kimi K2.5,
DeepSeek V3.2; benchmarks AppWorld, BrowseComp-Plus, SWE-bench, τ²-bench airline / retail / telecom. Each LLM call is a
span with start and end time, input and output tokens and finish reason. **Limit:** in most harnesses the span ends at
request submission (63% of spans are shorter than 10 ms), so model latency and tool time cannot be separated; the
start-to-start interval of consecutive calls of a session — the **reuse horizon of the previous prompt's KV** — is robust
and is what the table reports. 12.6% of end-to-start gaps are negative (overlapping spans: parallel calls or sub-agents).

| benchmark | sessions | calls / session p50 / p90 | horizon p10 / p50 / p90 / p99, s | > 10 s | > 30 s | prompt tokens p50 / p90 | growth per step p50 |
|---|---|---|---|---|---|---|---|
| AppWorld | 406 | 14 / 42 | 6.1 / 11.0 / 35.5 / 64 | 55% | 13% | 54.8k / 121k | 274 |
| BrowseComp-Plus | 133 | 19 / 50 | 4.4 / 6.1 / 20.6 / 52 | 30% | 5% | 59.6k / 130k | 3117 |
| SWE-bench | 391 | 35 / 84 | 1.4 / 7.2 / 25.1 / 57 | 35% | 7% | 25.0k / 46k | 359 |
| τ²-bench airline | 196 | 7 / 15 | 0.3 / 6.0 / 19.8 / 53 | 29% | 5% | 19.0k / 27k | 249 |
| τ²-bench retail | 469 | 8 / 15 | 1.3 / 6.4 / 29.1 / 56 | 34% | 9% | 19.2k / 28k | 240 |
| τ²-bench telecom | 186 | 15 / 34 | 1.8 / 6.2 / 19.6 / 49 | 28% | 5% | 4.0k / 29k | 109 |
| all | 1781 | — | — / 7.9 / 27.1 / — | 31% | — | — | — |

So in real agent sessions the previous prompt's KV is re-read after **6–11 s at the median, 20–36 s at p90, about
50–60 s at p99**; prompts are **20k–60k tokens** (80–230 chunks of 256 tokens; for an 8B model 2.5–7.5 GB of KV per
agent) and grow by ~1 chunk per step. (fig-public-agent-gaps)

### A2. PUBLIC TRACE: Mooncake tool-agent and conversation traces (Phase 1 characterization, 200 GiB setting)
Creation → second use p50 123 s (tool agent) / 147 s (conversation); next use within 60 s for 69% / 28% of reuses;
LRU turnover at 200 GiB ≈ 1 min (52 new blocks/s); the traces carry no tool or session timing.

### A3. REAL APPLICATION: tool durations and horizons measured on c28 (this round's long-tool runs vs the previous short-tool runs)
| quantity (p50 / p90) | short tools, 8 agents (`k8-l1g`, previous round) | short tools, 16 agents (`k16-l1g`) | real tools, 8 agents (`lt-k8-l1g`) | real tools, 16 agents (`lt-k16-l1g`) |
|---|---|---|---|---|
| tool execution | 1.09 / 1.50 s (**synthetic sleeps** 1.5 / 1.0 / 0.3 s) | 1.08 / 1.51 s (synthetic) | run_checks 8.0 / 13.3 s, profile 2.7 / 4.2 s, aggregate 2.5 / 4.0 s, python_exec 0.4 / 2.6 s (**measured**) | run_checks 9.0 / 14.8 s, profile 3.1 / 4.7 s, aggregate 2.8 / 4.3 s, python_exec 0.5 / 2.9 s (measured) |
| continue decision → next call's lookup (signal lead L) | 1.30 / 1.62 s | 1.25 / 1.61 s | 2.85 / 9.2 s | 3.09 / 10.6 s |
| reuse horizon H of a task's own chunks | 1.4 / 2.3 s | 1.4 / 2.3 s | 3.1 / 4.9 s | 3.2 / 5.2 s |
| LLM calls per task | 3 / 6 | 3 / 6 | 2 / 4 (9 of 200 hit max_turns) | 2 / 4 (9 of 200) |
| live working set W_live (chunks, mean / p90) | 28 / 33 | 57 / 65 | 13 / 18 | 21 / 28 |
| agent KV production P (chunks/s) | 3.2 | 4.9 | 0.8 | 1.4 |
| REAL LRU residence at 1 GB (write → eviction) | 22 / 28 s | 12 / 16 s | 69 / 83 s | 38 / 49 s |
| REAL reuse-hit share in LMCache at 1 GB | 0.971 | 0.965 | 0.986 | 0.972 |

The real tools (pandas scans of 1.5M–6M-row files, a 13-test pytest suite, model-written Python) take 2.5–15 s and
push the continue lead to 3 s (p50) / 10 s (p90) and the horizon to 3–5 s — the same order as the public trace's
horizons (6–11 s p50, 20–36 s p90). Two things the local runs cannot reproduce: the public trace's prompt sizes (20k–60k
tokens; here 1–2k, so W_live is 13–57 chunks and P is 1–5 chunks/s) and its session lengths (7–35 calls; here 2–6).
These are the known limits of the 4060 Ti setup; the replays below therefore sweep capacity relative to W_live and add
churn, rather than claiming absolute capacities.


## Task B — reuse horizon vs cache capacity (Deliverable 2; TRACE SIMULATION on the real traces, fig-regime, fig-regime-2d)
Each real trace (the LLM calls with their chunk hashes, lookup times and the recorded continue / end decisions) is
replayed through the capacity-only simulator at 9 capacities (24–384 chunks = 0.23–3.6 GB) and 4 background-churn
levels (0, 2, 5, 10 never-reused chunks/s from other tenants — **SYNTHETIC**, uniformly spaced; the `-bg` runs below
supply REAL churn). Every policy sees the same request stream, capacity and data-availability times; scoring covers the
agent accesses of the second half of the trace. Regime variables measured on each trace: live working set W_live (chunks
of unfinished tasks, sampled every second), agent production P (new chunks/s), own-chunk reuse horizon H, and the LRU
residence T_res (write → eviction, p50) at each capacity. "LRU evictions before reuse" is the share of LRU's evictions
that precede a later use of the block — the direct measure of "LRU loses data it will need".

Capacity relative to the live working set defines the three scenarios the brief asks for: **no pressure** (C ≥ 2.5
W_live: residence 15–100 s, 1–6% of evictions premature), **moderate pressure** (1 ≤ C/W_live < 2.5: residence
3–30 s, 8–16% premature) and **heavy pressure** (C < W_live: residence ≤ 3 s, 25–38% premature — the live contexts do
not fit). For reference, 8 / 16 concurrent agents of the 3B model with 1–2k-token contexts have W_live = 13–57 chunks
(0.1–0.5 GB); the public workloads' 20k–60k-token contexts would make W_live 1.2–3.7k chunks per 16 agents on an 8B
model (37–120 GB), see Task E.

**short tools, 16 agents, no churn (k16-l1g)** — W_live 57 chunks (p90 65), production 4.9 agent + 0.0 real background + 0.0 synthetic churn chunks/s, reuse horizon of own chunks p50 1.4 s / p90 2.3 s

| capacity (C / W_live) | LRU residence | LRU evictions before reuse | LRU dead occupancy | lru | slru | ttl30 | event_cont | event_end | event_both | oracle |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 = 0.23 GB (0.4) | 1.5 s | 53% | 39% | 0.867 | 0.867 (-1) | 0.867 (+0) | 0.914 (+171, 75% of reuses under protection) | 0.903 (+129) | 0.924 (+204) | 0.959 (+332) |
| 32 = 0.30 GB (0.6) | 3.0 s | 38% | 47% | 0.928 | 0.924 (-14) | 0.928 (+0) | 0.951 (+84, 75% of reuses under protection) | 0.951 (+84) | 0.953 (+90) | 0.970 (+152) |
| 48 = 0.45 GB (0.8) | 5.9 s | 22% | 59% | 0.959 | 0.958 (-4) | 0.959 (+0) | 0.960 (+4, 75% of reuses under protection) | 0.960 (+3) | 0.960 (+3) | 0.980 (+78) |
| 64 = 0.60 GB (1.1) | 8.6 s | 20% | 66% | 0.963 | 0.962 (-2) | 0.963 (+0) | 0.963 (+0, 75% of reuses under protection) | 0.962 (-3) | 0.962 (-3) | 0.986 (+82) |
| 96 = 0.91 GB (1.7) | 13.9 s | 18% | 74% | 0.968 | 0.967 (-3) | 0.968 (+0) | 0.968 (+0, 75% of reuses under protection) | 0.968 (+0) | 0.968 (+0) | 0.995 (+98) |
| 192 = 1.81 GB (3.4) | 30.5 s | 15% | 82% | 0.974 | 0.974 (+1) | 0.974 (+0) | 0.974 (+0, 75% of reuses under protection) | 0.974 (+0) | 0.974 (+0) | 1.000 (+95) |

**short tools, 16 agents, synthetic churn 5 chunks/s** — W_live 57 chunks (p90 65), production 4.9 agent + 0.0 real background + 5.0 synthetic churn chunks/s, reuse horizon of own chunks p50 1.4 s / p90 2.3 s

| capacity (C / W_live) | LRU residence | LRU evictions before reuse | LRU dead occupancy | lru | slru | ttl30 | event_cont | event_end | event_both | oracle |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 = 0.23 GB (0.4) | 1.0 s | 44% | 48% | 0.812 | 0.836 (+85) | 0.812 (+0) | 0.894 (+293, 74% of reuses under protection) | 0.835 (+84) | 0.903 (+326) | 0.958 (+524) |
| 32 = 0.30 GB (0.6) | 1.6 s | 35% | 53% | 0.873 | 0.865 (-30) | 0.873 (+0) | 0.933 (+213, 75% of reuses under protection) | 0.909 (+127) | 0.941 (+241) | 0.970 (+345) |
| 48 = 0.45 GB (0.8) | 3.1 s | 17% | 63% | 0.944 | 0.938 (-23) | 0.944 (+0) | 0.956 (+41, 75% of reuses under protection) | 0.951 (+24) | 0.953 (+31) | 0.980 (+128) |
| 64 = 0.60 GB (1.1) | 4.5 s | 13% | 70% | 0.957 | 0.956 (-3) | 0.957 (+0) | 0.959 (+5, 75% of reuses under protection) | 0.953 (-15) | 0.953 (-15) | 0.985 (+101) |
| 96 = 0.91 GB (1.7) | 7.4 s | 11% | 77% | 0.963 | 0.963 (+0) | 0.963 (+0) | 0.963 (+0, 75% of reuses under protection) | 0.953 (-34) | 0.953 (-34) | 0.995 (+116) |
| 192 = 1.81 GB (3.4) | 16.0 s | 9% | 86% | 0.969 | 0.969 (-2) | 0.969 (+0) | 0.969 (+0, 75% of reuses under protection) | 0.953 (-58) | 0.953 (-58) | 1.000 (+110) |

**real tools, 16 agents, no churn (lt-k16-l1g)** — W_live 21 chunks (p90 28), production 1.4 agent + 0.0 real background + 0.0 synthetic churn chunks/s, reuse horizon of own chunks p50 3.2 s / p90 5.2 s

| capacity (C / W_live) | LRU residence | LRU evictions before reuse | LRU dead occupancy | lru | slru | ttl30 | event_cont | event_end | event_both | oracle |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 = 0.23 GB (1.2) | 11.8 s | 11% | 66% | 0.993 | 0.993 (+0) | 0.993 (+0) | 0.996 (+3, 78% of reuses under protection) | 0.997 (+4) | 0.997 (+4) | 1.000 (+8) |
| 32 = 0.30 GB (1.5) | 16.4 s | 9% | 73% | 0.995 | 0.995 (+0) | 0.995 (+0) | 0.997 (+2, 78% of reuses under protection) | 0.997 (+2) | 0.997 (+2) | 1.000 (+6) |
| 48 = 0.45 GB (2.3) | 28.2 s | 6% | 82% | 0.997 | 0.997 (+0) | 0.997 (+0) | 0.997 (+0, 78% of reuses under protection) | 0.997 (+0) | 0.997 (+0) | 1.000 (+4) |
| 64 = 0.60 GB (3.1) | 39.8 s | 4% | 86% | 0.997 | 0.998 (+1) | 0.997 (+0) | 0.997 (+0, 78% of reuses under protection) | 0.997 (+0) | 0.997 (+0) | 1.000 (+3) |
| 96 = 0.91 GB (4.6) | 63.2 s | 1% | 90% | 0.999 | 0.999 (+0) | 0.999 (+0) | 0.999 (+0, 78% of reuses under protection) | 0.999 (+0) | 0.999 (+0) | 1.000 (+1) |
| 192 = 1.81 GB (9.2) | inf s | 0% | 92% | 1.000 | 1.000 (+0) | 1.000 (+0) | 1.000 (+0, 78% of reuses under protection) | 1.000 (+0) | 1.000 (+0) | 1.000 (+0) |

**real tools, 16 agents, synthetic churn 5 chunks/s** — W_live 21 chunks (p90 28), production 1.4 agent + 0.0 real background + 5.0 synthetic churn chunks/s, reuse horizon of own chunks p50 3.2 s / p90 5.2 s

| capacity (C / W_live) | LRU residence | LRU evictions before reuse | LRU dead occupancy | lru | slru | ttl30 | event_cont | event_end | event_both | oracle |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 = 0.23 GB (1.2) | 2.6 s | 13% | 71% | 0.946 | 0.951 (+6) | 0.946 (+0) | 0.988 (+44, 77% of reuses under protection) | 0.950 (+4) | 0.989 (+45) | 1.000 (+57) |
| 32 = 0.30 GB (1.5) | 3.8 s | 9% | 76% | 0.964 | 0.966 (+2) | 0.964 (+0) | 0.995 (+33, 77% of reuses under protection) | 0.976 (+13) | 0.996 (+34) | 1.000 (+38) |
| 48 = 0.45 GB (2.3) | 6.2 s | 4% | 82% | 0.990 | 0.990 (+0) | 0.990 (+0) | 0.996 (+7, 77% of reuses under protection) | 0.992 (+3) | 0.996 (+7) | 1.000 (+11) |
| 64 = 0.60 GB (3.1) | 8.8 s | 2% | 87% | 0.992 | 0.993 (+1) | 0.992 (+0) | 0.996 (+4, 77% of reuses under protection) | 0.992 (+0) | 0.996 (+4) | 1.000 (+8) |
| 96 = 0.91 GB (4.6) | 13.4 s | 2% | 91% | 0.994 | 0.995 (+1) | 0.994 (+0) | 0.996 (+2, 77% of reuses under protection) | 0.996 (+2) | 0.996 (+2) | 1.000 (+6) |
| 192 = 1.81 GB (9.2) | 28.4 s | 1% | 95% | 0.996 | 0.997 (+1) | 0.996 (+0) | 0.996 (+0, 77% of reuses under protection) | 0.996 (+0) | 0.996 (+0) | 1.000 (+4) |

Reading the tables (reuse-hit share; in brackets the hits gained over global LRU in the scored half, absolute):
- **No churn, any tool length:** at C ≥ W_live the oracle itself gains ≤ 3 points over LRU (short tools: the
  duplicate-prompt re-reads 30–60 s later, which no event announces; real tools: ≤ 0.7 points), and the events gain
  0–4 hits. LRU already holds every block that comes back within a residence time, and with H = 1.4–3.2 s and T_res =
  12–100 s everything does.
- **Heavy pressure (C < W_live):** LRU evicts live contexts (38% of evictions premature); the continue signal protects
  them: +84 … +213 hits (+2.3 … +6 points), 59–70% of the oracle's gain. The end signal alone recovers 5–37%.
- **Churn with real tools (the long-horizon case):** at C/W_live = 1.2–1.5 the residence falls to 2.6–3.8 s, i.e. the
  horizon of a real tool call (H = 3.2 s p50, 5.2 s p90), and LRU starts losing contexts (9–13% premature); the continue
  signal keeps 77% of the reuses under protection and recovers **77–87%** of the oracle's gain (+33 … +44 hits, +3.1 …
  +4.2 points). One capacity step further (C/W_live = 2.3, residence 6 s ≈ 2 H) the gain is +7 hits of +11; at 4.6 it
  is +2 of +6.
- **The end signal is never the useful one, and above the pressure band it is harmful:** it recovers at most 37% (heavy
  pressure) and its false positives (15% of a task's private chunks are read again by a later identical prompt) cost
  15–66 hits when there is room (−15 … −67% of the gain); session TTL equals LRU everywhere; SLRU is within ±1%.

### The bands, over all 144 replay settings (4 traces × 4 churn levels × 9 capacities)
| C / W_live band | points | LRU evictions before reuse (median) | H / T_res (median, range) | oracle − LRU (median, pts) | continue: share of gain min / median / max | continue: absolute median (max), pts | end+continue: share median (min) | end only: share median (min) |
|---|---|---|---|---|---|---|---|---|
| C < 0.7 W_live (capacity below the live set) | 8 | 38% | 1.14 (0.48–1.78) | 12.2 | 51 / 57 / 63% | +6.9 (+8.7) | 65% (54%) | 37% (5%) |
| 0.7–1.0 | 8 | 25% | 0.50 (0.24–1.17) | 4.4 | 5 / 51 / 70% | +2.2 (+11.0) | 46% (-6%) | 22% (-6%) |
| 1.0–1.5 | 12 | 16% | 0.46 (0.17–2.02) | 2.8 | 0 / 38 / 77% | +0.8 (+6.2) | 37% (-30%) | 4% (-30%) |
| 1.5–2.5 | 32 | 8% | 0.28 (0.07–1.70) | 3.0 | -1 / 0 / 93% | +0.0 (+7.4) | 0% (-48%) | 0% (-48%) |
| 2.5–5 | 32 | 6% | 0.13 (0.03–0.78) | 2.6 | 0 / 0 / 86% | +0.0 (+2.3) | 0% (-67%) | 0% (-67%) |
| > 5 (no pressure) | 52 | 1% | 0.05 (0.00–0.37) | 0.4 | 0 / 0 / 57% | +0.0 (+0.4) | -25% (-400%) | -25% (-300%) |

(Share of the oracle's gain over global LRU; "end+continue" and "end only" minima show the cost of the end signal's
false positives when there is no pressure.)

### REAL background churn (the `-bg2` runs: the Mooncake conversation trace replayed on the same server, de-quantized to steady arrivals)
With 3.2 chunks/s of real foreign traffic beside 8 agents producing 0.7 chunks/s, the measured LRU residence at 1 GB
falls from 69 s to 12.6 s and the real reuse-hit share from 0.986 to 0.980. The replay of that trace (no synthetic
churn) reproduces the band: at C / W_live = 1.9–2.5 the residence is 3.8–4.4 s against a 3.2 s horizon, LRU loses
16–21% of its evictions prematurely and drops to 0.921–0.937, and the **continue signal recovers 90–91% of the oracle's
gain (+64 … +81 hits, +5.7 … +7.1 points, 75% of the reuses under protection)**; SLRU recovers 56–64%; the end signal 0%.
One step up (C / W_live = 3.8, residence 7.5 s ≈ 2.3 H) the oracle's gap is 0.5 points and the signal gains +2 hits.
With 16 agents and 4.4 chunks/s of real steady churn (`lt-k16-l1g-bg2`) the same band appears at C / W_live = 1.3–1.7
(residence 3.7–3.8 s, horizon 3.6 s): LRU 0.904–0.912, continue **0.978–0.984 (+80 … +83 of +98 … +106 hits, 78–82%, +7
points)**, SLRU 0.954–0.960 (53–56%); at C / W_live = 2.5–3.3 (residence 6–8 s ≈ 2 H) the signal still takes 67–71% of a
1.1–1.3-point gap; from 5 W_live on, nothing.



## Task C — strong baselines (Deliverable 3)
The tables above contain the full comparison: static split + LRU (B; not shown separately — it is 0.5–3 points below
global LRU at small capacities and equal above, as in the previous round), global LRU (C), SLRU 1/3 (±1% of LRU),
session TTL 10 / 30 s (= LRU everywhere: an idle-time rule never fires before LRU would have evicted anyway), real
lifecycle-aware retention (end only / continue only / both, with the recorded events at their recorded times), and
the block oracle (E). Metrics per setting in `*-replay.csv`: reuse-hit share, overall hit rate, recomputed tokens,
chunks written, evictions before reuse, live / dead occupancy, hits under continue-protection (coverage), dead-marked
blocks read again (end false positives), LRU residence. Absolute benefit: the continue signal's largest gains are +33
… +44 hits in a 267-call scored half (real tools, churn 5, C/W_live 1.2–1.5; recompute avoided 8–11k tokens = 2–3% of
the half's prompt tokens) and +84 … +241 hits in a 782-call half (short tools, C < W_live). The oracle's own gap over
LRU is ≤ 3 points everywhere except under heavy pressure (9–17 points), so a 50–90% recovery is worth 1–8 points of
reuse-hit share, and 0–0.7 points where the real-tool trace is not under churn.


## Task D — runtime validation with real long tools and real background churn (Deliverable 4; REAL APPLICATION)
Runs (200 tasks each, Qwen2.5-3B-Instruct-AWQ, LMCache L1 1 GB, GPU cache 32k / 48k tokens; `benchmarks/agent/run_chain_lt.sh`):

| run | agents | background on the same server | serving time | real tool time p50 (checks / profile / aggregate) | continue lead p50 / p90 | REAL LRU residence p50 / p90 | contexts evicted before the next call | next call fully hit | REAL reuse-hit share |
|---|---|---|---|---|---|---|---|---|---|
| lt-k8-l1g | 8 | none | 3.5 min | 8.0 / 2.7 / 2.5 s | 2.9 / 9.2 s | 69 / 83 s | 0.0% | 100% | **0.986** |
| lt-k16-l1g | 16 | none | 2.2 min | 9.0 / 3.1 / 2.8 s | 3.1 / 10.6 s | 38 / 49 s | 0.0% | 100% | **0.972** |
| lt-k8-l1g-bg | 8 | Mooncake conversation replay at 0.05× (REAL, **bursty**: the trace's timestamps are quantized to 3 s, so ~8 prompts of ~30 chunks arrive together every 60 s) | 4.3 min | 8.0 / 2.9 / 2.5 s | 3.0 / 12.2 s | 12 / 49 s (p10 4 s) | 3.9% | 95% | **0.949** |
| lt-k16-l1g-bg | 16 | same bursty background | 2.8 min | — | 3.3 / 14.1 s | 6.8 / 30 s | 3.7% | 94% | **0.933** |
| lt-k8-l1g-bg2 | 8 | same trace, **steady** (timestamps de-quantized over the 3 s quantum; one ~30-chunk prompt every 6 s = 3.2 chunks/s) | 3.7 min | 7.9 / 2.7 / 2.6 s | 2.9 / 9.8 s | 12.6 / 31 s | 0.2% | 99% | **0.980** |
| lt-k16-l1g-bg2 | 16 | same steady background (4.4 chunks/s) | 2.3 min | 8.6 / 3.1 / 2.8 s | 3.2 / 9.9 s | 11.5 / 17.8 s | 0.1% | 98% | **0.965** |

What the real system did: without background, residence (38–69 s) is 10–20× the horizon (3 s) and nothing live is lost
(reuse-hit 0.972–0.986, the misses are the first reads of the system prompt and the repeated-prompt tasks). With the
bursty background every burst exceeds the 1 GB cache (8 × 30 chunks × 9.4 MB = 2.3 GB), so the cache is flushed about
once a minute: 3.7–3.9% of the contexts are evicted between a decision and the next call and the reuse-hit share drops
to 0.933–0.949. The replay of these two traces (REAL churn, no synthetic addition; `lt-k*-l1g-bg-churn0-replay.csv`)
gives the one case where a baseline beats the real events: a burst evicts everything that is not protected or hot, so
the continue signal (which protects only the contexts of tasks that are between calls at that moment, 72–74% of the
reuses) recovers 10–20% of the oracle's gain (+2 … +3 hits) while **SLRU recovers 50–60%** (+7 … +12 hits) by keeping
the blocks that were already re-read once — the shared prefix and the contexts of multi-call tasks. Absolute gaps:
oracle − LRU = 1.2–2.0 points.

With the background de-quantized to steady arrivals (`-bg2`, 3.2–4.4 chunks/s of foreign KV, one ~30-chunk prompt
every 6 s), the real system at 1 GB keeps a residence of 11.5–12.6 s against a 3.2–3.6 s horizon and loses almost no
context (0.1–0.2% evicted before the next call; reuse-hit 0.965–0.980). The replays of these two traces (REAL churn only,
`lt-k*-l1g-bg2-churn0-replay.csv`, included in fig-regime / fig-regime-2d) are the direct confirmation of the band
predicted from the synthetic sweeps: at C / W_live = 1.3–2.5, where the residence equals one horizon, the continue
signal recovers **78–91% of the oracle's gain (+64 … +83 hits, +5.7 … +7.4 points of reuse-hit share)**; at two
horizons 67–71% of a ~1-point gap; at ≥ 5 W_live nothing. The 1 GB cache of the real runs (C / W_live = 5–8 at 13–19
chunks live) is above the band, which is why the real reuse-hit share stayed at 0.965–0.980 under plain LRU: the
band would need the cache to be 4–6× smaller or the churn 4–6× larger than in these runs.


## Task E — when hints are useful: mechanism, not correlation (fig-regime-2d)
Three measured quantities decide it. LRU keeps a block for one residence time T_res = C / P (capacity over the total
production rate, agents plus co-tenants). A task's context is needed again after the horizon H (tool time plus model
time). A continue signal can hold a context only if the live contexts fit: C ≥ W_live. Hence:

- **H < T_res:** LRU already keeps the context; a hint protects what was never at risk (continue = LRU, end = LRU
  minus its false positives). This is the whole region above C ≈ 2 W_live in the replays and every short-tool setting
  without churn (H/T_res 0.01–0.3): 0–4% of a 0.4–3-point oracle gap.
- **H ≳ 0.5 T_res and C ≥ W_live:** LRU loses contexts between calls, there is room to keep them, and the continue
  signal (lead = the tool time, exactly the interval at risk) recovers 77–93% of the oracle's gain — the real-tool
  traces under 5–10 chunks/s of churn at C/W_live 1.2–2.5, residence 2.6–6 s against a 3–5 s horizon.
- **C < W_live:** the live contexts do not fit; the continue signal still recovers 51–70% of the oracle's gain
  (+7–9 points) by choosing which live context to drop, but the oracle itself is capacity-bound (it reaches only
  0.96–0.97) and the gain is paid by other live tasks.

The 2-D map (fig-regime-2d, left) shows the three regions with the 180 replay points (the 144 synthetic-churn settings plus the four background runs at 9 capacities) coloured by the continue signal's
recovery: green only in the band H/T_res ≳ 0.5 with C/W_live ≳ 1, light green left of C = W_live, red everywhere
below H/T_res ≈ 0.3. The gain comes from **protecting live data**, not from releasing dead data: continue-only equals
end+continue in every band, end-only never exceeds 37%, and above the band the end signal is net negative because 15%
of the blocks it declares dead are read again by a later identical prompt.

Answers to the six questions:
1. **Why 96–99% with short tools:** H = 1.4 s against T_res = 12–100 s (1 GB, 8–16 agents producing 3–5 chunks/s):
   every context comes back 10–70 residence times early. The 1–3.5% misses are the duplicate-prompt re-reads 30–60 s
   later and cold starts, which no runtime event predicts.
2. **When LRU starts losing needed blocks:** when C < P · H (residence shorter than the horizon) or C < W_live. With
   the agents as the only producer, P · H = 7 (short tools) to 4.5 chunks (real tools) — far below W_live, so the first
   condition needs other producers: 5–10 chunks/s of churn brought T_res to the horizon at C = 20–45 chunks = 1–2
   W_live. The second condition is reached by concurrency: W_live grows with the number of agents and their context
   size, P · H does not grow with the tool time (a slower loop produces proportionally slower).
3. **How much the signals recover:** 77–93% inside the band, 51–70% below the live set, 0–4% elsewhere (median over
   the 144 settings: 0%). In absolute terms +3 … +4 points inside the band, +7 … +9 under heavy pressure, 0 elsewhere.
4. **Live or dead:** live. The continue signal carries all of the gain; the end signal is at best a third of it under
   heavy pressure and a cost otherwise.
5. **Do these regimes exist in real agent workloads?** The public traces give H = 6–11 s (p50) / 20–36 s (p90) and
   20k–60k-token contexts. ESTIMATE for an 8B model and a 200 GiB host cache (fig-regime-2d, right; `kv_agent_regime.py`):
   with 16–64 concurrent agents T_res = 25–1200 s, i.e. H/T_res = 0.01–0.25 — the LRU regime — unless co-tenants write
   ≥ 900 chunks/s (29 GB/s, the host's whole write ceiling); with 256 agents the live set is 3–10× the cache (C/W_live
   = 0.1–0.3, H/T_res up to 1) — the capacity-bound regime. A smaller dedicated cache changes the arithmetic: 20 GiB of
   DRAM turns over in 7 s under 90 chunks/s (2.9 GB/s of KV, what the Mooncake conversation trace produces), which is
   the band. So the band is real but narrow: a cache sized within a few horizons of its churn, with room for the live
   contexts — not the default state of a 200 GiB tier serving tens of agents.
6. **A stable regime?** Yes as a condition, W_live ≲ C ≲ P · H, no as a default: it is a band of about one decade in
   C (fig-regime-2d), it moves with the co-tenants' production, and it appeared in this study only with churn added
   (synthetic, and real in the `-bg` runs) or with the cache below the live set.


## RQ1-B decision (Deliverable 5) — against the charter's Gate 2 (≥ 50% of the oracle's gain, error cost ≤ 25% of it)
**Information availability — PASS (previous round, unchanged):** the runtime knows continue / end at the end of every
LLM call, block-exact for the request's own context, with a lead equal to the tool time (2.9–3.3 s p50, 10–14 s p90 with
real tools; the public traces' horizons are 6–11 s p50, 20–36 s p90).
**Information utility — PASS only inside one band, FAIL outside it.** Over 144 replay settings of four real traces the
median recovery is 0%. The continue signal clears 50% exactly when (a) the LRU residence is within about two horizons
(H / T_res ≳ 0.5) and (b) the live contexts fit (C ≥ W_live): 77–93% with synthetic churn, **90–91% with real steady
churn**, +3 … +7 points of reuse-hit share; below the live set it recovers 51–70% (+7 … +9 points) of a capacity-bound
oracle; everywhere else 0–4% of a ≤ 3-point gap, and the end signal is net negative there (its 15% false positives cost
more than it gains, so the charter's error criterion fails for end-based eviction outside the band). Under bursty churn
(the raw Mooncake timestamps) the signal recovers 10–20% and SLRU 50–60%. Session TTL never beats LRU.
**Workload representativeness — the band exists but is not where real deployments sit by default.** Real agent loops
re-read their context after 6–11 s (p50); a 200 GiB host cache serving ≤ 64 such agents (8B model, ESTIMATE from the
public traces) turns over in 25–1200 s, i.e. H / T_res = 0.01–0.25: the LRU regime, where the signal is worth nothing.
The band is reached when the cache is small relative to its churn (a few GB per GB/s of foreign KV traffic, e.g. a
dedicated DRAM tier of ~20 GiB under 3 GB/s of chat traffic) or when ≥ ~256 agents with 20k–60k-token contexts share
200 GiB (the capacity-bound regime, where the oracle itself is limited).
**Generalizability — the mechanism is general, the benefit is conditional.** It holds for any agent loop whose horizon
is seconds to tens of seconds (all six public benchmarks): the continue signal protects exactly the interval at risk,
the end signal does not pay. It does not hold for chat (no signal) and it gives nothing once the cache keeps a context
for more than ~2 horizons, which a sensibly sized tier does.

**Gate 2: PARTIAL.** The criterion is met (77–93%) only in a regime that this study had to construct — co-tenant churn
that brings the residence down to the horizon with the live contexts still fitting — and that the public workload
parameters place outside the default operating point of a 200 GiB tier. The absolute benefit inside the band is 3–7
points of reuse-hit share (recompute −2 … −3%), the oracle's own gap being ≤ 3 points outside heavy pressure. The
criterion is not met in the no-pressure and moderate-pressure scenarios (0–4%). The 50% threshold was not changed;
no new predictor, policy or feature search was added.

### Final RQ1 assessment (all rounds)
- **Is future reuse information valuable?** Yes (Gate 1 PASS): the block oracle serves 70–94% of reuses where LRU serves
  17–65% on the Mooncake traces at 200 GiB, cuts recompute 26–43% and host writes 70–83%; most of the value is not
  storing the 58–79% of blocks that are never reused (`2026-10-17-kv-reuse-oracle-study.md`).
- **Which information is obtainable online?** Queued requests' exact block hashes (lead 0.2 s, worthless); the agent
  runtime's continue / end decisions (zero delay, block-exact; verified in real runs); nothing for chat. Session
  recency / TTL rules add nothing over LRU.
- **Which information cannot be predicted?** Whether a block will ever be reused, from creation-time or history
  features (lift ≤ 1.5×, online rules ≤ 6% of the ceiling); whether a chat session continues; which blocks of an ended
  task a later identical prompt will re-read (the 15% end false positives).
- **Which regimes give hints real benefit?** W_live ≲ C ≲ P · H: the cache turns over within about two reuse horizons
  and still holds the live contexts. Short-tool agents at ≥ 1 GB: no; real tools under steady co-tenant churn at
  C ≈ 2 W_live: yes (90%); bursty churn: no (SLRU does better); capacity below the live set: partially (51–70%,
  capacity-bound).
- **How much of the oracle's gain do agent hints recover?** 0–4% in the default regime; 77–93% in the band; 51–70%
  under heavy pressure; median over all settings 0%. In points of reuse-hit share: 0, 3–7, 7–9.
- **Enough evidence to enter the joint benefit analysis?** Not on the reuse-prediction premise. The information is real
  and cheap, but its hit-rate value is confined to a band that a well-sized tier avoids; a design that relies on it
  would have to size the cache into the band on purpose. What this round does not change: the lifecycle event's
  write-side value (deferred stores, simulated −49%) and the dead-occupancy release (74–96% of the cache-time) are not
  hit-rate benefits and were not re-tested here.
- **Limits that cannot be removed here:** the 4060 Ti cannot run the public traces' 20k–60k-token contexts or 70B
  models (W_live and P are 1–2 orders of magnitude smaller than in production, which is why capacity is reported
  relative to W_live); the public traces give horizons and prompt sizes but not tool names, concurrency or cache
  behaviour; LMCache's lazy offload crashes, so deferred stores stay simulated; the synthetic churn is uniform and the
  real churn is one chat trace at one rate.

