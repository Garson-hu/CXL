#!/bin/bash
# Replay queue of the 2026-11-10 admission study. Runs every line of the plan file once, in order, and re-reads the file after
# each run, so lines can be appended while it is running. Finished tags are recorded in <out>/done.txt and never repeated.
# plan line:  <tag> <conv|tool> <t1 trace-seconds> <speed> [replay.py key=value ...]      (# starts a comment)
# usage: queue_adm.sh <results_dir>/replay <plan_file>
set -u
OUT=$1; PLAN=$2; PY=/mnt/local/ghu4/envs/lmcache/bin/python; S=/home/ghu4/CXL/benchmarks/serving; W=/home/ghu4/CXL/workloads
cd "$OUT" || exit 1
while :; do
  next=""
  while read -r tag tr t1 speed rest; do
    [ -z "${tag:-}" ] && continue
    case "$tag" in \#*) continue;; esac
    grep -q "^end $tag " done.txt 2>/dev/null && continue
    next="$tag $tr $t1 $speed $rest"; break
  done < "$PLAN"
  [ -z "$next" ] && break
  set -- $next; tag=$1; tr=$2; t1=$3; speed=$4; shift 4
  [ "$tr" = conv ] && T=$W/mooncake_conversation_trace.jsonl || T=$W/mooncake_toolagent_trace.jsonl
  echo "[$(date -Is)] start $tag $tr 0-$t1 s at ${speed}x $*" >> chain.txt
  timeout 7200 taskset -c 80-87 $PY $S/replay.py . "$tag" "$T" 0 "$t1" "$speed" max_out=1024 dequant_s=1 "$@" > "$tag-driver.txt" 2>&1; rc=$?
  echo "[$(date -Is)] end $tag rc=$rc" >> chain.txt; echo "end $tag rc=$rc $(date -Is)" >> done.txt; sleep 5
done
echo "[$(date -Is)] queue empty" >> chain.txt
