#!/usr/bin/env bash
# Pair B address-map probes (docs/experiments/2026-09-01-pairb-address-map.md)
# P1: solo latency + 8T read bandwidth per half of /dev/dax2.0 (128G vs 384G)
# P2: co-run scaling — two 8T streams same-half vs cross-half (separate CCDs)
# P2L: chase victim in low half under 8T stream in same half vs other half
set -u
cd "$(dirname "$0")/../.."
CP=benchmarks/memory/cxlprobe
DAX=/dev/dax2.0
OUT=experimental_results/2026-09-01-pairb-address-map
mkdir -p "$OUT"
REPS=${REPS:-3}; S=4
{ date; ls -l $DAX; daxctl list -u | grep -A3 dax2.0; numactl --hardware | grep size; } > "$OUT/machine-state.txt" 2>&1
: > "$OUT/p1-solo.txt"; : > "$OUT/p2-corun.txt"; : > "$OUT/p2l-chase-under-load.txt"

stream() { $CP --mode=daxstream --dax=$DAX --dax-offset=$1 --size=8G --threads=8 --secs=$2 --cpu-offset=$3 --tag=$4 2>/dev/null; }
chase()  { $CP --mode=daxchase  --dax=$DAX --dax-offset=$1 --size=1G --samples=1000000 --secs=6 --cpu-offset=$2 --tag=$3 2>/dev/null; }

for rep in $(seq 1 $REPS); do
  echo "=== rep $rep $(date +%T) ==="
  # P1 solo
  for off in 128G 384G; do
    chase  $off 0 "p1-chase-$off"   >> "$OUT/p1-solo.txt"
    stream $off $S 0 "p1-stream-$off" >> "$OUT/p1-solo.txt"
  done
  # P2 co-run: A on CCD0 (cpu 0..7), B on CCD1 (cpu 16..23), started together
  for pair in "64G 160G same-low" "320G 416G same-high" "64G 320G cross"; do
    set -- $pair
    stream $1 $S 0  "p2-$3-A-$1" >> "$OUT/p2-corun.txt" &
    stream $2 $S 16 "p2-$3-B-$2" >> "$OUT/p2-corun.txt" &
    wait
  done
  # P2L: chase victim @128G (cpu 0) under 8T stream @ same half (160G) vs other half (384G)
  for agg in 160G 384G; do
    stream $agg 8 16 "p2l-agg-$agg" >> "$OUT/p2l-chase-under-load.txt" &
    A=$!; sleep 1.5
    chase 128G 0 "p2l-chase-under-$agg" >> "$OUT/p2l-chase-under-load.txt"
    wait $A
  done
done
echo "DONE $(date +%T)"
