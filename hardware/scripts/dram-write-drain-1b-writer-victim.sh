#!/usr/bin/env bash
# 1b addendum: victim that WRITES (4T plain / 4T NT on CCD0, node 0) under multi-CCD NT writers (cpus 32..).
set -u
cd "$(dirname "$0")/../.."
MB=benchmarks/memory/membench; OUT=experimental_results/2026-09-08-dram-write-drain
D=4; AGG_D=12; REPS=${REPS:-3}; NODE=0
MAT="$OUT/1b-matrix.csv"; AGG="$OUT/1b-aggressor.csv"; ERR="$OUT/1b-stderr.log"
victim() { row=$($MB --mode=$2 --node=$NODE --threads=4 --cpu-offset=0 --duration=$D --tag="$1" --csv 2>>"$ERR"); echo "$row,$rep" >> "$MAT"; }
for rep in $(seq 1 $REPS); do
  echo "=== writer-victim rep $rep $(date +%T) ==="
  victim "1b-wv-plain-idle" stream-write; victim "1b-wv-nt-idle" stream-write-nt
  for W in 64 96; do
    for vk in plain nt; do
      vm=stream-write; [ $vk = nt ] && vm=stream-write-nt
      $MB --mode=stream-write-nt --node=$NODE --threads=$W --cpu-offset=32 --size=256M --duration=$AGG_D --tag="1b-wv-$vk-w$W" --csv 2>>"$ERR" | sed "s/\$/,$rep/" >> "$AGG" & A=$!
      sleep 5; victim "1b-wv-$vk-w$W" $vm; wait $A
    done
  done
done
echo "DONE-WV $(date +%T)"
