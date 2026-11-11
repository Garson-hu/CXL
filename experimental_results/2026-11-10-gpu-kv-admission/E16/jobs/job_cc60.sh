#!/bin/bash
# Experiment C, mixed workloads (run_b.py s1 closed loop 1-16, s2 open loop 0.5-4 req/s, s3 bursts; 50 % external hits / 50 % misses of 1k-8k),
# prototype module v1.1 (commit 1b5fa31). This node: pools 7,456 (variants; the baseline cc-p7456-base ran here at 18:53-19:07) and 3,728 blocks.
R=/mnt/beegfs/ghu4/kvadm/results/cc; S=/home/ghu4/CXL/benchmarks/serving
runb() { tag=$1; shift; $S/remote16.sh $R run_b.py $tag scenarios=s1,s2,s3 reps=3 adm=true l1_gb=60 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
TF="adm_env=KVADM_POLICY=tokres=768,fastchunk=512"; TFS="adm_env=KVADM_POLICY=tokres=768,fastchunk=512,skip=3,hitres=600"
runb cc-p7456-tokfast gpu_blocks=7456 "$TF"
runb cc-p7456-tokfast-skip gpu_blocks=7456 "$TFS"
runb cc-p3728-base gpu_blocks=3728
runb cc-p3728-tokfast gpu_blocks=3728 "$TF"
runb cc-p3728-tokfast-skip gpu_blocks=3728 "$TFS"
runb cc-p7456-sync gpu_blocks=7456 async_sched=off
runb cc-p7456-priohits gpu_blocks=7456 prio=hits_first
runb cc-p7456-lpt1024 gpu_blocks=7456 long_prefill_threshold=1024
echo "[$(date -Is)] cc60 done" >> $R/chain.txt
