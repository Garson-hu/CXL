#!/bin/bash
# Variants of the overloaded tool-agent replay (seconds 0-100 at 0.08x) on a 16 GB node with the pool pinned to c28's 7,456 blocks and a 150 GB
# host tier (the replay stores at most 109 GB: no eviction, as with c28's 320 GB tier). Node c60, policy module v1.4 (commit 49c3585 + c68ce39).
# Its own stock baseline first; then P2 and the bypass bounds of 10 s and 30 s (P2 has 3 s).
R=/mnt/beegfs/ghu4/kvadm/results/X08; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
B="tokres=768,fastchunk=512,resvall,blkfirst"
run() { tag=$1; shift; $S/remote16.sh $R replay.py $tag $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=150 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run x08-base
run x08-p2 "adm_env=KVADM_POLICY=$B,skip=3,hitres=600"
run x08-p2-skip10 "adm_env=KVADM_POLICY=$B,skip=10,hitres=600"
run x08-p2-skip30 "adm_env=KVADM_POLICY=$B,skip=30,hitres=600"
echo "[$(date -Is)] x08a done" >> $R/chain.txt
