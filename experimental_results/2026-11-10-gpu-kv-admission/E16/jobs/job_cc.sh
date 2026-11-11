#!/bin/bash
# Experiment C, mixed workloads (run_b.py: closed loop 1-16, open loop 0.5-4 req/s, bursts 4-16; 50 % external hits / 50 % misses of 1k-8k) at four
# GPU KV pool sizes, stock scheduler vs prototypes, one node. First a load test of the 7B model (pool size of Experiment E2).
R=/mnt/beegfs/ghu4/kvadm/results/cc; S=/home/ghu4/CXL/benchmarks/serving
$S/remote16.sh $R run_adm.py e7-smoke plan=smoke l1_gb=40 model=Qwen/Qwen2.5-7B-Instruct-AWQ; echo "[$(date -Is)] e7-smoke done on $(hostname)" >> $R/chain.txt
runb() { tag=$1; shift; $S/remote16.sh $R run_b.py $tag scenarios=s1,s2,s3 reps=3 adm=true l1_gb=60 "$@"; echo "[$(date -Is)] $tag done" >> $R/chain.txt; sleep 5; }
TF="adm_env=KVADM_POLICY=tokres=768,fastchunk=512"; TFS="adm_env=KVADM_POLICY=tokres=768,fastchunk=512,skip=3,hitres=600"
for pool in 7456 3728 2048 14912; do
  fill=8; [ $pool = 14912 ] && fill=16
  runb cc-p$pool-base gpu_blocks=$pool fill=$fill
  runb cc-p$pool-tokfast gpu_blocks=$pool fill=$fill "$TF"
  runb cc-p$pool-tokfast-skip gpu_blocks=$pool fill=$fill "$TFS"
done
runb cc-p7456-sync gpu_blocks=7456 async_sched=off
runb cc-p7456-priohits gpu_blocks=7456 prio=hits_first
runb cc-p7456-lpt1024 gpu_blocks=7456 long_prefill_threshold=1024
echo "[$(date -Is)] cc done" >> $R/chain.txt
