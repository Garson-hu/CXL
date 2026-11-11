#!/bin/bash
# Capacity-sensitivity point of Experiment D on the 16 GB node c61 (pool pinned to c28's 7,456 blocks, 80 GB host tier, tool-agent 0-200 s at 0.04x):
# vLLM priority scheduling with oracle hits-first priorities (a request that was a hit in this node's stock run e-tool04-80-p7456-base is sent with
# priority 0), then P4 = P2 with the bypass bound raised from 3 s to 30 s (module v1.4, commit 49c3585 + logging c68ce39). The stock run and P1 of
# this configuration ran on the same node (job_e3.sh). Replaces job_e4.sh: job 334506 (P2) was killed one second after its start on 2026-11-11
# 01:24:16 (it started in the second in which the previous job on the node ended; exit 0:9, empty output, nothing written). Revised 2026-11-11
# 03:00: P2 gave way to P4 after x08-p2-skip30 (P2 at the sustainable load exists on c28 with the 320 GB tier, where its bypass is active 0.6 %
# of the time).
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
run() { tag=$1; shift; $S/remote16.sh $R replay.py $tag $T 0 200 0.04 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
# first (2026-11-11 03:05), one more variant of the overloaded tool-agent replay on this node (stock run x08b-base, job_x08b.sh): shortest-prompt-first
# with vLLM's priority scheduling (priority = number of prompt tokens), an ordering baseline that a client can realize without knowing the cache
X=/mnt/beegfs/ghu4/kvadm/results/X08
$S/remote16.sh $X replay.py x08b-priolen $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=150 adm=true gpu_blocks=7456 prio=len; echo "[$(date -Is)] x08b-priolen done on $(hostname)" >> $X/chain.txt; sleep 5
run e-tool04-80-p7456-priohits prio_from=$R/e-tool04-80-p7456-base-client.jsonl
run e-tool04-80-p7456-p4 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst,skip=30,hitres=600"
echo "[$(date -Is)] e4b done" >> $R/chain.txt
