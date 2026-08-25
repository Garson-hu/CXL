#!/usr/bin/env bash
# run-interference-matrix.sh — Phase 2 interference matrix.
# For each victim mode and each aggressor mode, run them concurrently with
# the same NUMA placement and measure the victim's slowdown vs running alone.
# Output: benchmarks/results/<timestamp>-phase2/matrix-node<N>.csv
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
MEMBENCH="$ROOT/benchmarks/memory/membench"

if [[ ! -x "$MEMBENCH" ]]; then
  echo "ERROR: membench not built. Run: (cd $ROOT/benchmarks/memory && make)"
  exit 1
fi

TS=$(date +%Y-%m-%d-%H-%M-%S)
OUT="$ROOT/benchmarks/results/${TS}-phase2"
mkdir -p "$OUT"

VICTIM_MODES=(latency random-read stream-read mixed)
AGGRESSOR_MODES=(stream-read stream-write random-read mixed)

# Per-process buffer size; keep modest so two processes fit comfortably.
SIZE=$((256 << 20))   # 256 MiB
VICTIM_DUR=5
AGG_DUR=7              # aggressor starts first and outlives victim
VICTIM_THREADS=1
AGG_THREADS=8

run_one() {
  local node="$1" victim_mode="$2" agg_mode="$3" header_tag="$4"
  local tag="v${victim_mode}-a${agg_mode}-node${node}"
  [[ "$header_tag" == "1" ]] && tag="header:${tag}"

  # Start aggressor in the background
  local agg_log="$OUT/agg-${victim_mode}-${agg_mode}-node${node}.csv"
  "$MEMBENCH" --node="$node" --mode="$agg_mode" \
              --size="$SIZE" --threads="$AGG_THREADS" \
              --duration="$AGG_DUR" --tag="agg-$tag" --csv \
              > "$agg_log" 2>>"$OUT/run.log" &
  local agg_pid=$!

  # Give aggressor a brief head-start
  sleep 0.5

  # Run victim, foreground
  "$MEMBENCH" --node="$node" --mode="$victim_mode" \
              --size="$SIZE" --threads="$VICTIM_THREADS" \
              --duration="$VICTIM_DUR" --tag="$tag" --csv \
              >> "$OUT/matrix-node${node}.csv" 2>>"$OUT/run.log"

  wait "$agg_pid" 2>/dev/null
}

run_baseline() {
  local node="$1" victim_mode="$2" header_tag="$3"
  local tag="v${victim_mode}-aNONE-node${node}"
  [[ "$header_tag" == "1" ]] && tag="header:${tag}"
  "$MEMBENCH" --node="$node" --mode="$victim_mode" \
              --size="$SIZE" --threads="$VICTIM_THREADS" \
              --duration="$VICTIM_DUR" --tag="$tag" --csv \
              >> "$OUT/matrix-node${node}.csv" 2>>"$OUT/run.log"
}

# Detect which nodes are usable
NODES=(0)
"$ROOT/scripts/check-cxl-memory.sh" 1 >/dev/null 2>&1 && NODES+=(1)

first=1
for n in "${NODES[@]}"; do
  for vm in "${VICTIM_MODES[@]}"; do
    # Baseline (no aggressor)
    run_baseline "$n" "$vm" "$first"; first=0
    for am in "${AGGRESSOR_MODES[@]}"; do
      run_one "$n" "$vm" "$am" 0
    done
  done
done

{
  echo "=== date ==="; date
  echo "=== numactl --hardware ==="; numactl --hardware
} > "$OUT/env.log"

echo "done. results in $OUT"
