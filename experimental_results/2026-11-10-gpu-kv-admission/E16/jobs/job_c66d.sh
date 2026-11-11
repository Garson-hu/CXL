#!/bin/bash
# Node c66, prototype module v1.4 (commit 49c3585)
S=/home/ghu4/CXL/benchmarks/serving
# (1) output-correctness check of the KV paths (run_correct.py), pool pinned at 7,456 blocks
R=/mnt/beegfs/ghu4/kvadm/results/correct
runc() { tag=$1; shift; $S/remote16.sh $R run_correct.py $tag n=48 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
runc correct-base
runc correct-p1 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
runc correct-p1-sync async_sched=off "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
runc correct-p2 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst,skip=3,hitres=600"
runc correct-base2
# (2) Experiment E, overload on the larger pool (3B-AWQ, about 19,900 blocks): tool-agent 0-100 s at 0.08x, 120 GB host tier (never filled in this window)
R=/mnt/beegfs/ghu4/kvadm/results/E; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
run() { tag=$1; t1=$2; speed=$3; shift 3; $S/remote16.sh $R replay.py $tag $T 0 $t1 $speed max_out=1024 dequant_s=1 tier=dram l1_gb=120 adm=true "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run e-tool08-120-big-base 100 0.08
run e-tool08-120-big-p1 100 0.08 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
echo "[$(date -Is)] c66d done" >> $R/chain.txt
