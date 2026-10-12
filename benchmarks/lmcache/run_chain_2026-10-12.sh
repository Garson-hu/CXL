#!/bin/bash
# Detached chain of 2026-10-12: experiment 2a (real LMCache, capacity-matched L1), experiment 3 real and emulated.
cd /home/ghu4/CXL
R2=experimental_results/2026-10-11-capacity-matched-kv/real
R3=experimental_results/2026-10-12-checkpoint-kv-mixed
echo "chain start $(date)"
for cfg in dram hybrid dax; do
  grep -q "^M done" $R2/$cfg-meta.txt 2>/dev/null || python3 benchmarks/lmcache/run_2a.py $R2 $cfg workloads/mooncake_conversation_trace.jsonl 0 180 0.08 $cfg 40
done
echo "exp3 real start $(date)"
for spec in none 96:8:full 96:8:rate:20 96:8:kvprio; do
  tag=$(echo $spec | tr ':' '_'); [ $spec = none ] && tag=none
  grep -q "^M done" $R3/real/$tag-meta.txt 2>/dev/null && continue
  if [ $spec = none ]; then python3 benchmarks/lmcache/run_2a.py $R3/real $tag workloads/mooncake_toolagent_trace.jsonl 0 120 0.08 dax 40
  else python3 benchmarks/lmcache/run_2a.py $R3/real $tag workloads/mooncake_toolagent_trace.jsonl 0 120 0.08 dax 40 --ckpt $spec; fi
done
echo "exp3 emulation start $(date)"
mkdir -p $R3/emulation
for cfg in 4:1320 8:2040; do
  IFS=: read sp t1 <<< "$cfg"
  for spec in none 64:8:full 64:8:rate:20 64:8:kvprio; do
    tag=8b-${sp}x-$(echo $spec | tr ':' '_'); f=$R3/emulation/$tag.txt
    grep -q "^S3 " $f 2>/dev/null && continue
    if [ $spec = none ]; then KV3_READER=1 benchmarks/memory/kvemu3 workloads/mooncake_toolagent_trace.jsonl 65536 600 $t1 $sp cxl 0 150 0.8 64 96 4 9.5 7300 > $f 2>&1
    else KV3_CKPT=$spec KV3_READER=1 benchmarks/memory/kvemu3 workloads/mooncake_toolagent_trace.jsonl 65536 600 $t1 $sp cxl 0 150 0.8 64 96 4 9.5 7300 > $f 2>&1; fi
  done
done
echo "chain end $(date)"
