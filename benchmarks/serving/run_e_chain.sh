#!/bin/bash
# Experiment E chain (2026-11-04): concurrent retrieval with 1 and 4 server transfer threads. usage: run_e_chain.sh <out_dir> [reps=4]
set -u
OUT=$1; REPS=${2:-4}; PY=/mnt/local/ghu4/envs/lmcache/bin/python; RUN=/home/ghu4/CXL/benchmarks/serving/run_e.py
mkdir -p "$OUT"; cd "$OUT" || exit 1
log() { echo "[$(date -Is)] $*" >> chain.txt; }
run() { local tag=$1; shift; log "start $tag $*"; timeout 3600 taskset -c 80-87 $PY $RUN . "$tag" reps=$REPS "$@" > "$tag-driver.txt" 2>&1; log "end $tag rc=$?"; sleep 5; }
# two more B configurations first (supported knobs that change when loaded requests get into a step): smaller prefill chunks and synchronous scheduling
RB=/home/ghu4/CXL/benchmarks/serving/run_b.py; BD=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap/B
( cd $BD && for v in "b-chunk512 max_batched=512" "b-noasync async_sched=off"; do set -- $v; echo "[$(date -Is)] start $1 $2" >> chain.txt; timeout 5400 taskset -c 80-87 $PY $RB . $1 reps=5 tier=dram $2 > $1-driver.txt 2>&1; echo "[$(date -Is)] end $1 rc=$?" >> chain.txt; sleep 5; done )
run e-workers1 tier=dram gpu_workers=1
run e-workers4 tier=dram gpu_workers=4
run e-ssd      tier=ssd l1_gb=10 gpu_workers=1 scenarios=e1
run e-workers1-nosamp tier=dram gpu_workers=1 samplers=false scenarios=e1
log "chain done"
