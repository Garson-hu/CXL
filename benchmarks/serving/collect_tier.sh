#!/usr/bin/env bash
# Collect the raw data of the 2026-11-12 CXL-vs-NVMe serving study.
#
# During the study the repo directory experimental_results/<study> is a symlink to c28's local NVMe (/home has a 40 GB quota). This
# script replaces the symlink by a real directory with the small artifacts the report's tables and figures are built from:
#   kept:  *-meta.txt *-driver.txt *-client.jsonl *-tier-timeline.csv *-tier-summary.md *-requests.csv *-scenarios.csv *-replay.json
#          *-tier.json *-tier-requests.csv *-traffic.csv *-residency.txt *-analysis.txt tables-*.md *-summary.csv tier-summary.csv
#          replay-summary.csv plan.txt done.txt chain.txt queue_*.log env/* trace-model/* figs/* README.md SUMMARY.md
#   left on c28 (/mnt/local/ghu4/results/<study>, not in git): *-kvevents.jsonl (LMCache event mirror with the per-chunk media copies)
#          *-vllmevt.*.jsonl *-steps.csv *-gpu.txt *-cpu.txt *-server.log *-lmcache.log *-status.txt *-pids.json
# Run only when the run queue is empty. Idempotent.
set -euo pipefail
STUDY=2026-11-12-cxl-vs-nvme-serving
SRC=/mnt/local/ghu4/results/$STUDY
DST=/home/ghu4/CXL/experimental_results/$STUDY
[ -d "$SRC" ] || { echo "source $SRC missing" >&2; exit 1; }
if pgrep -f "benchmarks/serving/queue_tier" >/dev/null || pgrep -f "queue_tier.sh" >/dev/null; then echo "the run queue is still running; refusing" >&2; exit 1; fi
if [ -L "$DST" ]; then rm "${DST:?}"; fi
mkdir -p "$DST"
rsync -a --prune-empty-dirs \
  --exclude='*-kvevents.jsonl' --exclude='*-vllmevt.*' --exclude='*-steps.csv' --exclude='*-gpu.txt' --exclude='*-cpu.txt' \
  --exclude='*-server.log' --exclude='*-lmcache.log' --exclude='*-status.txt' --exclude='*-pids.json' --exclude='*.bak-*' --exclude='figtmp/' \
  "$SRC/" "$DST/"
du -sh "$DST"; find "$DST" -type f | wc -l
