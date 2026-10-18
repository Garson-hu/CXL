#!/bin/bash
# RQ1-B reuse-horizon validation (2026-10-17): real long-tool agent runs (agent_tasks_lt: pandas / pytest / python tools
# with REAL execution time on 1.5M-6M-row datasets), 200 tasks each, same seed.
#   lt-k8-l1g     8 agents, L1 1 GB
#   lt-k16-l1g   16 agents, L1 1 GB
#   lt-k8-l1g-bg  8 agents, L1 1 GB, plus REAL background churn: the Mooncake conversation trace replayed at 0.05x on the same server
#   lt-k16-l1g-bg 16 agents, L1 1 GB, same background
cd /home/ghu4/CXL || exit 1
OUT=experimental_results/2026-10-17-rq1b-reuse-horizon/real; mkdir -p $OUT
PY=/mnt/local/ghu4/envs/lmcache/bin/python; BG=workloads/mooncake_conversation_trace.jsonl
$PY benchmarks/agent/run_agent_exp.py $OUT lt-k8-l1g     200 8  --l1-gb 1 --gpu-blocks 2048 --workload agent_tasks_lt --client-cpus 32-95
$PY benchmarks/agent/run_agent_exp.py $OUT lt-k16-l1g    200 16 --l1-gb 1 --gpu-blocks 3072 --workload agent_tasks_lt --client-cpus 32-95
$PY benchmarks/agent/run_agent_exp.py $OUT lt-k8-l1g-bg  200 8  --l1-gb 1 --gpu-blocks 2048 --workload agent_tasks_lt --client-cpus 32-95 --bg-trace $BG --bg-speed 0.05
$PY benchmarks/agent/run_agent_exp.py $OUT lt-k16-l1g-bg 200 16 --l1-gb 1 --gpu-blocks 3072 --workload agent_tasks_lt --client-cpus 32-95 --bg-trace $BG --bg-speed 0.05
echo "chain done $(date)"
