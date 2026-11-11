#!/bin/bash
# compute-contention scenario (plan c1) on c23, pool pinned to 7,456 blocks: stock scheduler, existing flags, prototype flags
R=/mnt/beegfs/ghu4/kvadm/results/c1test; S=/home/ghu4/CXL/benchmarks/serving
run() { tag=$1; shift; $S/remote16.sh $R run_adm.py $tag plan=c1 reps=3 hbase=6000 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done" >> $R/chain.txt; sleep 5; }
run c1-base
run c1-sync async_sched=off
run c1-lpt1024 long_prefill_threshold=1024
run c1-tok "adm_env=KVADM_POLICY=tokres=768"
run c1-tokfast "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run c1-tokfast-sync async_sched=off "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run c1-tokfast-eager eager_prefetch=true "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
echo "[$(date -Is)] c1test done" >> $R/chain.txt
