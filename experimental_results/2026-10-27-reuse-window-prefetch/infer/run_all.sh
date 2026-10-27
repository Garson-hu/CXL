#!/bin/bash
# Inference part of the 2026-10-27 exploratory study (window-based reuse LRU vs the existing baselines, capacity sweep): exact commands.
# Run from the repo root on c28. One process per trace x capacity, every policy in it (the admission simulator is single-threaded Python).
# Blocks: Llama-3.1-8B KV chunks of 512 tokens (67.1 MB); capacities 458 / 915 / 1831 / 2747 / 5493 blocks = 30 / 60 / 120 / 180 / 360 GiB
# (DRAM-only 60 GiB vs DRAM + CXL 180 GiB are the advisor's two configurations; 30 / 120 / 360 complete the curve; 10987 = 720 GiB for the
# ceiling). Scoring: second half of the requests (first half = warm-up and online statistics), usable-prefix hits, LMCache order.
# 2nd_int_auto = the RQ1 deployable policy (gap rule + res_ft regime switch on an SLRU structure, dead-eviction residence estimator).
set -u
cd /home/ghu4/CXL
O=experimental_results/2026-10-27-reuse-window-prefetch/infer; mkdir -p $O/hits
POL=lru,slru,2nd,2nd_int,2nd_int_auto,oracle,wslru:10,wslru:30,wslru:50,wslru:100,wslru:200,wslru:300,wlfu:10,wlfu:30,wlfu:50,wlfu:100,wlfu:200,wlfu:300,wslru2nd:10,wslru2nd:30,wslru2nd:50,wslru2nd:100,wslru2nd:200,wslru2nd:300
for tr in conversation toolagent; do
  for cap in 458 915 1831 2747 5493; do
    tag=$tr-cap$cap
    [ -f $O/$tag-replay.csv ] && continue
    nohup python3 scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O $tag --mooncake --caps $cap --policies $POL --regime res_ft --normal-mode slru --res-mode dead --dump-hits $O/hits/$tag > $O/$tag.log 2>&1 &
  done
  tag=$tr-cap10987
  [ -f $O/$tag-replay.csv ] || nohup python3 scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O $tag --mooncake --caps 10987 --policies lru,slru,2nd_int_auto,oracle,wslru:100,wslru2nd:100 --regime res_ft --normal-mode slru --res-mode dead --dump-hits $O/hits/$tag > $O/$tag.log 2>&1 &
done
wait
echo "INFERDONE $(date)"
