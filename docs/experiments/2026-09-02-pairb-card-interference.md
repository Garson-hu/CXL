# 2026-09-02 — Card-vs-card interference on Pair B (two CZ120s behind one host bridge)

**STATUS: CLOSED. Verdict: individual CXL cards are isolation domains. Traffic
on the neighbor card — reads OR saturating NT writes — leaves a latency victim
untouched (0%) and costs a bandwidth victim ≤6% (reads) / 0% (writes). The same
traffic on the victim's OWN card costs 1.9–2.1× latency and 51% bandwidth
(reads).** First real-hardware measurement of CXL-to-CXL interference at card
granularity. Raw: `experimental_results/2026-09-02-pairb-card-interference/`.

## Setup
/dev/dax2.0 = Pair B; card A = even 256 B class, card B = odd class (map proven
in `2026-09-01-pairb-address-map.md`). Victim on card A in dax region 64 GiB,
CCD0 (cpu 0..): pointer chase restricted to card A (`daxchase --class=0`, 1 M
samples) or 8-thread read stream (`daxstride --offset=0`). Aggressor = separate
process, 8 threads, CCD1 (cpu 16..), dax region 160 GiB, 10 s; victim window
(4 s) sits inside. Aggressor kinds: reads on card B / NT writes on card B /
reads on card A (control) / NT writes on card A (control). 3 reps, medians.
Tools: `cxlprobe` (`--class`, `daxstridewr` NT-write mode added this date);
`hardware/scripts/pairb-card-interference.sh`.

## Latency victim — chase on card A (median of reps; ns)
| aggressor | mean | p50 | p90 | p99 | p99.9 |
|---|---:|---:|---:|---:|---:|
| none (idle) | 225.6 | 219 | 219 | 469 | 489 |
| 8T reads on card B | 225.0 | 219 | 229 | 399 | 539 |
| 8T NT writes on card B | 224.8 | 219 | 229 | 409 | 519 |
| 8T reads on card A (same card) | 435.7 | 419 | 609 | 849 | 989 |
| 8T NT writes on card A (same card) | 464.9 | 459 | 619 | 819 | 979 |
| symmetric: chase on card B, idle | 229.6 | 219 | 229 | 390 | 619 |
| symmetric: chase on card B under NT writes on card A | 234.1 | 219 | 229 | 559 | 619 |

**Cross-card: zero effect** on mean, p50, p90 — even p99 is unchanged within
noise. **Same-card: 1.93× (reads) / 2.06× (writes)** at mean and p50; p90 ~2.7×.

## Bandwidth victim — 8T reads on card A (GiB/s, median; reps within ±0.1)
| aggressor | victim | aggressor avg over 10 s | aggressor during overlap (est.)* |
|---|---:|---:|---:|
| none | 23.8 | — | — |
| reads on card B | 22.3 (−6%) | 23.3 | ~22.6 |
| NT writes on card B | 24.1 (0%) | 19.1 | ~14.9 |
| reads on card A (same) | 11.7 (−51%) | 19.5 | ~12.9 |
| NT writes on card A (same) | 22.6 (−5%) | 18.8 | ~14.2 |
\* overlap estimate = (10 s avg − 6 s × solo rate) / 4 s; solo read 23.9, solo NT write 21.9.

## Findings
1. **Cards are isolation domains.** Nothing the neighbor card does moves the
   victim's latency; a read-vs-read pair across cards costs each side ~5–6%
   (the shared host bridge: even+odd aggregate 44.3–44.9 vs 2×23.9 = 47.8).
   Cross-card write storms cost the reader nothing.
2. **Same-card read+read shares one link fairly:** 11.7 + ~12.9 ≈ 24.6 = one
   card's ceiling. Textbook shared pipe.
3. **Card-level duplex is strong:** same-card 8T reads keep 22.6 (−5%) while
   NT writes add ~14 GiB/s → ~37 GiB/s on ONE card vs 23.9 single-direction
   (≈ +55%), stronger than the pair-level +30% of Gate 1. But same-card writes
   DO hurt a latency victim 2.06× — writes cost latency, not read bandwidth.
4. **Asymmetry in the shared path:** cross-card, readers are protected but NT
   writers yield (~−30% during overlap, est.). Reads appear to win arbitration
   upstream of the cards.
5. **Symmetry holds:** victim on card B under writes to card A: +2% mean, p50
   unchanged.

## Implications (feed `DESIGN.md` §7 / `PAPER.md`)
- "Give the noisy writer its own card" delivers Gate-2b-grade protection
  INSIDE the CXL tier: a write stream parked on card B is invisible to card A's
  latency-critical readers. Per-card placement = isolation, measured.
- Planner model per card: read budget ~23.9, write budget ~21.9, joint ≈ 37
  (duplex), latency penalty for co-located writes ≈ 2×; cross-card coupling
  ≤6% (reads) / 0 (writes) — small enough to treat cards as independent.
- Pair granularity (Aug-25, Pair A node): co-located CXL readers lost 41% bw
  under writes; at card granularity on Pair B the same-card read loss is 5%.
  Different pair/config — do not merge the numbers; both are recorded.

## Caveats
- Reads-only victims; write-victim and RMW-victim arms not run.
- Aggressor rates during overlap are estimates from 10 s averages (the
  aggressor runs 6 s solo); rerun with matched windows if a number is cited.
- Labels (card A = 01:00.0?) remain the decoder3.0 target-order assumption;
  disjointness is proven, identity is not.
