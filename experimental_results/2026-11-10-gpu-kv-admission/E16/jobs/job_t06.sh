#!/bin/bash
# Experiment D, an intermediate load between the sustainable one (0.04x) and overload (0.08x), on the 16 GB node c73 (2026-11-11 03:05):
# tool-agent trace, seconds 0-150 at 0.06x (2,500 wall s), GPU KV pool pinned to c28's 7,456 blocks, 80 GB host tier (the node has 125 GiB of RAM),
# policy module v1.4 (commit 49c3585 + c68ce39). Own stock run first; P2 (bypass bound 3 s); P4 (bypass bound 30 s); vLLM priority scheduling with
# oracle hits-first priorities taken from this node's stock run.
R=/mnt/beegfs/ghu4/kvadm/results/T06; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
B="tokres=768,fastchunk=512,resvall,blkfirst"
run() { tag=$1; shift; $S/remote16.sh $R replay.py $tag $T 0 150 0.06 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
run t06-base
run t06-p4 "adm_env=KVADM_POLICY=$B,skip=30,hitres=600"
run t06-p2 "adm_env=KVADM_POLICY=$B,skip=3,hitres=600"
run t06-priohits prio_from=$R/t06-base-client.jsonl
echo "[$(date -Is)] t06 done" >> $R/chain.txt
