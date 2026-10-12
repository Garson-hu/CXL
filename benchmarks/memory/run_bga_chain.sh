#!/bin/bash
# Budget-gated admission experiment (2026-10-12, agreed with the user): calibration -> fixed selection rule -> evaluation
# with independent repeats -> varying neighbour load (oracle budget = upper bound) -> 70B 4x long run. Host memory traffic
# emulation (kvemu2). Every tiered policy: DRAM 64 + CXL 136 GiB (200 GiB effective), per-tier LRU, the same warm-up
# placement (KV2_WARM=common). Calibration uses a later trace segment (2040 s on) than evaluation (600 s on). Finished runs
# are skipped, so the chain can be restarted. usage: run_bga_chain.sh [before_s=60]
set -u
cd /home/ghu4/CXL
BEF=${1:-60}
R=experimental_results/2026-10-12-budget-gated-admission; TR=workloads/mooncake_conversation_trace.jsonl
export KV2_WARM=common
done_() { grep -q "^M done" $1/$2-meta.txt 2>/dev/null; }
# run <dir> <tag> <neighbor> <block> <t0> <t1> <speed> <policy> <share|-> <budget|-> [extra run_exp2b args...]
run() {
  local d=$1 tag=$2 nb=$3 blk=$4 t0=$5 t1=$6 sp=$7 pol=$8 sh=$9 bu=${10}; shift 10
  done_ $d $tag && return
  local vt=80; [ $nb = reader ] && vt=8
  local e=(); [ "$sh" != - ] && e+=(KV2_SPLIT_SHARE=$sh); [ "$bu" != - ] && e+=(KV2_BUDGET_GBPS=$bu)
  env "${e[@]}" python3 benchmarks/memory/run_exp2b.py $d $tag $TR $blk $t0 $t1 $sp $pol 64 136 --neighbor $nb --vthreads $vt \
      --before-s $BEF --reader-chunk 64 "$@"
}
CAL="8b:65536:4:2040:2760 8b:65536:8:2040:3480 70b:163840:4:2040:2760"
EVAL="8b:65536:4:600:1320 8b:65536:8:600:2040 70b:163840:4:600:1320"
echo "calibration start $(date)"
for nb in opt reader; do
  for c in $CAL; do IFS=: read m blk sp t0 t1 <<< "$c"
    for s in 8 16 24 32 48; do run $R/calibration $nb-$m-${sp}x-split$s $nb $blk $t0 $t1 $sp split $(echo "scale=2; $s/100" | bc) -; done
    for b in 2 4 8 12 16 24 32; do run $R/calibration $nb-$m-${sp}x-budget$b $nb $blk $t0 $t1 $sp budget - $b; done
  done
done
python3 benchmarks/memory/analyze_bga.py $R/calibration > /dev/null && python3 benchmarks/memory/select_settings.py $R/calibration || exit 1
CH=$R/calibration/chosen.txt
pick() { awk -v n=$1 -v c=$2 -v k=$3 '$1==n && $2==c && $3==k {print $4}' $CH; }
echo "evaluation start $(date)"
for rep in 1 2 3; do
  for nb in opt reader; do
    for c in $EVAL; do IFS=: read m blk sp t0 t1 <<< "$c"; cf=$m-${sp}x
      s=$(pick $nb $cf split); b=$(pick $nb $cf budget)
      [ "$s" != 0 ] && run $R/evaluation $nb-$cf-split-r$rep $nb $blk $t0 $t1 $sp split $s -
      [ "$b" != 0 ] && run $R/evaluation $nb-$cf-budget-r$rep $nb $blk $t0 $t1 $sp budget - $b
      run $R/evaluation $nb-$cf-borrowtier-r$rep $nb $blk $t0 $t1 $sp borrowtier - -
      run $R/evaluation $nb-$cf-borrowmig-r$rep $nb $blk $t0 $t1 $sp borrowmig - -
      [ $rep = 1 ] && run $R/evaluation $nb-$cf-cxlfirst-r1 $nb $blk $t0 $t1 $sp cxlfirst - -
    done
  done
done
echo "varying start $(date)"
for rep in 1 2; do
  for c in 8b:65536:8:600:2040 70b:163840:4:600:1320; do IFS=: read m blk sp t0 t1 <<< "$c"; cf=$m-${sp}x
    s=$(pick opt $cf split); b=$(pick opt $cf budget); ob=$(pick any $cf offbudget)
    [ "$s" != 0 ] && run $R/varying $cf-split-r$rep opt $blk $t0 $t1 $sp split $s - --phases 30:30
    [ "$b" != 0 ] && run $R/varying $cf-budget-r$rep opt $blk $t0 $t1 $sp budget - $b --phases 30:30
    run $R/varying $cf-oracle-r$rep opt $blk $t0 $t1 $sp budget - - --phases 30:30 --phase-budgets $b:$ob
    run $R/varying $cf-borrowtier-r$rep opt $blk $t0 $t1 $sp borrowtier - - --phases 30:30
    run $R/varying $cf-borrowmig-r$rep opt $blk $t0 $t1 $sp borrowmig - - --phases 30:30
    run $R/varying $cf-cxlfirst-r$rep opt $blk $t0 $t1 $sp cxlfirst - - --phases 30:30
  done
done
echo "long run start $(date)"
s=$(pick opt 70b-4x split); b=$(pick opt 70b-4x budget)
[ "$b" != 0 ] && run $R/longrun 70b-4x-budget opt 163840 600 3480 4 budget - $b
[ "$s" != 0 ] && run $R/longrun 70b-4x-split opt 163840 600 3480 4 split $s -
run $R/longrun 70b-4x-cxlfirst opt 163840 600 3480 4 cxlfirst - -
for d in evaluation varying longrun; do python3 benchmarks/memory/analyze_bga.py $R/$d > /dev/null; done
echo "ALLDONE $(date)"
