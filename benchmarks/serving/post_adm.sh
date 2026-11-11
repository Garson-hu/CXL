#!/bin/bash
# Per-run analysis of an instrumented trace replay of the 2026-11-10 admission study: the replay summary (analyze_replay.py: <tag>-replay.json,
# <tag>-requests.csv, replay-summary.csv), the admission analysis (analyze_adm.py: <tag>-adm-requests.csv, <tag>-adm-kv.csv, tables-adm-<tag>.md)
# and the first-attempt table (adm_first_attempts.py). usage: post_adm.sh <results dir> <tag> [<tag> ...]
S=$(dirname "$(readlink -f "$0")"); PY=${PY:-/mnt/local/ghu4/envs/agent/bin/python}; R=$1; shift
for tag in "$@"; do
  $PY $S/analyze_replay.py "$R" "$tag" | cut -c1-400
  $PY $S/analyze_adm.py "$R" "$tag" > /dev/null || echo "analyze_adm failed for $tag"
  $PY $S/adm_first_attempts.py "$R" "$tag" > /dev/null || echo "adm_first_attempts failed for $tag"
done
