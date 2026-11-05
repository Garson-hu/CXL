#!/bin/bash
# Replaces queue_i.sh (2026-11-05 00:50, never started): the lighter-load capacity sweep now replays trace seconds 0-200 at 0.04x
# (5,000 wall s per run) because the offline reuse analysis (trace_reuse.py) shows the 0-50 s / 0-100 s windows hold almost no
# capacity-sensitive reuse (conversation: 4.5% at 2 GB vs 8.5% at 80 GB in 100 s; 4.5% vs 11.6% in 200 s). Configurations: 2 GB
# (GPU-cache-scale), 80 GB, 320 GB (CXL-scale capacity, DRAM standing in for the blocked DAX) and vLLM alone, both traces.
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
W=/home/ghu4/CXL/workloads; CONV=$W/mooncake_conversation_trace.jsonl; TOOL=$W/mooncake_toolagent_trace.jsonl
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
until grep -qE "\] all done 3$" $R/queue.txt 2>/dev/null; do sleep 60; done
cd $R/replay
# 2026-11-05 01:27: first re-run d-tool-dram2 (0.08x), contaminated by the premature start of this script (see replay/flawed/README-dl-conv-dram2.txt)
mkdir -p flawed; for f in d-tool-dram2-*; do [ -e "$f" ] && mv "$f" "flawed/${f/d-tool-dram2-/d-tool-dram2-contaminated-}"; done
log "I2: d-tool-dram2 rerun"; echo "[$(date -Is)] start d-tool-dram2 tier=dram l1_gb=2 (rerun)" >> chain.txt
timeout 5400 taskset -c 80-87 $PY $S/replay.py . d-tool-dram2 "$TOOL" 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=2 > d-tool-dram2-driver.txt 2>&1; echo "[$(date -Is)] end d-tool-dram2 rc=$? (rerun)" >> chain.txt; sleep 5
for tr in conv tool; do
  [ $tr = conv ] && T=$CONV || T=$TOOL
  for cfg in "dram2 tier=dram l1_gb=2" "dram80 tier=dram l1_gb=80" "dram320 tier=dram l1_gb=320" "none tier=none"; do
    set -- $cfg; tag=dl-$tr-$1; shift; log "I2: $tag"; echo "[$(date -Is)] start $tag $* (0-200 s at 0.04x)" >> chain.txt
    timeout 7200 taskset -c 80-87 $PY $S/replay.py . $tag "$T" 0 200 0.04 max_out=1024 dequant_s=1 "$@" > $tag-driver.txt 2>&1; echo "[$(date -Is)] end $tag rc=$?" >> chain.txt; sleep 5
  done
done
log "I2 done"
