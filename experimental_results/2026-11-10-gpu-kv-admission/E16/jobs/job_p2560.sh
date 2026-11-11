#!/bin/bash
# Experiment C, mixed workloads under severe GPU KV memory pressure: pool 2,560 blocks (40,960 tokens; a pool of 2,048 blocks equals
# max_model_len and vLLM does not start with it), stock / prototype v1.1 flags as in the other pools / with the head-of-line bypass; node c66
R=/mnt/beegfs/ghu4/kvadm/results/cc; S=/home/ghu4/CXL/benchmarks/serving
runb() { tag=$1; shift; $S/remote16.sh $R run_b.py $tag scenarios=s1,s2,s3 reps=3 adm=true l1_gb=60 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
TF="adm_env=KVADM_POLICY=tokres=768,fastchunk=512"; TFS="adm_env=KVADM_POLICY=tokres=768,fastchunk=512,skip=3,hitres=600"
runb cc-p2560-base gpu_blocks=2560
runb cc-p2560-tokfast gpu_blocks=2560 "$TF"
runb cc-p2560-tokfast-skip gpu_blocks=2560 "$TFS"
echo "[$(date -Is)] p2560 done" >> $R/chain.txt
