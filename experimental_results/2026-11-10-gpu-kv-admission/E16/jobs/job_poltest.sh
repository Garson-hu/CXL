#!/bin/bash
# policy smoke tests on c23 (same GPU model as c28, pool pinned to c28's 7,456 blocks): baseline and four flag sets, parts 3 and 5 of the a3 plan
R=/mnt/beegfs/ghu4/kvadm/results/poltest; S=/home/ghu4/CXL/benchmarks/serving
run() { tag=$1; shift; $S/remote16.sh $R run_adm.py $tag plan=a3 parts=3,5 reps=2 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done" >> $R/chain.txt; sleep 5; }
run e-pol0
run e-pol1 "adm_env=KVADM_POLICY=tokres=768"
run e-pol2 "adm_env=KVADM_POLICY=tokres=768,skip=3,hitres=600"
run e-pol3 "adm_env=KVADM_POLICY=alpha=0"
run e-pol4 "adm_env=KVADM_POLICY=skip=1,fallback=1"
echo "[$(date -Is)] poltest done" >> $R/chain.txt
