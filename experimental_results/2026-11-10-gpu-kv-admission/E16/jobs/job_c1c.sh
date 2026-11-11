#!/bin/bash
# compute-contention scenario (plan c1) with prototype module v1 (commit of 2026-11-10 18:45), same node as the c1b baseline where possible
R=/mnt/beegfs/ghu4/kvadm/results/c1c; S=/home/ghu4/CXL/benchmarks/serving
run() { tag=$1; shift; $S/remote16.sh $R run_adm.py $tag plan=c1 reps=3 hbase=6000 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run c1c-base
run c1c-tokfast512 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run c1c-tokfast256 "adm_env=KVADM_POLICY=tokres=768,fastchunk=256"
run c1c-tokfast512-sync async_sched=off "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run c1c-tok "adm_env=KVADM_POLICY=tokres=768"
run c1c-sync async_sched=off
run c1c-lpt1024 long_prefill_threshold=1024
run c1c-lpt512 long_prefill_threshold=512
run c1c-chunk512 max_batched=512
echo "[$(date -Is)] c1c done" >> $R/chain.txt
