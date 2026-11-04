#!/bin/bash
# Trace-replay chain (2026-11-04): Experiment D (host-cache capacity: DRAM L1 sizes, SSD-backed, vLLM alone) and the
# real-trace part of Experiment B (default vs eager prefetch vs 4 transfer threads), Mooncake conversation and
# tool-agent windows 0-100 trace-s at 0.08x (= 1,250 wall s each), output capped at 1024 tokens, 3B-AWQ.
# usage: run_replay_chain.sh <out_dir> <D|B|all> [t1=100] [speed=0.08]
set -u
OUT=$1; WHICH=$2; T1=${3:-100}; SPEED=${4:-0.08}; PY=/mnt/local/ghu4/envs/lmcache/bin/python; RUN=/home/ghu4/CXL/benchmarks/serving/replay.py
W=/home/ghu4/CXL/workloads; CONV=$W/mooncake_conversation_trace.jsonl; TOOL=$W/mooncake_toolagent_trace.jsonl
mkdir -p "$OUT"; cd "$OUT" || exit 1
log() { echo "[$(date -Is)] $*" >> chain.txt; }
run() { local tag=$1 trace=$2; shift 2; log "start $tag $*"; timeout 5400 taskset -c 80-87 $PY $RUN . "$tag" "$trace" 0 "$T1" "$SPEED" max_out=1024 dequant_s=1 "$@" > "$tag-driver.txt" 2>&1; log "end $tag rc=$?"; sleep 5; }
if [ "$WHICH" = D ] || [ "$WHICH" = all ]; then
  for tr in conv tool; do
    [ $tr = conv ] && T=$CONV || T=$TOOL
    for gb in 2 5 10 20 40 80; do run d-$tr-dram$gb "$T" tier=dram l1_gb=$gb; done
    run d-$tr-ssd "$T" tier=ssd l1_gb=10
    run d-$tr-none "$T" tier=none
  done
fi
if [ "$WHICH" = B ] || [ "$WHICH" = all ]; then
  for tr in conv tool; do
    [ $tr = conv ] && T=$CONV || T=$TOOL
    run br-$tr-eager "$T" tier=dram l1_gb=40 eager_prefetch=true
    run br-$tr-workers4 "$T" tier=dram l1_gb=40 gpu_workers=4
  done
fi
log "chain done ($WHICH)"
