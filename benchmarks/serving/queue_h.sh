#!/bin/bash
# After queue_g.sh ("G done"): the combination priority hits-first + prefill chunk 512 (the two knobs that each remove one of the waits).
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
until grep -q "G done" $R/queue.txt 2>/dev/null; do sleep 60; done
cd $R/B && log "H: b-prio-hits-chunk512"; timeout 5400 taskset -c 80-87 $PY $S/run_b.py . b-prio-hits-chunk512 reps=5 tier=dram prio=hits_first max_batched=512 > b-prio-hits-chunk512-driver.txt 2>&1; log "b-prio-hits-chunk512 rc=$?"; log "H done"
