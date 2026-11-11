#!/bin/bash
# c66, prototype module v1.1 (commit 1b5fa31): (1) the compute-contention scenario c1, (2) the memory-pressure scenarios c2 / c3,
# (3) mixed workloads at pools of 2,048 and 14,912 blocks
S=/home/ghu4/CXL/benchmarks/serving
R=/mnt/beegfs/ghu4/kvadm/results/c1c
run1() { tag=$1; shift; $S/remote16.sh $R run_adm.py $tag plan=c1 reps=3 hbase=6000 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run1 c1c-base
run1 c1c-tokfast512 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run1 c1c-tokfast256 "adm_env=KVADM_POLICY=tokres=768,fastchunk=256"
run1 c1c-tokfast512-sync async_sched=off "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run1 c1c-tok "adm_env=KVADM_POLICY=tokres=768"
run1 c1c-sync async_sched=off
run1 c1c-lpt1024 long_prefill_threshold=1024
run1 c1c-chunk512 max_batched=512
echo "[$(date -Is)] c1c done" >> $R/chain.txt
R=/mnt/beegfs/ghu4/kvadm/results/c2b
run2() { tag=$1; plan=$2; shift 2; $S/remote16.sh $R run_adm.py $tag plan=$plan reps=3 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run2 c3b-base c3
run2 c3b-skip2 c3 "adm_env=KVADM_POLICY=skip=2"
run2 c3b-tokfast-skip3-hitres c3 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,skip=3,hitres=600"
run2 c2b-base c2
run2 c2b-tokfast c2 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run2 c2b-tokfast-a0 c2 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,alpha=0"
run2 c2b-tokfast-a0-out512 c2 probe_out=512 tmax=60 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,alpha=0"
run2 c2b-tokfast-out512 c2 probe_out=512 tmax=60 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run2 c2b-tokfast-fb c2 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,skip=1,fallback=1"
echo "[$(date -Is)] c2b done" >> $R/chain.txt
R=/mnt/beegfs/ghu4/kvadm/results/cc
runb() { tag=$1; shift; $S/remote16.sh $R run_b.py $tag scenarios=s1,s2,s3 reps=3 adm=true l1_gb=60 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
TF="adm_env=KVADM_POLICY=tokres=768,fastchunk=512"; TFS="adm_env=KVADM_POLICY=tokres=768,fastchunk=512,skip=3,hitres=600"
for pool in 2048 14912; do
  fill=8; [ $pool = 14912 ] && fill=16
  runb cc-p$pool-base gpu_blocks=$pool fill=$fill
  runb cc-p$pool-tokfast gpu_blocks=$pool fill=$fill "$TF"
  runb cc-p$pool-tokfast-skip gpu_blocks=$pool fill=$fill "$TFS"
done
echo "[$(date -Is)] c66b done" >> $R/chain.txt
