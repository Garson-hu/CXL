#!/bin/bash
# Experiment B chain (2026-11-04): the controlled scenarios of run_b.py under the supported scheduler / connector
# configurations, same request sequences in every run. usage: run_b_chain.sh <out_dir> [reps=5]
set -u
OUT=$1; REPS=${2:-5}; PY=/mnt/local/ghu4/envs/lmcache/bin/python; RUN=/home/ghu4/CXL/benchmarks/serving/run_b.py
mkdir -p "$OUT"; cd "$OUT" || exit 1
log() { echo "[$(date -Is)] $*" >> chain.txt; }
run() { local tag=$1; shift; log "start $tag $*"; timeout 5400 taskset -c 80-87 $PY $RUN . "$tag" reps=$REPS "$@" > "$tag-driver.txt" 2>&1; log "end $tag rc=$?"; sleep 5; }
# two more single-request control variants first (which hook makes host hits fast: the LMCache event-bus mirror or the vLLM hook?)
RA=/home/ghu4/CXL/benchmarks/serving/run_a.py; A=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap/A
( cd $A && timeout 3600 taskset -c 80-87 $PY $RA . a-3b-dram-lmhookonly tier=dram hooks_vllm=false samplers=false enforce_eager=false Ls=256,1024,4096,16384 reps=4 > a-3b-dram-lmhookonly-driver.txt 2>&1; echo "[$(date -Is)] a-3b-dram-lmhookonly rc=$?" >> $OUT/chain.txt
  timeout 3600 taskset -c 80-87 $PY $RA . a-3b-dram-vllmhookonly tier=dram hooks_lm=false samplers=false enforce_eager=false Ls=256,1024,4096,16384 reps=4 > a-3b-dram-vllmhookonly-driver.txt 2>&1; echo "[$(date -Is)] a-3b-dram-vllmhookonly rc=$?" >> $OUT/chain.txt
  timeout 3600 taskset -c 80-87 $PY /home/ghu4/CXL/benchmarks/serving/run_a_idle.py . a-3b-idle tier=dram > a-3b-idle-driver.txt 2>&1; echo "[$(date -Is)] a-3b-idle rc=$?" >> $OUT/chain.txt )
run b-default   tier=dram
run b-eager     tier=dram eager_prefetch=true
run b-workers4  tier=dram gpu_workers=4
run b-prio-hits tier=dram prio=hits_first
run b-prio-cold tier=dram prio=cold_first
run b-none      tier=none
run b-default-nosamp tier=dram samplers=false scenarios=s2,s3
log "chain done"
