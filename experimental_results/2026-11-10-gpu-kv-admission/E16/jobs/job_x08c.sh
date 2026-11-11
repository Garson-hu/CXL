#!/bin/bash
# Conversation trace under overload (seconds 0-100 at 0.08x) on the 16 GB node c60 with the pool pinned to c28's 7,456 blocks and a 150 GB host
# tier (the replay stores at most 114 GB: no eviction, as with c28's 320 GB tier). Own stock baseline, P2, and P3 (P2 + starvation bound of 20 s).
# Policy module v1.4 (commit 49c3585 + c68ce39). Replaces the run conv08-320-p3 of c28's plan (2026-11-11 02:45).
R=/mnt/beegfs/ghu4/kvadm/results/X08; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_conversation_trace.jsonl
B="tokres=768,fastchunk=512,resvall,blkfirst"
run() { tag=$1; shift; $S/remote16.sh $R replay.py $tag $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=150 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run x08c-conv-base
run x08c-conv-p2 "adm_env=KVADM_POLICY=$B,skip=3,hitres=600"
run x08c-conv-p3 "adm_env=KVADM_POLICY=$B,skip=3,hitres=600,agecap=20"
echo "[$(date -Is)] x08c done" >> $R/chain.txt
