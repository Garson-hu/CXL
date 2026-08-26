# 2026-08-25 — Verification of the gate-2b "6.3× DRAM reader collapse"

**STATUS: CLOSED. Verdict: the collapse is REAL and robust.** User asked for a
careful verification of the headline gate-2b cell (DRAM 4T reader: 68.6 GiB/s
idle → 10.9 under 8 NT-writers to DRAM). This file re-examines the original
raw data and adds a targeted battery. Parent: `2026-08-25-direction-gates.md`.
Raw: `experimental_results/2026-08-25-gate2-verification/` (+ re-analysis of
`.../2026-08-25-direction-gates/`).

## Checks against the EXISTING raw data (no new runs)
1. **Stability:** the claim cell per-rep = 10.9/10.8/10.8/10.9/10.9 (±0.5%);
   idle control 68.4–68.6; writers→CXL control 68.4–68.7 (= idle, every rep).
2. **Conservation:** victim + concurrent writers = 10.9 + 54.7 = 65.6 GiB/s
   ≈ the 69.4 pure-read ceiling (95%; ~5% mixing loss, matches gate-1 mixed
   totals). Writers simply take 83% of one shared pipe — no accounting anomaly.
3. **Independent reproduction:** gate-1 (different code path: single process,
   same-CCD, in-process split) g1-n0-r4-w12 → readers 10.2. Two designs agree.

## New battery (3 reps each, node 0, victim = 4T stream-read on CCD0 unless noted)
| config | victim reads | writers | sum | conclusion |
|---|---:|---:|---:|---|
| idle | 68.4 | — | 68.4 | baseline |
| 2 NT writers | 10.5 | 55.1 | 65.6 | 2 threads already saturate the write path → same collapse; effect tracks write PRESSURE, not thread count |
| 4 NT writers | 9.3 | 55.2 | 64.5 | ditto |
| 8 NT writers | 10.9 | 54.7 | 65.6 | replication of the claim |
| 8 plain-store writers | 16.6 | 31.0 | — | NOT NT-specific: ordinary writes also crush the reader (4.1×); NT is the worst case (6.3×) |
| CCD-swap (victim CCD1, writers CCD0) | 10.2 | 55.1 | 65.2 | no CCD asymmetry — effect lives at the memory controller |
| 8 readers vs 8 NT writers | 10.3 | 54.5 | 64.8 | more reader threads reclaim NOTHING — structural, not queue-slot arithmetic |

## Mechanism (consistent with all cells)
A DRAM controller prioritizes reads until its write queue passes a high-water
mark, then switches to write-drain bursts. A saturating write stream (≥2 NT
threads ≈ 55 GiB/s) keeps the queue above the mark permanently, so the
controller lives in drain mode and reads starve between bursts — regardless of
reader thread count or core placement.

## Scope caveat (honest limit of the claim)
Every writer config here SATURATES the write path. The traffic-rate
dose-response (e.g., a rate-limited 5–10 GiB/s write stream) was not mapped;
the claim is scoped to **sustained saturating write streams** — which is what
checkpoint/eviction/log-flush bursts are. Rate-limited sweep = possible future
work if a reviewer asks.

## Verdict
6.3× (NT) / 4.1× (plain) DRAM reader collapse under saturating co-located
write streams: **confirmed** — stable, conserving, reproduced across two
experiment designs, insensitive to CCD placement and reader thread count, not
an NT-store artifact. The paired control (same writers → CXL: reader identical
to idle in every rep) stands. Gate-2b conclusions unchanged and strengthened.
