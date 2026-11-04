#!/bin/bash
# Follow-up queue (2026-11-04): after queue_all.sh ("all done"), Experiment F's controlled sensitivity scenario s4 under the default and the vLLM-alone configuration.
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
until grep -q "all done" $R/queue.txt 2>/dev/null; do sleep 60; done
mkdir -p $R/F && cd $R/F
log "F: s4 default"; timeout 5400 taskset -c 80-87 $PY $S/run_b.py . f-default tier=dram scenarios=s4 > f-default-driver.txt 2>&1; log "f-default rc=$?"
log "F: s4 none"; timeout 5400 taskset -c 80-87 $PY $S/run_b.py . f-none tier=none scenarios=s4 > f-none-driver.txt 2>&1; log "f-none rc=$?"
log "F done"
