#!/usr/bin/env bash
# 1b2 — REDO of the multi-CCD, conservation and writer-victim points of 1b with a verified
# overlap: aggressor 256 MiB/thread (fast pre-touch), 12 s settle before the victim, 30 s window,
# liveness check after the victim, wall-clock epochs from membench stderr (measure_start/end).
# Reader/victim on CCD0 (cpus 0..), writers on CCD2-7 (cpu-offset 32): 32T=CCD2-3, 64T=CCD2-5, 96T=CCD2-7.
set -u
cd "$(dirname "$0")/../.."
MB=benchmarks/memory/membench; CP=benchmarks/memory/cxlprobe
OUT=experimental_results/2026-09-08-dram-write-drain
D=4; AGG_D=30; SETTLE=12; REPS=${REPS:-3}; NODE=0
MAT="$OUT/1b2-matrix.csv"; AGG="$OUT/1b2-aggressor.csv"; CH="$OUT/1b2-chase.csv"; ERR="$OUT/1b2-stderr.log"; AGGERR="$OUT/1b2-aggressor-stderr.log"
HDR="tag,node,mode,threads,size_per_thread_bytes,read_pct,duration_sec,total_bytes,bandwidth_gib_s,avg_latency_ns,victim_latency_ns,aggressor_bandwidth_gib_s,total_bandwidth_gib_s,rep"
echo "$HDR" > "$MAT"; echo "$HDR" > "$AGG"; echo "tag,mode,node,samples,mean_ns,p50,p90,p99,p99.9,p99.99,max,rep" > "$CH"
victim() { # $1 tag $2 mode $3 threads
  echo "victim $1 rep=$rep start=$(date +%s.%N)" >> "$ERR"
  row=$($MB --mode=$2 --node=$NODE --threads=$3 --cpu-offset=0 --duration=$D --rw=67:33 --tag="$1" --csv 2>>"$ERR"); echo "$row,$rep" >> "$MAT"
  echo "victim $1 rep=$rep end=$(date +%s.%N)" >> "$ERR"
}
chase() { echo "chase $1 rep=$rep start=$(date +%s.%N)" >> "$ERR"
  row=$($CP --mode=chase --node=$NODE --size=1G --samples=1000000 --secs=$D --cpu-offset=0 --tag="$1" --csv 2>>"$ERR"); echo "$row,$rep" >> "$CH"
  echo "chase $1 rep=$rep end=$(date +%s.%N)" >> "$ERR"; }
agg_start() { # $1 mode $2 threads $3 tag
  echo "aggressor $3 rep=$rep launch=$(date +%s.%N)" >> "$AGGERR"
  $MB --mode=$1 --node=$NODE --threads=$2 --cpu-offset=32 --size=256M --duration=$AGG_D --tag="$3" --csv 2>>"$AGGERR" | sed "s/\$/,$rep/" >> "$AGG" & AGGPID=$!
  sleep $SETTLE; }
agg_end() { echo "aggressor $1 rep=$rep alive_after_victim=$(kill -0 $AGGPID 2>/dev/null && echo yes || echo NO) t=$(date +%s.%N)" >> "$AGGERR"; kill $AGGPID 2>/dev/null; wait $AGGPID 2>/dev/null; }
for rep in $(seq 1 "$REPS"); do
  echo "=== 1b2 rep $rep/$REPS $(date +%T) ==="
  victim 1b2-ro-idle stream-read 4; victim 1b2-ro32-idle stream-read 32; chase 1b2-chase-idle
  victim 1b2-wv-plain-idle stream-write 4; victim 1b2-wv-nt-idle stream-write-nt 4; victim 1b2-mixed16-idle mixed 16
  for kind in nt plain; do
    mode=stream-write-nt; [ $kind = plain ] && mode=stream-write
    for W in 32 64 96; do
      agg_start $mode $W "1b2-rw-$kind-w$W";  victim "1b2-rw-$kind-w$W" stream-read 4; agg_end "1b2-rw-$kind-w$W"
      agg_start $mode $W "1b2-ch-$kind-w$W";  chase  "1b2-chase-$kind-w$W";            agg_end "1b2-ch-$kind-w$W"
      echo "  $kind w$W read/chase done $(date +%T)"
    done
    # conservation (32T reader) and writer/mixed victims at the two strongest points
    for W in 64 96; do
      agg_start $mode $W "1b2-rw32-$kind-w$W"; victim "1b2-rw32-$kind-w$W" stream-read 32; agg_end "1b2-rw32-$kind-w$W"
      agg_start $mode $W "1b2-wv-plain-$kind-w$W"; victim "1b2-wv-plain-$kind-w$W" stream-write 4; agg_end "1b2-wv-plain-$kind-w$W"
      agg_start $mode $W "1b2-wv-nt-$kind-w$W"; victim "1b2-wv-nt-$kind-w$W" stream-write-nt 4; agg_end "1b2-wv-nt-$kind-w$W"
      agg_start $mode $W "1b2-mixed16-$kind-w$W"; victim "1b2-mixed16-$kind-w$W" mixed 16; agg_end "1b2-mixed16-$kind-w$W"
      echo "  $kind w$W victims done $(date +%T)"
    done
  done
done
echo "DONE-1B2 $(date +%T)"
