#!/bin/bash
# Capacity-sensitivity point of Experiment D on the 16 GB node c66, second part (2026-11-11 02:58): tool-agent trace, seconds 0-200 at 0.04x, pool
# pinned to 7,456 blocks, 80 GB host tier, policy module v1.4 (commit 49c3585 + c68ce39). The stock run of this node is e66-tool04-80-p7456-base
# (job_e66.sh, 334993; that job is stopped after its stock run because the two runs it would have made next - the bypass alone with a 3 s bound and
# P3 - were overtaken by the result of x08-p2-skip30). Runs: P4 = P2 with the bypass bound raised to 30 s; the bypass alone with the 30 s bound.
R=/mnt/beegfs/ghu4/kvadm/results/E; S=/home/ghu4/CXL/benchmarks/serving; T=/home/ghu4/CXL/workloads/mooncake_toolagent_trace.jsonl
B="tokres=768,fastchunk=512,resvall,blkfirst"
run() { tag=$1; shift; $S/remote16.sh $R replay.py $tag $T 0 200 0.04 max_out=1024 dequant_s=1 tier=dram l1_gb=80 adm=true gpu_blocks=7456 "$@"; echo "[$(date -Is)] $tag done on $(hostname)" >> $R/chain.txt; sleep 5; }
# (revised 2026-11-11 03:45) first the ordering baseline that a client can realize: vLLM priority scheduling with priority = number of prompt tokens
# (shortest prompt first); under overload it lowered the mean TTFT by 49 % (E16/X08/x08b-priolen) - does it do anything at the sustainable load?
run e66-tool04-80-p7456-priolen prio=len
run e66-tool04-80-p7456-skip30 "adm_env=KVADM_POLICY=skip=30,hitres=600"
# the overloaded replay on the large pool (19,916 blocks, 120 GB host tier; stock run e-tool08-120-big-base on this node, job_e8.sh): no admission attempt is
# refused there, so the bypass has nothing to act on - does ordering alone (shortest prompt first) help?
$S/remote16.sh $R replay.py e-tool08-120-big-priolen $T 0 100 0.08 max_out=1024 dequant_s=1 tier=dram l1_gb=120 adm=true prio=len; echo "[$(date -Is)] e-tool08-120-big-priolen done on $(hostname)" >> $R/chain.txt
echo "[$(date -Is)] e66b done" >> $R/chain.txt
