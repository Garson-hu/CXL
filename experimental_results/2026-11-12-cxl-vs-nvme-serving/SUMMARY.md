# Summary — CXL vs. NVMe memory expansion for LLM serving (2026-11-12 → 2026-11-14)

**Status: CLOSED 2026-11-14.** Exploratory study on branch `explore/cxl-vs-nvme-serving` (from `explore/gpu-kv-admission`), never
merged. The authoritative document is the report `docs/experiments/2026-11-12-cxl-vs-nvme-serving.md` (summary; A
configuration; B matrix; C results per experiment family; D causal analysis; E cross-experiment analysis; F negative results;
G limitations; H final answers; I correctness checklist). This file is the self-contained summary for a reader who opens the
data directory; `README.md` beside it describes the directories and per-run files. Numbers are quoted from the report; paths
are relative to this directory unless they start with `benchmarks/`, `docs/` or `/mnt/`.

**Evidence.** Everything is MEASURED on the real devices unless marked **model** (the offline trace-capacity analysis in
`trace-model/` and its timed variant, `pairs_tier.py timed`). No DRAM stand-in is used for CXL anywhere.

## 1. Question and constraints

*Under a fixed host DRAM budget, how does CXL memory expansion compare with NVMe-based KV cache expansion in end-to-end LLM
serving?* (brief of 2026-11-12). Kept constraints: 80 GiB DRAM KV budget enforced and verified at the cache level; 512 GiB
extension on either medium with matched logical capacity; the real CXL path with residency checks; O_DIRECT for the SSD and no
system-wide page-cache clearing; no new scheduler or replacement algorithm; `/dev/dax2.0` (another project's) never opened;
nothing reconfigured on the node; the store-counter fix of 2026-11-10 in every LMCache configuration; invalid runs kept and
excluded.

## 2. Platform

| | c28 |
|---|---|
| GPU | 1× RTX 4060 Ti, 8 GiB, PCIe 4.0 ×8 (host → GPU 12.4 GiB/s measured) |
| CPU / DRAM | 128 cores, 755 GiB (budget for KV: 80 GiB, LMCache L1) |
| CXL | `/dev/dax1.0` 269.5 GiB + `/dev/dax0.0` 242.5 GiB = 512 GiB, two windows over one pair of CZ120 cards, Device-DAX |
| NVMe | `/mnt/local` (ext4), link PCIe 4.0 ×2 of ×4; 2.9 GiB/s read through LMCache with O_DIRECT |
| model, software | Qwen2.5-3B-Instruct-AWQ (36 KiB of KV per token); vLLM 0.31.0, LMCache 0.5.5 multi-process; GPU KV pool 6,400 blocks in every run |

Configurations: `none` (vLLM alone), `dram80` (80 GiB DRAM L1), `hyb` (hybrid L1 = 80 GiB DRAM + 512 GiB CUDA-registered
Device-DAX, objects exist once; evicts from 473.6 GiB), `daxl2` (80 GiB DRAM L1 + CXL L2 adapter, inclusive; evicts from
409.6 GiB), `ssdn` (80 GiB DRAM L1 + `fs_native` L2 on NVMe, O_DIRECT, 512 GiB; evicts from 409.6 GiB); sensitivity:
`dram20`, `hyb20`, `ssdn20` (the DRAM part at 20 GiB instead of 80 GiB) and `dram592` (one DRAM L1 of 592 GiB without an
extension: the all-DRAM reference), on the conversation window at 0.08× only.

## 3. What ran — 86 runs: 58 results, 4 GPU-memory records, 3 functional checks, 8 superseded smoke runs, 13 void (`experiment-matrix.md` / `.csv`)

| family | what | raw data |
|---|---|---|
| P0 path validation | short runs with content hashes for every tier; full 512 GiB mapping | `P0/`, `P0/tables-p0.md`, `*-residency.txt` |
| GPU memory | cost of CUDA-registered host memory; fit of the full hybrid | `env/` |
| A single-request retrieval | 10 tier variants × 6 prefix lengths × 5 repetitions, idle server | `A/`, `A/tables-a.md` |
| C equal-hit comparison | 48 pre-stored prefixes, Poisson 0.5 / 2 / 4 / 8 req/s, identical hits in 5 tiers | `C/`, `C/tables-c.md` |
| D concurrent retrieval | bursts of 1–16 simultaneous hits, 6 tier variants | `D/`, `D/tables-d.md` |
| B end-to-end replays | Mooncake conversation and tool-agent traces: 0–400 s at 0.08×, 0–200 s at 0.04×, conversation 0–900 s at 0.08× (11,250 s) and 0–400 s at 0.16× (overload); same requests in every configuration | `B/`, `B/tables-b.md` |
| E traffic | per-second KV bytes per medium, overlap, write-side accounting — from the B runs | `B/tables-e.md`, `B/tables-writes.md`, `B/*-traffic.csv` |
| trace model | offline LRU over both traces (**model**) | `trace-model/` |

## 4. Results

**Verdict.** With the DRAM KV budget fixed at 80 GiB, 512 GiB of additional KV cache is worth having, and on this node it is
worth the same whether it is CXL memory or a properly configured NVMe tier: 16–24 % less prefill work at high load, roughly
half the TTFT, 6 % more throughput at saturation, the two media within 1 % of each other in every replay. CXL's advantage is
real per hit and reaches end-to-end metrics only where a hit is not queued behind the GPU (2.5–6.4 % of the requests of the
replayed traces).

### 4.1 One hit (A; `A/tables-a.md`)
TTFT of a 16K-token prefix on an idle server: GPU prefix cache 44 ms; DRAM 94 ms; CXL L1 93–94 ms; CXL as L2 114 ms; NVMe
290 ms (Python adapter 315 ms); recompute 3,385 ms. The GPU reads registered CXL memory at 12.4 GiB/s (its link's rate, as
from DRAM) and writes it at 3.89 GiB/s (DRAM: 12.14 GiB/s; unregistered CXL: 11.5 GiB/s). A file tier with buffered I/O
"reads" at 32.9 GiB/s from the page cache — the control that shows why O_DIRECT is required.

### 4.2 Identical hits under load and in bursts (C, D; `C/tables-c.md`, `D/tables-d.md`)
CXL L1 equals DRAM in every quantile at every rate (TTFT p50 104 / 147 / 232 / 1,375 ms against 105 / 146 / 234 / 1,376 ms).
NVMe: 162 / 250 / 400 / 1,690 ms (+55–71 % below saturation); 2.2–2.9× DRAM in bursts (940 against 430 ms at 16 simultaneous
8K hits). Bottlenecks by tier: GPU link and LMCache's single transfer thread (DRAM, CXL L1), LMCache's four load workers (CXL
L2, media still at 30 GiB/s), the device (NVMe, 2.9 GiB/s at any concurrency). At saturation all cached tiers complete
5.0–5.3 requests/s.

### 4.3 Trace replays (B; `B/tables-b.md`)

| window | cached share: DRAM only → + 512 GiB | recomputed tokens | TTFT p50 s: DRAM only → CXL hybrid / NVMe | TTFT mean s | completed req/s |
|---|---|---|---|---|---|
| conversation, 0.04× | 0.093 → 0.182 | −9.8 % | 3.92 → 3.20 / 3.19 | 7.04 → 6.36 / 6.36 | equal |
| tool-agent, 0.04× | 0.383 → 0.446 | −10.2 % | 2.08 → 1.49 / 1.50 | 5.81 → 5.15 / 5.15 | equal |
| conversation, 0.08× | 0.096 → 0.238 | −15.8 % | 16.71 → 8.67 / 8.62 | 22.42 → 13.32 / 13.25 | equal |
| tool-agent, 0.08× | 0.396 → 0.495 | −16.3 % | 12.40 → 6.30 / 6.31 | 19.78 → 11.60 / 11.47 | equal |
| conversation, 0.08×, long (11,250 s) | 0.097 → 0.309 (CXL) / 0.302 (NVMe) | −23.5 % / −22.7 % | 14.46 → 6.15 / 6.24 | 21.42 → 9.72 / 9.85 | equal |
| conversation, 0.16× (overload) | 0.130 → 0.208 / 0.209 | −8.9 % / −9.0 % | 857 → 793 / 791 | 836 → 755 / 753 | 0.287 → 0.305 / 0.306 |

- The gain reaches hits and misses alike through the GPU's queue (GPU busy 0.88 → 0.78–0.81 at 0.08×).
- The NVMe's load inside the cache server takes 78–106 ms at the median (328–410 ms at p95); it runs while the request waits
  for the GPU and shows only on hits that find the GPU free: +45 to +116 ms at the median.
- Long window: the hybrid keeps more (28 of 2,728 requests) because it is one exclusive level of 592 GiB against an inclusive
  second level of 512 GiB — tier structure, not speed: the same CXL memory as an inclusive L2 (`b-conv08L-daxl2`) has the
  NVMe's cached tokens in 2,727 of 2,728 requests (0.302; TTFT p50 6.32 s, mean 9.88 s). In that run LMCache's DAX adapter
  stalls at two of its five eviction batches (it deletes ≈ 9,320 keys under the lock its lookups need, with a quadratic
  de-duplication: 4.9 s for the loop alone): 14 requests are 2–10 s later; without the eight worst the paired mean
  difference to the NVMe run is +5 ms, the median −5 ms.
- Where the hit rates are equal the hybrid is the slower of the two by 0.3–1 % of the mean TTFT (slow store direction).
- Overload: with default settings vLLM's engine died twice (LMCache's 300-s read lock on looked-up chunks expires while the
  request waits; vLLM's default failure policy and an assertion end the engine) — `void/b-conv16-*`. The table's row is the
  repeat with `--l1-read-ttl-seconds 7200`. The lookup runs a median 377–418 s ahead of the service there.
- DRAM budget of 20 GiB instead of 80 GiB (conversation, 0.08×): the same cached share (0.238) and recomputed tokens with
  both extensions; TTFT p50 8.69 s (CXL hybrid) / 8.62 s (NVMe), mean 13.35 / 13.25 s. The extension serves nearly every host
  hit; the NVMe loads for 262 requests instead of 193 (87.7 instead of 68.7 GiB) and is visible, as before, only on hits that
  find the GPU free (6.2 % of the requests, +71 ms at the median). The 20 GiB and 80 GiB hybrids differ only between 216 s
  and 996 s — one stores into CXL memory, the other still into DRAM — and only there are the prefills of the first longer
  (+0.81 %, 90 % of the requests): the store direction is the cause of the hybrid's deficit. 20 GiB of DRAM alone
  (`b-conv08-dram20`) is nearly no host cache: cached share 0.048 (0.045 without LMCache), TTFT p50 22.66 s, mean 27.59 s;
  from that base the extension removes 20.0 % of the recomputed tokens and 62 % / 52 % of the TTFT median / mean (from the
  80 GiB base: 15.8 %, 48 % / 41 %).
- All 592 GiB as DRAM (reference; conversation, 0.08×): the same cached tokens on every request as with either extension.
  The first 150 s of the reference run are disturbed (the cache server was still touching its 592 GiB pool when the replay
  started; 29 requests are 1–8 s late) and are left out: on the other 1,139 requests the hybrid is +0.09 s (0.7 %) and the
  NVMe configuration +0.02 s (0.1 %) behind the reference at the mean, with a cache server of 81 GiB instead of 593 GiB.

### 4.4 Traffic on the CXL memory (E; `B/tables-e.md`, `B/tables-writes.md`)
2–20 MiB/s of reads and 22–74 MiB/s of writes on average; busiest second 2.1 GiB read on the GPU's path (2.9 GiB through the
L2 adapter), 0.25 GiB written (5–6 % of the pair's ≈ 46 GiB/s). 38–47 % of the retrieves at 0.08× and 0.16× meet a pending store as operations, but the copies never overlap on
the hybrid's path (one transfer thread; 0.00 s). CXL L2 loads run at half their rate or less next to a store (30 → 15.5 GiB/s, 29 → 11.5 GiB/s in the long window; about
one second of loads per replay; medium or CPU not separated). 79–86 % of the KV written to an extension is not read again
within the window.

