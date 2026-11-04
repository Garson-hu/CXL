#!/bin/bash
# Experiment A chain (2026-11-04): single-request KV retrieval cost, one server configuration after the other.
# usage: run_a_chain.sh <out_dir> <eager:true|false> [reps=8]
# Each run: run_a.py with the tier / model given; the driver output goes to <out>/<tag>-driver.txt and the chain's
# progress to <out>/chain.txt. Tags: a-<model>-<tier>[-nohooks].
set -u
OUT=$1; EAGER=$2; REPS=${3:-8}; PY=/mnt/local/ghu4/envs/lmcache/bin/python; RUN=/home/ghu4/CXL/benchmarks/serving/run_a.py
mkdir -p "$OUT"; cd "$OUT" || exit 1
LS=256,512,1024,2048,4096,8192,16384
log() { echo "[$(date -Is)] $*" >> chain.txt; }
run() { local tag=$1; shift; log "start $tag $*"; timeout 3600 taskset -c 80-87 $PY $RUN . "$tag" enforce_eager=$EAGER "$@" > "$tag-driver.txt" 2>&1; log "end $tag rc=$?"; sleep 5; }
# 3B-AWQ: DRAM tier, SSD tier, vLLM alone, and the no-instrumentation control
run a-3b-dram    tier=dram Ls=$LS reps=$REPS
run a-3b-ssd     tier=ssd  l1_gb=10 Ls=$LS reps=$REPS
run a-3b-none    tier=none Ls=$LS reps=$REPS
run a-3b-dram-nohooks tier=dram Ls=$LS reps=4 hooks=false samplers=false
# 1.5B fp16 (the model of the trace replays of 2026-10-10/11): DRAM tier
run a-15b-dram   tier=dram model=Qwen/Qwen2.5-1.5B-Instruct Ls=$LS reps=$REPS
log "chain done"
