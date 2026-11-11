#!/bin/bash
# Experiment E on the 16 GB RTX 4060 Ti node c61 (the stock baselines e-tool04-80-big-base and e-tool04-80-p7456-base ran on this node), prototype
# module v1.4 (commit 49c3585), configuration P1 (token reserve + short steps, resvall, blkfirst), 3B-AWQ, tool-agent 0-200 s at 0.04x, 80 GB host tier:
#  (1) pool pinned to c28's 7,456 blocks (the 80 GB capacity-sensitivity pair of Experiment D, on this node)
#  (2) the pool the node allows (19,916 blocks = 2.67x c28's): P1 with asynchronous and with synchronous scheduling
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
P="adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"
run() { tag=$1; t1=$2; speed=$3; shift 3; $S/remote16.sh $R replay.py $tag $T 0 $t1 $speed max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run e-tool04-80-p7456-p1 200 0.04 gpu_blocks=7456 "$P"
run e-tool04-80-big-p1 200 0.04 "$P"
run e-tool04-80-big-p1-sync 200 0.04 async_sched=off "$P"
echo "[$(date -Is)] e3 done" >> $R/chain.txt