### 4.5 Correctness (report I)
Residency by content: 85 / 85, 155 / 155, 35 / 35 L1 objects and 340 / 340, 592 / 592 L2 slots on the device; no DRAM copy of
CXL-resident KV; cache server RSS 80.9–81.2 GiB in every replay; NVMe device bytes read = bytes loaded, page cache empty;
identical requests, GPU pool and correctness fix in every configuration; a request counts as completed only with an output
token; outputs identical for 99.2 % of the requests between two extension configurations.

## 5. Answers to the brief's final questions (report H, condensed)

1. *Strongest evidence for CXL expansion:* expansion removes 16–24 % of prefill at high load and halves TTFT; a CXL hit is
   indistinguishable from a DRAM hit, which no other extension medium here achieves.
2. *Where CXL beats NVMe:* hits that are not queued behind the GPU (identical hits below saturation +55–71 % for NVMe; bursts
   2.2–2.9×); and when the cache fills (more unique capacity). Not at high load with queues, not under overload.
3. *Why:* one extra stage (SSD → DRAM at 2.9 GiB/s) against a direct GPU copy at 12.4 GiB/s; it matters only when it is on the
   critical path.
4. *Can SSD caching match it:* in these replays it already does with the stock native adapter and O_DIRECT; for unqueued hits
   the device's read rate remains.
