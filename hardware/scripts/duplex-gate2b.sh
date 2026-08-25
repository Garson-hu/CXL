#!/usr/bin/env bash
# Gate 2b — cross-interference with victim and aggressors on DIFFERENT CCDs.
# The first gate-2 run co-located victim/aggressor threads on adjacent cores;
# they shared a CCD fabric port, which dominated the result. Here: victim on
# cpus 0.. (CCD0 of quadrant 0), 8 NT-writer aggressors as a SEPARATE process
# on cpus 16.. (CCD1 of quadrant 0). Two-process pattern as in May phase22.
set -u
cd "$(dirname "$0")/../.."
MB=benchmarks/memory/membench
OUT=experimental_results/2026-08-25-direction-gates
mkdir -p "$OUT"
D=${D:-4}
REPS=${REPS:-5}
AGG_D=10        # aggressor runs longer; victim window sits fully inside
CXL=4; DRAM=0
HDR="tag,node,mode,threads,size_per_thread_bytes,read_pct,duration_sec,total_bytes,bandwidth_gib_s,avg_latency_ns,victim_latency_ns,aggressor_bandwidth_gib_s,total_bandwidth_gib_s,rep"
echo "$HDR" > "$OUT/gate2b-ccd-separated.csv"

run_victim() { # $1 tag  $2 node  $3 mode  $4 threads
  row=$($MB --mode="$3" --node="$2" --threads="$4" --cpu-offset=0 \
        --duration=$D --tag="$1" --csv 2>>"$OUT/gate2b-stderr.log")
  echo "$row,$rep" >> "$OUT/gate2b-ccd-separated.csv"
}

for rep in $(seq 1 "$REPS"); do
  echo "=== rep $rep/$REPS $(date +%T) ==="
  for V in $DRAM $CXL; do
    # idle baselines
    run_victim "g2b-lat-v$V-idle" "$V" latency 1
    run_victim "g2b-bw-v$V-idle"  "$V" stream-read 4
    for W in $DRAM $CXL; do
      # aggressor: separate process, CCD1 (cpu-offset 16), 8 NT writers
      $MB --mode=stream-write-nt --node="$W" --threads=8 --cpu-offset=16 \
          --duration=$AGG_D --tag="bg-w$W" --csv \
          >> "$OUT/gate2b-aggressor.csv" 2>>"$OUT/gate2b-stderr.log" &
      AGG=$!
      sleep 2.5   # let the aggressor finish setup and reach steady state
      run_victim "g2b-lat-v$V-wr$W" "$V" latency 1
      wait "$AGG"
      $MB --mode=stream-write-nt --node="$W" --threads=8 --cpu-offset=16 \
          --duration=$AGG_D --tag="bg-w$W" --csv \
          >> "$OUT/gate2b-aggressor.csv" 2>>"$OUT/gate2b-stderr.log" &
      AGG=$!
      sleep 2.5
      run_victim "g2b-bw-v$V-wr$W" "$V" stream-read 4
      wait "$AGG"
    done
  done
done
echo "DONE $(date +%T)"
