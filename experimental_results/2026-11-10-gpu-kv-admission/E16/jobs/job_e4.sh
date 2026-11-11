#!/bin/bash
# Experiment D, capacity-sensitivity pair on the 16 GB node c61 (pool pinned to c28's 7,456 blocks, 80 GB host tier, tool-agent 0-200 s at 0.04x):
# prototype configuration P2 (module v1.4, commit 49c3585 + logging c68ce39); the stock run and P1 of this configuration ran on the same node
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
run() { tag=$1; t1=$2; speed=$3; shift 3; $S/remote16.sh $R replay.py $tag $T 0 $t1 $speed max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run e-tool04-80-p7456-p2 200 0.04 gpu_blocks=7456 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst,skip=3,hitres=600"
echo "[$(date -Is)] e4 done" >> $R/chain.txt
