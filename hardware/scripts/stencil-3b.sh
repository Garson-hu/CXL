#!/usr/bin/env bash
# Phase 3b: stencil (pond) strategy comparison, CXL side. 8 GiB x 3 buffers, 16 threads, 20 steps.
cd "$(dirname "$0")/../.."
P=benchmarks/stencil/pond; OUT=experimental_results/2026-09-08-stencil-write-tier; mkdir -p $OUT
{ date; numactl --hardware | grep size; ls -l /dev/dax0.0 /dev/dax2.0; } > $OUT/machine-state.txt 2>&1
COMMON="--gib=8 --steps=20 --threads=16 --cpu0=0 --cpu-copy=64 --copy-threads=8"
run() { tag=$1; shift; echo "=== $tag $(date +%T) ==="; $P $COMMON --tag=$tag "$@" > $OUT/$tag.csv 2> $OUT/$tag.err; tail -1 $OUT/$tag.csv; }
for st in normal nt; do
  NT=""; [ $st = nt ] && NT="--nt"
  run A-alldram-rotate-$st   --place=dram,dram,dram --policy=rotate $NT
  run B-rotate-$st           --place=dram,dram,daxB --policy=rotate $NT
  run B-copyback-$st         --place=dram,dram,daxB --policy=copyback $NT
  run B-migrate-$st          --place=dram,dram,daxB --policy=migrate $NT
  run B-pingpong-$st         --place=dram,dram,daxB,daxA --policy=pingpong $NT
done
echo "DONE $(date +%T)"
