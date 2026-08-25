#!/usr/bin/env bash
# Three KV-cache placement baselines for the Week 1 LLM path.
# Edit CXL_NODES and MODEL before running.
#
# Report TTFT, TBT, throughput for each configuration.
set -u

CXL_NODES="${CXL_NODES:-2,3,4,5}"      # <-- set from numactl --hardware
DRAM_NODE="${DRAM_NODE:-0}"
MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"

echo "=== CONFIG 1: default DRAM ==="
numactl --membind="$DRAM_NODE" --cpunodebind="$DRAM_NODE" \
  vllm serve "$MODEL" --max-model-len 8192 &
SERVER=$!
# TODO: run benchmark client, collect TTFT / TBT / throughput
# kill $SERVER

echo "=== CONFIG 2: KV cache on CXL ==="
numactl --membind="$CXL_NODES" \
  vllm serve "$MODEL" --max-model-len 8192 &
SERVER=$!
# TODO: benchmark
# kill $SERVER

echo "=== CONFIG 3: interleaved DRAM + CXL ==="
numactl --interleave="$DRAM_NODE,$CXL_NODES" \
  vllm serve "$MODEL" --max-model-len 8192 &
SERVER=$!
# TODO: benchmark
# kill $SERVER
