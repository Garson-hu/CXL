#!/usr/bin/env bash
# Collect the raw data of the 2026-11-10 GPU-KV admission study.
#
# During the study the repo directory experimental_results/<study> was a symlink to c28's local NVMe (/home has a 40 GB quota), and the
# runs on the 16 GB RTX 4060 Ti nodes wrote to the shared scratch file system. This script
#   1. copies the 16 GB-node results (everything) from /mnt/beegfs/ghu4/kvadm/results to <c28 results>/E16/, so that all raw logs of the
#      study are in one place on c28's NVMe;
#   2. replaces the repo symlink by a real directory with the small artifacts the report's tables and figures are built from:
#        kept:  *-meta.txt *-node.txt *-driver.txt *-client.jsonl *-requests.csv *-scenarios.csv *-replay.json *-adm-requests.csv
#               *-adm-kv.csv *-correct.md tables*.md replay-summary.csv plan.txt chain.txt done.txt experiment-matrix.* figs/* README* SUMMARY.md
#        left on c28 (/mnt/local/ghu4/results/<study>, not in git): *-vllmevt.*.jsonl (request / step / ADMISSION streams) *-steps.csv
#               *-kvevents.jsonl *-gpu.txt *-cpu.txt *-server.log *-lmcache.log *-status.txt slurm-*.out
# Run only when no queue script and no Slurm job of the study is running. Idempotent.
set -euo pipefail
STUDY=2026-11-10-gpu-kv-admission
SRC=/mnt/local/ghu4/results/$STUDY
E16=/mnt/beegfs/ghu4/kvadm/results
DST=/home/ghu4/CXL/experimental_results/$STUDY
[ -d "$SRC" ] || { echo "source $SRC missing" >&2; exit 1; }
if pgrep -f "benchmarks/serving/queue_adm.sh" >/dev/null; then echo "the replay queue is still running; refusing" >&2; exit 1; fi
if squeue -h -u "$USER" -o "%j" 2>/dev/null | grep -q "^kvadm-"; then echo "kvadm jobs are still queued or running; refusing" >&2; exit 1; fi
[ -d "$E16" ] && rsync -a "$E16/" "$SRC/E16/"
# the job scripts of the 16 GB nodes (how every run there was started) next to their results
mkdir -p "$SRC/E16/jobs" && cp -p /mnt/beegfs/ghu4/kvadm/job_*.sh /mnt/beegfs/ghu4/kvadm/submit_after.sh "$SRC/E16/jobs/" 2>/dev/null || true
if [ -L "$DST" ]; then rm "${DST:?}"; fi
mkdir -p "$DST"
rsync -a --prune-empty-dirs \
  --exclude='*-vllmevt.*' --exclude='*-steps.csv' --exclude='*-kvevents.jsonl' --exclude='*-gpu.txt' --exclude='*-cpu.txt' \
  --exclude='*-server.log' --exclude='*-lmcache.log' --exclude='*-status.txt' --exclude='slurm-*.out' --exclude='*.err' --exclude='*.bak-*' \
  "$SRC/" "$DST/"
cat > "$DST/README.md" <<EOF
# Raw data of docs/experiments/$STUDY.md

Start with \`SUMMARY.md\` in this directory: the self-contained summary of the study (question, platform, every run, results,
answers to the brief's questions, negative results, limitations, data map, how to regenerate).

Collected on $(date +%F) with \`benchmarks/serving/collect_adm.sh\` from \`$SRC\` (c28, local NVMe) — which also holds a full copy of
the runs made on the 16 GB RTX 4060 Ti nodes (\`E16/\`, copied from \`$E16\`).

| directory | content |
|---|---|
| \`replay/\` | trace replays on c28 (Experiment D and the instrumented baselines of Experiment A): \`plan.txt\` (the queue), \`chain.txt\` / \`done.txt\` (start and end of every run), per-run files, \`tables-adm-<tag>.md\` (admission analysis), \`tables-first-<tag>.md\` (first admission attempts by occupancy), \`tables-d-*.md\` (configuration comparisons), \`tables-store-loss.md\`, \`replay-summary.csv\` |
| \`A3/\` | controlled reproduction on c28 (\`tables-a3-a3.md\`) |
| \`smoke/\` | smoke runs of the instrumentation |
| \`E16/a3gate/\` | the A3 trials with the full-sequence gate on and off (node c60) |
| \`E16/c1c/\`, \`E16/c2b/\`, \`E16/c5/\` | controlled scenarios of Experiment B: compute contention (c1), reservation gate (c2) and head-of-line blocking (c3), bounded reservation (c5) |
| \`E16/cc/\` | mixed workloads of Experiment C (pools 2,560 / 3,728 / 7,456 / 14,912 blocks; \`s4-*\` = hit-share sweep) |
| \`E16/E/\` | Experiment E (replays on the larger pool and with the 7B model) and the 80 GB capacity point of Experiment D on c61 (\`e-tool04-80-p7456-*\`) and c66 (\`e66-*\`) |
| \`E16/X08/\` | variants of the overloaded replays on c60 (\`x08-*\`: bypass bounds; \`x08c-conv-*\`: conversation trace) and c61 (\`x08b-*\`: one-flag variants, ordering baselines), each node with its own stock run |
| \`E16/T06/\` | the intermediate load (tool-agent trace at 0.06x) on c73 |
| \`E16/ccb/\` | mixed workloads under memory pressure with the 30 s bypass bound and the bypass alone, on c74 |
| \`E16/correct/\` | output-correctness check of the KV paths (\`*-correct.md\`) |
| \`E16/c1test\`, \`E16/c2\`, \`E16/poltest\`, \`E16/*/v1\`, \`E16/*/aborted\`, \`E16/*/failed-*\` | runs with prototype v1, aborted or failed runs: kept for the record, not used in the report unless it says so |
| \`E16/jobs/\` | the Slurm job scripts of the 16 GB nodes and the helper that chains them |
| \`figs/\` | the report's figures (PNG and PDF) and \`table-fig3-fig6.md\` |
| \`experiment-matrix.{csv,md}\` | one row per run: node, start, configuration, workload, requests, errors, completion (\`matrix_adm.py\`) |

Per run \`<tag>\`: \`<tag>-meta.txt\` (configuration and marks with the monotonic / wall clock pair), \`<tag>-node.txt\` (16 GB nodes: host,
GPU, driver), \`<tag>-driver.txt\` (driver output), \`<tag>-client.jsonl\` (one record per request as the client saw it, with a hash of
the generated text), \`<tag>-requests.csv\` (per-request timeline joined from the hooks), \`<tag>-adm-requests.csv\` (per-request admission
phases and waiting time by reason), \`<tag>-adm-kv.csv\` (GPU KV occupancy per engine step, decimated to 0.25 s), \`<tag>-replay.json\`
/ \`<tag>-scenarios.csv\` (run and scenario summaries).

Not in git (on c28 under \`$SRC\`): the admission streams \`<tag>-vllmevt.adm.<pid>.jsonl\` (every poll, admission attempt, preemption
and one line per engine step), the request and step streams \`<tag>-vllmevt.{req,step}.*.jsonl\`, \`<tag>-steps.csv\`,
\`<tag>-kvevents.jsonl\` (LMCache event mirror), \`<tag>-gpu.txt\` / \`<tag>-cpu.txt\` (samplers), \`<tag>-server.log\`,
\`<tag>-lmcache.log\`, \`<tag>-status.txt\`.
EOF
du -sh "$DST" "$SRC"
