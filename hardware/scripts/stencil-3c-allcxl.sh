#!/usr/bin/env bash
# 3c extra cell: Case C = ALL buffers on CXL (old=dax0.0@0, cur=dax1.0@0, new=dax1.0@16G), rotate,
# idle and under the 80T NT DRAM aggressor (CCD3-7, 256M/thread, 12 s settle, killed after).
set -u
cd "$(dirname "$0")/../.."
P=benchmarks/stencil/pond; MB=benchmarks/memory/membench
OUT=experimental_results/2026-09-14-stencil-3c; REPS=${REPS:-2}; STEPS=${STEPS:-20}
COMMON="--gib=8 --steps=$STEPS --threads=16 --cpu0=0 --cpu-copy=32 --copy-threads=8 --daxA=/dev/dax0.0 --daxB=/dev/dax1.0"
run() { tag=$1; shift; echo "=== $tag $(date +%T) ==="; $P $COMMON --tag=$tag "$@" > $OUT/$tag.csv 2> $OUT/$tag.err; tail -1 $OUT/$tag.csv; }
for rep in $(seq 1 $REPS); do
  for st in normal nt; do
    NT=""; [ $st = nt ] && NT="--nt"
    run idle-C-allcxl-rotate-$st-r$rep --place=daxA,daxB,daxB --daxoff=0,0,16 --policy=rotate $NT
    $MB --mode=stream-write-nt --node=0 --threads=80 --cpu-offset=48 --size=256M --duration=240 --tag=agg2-C-allcxl-$st-r$rep --csv >> $OUT/aggressor2.csv 2>> $OUT/aggressor2.err & AGG=$!
    sleep 12
    run press2-C-allcxl-rotate-$st-r$rep --place=daxA,daxB,daxB --daxoff=0,0,16 --policy=rotate $NT
    echo "  aggressor alive at end: $(kill -0 $AGG 2>/dev/null && echo yes || echo NO) $(date +%T)"
    kill $AGG 2>/dev/null; wait $AGG 2>/dev/null
  done
done
echo "DONE-ALLCXL $(date +%T)"
