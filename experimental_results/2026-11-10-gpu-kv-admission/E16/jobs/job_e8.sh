#!/bin/bash
# Experiment E, overload on the larger pool (16 GB RTX 4060 Ti node c66; 3B-AWQ; pool = what the node allows, about 19,900 blocks):
# tool-agent replay 0-100 s at 0.08x, 80 GB host tier (never filled in this window), stock and prototype v1.2 (commit 9f3b1c8)
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
P="adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall"
run() { tag=$1; t1=$2; speed=$3; shift 3; $S/remote16.sh $R replay.py $tag $T 0 $t1 $speed max_out=1024 dequant_s=1 tier=dram l1_gb=120 adm=true "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run e-tool08-120-big-base 100 0.08
run e-tool08-120-big-tokfast12 100 0.08 "$P"
echo "[$(date -Is)] e8 done" >> $R/chain.txt
