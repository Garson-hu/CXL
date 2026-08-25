#!/usr/bin/env bash
# Gates 1+2 for docs/experiments/2026-08-25-direction-gates.md
# Gate 1: duplex matrix   — R:W thread sweep per node (is the write direction
#                            a separate resource?)
# Gate 2: cross-interference — latency + bandwidth victims on each node under
#                            NT-write aggressors targeting each node.
# Output: experimental_results/2026-08-25-direction-gates/ (CSV + logs).
set -u
cd "$(dirname "$0")/../.."
MB=benchmarks/memory/membench
OUT=experimental_results/2026-08-25-direction-gates
mkdir -p "$OUT"
D=${D:-4}          # seconds per measured point
REPS=${REPS:-5}    # median-of-5 per METHODOLOGY.md
CXL=4; DRAM=0
HDR="tag,node,mode,threads,size_per_thread_bytes,read_pct,duration_sec,total_bytes,bandwidth_gib_s,avg_latency_ns,victim_latency_ns,aggressor_bandwidth_gib_s,total_bandwidth_gib_s,rep"

{ date; hostname; uname -r; numactl --hardware; } > "$OUT/machine-state.txt" 2>&1

echo "$HDR" > "$OUT/gate1-duplex-matrix.csv"
echo "$HDR" > "$OUT/gate2-cross-interference.csv"

for rep in $(seq 1 "$REPS"); do
  echo "=== rep $rep/$REPS gate1 $(date +%T) ==="
  for node in $CXL $DRAM; do
    for rw in "16 0" "12 4" "8 8" "4 12" "0 16"; do
      set -- $rw; R=$1; W=$2; T=$((R+W))
      row=$($MB --mode=duplex --node=$node --threads=$T --write-threads=$W \
            --duration=$D --tag="g1-n$node-r$R-w$W" --csv 2>>"$OUT/gate1-stderr.log")
      echo "$row,$rep" >> "$OUT/gate1-duplex-matrix.csv"
    done
  done
  echo "=== rep $rep/$REPS gate2 $(date +%T) ==="
  for V in $DRAM $CXL; do
    row=$($MB --mode=latency --node=$V --duration=$D \
          --tag="g2-lat-v$V-idle" --csv 2>>"$OUT/gate2-stderr.log")
    echo "$row,$rep" >> "$OUT/gate2-cross-interference.csv"
    row=$($MB --mode=stream-read --node=$V --threads=4 --duration=$D \
          --tag="g2-bw-v$V-idle" --csv 2>>"$OUT/gate2-stderr.log")
    echo "$row,$rep" >> "$OUT/gate2-cross-interference.csv"
    for W in $DRAM $CXL; do
      row=$($MB --mode=loaded-latency --node=$V --threads=9 \
            --aggressor-kind=write-nt --aggressor-node=$W --duration=$D \
            --tag="g2-lat-v$V-wr$W" --csv 2>>"$OUT/gate2-stderr.log")
      echo "$row,$rep" >> "$OUT/gate2-cross-interference.csv"
      row=$($MB --mode=duplex --node=$V --threads=12 --write-threads=8 \
            --write-node=$W --duration=$D \
            --tag="g2-bw-v$V-wr$W" --csv 2>>"$OUT/gate2-stderr.log")
      echo "$row,$rep" >> "$OUT/gate2-cross-interference.csv"
    done
  done
done
echo "DONE $(date +%T)"
