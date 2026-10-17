#!/bin/bash
# RQ1-B agent runtime validation (2026-10-17): the three real runs, back to back. 400 tasks each, same seed, same tasks.
#   k8-l1g   8 concurrent agents, LMCache L1 1 GB  (mild pressure: ~106 chunks of 9.4 MB vs ~50 live)
#   k16-l1g 16 concurrent agents, LMCache L1 1 GB  (pressure: the live contexts about fill the cache)
#   k8-l4g   8 concurrent agents, LMCache L1 4 GB  (no pressure: timing reference)
cd /home/ghu4/CXL || exit 1
OUT=experimental_results/2026-10-17-rq1b-agent-runtime-validation/real; mkdir -p $OUT
PY=/mnt/local/ghu4/envs/lmcache/bin/python
$PY benchmarks/agent/run_agent_exp.py $OUT k8-l1g  400 8  --l1-gb 1 --gpu-blocks 2048
$PY benchmarks/agent/run_agent_exp.py $OUT k16-l1g 400 16 --l1-gb 1 --gpu-blocks 3072
$PY benchmarks/agent/run_agent_exp.py $OUT k8-l4g  400 8  --l1-gb 4 --gpu-blocks 2048
echo "chain done $(date)"
