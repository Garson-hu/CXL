#!/usr/bin/env bash
# Phase 3c pressure world, corrected (2026-09-14): the first attempt started pond 3 s after an
# 80-thread aggressor with 1 GiB/thread buffers, whose pre-touch (80 GiB) had not finished; its
# NT phase only overlapped steps 16-19. Here: 256 MiB/thread (20 GiB), 12 s settle, 240 s window,
# aggressor killed after pond. Same CPU layout as stencil-3c.sh.
set -u
cd "$(dirname "$0")/../.."
P=benchmarks/stencil/pond; MB=benchmarks/memory/membench
OUT=experimental_results/2026-09-14-stencil-3c
AGG_T=${AGG_T:-80}; AGG_D=${AGG_D:-240}; REPS=${REPS:-2}; STEPS=${STEPS:-20}
COMMON="--gib=8 --steps=$STEPS --threads=16 --cpu0=0 --cpu-copy=32 --copy-threads=8 --daxA=/dev/dax0.0 --daxB=/dev/dax1.0"
run() { tag=$1; shift; echo "=== $tag $(date +%T) ==="; $P $COMMON --tag=$tag "$@" > $OUT/$tag.csv 2> $OUT/$tag.err; tail -1 $OUT/$tag.csv; }
for rep in $(seq 1 $REPS); do
  for st in normal nt; do
    NT=""; [ $st = nt ] && NT="--nt"
    for cfg in "A-alldram-rotate|dram,dram,dram|rotate" "B-rotate|dram,dram,daxB|rotate" \
               "B-copyback|dram,dram,daxB|copyback" "B-migrate|dram,dram,daxB|migrate" \
               "B-pingpong|dram,dram,daxB,daxA|pingpong"; do
      IFS='|' read name place pol <<< "$cfg"
      $MB --mode=stream-write-nt --node=0 --threads=$AGG_T --cpu-offset=48 --size=256M --duration=$AGG_D --tag=agg2-$name-$st-r$rep --csv \
          >> $OUT/aggressor2.csv 2>> $OUT/aggressor2.err & AGG=$!
      sleep 12
      run press2-$name-$st-r$rep --place=$place --policy=$pol $NT
      echo "  aggressor alive at end: $(kill -0 $AGG 2>/dev/null && echo yes || echo NO) $(date +%T)"
      kill $AGG 2>/dev/null; wait $AGG 2>/dev/null
    done
  done
done
echo "DONE-PRESS2 $(date +%T)"
