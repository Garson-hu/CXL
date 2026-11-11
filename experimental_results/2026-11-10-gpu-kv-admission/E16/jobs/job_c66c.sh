#!/bin/bash
# Node c66, prototype module v1.4 (commit 49c3585); P1 = tokres=768,fastchunk=512,resvall,blkfirst ; P2 = tokres=768,fastchunk=512,resvall,blkfirst,skip=3,hitres=600
S=/home/ghu4/CXL/benchmarks/serving
# (1) Experiment C, hit-share sweep (run_b.py s4: open loop at 2 req/s, 48 requests, share of external hits 0 / 0.25 / 0.5 / 0.75 / 1, short (1k-2k) and long (8k) prompts)
R=/mnt/beegfs/ghu4/kvadm/results/cc
runb() { tag=$1; shift; $S/remote16.sh $R run_b.py $tag adm=true l1_gb=60 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
for pool in 7456 3728; do
  runb s4-p$pool-base scenarios=s4 gpu_blocks=$pool
  runb s4-p$pool-p1 scenarios=s4 gpu_blocks=$pool "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
  runb s4-p$pool-p2 scenarios=s4 gpu_blocks=$pool "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst,skip=3,hitres=600"
done
# (2) Experiment B, bounded reservation for passed hits (run_adm.py plan=c5)
R=/mnt/beegfs/ghu4/kvadm/results/c5
run5() { tag=$1; shift; $S/remote16.sh $R run_adm.py $tag plan=c5 reps=3 tmax=45 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run5 c5-base
run5 c5-skip3 "adm_env=KVADM_POLICY=skip=3"
run5 c5-skip3-res300 "adm_env=KVADM_POLICY=skip=3,hitres=300"
run5 c5-skip3-res600 "adm_env=KVADM_POLICY=skip=3,hitres=600"
run5 c5-skip3-res1200 "adm_env=KVADM_POLICY=skip=3,hitres=1200"
run5 c5-skip8 "adm_env=KVADM_POLICY=skip=8"
run5 c5-p2 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst,skip=3,hitres=600"
# (3) Experiment C, mixed workloads (s1-s3) under severe memory pressure: pool 2,560 blocks (2,048 = max_model_len: vLLM does not start), and P1 / P2 at 14,912
R=/mnt/beegfs/ghu4/kvadm/results/cc
runb cc-p2560-base scenarios=s1,s2,s3 reps=3 gpu_blocks=2560
runb cc-p2560-p1 scenarios=s1,s2,s3 reps=3 gpu_blocks=2560 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
runb cc-p2560-p2 scenarios=s1,s2,s3 reps=3 gpu_blocks=2560 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst,skip=3,hitres=600"
runb cc-p14912-p1 scenarios=s1,s2,s3 reps=3 gpu_blocks=14912 fill=16 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
runb cc-p14912-p2 scenarios=s1,s2,s3 reps=3 gpu_blocks=14912 fill=16 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst,skip=3,hitres=600"
echo "[$(date -Is)] c66c done" >> $R/chain.txt
