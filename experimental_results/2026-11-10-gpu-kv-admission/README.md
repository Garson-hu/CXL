# Raw data of docs/experiments/2026-11-10-gpu-kv-admission.md

Start with `SUMMARY.md` in this directory: the self-contained summary of the study (question, platform, every run, results,
answers to the brief's questions, negative results, limitations, data map, how to regenerate).

Collected on 2026-11-11 with `benchmarks/serving/collect_adm.sh` from `/mnt/local/ghu4/results/2026-11-10-gpu-kv-admission` (c28, local NVMe) — which also holds a full copy of
the runs made on the 16 GB RTX 4060 Ti nodes (`E16/`, copied from `/mnt/beegfs/ghu4/kvadm/results`).

| directory | content |
|---|---|
| `replay/` | trace replays on c28 (Experiment D and the instrumented baselines of Experiment A): `plan.txt` (the queue), `chain.txt` / `done.txt` (start and end of every run), per-run files, `tables-adm-<tag>.md` (admission analysis), `tables-first-<tag>.md` (first admission attempts by occupancy), `tables-d-*.md` (configuration comparisons), `tables-store-loss.md`, `replay-summary.csv` |
| `A3/` | controlled reproduction on c28 (`tables-a3-a3.md`) |
| `smoke/` | smoke runs of the instrumentation |
| `E16/a3gate/` | the A3 trials with the full-sequence gate on and off (node c60) |
| `E16/c1c/`, `E16/c2b/`, `E16/c5/` | controlled scenarios of Experiment B: compute contention (c1), reservation gate (c2) and head-of-line blocking (c3), bounded reservation (c5) |
| `E16/cc/` | mixed workloads of Experiment C (pools 2,560 / 3,728 / 7,456 / 14,912 blocks; `s4-*` = hit-share sweep) |
| `E16/E/` | Experiment E (replays on the larger pool and with the 7B model) and the 80 GB capacity point of Experiment D on c61 (`e-tool04-80-p7456-*`) and c66 (`e66-*`) |
| `E16/X08/` | variants of the overloaded replays on c60 (`x08-*`: bypass bounds; `x08c-conv-*`: conversation trace) and c61 (`x08b-*`: one-flag variants, ordering baselines), each node with its own stock run |
| `E16/T06/` | the intermediate load (tool-agent trace at 0.06x) on c73 |
| `E16/ccb/` | mixed workloads under memory pressure with the 30 s bypass bound and the bypass alone, on c74 |
| `E16/correct/` | output-correctness check of the KV paths (`*-correct.md`) |
| `E16/c1test`, `E16/c2`, `E16/poltest`, `E16/*/v1`, `E16/*/aborted`, `E16/*/failed-*` | runs with prototype v1, aborted or failed runs: kept for the record, not used in the report unless it says so |
| `E16/jobs/` | the Slurm job scripts of the 16 GB nodes and the helper that chains them |
| `figs/` | the report's figures (PNG and PDF) and `table-fig3-fig6.md` |
| `experiment-matrix.{csv,md}` | one row per run: node, start, configuration, workload, requests, errors, completion (`matrix_adm.py`) |

Per run `<tag>`: `<tag>-meta.txt` (configuration and marks with the monotonic / wall clock pair), `<tag>-node.txt` (16 GB nodes: host,
GPU, driver), `<tag>-driver.txt` (driver output), `<tag>-client.jsonl` (one record per request as the client saw it, with a hash of
the generated text), `<tag>-requests.csv` (per-request timeline joined from the hooks), `<tag>-adm-requests.csv` (per-request admission
phases and waiting time by reason), `<tag>-adm-kv.csv` (GPU KV occupancy per engine step, decimated to 0.25 s), `<tag>-replay.json`
/ `<tag>-scenarios.csv` (run and scenario summaries).

Not in git (on c28 under `/mnt/local/ghu4/results/2026-11-10-gpu-kv-admission`): the admission streams `<tag>-vllmevt.adm.<pid>.jsonl` (every poll, admission attempt, preemption
and one line per engine step), the request and step streams `<tag>-vllmevt.{req,step}.*.jsonl`, `<tag>-steps.csv`,
`<tag>-kvevents.jsonl` (LMCache event mirror), `<tag>-gpu.txt` / `<tag>-cpu.txt` (samplers), `<tag>-server.log`,
`<tag>-lmcache.log`, `<tag>-status.txt`.
