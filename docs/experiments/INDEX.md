# Experiment index

*One row per experiment file. A row gets its verdict when the experiment closes;
the file is frozen from that moment (see `../README.md` rules). Newest first.*

| Date | File | Question | Verdict |
|---|---|---|---|
| 2026-09-08 | [2026-09-08-cxl-card-scaling.md](2026-09-08-cxl-card-scaling.md) | Can we select cards today, and does CXL bandwidth scale with 1/2/4 cards? Where is the shared bottleneck? | CLOSED — five answers recorded; **near-linear scaling** (read 24→46→90, NT-write 22→44→85 GiB/s); shared cost = host bridge inside Pair B (−6%), cross-pair 1%; duplex +53%/+36%/+42%; four cards 127–128 GiB/s mixed. Bottleneck = card link |
| 2026-09-08 | [2026-09-08-write-tier-campaign.md](2026-09-08-write-tier-campaign.md) | UMBRELLA PLAN: validate the write-tier thesis end-to-end (DRAM write-drain mechanism → CXL card scaling → stencil rotation → LULESH/VeloC → PolyStore integration) | **ACTIVE** — plan + TODO with per-phase status; read first in every session |
| 2026-09-08 | [2026-09-08-paira-interleave-hash.md](2026-09-08-paira-interleave-hash.md) | Is /dev/dax0.0 (Pair A) interleaved, and can software address its cards? (advisor request: verify experimentally, not via sysfs) | CLOSED — **interleaved and HASHED**: no single bit (8–16) and no XOR(8,9) isolates a card; same-class co-run 41.6 = different-class 41.7. Control (Pair B) cleanly shows its plain stripe at bit 8 (23.9). Per-card stays Pair-B-only |
| 2026-09-02 | [2026-09-02-pairb-card-interference.md](2026-09-02-pairb-card-interference.md) | Does traffic on one CXL card disturb a program on the neighbor card (same host bridge)? | CLOSED — **cards are isolation domains**: cross-card reads/NT-writes → 0% latency effect, ≤6%/0% bandwidth; same-card → 1.9–2.1× latency, −51% bw (reads). Card-level duplex ≈ +55%. First real-HW CXL-to-CXL card-granularity measurement |
| 2026-09-01 | [2026-09-01-pairb-address-map.md](2026-09-01-pairb-address-map.md) | Which /dev/dax2.0 offsets hit which card of Pair B? (H-concat vs H-stripe vs H-hash) | CLOSED — **plain-modulo 256 B stripe**: card = (offset>>8)&1, uniform over 512 GiB; each class alone = one card (23.9 GiB/s), even+odd = pair (44.3), even+even = one card (24.3). H-concat and H-hash refuted. First single-CZ120 numbers. Per-card targeting from userspace WORKS on Pair B |
| 2026-08-25 | [2026-08-25-gate2-verification.md](2026-08-25-gate2-verification.md) | Is the gate-2b 6.3× DRAM-reader collapse real? (user-requested verification) | CLOSED — **confirmed**: stable ±0.5%, sum conserves to the pipe ceiling, reproduced by gate-1 independently, not NT-specific (plain writes: 4.1×), CCD- and thread-count-insensitive. Scoped to saturating write streams |
| 2026-08-25 | [2026-08-25-direction-gates.md](2026-08-25-direction-gates.md) | Is CXL's write direction a separate, exploitable resource? (Gates 1–2 for Thesis v2) | CLOSED — **both gates PASS.** G1: duplex joint capacity 59.4 vs 45.8 single (+30%); DRAM pinned at one pipe. G2b: write stream moved DRAM→CXL costs the DRAM reader NOTHING (68.6 = idle; was 10.9 under DRAM writers), writers keep 80%; CXL co-located readers pay (−41% bw, 2.2× lat). Bonus: same-CCD fabric confound found + methodology fixed. Direction GO → W3 |
| 2026-08-11 | [2026-08-11-percard-prelim.md](2026-08-11-percard-prelim.md) | What can we learn about per-card behavior while the BIOS pairs the cards? (E1–E4 + NPS4 postscript) | CLOSED — E1 software split impossible; E3 tails benign, congestion real; E4 pairs differ +34% (topology confirmed 08-14); E2 blocked by famfs. Direction PARKED |
| 2026-05-19 | [2026-05-19-baseline-objplace.md](2026-05-19-baseline-objplace.md) | DRAM-vs-CXL baseline; does sensitivity-aware object placement beat hotness/interleave? | CLOSED — latency 1.5×, BW 35.5 GiB/s/pair; interference 2.0–2.13× bw-bound; ObjPlace +14.3%/+118%/+315%, ~0% overhead. All 5 go/no-go gates passed |

**Headline numbers, current machine (NPS4, since ~2026-08-12):** DRAM per
quadrant 174.8 ns, read 68.8 GiB/s @8T, plain-write 34.3 (= read/2 exactly).
CXL node 4 (Pair A) 287 ns, read 45.6 GiB/s @16T, plain-write 27.9 (+22% over
shared-pipe prediction). Older numbers in the files above predate NPS4 —
DRAM figures are not comparable across the 2026-08-12 reboot.
