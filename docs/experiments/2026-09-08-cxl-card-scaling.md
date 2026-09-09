# 2026-09-08 — Per-card selection status + CXL bandwidth scaling over 1 / 2 / 4 cards

**STATUS: CLOSED. Verdict: reads and NT-writes scale ~linearly with cards
(24 → 46 → 90 GiB/s read; 22 → 44 → 85 write); the only measurable shared
cost is the host bridge inside Pair B (−6%); crossing pairs costs 1%. Mixed
traffic beats the best single direction at every scale (+53% / +36% / +42%);
four cards sustain 127–128 GiB/s.** Campaign Phase 2 of
`2026-09-08-write-tier-campaign.md`. Raw:
`experimental_results/2026-09-08-cxl-card-scaling/` (scaling.csv = rep 1;
scaling-r2r3.csv = reps 2–3 after a session restart killed the first run;
summary-all-reps.txt = merged medians).

## Part 1 — the five questions, answered from established results
1. **Can I select individual physical CXL cards by address/range today?** Yes,
   two ways with different reach. Pair B (`/dev/dax2.0`): a single card via the
   256-byte parity class `card = (offset >> 8) & 1` — proven and uniform over
   the whole 512 GiB (`2026-09-01-pairb-address-map.md`), but usable only by
   code that chooses its own addresses (stripe finer than a page ⇒ no
   contiguous single-card buffer for applications). Pair A (`/dev/dax0.0`):
   pair granularity only — the way-selection is hashed
   (`2026-09-08-paira-interleave-hash.md`). Pair-level selection is
   deterministic and app-usable on both (contiguous mmap).
2. **Confirmed:** Pair B stripe rule and its uniformity; Pair A hash (no single
   bit, no bit8⊕bit9); Pair A and Pair B are physically disjoint card sets;
   Pair B's two cards are isolation domains (`2026-09-02-…`); single-card read
   23.9–24.2 and NT-write 22.0 GiB/s; pair read ~45.6.
3. **Still missing one verification:** which parity class is the card at
   01:00.0 vs 02:00.0 (label only; decoder3.0 target order assumed; needs root
   DF-PMU/telemetry). No experiment so far depends on it.
4. **Is system-ram enough?** For DRAM-vs-CXL(pair) placement, yes (node 1).
   But node 1 = `dax1.0` = Pair A's second window — the SAME cards as
   `dax0.0`; it is not a third independent resource.
5. **What devdax adds:** deterministic pair choice (the allocator no longer
   decides the window), the Pair B card-class instrument, a target for
   NT-store staging, and both pairs usable concurrently (system-ram gives one
   node).
Achievable device counts: **1 card** (Pair B even class), **2 cards**
(Pair B), **4 cards** (Pair B + Pair A). **3 cards impossible** (Pair A is
unsplittable).

## Part 2 — scaling experiment
Setup: `hardware/scripts/cxl-card-scaling.py`; cxlprobe `daxstride` (reads) /
`daxstridewr` (NT writes); 4 s per point; total threads T ∈ {4,8,16,32} split
across processes by mode ratio; each process on its own 32-cpu block (2 CCDs)
and its own dax region; 1 card = Pair B class 0 (stride 512 / chunk 256);
2 cards = Pair B all chunks; 4 cards = Pair B + Pair A concurrently. Median of
3 reps; rep-to-rep spread ≤ 1.0 GiB/s at every point.

Aggregate GiB/s (median of 3):
| cards | mode | T=4 | T=8 | T=16 | T=32 |
|---|---|---:|---:|---:|---:|
| 1 | read | 23.0 | 24.2 | 24.3 | 24.2 |
| 1 | NT write | 21.6 | 21.9 | 21.9 | 22.0 |
| 1 | mix 3:1 / 1:1 / 1:3 | 32.4 / 30.8 / 26.8 | 36.5 / 33.7 / 31.1 | 37.1 / 37.2 / 33.8 | 36.8 / 37.1 / 36.1 |
| 2 | read | 45.2 | 45.0 | 45.0 | 45.6 |
| 2 | NT write | 40.9 | 41.6 | 41.5 | 43.7 |
| 2 | mix 3:1 / 1:1 / 1:3 | 61.9 / 62.4 / 55.4 | 62.0 / 62.2 / 63.1 | 59.5 / 62.0 / 62.8 | 61.1 / 61.5 / 61.9 |
| 4 | read | 85.0 | 90.6 | 90.1 | 90.2 |
| 4 | NT write | 85.3 | 84.5 | 85.5 | 85.4 |
| 4 | mix 3:1 / 1:1 / 1:3 | 108.3 / 108.0 / 108.1 | 125.8 / 125.0 / 109.0 | 126.5 / 127.6 / 125.8 | 125.0 / 127.1 / 128.3 |

## Findings
1. **Near-linear scaling.** Read ×1.88 (1→2) and ×1.98 (2→4); NT-write ×1.99
   and ×1.95. Four cards: 90.2 read / 85.4 write.
2. **Where the shared cost is.** Inside Pair B (two cards on one host bridge)
   reads lose 6% vs 2× single (45.6 vs 48.5). Crossing pairs — different host
   bridges, different root complexes — loses 1% (90.2 vs 91.2). No CPU-fabric
   ceiling is visible up to 128 GiB/s aggregate. **The bottleneck is the card
   link (~24 GiB/s per direction per card), nothing upstream.**
3. **Duplex at every scale.** Best mix vs best single direction: +53% (1 card,
   37.1 vs 24.2), +36% (2, 61.9 vs 45.6), +42% (4, 128.3 vs 90.2). The
   single-card number is the cleanest duplex measurement we have: one x8 link
   carrying 37 GiB/s of useful traffic against a 24 GiB/s one-way cap.
4. **Saturation thread counts.** Pure read/write saturate by 4–8 threads at
   every scale; mixes need 8 threads at 2 cards and 16 at 4 cards to reach
   their plateau (mix 1:3 at 4 cards lags until 16 threads).
5. **Context.** 128 GiB/s across four cards exceeds today's crippled DRAM
   (25–41 GiB/s, interleave disabled) and is comparable to healthy DRAM
   (May: 94.6 @32T). A DRAM read+write control belongs here once the BIOS is
   reverted (🔴).

## Implications
- Multiple CXL cards DO provide additive bandwidth; a placement system can
  treat cards/pairs as independent bandwidth budgets with ≤6% coupling.
- For the write-tier thesis: parking write streams across several cards
  scales the write side linearly (22 → 44 → 85) while leaving the read side of
  other cards untouched (`2026-09-02` isolation data).
- Planner constants (per card): read 24.2, NT-write 22.0, joint ≈ 37;
  per pair: 45.6 / 43.7 / ≈ 62; four cards: 90 / 85 / ≈ 127.

## Caveats
Pair A contributes only as a whole pair; the "4 cards" point is Pair B + Pair A,
not four independently addressable units. Mixed-mode process thread splits
are rounded (min 1 per process); actual thread counts are in the CSV.
