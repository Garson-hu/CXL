# 2026-09-22 — Phase 2 re-run with a data-carrying snapshot: three simple policies vs cxlpath beside seven victims

**STATUS: CLOSED 2026-09-23 (117 runs: 39 settings × 3 interleaved repetitions, every producer rc = 0).** Replaces the numbers of
[2026-09-22-three-policies.md](2026-09-22-three-policies.md) and of items 1–2 of
[2026-09-22-moderate-pacing-dcp.md](2026-09-22-moderate-pacing-dcp.md), whose C producer copied a 98%-zero
snapshot ([2026-09-22-zero-line-writes.md](2026-09-22-zero-line-writes.md)). Raw:
`experimental_results/2026-09-22-three-policies-realdata/`. Tools: `benchmarks/policy/` (`ckpt_producer.c` now
fills its snapshot with xorshift pseudo-random data on the producer's 8 cpus; driver `run_policy.py`; the
daemon's default guard is 1.3 since this campaign, so tags carry no `-g`).

## Question
Same as the superseded file: a periodic checkpoint copy (64 GiB every 25 s; PageRank: 192 GiB every 30 s)
beside a DRAM-bound victim — where do all-DRAM (NT / plain), all-CXL, a throttled DRAM writer and cxlpath land
on the two axes (victim slowdown during the copy; completion time) — now with a snapshot whose every cache
line carries data. Victims: the synthetic reader (8 threads), CPU Adam / llama.cpp / PageRank on 80 threads
(saturated), and the same three on 32 threads (moderate). cxlpath bounds as before (reader 1.09 / 1.15; Adam
1.04 / 1.10; llama.cpp 1.06 / 1.10; PageRank 1.055 / 1.10; 32-thread victims 1.09 / 1.05), pacing on.

## Results (median of 3 repetitions, each = median over its last 3 of 6 copy windows; ranges over repetitions in
parentheses; per-run lines in `summary.csv`; figure `core-realdata.png`)

| victim | policy | copy GiB/s | completion s | victim slowdown during the copy | DRAM share |
|---|---|---|---|---|---|
| reader, 8 threads (moderate) | all-DRAM, NT (today) | 92.7 | 0.69 | **27.6%** (26.9–27.7) | 1.00 |
| reader | all-DRAM, plain stores | 59.8 | 1.07 | 26.2% | 1.00 |
| reader | all-CXL | 43.9 | 1.46 | 1.1% (0.7–2.5) | 0 |
| reader | DRAM throttled 20 / 30 | 20 / 30 | 3.20 / 2.13 | 6.9% / 9.8% | 1.00 |
| reader | **cxlpath** bound 1.09 | 59.7 | **1.07** (0.95–1.11) | **6.2%** (5.0–7.8) | 0.27 (0.24–0.37) |
| reader | cxlpath bound 1.15 | 65.2 | 0.98 (0.93–1.00) | 6.2% (5.7–8.2) | 0.34 (0.33–0.40) |
| PageRank 2^25, 32 threads (moderate); 192 GiB | all-DRAM, NT | 86.4 | 2.22 | **68.5%** (62.6–71.1) | 1.00 |
| PageRank-32 | all-CXL | 43.8 | 4.38 | −0.1% | 0 |
| PageRank-32 | DRAM throttled 20 | 20.0 | 9.60 | 10.7% | 1.00 |
| PageRank-32 | **cxlpath** bound 1.09 | 57.2 | **3.35** (3.23–3.40) | 7.8% (7.0–10.3) | 0.24 (0.23–0.27) |
| PageRank-32 | cxlpath bound 1.05 | 55.0 | 3.49 (3.34–3.69) | **6.3%** (4.8–9.2) | 0.23 (0.16–0.27) |
| llama.cpp, 32 threads (moderate) | all-DRAM, NT | **22.3** | 2.87 | 3.4% (2.5–3.8) | 1.00 |
| llama.cpp-32 | all-CXL | 29.7 | 2.16 | 0.4% | 0 |
| llama.cpp-32 | DRAM throttled 20 | 20.0 | 3.20 | 3.8% | 1.00 |
| llama.cpp-32 | cxlpath bound 1.09 / 1.05 | 29.4 / 28.8 | 2.18 / 2.22 | −0.8% / −0.1% | 0.00 (no loan: CXL never "full") |
| Adam step, 32 threads | all-DRAM, NT | 68.2 | 0.94 | **56.2%** (53.8–56.5) | 1.00 |
| Adam-32 | all-CXL | 43.9 | 1.46 | 11.6% | 0 |
| Adam-32 | DRAM throttled 20 | 20.0 | 3.20 | 14.5% | 1.00 |
| Adam-32 | cxlpath bound 1.09 (guard denies the loan; paced) | 39.7 | 1.61 (1.46–1.65) | 10.8% (10.0–11.5) | 0 |
| Adam-32 | cxlpath bound 1.05 (paced 64% of epochs) | 34.1 | 1.88 (1.71–2.00) | **8.0%** (7.4–8.8) | 0 |
| Adam step, 80 threads (saturated) | all-DRAM, NT | 18.8 | 3.40 | **16.1%** (16.0–16.7) | 1.00 |
| Adam-80 | all-DRAM, plain stores | 9.5 | 6.75 | 11.8% | 1.00 |
| Adam-80 | all-CXL | 18.3 | 3.50 | 6.8% | 0 |
| Adam-80 | DRAM throttled 10 / 20 | 10 / 20 | 6.40 / 3.20 | 7.9% / 17.5% | 1.00 |
| Adam-80 | cxlpath bound 1.04 / 1.10 | 18.3 / 18.6 | 3.50 / 3.44 | 6.6% / 6.9% | 0 |
| llama.cpp, 80 threads (saturated) | all-DRAM, NT | 61.7 | 1.04 | **31.1%** (30.1–32.0) | 1.00 |
| llama.cpp-80 | all-CXL | 39.8 | 1.61 | 9.1% (8.7–9.8) | 0 |
| llama.cpp-80 | DRAM throttled 20 | 20.0 | 3.20 | 11.8% | 1.00 |
| llama.cpp-80 | cxlpath bound 1.06 / 1.10 | 38.9 / 39.9 | 1.65 / 1.61 | 8.7% / 8.7% | 0 |
| PageRank 2^26, 80 threads (saturated); 192 GiB | all-DRAM, NT | 48.8 | 3.93 | **42.2%** (42.0–47.8) | 1.00 |
| PageRank-80 | all-CXL | 43.9 | 4.38 | 16.2% (15.2–16.6) | 0 |
| PageRank-80 | DRAM throttled 10 | 10.0 | 19.2 | 7.6% | 1.00 |
| PageRank-80 | cxlpath bound 1.055 / 1.10 | 39.4 / 43.8 | 4.88 / 4.38 | 12.9% (9.5–14.9) / 16.0% | 0 |

