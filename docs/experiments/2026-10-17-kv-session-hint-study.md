# 2026-10-17 — Session-level hint study: can application-level session information give the lifetime signal that block-level prediction cannot?

**STATUS: CLOSED 2026-10-17** (the last exploratory experiment on reuse predictability, by the user's brief). Evidence type:
**TRACE SIMULATION**; every hint that uses the trace's future is an **ORACLE** and labelled so. Raw:
`experimental_results/2026-10-17-kv-session-hint-study/` (`session-hints-8b-200GiB.csv`, `session-structure-8b-200GiB.json`,
`run-log.txt`, figures `fig-session-*.png/.svg`). Scripts: `scripts/kv_session_hint_study.py`, `scripts/kv_session_hint_figs.py`.
Follows `2026-10-17-kv-reuse-oracle-study.md` (Phase 1) with the same protocol; charter `docs/research/CHARTER.md`.

## Questions
Q1 potential value: if the system knew whether a conversation session will continue, how much of the block-level
oracle's gain would it get? Q2 availability: which of these signals exist in a real serving system, and when? Q3
robustness: what if the hint is wrong, late or missing?

## Method
- Same as Phase 1: Mooncake traces, 200 GiB (DRAM 64 + CXL 136), 8B blocks (64 MiB), two halves by request count, every
  policy warmed on the first half and scored on the second, stores complete at once, reuse-hit share = hits / accesses
  to blocks seen before.
- Sessions reconstructed from prefix chains (the trace has no session ids): a request's previous turn is the request
  that created the last old block of its prefix after the shared system block(s). A session's "continues" fact is the
  trace's future (oracle). Blocks referenced by two or more sessions are never marked dead by a hint.
- Policies: static split (B) and global LRU (C); `session_ttl<T>` (ONLINE: blocks of sessions idle > T evicted first);
  block-level oracle (Belady MIN with bypass, the ceiling); `hint` family (ORACLE session knowledge): mode `admit`
  (new blocks of a session that will not continue are not stored), `evict` (everything stored; a dead session's blocks
  become evict-first at request completion), `both`; `bound=T` ("continues" = next turn within T seconds); per-request
  errors `fp` (dead reported live), `fn` (live reported dead), `miss` (no hint → store, LRU); `delay=D` (EVENTS ONLY: no
  positive hint; a termination event arrives D seconds after a session's last request and marks its blocks evict-first).
- Extra metrics: hits from within-session reuse; occupancy-time spent on blocks with no future use; mean residence of
  blocks that were hit vs never hit; writes and bypassed blocks.
- Commands: `python3 scripts/kv_session_hint_study.py` (default policy set, ~20 min single core);
  `python3 scripts/kv_session_hint_figs.py`.

## Session structure (fig-session-structure)
| | conversation | tool agent | synthetic |
|---|---|---|---|
| sessions; single-turn sessions | 7,373; 69% | 6,554; 68% | 2,211; 82% |
| requests that have a next turn | 39% | 72% | 45% |
| reuses within the session / across sessions | 89% / 11% (the system block) | 95% / 5% | 100% / 0% |
| blocks of a turn re-read by the next turn (mean; new blocks only) | 81% (p50 92%); 56% | 82% (p50 86%); 14% | 94% (p50 97%); 26% |
| gap to the next turn p50 / p90; within 60 / 300 / 900 s | 123 / 480 s; 22 / 79 / 97% | 0 / 150 s; 80 / 96 / 100% | 55 / 280 s; 52 / 92 / 100% |
| occupancy-time on dead blocks: LRU / perfect session hint / block oracle | 70 / 26 / 9% | 70 / 40 / 9% | 38 / 10 / 8% |

Session continuation is a good but not exact proxy for block reuse: the next turn re-reads about four fifths of the
previous turn's blocks, and in the agent trace only 14% of a turn's *new* blocks (tool outputs are not carried forward).
Reuse is almost entirely within sessions, so a session signal addresses the right blocks.

## Results (fig-session-hint-policies, fig-session-hint-writes-occupancy): reuse-hit share on the test half; in brackets the share of the block oracle's gain over the static split
| policy | conversation | tool agent | synthetic |
|---|---|---|---|
| static split (B) = global LRU (C) | 0.174 | 0.647 | 0.344 |
| session TTL 300 s / 60 s (ONLINE) | 0.174 (0%) | 0.647 (0%) | 0.342 (0%) |
| block-level oracle (E) | 0.797 (100%) | 0.940 (100%) | 0.696 (100%) |
| perfect hint, admission only | 0.450 (44%) | 0.748 (34%) | 0.440 (27%) |
| perfect hint, eviction only | 0.513 (54%) | 0.771 (42%) | 0.486 (40%) |
| perfect hint, both | 0.513 (54%) | 0.771 (42%) | 0.486 (40%) |
| perfect hint, both, continues within 900 s | 0.519 (55%) | 0.773 (43%) | 0.486 (40%) |
| perfect hint, both, continues within 300 s | **0.633 (74%)** | **0.797 (51%)** | 0.488 (41%) |
| perfect hint, both, continues within 60 s | 0.305 (21%) | 0.693 (16%) | 0.576 (66%) |
| termination event, no delay (no positive hint) | 0.506 (53%) | 0.766 (41%) | 0.485 (40%) |
| termination event, 10 s late | 0.413 (38%) | 0.730 (28%) | 0.419 (22%) |
| termination event, 60 s / 300 s late | 0.174 (0%) | 0.647 (0%) | 0.342 (0%) |

Writes to host memory (test half): static split 18.0 / 17.6 / 6.6 TB; perfect hint with admission 6.1 / 7.4 / 3.6 TB
(−66 / −58 / −45%); block oracle 3.2 / 3.0 / 2.0 TB. Recomputed tokens: −14 / −11 / −17% for the perfect hint (ever),
−19 / −14 / −17% with the 300 s bound, −26 / −27 / −43% for the block oracle.

Hint quality (fig-session-hint-sensitivity; share of the block oracle's gain, mode both):
| | conversation | tool agent | synthetic |
|---|---|---|---|
| perfect | 54% | 42% | 40% |
| 10% / 30% false positives (dead session kept) | 42% / 24% | 33% / 20% | 37% / 28% |
| 10% / 30% false negatives (live session dropped) | 53% / 51% | 38% / 26% | 43% / 37% |
| 30% false positives and 30% false negatives | 23% | −1% | 19% |
| 30% / 60% of hints missing | 26% / 9% | 21% / 8% | 25% / 8% |

## What the numbers say
- **Q1 — value.** A perfect "this session continues" hint recovers 40–54% of the block oracle's gain (reuse-hit share
  0.51 / 0.77 / 0.49 against 0.17 / 0.65 / 0.34) and, with a 300 s bound, 74% / 51% / 41%. The gain is retention, not
  placement: eviction-only equals admission + eviction, and admission alone gives less because resident blocks of dead
  sessions still occupy the cache until LRU reaches them. Admission adds the write saving (−45 to −66%). Session hints
  fall short of the block oracle because a continued turn re-reads only ~80% of its blocks (14–56% of its new ones) and
  because "continues ever" keeps slow sessions (p90 gap 480 s) whose blocks the cache cannot afford: bounding the hint
  to 300 s helps on both real traces, and 60 s is too tight for chat.
- **Q2 — availability.** What matters is a *positive* hint at request time or a *termination* event within about
  10 s of the last answer; a termination event 60 s late is worthless (0%), because at 200 GiB the LRU has evicted the
  blocks by then anyway, and the online session state (recency, idle time) adds nothing over block LRU (session TTL =
  LRU). Chat clients do not know whether the user will send another message, and they report the end of a conversation
  late if at all; for the chat trace, therefore, only oracle information works. Agent frameworks know when a task loop
  ends and whether they will call the model again, and their turns chain within seconds (p50 gap 0 s): there a
  task-end event at delay 0–10 s is realistic and recovers 28–41% of the ceiling (+8–12 points of reuse-hit share,
  writes −58% if combined with admission). Estimating continuation from history was tested in Phase 1 (≤ 6%).
- **Q3 — robustness.** False positives are the expensive error (a kept dead session wastes capacity): 10% cost about a
  fifth of the benefit, 30% halve it; false negatives are cheap (a dropped live session costs its hits but frees space;
  30% keeps 51% on chat); hints missing for 30% of requests halve the benefit, 60% remove it; delay beyond ~10 s removes it.
- Perfect session hints and the block oracle are both oracles; no real system can be assumed to have the positive
  "will continue" signal for chat.

## Gate update (charter §8)
- Gate 1 (future information has value): unchanged, PASS.
- Gate 2 (the information is available online): **FAIL for chat** — only oracle hints clear 50%; realistic chat signals
  (late termination, recency) give 0%. **Borderline for agent workloads** — a task-end event with ≤ 10 s delay gives
  28–41% of the ceiling, below the 50% criterion but a real +8–12 points; it is an application interface, not a
  predictor. No further predictability search is justified.
- Gates 3 and 4: not reached.

## Verdict
Session-level information is the right kind of signal (reuse is within-session and the next turn re-reads most blocks)
and a perfect version of it is worth about half of the block oracle, but the half that a real chat system could obtain
(late termination events, recency) is worth nothing, and the half an agent framework could obtain (prompt task-end
events) is worth 28–41% of the ceiling. Decision by the user's cases: **Case B for chat, a weak Case A for agent
workloads.** Recommendation: stop the KV reuse-prediction direction as a research contribution; keep "explicit lifetime
release" (task-end / end-of-session events, immediate) as an optional application interface of the unified manager —
a mechanism, not a predictor — and return to the charter's higher-level question with capacity-aware placement,
interference-aware admission, lifecycle management and cross-application coordination as the candidate focus.
Limits: reconstructed sessions, three traces (one synthetic), capacity-only model, one error model (independent
per-request errors), one random seed.
