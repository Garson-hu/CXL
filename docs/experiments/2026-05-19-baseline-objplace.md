# 2026-05-19 — DRAM/CXL baseline + ObjPlace evaluation

**STATUS: CLOSED (frozen). Verdict in `INDEX.md`.**
Machine state at the time: NPS1 (node 0 = all 256 CPUs + 773 GB DRAM), node 1 =
CXL 2-card pair (then Pair B, dax2.0-era mapping), kernel 6.14.11+. All numbers
below predate the 2026-08-12 NPS4 reboot — DRAM figures not comparable to later
files. Raw CSVs: `experimental_results/2026-05-19-baseline-objplace/`
(13 timestamped run dirs; migrated from `benchmarks/results/` 2026-08-25).

## 1. Hardware characterization (phase1)
| Metric | DRAM (node 0) | CXL (node 1) | Ratio |
|---|---:|---:|---:|
| Pointer-chase latency | 182–184.9 ns | 276.5–279 ns | **1.50–1.53×** |
| 1-thread stream-read | 32.2 GiB/s | 19.5 GiB/s | 0.60× |
| 1-thread stream-write (plain stores) | 31.1 GiB/s | 18.5 GiB/s | 0.59× |
| 1-thread random-read | 2.30 GiB/s | 1.58 GiB/s | 0.69× |
| Saturation | ~309 GiB/s @128T | **35.5 GiB/s @4T, flat to 32T** | ~1/9 |

Placement integrity 630/630 sampled pages correct. **Conclusion: latency is fine
(~1.5×); the pair's bandwidth ceiling (35.5 GiB/s, hit at 4 threads) is the
binding constraint.**

## 2. Co-tenant interference (phase2 → 2.2 → confirm)
Phase 2 (shared cores, up to 8.75×) **REJECTED** as CPU artifact — methodology
fix recorded in `METHODOLOGY.md`. Disjoint-core results (phase 2.2 + median-of-5
confirm):
| CXL victim | 2 threads | 4 threads |
|---|---:|---:|
| stream-read (bandwidth-bound) | **2.01×** | **2.13×** |
| random-read (latency-bound) | ~1.1× | ~1.23× |
| any victim on DRAM | ~1.0× | ~1.0× |

**Claim: CXL co-tenant interference is severe for bandwidth-bound victims,
mild for latency-bound, absent on DRAM (headroom).**

## 3. ObjPlace evaluation (integ + block-1 + block-2)
API = manual hand-placement within noise (embedding per-step 36.6 vs 36.9 ms,
<1%): wins come from policy, not API tricks.

| Target | Result |
|---|---|
| T1 = manual | embedding +0.2%, gnn −0.1% |
| T2 vs interleave (skewed embedding) | **+14.3%** |
| T3 bandwidth protection under aggressor | **+315%** vs all-CXL (69 vs 17 GiB/s) |
| T4 vs hotness-only (sensitivity case) | **+118%** (31 vs 14 GiB/s) |
| T5 overhead | 0.2% (`obj_create` 10.8 µs; rebalance 0.26 µs/obj; 104 B/obj) |

Pressure sweep (vs hotness-only): +67% idle → +92/116/115/116% at 1/2/4/8
aggressor threads — **pressure-aware**. DRAM-budget sweep: 0% when ≤1 object
fits (degenerate), +22%/+18% at 40%/60% budgets. GNN gather: skewed (α=1.2)
**+8.3%** vs interleave; uniform **−11.6%** (planner lacks INTERLEAVE candidate
— known limitation, `DESIGN.md` §6).

## 4. Survived vs rejected
Survived: latency 1.5× / BW 35.5; 2.0–2.13× bw-bound interference; ObjPlace
= manual, beats interleave ~15% (skewed) and hotness-only (+118%, budget,
pressure). Rejected: "9× interference" (CPU artifact); "38% skew win" (noise);
KV layer-split benefit (null); win on uniform access (interleave wins).

## 5. Go/no-go gates (all passed)
latency ≤2.5× ✓ (1.53×) · BW ≥30 GiB/s ✓ (35.5) · interference ≥1.5× ✓
(2.0–2.13×) · beats interleave ≥15% ~✓ (14.3%) · beats hotness where
sensitivity matters ✓ (+118%).

## Reproduce
```
cd system/placement && make && cd ../.. ; (cd benchmarks/memory && make)
./system/placement/test_objplace
./scripts/run-dram-cxl-baseline.sh          # phase1
python3 benchmarks/phase22.py               # interference
python3 benchmarks/integ.py                 # API = manual
python3 benchmarks/eval_objplace.py         # block-1 (T1–T5)
python3 benchmarks/eval_block2.py           # pressure/budget/gnn/overhead
```
