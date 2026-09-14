#!/usr/bin/env bash
# 1b conservation check: does a LARGE reader (32T, CCD0-1) + saturating multi-CCD writers hit a fixed ceiling?
set -u
cd "$(dirname "$0")/../.."
MB=benchmarks/memory/membench; OUT=experimental_results/2026-09-08-dram-write-drain
D=4; AGG_D=10; REPS=${REPS:-3}; NODE=0
MAT="$OUT/1b-matrix.csv"; AGG="$OUT/1b-aggressor.csv"; ERR="$OUT/1b-stderr.log"
reader32() { row=$($MB --mode=stream-read --node=$NODE --threads=32 --cpu-offset=0 --duration=$D --tag="$1" --csv 2>>"$ERR"); echo "$row,$rep" >> "$MAT"; }
for rep in $(seq 1 $REPS); do
  echo "=== conservation rep $rep $(date +%T) ==="
  reader32 "1b-ro32-idle"
  for kind in nt plain; do
    mode=stream-write-nt; [ $kind = plain ] && mode=stream-write
    for W in 64 96; do
      $MB --mode=$mode --node=$NODE --threads=$W --cpu-offset=32 --duration=$AGG_D --tag="1b-rw32-$kind-w$W" --csv 2>>"$ERR" | sed "s/\$/,$rep/" >> "$AGG" & A=$!
      sleep 2.5; reader32 "1b-rw32-$kind-w$W"; wait $A
    done
  done
done
echo "DONE-CONS $(date +%T)"
