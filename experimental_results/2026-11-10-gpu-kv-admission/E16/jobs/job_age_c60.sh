#!/bin/bash
# Overloaded tool-agent replay on c60 (stock run x08-base on this node; pool pinned to 7,456 blocks, 150 GB host tier): shortest-prompt-first WITH AGING,
# an ordering a client or gateway can compute for vLLM's priority scheduling: priority = send time in ms + 3 x number of prompt tokens. A request can
# be overtaken only by shorter requests sent within 3 ms per token of difference after it (about 90 s for the largest prompts): does a bounded
# shortest-first keep the mean of shortest-prompt-first without its four-minute waits?
R=/mnt/beegfs/ghu4/kvadm/results/X08; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
$S/remote16.sh $R replay.py x08-priolenage3 $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=150 adm=true gpu_blocks=7456 prio=lenage:3; echo "[$(date -Is)] x08-priolenage3 done on $(hostname)" >> $R/chain.txt
echo "[$(date -Is)] age-c60 done" >> $R/chain.txt
