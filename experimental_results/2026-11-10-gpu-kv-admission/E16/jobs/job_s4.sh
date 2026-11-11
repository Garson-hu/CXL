#!/bin/bash
# Experiment C, hit-share sweep (run_b.py scenario s4: open loop at 2 req/s, 48 requests, share of external hits 0 / 0.25 / 0.5 / 0.75 / 1,
# short (1k-2k) and long (8k) prompts), stock against prototype v1.2 (commit 9f3b1c8), pools 7,456 and 3,728 blocks; node c66
R=/mnt/beegfs/ghu4/kvadm/results/cc; S=/home/ghu4/CXL/benchmarks/serving
runb() { tag=$1; shift; $S/remote16.sh $R run_b.py $tag scenarios=s4 adm=true l1_gb=60 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
TF="adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall"
for pool in 7456 3728; do
  runb s4-p$pool-base gpu_blocks=$pool
  runb s4-p$pool-tokfast12 gpu_blocks=$pool "$TF"
done
echo "[$(date -Is)] s4 done" >> $R/chain.txt
