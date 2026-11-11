#!/bin/bash
# One more ordering baseline of the overloaded tool-agent replay on c61 (stock run x08b-base, shortest-prompt-first x08b-priolen; same set-up as job_x08b.sh):
# vLLM priority scheduling with ORACLE shortest-compute-first priorities: the priority of a request is the number of prompt tokens the stock run had to
# compute for it (prompt minus cached tokens). The cache-aware counterpart of shortest-prompt-first: what does knowing the cache add to ordering?
R=/mnt/beegfs/ghu4/kvadm/results/X08; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
$S/remote16.sh $R replay.py x08b-priouncached $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=150 adm=true gpu_blocks=7456 prio_from=$R/x08b-base-client.jsonl prio=uncached; echo "[$(date -Is)] x08b-priouncached done on $(hostname)" >> $R/chain.txt
# then (added 2026-11-11 05:32) shortest-prompt-first at the sustainable load on this node too (80 GB host tier; stock, P1, oracle priority and P4 of this
# configuration ran here; on c66 shortest-prompt-first lowered the mean TTFT by 28 % with the misses 8 % faster)
E=/mnt/beegfs/ghu4/kvadm/results/E
$S/remote16.sh $E replay.py e-tool04-80-p7456-priolen $T 0 200 0.04 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 prio=len; echo "[$(date -Is)] e-tool04-80-p7456-priolen done on $(hostname)" >> $E/chain.txt
echo "[$(date -Is)] x08g done" >> $R/chain.txt
