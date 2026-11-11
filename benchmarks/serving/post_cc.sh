#!/bin/bash
# Per-run analysis of a controlled run (run_b.py / run_adm.py) of the 2026-11-10 admission study: per-request records (analyze_b.py:
# <tag>-requests.csv, <tag>-scenarios.csv) and the admission analysis over the measured request types (analyze_adm.py case=host,cold).
# usage: post_cc.sh <results dir> <tag> [<tag> ...]
S=$(dirname "$(readlink -f "$0")"); PY=${PY:-/mnt/local/ghu4/envs/agent/bin/python}; R=$1; shift
for tag in "$@"; do
  $PY $S/analyze_b.py "$R" "$tag" > "$R/$tag-summary.md" 2>/dev/null || echo "analyze_b failed for $tag"
  $PY $S/analyze_adm.py "$R" "$tag" case=host,cold > /dev/null 2>&1 || echo "analyze_adm failed for $tag"
done
