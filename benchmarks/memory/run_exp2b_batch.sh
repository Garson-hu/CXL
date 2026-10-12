#!/bin/bash
# Experiment 2b (2026-10-11): capacity-matched KV tiers in host memory traffic emulation (kvemu2). Effective capacity
# 200 GiB for every policy (LMCache-like: 80 + 170 GiB at its 0.8 eviction watermark; tiered policies 64 + 136 GiB).
# Cache warmed with trace seconds 0-600, then ~180 s of traffic. Borrow policies run the real cxlpathd with
# --loan-block-s 1 (the 60 s default stopped every loan in bursty KV traffic: 2026-10-11 test). Finished runs are skipped.
set -u
OUT=${1:-experimental_results/2026-10-11-capacity-matched-kv/emulation}
TR=workloads/mooncake_conversation_trace.jsonl
for nb in none reader opt; do
  vt=80; [ $nb = reader ] && vt=8
  for cfg in 8b:65536:4:1320 8b:65536:8:2040 70b:163840:4:1320; do
    IFS=: read m blk sp t1 <<< "$cfg"
    for pol in dram:200:0:0 dramcap48:200:0:48 cxl:0:200:0 lmcache:80:170:0 split:64:136:0 cxlfirst:64:136:0 borrowtier:64:136:0 borrowglob:64:136:0 borrowmig:64:136:0; do
      IFS=: read p d c cap <<< "$pol"; kp=$p; [ $p = dramcap48 ] && kp=dram
      tag=$nb-$m-${sp}x-$p
      grep -q "^M done" $OUT/$tag-meta.txt 2>/dev/null && continue
      python3 benchmarks/memory/run_exp2b.py $OUT $tag $TR $blk 600 $t1 $sp $kp $d $c --neighbor $nb --vthreads $vt --store-cap $cap
    done
  done
done
