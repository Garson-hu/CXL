#!/bin/bash
# Output-correctness check of the KV paths (run_correct.py), node c66, pool pinned at 7,456 blocks: stock, prototype v1.2 (token reserve + short
# steps + resvall), the same with synchronous scheduling, and with the head-of-line bypass
R=/mnt/beegfs/ghu4/kvadm/results/correct; S=/home/ghu4/CXL/benchmarks/serving
run() { tag=$1; shift; $S/remote16.sh $R run_correct.py $tag n=48 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run correct-base
run correct-tokfast12 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall"
run correct-tokfast12-sync async_sched=off "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall"
run correct-tokfast12-skip "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,skip=3,hitres=600"
run correct-base2
echo "[$(date -Is)] correct done" >> $R/chain.txt
