#!/bin/bash
# Follow-up on c60 (same set-up and stock runs as job_x08a.sh / job_x08d.sh; pool pinned to 7,456 blocks, 150 GB host tier; module v1.4):
# the bypass alone (stock token rules) on the conversation trace under overload with the 30 s bound, then on the overloaded tool-agent replay
# with bounds of 10 s, 100 s and 3 s, so that the bound is varied with and without the token rules on one node.
R=/mnt/beegfs/ghu4/kvadm/results/X08; S=/home/ghu4/CXL/benchmarks/serving; W=/home/ghu4/CXL/workloads
run() { tag=$1; T=$2; shift 2; $S/remote16.sh $R replay.py $tag $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=150 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
TT=$W/mooncake_toolagent_trace.jsonl; TC=$W/mooncake_conversation_trace.jsonl
run x08c-conv-skip30 $TC "adm_env=KVADM_POLICY=skip=30,hitres=600"
run x08c-conv-priolen $TC prio=len
run x08-skip10 $TT "adm_env=KVADM_POLICY=skip=10,hitres=600"
run x08-skip100 $TT "adm_env=KVADM_POLICY=skip=100,hitres=600"
run x08-skip3 $TT "adm_env=KVADM_POLICY=skip=3,hitres=600"
# the 30 s bypass without the block reservation for passed hits (what the reservation buys in the replay)
run x08-skip30-nores $TT "adm_env=KVADM_POLICY=skip=30"
echo "[$(date -Is)] x08f done" >> $R/chain.txt
