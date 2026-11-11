#!/bin/bash
# Sustainable load, 80 GB host tier, node c61 (stock run e-tool04-80-p7456-base, shortest-prompt-first e-tool04-80-p7456-priolen, P1, P4 on this node):
# a second measurement of shortest-prompt-first priority WITH the token mechanisms (P1) on top (first one: e66-tool04-80-p7456-priolen-p1 on c66, -41 %).
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
$S/remote16.sh $R replay.py e-tool04-80-p7456-priolen-p1 $T 0 200 0.04 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 prio=len "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"; echo "[$(date -Is)] e-tool04-80-p7456-priolen-p1 done on $(hostname)" >> $R/chain.txt
echo "[$(date -Is)] e61c done" >> $R/chain.txt
