#!/usr/bin/env bash
# Intel MLC sweep on c28. Requires `mlc` in PATH (download from Intel if absent).
#
# Usage: ./mlc-sweep.sh <DRAM_NODE> <CXL_NODE_1> [CXL_NODE_2 ...]
# Example: ./mlc-sweep.sh 0 2 3 4 5
#
# Populate the CXL NUMA node IDs from `numactl --hardware` output in inspect-system.sh.
set -u

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <DRAM_NODE> <CXL_NODE_1> [CXL_NODE_2 ...]"
  exit 1
fi

DRAM_NODE="$1"; shift
CXL_NODES=("$@")
CXL_LIST=$(IFS=,; echo "${CXL_NODES[*]}")

echo "=== date ==="; date
echo "DRAM_NODE=$DRAM_NODE  CXL_NODES=(${CXL_NODES[*]})  CXL_LIST=$CXL_LIST"
echo

echo "=== DRAM idle_latency ==="
mlc --idle_latency -c0 -i"$DRAM_NODE"
echo
echo "=== DRAM max_bandwidth ==="
mlc --max_bandwidth -c0 -i"$DRAM_NODE"
echo
echo "=== DRAM loaded_latency ==="
mlc --loaded_latency -c0 -i"$DRAM_NODE"
echo

for n in "${CXL_NODES[@]}"; do
  echo "=== CXL node $n idle_latency ==="
  mlc --idle_latency -c0 -i"$n"
  echo
  echo "=== CXL node $n max_bandwidth ==="
  mlc --max_bandwidth -c0 -i"$n"
  echo
  echo "=== CXL node $n loaded_latency ==="
  mlc --loaded_latency -c0 -i"$n"
  echo
done

echo "=== CXL aggregate (interleave $CXL_LIST) max_bandwidth ==="
numactl --interleave="$CXL_LIST" mlc --max_bandwidth
echo

echo "=== CXL aggregate loaded_latency ==="
numactl --interleave="$CXL_LIST" mlc --loaded_latency
