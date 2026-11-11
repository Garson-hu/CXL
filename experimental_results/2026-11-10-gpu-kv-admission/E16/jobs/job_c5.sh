#!/bin/bash
# Experiment B, bounded reservation for external hits that are passed over (run_adm.py plan=c5), prototype v1.2 (commit 9f3b1c8 + plan c5), node c66:
# stock; skip without reservation; skip with reservation budgets of 300 / 600 / 1,200 blocks; the same with the token reserve
R=/mnt/beegfs/ghu4/kvadm/results/c5; S=/home/ghu4/CXL/benchmarks/serving
run() { tag=$1; shift; $S/remote16.sh $R run_adm.py $tag plan=c5 reps=3 tmax=45 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run c5-base
run c5-skip3 "adm_env=KVADM_POLICY=skip=3"
run c5-skip3-res300 "adm_env=KVADM_POLICY=skip=3,hitres=300"
run c5-skip3-res600 "adm_env=KVADM_POLICY=skip=3,hitres=600"
run c5-skip3-res1200 "adm_env=KVADM_POLICY=skip=3,hitres=1200"
run c5-skip8 "adm_env=KVADM_POLICY=skip=8"
run c5-tokfast-skip3-res600 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,skip=3,hitres=600"
echo "[$(date -Is)] c5 done" >> $R/chain.txt
