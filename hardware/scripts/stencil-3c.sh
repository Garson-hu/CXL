#!/usr/bin/env bash
# Phase 3c: stencil (pond) Case A (all DRAM) vs Case B (new on CXL), healthy DRAM,
# two worlds: idle, and with a DRAM NT-write pressure aggressor on a separate CCD.
# CXL: daxA=/dev/dax0.0, daxB=/dev/dax1.0 (dax2.0 unavailable 2026-09-14).
# CPUs: compute 16T on cpus 0-15 (CCD0); copiers 8T on 32.. (CCD2); aggressor 80T on 48..127 (CCD3-7, ~290 GiB/s NT, per 1b).
set -u
cd "$(dirname "$0")/../.."
P=benchmarks/stencil/pond; MB=benchmarks/memory/membench
OUT=experimental_results/2026-09-14-stencil-3c; mkdir -p $OUT
AGG_T=${AGG_T:-80}; AGG_D=${AGG_D:-400}; REPS=${REPS:-2}; STEPS=${STEPS:-20}
{ date; hostname; uptime; numactl -H | head -4; ls -l /dev/dax*; echo "AGG_T=$AGG_T STEPS=$STEPS REPS=$REPS"; } > $OUT/machine-state.txt 2>&1
COMMON="--gib=8 --steps=$STEPS --threads=16 --cpu0=0 --cpu-copy=32 --copy-threads=8 --daxA=/dev/dax0.0 --daxB=/dev/dax1.0"
run() { tag=$1; shift; echo "=== $tag $(date +%T) ==="; $P $COMMON --tag=$tag "$@" > $OUT/$tag.csv 2> $OUT/$tag.err; tail -1 $OUT/$tag.csv; }
suite() { # $1 world prefix
  w=$1
  for st in normal nt; do
    NT=""; [ $st = nt ] && NT="--nt"
    run $w-A-alldram-rotate-$st-r$rep --place=dram,dram,dram --policy=rotate $NT
    run $w-B-rotate-$st-r$rep         --place=dram,dram,daxB --policy=rotate $NT
    run $w-B-copyback-$st-r$rep       --place=dram,dram,daxB --policy=copyback $NT
    run $w-B-migrate-$st-r$rep        --place=dram,dram,daxB --policy=migrate $NT
    run $w-B-pingpong-$st-r$rep       --place=dram,dram,daxB,daxA --policy=pingpong $NT
  done
}
for rep in $(seq 1 $REPS); do
  suite idle
  # pressure world: restart a fresh aggressor for every pond run (killed after; BW known from 1b write-only points)
  for st in normal nt; do
    NT=""; [ $st = nt ] && NT="--nt"
    for cfg in "A-alldram-rotate|dram,dram,dram|rotate" "B-rotate|dram,dram,daxB|rotate" \
               "B-copyback|dram,dram,daxB|copyback" "B-migrate|dram,dram,daxB|migrate" \
               "B-pingpong|dram,dram,daxB,daxA|pingpong"; do
      IFS='|' read name place pol <<< "$cfg"
      $MB --mode=stream-write-nt --node=0 --threads=$AGG_T --cpu-offset=48 --duration=$AGG_D --tag=agg-$name-$st-r$rep --csv \
          >> $OUT/aggressor.csv 2>> $OUT/aggressor.err & AGG=$!
      sleep 3
      run press-$name-$st-r$rep --place=$place --policy=$pol $NT
      kill $AGG 2>/dev/null; wait $AGG 2>/dev/null
    done
  done
done
echo "DONE $(date +%T)"
