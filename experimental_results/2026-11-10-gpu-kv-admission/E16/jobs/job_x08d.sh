#!/bin/bash
# Follow-up of x08a on the 16 GB node c60 (2026-11-11 02:55): P2 with a bypass bound of 30 s lowered the mean TTFT of the overloaded tool-agent
# replay by 28 % (3 s: 2 %, 10 s: 8 %). Same set-up as job_x08a.sh (pool pinned to 7,456 blocks, 150 GB host tier, stock run x08-base on this node,
# policy module v1.4, commit 49c3585 + c68ce39). Runs: the bypass alone with the 30 s bound (stock token rules); P2 with a bound of 100 s (longer
# than any TTFT of the run: effectively no bound); a repeat of P2 with 30 s. Then the conversation trace under overload on this node with its own
# stock run: P2 (3 s) and P2 with 30 s. Replaces job_x08c.sh (335007, cancelled 50 s after its start; its fragments are in X08/aborted-x08c/).
R=/mnt/beegfs/ghu4/kvadm/results/X08; S=/home/ghu4/CXL/benchmarks/serving; W=/home/ghu4/CXL/workloads
B="tokres=768,fastchunk=512,resvall,blkfirst"
run() { tag=$1; T=$2; shift 2; $S/remote16.sh $R replay.py $tag $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=150 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
TT=$W/mooncake_toolagent_trace.jsonl; TC=$W/mooncake_conversation_trace.jsonl
run x08-skip30 $TT "adm_env=KVADM_POLICY=skip=30,hitres=600"
run x08-p2-skip100 $TT "adm_env=KVADM_POLICY=$B,skip=100,hitres=600"
run x08-p2-skip30-r2 $TT "adm_env=KVADM_POLICY=$B,skip=30,hitres=600"
run x08c-conv-base $TC
run x08c-conv-p2 $TC "adm_env=KVADM_POLICY=$B,skip=3,hitres=600"
run x08c-conv-p2-skip30 $TC "adm_env=KVADM_POLICY=$B,skip=30,hitres=600"
echo "[$(date -Is)] x08d done" >> $R/chain.txt
