#!/bin/bash
# Experiment C, mixed workloads under GPU KV memory pressure with the bypass bound raised to 30 s (P4), on the 16 GB node c74 (2026-11-11 03:05):
# run_b.py s1 closed loop 1-16, s2 open loop 0.5-4 req/s, s3 bursts; 50 % external hits / 50 % misses of 1k-8k; pools 3,728 and 2,560 blocks;
# stock, P2 and P4 of each pool on this node (the earlier runs of these pools are on c60 and c66). Policy module v1.4 (commit 49c3585 + c68ce39).
R=/mnt/beegfs/ghu4/kvadm/results/ccb; S=/home/ghu4/CXL/benchmarks/serving
B="tokres=768,fastchunk=512,resvall,blkfirst"
runb() { tag=$1; shift; $S/remote16.sh $R run_b.py $tag scenarios=s1,s2,s3 reps=3 adm=true l1_gb=60 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
for P in 3728 2560; do
  runb ccb-p$P-base gpu_blocks=$P
  runb ccb-p$P-p2 gpu_blocks=$P "adm_env=KVADM_POLICY=$B,skip=3,hitres=600"
  runb ccb-p$P-p4 gpu_blocks=$P "adm_env=KVADM_POLICY=$B,skip=30,hitres=600"
done
echo "[$(date -Is)] cc74 done" >> $R/chain.txt