5. *Bottlenecks after expansion:* the GPU — prefill of what is not cached, the reuse ceiling of the trace, the GPU link and
   the single transfer thread on hits.
6. *CXL read/write concurrency:* not relevant with one small GPU.
7. *What remains:* serving points where retrieval is on the critical path; the time between lookup and service under
   overload; what is written to the extension; the GPU-memory cost of registered memory; several GPUs on one CXL pair.

## 6. Negative results (report F, condensed)
CXL is not faster end to end than NVMe in any replay; the hybrid is slightly slower when hit rates are equal; its one hit-rate
advantage is capacity; throughput does not change below saturation; under overload the GPU stays the bottleneck and the stock
stack crashes; 79–86 % of the extension's writes are never read; registration costs 1.2 GiB of an 8 GiB card; no evidence
that duplex traffic matters here.

## 7. Limitations (report G)
One 8 GiB GPU and a 3B model; the NVMe on half of its lanes; `dax0.0` / `dax1.0` are one pair of cards; the DRAM budget is
enforced at the cache level; one run per cell; traffic measured as application copies, not by hardware counters; the overload
round needs two non-default settings; the hybrid and the L2 tiers differ in unique capacity.

## 8. Data map
`README.md` lists every directory and file type. In git: per-run `*-meta.txt`, `*-driver.txt`, `*-client.jsonl`, the analysis
outputs (`*-tier.json`, `*-tier-requests.csv`, `*-requests.csv`, `*-traffic.csv`, `*-tier-timeline.csv`), all tables, figures
and the plan / done files. Not in git (on c28, `/mnt/local/ghu4/results/2026-11-12-cxl-vs-nvme-serving/`): `*-kvevents.jsonl`,
`*-vllmevt.*.jsonl`, `*-steps.csv`, sampler and server logs.

