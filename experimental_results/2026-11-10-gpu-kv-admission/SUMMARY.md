# Summary — GPU KV memory admission of external KV hits (RQ2 validation; 2026-11-10 → 2026-11-11)

**Status: COMPLETE 2026-11-11.** Exploratory study on branch `explore/gpu-kv-admission` (from
`explore/cxl-serving-scheduling-gap` cb7c4ba), never merged. The authoritative document is the report
`docs/experiments/2026-11-10-gpu-kv-admission.md` (summary; A root cause; B mechanisms; C end-to-end results: C1 mixed workloads,
C2 trace replays, C3 larger pool and model, C4 CXL; D cross-experiment analysis; E negative results; F implications and the
brief's success criteria; G correctness and validity; H limitations). This file is the self-contained summary for a reader who
opens the data directory: what was asked, what ran, what came out, what it means, where each number comes from and how to
regenerate tables and figures. `README.md` beside it describes the directories and the per-run files. Numbers are quoted from
the report; paths are relative to this directory unless they start with `benchmarks/`, `docs/` or `/mnt/`.

**Evidence labels.** MEASURED = real vLLM 0.31.0 + LMCache 0.5.5 serving with logging-only instrumentation (prototype runs name
their flags); SOURCE = read from the installed packages; PREVIOUSLY MEASURED = a closed experiment file of this project.
**Every host tier in this study is pinned DRAM. Nothing here is a CXL measurement** (§8).

## 1. Question and scope
The 2026-11-04 serving study found that requests whose KV is cached in host memory ("external hits") waited seconds under load
although loading the KV takes tens of milliseconds, and explained it from the source as a whole-prefix GPU KV reservation. The
brief of 2026-11-10 ("RQ2 validation: GPU KV memory admission") asks: what exactly delays an external hit (A), which minimal
change removes the unnecessary part (B), does that improve end-to-end serving (C, D) beyond one small GPU (E), with correctness
checks, negative results kept, and no forced positive conclusion. Constraints kept: earlier results and the research charter
untouched; all code behind flags, stock behaviour preserved; no privileged change to the CXL devices; branch not merged.

## 2. Platform
| | c28 (primary) | 16 GB nodes |
|---|---|---|
| GPU | RTX 4060 Ti 8 GB | RTX 4060 Ti 16 GB (same model) |
| CPU / RAM | 128 cores, 755 GiB | c60, c61, c66: EPYC 8124P 16 cores, 188 GiB; c73, c74: EPYC 7302P 16 cores, 125 GiB |
| host tier (pinned DRAM) | 320 GB (also 120 GB in the controlled trials) | 150 GB, 120 GB, 80 GB or 60 GB as the run says |
| GPU KV pool | pinned at 7,456 blocks (119,296 tokens) | pinned at 7,456 where compared with c28; 19,916 blocks = the node's own size; 2,560–14,912 in the mixed workloads |
| model | Qwen2.5-3B-Instruct-AWQ | the same; Qwen2.5-7B-Instruct-AWQ in one pair |
| software | vLLM 0.31.0, LMCache 0.5.5 (multi-process), Python 3.12 | a copy of c28's environment on the shared scratch file system |

No table compares runs across nodes: every family has its own stock run on its node. CXL: `/dev/dax0.0`, `/dev/dax1.0`,
`/dev/dax2.0` are root-only (checked 2026-11-10 15:55 and 2026-11-11 00:43); nothing was changed.

## 3. What ran — 181 server runs, 2026-11-10 15:55 → 2026-11-11 10:41 (`experiment-matrix.md` / `.csv`)
| family | where | what varied | raw data |
|---|---|---|---|
| A2 instrumented stock replays | c28 | tool-agent and conversation trace at 0.04× and 0.08× | `replay/*-base*` |
| A3 controlled reproduction; gate on / off | c28; c60 | free blocks relative to the probe's need, hit against miss, 114 trials | `A3/`, `E16/a3gate/` |
| B controlled scenarios | c66 | one mechanism per scenario: prefill in front (c1), reservation gate (c2), head-of-line blocking (c3), bounded reservation (c5) | `E16/c1c/`, `E16/c2b/`, `E16/c5/` |
| C1 mixed workloads | c60, c66; c74 | closed loop 1–16, open loop 0.5–4 requests/s, bursts, hit share; GPU KV pool 14,912 / 7,456 / 3,728 / 2,560 blocks; stock, existing options, P1, P2, P4, bypass alone | `E16/cc/`, `E16/ccb/` |
| C2 trace replays, primary | c28 | tool-agent and conversation, 0.04× and 0.08×, 320 GB; stock, existing options, ordering baselines, prototype versions and configurations | `replay/` |
| C2 overload variants | c60, c61 | bypass bound 3–100 s with and without the token mechanisms, block reservation off, one-flag variants, ordering baselines; conversation trace | `E16/X08/` |
| C2 capacity point (80 GB), intermediate load | c61, c66; c73 | stock, oracle priority, shortest-prompt-first, P1, P4, bypass alone; 0.06× | `E16/E/e-tool04-80-p7456-*`, `e66-*`; `E16/T06/` |
| C3 larger pool, larger model | c61, c66, c60 | pool 19,916 blocks at 0.04× and 0.08×; 7B model | `E16/E/` |
| G correctness | c66 | 48 prompts × five KV paths × five server configurations | `E16/correct/` |

Prototype configurations (`benchmarks/serving/kvadm/kvadm_policy.py`, environment variable `KVADM_POLICY`; nothing is active
without it): **P1** = `tokres=768,fastchunk=512,resvall,blkfirst` (token reserve and short steps); **P2** = P1 + `skip=3,hitres=600`
(bypass of a request that does not fit, bounded at 3 s, with 600 blocks kept for passed hits); **P3** = P2 + `agecap=20`;
**P4** = P1 + `skip=30,hitres=600`; **bypass alone** = `skip=<s>,hitres=600` with stock token rules; `storefix` = the store-counter
fix (included in every configuration above). Ordering baselines use vLLM's own `--scheduling-policy priority`:
**oracle hits-first** (priorities from the stock run), **shortest-prompt-first** (priority = number of prompt tokens).

## 4. Results

### 4.1 Cause (report A)
- A request whose KV is cached answers in 0.2–0.3 s on an idle engine and waits as long as an uncached one under load (3.3 s
  median, 8.2 s mean for host-dominant hits at the sustainable load; 19 s under overload).
- Where the waiting time goes, from a per-step attribution of every waiting interval (`replay/tables-adm-*-base.md`):
  **54–68 % token budget** — the waiting queue is scanned only with the tokens that running requests leave of the 2,048-token
  step, and one prefill leaves none; **10–35 % head-of-line blocking at the full-sequence block gate** once more than about
  75 % of the pool is in use; 5–16 % lookup and load step boundaries. The in-flight reservation that the earlier study blamed
  refused 17 of 4,924 attempts (sustainable load) and 9 of 6,527 (overload).
- Controlled trials (`A3/tables-a3-a3.md`): a hit and a miss of the same length are refused and admitted at the same
  free-block counts; the threshold is the request's own need; the number of running requests is irrelevant beyond the blocks
  they hold.
- Side finding (A5, `replay/tables-store-loss.md`): the LMCache connector advances its stored-token counter at every poll of a
  waiting request, so retried requests skip storing their new KV — 6 % of the KV at the sustainable load, 31–33 % under
  overload, also in the un-instrumented runs of 2026-11-05. A one-line fix stores all of it (108.9 against 73.8 GB).

### 4.2 Mechanisms (report B)
| mechanism | controlled result | verdict |
|---|---|---|
| token reserve + short steps | hit behind a 28k prefill: first token after 0.9–1.1 s instead of 4–8 s; blocker +10–18 % | works for the first token; request time unchanged behind 8k / 16k prefills |
| bypass of a request that does not fit (bounded) | requests that fit: 0.3–0.8 s instead of 8 s | works; the bound decides how much (§4.4) |
| bounded block reservation for passed hits | passed hit admitted 0.3–0.4 s later than in stock instead of 1.4 s | works in the scenario built for it; a small net cost in the overloaded replay (−28 % with it, −33 % without) |
| store fix | 108.9 GB stored instead of 73.8 GB, no class slower | works |
| reservation of loads relaxed (`alpha=0`) | hit admitted 2.4 s sooner, one preemption per trial | rejected |
| compute fallback | never applicable (the same gate refuses computing) | rejected |
| chunked loading | not expressible; no earlier admission | rejected (source) |

### 4.3 Controlled mixed workloads (report C1; `E16/cc/tables-cc-matrix.md`, `E16/ccb/tables-ccb-matrix.md`)
With no memory pressure at all (pools 14,912 and 7,456: no refused attempt) hits wait 3–6 s at saturation; the token mechanisms
bring them to 1.2–1.8 s (2.5–3.5× sooner), the misses pay +7 to +30 %, throughput −1 to −5 %. Under memory pressure (pools 3,728
and 2,560) the token mechanisms alone stop working in the open loop above capacity and the bypass is needed; with a 30 s bound
the hits' p95 falls from 11.7 s to 2.2–3.0 s, the misses are served sooner than in stock and the mean request time is 19–27 %
lower; the bypass alone gives the misses the larger share (−24 %, −37 %) with no throughput loss and is stock-like elsewhere.
Client-labelled hits-first priority is the strong existing option wherever a queue forms.

### 4.4 Trace replays (report C2) — the cross-load matrix
Each column is one replay family with its own stock run; each cell: change of the mean TTFT of all requests / of the mean
request time / of the mean TTFT of the stock run's misses, and the longest TTFT (s) (`replay/tables-cross-load.md`).

| configuration | sustainable, 320 GB (c28) | sustainable, 80 GB (c61) | sustainable, 80 GB (c66) | intermediate, 80 GB (c73) | overload, 320 GB (c28) | overload, 150 GB (c60) | overload, 150 GB (c61) | overload, large pool (c66) |
|---|---|---|---|---|---|---|---|---|
| stock: mean TTFT / mean request time / misses' mean TTFT / longest TTFT (s) | 4.93 / 11.4 / 7.89 / 44 | 5.41 / 12.2 / 8.12 / 52 | 5.37 / 12.1 / 8.06 / 52 | 9.93 / 19.3 / 12.30 / 61 | 14.67 / 27.6 / 16.64 / 53 | 14.75 / 27.7 / 16.71 / 53 | 14.15 / 26.8 / 16.13 / 52 | 12.72 / 32.4 / 14.53 / 46 |
| oracle hits-first priority | -20 % / -7 % / +2 % / 43 | -19 % / -7 % / +2 % / 49 | – | -32 % / -15 % / +2 % / 66 | -33 % / -16 % / +15 % / 56 | – | – | – |
| shortest-prompt-first priority | – | -28 % / -7 % / -8 % / 48 | -28 % / -7 % / -8 % / 48 | -43 % / -18 % / -15 % / 151 | -49 % / -21 % / -7 % / 249 | – | -49 % / -20 % / -8 % / 259 | -31 % / -10 % / -9 % / 62 |
| oracle shortest-compute-first priority | – | – | – | – | – | – | -52 % / -24 % / -9 % / 228 | – |
| shortest-prompt-first with aging (1 ms per token on c61; 3 ms on c60) | – | – | – | – | – | -50 % / -24 % / -8 % / 96 | -30 % / -14 % / -9 % / 52 | – |
| shortest-prompt-first + token mechanisms (P1) | – | -41 % / -10 % / -4 % / 51 | -41 % / -10 % / -4 % / 51 | – | – | – | – | – |
| token mechanisms (P1; with the 3 s bypass, P2, on c28 at the sustainable load and on c73) | -24 % / -7 % / +6 % / 40 | -23 % / -6 % / +8 % / 52 | – | -23 % / -7 % / +11 % / 63 | +9 % / +9 % / +28 % / 63 | – | – | +29 % / +22 % / +50 % / 68 |
| token mechanisms + bypass, 3 s (P2) | – | – | – | – | -4 % / +2 % / +29 % / 63 | -2 % / +3 % / +28 % / 63 | – | – |
| bypass alone, 3 s | – | – | – | – | – | -10 % / -6 % / -2 % / 56 | -12 % / -6 % / -1 % / 56 | – |
| bypass alone, 10 s | – | – | – | – | – | -23 % / -13 % / -5 % / 54 | – | – |
| bypass alone, 30 s | – | – | -16 % / -5 % / -4 % / 49 | -25 % / -10 % / -6 % / 64 | -28 % / -15 % / -6 % / 58 | -28 % / -15 % / -5 % / 58 | – | – |
| bypass alone, 100 s | – | – | – | – | – | -39 % / -20 % / -4 % / 75 | – | – |
| token mechanisms + bypass, 30 s (P4) | -34 % / -10 % / +3 % / 43 | -33 % / -9 % / +4 % / 52 | – | -32 % / -11 % / +8 % / 65 | – | -28 % / -10 % / +16 % / 61 | – | – |
| token mechanisms + bypass, 100 s | – | – | – | – | – | -45 % / -20 % / +9 % / 109 | – | – |

Conversation trace (`replay/tables-cross-load-conv.md`):

| configuration | conversation, sustainable, 320 GB (c28) | conversation, overload, 320 GB (c28) | conversation, overload, 150 GB (c60) |
|---|---|---|---|
| stock: mean TTFT / mean request time / misses' mean TTFT / longest TTFT (s) | 6.32 / 18.6 / 7.52 / 41 | 16.89 / 39.9 / 18.10 / 54 | 16.96 / 40.0 / 18.18 / 54 |
| shortest-prompt-first priority | -15 % / -1 % / -7 % / 45 | – | -32 % / -8 % / -12 % / 315 |
| bypass alone, 30 s | – | – | -22 % / -9 % / -8 % / 61 |
| token mechanisms + bypass, 3 s (P2) | – | +6 % / +6 % / +15 % / 67 | +6 % / +6 % / +15 % / 67 |
| token mechanisms + bypass, 30 s (P4) | -21 % / -4 % / -2 % / 44 | – | -7 % / +2 % / +7 % / 65 |

What it says:
1. The token mechanisms help where the queue drains (−23 to −26 % mean TTFT at the sustainable load, −23 % at 0.06×) and hurt
   under sustained overload (+9 %; +29 % on the large pool).
2. The bypass alone helps at every load with no class slower on average (−16 %, −25 %, −28 %; mean request time −5 %, −10 %,
   −15 %) and keeps the longest wait within about 6 s of stock. Its bound decides the size: 3 s −10 %, 10 s −23 % (no
   measurable cost), 30 s −28 %, 100 s −39 % (longest wait 75 s) (`E16/X08/tables-primary-x08-c60.md`, figure 8).
3. Both together (P4) are the best prototype configuration up to the intermediate load (−33 %, −32 %) and no better than the
   bypass alone under overload.
4. **Shortest-prompt-first — an option of the stock scheduler — does as well or better on the means at every load** (−28 %,
   −43 %, −49 %; −31 % on the large pool; the misses faster every time). In its plain form it has no bound: longest TTFT 48 s
   at the sustainable load (stock 52 s), 151 s at 0.06× (61 s), 249–259 s under overload (53 s), 315 s on the conversation
   trace. With an aging term in the priority (send time in ms + 1 ms per prompt token) it gives −30 % under overload with the
   longest wait of stock — the result of the bypass bounded at 30 s, without a prototype.
5. Knowing the cache adds little to the ordering: oracle hits-first reaches −19 to −33 %; oracle shortest-compute-first −52 %
   against −49 % for the prompt length.
6. The token reserve adds to that ordering where the queue drains: both together reach −41 % at the sustainable
   load (p95 −47 %, misses still 4 % faster than in stock); under overload it adds nothing.
7. No configuration changes throughput, makespan or GPU utilization by more than 2–3 %: every gain is a gain of order.

### 4.5 Beyond the 8 GB GPU (report C3; `E16/E/tables-primary-*.md`)
A pool 2.67× as large removes every refusal and preemption at the sustainable load and shortens the tail (p95 −20 %); the token
budget is exhausted for the same fifth of the run, a hit that arrives during a prefill still waits 15.8 s, and the token
mechanisms recover 21 % of mean TTFT there, 23 % on the small pool of the same node, 17 % with the 7B model. Under overload on
the large pool the token mechanisms are harmful (+29 %; the saturated token budget was the only admission control left) and
shortest-prompt-first still helps (−31 %). One GPU compute class only.

### 4.6 Correctness (report G)
The KV paths that run alone give the same text in every configuration, request by request (48 / 48 between stock and each
prototype run). Reusing KV instead of computing changes 1–3 of 48 texts on the stock server already (different chunking of the
uncached tail). Two stock replays agree on 543 of 544 texts; any change of scheduling, stock options included, changes 2–4 %.
No block leak, no repeated load, 4–12 preemptions against 5 in stock. Repeats agree within 1 % on the all-request means.
Instrumentation: 6 µs per 129 µs scheduler call. Three measured requests were lost to a client-side connection reset
before the client was made to retry.

## 5. Answers to the brief's questions (report F)
1. *Genuine bottleneck?* The delay is genuine and repeatable; it is a scheduling delay, not specific to external hits.
2. *Whole-prefix reservation the cause?* No.
3. *Practical mechanism?* Yes: token reserve, bounded bypass, and — simplest — the existing priority scheduling with the
   prompt length as priority.
4. *End-to-end improvement?* In latency, a quarter of the mean TTFT at the sustainable load and a quarter to a half under
   overload, by reordering; not in throughput. The prototype's best configuration is of the same order as shortest-prompt-first
   at the sustainable load (and adds 13 points on top of it) and is matched or beaten by it under overload.
5. *Beyond the 8 GB GPU?* The token-budget half yes; the memory half is a property of pool against workload.
6. *Host capacity?* Capacity and scheduling multiply: 80 → 320 GB gives −9 % mean TTFT, the mechanisms the same relative gain
   at both; under overload the stock store path loses a third of the KV, which bounds what capacity can do.
7. *A research direction?* The bottleneck is real but not specific to GPU KV admission, and its largest part — a bounded
   worst case included — has a remedy in the stock scheduler; what the admission mechanisms add is the token reserve at the
   sustainable load. The open points are listed in report F.7.
Success criteria of the brief: 1–3 met (the bottleneck under a different name), 4 and 6 partly, 5 depends on the mechanism.

## 6. Negative results (report E, condensed)
The starting hypothesis; `alpha=0`; compute fallback; chunked loading; synchronous scheduling and the prefill cap; prototype
v1 (store loss) and v1.1 (unbounded passing, 78 s waits); the token mechanisms under overload (+9 %, +29 % on the large pool,
+11 % with synchronous scheduling); the 3 s bound chosen from a controlled scenario; the prototype against the ordering
baselines; the token mechanisms on the conversation trace under overload; first token ≠ last token; no capacity gain anywhere;
starvation under shortest-prompt-first.

## 7. Limitations (report H)
One engine version; one GPU compute class (8 and 16 GB RTX 4060 Ti); two models; host tier = DRAM; two traces, first 100–200
trace seconds, three speeds; oracle baselines use a previous run; the prototype is a policy module (0.3 ms per step);
parameters varied on one replay; most configurations run once.

## 8. CXL
Blocked for the whole study (`/dev/dax*` root-only; `dax2.0` reserved for another project and not opened). The mechanisms act
in the scheduler, before a load is issued and after it has arrived, so they do not depend on the medium; lookup and retrieval
cost on CXL and the effect of concurrent stores are not measured.

## 9. Data map
See `README.md` for the directory table and the per-run file formats. In git: the small artifacts (configuration, client
records, per-request and admission tables, summaries, figures, `experiment-matrix.*`). On c28 only
(`/mnt/local/ghu4/results/2026-11-10-gpu-kv-admission/`, with a copy of the 16 GB-node results under `E16/`): the admission,
request and step streams, sampler output, server and LMCache logs.

## 10. Regenerating tables and figures (`benchmarks/serving/`)
```
post_adm.sh <dir> <tag>...            # per replay: analyze_replay.py, analyze_adm.py, adm_first_attempts.py
post_cc.sh <dir> <tag>...             # per controlled run
tables_adm_all.sh                     # every replay family: tables-primary-*, tables-tails-*, tables-d-*, the cross-load matrices
table_cc_matrix.py, table_cc.py, table_s4.py, table_c1.py, table_c5.py   # controlled workloads and scenarios
check_runs.py, store_loss.py, adm_overhead.py, matrix_adm.py             # correctness, store loss, overhead, configuration matrix
figs_adm.py (figures A1, A2, 1, 2), figs_adm2.py (3, 3b, 4, 5, 6, 7), fig_bypass_bound.py (8)
```
Each script's first lines give its exact arguments; the calls used for the report are in the report's figure and table
references and in `WORKLOG.md`.

## 11. Provenance
Branch `explore/gpu-kv-admission`; prototype module versions v1 537d2ff, v1.1 1b5fa31, v1.2 9f3b1c8, v1.3 68acb27, v1.4 49c3585
(+ logging c68ce39); client retry fb95dcb; report and tools in the commits of 2026-11-10 and 2026-11-11. Job scripts of the
16 GB nodes: `/mnt/beegfs/ghu4/kvadm/job_*.sh` (copied to `E16/jobs/`). The c28 queue: `replay/plan.txt`, `chain.txt`, `done.txt`.
