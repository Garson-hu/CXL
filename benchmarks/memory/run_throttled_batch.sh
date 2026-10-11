#!/bin/bash
# 2026-10-11 throttled-DRAM baseline: the layer-2 emulation (same trace window, calibration, tier size) with the KV
# tier in DRAM but all stores capped at 48 GB/s — the ceiling the CXL tier showed — so DRAM and CXL tiers move the
# same bytes with the same burst shape and the only difference is where they land. Finished runs are skipped.
set -u
OUT=${1:-experimental_results/2026-10-11-throttled-dram-baseline}
TR=workloads/mooncake_conversation_trace.jsonl
CAL="--link 9.5 --prefill 7300 --chunk 4 --workers 64 --store-cap 48"
win() { case $1 in 1) echo "600 840";; 4) echo "600 1560";; 8) echo "600 2520";; esac; }
for nb in none reader pr opt llama; do
  vt=80; [ $nb = reader ] && vt=8
  for cfg in 8b:65536:1 8b:65536:4 8b:65536:8 70b:163840:1 70b:163840:4; do
    IFS=: read m blk sp <<< "$cfg"; tag=$nb-$m-${sp}x-dramcap48
    grep -q "^M done" $OUT/$tag-meta.txt 2>/dev/null && continue
    python3 benchmarks/memory/run_layer2.py $OUT $tag $TR $blk $(win $sp) $sp 200 dram --neighbor $nb --vthreads $vt $CAL
  done
done
