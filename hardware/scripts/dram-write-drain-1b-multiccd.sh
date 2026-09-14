#!/usr/bin/env bash
# 1b extension — writers spread across several CCDs (NPS1: one CCD caps at ~79 GiB/s of
# NT writes, far below the 12-channel socket ceiling). Reader stays 4T on CCD0 (cpus 0-3).
# Writers: cpu-offset 32 → cpus 32.. ; 16 threads per CCD: 32T=CCD2-3, 64T=CCD2-5, 96T=CCD2-7.
set -u
cd "$(dirname "$0")/../.."
MB=benchmarks/memory/membench; CP=benchmarks/memory/cxlprobe
OUT=experimental_results/2026-09-08-dram-write-drain
D=${D:-4}; AGG_D=${AGG_D:-10}; REPS=${REPS:-3}; NODE=0
MAT="$OUT/1b-matrix.csv"; AGG="$OUT/1b-aggressor.csv"; CH="$OUT/1b-chase.csv"; ERR="$OUT/1b-stderr.log"
reader() { row=$($MB --mode=stream-read --node=$NODE --threads=4 --cpu-offset=0 --duration=$D --tag="$1" --csv 2>>"$ERR"); echo "$row,$rep" >> "$MAT"; }
chase()  { row=$($CP --mode=chase --node=$NODE --size=1G --samples=1000000 --secs=$D --cpu-offset=0 --tag="$1" --csv 2>>"$ERR"); echo "$row,$rep" >> "$CH"; }
writer_bg() { $MB --mode="$1" --node=$NODE --threads="$2" --cpu-offset=32 --duration="$4" --tag="$3" --csv 2>>"$ERR" | sed "s/\$/,$rep/" >> "$AGG" & AGGPID=$!; }
for rep in $(seq 1 "$REPS"); do
  echo "=== multiccd rep $rep/$REPS $(date +%T) ==="
  for kind in nt plain; do
    mode=stream-write-nt; [ $kind = plain ] && mode=stream-write
    for W in 32 64 96; do
      writer_bg $mode $W "1b-wo-$kind-w$W" $D; wait $AGGPID
      writer_bg $mode $W "1b-rw-$kind-w$W" $AGG_D; sleep 2.5; reader "1b-rw-$kind-w$W"; wait $AGGPID
      writer_bg $mode $W "1b-ch-$kind-w$W" $AGG_D; sleep 2.5; chase "1b-chase-$kind-w$W"; wait $AGGPID
      echo "  $kind w$W done $(date +%T)"
    done
  done
done
echo "DONE-MULTICCD $(date +%T)"