## 9. Regenerating tables and figures (`benchmarks/serving/`)
```
analyze_tier.py <dir> <tag>                      # A / C / D: per-request time line
analyze_tier_replay.py <B> <tag>                 # B / E: <tag>-tier.json, -tier-requests.csv, -traffic.csv
table_tier_p0.py <P0> tag ...                    # P0/tables-p0.md
table_tier_a.py <A> <figs> tag=label ...         # A/tables-a.md, figs/figA1..A4
table_tier_cd.py c|d <dir> <figs> tag=label ...  # tables-c.md / tables-d.md, figs/figC*, figD*
table_tier_b.py <B> <figs>                       # B/tables-b.md, B/tables-e.md, figs/figB1..B5, figE1
writes_tier.py <B>                               # B/tables-writes.md (all replays)
pairs_tier.py <B> pair|cached|l2pair|l2tags|l2direct|overload|lookups|since|startup|timed ...   # paired per-request numbers, lookup timing, timed model
matrix_tier.py <results>                         # experiment-matrix.md / .csv
trace_capacity_tier.py <csv> <png>               # trace-model/, figs/figT1
check_outputs.py <dir> <ref tag> <tag ...>       # output equality
verify_residency.py <tag>-kvevents.jsonl         # residency check (needs the event mirror on c28)
```

## 10. Provenance
Branch `explore/cxl-vs-nvme-serving`; harness, hook and analysis scripts in `benchmarks/serving/`; queue record in `plan.txt`,
`done.txt`, `chain.txt`; environment inspection in `env/inspect-2026-11-12.txt`. Earlier studies cited: 2026-11-04
(`docs/experiments/2026-11-04-cxl-serving-scheduling-gap.md`) and 2026-11-10 (`docs/experiments/2026-11-10-gpu-kv-admission.md`).
