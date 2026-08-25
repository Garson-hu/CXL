# Experiment index

*One row per experiment file. A row gets its verdict when the experiment closes;
the file is frozen from that moment (see `../README.md` rules). Newest first.*

| Date | File | Question | Verdict |
|---|---|---|---|
| 2026-08-25 | [2026-08-25-direction-gates.md](2026-08-25-direction-gates.md) | Is CXL's write direction a separate, exploitable resource? (Gates 1–2 for Thesis v2) | **ACTIVE** — W0 quick-look done (+22% over shared-pipe); gates not yet run |
| 2026-08-11 | [2026-08-11-percard-prelim.md](2026-08-11-percard-prelim.md) | What can we learn about per-card behavior while the BIOS pairs the cards? (E1–E4 + NPS4 postscript) | CLOSED — E1 software split impossible; E3 tails benign, congestion real; E4 pairs differ +34% (topology confirmed 08-14); E2 blocked by famfs. Direction PARKED |
| 2026-05-19 | [2026-05-19-baseline-objplace.md](2026-05-19-baseline-objplace.md) | DRAM-vs-CXL baseline; does sensitivity-aware object placement beat hotness/interleave? | CLOSED — latency 1.5×, BW 35.5 GiB/s/pair; interference 2.0–2.13× bw-bound; ObjPlace +14.3%/+118%/+315%, ~0% overhead. All 5 go/no-go gates passed |

**Headline numbers, current machine (NPS4, since ~2026-08-12):** DRAM per
quadrant 174.8 ns, read 68.8 GiB/s @8T, plain-write 34.3 (= read/2 exactly).
CXL node 4 (Pair A) 287 ns, read 45.6 GiB/s @16T, plain-write 27.9 (+22% over
shared-pipe prediction). Older numbers in the files above predate NPS4 —
DRAM figures are not comparable across the 2026-08-12 reboot.
