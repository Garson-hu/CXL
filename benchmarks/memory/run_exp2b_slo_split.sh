#!/bin/bash
# 2026-10-12: how much DRAM write bandwidth Adam tolerates at 70B 4x (paced static split, 200 GiB effective)
cd /home/ghu4/CXL
until grep -q "^M done" experimental_results/2026-10-11-capacity-matched-kv/real/hybrid-meta.txt 2>/dev/null; do sleep 20; done
sleep 30
OUT=experimental_results/2026-10-11-capacity-matched-kv/emulation; TR=workloads/mooncake_conversation_trace.jsonl
for d in 24 40; do
  c=$((200 - d)); tag=opt-70b-4x-split$d
  grep -q "^M done" $OUT/$tag-meta.txt 2>/dev/null && continue
  python3 benchmarks/memory/run_exp2b.py $OUT $tag $TR 163840 600 1320 4 split $d $c --neighbor opt --vthreads 80
done
echo ALLDONE
