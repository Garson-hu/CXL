#!/bin/bash
# Intermediate load (tool-agent, seconds 0-150 at 0.06x) on c73, same set-up and stock run as job_t06.sh: the bypass alone with the 30 s bound.
R=/mnt/beegfs/ghu4/kvadm/results/T06; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
$S/remote16.sh $R replay.py t06-skip30 $T 0 150 0.06 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 "adm_env=KVADM_POLICY=skip=30,hitres=600"; echo "[$(date -Is)] t06-skip30 done on $(hostname)" >> $R/chain.txt
$S/remote16.sh $R replay.py t06-priolen $T 0 150 0.06 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 prio=len; echo "[$(date -Is)] t06-priolen done on $(hostname)" >> $R/chain.txt
echo "[$(date -Is)] t06b done" >> $R/chain.txt
