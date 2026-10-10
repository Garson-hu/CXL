#!/bin/bash
# Layer-1 batch (revised 2026-10-10 after the 0.2x runs overloaded the card: ~4.6 k prompt tokens/s with real outputs).
# Normal load: trace minutes 0-3 at 0.08x (~60% of capacity), no neighbour, run to the end (~38 min each).
# Saturated: 0.2x, 10 min of serving (then open requests are cancelled), alone and beside each policy-campaign
# neighbour (cpus 0..; vLLM on 96-127).
set -u
OUT=${1:-experimental_results/2026-10-10-lmcache-kv-traffic/layer1}
T=workloads
python3 benchmarks/lmcache/run_layer1.py $OUT normal-conv $T/mooncake_conversation_trace.jsonl 0 180 0.08
python3 benchmarks/lmcache/run_layer1.py $OUT normal-tool $T/mooncake_toolagent_trace.jsonl    0 180 0.08
python3 benchmarks/lmcache/run_layer1.py $OUT sat-alone   $T/mooncake_conversation_trace.jsonl 0 300 0.2 --duration 600
for nb in reader pr opt llama; do
  vt=80; [ $nb = reader ] && vt=8
  python3 benchmarks/lmcache/run_layer1.py $OUT sat-$nb $T/mooncake_conversation_trace.jsonl 0 300 0.2 --duration 600 --neighbor $nb --vthreads $vt
done
