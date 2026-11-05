#!/bin/bash
# After queue part 3's H: a lighter-load capacity mini-sweep (0.04x, trace seconds 0-50) where even the smallest cache keeps up, to separate capacity from overload.
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
W=/home/ghu4/CXL/workloads; CONV=$W/mooncake_conversation_trace.jsonl; TOOL=$W/mooncake_toolagent_trace.jsonl
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
until grep -q "all done 3" $R/queue.txt 2>/dev/null; do sleep 60; done
cd $R/replay
for tr in conv tool; do
  [ $tr = conv ] && T=$CONV || T=$TOOL
  for cfg in "dram2 tier=dram l1_gb=2" "dram20 tier=dram l1_gb=20" "dram80 tier=dram l1_gb=80" "none tier=none"; do
    set -- $cfg; tag=dl-$tr-$1; shift; log "I: $tag"; echo "[$(date -Is)] start $tag $*" >> chain.txt
    timeout 3600 taskset -c 80-87 $PY $S/replay.py . $tag "$T" 0 50 0.04 max_out=1024 dequant_s=1 "$@" > $tag-driver.txt 2>&1; echo "[$(date -Is)] end $tag rc=$?" >> chain.txt; sleep 5
  done
done
log "I done"
