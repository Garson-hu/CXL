#!/bin/bash
# Mixed workloads under GPU KV memory pressure on c74, same set-up and stock runs as job_cc74.sh: the bypass alone with the 30 s bound.
R=/mnt/beegfs/ghu4/kvadm/results/ccb; S=/home/ghu4/CXL/benchmarks/serving
for P in 3728 2560; do
  $S/remote16.sh $R run_b.py ccb-p$P-skip30 scenarios=s1,s2,s3 reps=3 adm=true l1_gb=60 gpu_blocks=$P "adm_env=KVADM_POLICY=skip=30,hitres=600"; echo "[$(date -Is)] ccb-p$P-skip30 done on $(hostname)" >> $R/chain.txt; sleep 5
done
echo "[$(date -Is)] cc74b done" >> $R/chain.txt
