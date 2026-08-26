#!/usr/bin/env bash
# Verification battery for the gate-2b "6.3x DRAM reader collapse" cell.
# Tests: dose-response (2/4/8 writers), plain-store vs NT writers,
# CCD-swap, and 8R-vs-8W fairness. All on node 0 (DRAM).
set -u
cd "$(dirname "$0")/../.."
MB=benchmarks/memory/membench
OUT=experimental_results/2026-08-25-gate2-verification
mkdir -p "$OUT"
D=4; AGG_D=10; REPS=${REPS:-3}
HDR="tag,node,mode,threads,size_per_thread_bytes,read_pct,duration_sec,total_bytes,bandwidth_gib_s,avg_latency_ns,victim_latency_ns,aggressor_bandwidth_gib_s,total_bandwidth_gib_s,rep"
echo "$HDR" > "$OUT/victims.csv"
echo "$HDR" > "$OUT/aggressors.csv"
{ date; numactl --hardware | tail -8; } > "$OUT/machine-state.txt" 2>&1

# co-run: $1 tag, $2 victim-threads, $3 victim-offset, $4 agg-mode ("" = idle),
#         $5 agg-threads, $6 agg-offset
corun() {
  local tag=$1 vt=$2 voff=$3 amode=$4 at=$5 aoff=$6 AGG=""
  if [ -n "$amode" ]; then
    $MB --mode="$amode" --node=0 --threads="$at" --cpu-offset="$aoff" \
        --duration=$AGG_D --tag="agg-$tag" --csv \
        >> "$OUT/aggressors.csv" 2>>"$OUT/stderr.log" &
    AGG=$!
    sleep 2.5
  fi
  row=$($MB --mode=stream-read --node=0 --threads="$vt" --cpu-offset="$voff" \
        --duration=$D --tag="$tag" --csv 2>>"$OUT/stderr.log")
  echo "$row,$rep" >> "$OUT/victims.csv"
  [ -n "$AGG" ] && wait "$AGG"
}

for rep in $(seq 1 "$REPS"); do
  echo "=== rep $rep/$REPS $(date +%T) ==="
  corun v4r-idle          4 0  ""              0 16
  corun v4r-nt2w          4 0  stream-write-nt 2 16
  corun v4r-nt4w          4 0  stream-write-nt 4 16
  corun v4r-nt8w          4 0  stream-write-nt 8 16   # replication of the claim
  corun v4r-plain8w       4 0  stream-write    8 16   # plain stores instead of NT
  corun v4r-ccdswap-nt8w  4 16 stream-write-nt 8 0    # victim CCD1, writers CCD0
  corun v8r-nt8w          8 0  stream-write-nt 8 16   # 8 readers vs 8 writers
done
echo "DONE $(date +%T)"
