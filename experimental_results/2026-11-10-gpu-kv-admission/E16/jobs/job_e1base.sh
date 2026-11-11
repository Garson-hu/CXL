#!/bin/bash
# Experiment E, baselines on a 16 GB RTX 4060 Ti node (same GPU model as c28, twice the memory): tool-agent replay 0-200 s at 0.04x, 80 GB host tier,
# stock scheduler, (1) with the GPU KV pool the node allows (about 2.6x c28's) and (2) with the pool pinned to c28's 7,456 blocks
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
run() { tag=$1; shift; $S/remote16.sh $R replay.py $tag $T 0 200 0.04 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run e-tool04-80-big-base
run e-tool04-80-p7456-base gpu_blocks=7456
echo "[$(date -Is)] e1base done" >> $R/chain.txt
