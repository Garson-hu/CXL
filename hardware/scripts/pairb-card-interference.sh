#!/usr/bin/env bash
# Card-vs-card interference on Pair B via /dev/dax2.0 256B classes.
# Victim = card A (even class, dax region 64G, CCD0). Aggressor = 8T on card B
# (odd class) or card A (even class, control), dax region 160G, CCD1, reads or
# NT writes. See docs/experiments/2026-09-02-pairb-card-interference.md
set -u
cd "$(dirname "$0")/../.."
CP=benchmarks/memory/cxlprobe; DAX=/dev/dax2.0
OUT=experimental_results/2026-09-02-pairb-card-interference; mkdir -p "$OUT"
REPS=${REPS:-3}; VS=4; AS=10
{ date; ls -l $DAX; numactl --hardware | grep size; } > "$OUT/machine-state.txt" 2>&1
: > "$OUT/results.txt"
vchase()  { $CP --mode=daxchase  --dax=$DAX --dax-offset=64G --size=1G --samples=1000000 --secs=$VS --class=$1 --cpu-offset=0 --tag=$2 2>/dev/null >> "$OUT/results.txt"; }
vstream() { $CP --mode=daxstride --dax=$DAX --dax-offset=64G --size=8G --threads=8 --secs=$VS --stride=512 --chunk=256 --offset=$1 --cpu-offset=0 --tag=$2 2>/dev/null >> "$OUT/results.txt"; }
agg()     { $CP --mode=$1 --dax=$DAX --dax-offset=160G --size=8G --threads=8 --secs=$AS --stride=512 --chunk=256 --offset=$2 --cpu-offset=16 --tag=$3 2>/dev/null >> "$OUT/results.txt"; }
for rep in $(seq 1 $REPS); do
  echo "=== rep $rep $(date +%T) ==="
  vchase 0 "v-chase-A-idle"; vstream 0 "v-stream-A-idle"
  for cfg in "daxstride 256 readB" "daxstridewr 256 writeB" "daxstride 0 readA" "daxstridewr 0 writeA"; do
    set -- $cfg
    agg $1 $2 "agg-$3-for-chase" & A=$!; sleep 1.5; vchase 0 "v-chase-A-under-$3"; wait $A
    agg $1 $2 "agg-$3-for-stream" & A=$!; sleep 1.5; vstream 0 "v-stream-A-under-$3"; wait $A
  done
  # symmetric spot check: victim on card B (odd) under NT writes to card A (even)
  agg daxstridewr 0 "agg-writeA-for-chaseB" & A=$!; sleep 1.5; vchase 1 "v-chase-B-under-writeA"; wait $A
  vchase 1 "v-chase-B-idle"
done
echo "DONE $(date +%T)"
