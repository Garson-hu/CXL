#!/usr/bin/env bash
# 1b — DRAM write-drain measurement matrix (campaign Phase 1, Part B of
# docs/experiments/2026-09-08-dram-write-drain.md). Healthy DRAM (post 2026-09-09 reboot).
# Reader: 4T stream-read, node 0, cpus 0..3 (CCD0).  Writers: separate process,
# node 0, cpus 16.. (CCD1), {1,2,4,8,16} threads × {plain, NT} stores.
# Traffic: read-only, write-only, read+write; plus 1T pointer-chase (cxlprobe) under writers.
set -u
cd "$(dirname "$0")/../.."
MB=benchmarks/memory/membench
CP=benchmarks/memory/cxlprobe
OUT=experimental_results/2026-09-08-dram-write-drain
mkdir -p "$OUT"
D=${D:-4}; AGG_D=${AGG_D:-10}; REPS=${REPS:-3}; NODE=0
HDR="tag,node,mode,threads,size_per_thread_bytes,read_pct,duration_sec,total_bytes,bandwidth_gib_s,avg_latency_ns,victim_latency_ns,aggressor_bandwidth_gib_s,total_bandwidth_gib_s,rep"
MAT="$OUT/1b-matrix.csv"; AGG="$OUT/1b-aggressor.csv"; CH="$OUT/1b-chase.csv"; ERR="$OUT/1b-stderr.log"
echo "$HDR" > "$MAT"; echo "$HDR" > "$AGG"
echo "tag,mode,node,samples,mean_ns,p50,p90,p99,p99.9,p99.99,max,rep" > "$CH"
{ date; hostname; uptime; numactl -H | head -4; ls -l /dev/dax*; cat /proc/sys/kernel/perf_event_paranoid; } > "$OUT/1b-machine-state.txt" 2>&1

reader() { # $1 tag
  row=$($MB --mode=stream-read --node=$NODE --threads=4 --cpu-offset=0 --duration=$D --tag="$1" --csv 2>>"$ERR")
  echo "$row,$rep" >> "$MAT"
}
chase() { # $1 tag
  row=$($CP --mode=chase --node=$NODE --size=1G --samples=1000000 --secs=$D --cpu-offset=0 --tag="$1" --csv 2>>"$ERR")
  echo "$row,$rep" >> "$CH"
}
writer_bg() { # $1 mode $2 threads $3 tag $4 duration -> sets AGGPID
  $MB --mode="$1" --node=$NODE --threads="$2" --cpu-offset=16 --duration="$4" --tag="$3" --csv \
      2>>"$ERR" | sed "s/\$/,$rep/" >> "$AGG" &
  AGGPID=$!
}

for rep in $(seq 1 "$REPS"); do
  echo "=== rep $rep/$REPS $(date +%T) ==="
  reader "1b-ro-idle"
  chase  "1b-chase-idle"
  for kind in nt plain; do
    mode=stream-write-nt; [ $kind = plain ] && mode=stream-write
    for W in 1 2 4 8 16; do
      # write-only
      writer_bg $mode $W "1b-wo-$kind-w$W" $D; wait $AGGPID
      # read + write
      writer_bg $mode $W "1b-rw-$kind-w$W" $AGG_D; sleep 2.5
      reader "1b-rw-$kind-w$W"; wait $AGGPID
      # chase under writers
      writer_bg $mode $W "1b-ch-$kind-w$W" $AGG_D; sleep 2.5
      chase "1b-chase-$kind-w$W"; wait $AGGPID
      echo "  $kind w$W done $(date +%T)"
    done
  done
done
echo "DONE $(date +%T)"
