#!/bin/bash
# Run queue of the CXL-vs-NVMe serving study (2026-11-12). Runs every line of the plan file once, in order, one at a time (c28 has one
# GPU), and re-reads the plan after each run, so lines can be appended while it is running. Finished tags are recorded in
# <results>/done.txt and never repeated; a line can be removed or edited until its run starts.
# plan line:  <tag> <subdir> <driver> [key=value ...]          (# starts a comment)
#   driver:  a | c | e                    run_a.py / run_c.py / run_e.py  (single-request retrieval / equal-hit / concurrent retrieval)
#            conv:<t1>:<speed> | tool:<t1>:<speed>   replay.py of the Mooncake conversation / tool-agent trace, seconds 0..t1 at <speed>x
# After a run its analysis is started in the background (analyze_tier.py for a / c / e, analyze_tier_replay.py for replays).
# usage: queue_tier.sh <results_dir> <plan_file> [wait_for_file wait_for_pattern]
set -u
R=$1; PLAN=$2; PY=/mnt/local/ghu4/envs/lmcache/bin/python; S=/home/ghu4/CXL/benchmarks/serving; W=/home/ghu4/CXL/workloads
if [ $# -ge 4 ]; then until grep -q "$4" "$3" 2>/dev/null; do sleep 20; done; fi
cd "$S" || exit 1
while :; do
  next=""
  while read -r tag sub drv rest; do
    [ -z "${tag:-}" ] && continue
    case "$tag" in \#*) continue;; esac
    grep -q "^end $tag " "$R/done.txt" 2>/dev/null && continue
    next="$tag $sub $drv $rest"; break
  done < "$PLAN"
  [ -z "$next" ] && break
  set -- $next; tag=$1; sub=$2; drv=$3; shift 3; O=$R/$sub; mkdir -p "$O"
  if pgrep -f "lmcache serve[r]|vllm serv[e]" > /dev/null; then echo "[$(date -Is)] $tag: a server is still running, waiting" >> "$R/chain.txt"; sleep 30; pkill -INT -f "lmcache serve[r]|vllm serv[e]"; sleep 30; fi
  echo "[$(date -Is)] start $tag ($sub, $drv) $*" >> "$R/chain.txt"
  case "$drv" in
    a) timeout 3600 taskset -c 80-87 $PY run_a.py "$O" "$tag" "$@" > "$O/$tag-driver.txt" 2>&1; rc=$?; post="analyze_tier.py";;
    c) timeout 3600 taskset -c 80-87 $PY run_c.py "$O" "$tag" "$@" > "$O/$tag-driver.txt" 2>&1; rc=$?; post="analyze_tier.py";;
    e) timeout 3600 taskset -c 80-87 $PY run_e.py "$O" "$tag" "$@" > "$O/$tag-driver.txt" 2>&1; rc=$?; post="analyze_tier.py";;
    conv:*|tool:*)
      IFS=: read -r tr t1 speed <<< "$drv"
      [ "$tr" = conv ] && T=$W/mooncake_conversation_trace.jsonl || T=$W/mooncake_toolagent_trace.jsonl
      timeout 21600 taskset -c 80-87 $PY replay.py "$O" "$tag" "$T" 0 "$t1" "$speed" max_out=1024 dequant_s=1 "$@" > "$O/$tag-driver.txt" 2>&1; rc=$?; post="analyze_tier_replay.py";;
    *) echo "unknown driver $drv" >> "$R/chain.txt"; rc=99; post="";;
  esac
  echo "[$(date -Is)] end $tag rc=$rc" >> "$R/chain.txt"; echo "end $tag rc=$rc $(date -Is)" >> "$R/done.txt"
  [ -n "$post" ] && [ "$rc" = 0 ] && (nohup nice taskset -c 64-79 $PY $post "$O" "$tag" > "$O/$tag-analysis.txt" 2>&1 &)
  sleep 5
done
echo "[$(date -Is)] queue empty" >> "$R/chain.txt"
