#!/bin/bash
# Experiment E on a 16 GB RTX 4060 Ti node, prototype v1.2 (commit 9f3b1c8):
#  (1) same model as c28 (3B-AWQ), GPU KV pool the node allows (about 19,900 blocks), tool-agent 0-200 s at 0.04x, 80 GB host tier: prototype with and without synchronous scheduling
#  (2) larger model (Qwen2.5-7B-Instruct-AWQ, 56 KiB of KV per token, pool about 125k tokens = c28's token capacity), tool-agent 0-100 s at 0.02x: stock and prototype
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
P="adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall"
run() { tag=$1; t1=$2; speed=$3; shift 3; $S/remote16.sh $R replay.py $tag $T 0 $t1 $speed max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run e-tool04-80-big-tokfast12 200 0.04 "$P"
run e-tool04-80-big-tokfast12-sync 200 0.04 async_sched=off "$P"
run e7-tool02-80-base 100 0.02 model=Qwen/Qwen2.5-7B-Instruct-AWQ
run e7-tool02-80-tokfast12 100 0.02 model=Qwen/Qwen2.5-7B-Instruct-AWQ "$P"
echo "[$(date -Is)] e2 done" >> $R/chain.txt