What the daemon logs say (`*-daemon.csv`, repetition 1): probe level beside the victim relative to the calibrated
idle level — reader 1.13×, PageRank-32 1.15×, llama.cpp-32 1.07× (below the 1.3 guard: loan allowed), Adam-32 1.38×,
PageRank-80 1.45×, llama.cpp-80 1.67×, Adam-80 1.96× (guard: no loan). CXL "full" (ledger ≥ 90% of the 43.9 GiB/s
capacity) in 79–91% of active epochs beside the reader and PageRank-32 (spill reached 7–8/16), in **0%** beside
llama.cpp-32 — the copy into CXL achieves only 28.8 GiB/s there (see `2026-09-22-zero-line-writes.md`: data-carrying
writes beside llama.cpp run at 66% of the CXL capacity), so the constant-capacity fullness rule never fires and no
loan is given although the probe shows headroom. Pacing engaged beside Adam-32 (64% of active epochs) and
llama.cpp-80 (34%); 0–3% elsewhere.

Compared with the superseded zero-line campaign: beside the reader, Adam-80, PageRank-32 and PageRank-80 the numbers
are the same within a few points (DRAM copies of random data run at the zero-line rate beside those victims);
beside llama.cpp-32 the all-DRAM copy fell from 85.8 to 22.3 GiB/s and its harm from 23.7% to 3.4%, and all-CXL from
43.4 to 29.7 GiB/s; beside llama.cpp-80 all-DRAM 65.5 → 61.7 and all-CXL 43.6 → 39.8; beside Adam-32 all-DRAM
79 → 68 GiB/s and its harm 93% → 56%.

## Verdict
- **Moderate victims that leave DRAM headroom (reader, PageRank-32): the loan works with real data.** cxlpath lends
  23–34% of the chunks and finishes in 1.0–1.1 s (reader) / 3.35–3.5 s (PageRank-32) at 6–8% harm: 1.3–1.5× faster
  than all-CXL inside the bound, 3× faster than a throttled DRAM writer at equal harm, and 4–10× less harm than
  today's DRAM staging (27.6% / 68.5%). The copy rate is 57–65 GiB/s = 0.8–0.9 of the CXL capacity plus the phase-1
  DRAM budget for copies.
- **Saturated victims (Adam-80, llama.cpp-80, PageRank-80): cxlpath = all-CXL, 2.4–3.4× less harm than DRAM staging
  at the same or 1.1–1.5× the completion time** (6.6–6.9% vs 16.1%; 8.7% vs 31.1%; 12.9–16% vs 42.2%). Copies beside
  Adam are source-bound at 18 GiB/s whatever the destination.
- **llama.cpp-32 is the case where "CXL by default" is right and the loan is moot:** with data-carrying writes the DRAM
  copy runs at 22 GiB/s — slower than the CXL copy (30) — so DRAM staging has no speed advantage; all policies stay
  inside 4% harm. It also exposes a controller flaw: fullness is judged against a constant capacity (43.9 GiB/s), and
  beside llama.cpp the achievable CXL rate is 29, so the loan never triggers. Fullness must be measured against the
  rate achievable under the current co-runner (per-writer rate flattening, or a write probe) — a phase-3 change.
- **Adam-32** is not a moderate victim by the probe's measure (1.38× idle); the guard refuses the loan and pacing
  brings the harm from 11.6% (all-CXL) to 8.0% at 1.3× the completion time — the same behaviour as in the superseded
  campaign, now with real data.
- Pacing beside llama.cpp-80 / PageRank-80: marginal (8.7% vs 9.1%; 12.9% vs 16.2%), as before: the probe is a proxy
  for the victim's slowdown and the victims' own phases move it by more than a 1.06× bound.
