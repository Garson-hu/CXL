#!/bin/bash
# controlled reproduction A3 with the full-sequence admission gate on (stock default) and off (--no-scheduler-reserve-full-isl), same node, pool pinned to 7,456 blocks
R=/mnt/beegfs/ghu4/kvadm/results/a3gate; S=/home/ghu4/CXL/benchmarks/serving
run() { tag=$1; shift; $S/remote16.sh $R run_adm.py $tag plan=a3 gpu_blocks=7456 l1_gb=100 "$@"; echo "[$(date -Is)] $tag done" >> $R/chain.txt; sleep 5; }
run a3g-base
run a3g-noisl extra_vllm=--no-scheduler-reserve-full-isl
echo "[$(date -Is)] a3gate done" >> $R/chain.txt
