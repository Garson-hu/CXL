#!/usr/bin/env bash
# Collect the small raw artifacts of the 2026-11-04 serving study into the repo (experimental_results/<study>/).
#
# During the study the repo directory was a symlink to /mnt/local/ghu4/results/<study> (c28-local NVMe; /home has a
# 40 GB quota). This script replaces the symlink by a real directory holding every per-run and per-family artifact that
# the report's tables and figures are built from, and leaves the bulky logs on /mnt/local (listed in README.md):
#   kept:   *-meta.txt *-driver.txt *-client.jsonl *-requests.csv *-scenarios.csv *-replay.json *-timeline.csv
#           *-summary.md, tables*.md, replay-summary.csv trace-reuse.csv c-*.csv params-3b.json run_c.log chain.txt
#           queue*.txt experiment-matrix.* inspect/* figs/*.png figs/*.pdf
#   left:   *-steps.csv *-kvevents.jsonl *-gpu.txt *-cpu.txt *-vllmevt.*.jsonl *-server.log *-lmcache.log *-status.txt
#           (≈ 950 MB) and the figure test directories (figs-test/)
# Run ONLY after every queue script has finished (they write through the symlink). Idempotent.
set -euo pipefail
STUDY=2026-11-04-cxl-serving-scheduling-gap
SRC=/mnt/local/ghu4/results/$STUDY
DST=/home/ghu4/CXL/experimental_results/$STUDY
[ -d "$SRC" ] || { echo "source $SRC missing" >&2; exit 1; }
if pgrep -f "benchmarks/serving/queue" >/dev/null; then echo "a queue script is still running; refusing" >&2; exit 1; fi
if [ -L "$DST" ]; then rm "$DST"; fi
mkdir -p "$DST"
rsync -a --prune-empty-dirs \
  --exclude='*-steps.csv' --exclude='*-kvevents.jsonl' --exclude='*-gpu.txt' --exclude='*-cpu.txt' \
  --exclude='*-vllmevt.*' --exclude='*-server.log' --exclude='*-lmcache.log' --exclude='*-status.txt' \
  --exclude='figs-test/' --exclude='*.err' \
  "$SRC/" "$DST/"
cat > "$DST/README.md" <<EOF
# Raw data of docs/experiments/$STUDY.md

Collected from \`$SRC\` on $(date +%F) with \`benchmarks/serving/collect_small.sh\`. One directory per experiment
family (\`A\`, \`B\`, \`C\`, \`E\`, \`F\`, \`replay\` = Experiment D and the lighter-load sweep, \`smoke\`, \`inspect\`);
\`*/flawed/\` holds the quarantined runs listed in the report's §15.C. Per run \`<tag>\`: \`<tag>-meta.txt\`
(configuration and the monotonic/wall clock pair), \`<tag>-driver.txt\` (driver output), \`<tag>-client.jsonl\` (one
record per request as the client saw it), \`<tag>-requests.csv\` (per-request timeline joined from the hooks),
\`<tag>-scenarios.csv\` / \`<tag>-replay.json\` (per-group summaries). Tables (\`tables*.md\`) and figures (\`figs/\`)
are what the report embeds; \`experiment-matrix.{csv,md}\` is the §15.B matrix (\`matrix.py\`).

The bulky per-run logs stay on c28's local NVMe at \`$SRC\` (not in git; ≈ 950 MB): \`<tag>-steps.csv\` (engine step
log), \`<tag>-kvevents.jsonl\` (LMCache event mirror), \`<tag>-gpu.txt\` / \`<tag>-cpu.txt\` (samplers),
\`<tag>-vllmevt.*.jsonl\` (vLLM request/step events), \`<tag>-server.log\`, \`<tag>-lmcache.log\`, \`<tag>-status.txt\`.
EOF
du -sh "$DST"
