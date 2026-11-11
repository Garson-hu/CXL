#!/bin/bash
# Sustainable load, 80 GB host tier, node c66 (stock run e66-tool04-80-p7456-base, shortest-prompt-first e66-tool04-80-p7456-priolen; job_e66.sh, job_e66b.sh):
# shortest-prompt-first priority WITH the token mechanisms (P1) on top - do the prototype's token rules add anything to the best existing ordering option?
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
$S/remote16.sh $R replay.py e66-tool04-80-p7456-priolen-p1 $T 0 200 0.04 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 prio=len "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,resvall,blkfirst"; echo "[$(date -Is)] e66-tool04-80-p7456-priolen-p1 done on $(hostname)" >> $R/chain.txt
echo "[$(date -Is)] e66c done" >> $R/chain.txt
