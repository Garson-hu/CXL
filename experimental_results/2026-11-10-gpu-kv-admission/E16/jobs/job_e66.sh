#!/bin/bash
# Capacity-sensitivity point of Experiment D, decomposition family on the 16 GB node c66 (2026-11-11 02:45): tool-agent trace, seconds 0-200 at
# 0.04x, GPU KV pool pinned to c28's 7,456 blocks, 80 GB host tier, policy module v1.4 (commit 49c3585 + logging c68ce39).
# Own stock baseline on this node first; then the bypass alone (stock token rules) and P3 (P2 + starvation bound of 20 s).
# The stock / P1 / P2 / oracle-priority runs of the same configuration are on c61 (job_e3.sh, job_e4b.sh).
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
B="tokres=768,fastchunk=512,resvall,blkfirst"
run() { tag=$1; shift; $S/remote16.sh $R replay.py $tag $T 0 200 0.04 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run e66-tool04-80-p7456-base
run e66-tool04-80-p7456-skip "adm_env=KVADM_POLICY=skip=3,hitres=600"
run e66-tool04-80-p7456-p3 "adm_env=KVADM_POLICY=$B,skip=3,hitres=600,agecap=20"
echo "[$(date -Is)] e66 done" >> $R/chain.txt
