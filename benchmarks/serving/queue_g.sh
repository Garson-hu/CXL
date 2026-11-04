#!/bin/bash
# After queue_f.sh ("F done"): clean rerun of the SSD O_DIRECT single-request experiment (the first rerun found its prompts already on disk from the page-cache run).
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
until grep -q "F done" $R/queue.txt 2>/dev/null; do sleep 60; done
cd $R/A && log "G: clean ssd odirect rerun"; timeout 3600 taskset -c 80-87 $PY $S/run_a.py . a-3b-ssd-odirect2 tier=ssd l1_gb=10 ssd_odirect=true enforce_eager=false Ls=256,512,1024,2048,4096,8192,16384 reps=8 > a-3b-ssd-odirect2-driver.txt 2>&1; log "a-3b-ssd-odirect2 rc=$?"; log "G done"
