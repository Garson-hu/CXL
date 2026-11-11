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
if [ -L "$DST" ]; then rm "${DST:?}"; fi
mkdir -p "$DST"
rsync -a --prune-empty-dirs \
  --exclude='*-vllmevt.*' --exclude='*-steps.csv' --exclude='*-kvevents.jsonl' --exclude='*-gpu.txt' --exclude='*-cpu.txt' \
  --exclude='*-server.log' --exclude='*-lmcache.log' --exclude='*-status.txt' --exclude='slurm-*.out' --exclude='*.err' --exclude='*.bak-*' \
  "$SRC/" "$DST/"
du -sh "$DST" "$SRC"
