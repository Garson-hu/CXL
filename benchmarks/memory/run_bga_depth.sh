#!/bin/bash
# Bucket-depth sweep of the budget policy (2026-10-13, user's request): depths 2 / 4 / 8 blocks x budgets 8 / 16 / 32 GB/s
# next to Adam, 8B 4x and 8B 8x, on the CALIBRATION segment (depth 1 = the existing calibration runs); then the chosen
# (depth, budget) pair per configuration (select_depth.py: best hit inside the SLO) x 3 independent runs on the
# EVALUATION segment next to Adam, comparable with evaluation/. Waits for the main chain (ALLDONE in its log: same node,
# same dax0.0 region, same neighbour cpus), then rebuilds kvemu2 from the source with KV2_BUCKET_BLOCKS (default 1 =
# the old behaviour). Finished runs are skipped. usage: run_bga_depth.sh [before_s=60]
set -u
cd /home/ghu4/CXL
BEF=${1:-60}
R=experimental_results/2026-10-12-budget-gated-admission; TR=workloads/mooncake_conversation_trace.jsonl
until grep -q ALLDONE /mnt/local/ghu4/bga-chain-2.log 2>/dev/null; do sleep 60; done
echo "depth sweep start $(date)"
(cd benchmarks/memory && gcc -O2 -g -std=gnu11 -Wall -Wextra -Wno-misleading-indentation -Wno-unused-variable -Wno-unused-parameter \
   -mavx2 -pthread -I../../system/cxlpath/include kvemu2.c ../../system/cxlpath/build/libcxlpath.a -lm -o kvemu2) || { echo "build failed"; exit 1; }
echo "kvemu2 rebuilt $(date) (bucket-depth option; default depth 1)"
export KV2_WARM=common
done_() { grep -q "^M done" $1/$2-meta.txt 2>/dev/null; }
run() {   # run <dir> <tag> <block> <t0> <t1> <speed> <depth> <budget>
  local d=$1 tag=$2 blk=$3 t0=$4 t1=$5 sp=$6 depth=$7 bu=$8
  done_ $d $tag && return
  KV2_BUCKET_BLOCKS=$depth KV2_BUDGET_GBPS=$bu python3 benchmarks/memory/run_exp2b.py $d $tag $TR $blk $t0 $t1 $sp budget 64 136 \
      --neighbor opt --vthreads 80 --before-s $BEF --reader-chunk 64
}
for c in 8b:65536:4:2040:2760 8b:65536:8:2040:3480; do IFS=: read m blk sp t0 t1 <<< "$c"
  for d in 2 4 8; do for b in 8 16 32; do run $R/depth opt-$m-${sp}x-d$d-budget$b $blk $t0 $t1 $sp $d $b; done; done
done
python3 benchmarks/memory/analyze_bga.py $R/depth > /dev/null && python3 benchmarks/memory/select_depth.py $R/calibration $R/depth || exit 1
CH=$R/depth/chosen-depth.txt
echo "depth evaluation start $(date)"
for rep in 1 2 3; do
  for c in 8b:65536:4:600:1320 8b:65536:8:600:2040; do IFS=: read m blk sp t0 t1 <<< "$c"; cf=$m-${sp}x
    d=$(awk -v c=$cf '$2==c {print $4}' $CH); b=$(awk -v c=$cf '$2==c {print $6}' $CH)
    [ "$d" = 1 ] && continue     # depth 1 at its chosen budget already has three evaluation runs (evaluation/opt-<cfg>-budget-r*)
    run $R/depth-eval opt-$cf-d$d-budget$b-r$rep $blk $t0 $t1 $sp $d $b
  done
done
python3 benchmarks/memory/analyze_bga.py $R/depth-eval > /dev/null
echo "DEPTHDONE $(date)"
