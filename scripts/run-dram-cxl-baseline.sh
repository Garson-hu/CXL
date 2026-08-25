#!/usr/bin/env bash
# run-dram-cxl-baseline.sh — Phase 1 sweep with placement verification.
# Runs latency, stream-read, stream-write, random-read, and a thread-scaling
# sweep on both NUMA node 0 (DRAM) and node 1 (CXL).
#
# Every run uses --verify-placement --strict-placement. If any sampled page
# is on the wrong node, the script aborts with a clear message.
#
# Output: benchmarks/results/<timestamp>-phase1/*.csv
# Does not require sudo.
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
MEMBENCH="$ROOT/benchmarks/memory/membench"

if [[ ! -x "$MEMBENCH" ]]; then
  echo "ERROR: membench not built. Run: (cd $ROOT/benchmarks/memory && make)"
  exit 1
fi

# Verify both nodes are usable. CXL (node 1) is optional — script still runs
# DRAM-only and prints a warning.
"$ROOT/scripts/check-cxl-memory.sh" 1
CXL_OK=$?
if [[ $CXL_OK -ne 0 ]]; then
  echo "WARNING: CXL node not online; running DRAM-only baseline."
fi

TS=$(date +%Y-%m-%d-%H-%M-%S)
OUT="$ROOT/benchmarks/results/${TS}-phase1"
mkdir -p "$OUT"
echo "writing to $OUT"

NODES=(0)
[[ $CXL_OK -eq 0 ]] && NODES+=(1)

SIZE_SMALL="512M"
DUR=5
PLACEMENT_FLAGS=(--verify-placement --strict-placement)

# Helper: invoke membench, abort the whole script if strict placement fails.
run_mb() {
  local outfile="$1"; shift
  if ! "$MEMBENCH" "${PLACEMENT_FLAGS[@]}" "$@" >> "$outfile" 2>>"$OUT/run.log"; then
    rc=$?
    cat <<EOF
ERROR: membench failed with exit code $rc. Last command:
  $MEMBENCH ${PLACEMENT_FLAGS[*]} $*

Common cause: --strict-placement detected pages on the wrong NUMA node.
Look at $OUT/run.log for the "placement check:" line(s) and "wrong page"
samples. If pages went to node 0 when node 1 was requested, the kernel
silently fell back due to insufficient capacity or migration policy.

The script aborts so you don't waste a Phase 1 sweep on bad placement.
EOF
    exit $rc
  fi
}

# Single-thread idle metrics
for n in "${NODES[@]}"; do
  for mode in latency stream-read stream-write random-read; do
    tag="${mode}-node${n}-t1"
    [[ "$mode" == "latency" && "$n" == "0" ]] && tag="header:${tag}"
    run_mb "$OUT/baseline-single.csv" \
        --node="$n" --mode="$mode" --size="$SIZE_SMALL" \
        --threads=1 --duration="$DUR" --tag="$tag" --csv
  done
done

# Thread scaling for stream-read
for n in "${NODES[@]}"; do
  for t in 1 2 4 8 16 32 64 128; do
    tag="streamr-node${n}-t${t}"
    [[ "$t" == "1" && "$n" == "0" ]] && tag="header:${tag}"
    run_mb "$OUT/scaling-stream-read.csv" \
        --node="$n" --mode=stream-read --size="$SIZE_SMALL" \
        --threads="$t" --duration="$DUR" --tag="$tag" --csv
  done
done

# Loaded latency at multiple thread counts
for n in "${NODES[@]}"; do
  for t in 8 16 32; do
    tag="loadlat-node${n}-t${t}"
    [[ "$t" == "8" && "$n" == "0" ]] && tag="header:${tag}"
    run_mb "$OUT/loaded-latency.csv" \
        --node="$n" --mode=loaded-latency --size="$SIZE_SMALL" \
        --threads="$t" --duration="$DUR" --tag="$tag" --csv
  done
done

# Capture environment
{
  echo "=== date ==="; date
  echo; echo "=== hostname ==="; hostname
  echo; echo "=== numactl --hardware ==="; numactl --hardware
  echo; echo "=== /sys/devices/system/node/node1/meminfo ==="
  cat /sys/devices/system/node/node1/meminfo 2>/dev/null || echo "(no node 1)"
} > "$OUT/env.log"

echo "done. results in $OUT"
