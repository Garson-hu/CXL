#!/bin/bash
# Experiment E, larger model on a 16 GB RTX 4060 Ti node (c60): Qwen2.5-7B-Instruct-AWQ (56 KiB of KV per token; pool about 125k tokens = c28's
# token capacity with the 3B model), tool-agent replay 0-100 s at 0.02x, 80 GB host tier: stock and prototype P1 (module v1.4, commit 49c3585);
# then the mixed workloads (run_b.py s1-s3) with P1 and P2 at the pools measured on this node with the v1.1 flags (7,456 and 3,728 blocks)
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
run() { tag=$1; t1=$2; speed=$3; shift 3; $S/remote16.sh $R replay.py $tag $T 0 $t1 $speed max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run e7-tool02-80-base 100 0.02 model=Qwen/Qwen2.5-7B-Instruct-AWQ
run e7-tool02-80-p1 100 0.02 model=Qwen/Qwen2.5-7B-Instruct-AWQ "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
echo "[$(date -Is)] e7 done" >> $R/chain.txt
R=/mnt/beegfs/ghu4/kvadm/results/cc
runb() { tag=$1; shift; $S/remote16.sh $R run_b.py $tag scenarios=s1,s2,s3 reps=3 adm=true l1_gb=60 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
for pool in 7456 3728; do
  runb cc-p$pool-p1 gpu_blocks=$pool "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
  runb cc-p$pool-p2 gpu_blocks=$pool "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst,skip=3,hitres=600"
done
echo "[$(date -Is)] cc60-p done" >> $R/chain.txt
