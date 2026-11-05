#!/bin/bash
# 2026-11-05 05:40: Experiment F re-run of the DRAM-tier s4 scenario with a 160 GB L1. In f-default (40 GB, watermark 0.8) the
# LRU started evicting 202 s into the run (during s4-long-h0): the run stores ~78 GB of KV (LMCache stores every prompt's KV,
# cold ones included), so the 8k pool entries stored at the start were evicted before the long-prompt points and only 1 / 14 /
# 15 / 17 of the 8 / 23 / 30 / 48 intended pool requests hit the host tier there. 160 GB holds the whole run. Runs after queue_i2.
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
until grep -qE "\] I2 done$" $R/queue.txt 2>/dev/null; do sleep 60; done
cd $R/F
log "F2: s4 default l1=160"; timeout 5400 taskset -c 80-87 $PY $S/run_b.py . f-default-l1-160 tier=dram l1_gb=160 scenarios=s4 > f-default-l1-160-driver.txt 2>&1; log "f-default-l1-160 rc=$?"
log "F2 done"
