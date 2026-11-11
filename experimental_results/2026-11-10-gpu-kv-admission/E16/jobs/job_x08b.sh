#!/bin/bash
# Variants of the overloaded tool-agent replay on the 16 GB node c61 (same set-up as job_x08a.sh): its own stock baseline, the bypass alone (stock
# token rules), the v1.2 ablation (resvall without blkfirst), the starvation bound without the bypass, and P2 with synchronous scheduling.
R=/mnt/beegfs/ghu4/kvadm/results/X08; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
B="tokres=768,fastchunk=512,resvall,blkfirst"
run() { tag=$1; shift; $S/remote16.sh $R replay.py $tag $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=150 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run x08b-base
run x08b-skip "adm_env=KVADM_POLICY=skip=3,hitres=600"
run x08b-tokfast12 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall"
run x08b-p1-a20 "adm_env=KVADM_POLICY=$B,agecap=20"
run x08b-p2-sync async_sched=off "adm_env=KVADM_POLICY=$B,skip=3,hitres=600"
echo "[$(date -Is)] x08b done" >> $R/chain.txt
