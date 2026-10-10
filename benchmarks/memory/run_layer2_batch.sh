#!/bin/bash
# Layer 2 of 2026-10-10-lmcache-kv-traffic: HOST MEMORY TRAFFIC EMULATION (kvemu), conversation trace, cache warmed with
# trace seconds 0-600, then ~4 min of traffic: 1x [600,840), 4x [600,1560), 8x [600,2520) trace seconds. Block sizes
# of Llama-3.1-8B (64 MiB per 512 tokens) and Llama-3.1-70B (160 MiB). Tier 200 GiB in DRAM or in CXL (dax0.0).
# Calibration from layer 1: piece 2048 tokens (4 blocks), 9.5 GB/s per transfer, 7300 prefill tokens/s per request.
# Phase A: no neighbour (traffic: offered vs achieved, backlog, peaks). Phase B: beside each policy-campaign neighbour.
set -u
OUT=${1:-experimental_results/2026-10-10-lmcache-kv-traffic/layer2}
TR=workloads/mooncake_conversation_trace.jsonl
CAL="--link 9.5 --prefill 7300 --chunk 4 --workers 64"
win() { case $1 in 1) echo "600 840";; 4) echo "600 1560";; 8) echo "600 2520";; esac; }
for nb in none reader pr opt llama; do
  vt=80; [ $nb = reader ] && vt=8
  for model in 8b:65536 70b:163840; do
    m=${model%%:*}; blk=${model##*:}
    for sp in 1 4 8; do
      for place in dram cxl; do
        python3 benchmarks/memory/run_layer2.py $OUT $nb-$m-${sp}x-$place $TR $blk $(win $sp) $sp 200 $place --neighbor $nb --vthreads $vt $CAL
      done
    done
  done
done
